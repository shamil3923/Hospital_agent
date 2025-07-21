"""
Simple MCP Client for Hospital Agent
Provides a simplified interface to MCP tools
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class SimpleMCPToolsManager:
    """Simplified MCP tools manager that provides hospital data without requiring MCP server"""
    
    def __init__(self):
        self.initialized = False
        self.tools = {}
        
    async def initialize(self):
        """Initialize the MCP tools manager"""
        try:
            # Import hospital backend modules
            from backend.database import SessionLocal, Bed, Patient, BedOccupancyHistory
            self.SessionLocal = SessionLocal
            self.Bed = Bed
            self.Patient = Patient
            self.BedOccupancyHistory = BedOccupancyHistory
            
            self.initialized = True
            logger.info("SimpleMCPToolsManager initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import backend modules: {e}")
            self.initialized = False
            
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {"error": "MCP tools manager not initialized"}
            
        try:
            if tool_name == "get_bed_occupancy_status":
                return await self._get_bed_occupancy_status()
            elif tool_name == "get_available_beds":
                return await self._get_available_beds(**kwargs)
            elif tool_name == "get_critical_bed_alerts":
                return await self._get_critical_bed_alerts()
            elif tool_name == "get_patient_discharge_predictions":
                return await self._get_patient_discharge_predictions()
            elif tool_name == "update_bed_status":
                return await self._update_bed_status(**kwargs)
            elif tool_name == "assign_patient_to_bed":
                return await self._assign_patient_to_bed(**kwargs)
            elif tool_name == "create_patient_and_assign":
                return await self._create_patient_and_assign(**kwargs)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def _get_bed_occupancy_status(self) -> Dict[str, Any]:
        """Get current bed occupancy status"""
        try:
            db = self.SessionLocal()
            beds = db.query(self.Bed).all()
            
            total_beds = len(beds)
            occupied_beds = len([b for b in beds if b.status == 'occupied'])
            vacant_beds = len([b for b in beds if b.status == 'vacant'])
            cleaning_beds = len([b for b in beds if b.status == 'cleaning'])
            maintenance_beds = len([b for b in beds if b.status == 'maintenance'])
            
            # Ward breakdown
            wards = {}
            for bed in beds:
                ward = bed.ward or 'General'
                if ward not in wards:
                    wards[ward] = {'total': 0, 'occupied': 0, 'vacant': 0}
                wards[ward]['total'] += 1
                if bed.status == 'occupied':
                    wards[ward]['occupied'] += 1
                elif bed.status == 'vacant':
                    wards[ward]['vacant'] += 1
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            db.close()
            
            return {
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "cleaning_beds": cleaning_beds,
                "maintenance_beds": maintenance_beds,
                "occupancy_rate": round(occupancy_rate, 1),
                "ward_breakdown": wards,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting bed occupancy: {e}")
            return {"error": str(e)}
    
    async def _get_available_beds(self, ward: Optional[str] = None, bed_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available beds with optional filtering"""
        try:
            db = self.SessionLocal()
            query = db.query(self.Bed).filter(self.Bed.status == 'vacant')
            
            if ward:
                query = query.filter(self.Bed.ward.ilike(f'%{ward}%'))
            if bed_type:
                query = query.filter(self.Bed.bed_type.ilike(f'%{bed_type}%'))
            
            beds = query.all()
            
            result = []
            for bed in beds:
                result.append({
                    "bed_id": bed.id,
                    "bed_number": bed.bed_number,
                    "ward": bed.ward,
                    "bed_type": getattr(bed, 'bed_type', 'Standard'),
                    "status": bed.status,
                    "equipment": getattr(bed, 'equipment', 'Standard equipment'),
                    "last_cleaned": getattr(bed, 'last_cleaned', None)
                })
            
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting available beds: {e}")
            return []
    
    async def _get_critical_bed_alerts(self) -> List[Dict[str, Any]]:
        """Get critical bed management alerts"""
        try:
            db = self.SessionLocal()
            beds = db.query(self.Bed).all()
            
            alerts = []
            
            # Check capacity for all wards
            wards = {}
            for bed in beds:
                ward = bed.ward or 'General'
                if ward not in wards:
                    wards[ward] = {'total': 0, 'occupied': 0}
                wards[ward]['total'] += 1
                if bed.status == 'occupied':
                    wards[ward]['occupied'] += 1

            # Generate alerts for each ward at high capacity
            for ward_name, ward_stats in wards.items():
                ward_rate = (ward_stats['occupied'] / ward_stats['total'] * 100) if ward_stats['total'] > 0 else 0

                if ward_rate >= 90:
                    priority = "critical" if ward_rate >= 95 else "high"
                    alerts.append({
                        "type": "ward_capacity_critical",
                        "priority": priority,
                        "title": f"{ward_name} Capacity Critical",
                        "message": f"{ward_name} at {ward_rate:.1f}% capacity ({ward_stats['occupied']}/{ward_stats['total']} beds)",
                        "department": ward_name,
                        "action_required": True,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "ward": ward_name,
                            "occupancy_rate": ward_rate,
                            "occupied_beds": ward_stats['occupied'],
                            "total_beds": ward_stats['total']
                        }
                    })
            
            # Check overall capacity
            total_beds = len(beds)
            occupied_beds = len([b for b in beds if b.status == 'occupied'])
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            if occupancy_rate >= 85:
                alerts.append({
                    "type": "capacity_warning",
                    "priority": "high" if occupancy_rate >= 95 else "medium",
                    "title": "Hospital Capacity Alert",
                    "message": f"Hospital at {occupancy_rate:.1f}% capacity ({occupied_beds}/{total_beds} beds)",
                    "department": "Administration",
                    "action_required": True,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check beds needing maintenance
            maintenance_beds = [b for b in beds if b.status == 'maintenance']
            if len(maintenance_beds) > 2:
                alerts.append({
                    "type": "maintenance_alert",
                    "priority": "medium",
                    "title": "Multiple Beds Under Maintenance",
                    "message": f"{len(maintenance_beds)} beds currently under maintenance",
                    "department": "Maintenance",
                    "action_required": False,
                    "timestamp": datetime.now().isoformat()
                })
            
            db.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting critical alerts: {e}")
            return []
    
    async def _get_patient_discharge_predictions(self) -> List[Dict[str, Any]]:
        """Get predicted patient discharges using enhanced prediction logic"""
        try:
            db = self.SessionLocal()
            patients = db.query(self.Patient).filter(self.Patient.status == 'admitted').all()

            predictions = []
            for patient in patients:
                if patient.admission_date:
                    days_admitted = (datetime.now() - patient.admission_date).days

                    # Enhanced prediction logic based on hospital stay patterns
                    if days_admitted >= 2:  # Consider patients after 2+ days

                        # Base probability calculation
                        if days_admitted <= 3:
                            # Early stay: low probability
                            base_probability = 0.15
                            confidence = "low"
                            predicted_days = 2
                        elif days_admitted <= 5:
                            # Medium stay: moderate probability
                            base_probability = 0.45
                            confidence = "medium"
                            predicted_days = 1
                        elif days_admitted <= 7:
                            # Extended stay: high probability
                            base_probability = 0.70
                            confidence = "high"
                            predicted_days = 1
                        else:
                            # Long stay: very high probability
                            base_probability = 0.85
                            confidence = "high"
                            predicted_days = 1

                        # Adjust based on patient condition (simplified)
                        condition_factor = 1.0
                        if hasattr(patient, 'condition') and patient.condition:
                            condition = patient.condition.lower()
                            if 'critical' in condition or 'severe' in condition:
                                condition_factor = 0.7  # Lower discharge probability
                            elif 'stable' in condition or 'recovering' in condition:
                                condition_factor = 1.3  # Higher discharge probability

                        # Calculate final probability
                        final_probability = min(0.95, base_probability * condition_factor)

                        # Determine discharge readiness category
                        if final_probability >= 0.7:
                            readiness = "High - Ready for discharge planning"
                        elif final_probability >= 0.4:
                            readiness = "Medium - Monitor for discharge readiness"
                        else:
                            readiness = "Low - Continued care needed"

                        # Calculate predicted discharge date
                        predicted_discharge = datetime.now() + timedelta(days=predicted_days)

                        predictions.append({
                            "patient_id": patient.patient_id,
                            "patient_name": patient.name,
                            "admission_date": patient.admission_date.isoformat(),
                            "days_admitted": days_admitted,
                            "discharge_probability": round(final_probability, 2),
                            "predicted_discharge_date": predicted_discharge.isoformat(),
                            "confidence": confidence,
                            "readiness_category": readiness,
                            "factors": {
                                "length_of_stay": f"{days_admitted} days",
                                "base_probability": f"{base_probability:.1%}",
                                "condition_adjustment": f"{condition_factor:.1f}x",
                                "final_probability": f"{final_probability:.1%}"
                            },
                            "recommendations": self._get_discharge_recommendations(days_admitted, final_probability)
                        })

            # Sort by discharge probability (highest first)
            predictions.sort(key=lambda x: x['discharge_probability'], reverse=True)

            db.close()
            return predictions[:10]  # Return top 10 predictions

        except Exception as e:
            logger.error(f"Error getting discharge predictions: {e}")
            return []

    def _get_discharge_recommendations(self, days_admitted: int, probability: float) -> List[str]:
        """Get discharge planning recommendations based on prediction"""
        recommendations = []

        if probability >= 0.7:
            recommendations.extend([
                "Begin discharge planning process",
                "Coordinate with social services if needed",
                "Schedule follow-up appointments",
                "Prepare discharge medications"
            ])
        elif probability >= 0.4:
            recommendations.extend([
                "Monitor patient progress closely",
                "Assess discharge readiness daily",
                "Consider discharge planning preparation"
            ])
        else:
            recommendations.extend([
                "Continue current treatment plan",
                "Monitor for improvement",
                "Reassess in 24-48 hours"
            ])

        if days_admitted >= 7:
            recommendations.append("Review case for extended stay justification")

        return recommendations
    
    async def _update_bed_status(self, bed_number: str, new_status: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Update bed status"""
        try:
            db = self.SessionLocal()
            bed = db.query(self.Bed).filter(self.Bed.bed_number == bed_number).first()
            
            if not bed:
                db.close()
                return {"error": f"Bed {bed_number} not found"}
            
            old_status = bed.status
            bed.status = new_status
            
            if patient_id and hasattr(bed, 'patient_id'):
                bed.patient_id = patient_id
            
            db.commit()
            db.close()
            
            return {
                "success": True,
                "bed_number": bed_number,
                "old_status": old_status,
                "new_status": new_status,
                "patient_id": patient_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating bed status: {e}")
            return {"error": str(e)}
    
    async def _assign_patient_to_bed(self, patient_id: str, bed_number: str, doctor_id: Optional[str] = None) -> Dict[str, Any]:
        """Assign existing patient to a bed"""
        try:
            db = self.SessionLocal()

            # Find the bed
            bed = db.query(self.Bed).filter(self.Bed.bed_number == bed_number).first()
            if not bed:
                db.close()
                return {"error": f"Bed {bed_number} not found"}

            if bed.status != 'vacant':
                db.close()
                return {"error": f"Bed {bed_number} is not available (status: {bed.status})"}

            # Find the patient
            patient = db.query(self.Patient).filter(self.Patient.patient_id == patient_id).first()
            if not patient:
                db.close()
                return {"error": f"Patient {patient_id} not found"}

            # Update bed status
            bed.status = 'occupied'
            bed.patient_id = patient_id
            bed.last_updated = datetime.now()

            # Update patient status
            patient.current_bed_id = bed.id
            patient.status = 'admitted'
            if not patient.admission_date:
                patient.admission_date = datetime.now()

            # Create occupancy history record
            occupancy_record = self.BedOccupancyHistory(
                bed_id=bed.id,
                patient_id=patient_id,
                start_time=datetime.now(),
                status="occupied"
            )

            db.add(occupancy_record)
            db.commit()
            db.close()

            return {
                "success": True,
                "message": f"Patient {patient_id} successfully assigned to bed {bed_number}",
                "patient_id": patient_id,
                "patient_name": patient.name,
                "bed_number": bed_number,
                "bed_id": bed.id,
                "ward": bed.ward,
                "assignment_time": datetime.now().isoformat(),
                "doctor_id": doctor_id
            }

        except Exception as e:
            logger.error(f"Error assigning patient to bed: {e}")
            return {"error": str(e)}

    async def _create_patient_and_assign(self, patient_name: str, bed_number: str,
                                       age: Optional[int] = None, gender: Optional[str] = None,
                                       condition: Optional[str] = None, doctor_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new patient and assign them to a bed"""
        try:
            db = self.SessionLocal()

            # Find the bed
            bed = db.query(self.Bed).filter(self.Bed.bed_number == bed_number).first()
            if not bed:
                db.close()
                return {"error": f"Bed {bed_number} not found"}

            if bed.status != 'vacant':
                db.close()
                return {"error": f"Bed {bed_number} is not available (status: {bed.status})"}

            # Generate patient ID
            patient_id = f"PAT{int(datetime.now().timestamp())}"

            # Create new patient
            patient = self.Patient(
                patient_id=patient_id,
                name=patient_name,
                age=age,
                gender=gender,
                admission_date=datetime.now(),
                status='admitted',
                current_bed_id=bed.id,
                primary_condition=condition or 'General admission',  # Provide default
                severity='stable',  # Provide default
                isolation_required=False,  # Provide default
                dnr_status=False  # Provide default
            )

            # Update bed status
            bed.status = 'occupied'
            bed.patient_id = patient_id
            bed.last_updated = datetime.now()

            # Create occupancy history record
            occupancy_record = self.BedOccupancyHistory(
                bed_id=bed.id,
                patient_id=patient_id,
                start_time=datetime.now(),
                status="occupied"
            )

            db.add(patient)
            db.add(occupancy_record)
            db.commit()

            result = {
                "success": True,
                "message": f"Patient {patient_name} successfully created and assigned to bed {bed_number}",
                "patient_id": patient_id,
                "patient_name": patient_name,
                "bed_number": bed_number,
                "bed_id": bed.id,
                "ward": bed.ward,
                "assignment_time": datetime.now().isoformat(),
                "doctor_id": doctor_id
            }

            db.close()
            return result

        except Exception as e:
            logger.error(f"Error creating patient and assigning to bed: {e}")
            return {"error": str(e)}

    async def cleanup(self):
        """Cleanup resources"""
        self.initialized = False
        logger.info("SimpleMCPToolsManager cleaned up")
