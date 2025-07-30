"""
Enhanced Alert System with Improved Reliability and Actions
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

try:
    from .database import SessionLocal, Bed, Patient, Department, Staff
except ImportError:
    try:
        from database import SessionLocal, Bed, Patient, Department, Staff
    except ImportError:
        from backend.database import SessionLocal, Bed, Patient, Department, Staff

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Alert types for hospital management"""
    BED_AVAILABLE = "bed_available"
    DISCHARGE_UPCOMING = "discharge_upcoming"
    CAPACITY_CRITICAL = "capacity_critical"
    CAPACITY_HIGH = "capacity_high"
    NO_BEDS_AVAILABLE = "no_beds_available"
    CLEANING_OVERDUE = "cleaning_overdue"
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"
    PATIENT_TRANSFER = "patient_transfer"
    STAFF_SHORTAGE = "staff_shortage"
    EMERGENCY_PROTOCOL = "emergency_protocol"

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"

@dataclass
class AlertAction:
    """Represents an action that can be taken for an alert"""
    id: str
    name: str
    description: str
    endpoint: str
    method: str = "POST"
    requires_confirmation: bool = False
    auto_executable: bool = False
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

@dataclass
class Alert:
    """Enhanced alert data structure with actions"""
    id: str
    type: AlertType
    priority: AlertPriority
    status: AlertStatus
    title: str
    message: str
    department: str
    related_bed_id: Optional[int] = None
    related_patient_id: Optional[str] = None
    action_required: bool = False
    auto_resolve: bool = False
    created_at: datetime = None
    updated_at: datetime = None
    expires_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    available_actions: List[AlertAction] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.available_actions is None:
            self.available_actions = []
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to strings
        result['type'] = self.type.value
        result['priority'] = self.priority.value
        result['status'] = self.status.value
        # Convert datetime objects to ISO strings
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
        if self.expires_at:
            result['expires_at'] = self.expires_at.isoformat()
        return result

