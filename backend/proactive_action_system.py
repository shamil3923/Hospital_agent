"""
Proactive Alert and Action System
Automatically takes actions based on alerts and system conditions
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy.orm import Session

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from .alert_system import alert_system, Alert, AlertType, AlertPriority
    from .workflow_engine import workflow_engine
    from .autonomous_bed_agent import autonomous_bed_agent
    from .intelligent_bed_assignment import intelligent_bed_assignment, AssignmentPriority
    from .websocket_manager import websocket_manager
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from alert_system import alert_system, Alert, AlertType, AlertPriority
    from workflow_engine import workflow_engine
    from autonomous_bed_agent import autonomous_bed_agent
    from intelligent_bed_assignment import intelligent_bed_assignment, AssignmentPriority
    from websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of proactive actions"""
    EXPEDITE_CLEANING = "expedite_cleaning"
    TRIGGER_DISCHARGE = "trigger_discharge"
    ACTIVATE_OVERFLOW = "activate_overflow"
    NOTIFY_STAFF = "notify_staff"
    REASSIGN_BEDS = "reassign_beds"
    ESCALATE_MANAGEMENT = "escalate_management"
    OPTIMIZE_WORKFLOW = "optimize_workflow"
    EMERGENCY_PROTOCOL = "emergency_protocol"


class ActionTrigger(Enum):
    """What triggers a proactive action"""
    ALERT_GENERATED = "alert_generated"
    CAPACITY_THRESHOLD = "capacity_threshold"
    PREDICTION_RISK = "prediction_risk"
    WORKFLOW_DELAY = "workflow_delay"
    PATIENT_WAITING = "patient_waiting"
    SYSTEM_PERFORMANCE = "system_performance"


@dataclass
class ProactiveAction:
    """Represents a proactive action to be taken"""
    action_id: str
    action_type: ActionType
    trigger: ActionTrigger
    priority: AlertPriority
    description: str
    parameters: Dict[str, Any]
    conditions: Dict[str, Any]
    created_time: datetime
    executed_time: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    auto_execute: bool = True
    requires_approval: bool = False


