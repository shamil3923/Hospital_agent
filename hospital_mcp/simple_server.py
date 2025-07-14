"""
Simple MCP Server for Hospital Bed Management Tools
"""
import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Bed, Patient, BedOccupancyHistory
from sqlalchemy import func

logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """Simple MCP Server for Hospital Bed Management"""
    
    def __init__(self):
        self.tools = {
            "get_bed_occupancy_status": self._get_bed_occupancy_status,
            "get_available_beds": self._get_available_beds,
            "get_critical_bed_alerts": self._get_critical_bed_alerts,
            "get_patient_discharge_predictions": self._get_patient_discharge_predictions,
            "update_bed_status": self._update_bed_status
        }
    
    async def _get_bed_occupancy_status(self, **kwargs) -> Dict[str, Any]:
        """Get current bed occupancy status across all wards"""
        db = SessionLocal()
        try:
            # Get overall statistics
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            vacant_beds = db.query(Bed).filter(Bed.status == "vacant").count()
            cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
            maintenance_beds = db.query(Bed).filter(Bed.status == "maintenance").count()
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            # Get ward-wise breakdown - simplified approach
            ward_stats = []
            wards = db.query(Bed.ward).distinct().all()

            for ward_row in wards:
                ward_name = ward_row[0]
                total = db.query(Bed).filter(Bed.ward == ward_name).count()
                occupied = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == 'occupied').count()
                vacant = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == 'vacant').count()
                cleaning = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == 'cleaning').count()

                ward_stats.append({
                    'ward': ward_name,
                    'total': total,
                    'occupied': occupied,
                    'vacant': vacant,
                    'cleaning': cleaning
                })
            
            ward_breakdown = []
            for ward in ward_stats:
                ward_occupancy = (ward['occupied'] / ward['total'] * 100) if ward['total'] > 0 else 0
                ward_breakdown.append({
                    "ward": ward['ward'],
                    "total_beds": ward['total'],
                    "occupied": ward['occupied'],
                    "vacant": ward['vacant'],
                    "cleaning": ward['cleaning'],
                    "occupancy_rate": round(ward_occupancy, 1)
                })
            
            return {
                "overall": {
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "vacant_beds": vacant_beds,
                    "cleaning_beds": cleaning_beds,
                    "maintenance_beds": maintenance_beds,
                    "occupancy_rate": round(occupancy_rate, 1)
                },
                "ward_breakdown": ward_breakdown,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting bed occupancy status: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    async def _get_available_beds(self, ward: Optional[str] = None, bed_type: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get list of available beds, optionally filtered by ward or bed type"""
        db = SessionLocal()
        try:
            query = db.query(Bed).filter(Bed.status == "vacant")
            
            if ward:
                query = query.filter(Bed.ward == ward)
            if bed_type:
                query = query.filter(Bed.bed_type == bed_type)
                
            available_beds = query.all()
            
            result = []
            for bed in available_beds:
                result.append({
                    "bed_id": bed.id,
                    "bed_number": bed.bed_number,
                    "room_number": bed.room_number,
                    "ward": bed.ward,
                    "bed_type": bed.bed_type,
                    "floor_number": bed.floor_number,
                    "wing": bed.wing,
                    "private_room": bed.private_room,
                    "daily_rate": bed.daily_rate,
                    "last_updated": bed.last_updated.isoformat() if bed.last_updated else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting available beds: {e}")
            return []
        finally:
            db.close()
    
    async def _get_critical_bed_alerts(self, **kwargs) -> List[Dict[str, Any]]:
        """Get critical bed management alerts and recommendations"""
        db = SessionLocal()
        try:
            alerts = []
            
            # Check overall occupancy rate
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            if occupancy_rate > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"Hospital occupancy at {occupancy_rate:.1f}% - Critical capacity reached",
                    "recommendation": "Initiate discharge planning and consider patient transfers",
                    "priority": "high"
                })
            elif occupancy_rate > 85:
                alerts.append({
                    "type": "warning",
                    "message": f"Hospital occupancy at {occupancy_rate:.1f}% - High capacity",
                    "recommendation": "Monitor closely and prepare for potential capacity issues",
                    "priority": "medium"
                })
            
            # Check ICU capacity specifically
            icu_total = db.query(Bed).filter(Bed.ward == "ICU").count()
            icu_occupied = db.query(Bed).filter(Bed.ward == "ICU", Bed.status == "occupied").count()
            icu_rate = (icu_occupied / icu_total * 100) if icu_total > 0 else 0
            
            if icu_rate > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"ICU occupancy at {icu_rate:.1f}% - Critical care capacity reached",
                    "recommendation": "Review ICU patients for potential step-down candidates",
                    "priority": "high"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting critical alerts: {e}")
            return []
        finally:
            db.close()
    
    async def _get_patient_discharge_predictions(self, **kwargs) -> List[Dict[str, Any]]:
        """Get predicted patient discharges for bed planning"""
        db = SessionLocal()
        try:
            # Get patients with expected discharge dates
            upcoming_discharges = db.query(Patient).filter(
                Patient.status == "admitted",
                Patient.expected_discharge_date.isnot(None),
                Patient.expected_discharge_date >= datetime.now(),
                Patient.expected_discharge_date <= datetime.now() + timedelta(days=3)
            ).all()
            
            predictions = []
            for patient in upcoming_discharges:
                bed = db.query(Bed).filter(Bed.id == patient.current_bed_id).first()
                predictions.append({
                    "patient_id": patient.patient_id,
                    "patient_name": patient.name,
                    "current_bed": bed.bed_number if bed else "Unknown",
                    "ward": bed.ward if bed else "Unknown",
                    "expected_discharge": patient.expected_discharge_date.isoformat(),
                    "condition": patient.condition,
                    "severity": patient.severity
                })
            
            return sorted(predictions, key=lambda x: x["expected_discharge"])
            
        except Exception as e:
            logger.error(f"Error getting discharge predictions: {e}")
            return []
        finally:
            db.close()
    
    async def _update_bed_status(self, bed_number: str, new_status: str, patient_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Update bed status (occupied, vacant, cleaning, maintenance)"""
        db = SessionLocal()
        try:
            bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
            if not bed:
                return {"error": f"Bed {bed_number} not found"}
            
            old_status = bed.status
            bed.status = new_status
            bed.patient_id = patient_id
            bed.last_updated = datetime.now().isoformat()
            
            if new_status == "occupied" and patient_id:
                bed.admission_time = datetime.now().isoformat()
            elif new_status == "vacant":
                bed.admission_time = None
                bed.expected_discharge = None
                bed.patient_id = None
            
            db.commit()
            
            return {
                "success": True,
                "bed_number": bed_number,
                "old_status": old_status,
                "new_status": new_status,
                "patient_id": patient_id,
                "updated_at": bed.last_updated
            }
            
        except Exception as e:
            logger.error(f"Error updating bed status: {e}")
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        if arguments is None:
            arguments = {}
        
        try:
            result = await self.tools[tool_name](**arguments)
            return {"result": result}
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tools.keys())


# Global server instance
_server_instance = None

def get_server() -> SimpleMCPServer:
    """Get or create server instance"""
    global _server_instance
    if _server_instance is None:
        _server_instance = SimpleMCPServer()
    return _server_instance


async def main():
    """Main function for testing"""
    server = get_server()
    
    # Test bed occupancy
    print("Testing bed occupancy...")
    result = await server.call_tool("get_bed_occupancy_status")
    print(json.dumps(result, indent=2))
    
    # Test available beds
    print("\nTesting available beds...")
    result = await server.call_tool("get_available_beds")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
