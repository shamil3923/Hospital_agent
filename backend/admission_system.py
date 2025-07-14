"""
Patient Admission Process System
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from database import SessionLocal, Bed, Patient, BedOccupancyHistory, Staff, Department
from workflow_engine import workflow_engine
from alert_system import alert_system, Alert, AlertType, AlertPriority

logger = logging.getLogger(__name__)

class AdmissionType(Enum):
    """Types of hospital admissions"""
    EMERGENCY = "emergency"
    SCHEDULED = "scheduled"
    TRANSFER = "transfer"
    OBSERVATION = "observation"

class AdmissionPriority(Enum):
    """Admission priority levels"""
    CRITICAL = "critical"  # Life-threatening, immediate
    URGENT = "urgent"      # Serious, within 1 hour
    SEMI_URGENT = "semi_urgent"  # Within 4 hours
    ROUTINE = "routine"    # Scheduled, non-urgent

@dataclass
class AdmissionRequest:
    """Patient admission request"""
    patient_id: str
    patient_name: str
    age: int
    gender: str
    admission_type: AdmissionType
    priority: AdmissionPriority
    primary_condition: str
    secondary_conditions: List[str]
    allergies: List[str]
    medications: List[str]
    attending_physician: str
    requested_ward: Optional[str] = None
    bed_requirements: Dict[str, Any] = None
    insurance_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    special_needs: List[str] = None
    estimated_los: Optional[int] = None  # Length of stay in days
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.bed_requirements is None:
            self.bed_requirements = {}
        if self.special_needs is None:
            self.special_needs = []

class AdmissionSystem:
    """Intelligent patient admission system"""
    
    def __init__(self):
        self.pending_admissions: Dict[str, AdmissionRequest] = {}
        self.admission_queue: List[str] = []  # Ordered by priority
        self.running = False
        self.processing_tasks: List = []
    
    async def start_system(self):
        """Start the admission system"""
        if self.running:
            return
        
        self.running = True
        logger.info("🏥 Starting admission system...")
        
        # Start processing tasks
        self.processing_tasks = [
            asyncio.create_task(self._process_admission_queue()),
            asyncio.create_task(self._monitor_admission_timeouts()),
            asyncio.create_task(self._capacity_management())
        ]
        
        logger.info("✅ Admission system started")
    
    async def stop_system(self):
        """Stop the admission system"""
        self.running = False
        
        # Cancel all processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        self.processing_tasks.clear()
        
        logger.info("🛑 Admission system stopped")
    
    async def submit_admission_request(self, request: AdmissionRequest) -> str:
        """Submit a new admission request"""
        try:
            # Generate unique request ID
            request_id = f"ADM_{request.patient_id}_{int(datetime.now().timestamp())}"
            
            # Validate request
            validation_result = await self._validate_admission_request(request)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid admission request: {validation_result['errors']}")
            
            # Determine bed requirements based on condition and priority
            await self._determine_bed_requirements(request)
            
            # Add to pending admissions
            self.pending_admissions[request_id] = request
            
            # Add to priority queue
            self._add_to_queue(request_id)
            
            # Create admission alert
            if alert_system:
                alert = Alert(
                    type=AlertType.PATIENT_TRANSFER,
                    priority=self._map_admission_priority_to_alert(request.priority),
                    title=f"New {request.admission_type.value.title()} Admission",
                    message=f"Patient {request.patient_name} ({request.patient_id}) - {request.primary_condition}",
                    department=request.requested_ward or "Admissions",
                    related_patient_id=request.patient_id,
                    action_required=True,
                    metadata={
                        "admission_type": request.admission_type.value,
                        "priority": request.priority.value,
                        "condition": request.primary_condition,
                        "physician": request.attending_physician
                    }
                )
                await alert_system.create_alert(alert)
            
            logger.info(f"📝 Admission request submitted: {request.patient_name} ({request_id})")
            return request_id
            
        except Exception as e:
            logger.error(f"Error submitting admission request: {e}")
            raise
    
    async def _validate_admission_request(self, request: AdmissionRequest) -> Dict[str, Any]:
        """Validate admission request"""
        errors = []
        
        # Required fields
        if not request.patient_id:
            errors.append("Patient ID is required")
        if not request.patient_name:
            errors.append("Patient name is required")
        if not request.primary_condition:
            errors.append("Primary condition is required")
        if not request.attending_physician:
            errors.append("Attending physician is required")
        
        # Age validation
        if request.age < 0 or request.age > 150:
            errors.append("Invalid age")
        
        # Check for duplicate patient
        db = SessionLocal()
        existing_patient = db.query(Patient).filter(
            Patient.patient_id == request.patient_id,
            Patient.status == "admitted"
        ).first()
        
        if existing_patient:
            errors.append("Patient is already admitted")
        
        db.close()
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _determine_bed_requirements(self, request: AdmissionRequest):
        """Determine bed requirements based on patient condition"""
        # Default requirements
        requirements = {
            "isolation_required": False,
            "private_room": False,
            "equipment_needed": []
        }
        
        # Determine ward based on condition and priority
        if request.priority == AdmissionPriority.CRITICAL:
            if not request.requested_ward:
                request.requested_ward = "ICU"
            requirements["private_room"] = True
            requirements["equipment_needed"] = ["cardiac_monitor", "ventilator", "defibrillator"]
        
        elif "cardiac" in request.primary_condition.lower():
            if not request.requested_ward:
                request.requested_ward = "ICU"
            requirements["equipment_needed"] = ["cardiac_monitor", "defibrillator"]
        
        elif "respiratory" in request.primary_condition.lower():
            requirements["equipment_needed"] = ["oxygen", "ventilator"]
        
        elif "infectious" in request.primary_condition.lower() or "covid" in request.primary_condition.lower():
            requirements["isolation_required"] = True
            requirements["private_room"] = True
        
        elif request.age < 18:
            if not request.requested_ward:
                request.requested_ward = "Pediatric"
        
        elif "maternity" in request.primary_condition.lower() or "obstetric" in request.primary_condition.lower():
            if not request.requested_ward:
                request.requested_ward = "Maternity"
        
        # Emergency cases
        if request.admission_type == AdmissionType.EMERGENCY:
            if not request.requested_ward:
                request.requested_ward = "Emergency"
        
        # Default to General ward if not specified
        if not request.requested_ward:
            request.requested_ward = "General"
        
        # Update bed requirements
        request.bed_requirements.update(requirements)
        
        logger.info(f"🎯 Determined bed requirements for {request.patient_name}: Ward={request.requested_ward}, Requirements={requirements}")
    
    def _add_to_queue(self, request_id: str):
        """Add admission request to priority queue"""
        request = self.pending_admissions[request_id]
        
        # Find insertion point based on priority
        priority_order = [
            AdmissionPriority.CRITICAL,
            AdmissionPriority.URGENT,
            AdmissionPriority.SEMI_URGENT,
            AdmissionPriority.ROUTINE
        ]
        
        insertion_index = len(self.admission_queue)
        
        for i, existing_id in enumerate(self.admission_queue):
            existing_request = self.pending_admissions[existing_id]
            existing_priority_index = priority_order.index(existing_request.priority)
            new_priority_index = priority_order.index(request.priority)
            
            if new_priority_index < existing_priority_index:
                insertion_index = i
                break
            elif new_priority_index == existing_priority_index:
                # Same priority, order by creation time
                if request.created_at < existing_request.created_at:
                    insertion_index = i
                    break
        
        self.admission_queue.insert(insertion_index, request_id)
        logger.info(f"📋 Added to admission queue at position {insertion_index + 1}: {request.patient_name}")
    
    async def _process_admission_queue(self):
        """Process admission requests in priority order"""
        while self.running:
            try:
                if self.admission_queue:
                    request_id = self.admission_queue[0]
                    request = self.pending_admissions[request_id]
                    
                    # Check if bed is available
                    bed_available = await self._check_bed_availability(request)
                    
                    if bed_available:
                        # Process admission
                        success = await self._process_admission(request_id)
                        
                        if success:
                            # Remove from queue and pending
                            self.admission_queue.pop(0)
                            del self.pending_admissions[request_id]
                        else:
                            # Move to end of queue for retry
                            self.admission_queue.append(self.admission_queue.pop(0))
                    else:
                        # No bed available, check capacity management
                        await self._handle_no_bed_available(request)
                
            except Exception as e:
                logger.error(f"Error processing admission queue: {e}")
            
            await asyncio.sleep(10)  # Process every 10 seconds
    
    async def _check_bed_availability(self, request: AdmissionRequest) -> bool:
        """Check if suitable bed is available"""
        try:
            db = SessionLocal()
            
            # Build query for suitable beds
            query = db.query(Bed).filter(Bed.status == "vacant")
            
            if request.requested_ward:
                query = query.filter(Bed.ward == request.requested_ward)
            
            if request.bed_requirements.get("isolation_required"):
                query = query.filter(Bed.isolation_required == True)
            
            if request.bed_requirements.get("private_room"):
                query = query.filter(Bed.private_room == True)
            
            available_beds = query.all()
            db.close()
            
            return len(available_beds) > 0
            
        except Exception as e:
            logger.error(f"Error checking bed availability: {e}")
            return False
    
    async def _process_admission(self, request_id: str) -> bool:
        """Process a single admission"""
        try:
            request = self.pending_admissions[request_id]
            
            # Create patient record
            patient_created = await self._create_patient_record(request)
            if not patient_created:
                return False
            
            # Start bed assignment workflow
            workflow_id = await workflow_engine.create_workflow(
                "bed_assignment",
                {
                    "patient_id": request.patient_id,
                    "bed_requirements": request.bed_requirements
                }
            )
            
            # Create admission workflow
            admission_workflow_id = await self._create_admission_workflow(request)
            
            logger.info(f"✅ Admission processed: {request.patient_name} (Workflows: {workflow_id}, {admission_workflow_id})")
            
            # Create success alert
            if alert_system:
                alert = Alert(
                    type=AlertType.PATIENT_TRANSFER,
                    priority=AlertPriority.LOW,
                    title="Patient Admitted",
                    message=f"Patient {request.patient_name} successfully admitted to {request.requested_ward}",
                    department=request.requested_ward,
                    related_patient_id=request.patient_id,
                    metadata={
                        "admission_type": request.admission_type.value,
                        "workflow_id": workflow_id
                    }
                )
                await alert_system.create_alert(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing admission: {e}")
            return False
    
    async def _create_patient_record(self, request: AdmissionRequest) -> bool:
        """Create patient record in database"""
        try:
            db = SessionLocal()
            
            # Create patient
            patient = Patient(
                patient_id=request.patient_id,
                name=request.patient_name,
                age=request.age,
                gender=request.gender,
                primary_condition=request.primary_condition,
                secondary_conditions=json.dumps(request.secondary_conditions),
                allergies=json.dumps(request.allergies),
                medications=json.dumps(request.medications),
                severity=self._map_priority_to_severity(request.priority),
                admission_date=datetime.now(),
                expected_discharge_date=self._calculate_expected_discharge(request),
                attending_physician=request.attending_physician,
                emergency_contact=request.emergency_contact,
                insurance_id=request.insurance_id,
                status="pending_admission"
            )
            
            db.add(patient)
            db.commit()
            
            logger.info(f"👤 Created patient record: {request.patient_name}")
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating patient record: {e}")
            return False
    
    async def _create_admission_workflow(self, request: AdmissionRequest) -> str:
        """Create comprehensive admission workflow"""
        # This would create a workflow for the complete admission process
        # including documentation, insurance verification, etc.
        return f"admission_workflow_{request.patient_id}"
    
    async def _handle_no_bed_available(self, request: AdmissionRequest):
        """Handle situation when no bed is available"""
        if request.priority in [AdmissionPriority.CRITICAL, AdmissionPriority.URGENT]:
            # Create critical capacity alert
            if alert_system:
                alert = Alert(
                    type=AlertType.CAPACITY_CRITICAL,
                    priority=AlertPriority.CRITICAL,
                    title="No Bed Available for Critical Patient",
                    message=f"Critical patient {request.patient_name} waiting for {request.requested_ward} bed",
                    department=request.requested_ward,
                    related_patient_id=request.patient_id,
                    action_required=True,
                    metadata={
                        "priority": request.priority.value,
                        "condition": request.primary_condition,
                        "wait_time": str(datetime.now() - request.created_at)
                    }
                )
                await alert_system.create_alert(alert)
    
    async def _monitor_admission_timeouts(self):
        """Monitor admission request timeouts"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for requests that have been waiting too long
                for request_id, request in list(self.pending_admissions.items()):
                    wait_time = current_time - request.created_at
                    
                    # Define timeout thresholds based on priority
                    timeout_thresholds = {
                        AdmissionPriority.CRITICAL: timedelta(minutes=15),
                        AdmissionPriority.URGENT: timedelta(hours=1),
                        AdmissionPriority.SEMI_URGENT: timedelta(hours=4),
                        AdmissionPriority.ROUTINE: timedelta(hours=24)
                    }
                    
                    threshold = timeout_thresholds.get(request.priority, timedelta(hours=24))
                    
                    if wait_time > threshold:
                        # Create timeout alert
                        if alert_system:
                            alert = Alert(
                                type=AlertType.CAPACITY_CRITICAL,
                                priority=AlertPriority.HIGH,
                                title="Admission Request Timeout",
                                message=f"Patient {request.patient_name} has been waiting {wait_time} for admission",
                                department="Admissions",
                                related_patient_id=request.patient_id,
                                action_required=True,
                                metadata={
                                    "wait_time": str(wait_time),
                                    "priority": request.priority.value,
                                    "requested_ward": request.requested_ward
                                }
                            )
                            await alert_system.create_alert(alert)
                
            except Exception as e:
                logger.error(f"Error monitoring admission timeouts: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _capacity_management(self):
        """Monitor and manage hospital capacity"""
        while self.running:
            try:
                db = SessionLocal()
                
                # Check overall capacity
                total_beds = db.query(Bed).count()
                occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
                occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
                
                # Check pending admissions
                pending_count = len(self.pending_admissions)
                critical_pending = len([r for r in self.pending_admissions.values() 
                                     if r.priority == AdmissionPriority.CRITICAL])
                
                if occupancy_rate > 95 and pending_count > 0:
                    # Trigger capacity management protocols
                    await self._trigger_capacity_protocols(occupancy_rate, pending_count, critical_pending)
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error in capacity management: {e}")
            
            await asyncio.sleep(180)  # Check every 3 minutes
    
    async def _trigger_capacity_protocols(self, occupancy_rate: float, pending_count: int, critical_pending: int):
        """Trigger capacity management protocols"""
        if alert_system:
            alert = Alert(
                type=AlertType.CAPACITY_CRITICAL,
                priority=AlertPriority.CRITICAL,
                title="Capacity Management Protocol Activated",
                message=f"Hospital at {occupancy_rate:.1f}% capacity with {pending_count} pending admissions ({critical_pending} critical)",
                department="Administration",
                action_required=True,
                metadata={
                    "occupancy_rate": occupancy_rate,
                    "pending_admissions": pending_count,
                    "critical_pending": critical_pending,
                    "recommended_actions": [
                        "Review discharge candidates",
                        "Consider patient transfers",
                        "Activate surge protocols",
                        "Contact overflow facilities"
                    ]
                }
            )
            await alert_system.create_alert(alert)
    
    def _map_admission_priority_to_alert(self, priority: AdmissionPriority) -> AlertPriority:
        """Map admission priority to alert priority"""
        mapping = {
            AdmissionPriority.CRITICAL: AlertPriority.CRITICAL,
            AdmissionPriority.URGENT: AlertPriority.HIGH,
            AdmissionPriority.SEMI_URGENT: AlertPriority.MEDIUM,
            AdmissionPriority.ROUTINE: AlertPriority.LOW
        }
        return mapping.get(priority, AlertPriority.MEDIUM)
    
    def _map_priority_to_severity(self, priority: AdmissionPriority) -> str:
        """Map admission priority to patient severity"""
        mapping = {
            AdmissionPriority.CRITICAL: "critical",
            AdmissionPriority.URGENT: "serious",
            AdmissionPriority.SEMI_URGENT: "stable",
            AdmissionPriority.ROUTINE: "stable"
        }
        return mapping.get(priority, "stable")
    
    def _calculate_expected_discharge(self, request: AdmissionRequest) -> Optional[datetime]:
        """Calculate expected discharge date"""
        if request.estimated_los:
            return datetime.now() + timedelta(days=request.estimated_los)
        
        # Default estimates based on condition
        default_los = {
            "emergency": 1,
            "observation": 1,
            "surgery": 3,
            "cardiac": 5,
            "respiratory": 4,
            "infectious": 7
        }
        
        # Simple keyword matching for LOS estimation
        for condition_type, days in default_los.items():
            if condition_type in request.primary_condition.lower():
                return datetime.now() + timedelta(days=days)
        
        # Default to 3 days
        return datetime.now() + timedelta(days=3)
    
    def get_admission_queue_status(self) -> Dict[str, Any]:
        """Get current admission queue status"""
        return {
            "queue_length": len(self.admission_queue),
            "pending_admissions": len(self.pending_admissions),
            "priority_breakdown": {
                "critical": len([r for r in self.pending_admissions.values() if r.priority == AdmissionPriority.CRITICAL]),
                "urgent": len([r for r in self.pending_admissions.values() if r.priority == AdmissionPriority.URGENT]),
                "semi_urgent": len([r for r in self.pending_admissions.values() if r.priority == AdmissionPriority.SEMI_URGENT]),
                "routine": len([r for r in self.pending_admissions.values() if r.priority == AdmissionPriority.ROUTINE])
            },
            "queue": [
                {
                    "request_id": req_id,
                    "patient_name": self.pending_admissions[req_id].patient_name,
                    "priority": self.pending_admissions[req_id].priority.value,
                    "wait_time": str(datetime.now() - self.pending_admissions[req_id].created_at),
                    "requested_ward": self.pending_admissions[req_id].requested_ward
                }
                for req_id in self.admission_queue[:10]  # Show top 10
            ]
        }

# Global admission system instance
admission_system = AdmissionSystem()