class EnhancedAlertSystem:
    """Enhanced alert system with improved reliability and actions"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_subscribers: List[Callable] = []
        self.monitoring_tasks: List[asyncio.Task] = []
        self.running = False
        self.initialization_complete = False
        self.error_count = 0
        self.max_errors = 10
        
    async def initialize(self) -> bool:
        """Initialize the alert system with proper error handling"""
        try:
            logger.info("ALERT: Initializing Enhanced Alert System...")
            
            # Test database connection
            await self._test_database_connection()
            
            # Load existing alerts from database if needed
            await self._load_persistent_alerts()
            
            # Create default alert actions
            self._setup_default_actions()
            
            self.initialization_complete = True
            logger.info("SUCCESS: Enhanced Alert System initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Alert system initialization failed: {e}")
            self.initialization_complete = False
            return False
    
    async def _test_database_connection(self):
        """Test database connectivity"""
        try:
            with SessionLocal() as db:
                # Simple query to test connection
                bed_count = db.query(Bed).count()
                logger.info(f"ANALYTICS: Database connection verified: {bed_count} beds found")
        except Exception as e:
            logger.error(f"ERROR: Database connection test failed: {e}")
            raise
    
    async def _load_persistent_alerts(self):
        """Load any persistent alerts from database"""
        try:
            # For now, we'll start fresh each time
            # In production, you might want to persist alerts in database
            logger.info("INFO: Starting with fresh alert state")
        except Exception as e:
            logger.warning(f"WARNING: Could not load persistent alerts: {e}")
    
    def _setup_default_actions(self):
        """Setup default actions for different alert types"""
        self.default_actions = {
            AlertType.CAPACITY_CRITICAL: [
                AlertAction(
                    id="expedite_discharge",
                    name="Expedite Discharge",
                    description="Review and expedite discharge for stable patients",
                    endpoint="/api/alerts/actions/expedite-discharge",
                    requires_confirmation=True
                ),
                AlertAction(
                    id="activate_overflow",
                    name="Activate Overflow Protocol",
                    description="Activate overflow bed protocols",
                    endpoint="/api/alerts/actions/activate-overflow",
                    requires_confirmation=True
                ),
                AlertAction(
                    id="notify_administration",
                    name="Notify Administration",
                    description="Send urgent notification to hospital administration",
                    endpoint="/api/alerts/actions/notify-admin",
                    auto_executable=True
                )
            ],
            AlertType.BED_AVAILABLE: [
                AlertAction(
                    id="auto_assign",
                    name="Auto-Assign Patient",
                    description="Automatically assign waiting patient to available bed",
                    endpoint="/api/alerts/actions/auto-assign-bed",
                    auto_executable=True
                ),
                AlertAction(
                    id="notify_admissions",
                    name="Notify Admissions",
                    description="Notify admissions department of bed availability",
                    endpoint="/api/alerts/actions/notify-admissions",
                    auto_executable=True
                )
            ],
            AlertType.NO_BEDS_AVAILABLE: [
                AlertAction(
                    id="emergency_protocol",
                    name="Emergency Bed Protocol",
                    description="Activate emergency bed allocation protocol",
                    endpoint="/api/alerts/actions/emergency-protocol",
                    requires_confirmation=True
                ),
                AlertAction(
                    id="contact_other_facilities",
                    name="Contact Other Facilities",
                    description="Contact nearby hospitals for bed availability",
                    endpoint="/api/alerts/actions/contact-facilities",
                    requires_confirmation=False
                )
            ]
        }
    
    async def start_monitoring(self) -> bool:
        """Start real-time monitoring with improved error handling"""
        if not self.initialization_complete:
            logger.warning("WARNING: Alert system not initialized, attempting initialization...")
            if not await self.initialize():
                return False
        
        if self.running:
            logger.info("ℹ️ Alert monitoring already running")
            return True
        
        try:
            self.running = True
            self.error_count = 0
            
            logger.info("ALERT: Starting enhanced alert monitoring...")
            
            # Start monitoring tasks with individual error handling
            monitoring_functions = [
                self._monitor_bed_availability,
                self._monitor_capacity_levels,
                self._monitor_discharge_predictions,
                self._monitor_cleaning_schedules,
                self._monitor_equipment_status,
                self._cleanup_expired_alerts,
                self._auto_execute_actions
            ]
            
            self.monitoring_tasks = []
            for func in monitoring_functions:
                try:
                    task = asyncio.create_task(self._safe_monitor_wrapper(func))
                    self.monitoring_tasks.append(task)
                    logger.info(f"SUCCESS: Started monitoring task: {func.__name__}")
                except Exception as e:
                    logger.error(f"ERROR: Failed to start {func.__name__}: {e}")
            
            # Create initial alerts
            await self._create_initial_alerts()
            
            logger.info(f"SUCCESS: Alert monitoring started with {len(self.monitoring_tasks)} tasks")
            return True
            
        except Exception as e:
            logger.error(f"ERROR: Failed to start alert monitoring: {e}")
            self.running = False
            return False
    
    async def _safe_monitor_wrapper(self, monitor_func):
        """Wrapper for monitoring functions with error handling and recovery"""
        func_name = monitor_func.__name__
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                await monitor_func()
                consecutive_errors = 0  # Reset on success
                
            except Exception as e:
                consecutive_errors += 1
                self.error_count += 1
                
                logger.error(f"ERROR: Error in {func_name}: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"ERROR: {func_name} failed {consecutive_errors} times consecutively, stopping task")
                    break
                
                if self.error_count >= self.max_errors:
                    logger.error(f"ERROR: Too many errors ({self.error_count}), stopping alert system")
                    self.running = False
                    break
                
                # Exponential backoff for retries
                await asyncio.sleep(min(60, 2 ** consecutive_errors))
    
    async def _monitor_capacity_levels(self):
        """Enhanced capacity monitoring with better error handling"""
        while self.running:
            try:
                with SessionLocal() as db:
                    # Get all departments
                    departments = db.query(Department).all()
                    
                    for dept in departments:
                        try:
                            # Get department bed statistics
                            dept_beds = db.query(Bed).filter(Bed.ward == dept.name).all()
                            if not dept_beds:
                                continue
                                
                            total_beds = len(dept_beds)
                            occupied_beds = len([bed for bed in dept_beds if bed.status == "occupied"])
                            available_beds = len([bed for bed in dept_beds if bed.status == "vacant"])
                            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
                            
                            # Create alerts based on occupancy
                            await self._create_capacity_alert(dept.name, occupancy_rate, occupied_beds, total_beds, available_beds)
                            
                        except Exception as dept_error:
                            logger.error(f"Error processing department {dept.name}: {dept_error}")
                            continue
                
            except Exception as e:
                logger.error(f"Error in capacity monitoring: {e}")
                raise  # Re-raise to be handled by wrapper
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _create_capacity_alert(self, department: str, occupancy_rate: float, occupied: int, total: int, available: int):
        """Create capacity alerts with appropriate actions"""
        alert_id = f"capacity_{department.lower()}_{int(datetime.now().timestamp())}"
        
        # Check if similar alert already exists
        existing_alert = None
        for alert in self.active_alerts.values():
            if (alert.department == department and 
                alert.type in [AlertType.CAPACITY_CRITICAL, AlertType.CAPACITY_HIGH, AlertType.NO_BEDS_AVAILABLE] and
                alert.status == AlertStatus.ACTIVE):
                existing_alert = alert
                break
        
        # Critical capacity (≥90%)
        if occupancy_rate >= 90:
            if existing_alert and existing_alert.priority == AlertPriority.CRITICAL:
                return  # Don't duplicate critical alerts
                
            alert = Alert(
                id=alert_id,
                type=AlertType.CAPACITY_CRITICAL,
                priority=AlertPriority.CRITICAL,
                status=AlertStatus.ACTIVE,
                title=f"ALERT: CRITICAL: {department} at {occupancy_rate:.1f}% Capacity",
                message=f"{department} department at critical capacity ({occupied}/{total} beds). Immediate action required!",
                department=department,
                action_required=True,
                metadata={
                    "occupancy_rate": occupancy_rate,
                    "occupied_beds": occupied,
                    "total_beds": total,
                    "available_beds": available,
                    "threshold": "critical_90_percent"
                },
                available_actions=self.default_actions.get(AlertType.CAPACITY_CRITICAL, [])
            )
            
        # High capacity (80-89%)
        elif occupancy_rate >= 80:
            if existing_alert and existing_alert.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]:
                return
                
            alert = Alert(
                id=alert_id,
                type=AlertType.CAPACITY_HIGH,
                priority=AlertPriority.HIGH,
                status=AlertStatus.ACTIVE,
                title=f"WARNING: HIGH: {department} at {occupancy_rate:.1f}% Capacity",
                message=f"{department} department at high capacity ({occupied}/{total} beds). Monitor closely.",
                department=department,
                action_required=True,
                metadata={
                    "occupancy_rate": occupancy_rate,
                    "occupied_beds": occupied,
                    "total_beds": total,
                    "available_beds": available,
                    "threshold": "high_80_percent"
                },
                available_actions=[
                    AlertAction(
                        id="monitor_closely",
                        name="Monitor Closely",
                        description="Increase monitoring frequency for this department",
                        endpoint="/api/alerts/actions/monitor-closely",
                        auto_executable=True
                    )
                ]
            )
            
        # No beds available
        elif available == 0 and total > 0:
            alert = Alert(
                id=alert_id,
                type=AlertType.NO_BEDS_AVAILABLE,
                priority=AlertPriority.CRITICAL,
                status=AlertStatus.ACTIVE,
                title=f"BED: NO BEDS: {department}",
                message=f"{department} has no available beds ({occupied}/{total} occupied)",
                department=department,
                action_required=True,
                metadata={
                    "occupancy_rate": occupancy_rate,
                    "occupied_beds": occupied,
                    "total_beds": total,
                    "available_beds": 0
                },
                available_actions=self.default_actions.get(AlertType.NO_BEDS_AVAILABLE, [])
            )
        else:
            # Resolve existing alerts if capacity is normal
            if existing_alert:
                await self.resolve_alert(existing_alert.id, "system", "Capacity returned to normal levels")
            return
        
        # Create the alert
        await self.create_alert(alert)
    
    async def _monitor_bed_availability(self):
        """Monitor for newly available beds"""
        while self.running:
            try:
                with SessionLocal() as db:
                    # Check for beds that became available in the last 5 minutes
                    recent_time = datetime.now() - timedelta(minutes=5)
                    recently_vacant = db.query(Bed).filter(
                        Bed.status == "vacant",
                        Bed.last_updated >= recent_time
                    ).all()
                    
                    for bed in recently_vacant:
                        # Check if this is a high-demand bed type
                        if bed.ward in ["ICU", "Emergency"]:
                            alert = Alert(
                                id=f"bed_available_{bed.bed_number}_{int(datetime.now().timestamp())}",
                                type=AlertType.BED_AVAILABLE,
                                priority=AlertPriority.HIGH,
                                status=AlertStatus.ACTIVE,
                                title=f"BED: {bed.ward} Bed Available",
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
                                },
                                available_actions=self.default_actions.get(AlertType.BED_AVAILABLE, [])
                            )
                            await self.create_alert(alert)
                
            except Exception as e:
                logger.error(f"Error monitoring bed availability: {e}")
                raise
            
            await asyncio.sleep(120)  # Check every 2 minutes
    
    async def _monitor_discharge_predictions(self):
        """Monitor for upcoming discharges"""
        while self.running:
            try:
                with SessionLocal() as db:
                    # Check for discharges in next 2 hours
                    upcoming_time = datetime.now() + timedelta(hours=2)
                    upcoming_discharges = db.query(Patient).filter(
                        Patient.status == "admitted",
                        Patient.expected_discharge_date.isnot(None),
                        Patient.expected_discharge_date >= datetime.now(),
                        Patient.expected_discharge_date <= upcoming_time
                    ).all()
                    
                    for patient in upcoming_discharges:
                        if patient.current_bed_id:
                            bed = db.query(Bed).filter(Bed.id == patient.current_bed_id).first()
                            if bed:
                                time_until = patient.expected_discharge_date - datetime.now()
                                hours_until = time_until.total_seconds() / 3600
                                
                                alert = Alert(
                                    id=f"discharge_{patient.patient_id}_{int(datetime.now().timestamp())}",
                                    type=AlertType.DISCHARGE_UPCOMING,
                                    priority=AlertPriority.MEDIUM,
                                    status=AlertStatus.ACTIVE,
                                    title="INFO: Discharge Preparation Needed",
                                    message=f"Patient {patient.name} expected to discharge from {bed.bed_number} in {hours_until:.1f} hours",
                                    department=bed.ward,
                                    related_bed_id=bed.id,
                                    related_patient_id=patient.patient_id,
                                    action_required=True,
                                    metadata={
                                        "patient_name": patient.name,
                                        "bed_number": bed.bed_number,
                                        "expected_discharge": patient.expected_discharge_date.isoformat(),
                                        "hours_until": hours_until
                                    },
                                    available_actions=[
                                        AlertAction(
                                            id="prepare_discharge",
                                            name="Prepare Discharge",
                                            description="Start discharge preparation process",
                                            endpoint="/api/alerts/actions/prepare-discharge",
                                            parameters={"patient_id": patient.patient_id}
                                        )
                                    ]
                                )
                                await self.create_alert(alert)
                
            except Exception as e:
                logger.error(f"Error monitoring discharge predictions: {e}")
                raise
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _monitor_cleaning_schedules(self):
        """Monitor bed cleaning schedules"""
        while self.running:
            try:
                with SessionLocal() as db:
                    # Check for beds in cleaning status too long (>2 hours)
                    cleaning_threshold = datetime.now() - timedelta(hours=2)
                    overdue_cleaning = db.query(Bed).filter(
                        Bed.status == "cleaning",
                        Bed.last_updated < cleaning_threshold
                    ).all()
                    
                    for bed in overdue_cleaning[:5]:  # Limit to 5 alerts
                        hours_overdue = (datetime.now() - bed.last_updated).total_seconds() / 3600
                        
                        alert = Alert(
                            id=f"cleaning_overdue_{bed.bed_number}_{int(datetime.now().timestamp())}",
                            type=AlertType.CLEANING_OVERDUE,
                            priority=AlertPriority.MEDIUM,
                            status=AlertStatus.ACTIVE,
                            title="CLEANING: Cleaning Overdue",
                            message=f"Bed {bed.bed_number} has been in cleaning status for {hours_overdue:.1f} hours",
                            department=bed.ward,
                            related_bed_id=bed.id,
                            action_required=True,
                            metadata={
                                "bed_number": bed.bed_number,
                                "cleaning_started": bed.last_updated.isoformat(),
                                "hours_overdue": hours_overdue
                            },
                            available_actions=[
                                AlertAction(
                                    id="complete_cleaning",
                                    name="Mark Cleaning Complete",
                                    description="Mark bed cleaning as complete",
                                    endpoint=f"/api/beds/{bed.bed_number}/complete-cleaning",
                                    method="POST"
                                ),
                                AlertAction(
                                    id="notify_housekeeping",
                                    name="Notify Housekeeping",
                                    description="Send notification to housekeeping staff",
                                    endpoint="/api/alerts/actions/notify-housekeeping",
                                    parameters={"bed_id": bed.id}
                                )
                            ]
                        )
                        await self.create_alert(alert)
                
            except Exception as e:
                logger.error(f"Error monitoring cleaning schedules: {e}")
                raise
            
            await asyncio.sleep(600)  # Check every 10 minutes
    
    async def _monitor_equipment_status(self):
        """Monitor equipment maintenance schedules"""
        while self.running:
            try:
                # Placeholder for equipment monitoring
                # In a real system, this would check equipment maintenance schedules
                await asyncio.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring equipment: {e}")
                raise
    
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
                    await self.resolve_alert(alert_id, "system", "Alert expired")
                
            except Exception as e:
                logger.error(f"Error cleaning up alerts: {e}")
                raise
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _auto_execute_actions(self):
        """Auto-execute actions for alerts where appropriate"""
        while self.running:
            try:
                for alert in list(self.active_alerts.values()):
                    if alert.status == AlertStatus.ACTIVE:
                        for action in alert.available_actions:
                            if action.auto_executable and not action.requires_confirmation:
                                # Execute auto actions (implement based on your needs)
                                logger.info(f"AI: Auto-executing action {action.name} for alert {alert.id}")
                                # You would implement the actual action execution here
                
            except Exception as e:
                logger.error(f"Error in auto-execute actions: {e}")
                raise
            
            await asyncio.sleep(180)  # Check every 3 minutes
    
    async def _create_initial_alerts(self):
        """Create initial alerts for testing and immediate issues"""
        try:
            with SessionLocal() as db:
                # Check for immediate capacity issues
                departments = db.query(Department).all()
                
                for dept in departments:
                    dept_beds = db.query(Bed).filter(Bed.ward == dept.name).all()
                    if dept_beds:
                        occupied = len([bed for bed in dept_beds if bed.status == "occupied"])
                        total = len(dept_beds)
                        occupancy_rate = (occupied / total * 100) if total > 0 else 0
                        available = total - occupied
                        
                        await self._create_capacity_alert(dept.name, occupancy_rate, occupied, total, available)
                
                logger.info("SUCCESS: Initial alerts created")
                
        except Exception as e:
            logger.error(f"Error creating initial alerts: {e}")
    
    async def create_alert(self, alert: Alert) -> str:
        """Create and broadcast new alert with enhanced deduplication"""
        try:
            # Check for duplicate alerts
            for existing_id, existing_alert in list(self.active_alerts.items()):
                if (existing_alert.type == alert.type and
                    existing_alert.department == alert.department and
                    existing_alert.status == AlertStatus.ACTIVE and
                    existing_alert.related_bed_id == alert.related_bed_id):
                    
                    # Update existing alert instead of creating duplicate
                    existing_alert.updated_at = datetime.now()
                    existing_alert.message = alert.message
                    existing_alert.metadata.update(alert.metadata)
                    
                    await self._notify_subscribers(existing_alert)
                    logger.info(f"UPDATE: Updated existing alert: {existing_alert.title}")
                    return existing_id
            
            # Store new alert
            self.active_alerts[alert.id] = alert
            
            # Notify subscribers
            await self._notify_subscribers(alert)
            
            logger.info(f"ALERT: Alert created: {alert.title} ({alert.priority.value})")
            return alert.id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return ""
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system", reason: str = ""):
        """Resolve an active alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_by = resolved_by
                alert.updated_at = datetime.now()
                
                if reason:
                    alert.metadata["resolution_reason"] = reason
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                # Notify subscribers of resolution
                resolution_data = {
                    "type": "alert_resolved",
                    "alert_id": alert_id,
                    "resolved_by": resolved_by,
                    "reason": reason,
                    "resolved_at": datetime.now().isoformat()
                }
                
                await self._notify_subscribers_raw(resolution_data)
                logger.info(f"SUCCESS: Alert resolved: {alert.title} by {resolved_by}")
                
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = acknowledged_by
                alert.updated_at = datetime.now()
                
                await self._notify_subscribers(alert)
                logger.info(f"👍 Alert acknowledged: {alert.title} by {acknowledged_by}")
                
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
    
    async def execute_alert_action(self, alert_id: str, action_id: str, executed_by: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an action for an alert"""
        try:
            if alert_id not in self.active_alerts:
                return {"success": False, "error": "Alert not found"}
            
            alert = self.active_alerts[alert_id]
            action = None
            
            # Find the action
            for available_action in alert.available_actions:
                if available_action.id == action_id:
                    action = available_action
                    break
            
            if not action:
                return {"success": False, "error": "Action not found"}
            
            # Log action execution
            logger.info(f"TARGET: Executing action '{action.name}' for alert '{alert.title}' by {executed_by}")
            
            # Update alert status
            alert.status = AlertStatus.IN_PROGRESS
            alert.updated_at = datetime.now()
            alert.metadata["last_action"] = {
                "action_id": action_id,
                "action_name": action.name,
                "executed_by": executed_by,
                "executed_at": datetime.now().isoformat(),
                "parameters": parameters or {}
            }
            
            # Notify subscribers
            await self._notify_subscribers(alert)
            
            # Return success with action details
            return {
                "success": True,
                "action_executed": action.name,
                "alert_id": alert_id,
                "executed_by": executed_by,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing action {action_id} for alert {alert_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def subscribe_to_alerts(self, callback: Callable):
        """Subscribe to real-time alerts"""
        self.alert_subscribers.append(callback)
        logger.info(f"📡 New alert subscriber added. Total: {len(self.alert_subscribers)}")
    
    def unsubscribe_from_alerts(self, callback: Callable):
        """Unsubscribe from alerts"""
        if callback in self.alert_subscribers:
            self.alert_subscribers.remove(callback)
            logger.info(f"📡 Alert subscriber removed. Total: {len(self.alert_subscribers)}")
    
    async def _notify_subscribers(self, alert: Alert):
        """Notify all subscribers of alert update"""
        try:
            alert_data = alert.to_dict()
            await self._notify_subscribers_raw(alert_data)
        except Exception as e:
            logger.error(f"Error notifying subscribers: {e}")
    
    async def _notify_subscribers_raw(self, data: Dict[str, Any]):
        """Notify subscribers with raw data"""
        if not self.alert_subscribers:
            return
        
        for callback in self.alert_subscribers:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts as dictionaries"""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return self.active_alerts.get(alert_id)
    
    def get_alerts_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get alerts for specific department"""
        return [
            alert.to_dict() for alert in self.active_alerts.values()
            if alert.department.lower() == department.lower()
        ]
    
    def get_alerts_by_priority(self, priority: AlertPriority) -> List[Dict[str, Any]]:
        """Get alerts by priority level"""
        return [
            alert.to_dict() for alert in self.active_alerts.values()
            if alert.priority == priority
        ]
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        self.monitoring_tasks.clear()
        logger.info("🛑 Enhanced alert monitoring stopped")
    
    async def create_proactive_alerts(self):
        """Create proactive alerts for better hospital management"""
        try:
            with SessionLocal() as db:
                # Alert for ICU beds running low
                icu_beds = db.query(Bed).filter(Bed.ward == "ICU").all()
                icu_available = len([bed for bed in icu_beds if bed.status == "vacant"])
                
                if icu_available <= 1 and len(icu_beds) > 0:
                    alert = Alert(
                        id=f"proactive_icu_low_{int(datetime.now().timestamp())}",
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.HIGH,
                        status=AlertStatus.ACTIVE,
                        title="HOSPITAL: ICU Beds Running Low",
                        message=f"Only {icu_available} ICU bed(s) available. Consider discharge planning.",
                        department="ICU",
                        action_required=True,
                        metadata={
                            "available_icu_beds": icu_available,
                            "total_icu_beds": len(icu_beds),
                            "alert_type": "proactive_capacity",
                            "suggested_actions": [
                                "Review ICU discharge candidates",
                                "Prepare step-down unit beds",
                                "Contact bed management team"
                            ]
                        },
                        available_actions=self.default_actions.get(AlertType.CAPACITY_CRITICAL, [])
                    )
                    await self.create_alert(alert)
                
                # Alert for Emergency department capacity
                emergency_beds = db.query(Bed).filter(Bed.ward == "Emergency").all()
                if emergency_beds:
                    emergency_occupied = len([bed for bed in emergency_beds if bed.status == "occupied"])
                    emergency_total = len(emergency_beds)
                    emergency_rate = (emergency_occupied / emergency_total * 100)
                    
                    if emergency_rate >= 80:
                        alert = Alert(
                            id=f"proactive_emergency_high_{int(datetime.now().timestamp())}",
                            type=AlertType.CAPACITY_HIGH,
                            priority=AlertPriority.HIGH,
                            status=AlertStatus.ACTIVE,
                            title="ALERT: Emergency Department Near Capacity",
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
                            },
                            available_actions=[
                                AlertAction(
                                    id="activate_emergency_overflow",
                                    name="Activate Emergency Overflow",
                                    description="Activate emergency overflow protocols",
                                    endpoint="/api/alerts/actions/emergency-overflow",
                                    requires_confirmation=True
                                )
                            ]
                        )
                        await self.create_alert(alert)
                
                logger.info("SUCCESS: Proactive alerts created successfully")
                
        except Exception as e:
            logger.error(f"Error creating proactive alerts: {e}")

# Global enhanced alert system instance
enhanced_alert_system = EnhancedAlertSystem()