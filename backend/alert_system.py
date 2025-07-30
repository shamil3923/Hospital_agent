"""
Real-time Alert System for Hospital Management
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory
except ImportError:
    try:
        from database import SessionLocal, Bed, Patient, BedOccupancyHistory
    except ImportError:
        # Create mock classes if database not available
        class SessionLocal:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def query(self, *args): return MockQuery()

        class MockQuery:
            def filter(self, *args): return self
            def count(self): return 0
            def all(self): return []

        class Bed:
            pass
        class Patient:
            pass
        class BedOccupancyHistory:
            pass
from sqlalchemy import func

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Alert types for hospital management"""
    BED_AVAILABLE = "bed_available"
    DISCHARGE_UPCOMING = "discharge_upcoming"
    CAPACITY_CRITICAL = "capacity_critical"
    CLEANING_OVERDUE = "cleaning_overdue"
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"
    PATIENT_TRANSFER = "patient_transfer"
    STAFF_SHORTAGE = "staff_shortage"

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    department: str
    related_bed_id: Optional[int] = None
    related_patient_id: Optional[str] = None
    action_required: bool = False
    auto_resolve: bool = False
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    @property
    def timestamp(self):
        """Alias for created_at for backward compatibility"""
        return self.created_at

class RealTimeAlertSystem:
    """Real-time alert system for hospital management"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_subscribers: List = []
        self.monitoring_tasks: List = []
        self.running = False
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        if self.running:
            return
        
        self.running = True
        logger.info("🚨 Starting real-time alert monitoring...")
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._monitor_bed_availability()),
            asyncio.create_task(self._monitor_discharge_predictions()),
            asyncio.create_task(self._monitor_capacity_levels()),
            asyncio.create_task(self._monitor_cleaning_schedules()),
            asyncio.create_task(self._monitor_equipment_status()),
            asyncio.create_task(self._cleanup_expired_alerts())
        ]
        
        logger.info("✅ Alert monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        logger.info("🛑 Alert monitoring stopped")
    
    def subscribe_to_alerts(self, callback):
        """Subscribe to real-time alerts"""
        self.alert_subscribers.append(callback)
    
    def unsubscribe_from_alerts(self, callback):
        """Unsubscribe from alerts"""
        if callback in self.alert_subscribers:
            self.alert_subscribers.remove(callback)
    
    async def _notify_subscribers(self, alert: Alert):
        """Notify all subscribers of new alert"""
        alert_data = {
            "id": alert.id,
            "type": alert.type.value,
            "priority": alert.priority.value,
            "title": alert.title,
            "message": alert.message,
            "department": alert.department,
            "related_bed_id": alert.related_bed_id,
            "related_patient_id": alert.related_patient_id,
            "action_required": alert.action_required,
            "created_at": alert.created_at.isoformat(),
            "metadata": alert.metadata
        }
        
        # Notify all subscribers
        for callback in self.alert_subscribers:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def create_alert(self, alert: Alert) -> str:
        """Create and broadcast new alert with deduplication"""
        # Create unique ID based on type, department, and related resource
        base_id = f"{alert.type.value}_{alert.department}"
        if alert.related_bed_id:
            base_id += f"_bed_{alert.related_bed_id}"

        # Check if similar alert already exists (within last hour)
        current_time = datetime.now()
        for existing_id, existing_alert in list(self.active_alerts.items()):
            if (existing_id.startswith(base_id) and
                existing_alert.timestamp and
                (current_time - existing_alert.timestamp).total_seconds() < 3600):  # 1 hour
                logger.debug(f"Skipping duplicate alert: {base_id}")
                return existing_id

        # Create new alert
        alert.id = f"{base_id}_{int(current_time.timestamp())}"

        # Store alert
        self.active_alerts[alert.id] = alert
        
        # Notify subscribers
        await self._notify_subscribers(alert)
        
        logger.info(f"🚨 Alert created: {alert.title} ({alert.priority.value})")
        return alert.id
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            
            # Notify subscribers of resolution
            resolution_data = {
                "id": alert_id,
                "type": "alert_resolved",
                "resolved_at": datetime.now().isoformat()
            }
            
            for callback in self.alert_subscribers:
                try:
                    await callback(resolution_data)
                except Exception as e:
                    logger.error(f"Error notifying resolution: {e}")
            
            logger.info(f"✅ Alert resolved: {alert.title}")
    
    async def _monitor_bed_availability(self):
        """Monitor for bed availability changes"""
        while self.running:
            try:
                db = SessionLocal()
                
                # Check for beds that just became available
                recently_vacant = db.query(Bed).filter(
                    Bed.status == "vacant",
                    Bed.last_updated >= datetime.now() - timedelta(minutes=5)
                ).all()
                
                for bed in recently_vacant:
                    # Check if this is a high-demand bed type
                    if bed.bed_type in ["ICU", "Emergency"]:
                        alert = Alert(
                            id="",  # Will be set by create_alert
                            type=AlertType.BED_AVAILABLE,
                            priority=AlertPriority.HIGH,
                            title=f"{bed.bed_type} Bed Available",
                            message=f"Bed {bed.bed_number} in {bed.ward} is now available",
                            department=bed.ward,
                            related_bed_id=bed.id,
                            action_required=True,
                            auto_resolve=True,
                            expires_at=datetime.now() + timedelta(hours=1),
                            metadata={
                                "bed_number": bed.bed_number,
                                "bed_type": bed.bed_type,
                                "room_number": bed.room_number,
                                "private_room": bed.private_room
                            }
                        )
                        await self.create_alert(alert)
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error monitoring bed availability: {e}")
            
            await asyncio.sleep(120)  # Check every 2 minutes (reduced load)
    
    async def _monitor_discharge_predictions(self):
        """Monitor for upcoming discharges"""
        while self.running:
            try:
                db = SessionLocal()
                
                # Check for discharges in next 2 hours
                upcoming_discharges = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date.isnot(None),
                    Patient.expected_discharge_date >= datetime.now(),
                    Patient.expected_discharge_date <= datetime.now() + timedelta(hours=2)
                ).all()
                
                for patient in upcoming_discharges:
                    bed = db.query(Bed).filter(Bed.id == patient.current_bed_id).first()
                    if bed:
                        alert = Alert(
                            id="",  # Will be set by create_alert
                            type=AlertType.DISCHARGE_UPCOMING,
                            priority=AlertPriority.MEDIUM,
                            title="Discharge Preparation Needed",
                            message=f"Patient {patient.name} expected to discharge from {bed.bed_number} in {self._time_until(patient.expected_discharge_date)}",
                            department=bed.ward,
                            related_bed_id=bed.id,
                            related_patient_id=patient.patient_id,
                            action_required=True,
                            metadata={
                                "patient_name": patient.name,
                                "bed_number": bed.bed_number,
                                "expected_discharge": patient.expected_discharge_date.isoformat(),
                                "preparation_time": "30-45 minutes"
                            }
                        )
                        await self.create_alert(alert)
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error monitoring discharge predictions: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _monitor_capacity_levels(self):
        """Monitor hospital capacity levels"""
        while self.running:
            try:
                db = SessionLocal()
                
                # Check overall capacity
                total_beds = db.query(Bed).count()
                occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
                occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
                
                if occupancy_rate >= 95:
                    alert = Alert(
                        id="",  # Will be set by create_alert
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.CRITICAL,
                        title="Critical Capacity Reached",
                        message=f"Hospital at {occupancy_rate:.1f}% capacity. Immediate action required.",
                        department="all",
                        action_required=True,
                        metadata={
                            "occupancy_rate": occupancy_rate,
                            "total_beds": total_beds,
                            "occupied_beds": occupied_beds,
                            "available_beds": total_beds - occupied_beds
                        }
                    )
                    await self.create_alert(alert)
                
                elif occupancy_rate >= 90:
                    alert = Alert(
                        id="",  # Will be set by create_alert
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.HIGH,
                        title="High Capacity Warning",
                        message=f"Hospital at {occupancy_rate:.1f}% capacity. Monitor closely.",
                        department="all",
                        action_required=False,
                        metadata={
                            "occupancy_rate": occupancy_rate,
                            "total_beds": total_beds,
                            "occupied_beds": occupied_beds
                        }
                    )
                    await self.create_alert(alert)
                
                # Check ICU capacity specifically
                icu_total = db.query(Bed).filter(Bed.ward == "ICU").count()
                icu_occupied = db.query(Bed).filter(Bed.ward == "ICU", Bed.status == "occupied").count()
                icu_rate = (icu_occupied / icu_total * 100) if icu_total > 0 else 0
                
                if icu_rate >= 90:
                    # Check if we already have a recent ICU capacity alert
                    existing_alert = None
                    for alert_id, alert in self.active_alerts.items():
                        if (alert.type == AlertType.CAPACITY_CRITICAL and
                            alert.department == "ICU" and
                            "icu_occupancy_rate" in alert.metadata):
                            existing_alert = alert
                            break

                    # Only create new alert if no existing one or rate changed significantly
                    if not existing_alert or abs(existing_alert.metadata.get("icu_occupancy_rate", 0) - icu_rate) > 5:
                        alert = Alert(
                            id="",  # Will be set by create_alert
                            type=AlertType.CAPACITY_CRITICAL,
                            priority=AlertPriority.CRITICAL,
                            title="ICU Capacity Critical",
                            message=f"ICU at {icu_rate:.1f}% capacity ({icu_occupied}/{icu_total} beds). Immediate action required!",
                            department="ICU",
                            action_required=True,
                            metadata={
                                "icu_occupancy_rate": icu_rate,
                                "icu_total": icu_total,
                                "icu_occupied": icu_occupied,
                                "alert_type": "capacity_critical",
                                "recommended_actions": [
                                    "Review step-down candidates",
                                    "Contact overflow facilities",
                                    "Expedite discharges",
                                    "Activate surge protocols"
                                ]
                            }
                        )
                        await self.create_alert(alert)
                        logger.warning(f"🚨 ICU CRITICAL ALERT: {icu_rate:.1f}% occupancy ({icu_occupied}/{icu_total})")
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error monitoring capacity: {e}")
            
            await asyncio.sleep(120)  # Check every 2 minutes
    
    async def _monitor_cleaning_schedules(self):
        """Monitor bed cleaning schedules"""
        while self.running:
            try:
                db = SessionLocal()
                
                # Temporarily disabled to prevent spam - TODO: Fix bed status logic
                # Check for beds in cleaning status too long
                # cleaning_threshold = datetime.now() - timedelta(hours=2)
                # overdue_cleaning = db.query(Bed).filter(
                #     Bed.status == "cleaning",
                #     Bed.last_updated < cleaning_threshold
                # ).all()

                # Only create cleaning alerts for beds that actually need attention
                # for bed in overdue_cleaning[:5]:  # Limit to 5 alerts max
                #     alert = Alert(
                #         id="",  # Will be set by create_alert
                #         type=AlertType.CLEANING_OVERDUE,
                #         priority=AlertPriority.MEDIUM,
                #         title="Cleaning Overdue",
                #         message=f"Bed {bed.bed_number} has been in cleaning status for over 2 hours",
                #         department=bed.ward,
                #         related_bed_id=bed.id,
                #         action_required=True,
                #         metadata={
                #             "bed_number": bed.bed_number,
                #             "cleaning_started": bed.last_updated.isoformat() if bed.last_updated else None,
                #             "hours_overdue": (datetime.now() - bed.last_updated).total_seconds() / 3600 if bed.last_updated else 0
                #         }
                #     )
                #     await self.create_alert(alert)
                pass  # Temporarily disabled
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error monitoring cleaning schedules: {e}")
            
            await asyncio.sleep(600)  # Check every 10 minutes
    
    async def _monitor_equipment_status(self):
        """Monitor equipment maintenance schedules"""
        while self.running:
            try:
                # This would integrate with equipment management
                # For now, create sample alerts
                await asyncio.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring equipment: {e}")
    
    async def _cleanup_expired_alerts(self):
        """Clean up expired alerts"""
        while self.running:
            try:
                current_time = datetime.now()
                expired_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.expires_at and alert.expires_at <= current_time
                ]
                
                for alert_id in expired_alerts:
                    await self.resolve_alert(alert_id)
                
            except Exception as e:
                logger.error(f"Error cleaning up alerts: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    def _time_until(self, target_time: datetime) -> str:
        """Calculate human-readable time until target"""
        delta = target_time - datetime.now()
        
        if delta.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes} minutes"
        else:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours} hours"
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            {
                "id": alert.id,
                "type": alert.type.value,
                "priority": alert.priority.value,
                "title": alert.title,
                "message": alert.message,
                "department": alert.department,
                "related_bed_id": alert.related_bed_id,
                "related_patient_id": alert.related_patient_id,
                "action_required": alert.action_required,
                "created_at": alert.created_at.isoformat(),
                "metadata": alert.metadata
            }
            for alert in self.active_alerts.values()
        ]

    async def create_proactive_alerts(self):
        """Create proactive alerts for better hospital management"""
        try:
            # Import with fallback for different execution contexts
            try:
                from .database import SessionLocal, Bed, Patient
            except ImportError:
                try:
                    from database import SessionLocal, Bed, Patient
                except ImportError:
                    from backend.database import SessionLocal, Bed, Patient

            with SessionLocal() as db:
                # Alert 1: High-demand bed types
                icu_available = db.query(Bed).filter(
                    Bed.ward == "ICU",
                    Bed.status == "vacant"
                ).count()

                if icu_available <= 1:
                    alert = Alert(
                        id="",
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.HIGH,
                        title="ICU Beds Running Low",
                        message=f"Only {icu_available} ICU bed(s) available. Consider discharge planning.",
                        department="ICU",
                        action_required=True,
                        metadata={
                            "available_icu_beds": icu_available,
                            "alert_type": "proactive_capacity",
                            "suggested_actions": [
                                "Review ICU discharge candidates",
                                "Prepare step-down unit beds",
                                "Contact bed management team"
                            ]
                        }
                    )
                    await self.create_alert(alert)

                # Alert 2: Emergency department capacity
                emergency_occupied = db.query(Bed).filter(
                    Bed.ward == "Emergency",
                    Bed.status == "occupied"
                ).count()

                emergency_total = db.query(Bed).filter(Bed.ward == "Emergency").count()
                emergency_rate = (emergency_occupied / emergency_total * 100) if emergency_total > 0 else 0

                if emergency_rate >= 80:
                    alert = Alert(
                        id="",
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.HIGH,
                        title="Emergency Department Near Capacity",
                        message=f"Emergency department at {emergency_rate:.1f}% capacity. Prepare for overflow.",
                        department="Emergency",
                        action_required=True,
                        metadata={
                            "emergency_occupancy": emergency_rate,
                            "occupied_beds": emergency_occupied,
                            "total_beds": emergency_total,
                            "suggested_actions": [
                                "Expedite emergency discharges",
                                "Activate overflow protocols",
                                "Alert administration"
                            ]
                        }
                    )
                    await self.create_alert(alert)

                logger.info(f"Created proactive alerts for better hospital management")

        except Exception as e:
            logger.error(f"Error creating proactive alerts: {e}")

# Global alert system instance
alert_system = RealTimeAlertSystem()
