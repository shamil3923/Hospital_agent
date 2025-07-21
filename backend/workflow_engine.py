"""
Automated Workflow Engine for Hospital Operations
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory, Staff
    from .alert_system import alert_system, Alert, AlertType, AlertPriority
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory, Staff
    from alert_system import alert_system, Alert, AlertType, AlertPriority

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowPriority(Enum):
    """Workflow priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    id: str
    name: str
    action: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_minutes: int = 30
    retry_count: int = 0
    max_retries: int = 3
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class Workflow:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowEngine:
    """Automated workflow execution engine"""
    
    def __init__(self):
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_templates: Dict[str, Callable] = {}
        self.running = False
        self.execution_tasks: List = []
        
        # Register built-in workflow templates
        self._register_builtin_workflows()
    
    def _register_builtin_workflows(self):
        """Register built-in workflow templates"""
        self.workflow_templates.update({
            "bed_assignment": self._create_bed_assignment_workflow,
            "bed_cleaning": self._create_bed_cleaning_workflow,
            "patient_transfer": self._create_patient_transfer_workflow,
            "discharge_preparation": self._create_discharge_preparation_workflow,
            "admission_process": self._create_admission_process_workflow,
            "emergency_bed_allocation": self._create_emergency_bed_allocation_workflow
        })
    
    async def start_engine(self):
        """Start the workflow engine"""
        if self.running:
            return
        
        self.running = True
        logger.info("🔄 Starting workflow engine...")
        
        # Start execution tasks
        self.execution_tasks = [
            asyncio.create_task(self._workflow_executor()),
            asyncio.create_task(self._workflow_monitor()),
            asyncio.create_task(self._automatic_workflow_triggers())
        ]
        
        logger.info("✅ Workflow engine started")
    
    async def stop_engine(self):
        """Stop the workflow engine"""
        self.running = False
        
        # Cancel all execution tasks
        for task in self.execution_tasks:
            task.cancel()
        
        await asyncio.gather(*self.execution_tasks, return_exceptions=True)
        self.execution_tasks.clear()
        
        logger.info("🛑 Workflow engine stopped")
    
    async def create_workflow(self, template_name: str, parameters: Dict[str, Any]) -> str:
        """Create and start a new workflow"""
        if template_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {template_name}")
        
        # Generate workflow
        workflow = self.workflow_templates[template_name](parameters)
        
        # Add to active workflows
        self.active_workflows[workflow.id] = workflow
        
        logger.info(f"📋 Created workflow: {workflow.name} ({workflow.id})")
        return workflow.id
    
    async def cancel_workflow(self, workflow_id: str):
        """Cancel an active workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            logger.info(f"❌ Cancelled workflow: {workflow.name}")
    
    async def _workflow_executor(self):
        """Execute pending workflows"""
        while self.running:
            try:
                # Find workflows ready for execution
                ready_workflows = [
                    wf for wf in self.active_workflows.values()
                    if wf.status == WorkflowStatus.PENDING
                ]
                
                # Sort by priority
                ready_workflows.sort(key=lambda w: w.priority.value, reverse=True)
                
                # Execute workflows
                for workflow in ready_workflows:
                    if not self.running:
                        break
                    
                    await self._execute_workflow(workflow)
                
            except Exception as e:
                logger.error(f"Error in workflow executor: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute a single workflow"""
        try:
            workflow.status = WorkflowStatus.IN_PROGRESS
            workflow.started_at = datetime.now()
            
            logger.info(f"🚀 Executing workflow: {workflow.name}")
            
            # Execute steps in dependency order
            completed_steps = set()
            
            while len(completed_steps) < len(workflow.steps):
                progress_made = False
                
                for step in workflow.steps:
                    if (step.id not in completed_steps and 
                        all(dep in completed_steps for dep in step.dependencies)):
                        
                        # Execute step
                        success = await self._execute_step(step, workflow)
                        
                        if success:
                            completed_steps.add(step.id)
                            progress_made = True
                        else:
                            # Step failed
                            if step.retry_count >= step.max_retries:
                                workflow.status = WorkflowStatus.FAILED
                                logger.error(f"❌ Workflow failed: {workflow.name} (Step: {step.name})")
                                return
                            else:
                                step.retry_count += 1
                                logger.warning(f"🔄 Retrying step: {step.name} (Attempt {step.retry_count})")
                
                if not progress_made:
                    # No progress possible - circular dependency or all remaining steps failed
                    workflow.status = WorkflowStatus.FAILED
                    logger.error(f"❌ Workflow stuck: {workflow.name}")
                    return
            
            # All steps completed
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            
            logger.info(f"✅ Workflow completed: {workflow.name}")
            
            # Create completion alert
            if alert_system:
                alert = Alert(
                    type=AlertType.PATIENT_TRANSFER,  # Generic type for workflow completion
                    priority=AlertPriority.LOW,
                    title="Workflow Completed",
                    message=f"Workflow '{workflow.name}' completed successfully",
                    department="Operations",
                    metadata={"workflow_id": workflow.id, "duration": str(workflow.completed_at - workflow.started_at)}
                )
                await alert_system.create_alert(alert)
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.error(f"❌ Workflow execution error: {workflow.name} - {e}")
    
    async def _execute_step(self, step: WorkflowStep, workflow: Workflow) -> bool:
        """Execute a single workflow step"""
        try:
            step.status = WorkflowStatus.IN_PROGRESS
            step.started_at = datetime.now()
            
            logger.info(f"⚡ Executing step: {step.name}")
            
            # Execute the step action
            result = await step.action(step.parameters, workflow.metadata)
            
            if result:
                step.status = WorkflowStatus.COMPLETED
                step.completed_at = datetime.now()
                return True
            else:
                step.status = WorkflowStatus.FAILED
                return False
                
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error_message = str(e)
            logger.error(f"❌ Step execution error: {step.name} - {e}")
            return False
    
    async def _workflow_monitor(self):
        """Monitor workflow timeouts and cleanup"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for timed out workflows
                for workflow in list(self.active_workflows.values()):
                    if workflow.status == WorkflowStatus.IN_PROGRESS:
                        # Check step timeouts
                        for step in workflow.steps:
                            if (step.status == WorkflowStatus.IN_PROGRESS and 
                                step.started_at and
                                current_time - step.started_at > timedelta(minutes=step.timeout_minutes)):
                                
                                step.status = WorkflowStatus.FAILED
                                step.error_message = "Step timeout"
                                logger.warning(f"⏰ Step timeout: {step.name}")
                
                # Cleanup completed workflows older than 24 hours
                cutoff_time = current_time - timedelta(hours=24)
                completed_workflows = [
                    wf_id for wf_id, wf in self.active_workflows.items()
                    if wf.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
                    and wf.completed_at and wf.completed_at < cutoff_time
                ]
                
                for wf_id in completed_workflows:
                    del self.active_workflows[wf_id]
                
            except Exception as e:
                logger.error(f"Error in workflow monitor: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _automatic_workflow_triggers(self):
        """Automatically trigger workflows based on conditions"""
        while self.running:
            try:
                db = SessionLocal()
                
                # Trigger bed cleaning workflows for beds that need cleaning
                beds_needing_cleaning = db.query(Bed).filter(
                    Bed.status == "cleaning",
                    Bed.last_updated < datetime.now() - timedelta(minutes=30)
                ).all()
                
                for bed in beds_needing_cleaning:
                    # Check if cleaning workflow already exists
                    existing_workflow = any(
                        wf.metadata.get("bed_id") == bed.id and "cleaning" in wf.name.lower()
                        for wf in self.active_workflows.values()
                        if wf.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]
                    )
                    
                    if not existing_workflow:
                        await self.create_workflow("bed_cleaning", {"bed_id": bed.id})
                
                # Trigger discharge preparation workflows
                upcoming_discharges = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date.isnot(None),
                    Patient.expected_discharge_date >= datetime.now(),
                    Patient.expected_discharge_date <= datetime.now() + timedelta(hours=4)
                ).all()
                
                for patient in upcoming_discharges:
                    # Check if discharge workflow already exists
                    existing_workflow = any(
                        wf.metadata.get("patient_id") == patient.patient_id and "discharge" in wf.name.lower()
                        for wf in self.active_workflows.values()
                        if wf.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]
                    )
                    
                    if not existing_workflow:
                        await self.create_workflow("discharge_preparation", {"patient_id": patient.patient_id})
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error in automatic workflow triggers: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    def _create_bed_assignment_workflow(self, parameters: Dict[str, Any]) -> Workflow:
        """Create bed assignment workflow"""
        patient_id = parameters["patient_id"]
        bed_requirements = parameters.get("bed_requirements", {})
        
        workflow_id = f"bed_assignment_{patient_id}_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                id="find_suitable_bed",
                name="Find Suitable Bed",
                action=self._find_suitable_bed,
                parameters={"patient_id": patient_id, "requirements": bed_requirements}
            ),
            WorkflowStep(
                id="reserve_bed",
                name="Reserve Bed",
                action=self._reserve_bed,
                parameters={"patient_id": patient_id},
                dependencies=["find_suitable_bed"]
            ),
            WorkflowStep(
                id="notify_staff",
                name="Notify Staff",
                action=self._notify_staff_assignment,
                parameters={"patient_id": patient_id},
                dependencies=["reserve_bed"]
            ),
            WorkflowStep(
                id="update_records",
                name="Update Patient Records",
                action=self._update_patient_bed_assignment,
                parameters={"patient_id": patient_id},
                dependencies=["reserve_bed"]
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name=f"Bed Assignment for Patient {patient_id}",
            description="Automated bed assignment workflow",
            steps=steps,
            priority=WorkflowPriority.HIGH,
            metadata={"patient_id": patient_id, "type": "bed_assignment"}
        )
    
    def _create_bed_cleaning_workflow(self, parameters: Dict[str, Any]) -> Workflow:
        """Create bed cleaning workflow"""
        bed_id = parameters["bed_id"]
        
        workflow_id = f"bed_cleaning_{bed_id}_{int(datetime.now().timestamp())}"
        
        steps = [
            WorkflowStep(
                id="notify_housekeeping",
                name="Notify Housekeeping",
                action=self._notify_housekeeping,
                parameters={"bed_id": bed_id}
            ),
            WorkflowStep(
                id="track_cleaning_progress",
                name="Track Cleaning Progress",
                action=self._track_cleaning_progress,
                parameters={"bed_id": bed_id},
                dependencies=["notify_housekeeping"],
                timeout_minutes=90
            ),
            WorkflowStep(
                id="quality_check",
                name="Quality Check",
                action=self._perform_quality_check,
                parameters={"bed_id": bed_id},
                dependencies=["track_cleaning_progress"]
            ),
            WorkflowStep(
                id="mark_bed_available",
                name="Mark Bed Available",
                action=self._mark_bed_available,
                parameters={"bed_id": bed_id},
                dependencies=["quality_check"]
            )
        ]
        
        return Workflow(
            id=workflow_id,
            name=f"Bed Cleaning for Bed {bed_id}",
            description="Automated bed cleaning and preparation workflow",
            steps=steps,
            priority=WorkflowPriority.NORMAL,
            metadata={"bed_id": bed_id, "type": "bed_cleaning"}
        )
    
    # Workflow action implementations
    async def _find_suitable_bed(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Find a suitable bed for patient"""
        try:
            db = SessionLocal()
            patient_id = parameters["patient_id"]
            requirements = parameters.get("requirements", {})
            
            # Find patient
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                return False
            
            # Find suitable beds
            query = db.query(Bed).filter(Bed.status == "vacant")
            
            # Apply requirements
            if requirements.get("ward"):
                query = query.filter(Bed.ward == requirements["ward"])
            if requirements.get("bed_type"):
                query = query.filter(Bed.bed_type == requirements["bed_type"])
            if requirements.get("private_room"):
                query = query.filter(Bed.private_room == True)
            if requirements.get("isolation_required"):
                query = query.filter(Bed.isolation_required == True)
            
            suitable_beds = query.all()
            
            if suitable_beds:
                # Select best bed (for now, just the first one)
                selected_bed = suitable_beds[0]
                metadata["selected_bed_id"] = selected_bed.id
                metadata["selected_bed_number"] = selected_bed.bed_number
                
                logger.info(f"✅ Found suitable bed: {selected_bed.bed_number} for patient {patient_id}")
                db.close()
                return True
            else:
                logger.warning(f"⚠️ No suitable bed found for patient {patient_id}")
                db.close()
                return False
                
        except Exception as e:
            logger.error(f"Error finding suitable bed: {e}")
            return False
    
    async def _reserve_bed(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Reserve the selected bed"""
        try:
            db = SessionLocal()
            bed_id = metadata.get("selected_bed_id")
            patient_id = parameters["patient_id"]
            
            if not bed_id:
                return False
            
            # Update bed status
            bed = db.query(Bed).filter(Bed.id == bed_id).first()
            if bed and bed.status == "vacant":
                bed.status = "occupied"
                bed.patient_id = patient_id
                bed.admission_time = datetime.now()
                bed.last_updated = datetime.now()
                
                db.commit()
                logger.info(f"✅ Reserved bed {bed.bed_number} for patient {patient_id}")
                db.close()
                return True
            else:
                logger.warning(f"⚠️ Bed {bed_id} no longer available")
                db.close()
                return False
                
        except Exception as e:
            logger.error(f"Error reserving bed: {e}")
            return False
    
    async def _notify_staff_assignment(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Notify staff of bed assignment"""
        try:
            if alert_system:
                bed_number = metadata.get("selected_bed_number", "Unknown")
                patient_id = parameters["patient_id"]
                
                alert = Alert(
                    type=AlertType.PATIENT_TRANSFER,
                    priority=AlertPriority.MEDIUM,
                    title="Bed Assignment Completed",
                    message=f"Patient {patient_id} assigned to bed {bed_number}",
                    department="Nursing",
                    metadata={"patient_id": patient_id, "bed_number": bed_number}
                )
                await alert_system.create_alert(alert)
            
            return True
        except Exception as e:
            logger.error(f"Error notifying staff: {e}")
            return False
    
    async def _update_patient_bed_assignment(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Update patient records with bed assignment"""
        try:
            db = SessionLocal()
            patient_id = parameters["patient_id"]
            bed_id = metadata.get("selected_bed_id")
            
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if patient:
                patient.current_bed_id = bed_id
                patient.status = "admitted"
                
                # Create occupancy history record
                history = BedOccupancyHistory(
                    bed_id=bed_id,
                    patient_id=patient_id,
                    status="occupied",
                    reason="admission",
                    start_time=datetime.now(),
                    assigned_by="workflow_system"
                )
                db.add(history)
                
                db.commit()
                logger.info(f"✅ Updated patient {patient_id} bed assignment")
                db.close()
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error updating patient records: {e}")
            return False
    
    # Additional workflow action stubs (to be implemented)
    async def _notify_housekeeping(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Notify housekeeping staff"""
        # Implementation would integrate with staff notification system
        await asyncio.sleep(1)  # Simulate notification
        return True
    
    async def _track_cleaning_progress(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Track bed cleaning progress"""
        # Implementation would track actual cleaning progress
        await asyncio.sleep(2)  # Simulate cleaning time
        return True
    
    async def _perform_quality_check(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Perform quality check on cleaned bed"""
        # Implementation would integrate with quality assurance
        await asyncio.sleep(1)  # Simulate quality check
        return True
    
    async def _mark_bed_available(self, parameters: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Mark bed as available after cleaning"""
        try:
            db = SessionLocal()
            bed_id = parameters["bed_id"]
            
            bed = db.query(Bed).filter(Bed.id == bed_id).first()
            if bed:
                bed.status = "vacant"
                bed.last_cleaned = datetime.now()
                bed.last_updated = datetime.now()
                
                db.commit()
                logger.info(f"✅ Bed {bed.bed_number} marked as available")
                db.close()
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error marking bed available: {e}")
            return False
    
    # Placeholder methods for other workflow templates
    def _create_patient_transfer_workflow(self, parameters: Dict[str, Any]) -> Workflow:
        """Create patient transfer workflow"""
        # Implementation for patient transfers between beds/wards
        pass
    
    def _create_discharge_preparation_workflow(self, parameters: Dict[str, Any]) -> Workflow:
        """Create discharge preparation workflow"""
        # Implementation for discharge preparation
        pass
    
    def _create_admission_process_workflow(self, parameters: Dict[str, Any]) -> Workflow:
        """Create admission process workflow"""
        # Implementation for patient admission
        pass
    
    def _create_emergency_bed_allocation_workflow(self, parameters: Dict[str, Any]) -> Workflow:
        """Create emergency bed allocation workflow"""
        # Implementation for emergency situations
        pass
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "id": workflow.id,
                "name": workflow.name,
                "status": workflow.status.value,
                "progress": len([s for s in workflow.steps if s.status == WorkflowStatus.COMPLETED]) / len(workflow.steps) * 100,
                "steps": [
                    {
                        "id": step.id,
                        "name": step.name,
                        "status": step.status.value,
                        "error": step.error_message
                    }
                    for step in workflow.steps
                ]
            }
        return None
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        return [
            {
                "id": wf.id,
                "name": wf.name,
                "status": wf.status.value,
                "priority": wf.priority.value,
                "created_at": wf.created_at.isoformat(),
                "metadata": wf.metadata
            }
            for wf in self.active_workflows.values()
        ]

# Global workflow engine instance
workflow_engine = WorkflowEngine()
