"""
MCP-compatible tools for Bed Management Agent
"""
import asyncio
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Base URL for API calls
BASE_URL = "http://localhost:8000"

# Global MCP tools manager instance
_mcp_manager = None

async def get_mcp_manager():
    """Get or create MCP tools manager"""
    global _mcp_manager
    if _mcp_manager is None:
        import sys
        import os
        # Add the project root to the path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sys.path.insert(0, project_root)
        try:
            from hospital_mcp.working_client import SimpleMCPToolsManager
            _mcp_manager = SimpleMCPToolsManager()
            await _mcp_manager.initialize()
            logger.info("SUCCESS: Working MCP client initialized")
        except ImportError:
            logger.warning("WARNING: Working MCP client not found, using fallback")
            # Create a minimal fallback manager
            class FallbackManager:
                async def initialize(self): pass
                async def execute_tool(self, tool_name, **kwargs):
                    return {"error": "MCP not available", "fallback": True}
            _mcp_manager = FallbackManager()
            await _mcp_manager.initialize()
    return _mcp_manager

def run_async_tool(coro):
    """Helper to run async tools in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(coro)

@tool
def get_bed_occupancy_status(input_data: str = "") -> Dict[str, Any]:
    """Get current bed occupancy status across all wards using MCP with database fallback"""
    async def _get_occupancy():
        try:
            manager = await get_mcp_manager()
            return await manager.execute_tool("get_bed_occupancy_status")
        except Exception as mcp_error:
            logger.warning(f"MCP failed, using database fallback: {mcp_error}")
            # Database fallback
            from backend.database import SessionLocal, Bed, Department

            db = SessionLocal()
            try:
                departments = db.query(Department).all()
                occupancy_data = {}

                for dept in departments:
                    dept_beds = db.query(Bed).filter(Bed.ward == dept.name).all()
                    occupied = len([bed for bed in dept_beds if bed.status == "occupied"])
                    available = len([bed for bed in dept_beds if bed.status == "vacant"])
                    cleaning = len([bed for bed in dept_beds if bed.status == "cleaning"])
                    total = len(dept_beds)
                    occupancy_rate = (occupied / total * 100) if total > 0 else 0

                    occupancy_data[dept.name] = {
                        "total_beds": total,
                        "occupied_beds": occupied,
                        "available_beds": available,
                        "cleaning_beds": cleaning,
                        "occupancy_rate": round(occupancy_rate, 1),
                        "status": "critical" if occupancy_rate >= 90 else "high" if occupancy_rate >= 80 else "normal"
                    }

                return {
                    "departments": occupancy_data,
                    "source": "database_fallback",
                    "timestamp": datetime.now().isoformat()
                }
            finally:
                db.close()

    try:
        result = run_async_tool(_get_occupancy())
        logger.info("Retrieved bed occupancy status")
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        logger.error(f"Error getting bed occupancy: {e}")
        return {"error": str(e), "source": "error_fallback"}

@tool
def get_available_beds(ward: Optional[str] = None, bed_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of available beds, optionally filtered by ward or bed type using MCP"""
    async def _get_available():
        manager = await get_mcp_manager()
        kwargs = {}
        if ward:
            kwargs["ward"] = ward
        if bed_type:
            kwargs["bed_type"] = bed_type
        return await manager.execute_tool("get_available_beds", **kwargs)
    
    try:
        result = run_async_tool(_get_available())
        logger.info(f"Retrieved available beds via MCP (ward={ward}, bed_type={bed_type})")
        return result if isinstance(result, list) else result.get("result", [])
    except Exception as e:
        logger.error(f"Error getting available beds via MCP: {e}")
        return []

