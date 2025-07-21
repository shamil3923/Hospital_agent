"""
Autonomous Task Scheduler
Coordinates and schedules all autonomous bed management operations
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
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog
    from .autonomous_bed_agent import autonomous_bed_agent
    from .predictive_analytics import predictive_analytics
    from .intelligent_bed_assignment import intelligent_bed_assignment, AssignmentPriority
    from .alert_system import alert_system
    from .workflow_engine import workflow_engine
    from .websocket_manager import websocket_manager
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog
    from autonomous_bed_agent import autonomous_bed_agent
    from predictive_analytics import predictive_analytics
    from intelligent_bed_assignment import intelligent_bed_assignment, AssignmentPriority
    from alert_system import alert_system
    from workflow_engine import workflow_engine
    from websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of autonomous tasks"""
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    BED_ASSIGNMENT = "bed_assignment"
    CAPACITY_MONITORING = "capacity_monitoring"
    DISCHARGE_PLANNING = "discharge_planning"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    PERFORMANCE_MONITORING = "performance_monitoring"
    DATA_SYNC = "data_sync"
    ALERT_PROCESSING = "alert_processing"


class TaskPriority(Enum):
    """Priority levels for scheduled tasks"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ScheduledTask:
    """Represents a scheduled autonomous task"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    function: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    max_runtime_seconds: int = 300  # 5 minutes default
    retry_count: int = 0
    max_retries: int = 3
    parameters: Dict[str, Any] = None


