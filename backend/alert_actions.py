"""
Alert Action Handlers for Hospital Management System
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

try:
    from .database import SessionLocal, Bed, Patient, Department, Staff, BedOccupancyHistory
    from .enhanced_alert_system import enhanced_alert_system
except ImportError:
    try:
        from database import SessionLocal, Bed, Patient, Department, Staff, BedOccupancyHistory
        from enhanced_alert_system import enhanced_alert_system
    except ImportError:
        from backend.database import SessionLocal, Bed, Patient, Department, Staff, BedOccupancyHistory
        from backend.enhanced_alert_system import enhanced_alert_system

logger = logging.getLogger(__name__)

class AlertActionHandler:
    """Handles execution of alert actions"""
    
    def __init__(self):
        self.action_handlers = {
            "expedite_discharge": self.expedite_discharge,
            "activate_overflow": self.activate_overflow_protocol,
            "notify_administration": self.notify_administration,
            "auto_assign": self.auto_assign_bed,
            "notify_admissions": self.notify_admissions,
            "emergency_protocol": self.emergency_bed_protocol,
            "contact_other_facilities": self.contact_other_facilities,
            "complete_cleaning": self.complete_cleaning,
            "notify_housekeeping": self.notify_housekeeping,
            "prepare_discharge": self.prepare_discharge,
            "monitor_closely": self.monitor_closely,
            "activate_emergency_overflow": self.activate_emergency_overflow
        }
    
    async def execute_action(self, action_id: str, alert_id: str, parameters: Dict[str, Any] = None, executed_by: str = "system") -> Dict[str, Any]:
        """Execute an alert action"""
        try:
            if action_id not in self.action_handlers:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_id}",
                    "action_id": action_id
                }
            
            handler = self.action_handlers[action_id]
            result = await handler(alert_id, parameters or {}, executed_by)
            
            # Log the action execution
            logger.info(f"🎯 Action '{action_id}' executed for alert '{alert_id}' by {executed_by}")
            
            return {
                "success": True,
                "action_id": action_id,
                "alert_id": alert_id,
                "executed_by": executed_by,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing action '{action_id}': {e}")
            return {
                "success": False,
                "error": str(e),
                "action_id": action_id,
                "alert_id": alert_id
            }
    
    async def expedite_discharge(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Expedite discharge for stable patients in high-capacity departments"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            department = alert.department
            
            with SessionLocal() as db:
                # Find patients in the department who are stable and could be discharged
                dept_beds = db.query(Bed).filter(
                    Bed.ward == department,
                    Bed.status == "occupied"
                ).all()
                
                discharge_candidates = []
                for bed in dept_beds:
                    if bed.patient_id:
                        patient = db.query(Patient).filter(Patient.patient_id == bed.patient_id).first()
                        if patient and patient.severity in ["stable", "improving"]:
                            # Check if patient has been there for more than 2 days
                            if patient.admission_date and (datetime.now() - patient.admission_date).days >= 2:
                                discharge_candidates.append({
                                    "patient_id": patient.patient_id,
                                    "patient_name": patient.name,
                                    "bed_number": bed.bed_number,
                                    "admission_date": patient.admission_date.isoformat(),
                                    "condition": patient.primary_condition,
                                    "severity": patient.severity
                                })
                
                # Update expected discharge dates for candidates
                for candidate in discharge_candidates[:3]:  # Limit to top 3
                    patient = db.query(Patient).filter(Patient.patient_id == candidate["patient_id"]).first()
                    if patient:
                        # Set discharge for tomorrow if not already set
                        if not patient.expected_discharge_date or patient.expected_discharge_date > datetime.now() + timedelta(days=1):
                            patient.expected_discharge_date = datetime.now() + timedelta(days=1)
                
                db.commit()
                
                return {
                    "message": f"Expedited discharge for {len(discharge_candidates[:3])} patients in {department}",
                    "discharge_candidates": discharge_candidates[:3],
                    "department": department
                }
                
        except Exception as e:
            logger.error(f"Error in expedite_discharge: {e}")
            return {"error": str(e)}
    
    async def activate_overflow_protocol(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Activate overflow bed protocols"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            department = alert.department
            
            with SessionLocal() as db:
                # Find beds that could be converted to overflow
                potential_overflow = db.query(Bed).filter(
                    Bed.status == "maintenance",
                    Bed.ward != department
                ).limit(5).all()
                
                overflow_beds = []
                for bed in potential_overflow:
                    # Convert maintenance beds to available if safe
                    bed.status = "vacant"
                    bed.last_updated = datetime.now()
                    overflow_beds.append({
                        "bed_number": bed.bed_number,
                        "ward": bed.ward,
                        "room_number": bed.room_number
                    })
                
                db.commit()
                
                return {
                    "message": f"Activated overflow protocol for {department}",
                    "overflow_beds_activated": len(overflow_beds),
                    "beds": overflow_beds,
                    "department": department
                }
                
        except Exception as e:
            logger.error(f"Error in activate_overflow_protocol: {e}")
            return {"error": str(e)}
    
    async def notify_administration(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Send notification to hospital administration"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            # In a real system, this would send emails/SMS to administrators
            notification_message = f"""
            URGENT HOSPITAL ALERT
            
            Alert: {alert.title}
            Department: {alert.department}
            Priority: {alert.priority.value.upper()}
            
            Message: {alert.message}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Triggered by: {executed_by}
            
            Please take immediate action.
            """
            
            # Log the notification (in real system, send via email/SMS)
            logger.warning(f"🚨 ADMIN NOTIFICATION: {alert.title}")
            
            return {
                "message": "Administration notified successfully",
                "notification_sent": True,
                "alert_title": alert.title,
                "department": alert.department,
                "priority": alert.priority.value
            }
            
        except Exception as e:
            logger.error(f"Error in notify_administration: {e}")
            return {"error": str(e)}
    
    async def auto_assign_bed(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Automatically assign waiting patient to available bed"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert or not alert.related_bed_id:
                return {"error": "Alert or bed not found"}
            
            with SessionLocal() as db:
                # Get the available bed
                bed = db.query(Bed).filter(Bed.id == alert.related_bed_id).first()
                if not bed or bed.status != "vacant":
                    return {"error": "Bed is no longer available"}
                
                # Find a waiting patient suitable for this bed type/ward
                waiting_patients = db.query(Patient).filter(
                    Patient.status == "pending_assignment",
                    Patient.current_bed_id.is_(None)
                ).order_by(Patient.admission_date).all()
                
                suitable_patient = None
                for patient in waiting_patients:
                    # Simple matching logic - in real system, this would be more sophisticated
                    if bed.ward == "ICU" and patient.severity in ["critical", "serious"]:
                        suitable_patient = patient
                        break
                    elif bed.ward == "Emergency" and patient.severity in ["urgent", "serious"]:
                        suitable_patient = patient
                        break
                    elif bed.ward in ["General", "Medical"] and patient.severity in ["stable", "improving"]:
                        suitable_patient = patient
                        break
                
                if suitable_patient:
                    # Assign patient to bed
                    bed.status = "occupied"
                    bed.patient_id = suitable_patient.patient_id
                    bed.last_updated = datetime.now()
                    
                    suitable_patient.current_bed_id = bed.id
                    suitable_patient.status = "admitted"
                    
                    # Create occupancy history
                    occupancy_record = BedOccupancyHistory(
                        bed_id=bed.id,
                        patient_id=suitable_patient.patient_id,
                        start_time=datetime.now(),
                        status="occupied",
                        assigned_by=executed_by
                    )
                    db.add(occupancy_record)
                    db.commit()
                    
                    return {
                        "message": f"Patient {suitable_patient.name} auto-assigned to bed {bed.bed_number}",
                        "patient_name": suitable_patient.name,
                        "patient_id": suitable_patient.patient_id,
                        "bed_number": bed.bed_number,
                        "ward": bed.ward
                    }
                else:
                    return {
                        "message": "No suitable waiting patients found for this bed",
                        "bed_number": bed.bed_number,
                        "ward": bed.ward
                    }
                
        except Exception as e:
            logger.error(f"Error in auto_assign_bed: {e}")
            return {"error": str(e)}
    
    async def notify_admissions(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Notify admissions department of bed availability"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            # In real system, this would send notification to admissions staff
            logger.info(f"📢 ADMISSIONS NOTIFICATION: Bed available in {alert.department}")
            
            return {
                "message": "Admissions department notified of bed availability",
                "department": alert.department,
                "notification_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error in notify_admissions: {e}")
            return {"error": str(e)}
    
    async def emergency_bed_protocol(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Activate emergency bed allocation protocol"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            department = alert.department
            
            with SessionLocal() as db:
                # Emergency protocol: Convert some cleaning/maintenance beds to available
                emergency_beds = db.query(Bed).filter(
                    Bed.ward == department,
                    Bed.status.in_(["cleaning", "maintenance"])
                ).limit(3).all()
                
                activated_beds = []
                for bed in emergency_beds:
                    bed.status = "vacant"
                    bed.last_updated = datetime.now()
                    activated_beds.append({
                        "bed_number": bed.bed_number,
                        "room_number": bed.room_number,
                        "previous_status": bed.status
                    })
                
                db.commit()
                
                return {
                    "message": f"Emergency bed protocol activated for {department}",
                    "emergency_beds_activated": len(activated_beds),
                    "beds": activated_beds,
                    "department": department
                }
                
        except Exception as e:
            logger.error(f"Error in emergency_bed_protocol: {e}")
            return {"error": str(e)}
    
    async def contact_other_facilities(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Contact other healthcare facilities for bed availability"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            # Mock data for other facilities (in real system, this would query external APIs)
            nearby_facilities = [
                {"name": "City General Hospital", "distance": "2.3 miles", "available_beds": 5},
                {"name": "Regional Medical Center", "distance": "4.1 miles", "available_beds": 12},
                {"name": "Community Hospital", "distance": "6.8 miles", "available_beds": 3}
            ]
            
            logger.info(f"📞 Contacting other facilities for {alert.department} bed availability")
            
            return {
                "message": "Contacted nearby facilities for bed availability",
                "facilities_contacted": len(nearby_facilities),
                "facilities": nearby_facilities,
                "department": alert.department
            }
            
        except Exception as e:
            logger.error(f"Error in contact_other_facilities: {e}")
            return {"error": str(e)}
    
    async def complete_cleaning(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Mark bed cleaning as complete"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert or not alert.related_bed_id:
                return {"error": "Alert or bed not found"}
            
            with SessionLocal() as db:
                bed = db.query(Bed).filter(Bed.id == alert.related_bed_id).first()
                if not bed:
                    return {"error": "Bed not found"}
                
                bed.status = "vacant"
                bed.last_cleaned = datetime.now()
                bed.last_updated = datetime.now()
                db.commit()
                
                # Resolve the cleaning alert
                await enhanced_alert_system.resolve_alert(alert_id, executed_by, "Cleaning completed")
                
                return {
                    "message": f"Bed {bed.bed_number} cleaning completed",
                    "bed_number": bed.bed_number,
                    "ward": bed.ward,
                    "status": "vacant"
                }
                
        except Exception as e:
            logger.error(f"Error in complete_cleaning: {e}")
            return {"error": str(e)}
    
    async def notify_housekeeping(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Notify housekeeping staff"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            bed_id = parameters.get("bed_id") or alert.related_bed_id
            
            with SessionLocal() as db:
                bed = db.query(Bed).filter(Bed.id == bed_id).first()
                if bed:
                    logger.info(f"🧹 HOUSEKEEPING NOTIFICATION: Bed {bed.bed_number} needs attention")
                    
                    return {
                        "message": f"Housekeeping notified for bed {bed.bed_number}",
                        "bed_number": bed.bed_number,
                        "ward": bed.ward,
                        "notification_sent": True
                    }
                else:
                    return {"error": "Bed not found"}
                
        except Exception as e:
            logger.error(f"Error in notify_housekeeping: {e}")
            return {"error": str(e)}
    
    async def prepare_discharge(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Start discharge preparation process"""
        try:
            patient_id = parameters.get("patient_id")
            if not patient_id:
                return {"error": "Patient ID required"}
            
            with SessionLocal() as db:
                patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
                if not patient:
                    return {"error": "Patient not found"}
                
                # Create discharge preparation checklist
                discharge_checklist = [
                    "Medical clearance from attending physician",
                    "Medication reconciliation completed",
                    "Discharge instructions prepared",
                    "Follow-up appointments scheduled",
                    "Transportation arrangements confirmed",
                    "Home care services arranged (if needed)"
                ]
                
                logger.info(f"📋 Discharge preparation started for patient {patient.name}")
                
                return {
                    "message": f"Discharge preparation started for {patient.name}",
                    "patient_name": patient.name,
                    "patient_id": patient_id,
                    "checklist": discharge_checklist,
                    "expected_discharge": patient.expected_discharge_date.isoformat() if patient.expected_discharge_date else None
                }
                
        except Exception as e:
            logger.error(f"Error in prepare_discharge: {e}")
            return {"error": str(e)}
    
    async def monitor_closely(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Increase monitoring frequency for department"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            department = alert.department
            
            # In real system, this would adjust monitoring parameters
            logger.info(f"👁️ Increased monitoring activated for {department}")
            
            return {
                "message": f"Increased monitoring activated for {department}",
                "department": department,
                "monitoring_frequency": "Every 15 minutes",
                "duration": "Next 4 hours"
            }
            
        except Exception as e:
            logger.error(f"Error in monitor_closely: {e}")
            return {"error": str(e)}
    
    async def activate_emergency_overflow(self, alert_id: str, parameters: Dict[str, Any], executed_by: str) -> Dict[str, Any]:
        """Activate emergency overflow protocols"""
        try:
            alert = enhanced_alert_system.get_alert_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}
            
            # Emergency overflow protocol
            logger.warning(f"🚨 EMERGENCY OVERFLOW ACTIVATED for {alert.department}")
            
            return {
                "message": f"Emergency overflow protocol activated for {alert.department}",
                "department": alert.department,
                "protocol_level": "Emergency",
                "additional_capacity": "10-15 beds",
                "estimated_setup_time": "30-45 minutes"
            }
            
        except Exception as e:
            logger.error(f"Error in activate_emergency_overflow: {e}")
            return {"error": str(e)}

# Global alert action handler instance
alert_action_handler = AlertActionHandler()