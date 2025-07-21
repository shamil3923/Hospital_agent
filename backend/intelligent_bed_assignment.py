"""
Intelligent Automatic Bed Assignment System
Automatically assigns optimal beds to patients based on medical needs, preferences, and optimization criteria
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

try:
    from .database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from .autonomous_bed_agent import autonomous_bed_agent
    from .alert_system import alert_system, Alert, AlertType, AlertPriority
    from .workflow_engine import workflow_engine
except ImportError:
    from database import SessionLocal, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from autonomous_bed_agent import autonomous_bed_agent
    from alert_system import alert_system, Alert, AlertType, AlertPriority
    from workflow_engine import workflow_engine

logger = logging.getLogger(__name__)


class AssignmentPriority(Enum):
    """Priority levels for bed assignments"""
    EMERGENCY = 1
    URGENT = 2
    HIGH = 3
    MEDIUM = 4
    LOW = 5


class AssignmentCriteria(Enum):
    """Criteria for bed assignment optimization"""
    MEDICAL_NEEDS = "medical_needs"
    PATIENT_PREFERENCE = "patient_preference"
    COST_OPTIMIZATION = "cost_optimization"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"
    INFECTION_CONTROL = "infection_control"
    FAMILY_PROXIMITY = "family_proximity"


@dataclass
class BedMatchScore:
    """Score for how well a bed matches a patient"""
    bed_id: int
    bed_number: str
    ward: str
    bed_type: str
    total_score: float
    criteria_scores: Dict[str, float]
    confidence: float
    assignment_reasons: List[str]
    potential_issues: List[str]


@dataclass
class AssignmentRequest:
    """Request for automatic bed assignment"""
    patient_id: str
    priority: AssignmentPriority
    medical_requirements: Dict[str, Any]
    preferences: Dict[str, Any]
    constraints: Dict[str, Any]
    requested_time: datetime
    deadline: Optional[datetime] = None


class IntelligentBedAssignment:
    """Intelligent automatic bed assignment system"""
    
    def __init__(self):
        self.assignment_queue: List[AssignmentRequest] = []
        self.assignment_history: List[Dict] = []
        self.running = False
        self.assignment_task = None
        
        # Scoring weights for different criteria
        self.criteria_weights = {
            AssignmentCriteria.MEDICAL_NEEDS: 0.35,
            AssignmentCriteria.PATIENT_PREFERENCE: 0.15,
            AssignmentCriteria.COST_OPTIMIZATION: 0.10,
            AssignmentCriteria.WORKFLOW_EFFICIENCY: 0.15,
            AssignmentCriteria.INFECTION_CONTROL: 0.15,
            AssignmentCriteria.FAMILY_PROXIMITY: 0.10
        }
        
        # Performance metrics
        self.metrics = {
            'assignments_made': 0,
            'successful_assignments': 0,
            'average_assignment_time': 0.0,
            'patient_satisfaction_score': 0.0,
            'bed_utilization_improvement': 0.0
        }
    
    async def start_assignment_system(self):
        """Start the automatic bed assignment system"""
        if self.running:
            logger.warning("Bed assignment system is already running")
            return
        
        self.running = True
        logger.info("🛏️ Starting Intelligent Bed Assignment System...")
        
        # Start assignment processing task
        self.assignment_task = asyncio.create_task(self._process_assignment_queue())
        
        logger.info("✅ Intelligent Bed Assignment System started")
    
    async def stop_assignment_system(self):
        """Stop the automatic bed assignment system"""
        self.running = False
        
        if self.assignment_task:
            self.assignment_task.cancel()
            try:
                await self.assignment_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Intelligent Bed Assignment System stopped")
    
    async def request_bed_assignment(self, patient_id: str, priority: AssignmentPriority = AssignmentPriority.MEDIUM, 
                                   medical_requirements: Dict[str, Any] = None, 
                                   preferences: Dict[str, Any] = None,
                                   constraints: Dict[str, Any] = None,
                                   deadline: Optional[datetime] = None) -> str:
        """Request automatic bed assignment for a patient"""
        try:
            request = AssignmentRequest(
                patient_id=patient_id,
                priority=priority,
                medical_requirements=medical_requirements or {},
                preferences=preferences or {},
                constraints=constraints or {},
                requested_time=datetime.now(),
                deadline=deadline
            )
            
            # Add to queue (sorted by priority)
            self.assignment_queue.append(request)
            self.assignment_queue.sort(key=lambda r: r.priority.value)
            
            logger.info(f"🛏️ Bed assignment requested for patient {patient_id} with priority {priority.name}")
            
            return f"assignment_request_{patient_id}_{datetime.now().timestamp()}"
            
        except Exception as e:
            logger.error(f"Error requesting bed assignment: {e}")
            raise
    
    async def _process_assignment_queue(self):
        """Process the bed assignment queue"""
        while self.running:
            try:
                if self.assignment_queue:
                    # Get highest priority request
                    request = self.assignment_queue.pop(0)
                    
                    # Process the assignment
                    await self._process_assignment_request(request)
                
                await asyncio.sleep(5)  # Check queue every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing assignment queue: {e}")
                await asyncio.sleep(10)
    
    async def _process_assignment_request(self, request: AssignmentRequest):
        """Process a single bed assignment request"""
        try:
            start_time = datetime.now()
            
            logger.info(f"🛏️ Processing bed assignment for patient {request.patient_id}")
            
            # Get patient information
            patient = await self._get_patient_info(request.patient_id)
            if not patient:
                logger.error(f"Patient {request.patient_id} not found")
                return
            
            # Find optimal bed
            optimal_bed = await self._find_optimal_bed(patient, request)
            
            if optimal_bed:
                # Execute the assignment
                success = await self._execute_bed_assignment(patient, optimal_bed, request)
                
                if success:
                    # Update metrics
                    assignment_time = (datetime.now() - start_time).total_seconds()
                    self._update_assignment_metrics(assignment_time, True)
                    
                    # Log successful assignment
                    await self._log_assignment(patient, optimal_bed, request, "success")
                    
                    logger.info(f"✅ Successfully assigned bed {optimal_bed.bed_number} to patient {request.patient_id}")
                else:
                    logger.error(f"❌ Failed to execute bed assignment for patient {request.patient_id}")
                    await self._log_assignment(patient, optimal_bed, request, "failed")
            else:
                # No suitable bed found
                await self._handle_no_bed_available(patient, request)
                logger.warning(f"⚠️ No suitable bed found for patient {request.patient_id}")
                
        except Exception as e:
            logger.error(f"Error processing assignment request: {e}")
    
    async def _find_optimal_bed(self, patient: Dict[str, Any], request: AssignmentRequest) -> Optional[BedMatchScore]:
        """Find the optimal bed for a patient"""
        try:
            with SessionLocal() as db:
                # Get all available beds
                available_beds = db.query(Bed).filter(Bed.status == 'vacant').all()
                
                if not available_beds:
                    return None
                
                # Score each bed
                bed_scores = []
                
                for bed in available_beds:
                    score = await self._calculate_bed_match_score(bed, patient, request)
                    if score.total_score > 0:  # Only consider beds with positive scores
                        bed_scores.append(score)
                
                if not bed_scores:
                    return None
                
                # Sort by total score (highest first)
                bed_scores.sort(key=lambda s: s.total_score, reverse=True)
                
                # Return the best match
                return bed_scores[0]
                
        except Exception as e:
            logger.error(f"Error finding optimal bed: {e}")
            return None
    
    async def _calculate_bed_match_score(self, bed: Bed, patient: Dict[str, Any], request: AssignmentRequest) -> BedMatchScore:
        """Calculate how well a bed matches a patient's needs"""
        try:
            criteria_scores = {}
            assignment_reasons = []
            potential_issues = []
            
            # Medical needs scoring
            medical_score = await self._score_medical_needs(bed, patient, request.medical_requirements)
            criteria_scores[AssignmentCriteria.MEDICAL_NEEDS.value] = medical_score
            
            # Patient preference scoring
            preference_score = await self._score_patient_preferences(bed, patient, request.preferences)
            criteria_scores[AssignmentCriteria.PATIENT_PREFERENCE.value] = preference_score
            
            # Cost optimization scoring
            cost_score = await self._score_cost_optimization(bed, patient)
            criteria_scores[AssignmentCriteria.COST_OPTIMIZATION.value] = cost_score
            
            # Workflow efficiency scoring
            workflow_score = await self._score_workflow_efficiency(bed, patient)
            criteria_scores[AssignmentCriteria.WORKFLOW_EFFICIENCY.value] = workflow_score
            
            # Infection control scoring
            infection_score = await self._score_infection_control(bed, patient)
            criteria_scores[AssignmentCriteria.INFECTION_CONTROL.value] = infection_score
            
            # Family proximity scoring
            family_score = await self._score_family_proximity(bed, patient)
            criteria_scores[AssignmentCriteria.FAMILY_PROXIMITY.value] = family_score
            
            # Calculate weighted total score
            total_score = 0.0
            for criteria, score in criteria_scores.items():
                weight = self.criteria_weights.get(AssignmentCriteria(criteria), 0.1)
                total_score += score * weight
            
            # Generate assignment reasons
            if medical_score > 80:
                assignment_reasons.append(f"Excellent medical fit for {bed.bed_type} bed")
            if preference_score > 70:
                assignment_reasons.append("Matches patient preferences")
            if workflow_score > 75:
                assignment_reasons.append("Optimizes workflow efficiency")
            
            # Identify potential issues
            if medical_score < 50:
                potential_issues.append("May not fully meet medical requirements")
            if infection_score < 60:
                potential_issues.append("Infection control considerations")
            if cost_score < 40:
                potential_issues.append("Higher cost option")
            
            # Calculate confidence based on score consistency
            score_values = list(criteria_scores.values())
            confidence = min(1.0, (total_score / 100.0) * (1 - (max(score_values) - min(score_values)) / 100.0))
            
            return BedMatchScore(
                bed_id=bed.id,
                bed_number=bed.bed_number,
                ward=bed.ward,
                bed_type=bed.bed_type,
                total_score=total_score,
                criteria_scores=criteria_scores,
                confidence=confidence,
                assignment_reasons=assignment_reasons,
                potential_issues=potential_issues
            )
            
        except Exception as e:
            logger.error(f"Error calculating bed match score: {e}")
            return BedMatchScore(
                bed_id=bed.id,
                bed_number=bed.bed_number,
                ward=bed.ward,
                bed_type=bed.bed_type,
                total_score=0.0,
                criteria_scores={},
                confidence=0.0,
                assignment_reasons=[],
                potential_issues=["Error in scoring calculation"]
            )

    # Scoring methods for different criteria

    async def _score_medical_needs(self, bed: Bed, patient: Dict[str, Any], medical_requirements: Dict[str, Any]) -> float:
        """Score bed based on medical needs compatibility"""
        try:
            score = 50.0  # Base score

            patient_condition = patient.get('condition', '').lower()
            bed_type = bed.bed_type.lower()

            # Critical care matching
            if 'icu' in patient_condition or 'critical' in patient_condition:
                if bed_type == 'icu':
                    score += 40
                elif bed_type in ['emergency', 'step-down']:
                    score += 20
                else:
                    score -= 30

            # Emergency care matching
            elif 'emergency' in patient_condition or 'trauma' in patient_condition:
                if bed_type == 'emergency':
                    score += 35
                elif bed_type == 'icu':
                    score += 25
                else:
                    score -= 20

            # Surgical patients
            elif 'surgery' in patient_condition or 'post-op' in patient_condition:
                if bed_type in ['surgical', 'general']:
                    score += 30
                elif bed_type == 'icu':
                    score += 15
                else:
                    score -= 10

            # Pediatric patients
            if patient.get('age', 0) < 18:
                if bed.ward.lower() == 'pediatric':
                    score += 25
                else:
                    score -= 15

            # Maternity patients
            if 'maternity' in patient_condition or 'obstetric' in patient_condition:
                if bed.ward.lower() == 'maternity':
                    score += 30
                else:
                    score -= 25

            # Medical requirements
            if medical_requirements.get('isolation_required'):
                if bed.private_room:
                    score += 20
                else:
                    score -= 30

            if medical_requirements.get('monitoring_level') == 'high':
                if bed_type in ['icu', 'step-down']:
                    score += 15
                else:
                    score -= 10

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring medical needs: {e}")
            return 50.0

    async def _score_patient_preferences(self, bed: Bed, patient: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Score bed based on patient preferences"""
        try:
            score = 50.0  # Base score

            # Private room preference
            if preferences.get('private_room'):
                if bed.private_room:
                    score += 30
                else:
                    score -= 20

            # Ward preference
            preferred_ward = preferences.get('preferred_ward')
            if preferred_ward and bed.ward.lower() == preferred_ward.lower():
                score += 25

            # Floor preference
            preferred_floor = preferences.get('preferred_floor')
            if preferred_floor and hasattr(bed, 'floor') and bed.floor == preferred_floor:
                score += 15

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring patient preferences: {e}")
            return 50.0

    async def _score_cost_optimization(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Score bed based on cost optimization"""
        try:
            score = 50.0  # Base score

            # Private rooms are more expensive
            if bed.private_room:
                if patient.get('insurance_type') == 'premium':
                    score += 20
                else:
                    score -= 15
            else:
                score += 10  # Shared rooms are more cost-effective

            # ICU beds are most expensive
            if bed.bed_type.lower() == 'icu':
                patient_condition = patient.get('condition', '').lower()
                if 'critical' in patient_condition or 'icu' in patient_condition:
                    score += 10  # Justified cost
                else:
                    score -= 20  # Unnecessary cost

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring cost optimization: {e}")
            return 50.0

    async def _score_workflow_efficiency(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Score bed based on workflow efficiency"""
        try:
            score = 50.0  # Base score

            # Ward specialization efficiency
            patient_condition = patient.get('condition', '').lower()
            if 'cardiac' in patient_condition and bed.ward.lower() == 'cardiac':
                score += 20
            elif 'neuro' in patient_condition and bed.ward.lower() == 'neurology':
                score += 20
            elif 'ortho' in patient_condition and bed.ward.lower() == 'orthopedic':
                score += 20

            # Bed turnover efficiency
            if bed.last_updated:
                hours_vacant = (datetime.now() - bed.last_updated).total_seconds() / 3600
                score += min(15, hours_vacant)

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring workflow efficiency: {e}")
            return 50.0

    async def _score_infection_control(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Score bed based on infection control requirements"""
        try:
            score = 50.0  # Base score

            patient_condition = patient.get('condition', '').lower()

            # Isolation requirements
            if 'isolation' in patient_condition or 'infectious' in patient_condition:
                if bed.private_room:
                    score += 30
                else:
                    score -= 40  # Cannot place infectious patients in shared rooms

            # Immunocompromised patients
            if 'immunocompromised' in patient_condition or 'chemo' in patient_condition:
                if bed.private_room:
                    score += 25
                else:
                    score -= 20

            # Recent bed cleaning
            if bed.status == 'vacant' and bed.last_updated:
                hours_since_cleaning = (datetime.now() - bed.last_updated).total_seconds() / 3600
                if hours_since_cleaning < 2:  # Recently cleaned
                    score += 15
                elif hours_since_cleaning > 24:  # Too long since cleaning
                    score -= 10

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring infection control: {e}")
            return 50.0

    async def _score_family_proximity(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Score bed based on family proximity considerations"""
        try:
            score = 50.0  # Base score

            # Family visiting preferences
            if patient.get('frequent_visitors'):
                if bed.private_room:
                    score += 20  # Better for family visits
                else:
                    score -= 10  # Shared rooms less ideal for frequent visitors

            # Pediatric patients need family proximity
            if patient.get('age', 0) < 18:
                if bed.ward.lower() == 'pediatric':
                    score += 15  # Pediatric wards are family-friendly

            # End-of-life care
            if 'palliative' in patient.get('condition', '').lower():
                if bed.private_room:
                    score += 25  # Privacy important for end-of-life care

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring family proximity: {e}")
            return 50.0

    # Assignment execution methods

    async def _execute_bed_assignment(self, patient: Dict[str, Any], bed_match: BedMatchScore, request: AssignmentRequest) -> bool:
        """Execute the actual bed assignment"""
        try:
            with SessionLocal() as db:
                # Get the bed and patient objects
                bed = db.query(Bed).get(bed_match.bed_id)
                patient_obj = db.query(Patient).filter(Patient.patient_id == patient['patient_id']).first()

                if not bed or not patient_obj:
                    logger.error(f"Bed or patient not found for assignment")
                    return False

                # Double-check bed is still available
                if bed.status != 'vacant':
                    logger.warning(f"Bed {bed.bed_number} is no longer available")
                    return False

                # Update bed status
                bed.status = 'occupied'
                bed.patient_id = patient['patient_id']
                bed.admission_time = datetime.now()
                bed.expected_discharge = patient_obj.expected_discharge_date
                bed.last_updated = datetime.now()

                # Update patient
                patient_obj.current_bed_id = bed.id
                patient_obj.status = 'admitted'

                # Create occupancy history record
                history = BedOccupancyHistory(
                    bed_id=bed.id,
                    patient_id=patient['patient_id'],
                    admission_time=datetime.now(),
                    expected_discharge_time=patient_obj.expected_discharge_date
                )

                db.add(bed)
                db.add(patient_obj)
                db.add(history)
                db.commit()

                # Generate assignment alert/notification
                if alert_system:
                    alert = Alert(
                        type=AlertType.BED_AVAILABLE,
                        priority=AlertPriority.MEDIUM,
                        title="Automatic Bed Assignment Completed",
                        message=f"Patient {patient['patient_id']} automatically assigned to bed {bed.bed_number} in {bed.ward}",
                        department=bed.ward,
                        action_required=False,
                        metadata={
                            'patient_id': patient['patient_id'],
                            'bed_number': bed.bed_number,
                            'ward': bed.ward,
                            'assignment_score': bed_match.total_score,
                            'confidence': bed_match.confidence,
                            'assignment_reasons': bed_match.assignment_reasons
                        }
                    )
                    await alert_system.create_alert(alert)

                # Trigger post-assignment workflow
                if workflow_engine:
                    await workflow_engine.create_workflow(
                        "post_bed_assignment",
                        {
                            "patient_id": patient['patient_id'],
                            "bed_id": bed.id,
                            "assignment_type": "automatic",
                            "priority": request.priority.name.lower()
                        }
                    )

                return True

        except Exception as e:
            logger.error(f"Error executing bed assignment: {e}")
            return False

    async def _handle_no_bed_available(self, patient: Dict[str, Any], request: AssignmentRequest):
        """Handle case when no suitable bed is available"""
        try:
            # Generate high-priority alert
            if alert_system:
                alert = Alert(
                    type=AlertType.CAPACITY_CRITICAL,
                    priority=AlertPriority.HIGH if request.priority in [AssignmentPriority.EMERGENCY, AssignmentPriority.URGENT] else AlertPriority.MEDIUM,
                    title="No Bed Available for Patient",
                    message=f"Unable to find suitable bed for patient {patient['patient_id']} with {request.priority.name} priority",
                    department="Bed Management",
                    action_required=True,
                    metadata={
                        'patient_id': patient['patient_id'],
                        'priority': request.priority.name,
                        'medical_requirements': request.medical_requirements,
                        'preferences': request.preferences,
                        'requested_time': request.requested_time.isoformat()
                    }
                )
                await alert_system.create_alert(alert)

            # Add to waiting list or escalate based on priority
            if request.priority in [AssignmentPriority.EMERGENCY, AssignmentPriority.URGENT]:
                # Escalate immediately
                await self._escalate_urgent_assignment(patient, request)
            else:
                # Add back to queue with higher priority
                request.priority = AssignmentPriority.HIGH
                self.assignment_queue.insert(0, request)  # Add to front of queue

        except Exception as e:
            logger.error(f"Error handling no bed available: {e}")

    async def _escalate_urgent_assignment(self, patient: Dict[str, Any], request: AssignmentRequest):
        """Escalate urgent bed assignment requests"""
        try:
            # Try to find beds that could be made available
            with SessionLocal() as db:
                # Look for beds in cleaning that could be expedited
                cleaning_beds = db.query(Bed).filter(Bed.status == 'cleaning').all()

                if cleaning_beds:
                    # Trigger expedited cleaning workflow
                    if workflow_engine:
                        for bed in cleaning_beds[:2]:  # Try first 2 cleaning beds
                            await workflow_engine.create_workflow(
                                "expedited_bed_cleaning",
                                {
                                    "bed_id": bed.id,
                                    "priority": "emergency",
                                    "reason": f"Urgent patient assignment needed for {patient['patient_id']}"
                                }
                            )

                # Look for patients who could be discharged early
                potential_discharges = db.query(Patient).filter(
                    Patient.status == "admitted",
                    Patient.expected_discharge_date <= datetime.now() + timedelta(hours=6)
                ).all()

                if potential_discharges:
                    # Trigger discharge planning workflow
                    if workflow_engine:
                        for discharge_patient in potential_discharges[:2]:
                            await workflow_engine.create_workflow(
                                "expedited_discharge",
                                {
                                    "patient_id": discharge_patient.patient_id,
                                    "priority": "high",
                                    "reason": f"Bed needed for urgent patient {patient['patient_id']}"
                                }
                            )

            logger.info(f"🚨 Escalated urgent bed assignment for patient {patient['patient_id']}")

        except Exception as e:
            logger.error(f"Error escalating urgent assignment: {e}")

    # Utility methods

    async def _get_patient_info(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive patient information"""
        try:
            with SessionLocal() as db:
                patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

                if not patient:
                    return None

                return {
                    'patient_id': patient.patient_id,
                    'name': patient.name,
                    'age': patient.age,
                    'gender': patient.gender,
                    'condition': patient.condition,
                    'status': patient.status,
                    'admission_date': patient.admission_date,
                    'expected_discharge_date': patient.expected_discharge_date,
                    'current_bed_id': patient.current_bed_id,
                    'attending_doctor': patient.attending_doctor,
                    'insurance_type': getattr(patient, 'insurance_type', 'standard'),
                    'expected_length_of_stay': getattr(patient, 'expected_length_of_stay', 3),
                    'requires_frequent_monitoring': getattr(patient, 'requires_frequent_monitoring', False),
                    'frequent_visitors': getattr(patient, 'frequent_visitors', False)
                }

        except Exception as e:
            logger.error(f"Error getting patient info: {e}")
            return None

    async def _log_assignment(self, patient: Dict[str, Any], bed_match: BedMatchScore, request: AssignmentRequest, status: str):
        """Log bed assignment details"""
        try:
            assignment_record = {
                'patient_id': patient['patient_id'],
                'bed_id': bed_match.bed_id,
                'bed_number': bed_match.bed_number,
                'ward': bed_match.ward,
                'bed_type': bed_match.bed_type,
                'assignment_score': bed_match.total_score,
                'confidence': bed_match.confidence,
                'criteria_scores': bed_match.criteria_scores,
                'assignment_reasons': bed_match.assignment_reasons,
                'potential_issues': bed_match.potential_issues,
                'request_priority': request.priority.name,
                'request_time': request.requested_time.isoformat(),
                'assignment_time': datetime.now().isoformat(),
                'status': status
            }

            # Add to assignment history
            self.assignment_history.append(assignment_record)

            # Keep only last 100 assignments
            if len(self.assignment_history) > 100:
                self.assignment_history = self.assignment_history[-100:]

            # Log to database
            with SessionLocal() as db:
                log_entry = AgentLog(
                    agent_name="intelligent_bed_assignment",
                    action="bed_assignment",
                    details=f"Patient {patient['patient_id']} -> Bed {bed_match.bed_number} | Score: {bed_match.total_score:.1f} | Status: {status}",
                    status=status,
                    timestamp=datetime.now()
                )
                db.add(log_entry)
                db.commit()

        except Exception as e:
            logger.error(f"Error logging assignment: {e}")

    def _update_assignment_metrics(self, assignment_time: float, success: bool):
        """Update assignment performance metrics"""
        try:
            self.metrics['assignments_made'] += 1

            if success:
                self.metrics['successful_assignments'] += 1

            # Update average assignment time
            current_avg = self.metrics['average_assignment_time']
            total_assignments = self.metrics['assignments_made']
            new_avg = ((current_avg * (total_assignments - 1)) + assignment_time) / total_assignments
            self.metrics['average_assignment_time'] = new_avg

            # Calculate success rate
            success_rate = (self.metrics['successful_assignments'] / self.metrics['assignments_made']) * 100
            self.metrics['success_rate'] = success_rate

        except Exception as e:
            logger.error(f"Error updating assignment metrics: {e}")

    # Public API methods

    def get_assignment_queue_status(self) -> Dict[str, Any]:
        """Get current assignment queue status"""
        return {
            'queue_length': len(self.assignment_queue),
            'emergency_requests': len([r for r in self.assignment_queue if r.priority == AssignmentPriority.EMERGENCY]),
            'urgent_requests': len([r for r in self.assignment_queue if r.priority == AssignmentPriority.URGENT]),
            'high_requests': len([r for r in self.assignment_queue if r.priority == AssignmentPriority.HIGH]),
            'requests': [
                {
                    'patient_id': r.patient_id,
                    'priority': r.priority.name,
                    'requested_time': r.requested_time.isoformat(),
                    'deadline': r.deadline.isoformat() if r.deadline else None
                }
                for r in self.assignment_queue
            ]
        }

    def get_assignment_metrics(self) -> Dict[str, Any]:
        """Get assignment performance metrics"""
        return self.metrics.copy()

    def get_assignment_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent assignment history"""
        return self.assignment_history[-limit:] if self.assignment_history else []

    async def get_bed_recommendations(self, patient_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get bed recommendations for a patient without assigning"""
        try:
            patient = await self._get_patient_info(patient_id)
            if not patient:
                return []

            # Create a mock request for scoring
            mock_request = AssignmentRequest(
                patient_id=patient_id,
                priority=AssignmentPriority.MEDIUM,
                medical_requirements={},
                preferences={},
                constraints={},
                requested_time=datetime.now()
            )

            with SessionLocal() as db:
                available_beds = db.query(Bed).filter(Bed.status == 'vacant').all()

                bed_scores = []
                for bed in available_beds:
                    score = await self._calculate_bed_match_score(bed, patient, mock_request)
                    bed_scores.append({
                        'bed_id': score.bed_id,
                        'bed_number': score.bed_number,
                        'ward': score.ward,
                        'bed_type': score.bed_type,
                        'total_score': score.total_score,
                        'confidence': score.confidence,
                        'assignment_reasons': score.assignment_reasons,
                        'potential_issues': score.potential_issues,
                        'criteria_scores': score.criteria_scores
                    })

                # Sort by score and return top N
                bed_scores.sort(key=lambda x: x['total_score'], reverse=True)
                return bed_scores[:top_n]

        except Exception as e:
            logger.error(f"Error getting bed recommendations: {e}")
            return []

    async def force_assignment(self, patient_id: str, bed_id: int, override_reason: str) -> bool:
        """Force assignment of a specific bed to a patient (admin override)"""
        try:
            with SessionLocal() as db:
                bed = db.query(Bed).get(bed_id)
                patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

                if not bed or not patient:
                    return False

                if bed.status != 'vacant':
                    logger.warning(f"Forcing assignment to non-vacant bed {bed.bed_number}")

                # Execute assignment
                bed.status = 'occupied'
                bed.patient_id = patient_id
                bed.admission_time = datetime.now()
                bed.expected_discharge = patient.expected_discharge_date
                bed.last_updated = datetime.now()

                patient.current_bed_id = bed.id
                patient.status = 'admitted'

                # Create history record
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

                # Log the forced assignment
                log_entry = AgentLog(
                    agent_name="intelligent_bed_assignment",
                    action="forced_assignment",
                    details=f"FORCED: Patient {patient_id} -> Bed {bed.bed_number} | Reason: {override_reason}",
                    status="forced",
                    timestamp=datetime.now()
                )
                db.add(log_entry)
                db.commit()

                logger.info(f"🔧 Forced assignment: Patient {patient_id} -> Bed {bed.bed_number}")
                return True

        except Exception as e:
            logger.error(f"Error in forced assignment: {e}")
            return False


    # Scoring methods for different criteria

    async def _score_medical_needs(self, bed: Bed, patient: Dict[str, Any], medical_requirements: Dict[str, Any]) -> float:
        """Score bed based on medical needs compatibility"""
        try:
            score = 50.0  # Base score

            patient_condition = patient.get('condition', '').lower()
            bed_type = bed.bed_type.lower()

            # Critical care matching
            if 'icu' in patient_condition or 'critical' in patient_condition:
                if bed_type == 'icu':
                    score += 40
                elif bed_type in ['emergency', 'step-down']:
                    score += 20
                else:
                    score -= 30

            # Emergency care matching
            elif 'emergency' in patient_condition or 'trauma' in patient_condition:
                if bed_type == 'emergency':
                    score += 35
                elif bed_type == 'icu':
                    score += 25
                else:
                    score -= 20

            # Surgical patients
            elif 'surgery' in patient_condition or 'post-op' in patient_condition:
                if bed_type in ['surgical', 'general']:
                    score += 30
                elif bed_type == 'icu':
                    score += 15
                else:
                    score -= 10

            # Pediatric patients
            if patient.get('age', 0) < 18:
                if bed.ward.lower() == 'pediatric':
                    score += 25
                else:
                    score -= 15

            # Maternity patients
            if 'maternity' in patient_condition or 'obstetric' in patient_condition:
                if bed.ward.lower() == 'maternity':
                    score += 30
                else:
                    score -= 25

            # Medical requirements
            if medical_requirements.get('isolation_required'):
                if bed.private_room:
                    score += 20
                else:
                    score -= 30

            if medical_requirements.get('monitoring_level') == 'high':
                if bed_type in ['icu', 'step-down']:
                    score += 15
                else:
                    score -= 10

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring medical needs: {e}")
            return 50.0

    async def _score_patient_preferences(self, bed: Bed, patient: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Score bed based on patient preferences"""
        try:
            score = 50.0  # Base score

            # Private room preference
            if preferences.get('private_room'):
                if bed.private_room:
                    score += 30
                else:
                    score -= 20

            # Ward preference
            preferred_ward = preferences.get('preferred_ward')
            if preferred_ward and bed.ward.lower() == preferred_ward.lower():
                score += 25

            # Floor preference
            preferred_floor = preferences.get('preferred_floor')
            if preferred_floor and hasattr(bed, 'floor') and bed.floor == preferred_floor:
                score += 15

            # Room type preferences
            if preferences.get('quiet_room') and bed.room_number:
                # Assume higher room numbers are quieter (away from elevators/nurses station)
                try:
                    room_num = int(bed.room_number)
                    if room_num % 10 > 5:  # Rooms ending in 6-9 might be quieter
                        score += 10
                except:
                    pass

            # Gender considerations for shared rooms
            if not bed.private_room and preferences.get('gender_preference'):
                # This would require checking other patients in the room
                # Simplified for now
                score += 5

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring patient preferences: {e}")
            return 50.0

    async def _score_cost_optimization(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Score bed based on cost optimization"""
        try:
            score = 50.0  # Base score

            # Private rooms are more expensive
            if bed.private_room:
                if patient.get('insurance_type') == 'premium':
                    score += 20
                else:
                    score -= 15
            else:
                score += 10  # Shared rooms are more cost-effective

            # ICU beds are most expensive
            if bed.bed_type.lower() == 'icu':
                patient_condition = patient.get('condition', '').lower()
                if 'critical' in patient_condition or 'icu' in patient_condition:
                    score += 10  # Justified cost
                else:
                    score -= 20  # Unnecessary cost

            # General beds are most cost-effective
            elif bed.bed_type.lower() == 'general':
                score += 15

            # Consider length of stay
            expected_los = patient.get('expected_length_of_stay', 3)
            if expected_los > 7 and bed.private_room:
                score -= 10  # Long stays in private rooms are expensive

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring cost optimization: {e}")
            return 50.0

    async def _score_workflow_efficiency(self, bed: Bed, patient: Dict[str, Any]) -> float:
        """Score bed based on workflow efficiency"""
        try:
            score = 50.0  # Base score

            # Proximity to nursing station (if available)
            if hasattr(bed, 'distance_to_nursing_station'):
                distance = bed.distance_to_nursing_station
                if patient.get('requires_frequent_monitoring'):
                    score += max(0, 20 - distance * 2)  # Closer is better for high-need patients
                else:
                    score += min(20, distance)  # Farther is fine for stable patients

            # Ward specialization efficiency
            patient_condition = patient.get('condition', '').lower()
            if 'cardiac' in patient_condition and bed.ward.lower() == 'cardiac':
                score += 20
            elif 'neuro' in patient_condition and bed.ward.lower() == 'neurology':
                score += 20
            elif 'ortho' in patient_condition and bed.ward.lower() == 'orthopedic':
                score += 20

            # Bed turnover efficiency
            # Beds that have been vacant longer are better for workflow
            if bed.last_updated:
                hours_vacant = (datetime.now() - bed.last_updated).total_seconds() / 3600
                score += min(15, hours_vacant)

            # Room occupancy efficiency
            if not bed.private_room:
                # Check if room has other patients (would need room occupancy data)
                # For now, assume shared rooms are more efficient
                score += 10

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error scoring workflow efficiency: {e}")
            return 50.0

# Global instance
intelligent_bed_assignment = IntelligentBedAssignment()