class AutonomousScheduler:
    """Autonomous task scheduler for bed management operations"""
    
    def __init__(self):
        self.running = False
        self.scheduler_task = None
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_history: List[Dict] = []
        self.performance_metrics = {
            'tasks_executed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0.0,
            'system_uptime': 0.0,
            'last_health_check': None
        }
        
        # Initialize default tasks
        self._initialize_default_tasks()
    
    def _initialize_default_tasks(self):
        """Initialize default autonomous tasks"""
        
        # Predictive analysis - every 15 minutes
        self.scheduled_tasks["predictive_analysis"] = ScheduledTask(
            task_id="predictive_analysis",
            task_type=TaskType.PREDICTIVE_ANALYSIS,
            priority=TaskPriority.HIGH,
            function=self._run_predictive_analysis,
            interval_seconds=900,  # 15 minutes
            parameters={}
        )
        
        # Bed assignment processing - every 30 seconds
        self.scheduled_tasks["bed_assignment"] = ScheduledTask(
            task_id="bed_assignment",
            task_type=TaskType.BED_ASSIGNMENT,
            priority=TaskPriority.CRITICAL,
            function=self._process_bed_assignments,
            interval_seconds=30,
            parameters={}
        )
        
        # Capacity monitoring - every 2 minutes
        self.scheduled_tasks["capacity_monitoring"] = ScheduledTask(
            task_id="capacity_monitoring",
            task_type=TaskType.CAPACITY_MONITORING,
            priority=TaskPriority.HIGH,
            function=self._monitor_capacity,
            interval_seconds=120,
            parameters={}
        )
        
        # Discharge planning - every 10 minutes
        self.scheduled_tasks["discharge_planning"] = ScheduledTask(
            task_id="discharge_planning",
            task_type=TaskType.DISCHARGE_PLANNING,
            priority=TaskPriority.MEDIUM,
            function=self._optimize_discharge_planning,
            interval_seconds=600,
            parameters={}
        )
        
        # Workflow optimization - every 5 minutes
        self.scheduled_tasks["workflow_optimization"] = ScheduledTask(
            task_id="workflow_optimization",
            task_type=TaskType.WORKFLOW_OPTIMIZATION,
            priority=TaskPriority.MEDIUM,
            function=self._optimize_workflows,
            interval_seconds=300,
            parameters={}
        )
        
        # Performance monitoring - every 1 minute
        self.scheduled_tasks["performance_monitoring"] = ScheduledTask(
            task_id="performance_monitoring",
            task_type=TaskType.PERFORMANCE_MONITORING,
            priority=TaskPriority.LOW,
            function=self._monitor_performance,
            interval_seconds=60,
            parameters={}
        )
        
        # Data synchronization - every 5 minutes
        self.scheduled_tasks["data_sync"] = ScheduledTask(
            task_id="data_sync",
            task_type=TaskType.DATA_SYNC,
            priority=TaskPriority.LOW,
            function=self._sync_data,
            interval_seconds=300,
            parameters={}
        )
        
        # Alert processing - every 1 minute
        self.scheduled_tasks["alert_processing"] = ScheduledTask(
            task_id="alert_processing",
            task_type=TaskType.ALERT_PROCESSING,
            priority=TaskPriority.HIGH,
            function=self._process_alerts,
            interval_seconds=60,
            parameters={}
        )
    
    async def start_scheduler(self):
        """Start the autonomous task scheduler"""
        if self.running:
            logger.warning("Autonomous scheduler is already running")
            return
        
        self.running = True
        logger.info("🤖 Starting Autonomous Task Scheduler...")
        
        # Initialize next run times
        current_time = datetime.now()
        for task in self.scheduled_tasks.values():
            task.next_run = current_time + timedelta(seconds=task.interval_seconds)
        
        # Start scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Start all autonomous systems
        await self._start_autonomous_systems()
        
        logger.info("✅ Autonomous Task Scheduler started successfully")
    
    async def stop_scheduler(self):
        """Stop the autonomous task scheduler"""
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Stop all autonomous systems
        await self._stop_autonomous_systems()
        
        logger.info("🛑 Autonomous Task Scheduler stopped")
    
    async def _start_autonomous_systems(self):
        """Start all autonomous systems"""
        try:
            # Start autonomous bed agent
            await autonomous_bed_agent.start_autonomous_operations()
            
            # Start intelligent bed assignment
            await intelligent_bed_assignment.start_assignment_system()
            
            # Start alert system if available
            if alert_system:
                await alert_system.start_monitoring()
            
            # Start workflow engine if available
            if workflow_engine:
                await workflow_engine.start_engine()
            
            logger.info("✅ All autonomous systems started")
            
        except Exception as e:
            logger.error(f"Error starting autonomous systems: {e}")
    
    async def _stop_autonomous_systems(self):
        """Stop all autonomous systems"""
        try:
            # Stop autonomous bed agent
            await autonomous_bed_agent.stop_autonomous_operations()
            
            # Stop intelligent bed assignment
            await intelligent_bed_assignment.stop_assignment_system()
            
            # Stop alert system if available
            if alert_system:
                await alert_system.stop_monitoring()
            
            # Stop workflow engine if available
            if workflow_engine:
                await workflow_engine.stop_engine()
            
            logger.info("✅ All autonomous systems stopped")
            
        except Exception as e:
            logger.error(f"Error stopping autonomous systems: {e}")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        start_time = datetime.now()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Update system uptime
                self.performance_metrics['system_uptime'] = (current_time - start_time).total_seconds()
                
                # Find tasks ready to run
                ready_tasks = [
                    task for task in self.scheduled_tasks.values()
                    if (task.enabled and 
                        task.next_run and 
                        current_time >= task.next_run)
                ]
                
                # Sort by priority
                ready_tasks.sort(key=lambda t: t.priority.value)
                
                # Execute ready tasks
                for task in ready_tasks:
                    if not self.running:
                        break
                    
                    await self._execute_task(task)
                
                # Sleep for a short interval
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(10)
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            execution_start = datetime.now()
            
            logger.debug(f"🤖 Executing task: {task.task_id}")
            
            # Create timeout for task execution
            try:
                await asyncio.wait_for(
                    task.function(task.parameters or {}),
                    timeout=task.max_runtime_seconds
                )
                
                # Task completed successfully
                task.last_run = execution_start
                task.next_run = execution_start + timedelta(seconds=task.interval_seconds)
                task.retry_count = 0
                
                # Update metrics
                execution_time = (datetime.now() - execution_start).total_seconds()
                self._update_task_metrics(task, execution_time, True)
                
                # Log successful execution
                self._log_task_execution(task, "success", execution_time)
                
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Task {task.task_id} timed out after {task.max_runtime_seconds} seconds")
                await self._handle_task_failure(task, "timeout")
                
            except Exception as e:
                logger.error(f"❌ Task {task.task_id} failed: {e}")
                await self._handle_task_failure(task, str(e))
                
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
    
    async def _handle_task_failure(self, task: ScheduledTask, error: str):
        """Handle task execution failure"""
        try:
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                # Schedule retry with exponential backoff
                retry_delay = min(300, 30 * (2 ** (task.retry_count - 1)))  # Max 5 minutes
                task.next_run = datetime.now() + timedelta(seconds=retry_delay)
                
                logger.info(f"🔄 Retrying task {task.task_id} in {retry_delay} seconds (attempt {task.retry_count}/{task.max_retries})")
            else:
                # Max retries exceeded, schedule next regular run
                task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
                task.retry_count = 0
                
                logger.error(f"❌ Task {task.task_id} failed after {task.max_retries} retries")
            
            # Update metrics
            self._update_task_metrics(task, 0, False)
            
            # Log failure
            self._log_task_execution(task, "failed", 0, error)
            
        except Exception as e:
            logger.error(f"Error handling task failure: {e}")
    
    # Task execution methods
    
    async def _run_predictive_analysis(self, parameters: Dict[str, Any]):
        """Run predictive analysis task"""
        try:
            predictions = await predictive_analytics.generate_24hour_predictions()
            
            # Update autonomous agent with new predictions
            autonomous_bed_agent.predictions = predictions
            
            # Broadcast predictions to dashboard
            if websocket_manager:
                await websocket_manager.broadcast_to_all({
                    'type': 'predictive_analysis_update',
                    'predictions': [autonomous_bed_agent._prediction_to_dict(p) for p in predictions],
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"🔮 Predictive analysis completed: {len(predictions)} predictions generated")
            
        except Exception as e:
            logger.error(f"Error in predictive analysis task: {e}")
            raise

    async def _process_bed_assignments(self, parameters: Dict[str, Any]):
        """Process pending bed assignments"""
        try:
            # Check for patients without beds
            with SessionLocal() as db:
                unassigned_patients = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.current_bed_id.is_(None)
                ).all()

                for patient in unassigned_patients:
                    # Determine priority based on patient condition
                    priority = AssignmentPriority.MEDIUM
                    condition = patient.condition.lower() if patient.condition else ""

                    if any(keyword in condition for keyword in ['emergency', 'critical', 'trauma']):
                        priority = AssignmentPriority.EMERGENCY
                    elif any(keyword in condition for keyword in ['urgent', 'icu']):
                        priority = AssignmentPriority.URGENT
                    elif any(keyword in condition for keyword in ['surgery', 'post-op']):
                        priority = AssignmentPriority.HIGH

                    # Request bed assignment
                    await intelligent_bed_assignment.request_bed_assignment(
                        patient_id=patient.patient_id,
                        priority=priority,
                        medical_requirements={
                            'isolation_required': 'isolation' in condition,
                            'monitoring_level': 'high' if 'critical' in condition else 'medium'
                        },
                        preferences={
                            'private_room': patient.age < 18 or 'private' in condition
                        }
                    )

            logger.debug("🛏️ Bed assignment processing completed")

        except Exception as e:
            logger.error(f"Error in bed assignment task: {e}")
            raise

    async def _monitor_capacity(self, parameters: Dict[str, Any]):
        """Monitor bed capacity and generate alerts"""
        try:
            with SessionLocal() as db:
                # Get overall capacity
                total_beds = db.query(Bed).count()
                occupied_beds = db.query(Bed).filter(Bed.status == 'occupied').count()
                occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

                # Check capacity thresholds
                if occupancy_rate >= 95:
                    # Critical capacity - trigger immediate actions
                    await autonomous_bed_agent._queue_autonomous_action(
                        autonomous_bed_agent.AutonomousAction(
                            id=f"critical_capacity_{datetime.now().timestamp()}",
                            action_type=autonomous_bed_agent.ActionType.ALERT_GENERATION,
                            priority=autonomous_bed_agent.ActionPriority.CRITICAL,
                            description="Critical hospital capacity reached",
                            parameters={
                                'occupancy_rate': occupancy_rate,
                                'total_beds': total_beds,
                                'occupied_beds': occupied_beds
                            },
                            scheduled_time=datetime.now(),
                            confidence_score=1.0
                        )
                    )

                # Ward-specific capacity monitoring
                ward_stats = db.query(Bed.ward,
                                    db.func.count(Bed.id).label('total'),
                                    db.func.sum(db.case([(Bed.status == 'occupied', 1)], else_=0)).label('occupied')
                                    ).group_by(Bed.ward).all()

                for ward, total, occupied in ward_stats:
                    ward_occupancy = (occupied / total * 100) if total > 0 else 0

                    if ward_occupancy >= 90:
                        # High ward occupancy
                        await autonomous_bed_agent._queue_autonomous_action(
                            autonomous_bed_agent.AutonomousAction(
                                id=f"ward_capacity_{ward}_{datetime.now().timestamp()}",
                                action_type=autonomous_bed_agent.ActionType.CAPACITY_OPTIMIZATION,
                                priority=autonomous_bed_agent.ActionPriority.HIGH,
                                description=f"High capacity in {ward} ward",
                                parameters={
                                    'ward': ward,
                                    'occupancy_rate': ward_occupancy,
                                    'total_beds': total,
                                    'occupied_beds': occupied
                                },
                                scheduled_time=datetime.now(),
                                confidence_score=0.9
                            )
                        )

            logger.debug("📊 Capacity monitoring completed")

        except Exception as e:
            logger.error(f"Error in capacity monitoring task: {e}")
            raise

    async def _optimize_discharge_planning(self, parameters: Dict[str, Any]):
        """Optimize discharge planning processes"""
        try:
            with SessionLocal() as db:
                # Find patients ready for discharge
                current_time = datetime.now()
                discharge_candidates = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date.isnot(None),
                    Patient.expected_discharge_date <= current_time + timedelta(hours=24)
                ).all()

                for patient in discharge_candidates:
                    # Calculate discharge readiness score
                    hours_until_discharge = (patient.expected_discharge_date - current_time).total_seconds() / 3600

                    if hours_until_discharge <= 6:  # Within 6 hours
                        # Trigger discharge preparation workflow
                        if workflow_engine:
                            await workflow_engine.create_workflow(
                                "discharge_preparation",
                                {
                                    "patient_id": patient.patient_id,
                                    "expected_discharge": patient.expected_discharge_date.isoformat(),
                                    "priority": "high" if hours_until_discharge <= 2 else "medium",
                                    "initiated_by": "autonomous_scheduler"
                                }
                            )

            logger.debug("📋 Discharge planning optimization completed")

        except Exception as e:
            logger.error(f"Error in discharge planning task: {e}")
            raise

    async def _optimize_workflows(self, parameters: Dict[str, Any]):
        """Optimize workflow processes"""
        try:
            # Check for stuck workflows
            if workflow_engine:
                # This would analyze workflow performance and optimize
                # For now, just log the optimization attempt
                logger.debug("⚙️ Workflow optimization completed")

        except Exception as e:
            logger.error(f"Error in workflow optimization task: {e}")
            raise

    async def _monitor_performance(self, parameters: Dict[str, Any]):
        """Monitor system performance"""
        try:
            # Collect performance metrics from all systems
            metrics = {
                'autonomous_agent': autonomous_bed_agent.get_performance_metrics(),
                'bed_assignment': intelligent_bed_assignment.get_assignment_metrics(),
                'predictive_analytics': predictive_analytics.get_model_performance(),
                'scheduler': self.performance_metrics.copy(),
                'timestamp': datetime.now().isoformat()
            }

            # Update health check
            self.performance_metrics['last_health_check'] = datetime.now().isoformat()

            # Broadcast metrics to dashboard
            if websocket_manager:
                await websocket_manager.broadcast_to_all({
                    'type': 'performance_metrics',
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat()
                })

            logger.debug("📈 Performance monitoring completed")

        except Exception as e:
            logger.error(f"Error in performance monitoring task: {e}")
            raise

    async def _sync_data(self, parameters: Dict[str, Any]):
        """Synchronize data across systems"""
        try:
            # This would sync data between different systems
            # For now, just ensure data consistency
            logger.debug("🔄 Data synchronization completed")

        except Exception as e:
            logger.error(f"Error in data sync task: {e}")
            raise

    async def _process_alerts(self, parameters: Dict[str, Any]):
        """Process and manage alerts"""
        try:
            # This would process pending alerts and take actions
            # For now, just log the alert processing
            logger.debug("🚨 Alert processing completed")

        except Exception as e:
            logger.error(f"Error in alert processing task: {e}")
            raise

    # Utility methods

    def _update_task_metrics(self, task: ScheduledTask, execution_time: float, success: bool):
        """Update task execution metrics"""
        try:
            self.performance_metrics['tasks_executed'] += 1

            if success:
                self.performance_metrics['successful_tasks'] += 1
            else:
                self.performance_metrics['failed_tasks'] += 1

            # Update average execution time
            if execution_time > 0:
                current_avg = self.performance_metrics['average_execution_time']
                total_tasks = self.performance_metrics['tasks_executed']
                new_avg = ((current_avg * (total_tasks - 1)) + execution_time) / total_tasks
                self.performance_metrics['average_execution_time'] = new_avg

        except Exception as e:
            logger.error(f"Error updating task metrics: {e}")

    def _log_task_execution(self, task: ScheduledTask, status: str, execution_time: float, error: str = None):
        """Log task execution details"""
        try:
            execution_record = {
                'task_id': task.task_id,
                'task_type': task.task_type.value,
                'priority': task.priority.value,
                'status': status,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat(),
                'retry_count': task.retry_count,
                'error': error
            }

            # Add to task history
            self.task_history.append(execution_record)

            # Keep only last 100 executions
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]

            # Log to database
            with SessionLocal() as db:
                log_entry = AgentLog(
                    agent_name="autonomous_scheduler",
                    action=f"task_execution_{task.task_type.value}",
                    details=f"Task: {task.task_id} | Status: {status} | Time: {execution_time:.2f}s" + (f" | Error: {error}" if error else ""),
                    status=status,
                    timestamp=datetime.now()
                )
                db.add(log_entry)
                db.commit()

        except Exception as e:
            logger.error(f"Error logging task execution: {e}")

    # Public API methods

    def add_task(self, task: ScheduledTask):
        """Add a new scheduled task"""
        self.scheduled_tasks[task.task_id] = task
        if self.running:
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
        logger.info(f"📅 Added scheduled task: {task.task_id}")

    def remove_task(self, task_id: str):
        """Remove a scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"🗑️ Removed scheduled task: {task_id}")

    def enable_task(self, task_id: str):
        """Enable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = True
            logger.info(f"✅ Enabled task: {task_id}")

    def disable_task(self, task_id: str):
        """Disable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = False
            logger.info(f"❌ Disabled task: {task_id}")

    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all scheduled tasks"""
        return {
            'total_tasks': len(self.scheduled_tasks),
            'enabled_tasks': len([t for t in self.scheduled_tasks.values() if t.enabled]),
            'disabled_tasks': len([t for t in self.scheduled_tasks.values() if not t.enabled]),
            'tasks': [
                {
                    'task_id': task.task_id,
                    'task_type': task.task_type.value,
                    'priority': task.priority.value,
                    'enabled': task.enabled,
                    'interval_seconds': task.interval_seconds,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'retry_count': task.retry_count
                }
                for task in self.scheduled_tasks.values()
            ]
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get scheduler performance metrics"""
        return self.performance_metrics.copy()

    def get_task_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent task execution history"""
        return self.task_history[-limit:] if self.task_history else []

    async def force_task_execution(self, task_id: str) -> bool:
        """Force immediate execution of a specific task"""
        try:
            if task_id not in self.scheduled_tasks:
                logger.error(f"Task {task_id} not found")
                return False

            task = self.scheduled_tasks[task_id]
            await self._execute_task(task)

            logger.info(f"🔧 Forced execution of task: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error forcing task execution: {e}")
            return False

    def update_task_interval(self, task_id: str, new_interval_seconds: int):
        """Update the interval for a scheduled task"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            task.interval_seconds = new_interval_seconds

            # Update next run time
            if task.last_run:
                task.next_run = task.last_run + timedelta(seconds=new_interval_seconds)
            else:
                task.next_run = datetime.now() + timedelta(seconds=new_interval_seconds)

            logger.info(f"⏰ Updated interval for task {task_id} to {new_interval_seconds} seconds")

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            health_status = {
                'scheduler_running': self.running,
                'uptime_seconds': self.performance_metrics['system_uptime'],
                'tasks_status': self.get_task_status(),
                'performance_metrics': self.get_performance_metrics(),
                'autonomous_systems': {
                    'bed_agent_running': autonomous_bed_agent.running,
                    'assignment_system_running': intelligent_bed_assignment.running,
                    'alert_system_available': alert_system is not None,
                    'workflow_engine_available': workflow_engine is not None
                },
                'last_health_check': datetime.now().isoformat()
            }

            # Calculate overall health score
            total_tasks = self.performance_metrics['tasks_executed']
            successful_tasks = self.performance_metrics['successful_tasks']
            health_score = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 100

            health_status['health_score'] = health_score
            health_status['status'] = 'healthy' if health_score >= 90 else 'degraded' if health_score >= 70 else 'unhealthy'

            return health_status

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Global instance
autonomous_scheduler = AutonomousScheduler()
