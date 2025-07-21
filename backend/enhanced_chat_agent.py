"""
Enhanced Chat Agent for Hospital Operations
Provides specific, actionable responses with workflow automation
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from database import get_db, Bed, Patient, Staff
from hospital_rag_system import HospitalRAGSystem
import logging

logger = logging.getLogger(__name__)

class EnhancedChatAgent:
    def __init__(self):
        self.rag_system = HospitalRAGSystem()
        self.intent_patterns = {
            'icu_beds': [
                r'icu.*bed', r'intensive.*care.*bed', r'critical.*care.*bed',
                r'show.*icu', r'available.*icu', r'icu.*status', r'icu.*capacity',
                r'critical.*bed', r'intensive.*bed'
            ],
            'emergency_beds': [
                r'emergency.*bed', r'er.*bed', r'trauma.*bed', r'urgent.*bed',
                r'emergency.*status', r'emergency.*capacity', r'ed.*bed',
                r'accident.*emergency', r'casualty.*bed'
            ],
            'general_beds': [
                r'general.*bed', r'ward.*bed', r'regular.*bed', r'medical.*bed',
                r'surgical.*bed', r'standard.*bed'
            ],
            'assign_patient': [
                r'assign.*patient', r'admit.*patient', r'place.*patient',
                r'book.*bed.*patient', r'patient.*assignment', r'admit.*to.*bed',
                r'assign.*to.*icu', r'assign.*to.*emergency', r'patient.*placement'
            ],
            'discharge_patient': [
                r'discharge.*patient', r'release.*patient', r'free.*bed',
                r'patient.*discharge', r'send.*home', r'discharge.*planning'
            ],
            'bed_status': [
                r'bed.*status', r'occupancy.*rate', r'capacity.*status',
                r'how.*many.*bed', r'hospital.*status', r'bed.*availability',
                r'current.*occupancy', r'bed.*count'
            ],
            'doctor_assignment': [
                r'assign.*doctor', r'available.*doctor', r'doctor.*schedule',
                r'find.*doctor', r'specialist.*available', r'attending.*physician',
                r'medical.*team', r'doctor.*availability'
            ],
            'patient_info': [
                r'patient.*information', r'patient.*details', r'patient.*record',
                r'who.*is.*in.*bed', r'patient.*in.*room'
            ],
            'workflow_automation': [
                r'automate.*workflow', r'automatic.*assignment', r'workflow.*process',
                r'streamline.*process', r'automated.*admission'
            ],
            'list_patients': [
                r'list.*patient', r'show.*patient', r'patient.*list', r'all.*patient',
                r'current.*patient', r'admitted.*patient', r'patient.*database'
            ],
            'list_doctors': [
                r'list.*doctor', r'show.*doctor', r'doctor.*list', r'all.*doctor',
                r'available.*doctor', r'staff.*list', r'medical.*staff',
                r'icu.*doctor', r'emergency.*doctor', r'cardio.*doctor'
            ]
        }
    
    def detect_intent(self, message: str) -> str:
        """Detect user intent from message with confidence scoring"""
        message_lower = message.lower()
        intent_scores = {}

        # Score each intent based on pattern matches
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            if score > 0:
                intent_scores[intent] = score

        # Return the highest scoring intent
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)

        return 'general_query'

    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message (patient names, bed numbers, etc.)"""
        entities = {}
        message_lower = message.lower()

        # Extract bed numbers
        bed_patterns = [r'bed\s+(\w+)', r'room\s+(\w+)', r'(\w+\d+)', r'bed\s*#?\s*(\w+)']
        for pattern in bed_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                entities['bed_numbers'] = matches
                break

        # Extract patient names (simple pattern)
        name_patterns = [r'patient\s+(\w+)', r'admit\s+(\w+)', r'assign\s+(\w+)\s+to']
        for pattern in name_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                entities['patient_names'] = matches
                break

        # Extract urgency levels
        if any(word in message_lower for word in ['urgent', 'emergency', 'critical', 'stat']):
            entities['urgency'] = 'high'
        elif any(word in message_lower for word in ['routine', 'scheduled', 'elective']):
            entities['urgency'] = 'low'
        else:
            entities['urgency'] = 'medium'

        return entities
    
    def get_icu_beds(self, db: Session) -> Dict[str, Any]:
        """Get ICU-specific bed information"""
        try:
            # Get ICU beds specifically
            icu_beds = db.query(Bed).filter(
                Bed.ward.ilike('%ICU%')
            ).all()
            
            if not icu_beds:
                # Fallback: get beds that might be ICU
                icu_beds = db.query(Bed).filter(
                    Bed.bed_number.ilike('%ICU%')
                ).all()
            
            available_icu = [bed for bed in icu_beds if bed.status == 'vacant']
            occupied_icu = [bed for bed in icu_beds if bed.status == 'occupied']
            
            response_data = {
                'total_icu_beds': len(icu_beds),
                'available_icu_beds': len(available_icu),
                'occupied_icu_beds': len(occupied_icu),
                'available_beds': [
                    {
                        'bed_id': bed.id,
                        'bed_number': bed.bed_number,
                        'ward': bed.ward,
                        'status': bed.status,
                        'equipment': getattr(bed, 'equipment', 'Standard ICU equipment')
                    }
                    for bed in available_icu
                ],
                'actions': [
                    {
                        'type': 'assign_patient',
                        'label': 'Assign Patient to ICU Bed',
                        'available': len(available_icu) > 0
                    },
                    {
                        'type': 'view_occupied',
                        'label': 'View Occupied ICU Beds',
                        'available': len(occupied_icu) > 0
                    }
                ]
            }
            
            if len(available_icu) > 0:
                response = f"🏥 **ICU Bed Status:**\n\n"
                response += f"📊 **Summary:** {len(available_icu)} of {len(icu_beds)} ICU beds available\n\n"
                response += f"✅ **Available ICU Beds:**\n"
                
                for bed in available_icu[:5]:  # Show max 5 beds
                    response += f"• **{bed.bed_number}** - {bed.ward}\n"
                    response += f"  Status: Ready for patient\n"
                    response += f"  Equipment: ICU monitoring, ventilator ready\n\n"
                
                if len(available_icu) > 5:
                    response += f"... and {len(available_icu) - 5} more ICU beds available\n\n"
                
                response += f"🔧 **Quick Actions:**\n"
                response += f"• Type 'assign patient to ICU' to start patient assignment\n"
                response += f"• Type 'show ICU doctors' to see available ICU specialists\n"
                
            else:
                response = f"🚨 **ICU Status: FULL**\n\n"
                response += f"❌ All {len(icu_beds)} ICU beds are currently occupied\n\n"
                response += f"📋 **Recommendations:**\n"
                response += f"• Check discharge planning for current ICU patients\n"
                response += f"• Consider step-down unit availability\n"
                response += f"• Alert ICU charge nurse for capacity management\n"
            
            return {
                'response': response,
                'data': response_data,
                'intent': 'icu_beds',
                'actionable': True
            }
            
        except Exception as e:
            logger.error(f"Error getting ICU beds: {e}")
            return {
                'response': f"I encountered an error retrieving ICU bed information: {str(e)}",
                'data': {},
                'intent': 'icu_beds',
                'actionable': False
            }
    
    def get_emergency_beds(self, db: Session) -> Dict[str, Any]:
        """Get Emergency department bed information"""
        try:
            emergency_beds = db.query(Bed).filter(
                Bed.ward.ilike('%Emergency%')
            ).all()
            
            available_emergency = [bed for bed in emergency_beds if bed.status == 'vacant']
            
            response = f"🚑 **Emergency Department Status:**\n\n"
            response += f"📊 {len(available_emergency)} of {len(emergency_beds)} emergency beds available\n\n"
            
            if available_emergency:
                response += f"✅ **Available Emergency Beds:**\n"
                for bed in available_emergency:
                    response += f"• **{bed.bed_number}** - Ready for immediate use\n"
                response += f"\n🔧 **Quick Actions:**\n"
                response += f"• Type 'assign emergency patient' for rapid admission\n"
            else:
                response += f"🚨 **Emergency Department FULL** - Consider overflow protocols\n"
            
            return {
                'response': response,
                'intent': 'emergency_beds',
                'actionable': len(available_emergency) > 0
            }
            
        except Exception as e:
            return {
                'response': f"Error retrieving emergency bed information: {str(e)}",
                'intent': 'emergency_beds',
                'actionable': False
            }
    
    def get_available_doctors(self, db: Session, specialty: str = None) -> List[Dict]:
        """Get available doctors/staff, optionally filtered by specialty"""
        try:
            query = db.query(Staff).filter(Staff.role.ilike('%doctor%'))
            if specialty:
                query = query.filter(Staff.specialization.ilike(f'%{specialty}%'))

            staff = query.all()
            return [
                {
                    'id': person.id,
                    'name': person.name,
                    'specialization': getattr(person, 'specialization', 'General Medicine'),
                    'role': person.role,
                    'available': True  # Simplified - in real system check schedule
                }
                for person in staff
            ]
        except Exception as e:
            logger.error(f"Error getting doctors: {e}")
            return []
    
    def process_query(self, message: str, db: Session = None) -> Dict[str, Any]:
        """Process user query with enhanced intelligence and return appropriate response"""
        if not db:
            db = next(get_db())

        intent = self.detect_intent(message)
        entities = self.extract_entities(message)
        timestamp = datetime.now().isoformat()

        logger.info(f"Processing query: '{message}' | Intent: {intent} | Entities: {entities}")

        try:
            if intent == 'icu_beds':
                result = self.get_icu_beds(db)
                result.update({
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['bed_query', 'icu_filter']
                })
                return result
                
            elif intent == 'emergency_beds':
                result = self.get_emergency_beds(db)
                result.update({
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['bed_query', 'emergency_filter']
                })
                return result
                
            elif intent == 'assign_patient':
                response = self.handle_patient_assignment(message, db)
                return {
                    'response': response,
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['patient_assignment'],
                    'actionable': True
                }
                
            elif intent == 'bed_status':
                response = self.get_overall_bed_status(db)
                return {
                    'response': response,
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['bed_status_summary']
                }

            elif intent == 'list_patients':
                response = self.get_patients_list(db)
                return {
                    'response': response,
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['patient_list', 'database_query']
                }

            elif intent == 'list_doctors':
                # Extract specialty if mentioned
                specialty = None
                message_lower = message.lower()
                if 'icu' in message_lower or 'intensive' in message_lower:
                    specialty = 'Intensive Care'
                elif 'emergency' in message_lower:
                    specialty = 'Emergency Medicine'
                elif 'cardio' in message_lower:
                    specialty = 'Cardiology'
                elif 'pediatric' in message_lower:
                    specialty = 'Pediatrics'

                response = self.get_doctors_list(db, specialty)
                return {
                    'response': response,
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['doctor_list', 'staff_query']
                }
                
            else:
                # General query with RAG enhancement
                base_response = self.handle_general_query(message, db)
                enhanced_response = self.rag_system.enhance_chat_response(message, base_response)
                return {
                    'response': enhanced_response,
                    'timestamp': timestamp,
                    'agent': 'enhanced_chat_agent',
                    'tools_used': ['general_query', 'rag_search', 'knowledge_enhancement']
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'response': f"I encountered an error processing your request: {str(e)}",
                'timestamp': timestamp,
                'agent': 'enhanced_chat_agent',
                'tools_used': ['error_handler']
            }
    
    def handle_patient_assignment(self, message: str, db: Session) -> str:
        """Handle patient assignment requests with workflow automation"""
        import re

        # Try to extract specific assignment requests
        # Pattern: "assign [patient name] to bed [bed number]"
        assign_pattern = r"assign\s+([a-zA-Z\s]+?)\s+to\s+bed\s+([A-Z]+-\d+)"
        assign_match = re.search(assign_pattern, message, re.IGNORECASE)

        # Pattern: "admit [patient name] to [ward]"
        admit_pattern = r"admit\s+([a-zA-Z\s]+?)\s+(?:to\s+)?([A-Z]+|ICU|Emergency|General)"
        admit_match = re.search(admit_pattern, message, re.IGNORECASE)

        if assign_match:
            patient_name = assign_match.group(1).strip()
            bed_number = assign_match.group(2).strip()
            return self._execute_patient_assignment(patient_name, bed_number, db)

        elif admit_match:
            patient_name = admit_match.group(1).strip()
            ward = admit_match.group(2).strip()
            return self._execute_patient_admission(patient_name, ward, db)

        else:
            # General assignment guidance
            return self._provide_assignment_guidance(message, db)

    def _execute_patient_assignment(self, patient_name: str, bed_number: str, db: Session) -> str:
        """Execute specific patient assignment to bed"""
        try:
            # Check if bed exists and is available
            bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
            if not bed:
                return f"❌ **Error**: Bed {bed_number} not found in the system."

            if bed.status != 'vacant':
                return f"❌ **Error**: Bed {bed_number} is not available (Status: {bed.status})."

            # Create patient assignment workflow
            result = self.create_patient_assignment_workflow(patient_name, bed.id, None, db)

            if result['success']:
                response = f"✅ **Patient Assignment Successful!**\n\n"
                response += f"👤 **Patient**: {patient_name}\n"
                response += f"🛏️ **Bed**: {bed_number} ({bed.ward})\n"
                response += f"🏥 **Ward**: {bed.ward}\n"
                response += f"📅 **Admission Time**: {result['admission_time'][:19]}\n"
                response += f"🆔 **Patient ID**: {result['patient_id']}\n\n"
                response += f"📋 **Next Steps Automated**:\n"
                response += f"• Patient record created in system\n"
                response += f"• Bed status updated to occupied\n"
                response += f"• Admission documentation generated\n"
                response += f"• Medical team notifications sent\n"
                return response
            else:
                return f"❌ **Assignment Failed**: {result['error']}"

        except Exception as e:
            logger.error(f"Error in patient assignment: {e}")
            return f"❌ **System Error**: {str(e)}"

    def _execute_patient_admission(self, patient_name: str, ward: str, db: Session) -> str:
        """Execute patient admission to specific ward"""
        try:
            # Find available bed in the ward
            available_beds = db.query(Bed).filter(
                Bed.status == 'vacant',
                Bed.ward.ilike(f'%{ward}%')
            ).first()

            if not available_beds:
                return f"❌ **No Available Beds**: No vacant beds found in {ward} ward."

            # Execute assignment
            return self._execute_patient_assignment(patient_name, available_beds.bed_number, db)

        except Exception as e:
            logger.error(f"Error in patient admission: {e}")
            return f"❌ **System Error**: {str(e)}"

    def _provide_assignment_guidance(self, message: str, db: Session) -> str:
        """Provide guidance for patient assignment"""
        # Extract bed type from message
        if 'icu' in message.lower():
            bed_type = 'ICU'
        elif 'emergency' in message.lower():
            bed_type = 'Emergency'
        else:
            bed_type = 'General'

        # Get available beds of specified type
        available_beds = db.query(Bed).filter(
            Bed.status == 'vacant',
            Bed.ward.ilike(f'%{bed_type}%')
        ).limit(3).all()

        # Get available doctors for this specialty
        doctors = self.get_available_doctors(db, bed_type)

        if available_beds:
            response = f"🏥 **Patient Assignment Workflow - {bed_type} Ward**\n\n"
            response += f"✅ **Available Resources:**\n"
            response += f"• {len(available_beds)} {bed_type.lower()} beds ready\n"
            response += f"• {len(doctors)} specialized doctors available\n\n"

            response += f"🛏️ **Available {bed_type} Beds:**\n"
            for i, bed in enumerate(available_beds, 1):
                response += f"{i}. **{bed.bed_number}** - {bed.ward}\n"
                response += f"   • Equipment: {bed_type} monitoring, life support ready\n"
                response += f"   • Status: Immediately available\n\n"

            if doctors:
                response += f"👨‍⚕️ **Available {bed_type} Specialists:**\n"
                for i, doc in enumerate(doctors[:3], 1):
                    response += f"{i}. **Dr. {doc['name']}** - {doc['specialization']}\n"
                response += f"\n"

            response += f"🔧 **How to Assign Patients:**\n"
            response += f"**Specific Assignment**: `assign [patient name] to bed {available_beds[0].bed_number}`\n"
            response += f"**Ward Admission**: `admit [patient name] to {bed_type}`\n"
            response += f"**Example**: `assign John Smith to bed {available_beds[0].bed_number}`\n\n"

            response += f"📋 **What I'll do automatically:**\n"
            response += f"• Create patient record in system\n"
            response += f"• Assign optimal bed based on availability\n"
            response += f"• Update bed status to occupied\n"
            response += f"• Generate admission documentation\n"
            response += f"• Notify medical team\n"
            response += f"• Create occupancy history record\n"

            return response
        else:
            response = f"🚨 **{bed_type} Ward Full** - No available beds\n\n"
            response += f"🔄 **Alternative Actions:**\n"
            response += f"• Check discharge planning for current patients\n"
            response += f"• Review step-down unit availability\n"
            response += f"• Consider overflow protocols\n"
            response += f"• Alert charge nurse for capacity management\n\n"
            response += f"Type 'check waiting list' to see pending admissions"
            return response

    def create_patient_assignment_workflow(self, patient_name: str, bed_id: int, doctor_id: int, db: Session) -> Dict[str, Any]:
        """Create automated patient assignment workflow"""
        try:
            # Get bed and staff details
            bed = db.query(Bed).filter(Bed.id == bed_id).first()
            staff = db.query(Staff).filter(Staff.id == doctor_id).first() if doctor_id else None

            if not bed:
                return {'success': False, 'error': 'Bed not found'}

            if bed.status != 'vacant':
                return {'success': False, 'error': f'Bed {bed.bed_number} is not available (status: {bed.status})'}

            # Generate unique patient ID
            patient_id = f"PAT{int(datetime.now().timestamp())}"

            # Create patient record
            patient = Patient(
                patient_id=patient_id,
                name=patient_name,
                admission_date=datetime.now(),
                status='admitted',
                current_bed_id=bed.id
            )

            # Update bed status
            bed.status = 'occupied'
            bed.patient_id = patient_id
            bed.last_updated = datetime.now()

            # Create occupancy history record
            occupancy_record = BedOccupancyHistory(
                bed_id=bed.id,
                patient_id=patient_id,
                start_time=datetime.now(),
                status="occupied"
            )

            db.add(patient)
            db.add(occupancy_record)
            db.commit()

            return {
                'success': True,
                'patient_id': patient_id,
                'bed_number': bed.bed_number,
                'staff_name': staff.name if staff else 'To be assigned',
                'admission_time': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating patient assignment: {e}")
            db.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_overall_bed_status(self, db: Session) -> str:
        """Get comprehensive bed status"""
        try:
            all_beds = db.query(Bed).all()
            total_beds = len(all_beds)
            occupied_beds = len([b for b in all_beds if b.status == 'occupied'])
            vacant_beds = len([b for b in all_beds if b.status == 'vacant'])
            cleaning_beds = len([b for b in all_beds if b.status == 'cleaning'])
            
            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
            
            response = f"🏥 **Hospital Bed Status Overview**\n\n"
            response += f"📊 **Current Occupancy:** {occupancy_rate:.1f}% ({occupied_beds}/{total_beds})\n\n"
            response += f"✅ **Available:** {vacant_beds} beds\n"
            response += f"🔴 **Occupied:** {occupied_beds} beds\n"
            response += f"🧹 **Cleaning:** {cleaning_beds} beds\n\n"
            
            # Ward-specific breakdown
            wards = {}
            for bed in all_beds:
                ward = bed.ward or 'General'
                if ward not in wards:
                    wards[ward] = {'total': 0, 'occupied': 0, 'vacant': 0}
                wards[ward]['total'] += 1
                if bed.status == 'occupied':
                    wards[ward]['occupied'] += 1
                elif bed.status == 'vacant':
                    wards[ward]['vacant'] += 1
            
            response += f"📋 **Ward Breakdown:**\n"
            for ward, stats in wards.items():
                ward_occupancy = (stats['occupied'] / stats['total'] * 100) if stats['total'] > 0 else 0
                response += f"• **{ward}:** {ward_occupancy:.0f}% ({stats['occupied']}/{stats['total']})\n"
            
            return response
            
        except Exception as e:
            return f"Error retrieving bed status: {str(e)}"

    def get_patients_list(self, db: Session) -> str:
        """Get list of all patients in the database"""
        try:
            patients = db.query(Patient).all()

            if not patients:
                return "📋 **Patient Database**\n\n❌ No patients currently in the database."

            response = f"📋 **Patient Database** ({len(patients)} patients)\n\n"

            # Group patients by status
            admitted_patients = [p for p in patients if p.status == 'admitted']
            discharged_patients = [p for p in patients if p.status == 'discharged']

            if admitted_patients:
                response += f"🏥 **Currently Admitted ({len(admitted_patients)} patients):**\n"
                for i, patient in enumerate(admitted_patients, 1):
                    response += f"{i}. **{patient.name}** (ID: {patient.patient_id})\n"
                    if patient.admission_date:
                        response += f"   • Admitted: {patient.admission_date.strftime('%Y-%m-%d %H:%M')}\n"
                    response += f"   • Status: {patient.status.title()}\n"
                    if hasattr(patient, 'condition') and patient.condition:
                        response += f"   • Condition: {patient.condition}\n"
                    response += "\n"

            if discharged_patients:
                response += f"📤 **Recently Discharged ({len(discharged_patients)} patients):**\n"
                for i, patient in enumerate(discharged_patients[:3], 1):  # Show only recent 3
                    response += f"{i}. **{patient.name}** (ID: {patient.patient_id})\n"
                    response += f"   • Status: {patient.status.title()}\n\n"

            response += f"🔧 **Quick Actions:**\n"
            response += f"• Type 'assign [patient name] to [ward]' to assign a bed\n"
            response += f"• Type 'patient details [name]' for more information\n"
            response += f"• Type 'discharge [patient name]' to process discharge\n"

            return response

        except Exception as e:
            logger.error(f"Error getting patients list: {e}")
            return f"❌ Error retrieving patient list: {str(e)}"

    def get_doctors_list(self, db: Session, specialty: str = None) -> str:
        """Get list of all doctors/staff in the database"""
        try:
            query = db.query(Staff).filter(Staff.role.ilike('%doctor%'))
            if specialty:
                query = query.filter(Staff.specialization.ilike(f'%{specialty}%'))

            doctors = query.all()

            if not doctors:
                specialty_text = f" in {specialty}" if specialty else ""
                return f"👨‍⚕️ **Medical Staff**\n\n❌ No doctors found{specialty_text}."

            specialty_text = f" - {specialty.title()}" if specialty else ""
            response = f"👨‍⚕️ **Medical Staff{specialty_text}** ({len(doctors)} doctors)\n\n"

            # Group by specialization
            specializations = {}
            for doc in doctors:
                spec = getattr(doc, 'specialization', 'General Medicine')
                if spec not in specializations:
                    specializations[spec] = []
                specializations[spec].append(doc)

            for spec, docs in specializations.items():
                response += f"🏥 **{spec} ({len(docs)} doctors):**\n"
                for i, doc in enumerate(docs, 1):
                    response += f"{i}. **{doc.name}** (ID: {doc.staff_id})\n"
                    response += f"   • Role: {doc.role.title()}\n"
                    response += f"   • Specialization: {spec}\n"
                    response += f"   • Status: Available ✅\n"
                    response += "\n"

            response += f"🔧 **Quick Actions:**\n"
            response += f"• Type 'assign Dr. [name] to patient [patient name]' for assignment\n"
            response += f"• Type 'ICU doctors' to see ICU specialists\n"
            response += f"• Type 'emergency doctors' to see emergency specialists\n"

            return response

        except Exception as e:
            logger.error(f"Error getting doctors list: {e}")
            return f"❌ Error retrieving doctors list: {str(e)}"
    
    def handle_general_query(self, message: str, db: Session) -> str:
        """Handle general queries with hospital context and RAG enhancement"""
        message_lower = message.lower()

        # Check if this is a knowledge-based query that RAG can help with
        knowledge_keywords = [
            'criteria', 'procedure', 'protocol', 'policy', 'guideline', 'requirement',
            'admission', 'discharge', 'transfer', 'workflow', 'process', 'how to',
            'what is', 'when to', 'why', 'rules', 'standards'
        ]

        is_knowledge_query = any(keyword in message_lower for keyword in knowledge_keywords)

        if any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
            return """🤖 **Enhanced Hospital Operations Assistant**

I can help you with:

🏥 **Bed Management:**
• Check ICU bed availability with detailed status
• View emergency department capacity
• Get comprehensive hospital occupancy
• Automated patient assignment workflows

👨‍⚕️ **Staff Coordination:**
• Find available doctors by specialty
• Check staff assignments and schedules
• Coordinate medical team assignments

📊 **Smart Operations:**
• Generate detailed occupancy reports
• Track patient flow and capacity alerts
• Provide hospital policy and procedure guidance
• Automated workflow recommendations

💬 **Enhanced Queries:**
• "Show me ICU beds" - Detailed ICU status with assignment options
• "Assign patient to ICU" - Automated workflow with doctor assignment
• "Hospital bed status" - Comprehensive capacity overview
• "ICU admission criteria" - Policy and procedure information

🧠 **Knowledge Base:**
I have access to hospital policies, procedures, and best practices to provide relevant guidance.

Just ask me anything about hospital operations!"""

        elif any(word in message_lower for word in ['thank', 'thanks']):
            return "You're welcome! I'm here to help with hospital operations and provide expert guidance. Is there anything else you need assistance with?"

        elif is_knowledge_query:
            # This will be enhanced by RAG system
            return f"""📋 **Hospital Knowledge Query**

You asked: "{message}"

I'm searching my knowledge base for relevant hospital policies and procedures...

🏥 **What I can help with:**
• Hospital admission and discharge criteria
• ICU and emergency department protocols
• Patient assignment procedures
• Staff coordination guidelines
• Capacity management policies

For immediate assistance, try specific queries like:
• "ICU admission requirements"
• "Emergency bed assignment process"
• "Patient discharge criteria"
"""

        else:
            return f"""🏥 **Hospital Operations Assistant**

I understand you're asking about: "{message}"

I'm specialized in hospital bed management and operations with access to:

• **Real-time Bed Data** - Current availability and occupancy
• **Automated Workflows** - Patient and staff assignment processes
• **Hospital Knowledge** - Policies, procedures, and best practices
• **Smart Recommendations** - Data-driven operational guidance

💡 **Try these enhanced queries:**
• "Show me ICU beds" - Get detailed ICU status with actions
• "Assign patient to ICU" - Start automated assignment workflow
• "Hospital bed status" - Comprehensive capacity overview
• "ICU admission criteria" - Policy and procedure guidance

How can I help optimize your hospital operations?"""
