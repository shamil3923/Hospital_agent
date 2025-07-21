"""
Autonomous Bed Management Agent
Proactively manages all bed-related operations without human intervention
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from .alert_system import alert_system, Alert, AlertType, AlertPriority
    from .workflow_engine import workflow_engine
    from .websocket_manager import websocket_manager
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from alert_system import alert_system, Alert, AlertType, AlertPriority
    from workflow_engine import workflow_engine
    from websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of autonomous actions"""
    BED_ASSIGNMENT = "bed_assignment"
    DISCHARGE_PLANNING = "discharge_planning"
    CAPACITY_OPTIMIZATION = "capacity_optimization"
    CLEANING_SCHEDULE = "cleaning_schedule"
    ALERT_GENERATION = "alert_generation"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    WORKFLOW_TRIGGER = "workflow_trigger"


class ActionPriority(Enum):
    """Priority levels for autonomous actions"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AutonomousAction:
    """Represents an autonomous action taken by the agent"""
    id: str
    action_type: ActionType
    priority: ActionPriority
    description: str
    parameters: Dict[str, Any]
    scheduled_time: datetime
    executed_time: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed
    result: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0


@dataclass
class BedPrediction:
    """Bed occupancy prediction for future time periods"""
    timestamp: datetime
    ward: str
    bed_type: str
    predicted_occupancy: int
    total_beds: int
    occupancy_rate: float
    confidence: float
    risk_level: str  # low, medium, high, critical


class AutonomousBedAgent:
    """Fully autonomous bed management agent"""
    
    def __init__(self):
        self.running = False
        self.action_queue: List[AutonomousAction] = []
        self.predictions: List[BedPrediction] = []
        self.autonomous_tasks: List = []
        self.decision_history: List[Dict] = []
        self.performance_metrics = {
            'actions_taken': 0,
            'successful_predictions': 0,
            'beds_assigned': 0,
            'capacity_optimizations': 0,
            'alerts_generated': 0,
            'average_response_time': 0.0
        }
        
        # Configuration
        self.prediction_window_hours = 24
        self.action_interval_seconds = 30  # Check for actions every 30 seconds
        self.prediction_interval_minutes = 15  # Update predictions every 15 minutes
        self.capacity_threshold_critical = 95  # % occupancy
        self.capacity_threshold_high = 85
        
    async def start_autonomous_operations(self):
        """Start all autonomous operations"""
        if self.running:
            logger.warning("Autonomous bed agent is already running")
            return
            
        self.running = True
        logger.info("🤖 Starting Autonomous Bed Management Agent...")
        
        # Start all autonomous tasks
        self.autonomous_tasks = [
            asyncio.create_task(self._continuous_monitoring()),
            asyncio.create_task(self._predictive_analysis_loop()),
            asyncio.create_task(self._autonomous_action_executor()),
            asyncio.create_task(self._capacity_optimization_loop()),
            asyncio.create_task(self._automatic_bed_assignment_loop()),
            asyncio.create_task(self._discharge_planning_loop()),
            asyncio.create_task(self._performance_monitoring())
        ]
        
        logger.info("✅ Autonomous Bed Management Agent started successfully")
        
        # Log the startup
        await self._log_autonomous_action(
            ActionType.WORKFLOW_TRIGGER,
            "Autonomous agent startup",
            {"startup_time": datetime.now().isoformat()}
        )
    
    async def stop_autonomous_operations(self):
        """Stop all autonomous operations"""
        self.running = False
        
        # Cancel all tasks
        for task in self.autonomous_tasks:
            task.cancel()
        
        await asyncio.gather(*self.autonomous_tasks, return_exceptions=True)
        self.autonomous_tasks.clear()
        
        logger.info("🛑 Autonomous Bed Management Agent stopped")
    
    async def _continuous_monitoring(self):
        """Continuously monitor hospital bed status and make autonomous decisions"""
        while self.running:
            try:
                start_time = datetime.now()
                
                # Get current bed status
                bed_status = await self._get_current_bed_status()
                
                # Analyze current situation and generate actions
                actions = await self._analyze_and_generate_actions(bed_status)
                
                # Add actions to queue
                for action in actions:
                    await self._queue_autonomous_action(action)
                
                # Update performance metrics
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_performance_metrics('monitoring', response_time)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
            
            await asyncio.sleep(self.action_interval_seconds)
    
    async def _predictive_analysis_loop(self):
        """Continuously update bed occupancy predictions"""
        while self.running:
            try:
                logger.info("🔮 Running predictive analysis...")
                
                # Generate 24-hour predictions
                predictions = await self._generate_24hour_predictions()
                self.predictions = predictions
                
                # Analyze predictions for potential issues
                critical_predictions = [p for p in predictions if p.risk_level in ['high', 'critical']]
                
                if critical_predictions:
                    # Generate proactive actions based on predictions
                    for prediction in critical_predictions:
                        await self._handle_critical_prediction(prediction)
                
                # Broadcast predictions to dashboard
                if websocket_manager:
                    await websocket_manager.broadcast_to_all({
                        'type': 'bed_predictions',
                        'predictions': [self._prediction_to_dict(p) for p in predictions],
                        'timestamp': datetime.now().isoformat()
                    })
                
                logger.info(f"✅ Generated {len(predictions)} bed predictions")
                
            except Exception as e:
                logger.error(f"Error in predictive analysis: {e}")
            
            await asyncio.sleep(self.prediction_interval_minutes * 60)
    
    async def _autonomous_action_executor(self):
        """Execute queued autonomous actions"""
        while self.running:
            try:
                if self.action_queue:
                    # Sort actions by priority and scheduled time
                    self.action_queue.sort(key=lambda a: (a.priority.value, a.scheduled_time))
                    
                    # Execute ready actions
                    current_time = datetime.now()
                    ready_actions = [a for a in self.action_queue if a.scheduled_time <= current_time and a.status == "pending"]
                    
                    for action in ready_actions:
                        await self._execute_autonomous_action(action)
                        self.action_queue.remove(action)
                
            except Exception as e:
                logger.error(f"Error in action executor: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def _capacity_optimization_loop(self):
        """Continuously optimize bed capacity utilization"""
        while self.running:
            try:
                # Analyze current capacity utilization
                optimization_actions = await self._analyze_capacity_optimization()
                
                for action in optimization_actions:
                    await self._queue_autonomous_action(action)
                
            except Exception as e:
                logger.error(f"Error in capacity optimization: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def _automatic_bed_assignment_loop(self):
        """Automatically assign beds to patients without beds"""
        while self.running:
            try:
                # Find patients without beds
                unassigned_patients = await self._get_unassigned_patients()
                
                for patient in unassigned_patients:
                    # Find optimal bed for patient
                    optimal_bed = await self._find_optimal_bed_for_patient(patient)
                    
                    if optimal_bed:
                        # Create autonomous bed assignment action
                        action = AutonomousAction(
                            id=f"bed_assign_{patient['patient_id']}_{datetime.now().timestamp()}",
                            action_type=ActionType.BED_ASSIGNMENT,
                            priority=ActionPriority.HIGH,
                            description=f"Auto-assign bed {optimal_bed['bed_number']} to patient {patient['patient_id']}",
                            parameters={
                                'patient_id': patient['patient_id'],
                                'bed_id': optimal_bed['id'],
                                'assignment_reason': 'autonomous_optimization',
                                'confidence': optimal_bed.get('match_confidence', 0.8)
                            },
                            scheduled_time=datetime.now(),
                            confidence_score=optimal_bed.get('match_confidence', 0.8)
                        )
                        
                        await self._queue_autonomous_action(action)
                
            except Exception as e:
                logger.error(f"Error in automatic bed assignment: {e}")
            
            await asyncio.sleep(120)  # Check every 2 minutes
    
    async def _discharge_planning_loop(self):
        """Proactively plan and optimize discharge processes"""
        while self.running:
            try:
                # Identify patients ready for discharge
                discharge_candidates = await self._identify_discharge_candidates()
                
                for candidate in discharge_candidates:
                    # Create discharge planning action
                    action = AutonomousAction(
                        id=f"discharge_plan_{candidate['patient_id']}_{datetime.now().timestamp()}",
                        action_type=ActionType.DISCHARGE_PLANNING,
                        priority=ActionPriority.MEDIUM,
                        description=f"Plan discharge for patient {candidate['patient_id']}",
                        parameters={
                            'patient_id': candidate['patient_id'],
                            'bed_id': candidate['bed_id'],
                            'predicted_discharge': candidate['predicted_discharge'],
                            'confidence': candidate['confidence']
                        },
                        scheduled_time=datetime.now(),
                        confidence_score=candidate['confidence']
                    )
                    
                    await self._queue_autonomous_action(action)
                
            except Exception as e:
                logger.error(f"Error in discharge planning: {e}")
            
            await asyncio.sleep(600)  # Check every 10 minutes

    async def _performance_monitoring(self):
        """Monitor and report autonomous agent performance"""
        while self.running:
            try:
                # Calculate performance metrics
                metrics = await self._calculate_performance_metrics()

                # Log performance
                logger.info(f"🤖 Autonomous Agent Performance: {metrics}")

                # Broadcast metrics to dashboard
                if websocket_manager:
                    await websocket_manager.broadcast_to_all({
                        'type': 'autonomous_metrics',
                        'metrics': metrics,
                        'timestamp': datetime.now().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")

            await asyncio.sleep(300)  # Report every 5 minutes

    # Core autonomous decision-making methods

    async def _get_current_bed_status(self) -> Dict[str, Any]:
        """Get comprehensive current bed status"""
        try:
            with SessionLocal() as db:
                # Get all beds with current status
                beds = db.query(Bed).all()

                # Calculate occupancy by ward and type
                ward_occupancy = {}
                type_occupancy = {}

                for bed in beds:
                    # Ward occupancy
                    if bed.ward not in ward_occupancy:
                        ward_occupancy[bed.ward] = {'total': 0, 'occupied': 0, 'available': 0}

                    ward_occupancy[bed.ward]['total'] += 1
                    if bed.status == 'occupied':
                        ward_occupancy[bed.ward]['occupied'] += 1
                    elif bed.status == 'vacant':
                        ward_occupancy[bed.ward]['available'] += 1

                    # Type occupancy
                    if bed.bed_type not in type_occupancy:
                        type_occupancy[bed.bed_type] = {'total': 0, 'occupied': 0, 'available': 0}

                    type_occupancy[bed.bed_type]['total'] += 1
                    if bed.status == 'occupied':
                        type_occupancy[bed.bed_type]['occupied'] += 1
                    elif bed.status == 'vacant':
                        type_occupancy[bed.bed_type]['available'] += 1

                # Calculate occupancy rates
                for ward_data in ward_occupancy.values():
                    ward_data['occupancy_rate'] = (ward_data['occupied'] / ward_data['total'] * 100) if ward_data['total'] > 0 else 0

                for type_data in type_occupancy.values():
                    type_data['occupancy_rate'] = (type_data['occupied'] / type_data['total'] * 100) if type_data['total'] > 0 else 0

                return {
                    'beds': [self._bed_to_dict(bed) for bed in beds],
                    'ward_occupancy': ward_occupancy,
                    'type_occupancy': type_occupancy,
                    'total_beds': len(beds),
                    'total_occupied': sum(1 for bed in beds if bed.status == 'occupied'),
                    'total_available': sum(1 for bed in beds if bed.status == 'vacant'),
                    'overall_occupancy_rate': (sum(1 for bed in beds if bed.status == 'occupied') / len(beds) * 100) if beds else 0,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting bed status: {e}")
            return {'error': str(e)}

    async def _analyze_and_generate_actions(self, bed_status: Dict[str, Any]) -> List[AutonomousAction]:
        """Analyze current bed status and generate autonomous actions"""
        actions = []

        try:
            if 'error' in bed_status:
                return actions

            current_time = datetime.now()
            overall_occupancy = bed_status.get('overall_occupancy_rate', 0)

            # Critical capacity alert and action
            if overall_occupancy >= self.capacity_threshold_critical:
                actions.append(AutonomousAction(
                    id=f"critical_capacity_{current_time.timestamp()}",
                    action_type=ActionType.ALERT_GENERATION,
                    priority=ActionPriority.CRITICAL,
                    description="Critical bed capacity reached - immediate action required",
                    parameters={
                        'occupancy_rate': overall_occupancy,
                        'alert_type': 'critical_capacity',
                        'recommended_actions': ['expedite_discharges', 'activate_overflow_protocol', 'contact_management']
                    },
                    scheduled_time=current_time,
                    confidence_score=1.0
                ))

            # High capacity optimization
            elif overall_occupancy >= self.capacity_threshold_high:
                actions.append(AutonomousAction(
                    id=f"capacity_optimization_{current_time.timestamp()}",
                    action_type=ActionType.CAPACITY_OPTIMIZATION,
                    priority=ActionPriority.HIGH,
                    description="High bed occupancy - optimize capacity utilization",
                    parameters={
                        'occupancy_rate': overall_occupancy,
                        'optimization_type': 'high_capacity'
                    },
                    scheduled_time=current_time,
                    confidence_score=0.9
                ))

            # Ward-specific actions
            for ward, ward_data in bed_status.get('ward_occupancy', {}).items():
                ward_occupancy = ward_data.get('occupancy_rate', 0)

                if ward_occupancy >= 95:
                    actions.append(AutonomousAction(
                        id=f"ward_critical_{ward}_{current_time.timestamp()}",
                        action_type=ActionType.ALERT_GENERATION,
                        priority=ActionPriority.CRITICAL,
                        description=f"Critical capacity in {ward} ward",
                        parameters={
                            'ward': ward,
                            'occupancy_rate': ward_occupancy,
                            'available_beds': ward_data.get('available', 0)
                        },
                        scheduled_time=current_time,
                        confidence_score=1.0
                    ))

            # Bed type specific actions
            for bed_type, type_data in bed_status.get('type_occupancy', {}).items():
                type_occupancy = type_data.get('occupancy_rate', 0)

                if bed_type in ['ICU', 'Emergency'] and type_occupancy >= 90:
                    actions.append(AutonomousAction(
                        id=f"critical_bedtype_{bed_type}_{current_time.timestamp()}",
                        action_type=ActionType.ALERT_GENERATION,
                        priority=ActionPriority.CRITICAL,
                        description=f"Critical {bed_type} bed shortage",
                        parameters={
                            'bed_type': bed_type,
                            'occupancy_rate': type_occupancy,
                            'available_beds': type_data.get('available', 0)
                        },
                        scheduled_time=current_time,
                        confidence_score=1.0
                    ))

            # Check for beds stuck in cleaning status
            cleaning_beds = [bed for bed in bed_status.get('beds', []) if bed.get('status') == 'cleaning']
            for bed in cleaning_beds:
                last_updated = datetime.fromisoformat(bed.get('last_updated', current_time.isoformat()))
                if (current_time - last_updated).total_seconds() > 7200:  # 2 hours
                    actions.append(AutonomousAction(
                        id=f"cleaning_overdue_{bed['id']}_{current_time.timestamp()}",
                        action_type=ActionType.WORKFLOW_TRIGGER,
                        priority=ActionPriority.HIGH,
                        description=f"Bed {bed['bed_number']} cleaning overdue",
                        parameters={
                            'bed_id': bed['id'],
                            'bed_number': bed['bed_number'],
                            'hours_overdue': (current_time - last_updated).total_seconds() / 3600
                        },
                        scheduled_time=current_time,
                        confidence_score=1.0
                    ))

        except Exception as e:
            logger.error(f"Error analyzing bed status: {e}")

        return actions

    async def _generate_24hour_predictions(self) -> List[BedPrediction]:
        """Generate 24-hour bed occupancy predictions"""
        predictions = []

        try:
            with SessionLocal() as db:
                current_time = datetime.now()

                # Get current bed status
                beds = db.query(Bed).all()

                # Get patients with expected discharge dates
                patients = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date.isnot(None)
                ).all()

                # Get historical occupancy patterns (simplified)
                historical_data = db.query(BedOccupancyHistory).filter(
                    BedOccupancyHistory.admission_time >= current_time - timedelta(days=30)
                ).all()

                # Generate predictions for each hour in next 24 hours
                for hour_offset in range(24):
                    prediction_time = current_time + timedelta(hours=hour_offset)

                    # Group by ward and bed type
                    ward_predictions = {}

                    for bed in beds:
                        ward = bed.ward
                        bed_type = bed.bed_type

                        if ward not in ward_predictions:
                            ward_predictions[ward] = {}
                        if bed_type not in ward_predictions[ward]:
                            ward_predictions[ward][bed_type] = {
                                'total_beds': 0,
                                'predicted_occupied': 0,
                                'current_occupied': 0
                            }

                        ward_predictions[ward][bed_type]['total_beds'] += 1

                        # Current occupancy
                        if bed.status == 'occupied':
                            ward_predictions[ward][bed_type]['current_occupied'] += 1

                            # Check if patient will be discharged by prediction time
                            patient = next((p for p in patients if p.current_bed_id == bed.id), None)
                            if patient and patient.expected_discharge_date:
                                if patient.expected_discharge_date <= prediction_time:
                                    # Patient will be discharged, bed becomes available
                                    continue

                            # Patient still occupying bed
                            ward_predictions[ward][bed_type]['predicted_occupied'] += 1

                    # Create predictions for each ward/bed_type combination
                    for ward, bed_types in ward_predictions.items():
                        for bed_type, data in bed_types.items():
                            total_beds = data['total_beds']
                            predicted_occupied = data['predicted_occupied']
                            occupancy_rate = (predicted_occupied / total_beds * 100) if total_beds > 0 else 0

                            # Determine risk level
                            if occupancy_rate >= 95:
                                risk_level = "critical"
                            elif occupancy_rate >= 85:
                                risk_level = "high"
                            elif occupancy_rate >= 70:
                                risk_level = "medium"
                            else:
                                risk_level = "low"

                            # Calculate confidence based on data availability
                            confidence = min(0.9, 0.5 + (len(historical_data) / 100))

                            prediction = BedPrediction(
                                timestamp=prediction_time,
                                ward=ward,
                                bed_type=bed_type,
                                predicted_occupancy=predicted_occupied,
                                total_beds=total_beds,
                                occupancy_rate=occupancy_rate,
                                confidence=confidence,
                                risk_level=risk_level
                            )

                            predictions.append(prediction)

        except Exception as e:
            logger.error(f"Error generating predictions: {e}")

        return predictions

    async def _handle_critical_prediction(self, prediction: BedPrediction):
        """Handle critical bed occupancy predictions"""
        try:
            current_time = datetime.now()

            # Generate proactive action based on prediction
            action = AutonomousAction(
                id=f"critical_prediction_{prediction.ward}_{prediction.bed_type}_{current_time.timestamp()}",
                action_type=ActionType.PREDICTIVE_ANALYSIS,
                priority=ActionPriority.CRITICAL if prediction.risk_level == "critical" else ActionPriority.HIGH,
                description=f"Critical bed shortage predicted for {prediction.ward} {prediction.bed_type} at {prediction.timestamp.strftime('%H:%M')}",
                parameters={
                    'prediction_time': prediction.timestamp.isoformat(),
                    'ward': prediction.ward,
                    'bed_type': prediction.bed_type,
                    'predicted_occupancy_rate': prediction.occupancy_rate,
                    'available_beds': prediction.total_beds - prediction.predicted_occupancy,
                    'confidence': prediction.confidence,
                    'recommended_actions': [
                        'expedite_discharges',
                        'prepare_overflow_beds',
                        'alert_management',
                        'optimize_bed_assignments'
                    ]
                },
                scheduled_time=current_time,
                confidence_score=prediction.confidence
            )

            await self._queue_autonomous_action(action)

            # Also generate immediate alert
            if alert_system:
                alert = Alert(
                    type=AlertType.CAPACITY_CRITICAL,
                    priority=AlertPriority.CRITICAL if prediction.risk_level == "critical" else AlertPriority.HIGH,
                    title=f"Predicted {prediction.bed_type} Bed Shortage",
                    message=f"Critical bed shortage predicted for {prediction.ward} {prediction.bed_type} at {prediction.timestamp.strftime('%H:%M')} - {prediction.occupancy_rate:.1f}% occupancy",
                    department=prediction.ward,
                    action_required=True,
                    metadata={
                        'prediction_time': prediction.timestamp.isoformat(),
                        'predicted_occupancy_rate': prediction.occupancy_rate,
                        'confidence': prediction.confidence,
                        'bed_type': prediction.bed_type
                    }
                )
                await alert_system.create_alert(alert)

        except Exception as e:
            logger.error(f"Error handling critical prediction: {e}")

    async def _get_unassigned_patients(self) -> List[Dict[str, Any]]:
        """Get patients who need bed assignments"""
        try:
            with SessionLocal() as db:
                # Find patients without beds or with pending bed assignments
                unassigned = db.query(Patient).filter(
                    or_(
                        Patient.current_bed_id.is_(None),
                        and_(
                            Patient.status == "admitted",
                            Patient.current_bed_id.is_(None)
                        )
                    )
                ).all()

                return [self._patient_to_dict(patient) for patient in unassigned]

        except Exception as e:
            logger.error(f"Error getting unassigned patients: {e}")
            return []

    async def _find_optimal_bed_for_patient(self, patient: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the optimal bed for a patient using intelligent matching"""
        try:
            with SessionLocal() as db:
                # Get available beds
                available_beds = db.query(Bed).filter(Bed.status == 'vacant').all()

                if not available_beds:
                    return None

                # Score each bed for this patient
                bed_scores = []

                for bed in available_beds:
                    score = await self._calculate_bed_patient_match_score(bed, patient)
                    bed_scores.append({
                        'bed': bed,
                        'score': score,
                        'match_confidence': score / 100.0  # Convert to 0-1 scale
                    })

                # Sort by score (highest first)
                bed_scores.sort(key=lambda x: x['score'], reverse=True)

                if bed_scores and bed_scores[0]['score'] > 50:  # Minimum acceptable score
                    best_match = bed_scores[0]
                    bed_dict = self._bed_to_dict(best_match['bed'])
                    bed_dict['match_confidence'] = best_match['match_confidence']
                    return bed_dict

                return None

        except Exception as e:
            logger.error(f"Error finding optimal bed: {e}")
            return None

    async def _calculate_bed_patient_match_score(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Calculate how well a bed matches a patient's needs"""
        score = 50.0  # Base score

        try:
            # Ward preference (if specified)
            preferred_ward = patient.get('preferred_ward')
            if preferred_ward and bed.ward == preferred_ward:
                score += 30
            elif preferred_ward and bed.ward != preferred_ward:
                score -= 20

            # Bed type matching
            patient_condition = patient.get('condition', '').lower()
            if 'icu' in patient_condition or 'critical' in patient_condition:
                if bed.bed_type == 'ICU':
                    score += 40
                else:
                    score -= 30
            elif 'emergency' in patient_condition:
                if bed.bed_type == 'Emergency':
                    score += 35
                else:
                    score -= 25

            # Private room preference
            if patient.get('private_room_requested') and bed.private_room:
                score += 20
            elif patient.get('private_room_requested') and not bed.private_room:
                score -= 10

            # Gender considerations (if applicable)
            if not bed.private_room:
                # Check if there are other patients in the room with different gender
                # This would require room occupancy data - simplified for now
                pass

            # Distance from nursing station (if available)
            if hasattr(bed, 'distance_from_nursing_station'):
                if patient.get('requires_frequent_monitoring'):
                    score += max(0, 20 - bed.distance_from_nursing_station * 2)

            # Bed availability duration (prefer beds that have been available longer)
            if hasattr(bed, 'last_updated'):
                hours_available = (datetime.now() - bed.last_updated).total_seconds() / 3600
                score += min(10, hours_available)

        except Exception as e:
            logger.error(f"Error calculating bed match score: {e}")

        return max(0, min(100, score))  # Clamp between 0-100

    async def _identify_discharge_candidates(self) -> List[Dict[str, Any]]:
        """Identify patients who are candidates for discharge"""
        candidates = []

        try:
            with SessionLocal() as db:
                current_time = datetime.now()

                # Find patients with expected discharge dates in next 24 hours
                upcoming_discharges = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date.isnot(None),
                    Patient.expected_discharge_date >= current_time,
                    Patient.expected_discharge_date <= current_time + timedelta(hours=24)
                ).all()

                for patient in upcoming_discharges:
                    # Calculate confidence based on various factors
                    confidence = 0.7  # Base confidence

                    # Time until expected discharge
                    time_to_discharge = (patient.expected_discharge_date - current_time).total_seconds() / 3600
                    if time_to_discharge <= 2:  # Within 2 hours
                        confidence += 0.2
                    elif time_to_discharge <= 6:  # Within 6 hours
                        confidence += 0.1

                    # Length of stay (longer stays might be more predictable)
                    if patient.admission_date:
                        stay_duration = (current_time - patient.admission_date).days
                        if stay_duration >= 3:
                            confidence += 0.1

                    candidates.append({
                        'patient_id': patient.patient_id,
                        'bed_id': patient.current_bed_id,
                        'predicted_discharge': patient.expected_discharge_date.isoformat(),
                        'confidence': min(1.0, confidence),
                        'time_to_discharge_hours': time_to_discharge
                    })

        except Exception as e:
            logger.error(f"Error identifying discharge candidates: {e}")

        return candidates

    async def _analyze_capacity_optimization(self) -> List[AutonomousAction]:
        """Analyze and generate capacity optimization actions"""
        actions = []

        try:
            with SessionLocal() as db:
                current_time = datetime.now()

                # Find beds that could be optimized
                beds = db.query(Bed).all()

                # Check for beds in cleaning status too long
                long_cleaning_beds = [
                    bed for bed in beds
                    if bed.status == 'cleaning' and bed.last_updated and
                    (current_time - bed.last_updated).total_seconds() > 3600  # 1 hour
                ]

                for bed in long_cleaning_beds:
                    actions.append(AutonomousAction(
                        id=f"optimize_cleaning_{bed.id}_{current_time.timestamp()}",
                        action_type=ActionType.CAPACITY_OPTIMIZATION,
                        priority=ActionPriority.MEDIUM,
                        description=f"Optimize cleaning process for bed {bed.bed_number}",
                        parameters={
                            'bed_id': bed.id,
                            'bed_number': bed.bed_number,
                            'cleaning_duration_hours': (current_time - bed.last_updated).total_seconds() / 3600,
                            'optimization_type': 'expedite_cleaning'
                        },
                        scheduled_time=current_time,
                        confidence_score=0.8
                    ))

                # Check for underutilized wards
                ward_utilization = {}
                for bed in beds:
                    if bed.ward not in ward_utilization:
                        ward_utilization[bed.ward] = {'total': 0, 'occupied': 0}

                    ward_utilization[bed.ward]['total'] += 1
                    if bed.status == 'occupied':
                        ward_utilization[bed.ward]['occupied'] += 1

                for ward, data in ward_utilization.items():
                    utilization_rate = (data['occupied'] / data['total'] * 100) if data['total'] > 0 else 0

                    if utilization_rate < 30 and data['total'] > 5:  # Low utilization in larger wards
                        actions.append(AutonomousAction(
                            id=f"optimize_ward_{ward}_{current_time.timestamp()}",
                            action_type=ActionType.CAPACITY_OPTIMIZATION,
                            priority=ActionPriority.LOW,
                            description=f"Optimize underutilized {ward} ward",
                            parameters={
                                'ward': ward,
                                'utilization_rate': utilization_rate,
                                'total_beds': data['total'],
                                'occupied_beds': data['occupied'],
                                'optimization_type': 'ward_consolidation'
                            },
                            scheduled_time=current_time,
                            confidence_score=0.6
                        ))

        except Exception as e:
            logger.error(f"Error analyzing capacity optimization: {e}")

        return actions

    # Action execution methods

    async def _queue_autonomous_action(self, action: AutonomousAction):
        """Queue an autonomous action for execution"""
        self.action_queue.append(action)
        logger.info(f"🤖 Queued autonomous action: {action.description}")

        # Log the action
        await self._log_autonomous_action(
            action.action_type,
            action.description,
            action.parameters
        )

    async def _execute_autonomous_action(self, action: AutonomousAction):
        """Execute a specific autonomous action"""
        try:
            action.status = "executing"
            action.executed_time = datetime.now()

            logger.info(f"🤖 Executing autonomous action: {action.description}")

            result = None

            if action.action_type == ActionType.BED_ASSIGNMENT:
                result = await self._execute_bed_assignment(action)
            elif action.action_type == ActionType.DISCHARGE_PLANNING:
                result = await self._execute_discharge_planning(action)
            elif action.action_type == ActionType.CAPACITY_OPTIMIZATION:
                result = await self._execute_capacity_optimization(action)
            elif action.action_type == ActionType.CLEANING_SCHEDULE:
                result = await self._execute_cleaning_schedule(action)
            elif action.action_type == ActionType.ALERT_GENERATION:
                result = await self._execute_alert_generation(action)
            elif action.action_type == ActionType.PREDICTIVE_ANALYSIS:
                result = await self._execute_predictive_analysis(action)
            elif action.action_type == ActionType.WORKFLOW_TRIGGER:
                result = await self._execute_workflow_trigger(action)

            action.result = result
            action.status = "completed" if result and not result.get('error') else "failed"

            # Update performance metrics
            self.performance_metrics['actions_taken'] += 1
            if action.status == "completed":
                if action.action_type == ActionType.BED_ASSIGNMENT:
                    self.performance_metrics['beds_assigned'] += 1
                elif action.action_type == ActionType.CAPACITY_OPTIMIZATION:
                    self.performance_metrics['capacity_optimizations'] += 1
                elif action.action_type == ActionType.ALERT_GENERATION:
                    self.performance_metrics['alerts_generated'] += 1

            # Store in decision history
            self.decision_history.append({
                'action_id': action.id,
                'action_type': action.action_type.value,
                'description': action.description,
                'parameters': action.parameters,
                'result': result,
                'status': action.status,
                'executed_time': action.executed_time.isoformat(),
                'confidence_score': action.confidence_score
            })

            # Keep only last 100 decisions
            if len(self.decision_history) > 100:
                self.decision_history = self.decision_history[-100:]

            logger.info(f"✅ Autonomous action completed: {action.description} - Status: {action.status}")

        except Exception as e:
            action.status = "failed"
            action.result = {'error': str(e)}
            logger.error(f"❌ Autonomous action failed: {action.description} - Error: {e}")

    async def _execute_bed_assignment(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute autonomous bed assignment"""
        try:
            patient_id = action.parameters.get('patient_id')
            bed_id = action.parameters.get('bed_id')

            with SessionLocal() as db:
                # Get patient and bed
                patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
                bed = db.query(Bed).get(bed_id)

                if not patient or not bed:
                    return {'error': 'Patient or bed not found'}

                if bed.status != 'vacant':
                    return {'error': 'Bed is not available'}

                # Assign bed to patient
                bed.status = 'occupied'
                bed.patient_id = patient_id
                bed.admission_time = datetime.now()
                bed.expected_discharge = patient.expected_discharge_date
                bed.last_updated = datetime.now()

                patient.current_bed_id = bed.id

                # Create occupancy history record
                history = BedOccupancyHistory(
                    bed_id=bed.id,
                    patient_id=patient_id,
                    admission_time=datetime.now(),
                    expected_discharge_time=patient.expected_discharge_date
                )

                db.add(bed)
                db.add(patient)
                db.add(history)
                db.commit()

                # Broadcast update
                if websocket_manager:
                    await websocket_manager.broadcast_to_all({
                        'type': 'autonomous_bed_assignment',
                        'bed_number': bed.bed_number,
                        'patient_id': patient_id,
                        'ward': bed.ward,
                        'timestamp': datetime.now().isoformat()
                    })

                return {
                    'success': True,
                    'bed_number': bed.bed_number,
                    'patient_id': patient_id,
                    'ward': bed.ward,
                    'assignment_time': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error executing bed assignment: {e}")
            return {'error': str(e)}

    async def _execute_discharge_planning(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute discharge planning action"""
        try:
            patient_id = action.parameters.get('patient_id')
            bed_id = action.parameters.get('bed_id')

            # Trigger discharge planning workflow
            if workflow_engine:
                workflow_id = await workflow_engine.create_workflow(
                    "discharge_planning",
                    {
                        "patient_id": patient_id,
                        "bed_id": bed_id,
                        "initiated_by": "autonomous_agent",
                        "priority": "high"
                    }
                )

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'patient_id': patient_id,
                    'action': 'discharge_planning_initiated'
                }
            else:
                return {'error': 'Workflow engine not available'}

        except Exception as e:
            logger.error(f"Error executing discharge planning: {e}")
            return {'error': str(e)}

    async def _execute_capacity_optimization(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute capacity optimization action"""
        try:
            optimization_type = action.parameters.get('optimization_type')

            if optimization_type == 'expedite_cleaning':
                bed_id = action.parameters.get('bed_id')

                # Trigger expedited cleaning workflow
                if workflow_engine:
                    workflow_id = await workflow_engine.create_workflow(
                        "expedited_bed_cleaning",
                        {
                            "bed_id": bed_id,
                            "priority": "high",
                            "initiated_by": "autonomous_agent"
                        }
                    )

                    return {
                        'success': True,
                        'workflow_id': workflow_id,
                        'optimization_type': optimization_type,
                        'bed_id': bed_id
                    }

            elif optimization_type == 'ward_consolidation':
                ward = action.parameters.get('ward')

                # This would involve complex bed reassignment logic
                # For now, just log the recommendation
                logger.info(f"🤖 Recommending ward consolidation for {ward}")

                return {
                    'success': True,
                    'optimization_type': optimization_type,
                    'ward': ward,
                    'action': 'recommendation_logged'
                }

            return {'error': f'Unknown optimization type: {optimization_type}'}

        except Exception as e:
            logger.error(f"Error executing capacity optimization: {e}")
            return {'error': str(e)}

    async def _execute_cleaning_schedule(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute cleaning schedule action"""
        try:
            bed_id = action.parameters.get('bed_id')

            if workflow_engine:
                workflow_id = await workflow_engine.create_workflow(
                    "bed_cleaning",
                    {
                        "bed_id": bed_id,
                        "initiated_by": "autonomous_agent",
                        "priority": "medium"
                    }
                )

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'bed_id': bed_id,
                    'action': 'cleaning_scheduled'
                }
            else:
                return {'error': 'Workflow engine not available'}

        except Exception as e:
            logger.error(f"Error executing cleaning schedule: {e}")
            return {'error': str(e)}

    async def _execute_alert_generation(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute alert generation action"""
        try:
            alert_type = action.parameters.get('alert_type', 'general')

            if alert_system:
                alert = Alert(
                    type=AlertType.CAPACITY_CRITICAL if 'critical' in alert_type else AlertType.BED_AVAILABLE,
                    priority=AlertPriority.CRITICAL if action.priority == ActionPriority.CRITICAL else AlertPriority.HIGH,
                    title=f"Autonomous Alert: {action.description}",
                    message=action.description,
                    department=action.parameters.get('ward', 'General'),
                    action_required=True,
                    metadata=action.parameters
                )

                alert_id = await alert_system.create_alert(alert)

                return {
                    'success': True,
                    'alert_id': alert_id,
                    'alert_type': alert_type,
                    'action': 'alert_generated'
                }
            else:
                return {'error': 'Alert system not available'}

        except Exception as e:
            logger.error(f"Error executing alert generation: {e}")
            return {'error': str(e)}

    async def _execute_predictive_analysis(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute predictive analysis action"""
        try:
            # This action typically generates alerts and recommendations
            # The actual prediction was already done, this is the response action

            recommended_actions = action.parameters.get('recommended_actions', [])

            # Execute recommended actions
            results = []
            for rec_action in recommended_actions:
                if rec_action == 'expedite_discharges':
                    # Trigger discharge planning for eligible patients
                    discharge_candidates = await self._identify_discharge_candidates()
                    for candidate in discharge_candidates[:3]:  # Top 3 candidates
                        if workflow_engine:
                            workflow_id = await workflow_engine.create_workflow(
                                "expedited_discharge",
                                {
                                    "patient_id": candidate['patient_id'],
                                    "initiated_by": "autonomous_agent_prediction"
                                }
                            )
                            results.append(f"Expedited discharge workflow {workflow_id} for patient {candidate['patient_id']}")

                elif rec_action == 'prepare_overflow_beds':
                    # This would involve activating overflow capacity
                    logger.info("🤖 Recommending overflow bed preparation")
                    results.append("Overflow bed preparation recommended")

                elif rec_action == 'alert_management':
                    # Generate management alert
                    if alert_system:
                        mgmt_alert = Alert(
                            type=AlertType.CAPACITY_CRITICAL,
                            priority=AlertPriority.CRITICAL,
                            title="Management Alert: Predicted Bed Shortage",
                            message=f"Autonomous agent predicts critical bed shortage: {action.description}",
                            department="Management",
                            action_required=True,
                            metadata=action.parameters
                        )
                        alert_id = await alert_system.create_alert(mgmt_alert)
                        results.append(f"Management alert {alert_id} generated")

            return {
                'success': True,
                'actions_executed': results,
                'prediction_parameters': action.parameters
            }

        except Exception as e:
            logger.error(f"Error executing predictive analysis: {e}")
            return {'error': str(e)}

    async def _execute_workflow_trigger(self, action: AutonomousAction) -> Dict[str, Any]:
        """Execute workflow trigger action"""
        try:
            if workflow_engine:
                # Determine workflow type based on action parameters
                if 'cleaning_overdue' in action.id:
                    workflow_type = "urgent_bed_cleaning"
                else:
                    workflow_type = "general_workflow"

                workflow_id = await workflow_engine.create_workflow(
                    workflow_type,
                    {
                        **action.parameters,
                        "initiated_by": "autonomous_agent",
                        "priority": "high" if action.priority in [ActionPriority.CRITICAL, ActionPriority.HIGH] else "medium"
                    }
                )

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'workflow_type': workflow_type,
                    'action': 'workflow_triggered'
                }
            else:
                return {'error': 'Workflow engine not available'}

        except Exception as e:
            logger.error(f"Error executing workflow trigger: {e}")
            return {'error': str(e)}

    # Utility methods

    async def _log_autonomous_action(self, action_type: ActionType, description: str, parameters: Dict[str, Any]):
        """Log autonomous actions to database"""
        try:
            with SessionLocal() as db:
                log_entry = AgentLog(
                    agent_name="autonomous_bed_agent",
                    action=action_type.value,
                    details=f"{description} | Parameters: {json.dumps(parameters)}",
                    status="autonomous_action",
                    timestamp=datetime.now()
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.error(f"Error logging autonomous action: {e}")

    async def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate and return performance metrics"""
        try:
            # Calculate success rate
            total_actions = len(self.decision_history)
            successful_actions = len([d for d in self.decision_history if d['status'] == 'completed'])
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0

            # Calculate average confidence
            avg_confidence = np.mean([d['confidence_score'] for d in self.decision_history]) if self.decision_history else 0

            # Get current queue size
            queue_size = len(self.action_queue)
            pending_actions = len([a for a in self.action_queue if a.status == 'pending'])

            return {
                **self.performance_metrics,
                'success_rate': success_rate,
                'average_confidence': avg_confidence,
                'total_decisions': total_actions,
                'queue_size': queue_size,
                'pending_actions': pending_actions,
                'predictions_generated': len(self.predictions),
                'last_prediction_time': self.predictions[-1].timestamp.isoformat() if self.predictions else None,
                'uptime_hours': (datetime.now() - datetime.now()).total_seconds() / 3600 if self.running else 0
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return self.performance_metrics

    def _update_performance_metrics(self, operation: str, response_time: float):
        """Update performance metrics"""
        try:
            current_avg = self.performance_metrics['average_response_time']
            total_ops = self.performance_metrics.get('total_operations', 0) + 1

            # Update average response time
            new_avg = ((current_avg * (total_ops - 1)) + response_time) / total_ops
            self.performance_metrics['average_response_time'] = new_avg
            self.performance_metrics['total_operations'] = total_ops

        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    def _bed_to_dict(self, bed: Bed) -> Dict[str, Any]:
        """Convert bed object to dictionary"""
        return {
            'id': bed.id,
            'bed_number': bed.bed_number,
            'ward': bed.ward,
            'bed_type': bed.bed_type,
            'status': bed.status,
            'room_number': bed.room_number,
            'private_room': bed.private_room,
            'patient_id': bed.patient_id,
            'admission_time': bed.admission_time.isoformat() if bed.admission_time else None,
            'expected_discharge': bed.expected_discharge.isoformat() if bed.expected_discharge else None,
            'last_updated': bed.last_updated.isoformat() if bed.last_updated else None
        }

    def _patient_to_dict(self, patient: Patient) -> Dict[str, Any]:
        """Convert patient object to dictionary"""
        return {
            'patient_id': patient.patient_id,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'condition': patient.condition,
            'status': patient.status,
            'admission_date': patient.admission_date.isoformat() if patient.admission_date else None,
            'expected_discharge_date': patient.expected_discharge_date.isoformat() if patient.expected_discharge_date else None,
            'current_bed_id': patient.current_bed_id,
            'attending_doctor': patient.attending_doctor,
            'preferred_ward': getattr(patient, 'preferred_ward', None),
            'private_room_requested': getattr(patient, 'private_room_requested', False),
            'requires_frequent_monitoring': getattr(patient, 'requires_frequent_monitoring', False)
        }

    def _prediction_to_dict(self, prediction: BedPrediction) -> Dict[str, Any]:
        """Convert prediction object to dictionary"""
        return {
            'timestamp': prediction.timestamp.isoformat(),
            'ward': prediction.ward,
            'bed_type': prediction.bed_type,
            'predicted_occupancy': prediction.predicted_occupancy,
            'total_beds': prediction.total_beds,
            'occupancy_rate': prediction.occupancy_rate,
            'confidence': prediction.confidence,
            'risk_level': prediction.risk_level
        }

    # Public API methods

    def get_current_predictions(self) -> List[Dict[str, Any]]:
        """Get current bed occupancy predictions"""
        return [self._prediction_to_dict(p) for p in self.predictions]

    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get recent autonomous decision history"""
        return self.decision_history.copy()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()

    def get_action_queue_status(self) -> Dict[str, Any]:
        """Get current action queue status"""
        return {
            'total_actions': len(self.action_queue),
            'pending': len([a for a in self.action_queue if a.status == 'pending']),
            'executing': len([a for a in self.action_queue if a.status == 'executing']),
            'actions': [
                {
                    'id': a.id,
                    'type': a.action_type.value,
                    'priority': a.priority.value,
                    'description': a.description,
                    'status': a.status,
                    'scheduled_time': a.scheduled_time.isoformat(),
                    'confidence_score': a.confidence_score
                }
                for a in self.action_queue
            ]
        }


# Global instance
autonomous_bed_agent = AutonomousBedAgent()