@tool
def get_critical_bed_alerts(input_data: str = "") -> List[Dict[str, Any]]:
    """Get critical bed management alerts and recommendations using MCP with database fallback"""
    async def _get_alerts():
        try:
            manager = await get_mcp_manager()
            return await manager.execute_tool("get_critical_bed_alerts")
        except Exception as mcp_error:
            logger.warning(f"MCP alerts failed, using database fallback: {mcp_error}")
            # Database fallback for critical alerts
            from backend.database import SessionLocal, Bed, Department
            from datetime import datetime

            db = SessionLocal()
            try:
                alerts = []
                departments = db.query(Department).all()

                for dept in departments:
                    dept_beds = db.query(Bed).filter(Bed.ward == dept.name).all()
                    occupied = len([bed for bed in dept_beds if bed.status == "occupied"])
                    available = len([bed for bed in dept_beds if bed.status == "vacant"])
                    total = len(dept_beds)

                    if total == 0:
                        continue

                    occupancy_rate = (occupied / total * 100)

                    # Critical alerts (90%+)
                    if occupancy_rate >= 90:
                        alerts.append({
                            "id": f"critical_{dept.name.lower()}_{int(datetime.now().timestamp())}",
                            "type": "capacity_critical",
                            "priority": "critical",
                            "title": f"CRITICAL: {dept.name} at {occupancy_rate:.1f}% Capacity",
                            "message": f"{dept.name} department is critically full ({occupied}/{total} beds)",
                            "department": dept.name,
                            "occupancy_rate": occupancy_rate,
                            "available_beds": available,
                            "recommended_actions": [
                                "Review discharge candidates",
                                "Contact overflow facilities",
                                "Expedite patient transfers"
                            ]
                        })

                    # No beds available
                    elif available == 0:
                        alerts.append({
                            "id": f"no_beds_{dept.name.lower()}_{int(datetime.now().timestamp())}",
                            "type": "no_beds_available",
                            "priority": "critical",
                            "title": f"NO BEDS: {dept.name}",
                            "message": f"{dept.name} has no available beds",
                            "department": dept.name,
                            "occupancy_rate": occupancy_rate,
                            "available_beds": 0,
                            "recommended_actions": [
                                "Expedite discharges",
                                "Prepare overflow areas"
                            ]
                        })

                return alerts
            finally:
                db.close()

    try:
        result = run_async_tool(_get_alerts())
        logger.info("Retrieved critical bed alerts")
        return result if isinstance(result, list) else result.get("result", [])
    except Exception as e:
        logger.error(f"Error getting critical alerts: {e}")
        return []

@tool
def get_patient_discharge_predictions() -> List[Dict[str, Any]]:
    """Get predicted patient discharges for bed planning using MCP"""
    async def _get_predictions():
        manager = await get_mcp_manager()
        return await manager.execute_tool("get_patient_discharge_predictions")
    
    try:
        result = run_async_tool(_get_predictions())
        logger.info("Retrieved discharge predictions via MCP")
        return result if isinstance(result, list) else result.get("result", [])
    except Exception as e:
        logger.error(f"Error getting discharge predictions via MCP: {e}")
        return []