class ProactiveActionSystem:
    """Proactive alert and action system"""
    
    def __init__(self):
        self.running = False
        self.action_queue: List[ProactiveAction] = []
        self.action_history: List[Dict] = []
        self.action_handlers: Dict[ActionType, Callable] = {}
        self.monitoring_task = None
        
        # Performance metrics
        self.metrics = {
            'actions_triggered': 0,
            'actions_executed': 0,
            'actions_successful': 0,
            'average_response_time': 0.0,
            'alerts_processed': 0,
            'proactive_interventions': 0
        }
        
        # Configuration
        self.capacity_thresholds = {
            'critical': 95,
            'high': 85,
            'warning': 75
        }
        
        self.response_times = {
            AlertPriority.CRITICAL: 30,    # 30 seconds
            AlertPriority.HIGH: 120,       # 2 minutes
            AlertPriority.MEDIUM: 300,     # 5 minutes
            AlertPriority.LOW: 600         # 10 minutes
        }
        
        # Initialize action handlers
        self._initialize_action_handlers()
    
    def _initialize_action_handlers(self):
        """Initialize action handlers for different action types"""
        self.action_handlers = {
            ActionType.EXPEDITE_CLEANING: self._handle_expedite_cleaning,
            ActionType.TRIGGER_DISCHARGE: self._handle_trigger_discharge,
            ActionType.ACTIVATE_OVERFLOW: self._handle_activate_overflow,
            ActionType.NOTIFY_STAFF: self._handle_notify_staff,
            ActionType.REASSIGN_BEDS: self._handle_reassign_beds,
            ActionType.ESCALATE_MANAGEMENT: self._handle_escalate_management,
            ActionType.OPTIMIZE_WORKFLOW: self._handle_optimize_workflow,
            ActionType.EMERGENCY_PROTOCOL: self._handle_emergency_protocol
        }
    
    async def start_proactive_system(self):
        """Start the proactive action system"""
        if self.running:
            logger.warning("Proactive action system is already running")
            return
        
        self.running = True
        logger.info("🚀 Starting Proactive Alert and Action System...")
        
        # Start monitoring and action processing
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Subscribe to alert system if available
        if alert_system:
            # This would subscribe to alert notifications
            pass
        
        logger.info("✅ Proactive Alert and Action System started")
    
    async def stop_proactive_system(self):
        """Stop the proactive action system"""
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Proactive Alert and Action System stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for proactive actions"""
        while self.running:
            try:
                # Check for new conditions that require proactive actions
                await self._check_proactive_conditions()
                
                # Process pending actions
                await self._process_action_queue()
                
                # Monitor system performance
                await self._monitor_system_performance()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in proactive monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _check_proactive_conditions(self):
        """Check for conditions that require proactive actions"""
        try:
            # Check capacity conditions
            await self._check_capacity_conditions()
            
            # Check patient waiting conditions
            await self._check_patient_waiting_conditions()
            
            # Check workflow delay conditions
            await self._check_workflow_delay_conditions()
            
            # Check prediction-based conditions
            await self._check_prediction_conditions()
            
        except Exception as e:
            logger.error(f"Error checking proactive conditions: {e}")
    
    async def _check_capacity_conditions(self):
        """Check bed capacity conditions and trigger actions"""
        try:
            with SessionLocal() as db:
                # Overall capacity
                total_beds = db.query(Bed).count()
                occupied_beds = db.query(Bed).filter(Bed.status == 'occupied').count()
                occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
                
                # Critical capacity
                if occupancy_rate >= self.capacity_thresholds['critical']:
                    await self._trigger_action(
                        ActionType.EMERGENCY_PROTOCOL,
                        ActionTrigger.CAPACITY_THRESHOLD,
                        AlertPriority.CRITICAL,
                        "Critical hospital capacity - emergency protocol activated",
                        {
                            'occupancy_rate': occupancy_rate,
                            'total_beds': total_beds,
                            'occupied_beds': occupied_beds,
                            'protocol_type': 'critical_capacity'
                        }
                    )
                
                # High capacity
                elif occupancy_rate >= self.capacity_thresholds['high']:
                    await self._trigger_action(
                        ActionType.ACTIVATE_OVERFLOW,
                        ActionTrigger.CAPACITY_THRESHOLD,
                        AlertPriority.HIGH,
                        "High capacity - activating overflow protocols",
                        {
                            'occupancy_rate': occupancy_rate,
                            'total_beds': total_beds,
                            'occupied_beds': occupied_beds
                        }
                    )
                
                # Check ICU capacity specifically
                icu_total = db.query(Bed).filter(Bed.bed_type == 'ICU').count()
                icu_occupied = db.query(Bed).filter(Bed.bed_type == 'ICU', Bed.status == 'occupied').count()
                icu_rate = (icu_occupied / icu_total * 100) if icu_total > 0 else 0
                
                if icu_rate >= 90:
                    await self._trigger_action(
                        ActionType.ESCALATE_MANAGEMENT,
                        ActionTrigger.CAPACITY_THRESHOLD,
                        AlertPriority.CRITICAL,
                        "ICU capacity critical - management escalation",
                        {
                            'icu_occupancy_rate': icu_rate,
                            'icu_total': icu_total,
                            'icu_occupied': icu_occupied,
                            'bed_type': 'ICU'
                        }
                    )
                
        except Exception as e:
            logger.error(f"Error checking capacity conditions: {e}")
    
    async def _check_patient_waiting_conditions(self):
        """Check for patients waiting for beds"""
        try:
            with SessionLocal() as db:
                # Find patients without beds
                waiting_patients = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.current_bed_id.is_(None)
                ).all()
                
                for patient in waiting_patients:
                    # Check how long they've been waiting
                    if patient.admission_date:
                        waiting_hours = (datetime.now() - patient.admission_date).total_seconds() / 3600
                        
                        if waiting_hours > 4:  # Waiting more than 4 hours
                            priority = AlertPriority.CRITICAL if waiting_hours > 8 else AlertPriority.HIGH
                            
                            await self._trigger_action(
                                ActionType.EXPEDITE_CLEANING,
                                ActionTrigger.PATIENT_WAITING,
                                priority,
                                f"Patient {patient.patient_id} waiting {waiting_hours:.1f} hours for bed",
                                {
                                    'patient_id': patient.patient_id,
                                    'waiting_hours': waiting_hours,
                                    'patient_condition': patient.condition
                                }
                            )
                
        except Exception as e:
            logger.error(f"Error checking patient waiting conditions: {e}")
    
    async def _check_workflow_delay_conditions(self):
        """Check for delayed workflows"""
        try:
            with SessionLocal() as db:
                # Check beds stuck in cleaning
                current_time = datetime.now()
                stuck_cleaning_beds = db.query(Bed).filter(
                    Bed.status == 'cleaning',
                    Bed.last_updated < current_time - timedelta(hours=2)
                ).all()
                
                for bed in stuck_cleaning_beds:
                    hours_stuck = (current_time - bed.last_updated).total_seconds() / 3600
                    
                    await self._trigger_action(
                        ActionType.EXPEDITE_CLEANING,
                        ActionTrigger.WORKFLOW_DELAY,
                        AlertPriority.HIGH,
                        f"Bed {bed.bed_number} stuck in cleaning for {hours_stuck:.1f} hours",
                        {
                            'bed_id': bed.id,
                            'bed_number': bed.bed_number,
                            'hours_stuck': hours_stuck,
                            'ward': bed.ward
                        }
                    )
                
        except Exception as e:
            logger.error(f"Error checking workflow delay conditions: {e}")
    
    async def _check_prediction_conditions(self):
        """Check prediction-based conditions"""
        try:
            # Get predictions from autonomous agent
            predictions = autonomous_bed_agent.get_current_predictions()
            
            for prediction in predictions:
                if prediction.get('risk_level') == 'critical':
                    await self._trigger_action(
                        ActionType.TRIGGER_DISCHARGE,
                        ActionTrigger.PREDICTION_RISK,
                        AlertPriority.HIGH,
                        f"Critical bed shortage predicted for {prediction.get('ward')} {prediction.get('bed_type')}",
                        {
                            'prediction': prediction,
                            'ward': prediction.get('ward'),
                            'bed_type': prediction.get('bed_type'),
                            'predicted_time': prediction.get('timestamp')
                        }
                    )
                
        except Exception as e:
            logger.error(f"Error checking prediction conditions: {e}")
    
    async def _trigger_action(self, action_type: ActionType, trigger: ActionTrigger, priority: AlertPriority, 
                            description: str, parameters: Dict[str, Any]):
        """Trigger a proactive action"""
        try:
            # Check if similar action already exists
            existing_action = next(
                (action for action in self.action_queue 
                 if action.action_type == action_type and 
                    action.status in ['pending', 'executing'] and
                    action.parameters.get('bed_id') == parameters.get('bed_id') and
                    action.parameters.get('patient_id') == parameters.get('patient_id')),
                None
            )
            
            if existing_action:
                logger.debug(f"Similar action already exists: {action_type.value}")
                return
            
            # Create new action
            action = ProactiveAction(
                action_id=f"{action_type.value}_{datetime.now().timestamp()}",
                action_type=action_type,
                trigger=trigger,
                priority=priority,
                description=description,
                parameters=parameters,
                conditions={
                    'trigger_time': datetime.now().isoformat(),
                    'system_state': 'active'
                },
                created_time=datetime.now(),
                auto_execute=True,
                requires_approval=priority == AlertPriority.CRITICAL and action_type in [ActionType.EMERGENCY_PROTOCOL, ActionType.ESCALATE_MANAGEMENT]
            )
            
            # Add to queue
            self.action_queue.append(action)
            self.action_queue.sort(key=lambda a: a.priority.value)  # Sort by priority
            
            # Update metrics
            self.metrics['actions_triggered'] += 1
            
            logger.info(f"🚀 Triggered proactive action: {description}")
            
            # Broadcast action to dashboard
            if websocket_manager:
                await websocket_manager.broadcast_to_all({
                    'type': 'proactive_action_triggered',
                    'action': {
                        'action_id': action.action_id,
                        'action_type': action.action_type.value,
                        'priority': action.priority.value,
                        'description': action.description,
                        'trigger': action.trigger.value
                    },
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error triggering action: {e}")
    
    async def _process_action_queue(self):
        """Process pending actions in the queue"""
        try:
            if not self.action_queue:
                return
            
            # Get actions ready for execution
            current_time = datetime.now()
            ready_actions = [
                action for action in self.action_queue
                if (action.status == 'pending' and 
                    action.auto_execute and 
                    not action.requires_approval)
            ]
            
            # Execute ready actions
            for action in ready_actions:
                if not self.running:
                    break
                
                await self._execute_action(action)
                self.action_queue.remove(action)
            
        except Exception as e:
            logger.error(f"Error processing action queue: {e}")

    async def _execute_action(self, action: ProactiveAction):
        """Execute a proactive action"""
        try:
            action.status = 'executing'
            action.executed_time = datetime.now()

            logger.info(f"🔧 Executing proactive action: {action.description}")

            # Get action handler
            handler = self.action_handlers.get(action.action_type)
            if not handler:
                raise Exception(f"No handler found for action type: {action.action_type}")

            # Execute the action
            result = await handler(action)

            # Update action status
            action.status = 'completed' if result.get('success') else 'failed'
            action.result = result

            # Update metrics
            self.metrics['actions_executed'] += 1
            if action.status == 'completed':
                self.metrics['actions_successful'] += 1

            # Calculate response time
            response_time = (action.executed_time - action.created_time).total_seconds()
            current_avg = self.metrics['average_response_time']
            total_actions = self.metrics['actions_executed']
            new_avg = ((current_avg * (total_actions - 1)) + response_time) / total_actions
            self.metrics['average_response_time'] = new_avg

            # Add to history
            self._add_to_history(action)

            logger.info(f"✅ Proactive action completed: {action.description} - Status: {action.status}")

        except Exception as e:
            action.status = 'failed'
            action.result = {'success': False, 'error': str(e)}
            self._add_to_history(action)
            logger.error(f"❌ Proactive action failed: {action.description} - Error: {e}")

    # Action handlers

    async def _handle_expedite_cleaning(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle expedited cleaning action"""
        try:
            bed_id = action.parameters.get('bed_id')

            if workflow_engine and bed_id:
                # Trigger expedited cleaning workflow
                workflow_id = await workflow_engine.create_workflow(
                    "expedited_bed_cleaning",
                    {
                        "bed_id": bed_id,
                        "priority": "critical",
                        "initiated_by": "proactive_action_system",
                        "reason": action.description
                    }
                )

                # Notify housekeeping staff
                await self._notify_staff_urgent(
                    "housekeeping",
                    f"URGENT: Expedited cleaning required for bed {action.parameters.get('bed_number', bed_id)}",
                    action.parameters
                )

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'action': 'expedited_cleaning_triggered'
                }
            else:
                return {'success': False, 'error': 'Workflow engine not available or bed_id missing'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_trigger_discharge(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle discharge triggering action"""
        try:
            # Find patients ready for early discharge
            with SessionLocal() as db:
                current_time = datetime.now()
                discharge_candidates = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date.isnot(None),
                    Patient.expected_discharge_date <= current_time + timedelta(hours=12)
                ).limit(3).all()  # Top 3 candidates

                triggered_discharges = []

                for patient in discharge_candidates:
                    if workflow_engine:
                        workflow_id = await workflow_engine.create_workflow(
                            "expedited_discharge",
                            {
                                "patient_id": patient.patient_id,
                                "priority": "high",
                                "initiated_by": "proactive_action_system",
                                "reason": "Capacity optimization"
                            }
                        )
                        triggered_discharges.append({
                            'patient_id': patient.patient_id,
                            'workflow_id': workflow_id
                        })

                # Notify medical staff
                await self._notify_staff_urgent(
                    "medical",
                    f"Expedited discharge review requested for {len(triggered_discharges)} patients",
                    {'patients': triggered_discharges}
                )

                return {
                    'success': True,
                    'triggered_discharges': triggered_discharges,
                    'count': len(triggered_discharges)
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_activate_overflow(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle overflow activation action"""
        try:
            # Activate overflow protocols
            occupancy_rate = action.parameters.get('occupancy_rate', 0)

            # Trigger overflow bed preparation
            if workflow_engine:
                workflow_id = await workflow_engine.create_workflow(
                    "activate_overflow_beds",
                    {
                        "occupancy_rate": occupancy_rate,
                        "priority": "high",
                        "initiated_by": "proactive_action_system"
                    }
                )

                # Notify management and nursing
                await self._notify_staff_urgent(
                    "management",
                    f"Overflow protocol activated - {occupancy_rate:.1f}% capacity",
                    action.parameters
                )

                await self._notify_staff_urgent(
                    "nursing",
                    "Overflow beds being prepared - expect additional patients",
                    action.parameters
                )

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'action': 'overflow_activated'
                }
            else:
                return {'success': False, 'error': 'Workflow engine not available'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_notify_staff(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle staff notification action"""
        try:
            staff_type = action.parameters.get('staff_type', 'general')
            message = action.parameters.get('message', action.description)

            await self._notify_staff_urgent(staff_type, message, action.parameters)

            return {
                'success': True,
                'staff_type': staff_type,
                'message': message
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_reassign_beds(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle bed reassignment action"""
        try:
            # Trigger intelligent bed reassignment
            reassignments = 0

            # Find patients who could be moved to more appropriate beds
            with SessionLocal() as db:
                patients = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.current_bed_id.isnot(None)
                ).limit(5).all()

                for patient in patients:
                    # Get bed recommendations
                    recommendations = await intelligent_bed_assignment.get_bed_recommendations(
                        patient.patient_id, top_n=3
                    )

                    if recommendations and recommendations[0]['total_score'] > 80:
                        # High-scoring alternative bed available
                        current_bed = db.query(Bed).get(patient.current_bed_id)
                        if current_bed and current_bed.bed_type != recommendations[0]['bed_type']:
                            # Different bed type - potential optimization
                            reassignments += 1

            return {
                'success': True,
                'potential_reassignments': reassignments,
                'action': 'reassignment_analysis_completed'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_escalate_management(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle management escalation action"""
        try:
            # Generate critical alert for management
            if alert_system:
                alert = Alert(
                    type=AlertType.CAPACITY_CRITICAL,
                    priority=AlertPriority.CRITICAL,
                    title="MANAGEMENT ESCALATION: Critical Bed Capacity",
                    message=f"Proactive system escalation: {action.description}",
                    department="Management",
                    action_required=True,
                    metadata=action.parameters
                )
                alert_id = await alert_system.create_alert(alert)

                # Notify management staff
                await self._notify_staff_urgent(
                    "management",
                    f"CRITICAL ESCALATION: {action.description}",
                    action.parameters
                )

                return {
                    'success': True,
                    'alert_id': alert_id,
                    'action': 'management_escalated'
                }
            else:
                return {'success': False, 'error': 'Alert system not available'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_optimize_workflow(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle workflow optimization action"""
        try:
            # Trigger workflow optimization
            if workflow_engine:
                workflow_id = await workflow_engine.create_workflow(
                    "workflow_optimization",
                    {
                        "optimization_type": "proactive",
                        "initiated_by": "proactive_action_system",
                        "parameters": action.parameters
                    }
                )

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'action': 'workflow_optimization_triggered'
                }
            else:
                return {'success': False, 'error': 'Workflow engine not available'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _handle_emergency_protocol(self, action: ProactiveAction) -> Dict[str, Any]:
        """Handle emergency protocol activation"""
        try:
            protocol_type = action.parameters.get('protocol_type', 'general')

            # Activate emergency protocols
            emergency_actions = []

            # 1. Expedite all possible discharges
            if workflow_engine:
                discharge_workflow = await workflow_engine.create_workflow(
                    "emergency_discharge_review",
                    {
                        "priority": "critical",
                        "initiated_by": "emergency_protocol"
                    }
                )
                emergency_actions.append(f"Emergency discharge review: {discharge_workflow}")

            # 2. Activate all overflow capacity
            if workflow_engine:
                overflow_workflow = await workflow_engine.create_workflow(
                    "emergency_overflow_activation",
                    {
                        "priority": "critical",
                        "initiated_by": "emergency_protocol"
                    }
                )
                emergency_actions.append(f"Emergency overflow activation: {overflow_workflow}")

            # 3. Alert all management
            await self._notify_staff_urgent(
                "management",
                f"EMERGENCY PROTOCOL ACTIVATED: {action.description}",
                action.parameters
            )

            # 4. Generate critical system alert
            if alert_system:
                alert = Alert(
                    type=AlertType.CAPACITY_CRITICAL,
                    priority=AlertPriority.CRITICAL,
                    title="EMERGENCY PROTOCOL ACTIVATED",
                    message=f"Emergency bed capacity protocol activated: {action.description}",
                    department="Hospital Operations",
                    action_required=True,
                    metadata=action.parameters
                )
                alert_id = await alert_system.create_alert(alert)
                emergency_actions.append(f"Critical alert generated: {alert_id}")

            return {
                'success': True,
                'protocol_type': protocol_type,
                'emergency_actions': emergency_actions,
                'action': 'emergency_protocol_activated'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # Utility methods

    async def _notify_staff_urgent(self, staff_type: str, message: str, parameters: Dict[str, Any]):
        """Send urgent notification to staff"""
        try:
            # This would integrate with hospital communication systems
            # For now, log the notification and broadcast via websocket

            notification = {
                'type': 'urgent_staff_notification',
                'staff_type': staff_type,
                'message': message,
                'parameters': parameters,
                'timestamp': datetime.now().isoformat(),
                'priority': 'urgent'
            }

            # Broadcast to dashboard
            if websocket_manager:
                await websocket_manager.broadcast_to_all(notification)

            # Log the notification
            with SessionLocal() as db:
                log_entry = AgentLog(
                    agent_name="proactive_action_system",
                    action="staff_notification",
                    details=f"Urgent notification to {staff_type}: {message}",
                    status="sent",
                    timestamp=datetime.now()
                )
                db.add(log_entry)
                db.commit()

            logger.info(f"📢 Urgent notification sent to {staff_type}: {message}")

        except Exception as e:
            logger.error(f"Error sending staff notification: {e}")

    async def _monitor_system_performance(self):
        """Monitor system performance and trigger actions if needed"""
        try:
            # Check if autonomous systems are responding
            if autonomous_bed_agent.running:
                # Check last activity
                if hasattr(autonomous_bed_agent, 'last_activity'):
                    last_activity = autonomous_bed_agent.last_activity
                    if (datetime.now() - last_activity).total_seconds() > 600:  # 10 minutes
                        await self._trigger_action(
                            ActionType.NOTIFY_STAFF,
                            ActionTrigger.SYSTEM_PERFORMANCE,
                            AlertPriority.MEDIUM,
                            "Autonomous bed agent appears inactive",
                            {'system': 'autonomous_bed_agent', 'last_activity': last_activity.isoformat()}
                        )

        except Exception as e:
            logger.error(f"Error monitoring system performance: {e}")

    def _add_to_history(self, action: ProactiveAction):
        """Add action to history"""
        try:
            history_record = {
                'action_id': action.action_id,
                'action_type': action.action_type.value,
                'trigger': action.trigger.value,
                'priority': action.priority.value,
                'description': action.description,
                'parameters': action.parameters,
                'created_time': action.created_time.isoformat(),
                'executed_time': action.executed_time.isoformat() if action.executed_time else None,
                'status': action.status,
                'result': action.result
            }

            self.action_history.append(history_record)

            # Keep only last 100 actions
            if len(self.action_history) > 100:
                self.action_history = self.action_history[-100:]

            # Log to database
            with SessionLocal() as db:
                log_entry = AgentLog(
                    agent_name="proactive_action_system",
                    action=f"proactive_{action.action_type.value}",
                    details=f"{action.description} | Status: {action.status}",
                    status=action.status,
                    timestamp=action.executed_time or action.created_time
                )
                db.add(log_entry)
                db.commit()

        except Exception as e:
            logger.error(f"Error adding action to history: {e}")

    # Public API methods

    def get_action_queue_status(self) -> Dict[str, Any]:
        """Get current action queue status"""
        return {
            'queue_length': len(self.action_queue),
            'pending_actions': len([a for a in self.action_queue if a.status == 'pending']),
            'executing_actions': len([a for a in self.action_queue if a.status == 'executing']),
            'critical_actions': len([a for a in self.action_queue if a.priority == AlertPriority.CRITICAL]),
            'actions': [
                {
                    'action_id': action.action_id,
                    'action_type': action.action_type.value,
                    'priority': action.priority.value,
                    'description': action.description,
                    'status': action.status,
                    'created_time': action.created_time.isoformat(),
                    'auto_execute': action.auto_execute,
                    'requires_approval': action.requires_approval
                }
                for action in self.action_queue
            ]
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get proactive action system metrics"""
        return self.metrics.copy()

    def get_action_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent action history"""
        return self.action_history[-limit:] if self.action_history else []

    async def approve_action(self, action_id: str) -> bool:
        """Approve a pending action that requires approval"""
        try:
            action = next((a for a in self.action_queue if a.action_id == action_id), None)

            if not action:
                logger.error(f"Action {action_id} not found")
                return False

            if not action.requires_approval:
                logger.warning(f"Action {action_id} does not require approval")
                return False

            action.requires_approval = False
            action.auto_execute = True

            logger.info(f"✅ Action approved: {action_id}")
            return True

        except Exception as e:
            logger.error(f"Error approving action: {e}")
            return False

    async def cancel_action(self, action_id: str) -> bool:
        """Cancel a pending action"""
        try:
            action = next((a for a in self.action_queue if a.action_id == action_id), None)

            if not action:
                logger.error(f"Action {action_id} not found")
                return False

            if action.status == 'executing':
                logger.warning(f"Cannot cancel executing action: {action_id}")
                return False

            action.status = 'cancelled'
            self.action_queue.remove(action)
            self._add_to_history(action)

            logger.info(f"❌ Action cancelled: {action_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling action: {e}")
            return False

    def update_thresholds(self, new_thresholds: Dict[str, Any]):
        """Update capacity thresholds"""
        try:
            if 'capacity_thresholds' in new_thresholds:
                self.capacity_thresholds.update(new_thresholds['capacity_thresholds'])

            if 'response_times' in new_thresholds:
                self.response_times.update(new_thresholds['response_times'])

            logger.info("⚙️ Proactive action thresholds updated")

        except Exception as e:
            logger.error(f"Error updating thresholds: {e}")

    async def force_action_execution(self, action_type: ActionType, parameters: Dict[str, Any]) -> str:
        """Force execution of a specific action type"""
        try:
            action_id = await self._trigger_action(
                action_type,
                ActionTrigger.SYSTEM_PERFORMANCE,  # Manual trigger
                AlertPriority.HIGH,
                f"Manually triggered {action_type.value}",
                parameters
            )

            logger.info(f"🔧 Forced action execution: {action_type.value}")
            return action_id

        except Exception as e:
            logger.error(f"Error forcing action execution: {e}")
            return ""


# Global instance
proactive_action_system = ProactiveActionSystem()
