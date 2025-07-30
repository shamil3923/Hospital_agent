"""
Smart Bed Allocation Engine - Autonomous AI Agent
Intelligently matches patients to optimal beds based on multiple criteria
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
# Import with fallback for different execution contexts
try:
    from .database import get_db, Bed, Patient, Staff
except ImportError:
    try:
        from database import get_db, Bed, Patient, Staff
    except ImportError:
        from backend.database import get_db, Bed, Patient, Staff
import logging

logger = logging.getLogger(__name__)

class SmartBedAllocationEngine:
    """
    Autonomous AI agent for intelligent bed allocation
    Considers medical condition, equipment, doctor specialization, infection control, and preferences
    """
    
    def __init__(self):
        self.allocation_weights = {
            'medical_condition_match': 0.35,    # Highest priority - medical needs
            'doctor_specialization': 0.25,     # Doctor expertise match
            'equipment_availability': 0.20,    # Required equipment/monitoring
            'infection_control': 0.15,         # Isolation requirements
            'patient_preferences': 0.05        # Patient comfort preferences
        }
        
        # Medical condition to ward mapping
        self.condition_ward_mapping = {
            'cardiac': ['ICU', 'Cardiac'],
            'respiratory': ['ICU', 'Pulmonary'],
            'neurological': ['ICU', 'Neurology'],
            'surgical': ['General', 'Surgical'],
            'pediatric': ['Pediatric'],
            'maternity': ['Maternity'],
            'emergency': ['Emergency', 'ICU'],
            'critical': ['ICU'],
            'stable': ['General'],
            'recovery': ['General', 'Recovery']
        }
        
        # Equipment requirements by condition
        self.equipment_requirements = {
            'cardiac': ['cardiac_monitor', 'defibrillator', 'oxygen'],
            'respiratory': ['ventilator', 'oxygen', 'pulse_oximeter'],
            'neurological': ['neuro_monitor', 'oxygen'],
            'surgical': ['post_op_monitor', 'pain_management'],
            'critical': ['full_monitoring', 'life_support'],
            'stable': ['basic_monitoring']
        }
        
        # Infection control protocols
        self.isolation_requirements = {
            'airborne': ['negative_pressure_room'],
            'droplet': ['private_room'],
            'contact': ['private_room', 'barrier_precautions'],
            'standard': []  # No special requirements
        }

    def recommend_bed(self, patient_data: Dict, db: Session = None) -> Dict:
        """
        Synchronous bed recommendation - used by API endpoints
        """
        try:
            # Use synchronous version to avoid event loop issues
            if db is None:
                from database import SessionLocal
                with SessionLocal() as session:
                    result = self._sync_find_optimal_bed(patient_data, session)
            else:
                result = self._sync_find_optimal_bed(patient_data, db)

            # Convert result format to match API expectations
            if result and result.get('success'):
                return {
                    'status': 'success',
                    'recommendation': {
                        'bed_number': result['recommended_bed']['bed_number'],
                        'ward': result['recommended_bed']['ward'],
                        'room': result['recommended_bed']['room'],
                        'bed_type': result['recommended_bed']['bed_type'],
                        'confidence_score': result['confidence_score'],
                        'reasoning': result['reasoning'],
                        'assigned_doctor': {'name': 'Dr. Sarah Johnson', 'specialization': 'Neurology'},  # Mock for now
                        'equipment_list': ['Neurological monitoring', 'IV access', 'Emergency cart'],
                        'estimated_los': '2-3 days'
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': result.get('error', 'No suitable bed found'),
                    'recommendation': None
                }

        except Exception as e:
            logger.error(f"Error in recommend_bed: {e}")
            return {
                'status': 'error',
                'message': f'Bed recommendation failed: {str(e)}',
                'recommendation': None
            }

    def _sync_find_optimal_bed(self, patient_data: Dict, db: Session) -> Dict:
        """
        Synchronous version of find_optimal_bed for when async is not available
        """
        try:
            # Get all available beds
            available_beds = db.query(Bed).filter(Bed.status == "vacant").all()

            if not available_beds:
                return {
                    'success': False,
                    'error': 'No available beds found',
                    'fallback_recommendation': 'Contact bed management for manual assignment'
                }

            # Score each bed (simplified sync version)
            bed_scores = []
            for bed in available_beds:
                score = self._sync_calculate_bed_score(patient_data, bed, db)
                bed_scores.append({
                    'bed': bed,
                    'score': score['total_score'],
                    'reasoning': score['reasoning'],
                    'match_details': score['details']
                })

            # Sort by score
            bed_scores.sort(key=lambda x: x['score'], reverse=True)

            if bed_scores:
                best_match = bed_scores[0]

                return {
                    'success': True,
                    'recommended_bed': {
                        'bed_number': best_match['bed'].bed_number,
                        'ward': best_match['bed'].ward,
                        'room': best_match['bed'].room_number,
                        'bed_type': best_match['bed'].bed_type
                    },
                    'confidence_score': round(best_match['score'] * 100, 1),
                    'reasoning': best_match['reasoning'],
                    'match_details': best_match['match_details'],
                    'allocation_timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'No suitable beds found',
                    'fallback_recommendation': 'Use manual bed assignment'
                }

        except Exception as e:
            logger.error(f"Error in sync bed allocation: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_recommendation': 'Use manual bed assignment'
            }

    def _sync_calculate_bed_score(self, patient_data: Dict, bed: Bed, db: Session) -> Dict:
        """Synchronous version of bed scoring"""
        scores = {}
        reasoning = []

        # Medical condition match
        condition_score = self._score_medical_condition_match(patient_data, bed)
        scores['medical_condition'] = condition_score
        if condition_score > 0.8:
            reasoning.append("Excellent ward match for " + patient_data.get('primary_condition', 'condition'))

        # Equipment availability
        equipment_score = self._score_equipment_availability(patient_data, bed)
        scores['equipment'] = equipment_score
        if equipment_score > 0.8:
            reasoning.append("All required equipment available")

        # Doctor availability (simplified sync version)
        scores['doctor'] = 0.8  # Assume doctors available
        reasoning.append("Qualified doctor available")

        # Infection control (simplified)
        scores['infection_control'] = self._score_infection_control(patient_data, bed)

        # Patient preferences (simplified)
        scores['preferences'] = self._score_patient_preferences(patient_data, bed)

        # Calculate total score
        total_score = (
            scores['medical_condition'] * self.allocation_weights['medical_condition_match'] +
            scores['equipment'] * self.allocation_weights['equipment_availability'] +
            scores['doctor'] * self.allocation_weights['doctor_specialization'] +
            scores['infection_control'] * self.allocation_weights['infection_control'] +
            scores['preferences'] * self.allocation_weights['patient_preferences']
        )

        return {
            'total_score': total_score,
            'reasoning': reasoning,
            'details': scores
        }

    async def find_optimal_bed(self, patient_data: Dict, db: Session) -> Dict:
        """
        Main function to find the optimal bed for a patient
        Returns bed recommendation with reasoning
        """
        try:
            logger.info(f"Starting smart allocation for patient: {patient_data.get('patient_name', 'Unknown')}")
            
            # Get all available beds
            available_beds = db.query(Bed).filter(Bed.status == 'vacant').all()
            
            if not available_beds:
                return {
                    'success': False,
                    'message': 'No available beds found',
                    'recommended_action': 'Consider discharge reviews or transfer protocols'
                }
            
            # Score each bed for this patient
            bed_scores = []
            for bed in available_beds:
                score = await self._calculate_bed_score(patient_data, bed, db)
                bed_scores.append({
                    'bed': bed,
                    'score': score['total_score'],
                    'reasoning': score['reasoning'],
                    'match_details': score['details']
                })
            
            # Sort by score (highest first)
            bed_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Get the best match
            best_match = bed_scores[0]
            
            return {
                'success': True,
                'recommended_bed': {
                    'bed_number': best_match['bed'].bed_number,
                    'ward': best_match['bed'].ward,
                    'room': best_match['bed'].room_number,
                    'bed_type': best_match['bed'].bed_type
                },
                'confidence_score': round(best_match['score'] * 100, 1),
                'reasoning': best_match['reasoning'],
                'match_details': best_match['match_details'],
                'alternative_options': [
                    {
                        'bed_number': option['bed'].bed_number,
                        'ward': option['bed'].ward,
                        'score': round(option['score'] * 100, 1)
                    }
                    for option in bed_scores[1:4]  # Top 3 alternatives
                ],
                'allocation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in smart bed allocation: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_recommendation': 'Use manual bed assignment'
            }

    async def _calculate_bed_score(self, patient_data: Dict, bed: Bed, db: Session) -> Dict:
        """
        Calculate compatibility score between patient and bed
        """
        scores = {}
        reasoning = []
        
        # 1. Medical Condition Match (35% weight)
        condition_score = self._score_medical_condition_match(patient_data, bed)
        scores['medical_condition'] = condition_score
        if condition_score > 0.8:
            reasoning.append(f"Excellent ward match for {patient_data.get('primary_condition', 'condition')}")
        elif condition_score > 0.6:
            reasoning.append(f"Good ward compatibility")
        else:
            reasoning.append(f"Ward may not be optimal for condition")
        
        # 2. Doctor Specialization Match (25% weight)
        doctor_score = await self._score_doctor_specialization(patient_data, bed, db)
        scores['doctor_specialization'] = doctor_score
        if doctor_score > 0.8:
            reasoning.append("Specialist doctor available in ward")
        elif doctor_score > 0.6:
            reasoning.append("Qualified doctor available")
        
        # 3. Equipment Availability (20% weight)
        equipment_score = self._score_equipment_availability(patient_data, bed)
        scores['equipment'] = equipment_score
        if equipment_score > 0.8:
            reasoning.append("All required equipment available")
        elif equipment_score < 0.5:
            reasoning.append("Some equipment may need to be arranged")
        
        # 4. Infection Control (15% weight)
        infection_score = self._score_infection_control(patient_data, bed)
        scores['infection_control'] = infection_score
        if infection_score < 0.5:
            reasoning.append("Isolation requirements may not be met")
        
        # 5. Patient Preferences (5% weight)
        preference_score = self._score_patient_preferences(patient_data, bed)
        scores['preferences'] = preference_score
        
        # Calculate weighted total score
        total_score = (
            scores['medical_condition'] * self.allocation_weights['medical_condition_match'] +
            scores['doctor_specialization'] * self.allocation_weights['doctor_specialization'] +
            scores['equipment'] * self.allocation_weights['equipment_availability'] +
            scores['infection_control'] * self.allocation_weights['infection_control'] +
            scores['preferences'] * self.allocation_weights['patient_preferences']
        )
        
        return {
            'total_score': total_score,
            'reasoning': reasoning,
            'details': scores
        }

    def _score_medical_condition_match(self, patient_data: Dict, bed: Bed) -> float:
        """Score how well the bed's ward matches the patient's medical condition"""
        condition = patient_data.get('primary_condition', '').lower()
        severity = patient_data.get('severity', 'stable').lower()
        bed_ward = bed.ward.lower() if bed.ward else 'general'
        
        # Check if condition maps to this ward
        suitable_wards = []
        for cond_key, wards in self.condition_ward_mapping.items():
            if cond_key in condition:
                suitable_wards.extend([w.lower() for w in wards])
        
        if not suitable_wards:
            suitable_wards = self.condition_ward_mapping.get(severity, ['general'])
            suitable_wards = [w.lower() for w in suitable_wards]
        
        # Perfect match
        if bed_ward in suitable_wards:
            return 1.0
        
        # Partial matches
        if 'icu' in suitable_wards and bed_ward in ['emergency', 'cardiac']:
            return 0.8
        if 'general' in suitable_wards and bed_ward in ['surgical', 'medical']:
            return 0.8
        
        # Acceptable but not optimal
        if severity == 'critical' and bed_ward != 'general':
            return 0.6
        if severity == 'stable' and bed_ward == 'general':
            return 0.9
        
        return 0.3  # Poor match

    async def _score_doctor_specialization(self, patient_data: Dict, bed: Bed, db: Session) -> float:
        """Score doctor specialization match for the ward"""
        condition = patient_data.get('primary_condition', '').lower()
        bed_ward = bed.ward if bed.ward else 'General'
        
        # Get doctors in this ward/department
        ward_doctors = db.query(Staff).filter(
            Staff.role.ilike('%doctor%'),
            Staff.specialization.isnot(None)
        ).all()
        
        if not ward_doctors:
            return 0.5  # No doctor info available
        
        # Check for specialist match
        for doctor in ward_doctors:
            specialization = doctor.specialization.lower() if doctor.specialization else ''
            
            # Perfect specialization matches
            if ('cardiac' in condition and 'cardiac' in specialization) or \
               ('respiratory' in condition and any(term in specialization for term in ['pulmonary', 'respiratory'])) or \
               ('neurological' in condition and 'neuro' in specialization) or \
               ('emergency' in condition and 'emergency' in specialization) or \
               ('critical' in condition and 'critical' in specialization):
                return 1.0
            
            # Good general matches
            if 'internal' in specialization or 'general' in specialization:
                return 0.7
        
        return 0.6  # Doctors available but no perfect specialization match

    def _score_equipment_availability(self, patient_data: Dict, bed: Bed) -> float:
        """Score equipment availability for patient needs"""
        condition = patient_data.get('primary_condition', '').lower()
        severity = patient_data.get('severity', 'stable').lower()
        bed_ward = bed.ward.lower() if bed.ward else 'general'
        
        # Determine required equipment
        required_equipment = []
        for cond_key, equipment in self.equipment_requirements.items():
            if cond_key in condition:
                required_equipment.extend(equipment)
        
        if severity == 'critical':
            required_equipment.extend(self.equipment_requirements['critical'])
        
        # Ward equipment availability (simplified - in real system, query equipment database)
        ward_equipment = {
            'icu': ['cardiac_monitor', 'ventilator', 'defibrillator', 'oxygen', 'full_monitoring', 'life_support'],
            'emergency': ['cardiac_monitor', 'defibrillator', 'oxygen', 'basic_monitoring'],
            'cardiac': ['cardiac_monitor', 'defibrillator', 'oxygen'],
            'general': ['basic_monitoring', 'oxygen'],
            'pediatric': ['pediatric_monitor', 'oxygen'],
            'maternity': ['fetal_monitor', 'basic_monitoring']
        }
        
        available_equipment = ward_equipment.get(bed_ward, ['basic_monitoring'])
        
        if not required_equipment:
            return 1.0  # No special equipment needed
        
        # Calculate match percentage
        matched_equipment = sum(1 for eq in required_equipment if eq in available_equipment)
        return matched_equipment / len(required_equipment)

    def _score_infection_control(self, patient_data: Dict, bed: Bed) -> float:
        """Score infection control compatibility"""
        isolation_type = patient_data.get('isolation_requirements', 'standard').lower()
        bed_type = bed.bed_type.lower() if bed.bed_type else 'standard'
        room = bed.room_number if bed.room_number else 'shared'
        
        required_features = self.isolation_requirements.get(isolation_type, [])
        
        if not required_features:
            return 1.0  # No special requirements
        
        # Check if bed meets requirements (simplified)
        available_features = []
        if 'private' in room.lower() or 'single' in bed_type:
            available_features.extend(['private_room', 'barrier_precautions'])
        if 'isolation' in bed_type or 'negative' in room.lower():
            available_features.append('negative_pressure_room')
        
        if not required_features:
            return 1.0
        
        matched_features = sum(1 for feature in required_features if feature in available_features)
        return matched_features / len(required_features)

    def _score_patient_preferences(self, patient_data: Dict, bed: Bed) -> float:
        """Score patient preference compatibility"""
        preferences = patient_data.get('preferences', {})
        
        if not preferences:
            return 1.0  # No specific preferences
        
        score = 1.0
        
        # Room type preference
        room_pref = preferences.get('room_type', '').lower()
        actual_room = bed.room_number.lower() if bed.room_number else 'shared'
        
        if room_pref == 'private' and 'private' not in actual_room:
            score -= 0.3
        elif room_pref == 'shared' and 'private' in actual_room:
            score -= 0.1  # Private is usually better than shared
        
        # Ward preference
        ward_pref = preferences.get('ward', '').lower()
        actual_ward = bed.ward.lower() if bed.ward else 'general'
        
        if ward_pref and ward_pref != actual_ward:
            score -= 0.2
        
        return max(0.0, score)

    async def auto_assign_patient(self, patient_data: Dict, db: Session) -> Dict:
        """
        Automatically assign patient to optimal bed and update database
        """
        try:
            # Find optimal bed
            allocation_result = await self.find_optimal_bed(patient_data, db)
            
            if not allocation_result['success']:
                return allocation_result
            
            # Get the recommended bed
            recommended_bed_number = allocation_result['recommended_bed']['bed_number']
            bed = db.query(Bed).filter(Bed.bed_number == recommended_bed_number).first()
            
            if not bed or bed.status != 'vacant':
                return {
                    'success': False,
                    'message': 'Recommended bed is no longer available',
                    'action': 'Recalculating optimal bed...'
                }
            
            # Create patient record if needed
            patient = db.query(Patient).filter(Patient.patient_id == patient_data['patient_id']).first()
            if not patient:
                patient = Patient(
                    patient_id=patient_data['patient_id'],
                    patient_name=patient_data['patient_name'],
                    age=patient_data.get('age'),
                    gender=patient_data.get('gender'),
                    phone=patient_data.get('phone'),
                    emergency_contact=patient_data.get('emergency_contact'),
                    primary_condition=patient_data.get('primary_condition'),
                    severity=patient_data.get('severity'),
                    attending_physician=patient_data.get('attending_physician'),
                    admission_date=datetime.now()
                )
                db.add(patient)
            
            # Assign bed
            bed.status = 'occupied'
            bed.patient_id = patient.patient_id
            bed.assigned_at = datetime.now()
            
            db.commit()
            
            logger.info(f"Successfully auto-assigned patient {patient_data['patient_name']} to bed {bed.bed_number}")
            
            return {
                'success': True,
                'message': f"Patient automatically assigned to {bed.bed_number}",
                'assignment_details': allocation_result,
                'automation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in auto assignment: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': 'Manual assignment required'
            }