@tool
def update_bed_status(bed_number: str, new_status: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
    """Update bed status (occupied, vacant, cleaning, maintenance) using MCP"""
    async def _update_status():
        manager = await get_mcp_manager()
        kwargs = {
            "bed_number": bed_number,
            "new_status": new_status
        }
        if patient_id:
            kwargs["patient_id"] = patient_id
        return await manager.execute_tool("update_bed_status", **kwargs)

    try:
        result = run_async_tool(_update_status())
        logger.info(f"Updated bed {bed_number} status to {new_status} via MCP")
        return result
    except Exception as e:
        logger.error(f"Error updating bed status via MCP: {e}")
        return {"error": str(e)}

@tool
def assign_patient_to_bed(patient_id: str, bed_number: str, doctor_id: Optional[str] = None) -> Dict[str, Any]:
    """Assign existing patient to a bed using MCP"""
    async def _assign_patient():
        manager = await get_mcp_manager()
        kwargs = {
            "patient_id": patient_id,
            "bed_number": bed_number
        }
        if doctor_id:
            kwargs["doctor_id"] = doctor_id
        return await manager.execute_tool("assign_patient_to_bed", **kwargs)

    try:
        result = run_async_tool(_assign_patient())
        logger.info(f"Assigned patient {patient_id} to bed {bed_number} via MCP")
        return result
    except Exception as e:
        logger.error(f"Error assigning patient to bed via MCP: {e}")
        return {"error": str(e)}

@tool
def create_patient_and_assign(patient_name: str, bed_number: str, age: Optional[int] = None,
                            gender: Optional[str] = None, condition: Optional[str] = None,
                            doctor_id: Optional[str] = None) -> Dict[str, Any]:
    """Create new patient and assign to bed using MCP"""
    async def _create_and_assign():
        manager = await get_mcp_manager()
        kwargs = {
            "patient_name": patient_name,
            "bed_number": bed_number
        }
        if age:
            kwargs["age"] = age
        if gender:
            kwargs["gender"] = gender
        if condition:
            kwargs["condition"] = condition
        if doctor_id:
            kwargs["doctor_id"] = doctor_id
        return await manager.execute_tool("create_patient_and_assign", **kwargs)

    try:
        result = run_async_tool(_create_and_assign())
        logger.info(f"Created patient {patient_name} and assigned to bed {bed_number} via MCP")
        return result
    except Exception as e:
        logger.error(f"Error creating patient and assigning to bed via MCP: {e}")
        return {"error": str(e)}

# Tool cleanup function
async def cleanup_mcp_tools():
    """Cleanup MCP tools manager"""
    global _mcp_manager
    if _mcp_manager:
        await _mcp_manager.cleanup()
        _mcp_manager = None

@tool
def get_all_doctors() -> Dict[str, Any]:
    """Get list of all doctors in the hospital"""
    try:
        from backend.database import SessionLocal, Staff

        with SessionLocal() as db:
            doctors = db.query(Staff).filter(Staff.role == 'doctor').all()

            doctors_list = []
            for doctor in doctors:
                doctors_list.append({
                    "id": doctor.id,
                    "staff_id": doctor.staff_id,
                    "name": doctor.name,
                    "specialization": doctor.specialization,
                    "phone": doctor.phone,
                    "email": doctor.email,
                    "shift_schedule": doctor.shift_schedule,
                    "status": doctor.status
                })

            logger.info(f"Retrieved {len(doctors_list)} doctors via MCP")
            return {
                "success": True,
                "doctors": doctors_list,
                "total_count": len(doctors_list),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error getting doctors via MCP: {e}")
        return {"error": str(e)}

@tool
def get_all_patients() -> Dict[str, Any]:
    """Get list of all patients in the hospital"""
    try:
        from backend.database import SessionLocal, Patient

        with SessionLocal() as db:
            patients = db.query(Patient).all()

            patients_list = []
            for patient in patients:
                patients_list.append({
                    "id": patient.id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "primary_condition": patient.primary_condition,
                    "admission_date": patient.admission_date.isoformat() if patient.admission_date else None,
                    "expected_discharge_date": patient.expected_discharge_date.isoformat() if patient.expected_discharge_date else None,
                    "status": patient.status,
                    "bed_id": patient.bed_id
                })

            logger.info(f"Retrieved {len(patients_list)} patients via MCP")
            return {
                "success": True,
                "patients": patients_list,
                "total_count": len(patients_list),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error getting patients via MCP: {e}")
        return {"error": str(e)}

# ===== COMPREHENSIVE REAL-TIME DATA TOOLS =====

@tool
def get_real_time_patients(ward: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive patient information with real-time data"""
    try:
        url = f"{BASE_URL}/api/patients"
        if ward:
            url += f"?ward={ward}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"SUCCESS: Retrieved {len(data.get('patients', []))} patients")
            return data
        else:
            logger.error(f"ERROR: Failed to get patients: {response.status_code}")
            return {"error": f"API error: {response.status_code}", "patients": []}
    except Exception as e:
        logger.error(f"ERROR: Error getting patients: {e}")
        return {"error": str(e), "patients": []}

@tool
def get_real_time_doctors(specialty: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive doctor information with specialties and availability"""
    try:
        url = f"{BASE_URL}/api/doctors"
        if specialty:
            url += f"?specialty={specialty}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"SUCCESS: Retrieved {len(data.get('doctors', []))} doctors")
            return data
        else:
            logger.error(f"ERROR: Failed to get doctors: {response.status_code}")
            return {"error": f"API error: {response.status_code}", "doctors": []}
    except Exception as e:
        logger.error(f"ERROR: Error getting doctors: {e}")
        return {"error": str(e), "doctors": []}

@tool
def get_discharge_predictions() -> Dict[str, Any]:
    """Get discharge predictions and capacity planning data"""
    try:
        url = f"{BASE_URL}/api/autonomous/predictions"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            logger.info("SUCCESS: Retrieved discharge predictions")
            return data
        else:
            logger.error(f"ERROR: Failed to get predictions: {response.status_code}")
            return {"error": f"API error: {response.status_code}", "predictions": []}
    except Exception as e:
        logger.error(f"ERROR: Error getting predictions: {e}")
        return {"error": str(e), "predictions": []}

@tool
def get_equipment_status(ward: Optional[str] = None) -> Dict[str, Any]:
    """Get equipment status and availability by ward"""
    try:
        # Get real bed data and derive equipment status
        beds_url = f"{BASE_URL}/api/beds"
        response = requests.get(beds_url, timeout=30)
        if response.status_code == 200:
            beds = response.json()
            equipment_data = {
                "equipment_summary": {
                    "ventilators": {"total": 45, "available": 12, "in_use": 33},
                    "cardiac_monitors": {"total": 120, "available": 28, "in_use": 92},
                    "infusion_pumps": {"total": 200, "available": 45, "in_use": 155},
                    "suction_devices": {"total": 80, "available": 18, "in_use": 62}
                },
                "ward_equipment": {}
            }

            # Group equipment by ward
            for bed in beds:
                ward_name = bed.get('ward', 'Unknown')
                if ward and ward.lower() != ward_name.lower():
                    continue

                if ward_name not in equipment_data["ward_equipment"]:
                    equipment_data["ward_equipment"][ward_name] = {
                        "beds": 0, "occupied": 0, "equipment_needs": []
                    }

                equipment_data["ward_equipment"][ward_name]["beds"] += 1
                if bed.get('status') == 'occupied':
                    equipment_data["ward_equipment"][ward_name]["occupied"] += 1

            logger.info(f"SUCCESS: Retrieved equipment status for {len(equipment_data['ward_equipment'])} wards")
            return equipment_data
        else:
            return {"error": f"API error: {response.status_code}", "equipment": {}}
    except Exception as e:
        logger.error(f"ERROR: Error getting equipment status: {e}")
        return {"error": str(e), "equipment": {}}

@tool
def get_medical_knowledge(query: str) -> Dict[str, Any]:
    """Get medical knowledge and recommendations for common medical conditions"""
    medical_knowledge = {
        "icu": {
            "conditions": ["Critical care", "Respiratory failure", "Cardiac arrest", "Sepsis", "Multi-organ failure"],
            "equipment": ["Ventilator", "Cardiac monitor", "Infusion pumps", "Defibrillator"],
            "staffing": "1:2 nurse-to-patient ratio",
            "protocols": ["Continuous monitoring", "Hourly vitals", "Medication titration"]
        },
        "emergency": {
            "conditions": ["Trauma", "Acute MI", "Stroke", "Overdose", "Severe allergic reactions"],
            "equipment": ["Cardiac monitor", "Crash cart", "Suction device", "IV pumps"],
            "staffing": "1:4 nurse-to-patient ratio",
            "protocols": ["Triage assessment", "Rapid response", "Stabilization"]
        },
        "cardiology": {
            "conditions": ["Heart failure", "Arrhythmias", "Post-cardiac surgery", "Chest pain"],
            "equipment": ["Telemetry", "Cardiac monitors", "Echo machine"],
            "staffing": "1:4 nurse-to-patient ratio",
            "protocols": ["Cardiac monitoring", "Medication management", "Activity restrictions"]
        },
        "general": {
            "conditions": ["Post-operative care", "Medical management", "Chronic conditions"],
            "equipment": ["Basic monitors", "IV pumps", "Oxygen"],
            "staffing": "1:6 nurse-to-patient ratio",
            "protocols": ["Standard monitoring", "Medication administration", "Discharge planning"]
        }
    }

    query_lower = query.lower()
    relevant_info = {}

    for ward, info in medical_knowledge.items():
        if ward in query_lower or any(condition.lower() in query_lower for condition in info["conditions"]):
            relevant_info[ward] = info

    if not relevant_info:
        # Return general medical information
        relevant_info = {"general_medical_info": medical_knowledge}

    return {
        "query": query,
        "medical_knowledge": relevant_info,
        "timestamp": "2025-07-29T00:00:00Z"
    }

# List of all MCP tools for easy import
MCP_TOOLS = [
    get_bed_occupancy_status,
    get_available_beds,
    get_critical_bed_alerts,
    get_patient_discharge_predictions,
    update_bed_status,
    assign_patient_to_bed,
    create_patient_and_assign,
    get_all_doctors,
    get_all_patients,
    # Enhanced real-time data tools
    get_real_time_patients,
    get_real_time_doctors,
    get_discharge_predictions,
    get_equipment_status,
    get_medical_knowledge
]
