"""
Enhanced Bed Management Agent with Advanced Features
"""
from datetime import datetime
import sys
import os
import time
import uuid

# Add backend to path to import database modules
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_path)

# Import enhancement modules
try:
    from .intent_processor import IntentProcessor
    from .conversation_memory import ConversationMemory
    from .error_handler import ErrorHandler, ErrorType
    from .performance_optimizer import QueryOptimizer, PerformanceMonitor
except ImportError:
    # Fallback imports for direct execution
    from intent_processor import IntentProcessor
    from conversation_memory import ConversationMemory
    from error_handler import ErrorHandler, ErrorType
    from performance_optimizer import QueryOptimizer, PerformanceMonitor

try:
    from database import SessionLocal, Bed, Patient
    from sqlalchemy.orm import Session
    DATABASE_AVAILABLE = True
    print(f"Database modules imported successfully from {backend_path}")
except ImportError as e:
    print(f"Database import error: {e}")
    print(f"Tried to import from: {backend_path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    DATABASE_AVAILABLE = False

class EnhancedBedAgent:
    def __init__(self, session_id: str = None):
        self.db_available = DATABASE_AVAILABLE
        self.session_id = session_id or str(uuid.uuid4())

        # Initialize enhancement components
        self.intent_processor = IntentProcessor()
        self.conversation_memory = ConversationMemory(self.session_id)
        self.error_handler = ErrorHandler()
        self.query_optimizer = QueryOptimizer()
        self.performance_monitor = PerformanceMonitor()

        print(f"Enhanced Bed Agent initialized with session: {self.session_id}")

    def get_db_session(self):
        """Get database session"""
        if not self.db_available:
            return None
        return SessionLocal()

    def get_bed_occupancy(self):
        """Get bed occupancy statistics"""
        if not self.db_available:
            return {"error": "Database connection not available"}

        try:
            db = self.get_db_session()

            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == 'occupied').count()
            vacant_beds = db.query(Bed).filter(Bed.status == 'vacant').count()
            cleaning_beds = db.query(Bed).filter(Bed.status == 'cleaning').count()

            db.close()

            occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

            return {
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "cleaning_beds": cleaning_beds,
                "occupancy_rate": round(occupancy_rate, 1)
            }
        except Exception as e:
            return {"error": str(e)}

    def get_available_beds(self, ward=None):
        """Get available beds, optionally filtered by ward"""
        if not self.db_available:
            print("Database not available")
            return []

        try:
            db = self.get_db_session()
            if not db:
                print("Failed to get database session")
                return []

            query = db.query(Bed).filter(Bed.status == 'vacant')
            if ward:
                query = query.filter(Bed.ward.ilike(f'%{ward}%'))

            beds = query.all()
            print(f"Found {len(beds)} available beds" + (f" in {ward} ward" if ward else ""))

            db.close()

            return [{
                "bed_number": bed.bed_number,
                "room_number": bed.room_number,
                "ward": bed.ward,
                "bed_type": bed.bed_type,
                "floor_number": bed.floor_number,
                "wing": bed.wing,
                "private_room": bed.private_room,
                "daily_rate": bed.daily_rate
            } for bed in beds]

        except Exception as e:
            print(f"Error getting available beds: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def assign_bed(self, bed_number, patient_name, patient_id=None):
        """Assign a bed to a patient"""
        if not self.db_available:
            return {"error": "Database connection not available"}

        try:
            db = self.get_db_session()

            # Find the bed
            bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
            if not bed:
                db.close()
                return {"error": f"Bed {bed_number} not found"}

            if bed.status != 'vacant':
                db.close()
                return {"error": f"Bed {bed_number} is not available (status: {bed.status})"}

            # Generate patient ID if not provided
            if not patient_id:
                patient_id = f"PAT{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Create patient record
            patient = Patient(
                patient_id=patient_id,
                name=patient_name,
                age=0,  # Default values - can be updated later
                gender="unknown",
                primary_condition="General admission",
                severity="stable",
                admission_date=datetime.now(),
                current_bed_id=bed.id,
                status="admitted"
            )
            db.add(patient)
            db.flush()  # Get the patient ID

            # Update bed status
            bed.status = 'occupied'
            bed.patient_id = patient.patient_id
            bed.last_updated = datetime.now()

            db.commit()
            db.close()

            return {
                "success": True,
                "message": f"Successfully assigned {patient_name} to bed {bed_number}",
                "bed_number": bed_number,
                "patient_name": patient_name,
                "patient_id": patient.patient_id
            }

        except Exception as e:
            print(f"Error assigning bed: {e}")
            return {"error": str(e)}

    def get_patients(self, ward=None, status=None):
        """Get patient information, optionally filtered by ward or status"""
        if not self.db_available:
            return []

        try:
            db = self.get_db_session()
            if not db:
                return []

            # Base query for patients
            query = db.query(Patient)

            # Filter by status if provided
            if status:
                query = query.filter(Patient.status.ilike(f'%{status}%'))

            # Filter by ward if provided (join with beds)
            if ward:
                query = query.join(Bed, Patient.current_bed_id == Bed.id).filter(Bed.ward.ilike(f'%{ward}%'))

            patients = query.all()
            db.close()

            patient_list = []
            for patient in patients:
                # Get bed information if patient has a bed
                bed_info = None
                if patient.current_bed_id:
                    db2 = self.get_db_session()
                    bed = db2.query(Bed).filter(Bed.id == patient.current_bed_id).first()
                    if bed:
                        bed_info = {
                            "bed_number": bed.bed_number,
                            "room_number": bed.room_number,
                            "ward": bed.ward
                        }
                    db2.close()

                patient_list.append({
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "primary_condition": patient.primary_condition,
                    "severity": patient.severity,
                    "status": patient.status,
                    "admission_date": patient.admission_date.strftime("%Y-%m-%d %H:%M") if patient.admission_date else None,
                    "attending_physician": patient.attending_physician,
                    "bed_info": bed_info
                })

            return patient_list

        except Exception as e:
            print(f"Error getting patients: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_patient_by_id(self, patient_id):
        """Get specific patient information by ID"""
        if not self.db_available:
            return None

        try:
            db = self.get_db_session()
            if not db:
                return None

            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                db.close()
                return None

            # Get bed information if patient has a bed
            bed_info = None
            if patient.current_bed_id:
                bed = db.query(Bed).filter(Bed.id == patient.current_bed_id).first()
                if bed:
                    bed_info = {
                        "bed_number": bed.bed_number,
                        "room_number": bed.room_number,
                        "ward": bed.ward,
                        "floor_number": bed.floor_number,
                        "wing": bed.wing
                    }

            db.close()

            return {
                "patient_id": patient.patient_id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "primary_condition": patient.primary_condition,
                "severity": patient.severity,
                "status": patient.status,
                "admission_date": patient.admission_date.strftime("%Y-%m-%d %H:%M") if patient.admission_date else None,
                "attending_physician": patient.attending_physician,
                "emergency_contact": patient.emergency_contact,
                "phone": patient.phone,
                "bed_info": bed_info
            }

        except Exception as e:
            print(f"Error getting patient by ID: {e}")
            return None

    def process_query(self, query):
        """Enhanced query processing with intent recognition and context"""
        start_time = time.time()

        try:
            # Process query with intent recognition
            processed_query = self.intent_processor.process_query(query)
            intent = processed_query['intent']
            entities = processed_query['entities']
            confidence = processed_query['confidence']

            # Check if this is a follow-up query
            is_follow_up = self.conversation_memory.is_follow_up_query(intent, entities)

            # Get current context for enhanced responses
            current_context = self.conversation_memory.get_current_context()

            # Route to appropriate handler based on intent
            if intent == 'patient_info':
                response = self._handle_patient_info_query(entities, current_context, is_follow_up)
            elif intent == 'patient_lookup':
                response = self._handle_patient_lookup_query(entities, current_context)
            elif intent == 'bed_availability':
                response = self._handle_bed_availability_query(entities, current_context, is_follow_up)
            elif intent == 'bed_assignment':
                response = self._handle_bed_assignment_query(entities, current_context)
            elif intent == 'occupancy_status':
                response = self._handle_occupancy_status_query(entities, current_context)
            elif intent == 'discharge_info':
                response = self._handle_discharge_info_query(entities, current_context)
            else:
                response = self._handle_general_inquiry(query, current_context)

            # Record conversation turn
            execution_time = time.time() - start_time
            self.conversation_memory.add_turn(query, intent, entities, response, confidence)
            self.performance_monitor.record_request(execution_time, True)

            # Add contextual suggestions
            suggestions = self.conversation_memory.get_contextual_suggestions()

            return {
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "agent": "enhanced_bed_agent",
                "confidence": confidence,
                "intent": intent,
                "entities": entities,
                "suggestions": suggestions[:3],  # Top 3 suggestions
                "session_id": self.session_id,
                "is_follow_up": is_follow_up,
                "execution_time": round(execution_time, 3)
            }

        except Exception as e:
            # Handle errors gracefully
            execution_time = time.time() - start_time
            self.performance_monitor.record_request(execution_time, False)

            error_response = self.error_handler.handle_error(
                e,
                {'query': query, 'session_id': self.session_id},
                query
            )

            return {
                "response": error_response['response'],
                "timestamp": datetime.now().isoformat(),
                "agent": "enhanced_bed_agent",
                "error": True,
                "suggestions": error_response.get('suggestions', []),
                "session_id": self.session_id,
                "execution_time": round(execution_time, 3)
            }

    @QueryOptimizer().cached_query('patient_info')
    def _handle_patient_info_query(self, entities, context, is_follow_up, **kwargs):
        """Handle patient information queries with caching"""
        ward = entities.get('ward') or context.get('ward')

        # Use context if this is a follow-up
        if is_follow_up and not ward and 'ward' in context:
            ward = context['ward']

        patients = self.get_patients(ward=ward, status="admitted")

        if not patients:
            ward_text = f" in {ward} ward" if ward else ""
            return f"There are currently no admitted patients{ward_text}."

        patient_list = []
        for patient in patients[:10]:  # Show first 10 patients
            bed_text = f" in bed {patient['bed_info']['bed_number']} ({patient['bed_info']['ward']} ward, Room {patient['bed_info']['room_number']})" if patient['bed_info'] else " (no bed assigned)"
            patient_list.append(f"• {patient['name']} (ID: {patient['patient_id']}) - {patient['primary_condition']} ({patient['severity']}){bed_text}")

        patient_text = "\n".join(patient_list)
        ward_text = f" in {ward} ward" if ward else ""
        total_text = f" (showing {len(patient_list)} of {len(patients)})" if len(patients) > 10 else ""

        return f"Current admitted patients{ward_text}{total_text}:\n\n{patient_text}"

    @QueryOptimizer().cached_query('patient_lookup')
    def _handle_patient_lookup_query(self, entities, context, **kwargs):
        """Handle specific patient lookup queries"""
        patient_id = entities.get('patient_id')

        if not patient_id:
            return "Please provide a valid patient ID (e.g., 'PAT123' or 'ID: PAT123')."

        patient = self.get_patient_by_id(patient_id)
        if patient:
            bed_text = f" in bed {patient['bed_info']['bed_number']} ({patient['bed_info']['ward']} ward, Room {patient['bed_info']['room_number']}, Floor {patient['bed_info']['floor_number']}, {patient['bed_info']['wing']} Wing)" if patient['bed_info'] else " (no bed assigned)"
            return f"Patient Information:\n\n• Name: {patient['name']}\n• ID: {patient['patient_id']}\n• Age: {patient['age']}, Gender: {patient['gender']}\n• Condition: {patient['primary_condition']} ({patient['severity']})\n• Status: {patient['status']}\n• Admission Date: {patient['admission_date']}\n• Attending Physician: {patient['attending_physician']}\n• Location: {bed_text}\n• Emergency Contact: {patient['emergency_contact']}\n• Phone: {patient['phone']}"
        else:
            return f"Patient with ID '{patient_id}' not found in the system."

    @QueryOptimizer().cached_query('bed_availability')
    def _handle_bed_availability_query(self, entities, context, is_follow_up, **kwargs):
        """Handle bed availability queries with context awareness"""
        ward = entities.get('ward') or context.get('ward')

        # Use context if this is a follow-up
        if is_follow_up and not ward and 'ward' in context:
            ward = context['ward']

        available_beds = self.get_available_beds(ward)

        if not available_beds:
            ward_text = f" in {ward} ward" if ward else ""
            return f"There are currently no available beds{ward_text}."

        bed_list = []
        for bed in available_beds:
            bed_list.append(f"• {bed['bed_number']} ({bed['ward']} ward, Room {bed['room_number']})")

        bed_text = "\n".join(bed_list)
        ward_text = f" in {ward} ward" if ward else ""

        return f"Available beds{ward_text}:\n\n{bed_text}"

    @QueryOptimizer().cached_query('occupancy_status')
    def _handle_occupancy_status_query(self, entities, context, **kwargs):
        """Handle occupancy status queries"""
        data = self.get_bed_occupancy()
        if "error" in data:
            return f"Sorry, I encountered an error: {data['error']}"

        return f"Current bed occupancy is {data['occupancy_rate']}% with {data['occupied_beds']} occupied beds out of {data['total_beds']} total beds. {data['vacant_beds']} beds are available."

    def _handle_bed_assignment_query(self, entities, context):
        """Handle bed assignment requests"""
        ward = entities.get('ward') or context.get('ward')

        available_beds = self.get_available_beds(ward)

        if not available_beds:
            ward_text = f" in {ward} ward" if ward else ""
            return f"I'm sorry, there are currently no available beds{ward_text}. Would you like me to check other wards or add the patient to a waiting list?"

        bed_list = []
        for bed in available_beds[:5]:  # Show first 5 beds
            bed_list.append(f"• {bed['bed_number']} ({bed['ward']} ward, Room {bed['room_number']})")

        bed_text = "\n".join(bed_list)
        ward_text = f" in {ward} ward" if ward else ""

        return f"I can help you assign a patient to an available bed. We currently have {len(available_beds)} available beds{ward_text}.\n\nAvailable beds:\n{bed_text}\n\nTo assign a specific bed, please provide the patient details and preferred bed number."

    def _handle_discharge_info_query(self, entities, context):
        """Handle discharge information queries"""
        # This would integrate with discharge planning system
        return "Discharge information feature is being developed. Please contact the nursing station for current discharge schedules."

    def _handle_general_inquiry(self, query, context):
        """Handle general inquiries and provide help"""
        suggestions = self.intent_processor.suggest_corrections(query)

        if suggestions:
            suggestion_text = "\n".join([f"• {s}" for s in suggestions])
            return f"I'm not sure I understood your request. Here are some suggestions:\n\n{suggestion_text}"

        return "I'm the Enhanced Bed Management Agent. I can help you with:\n• Bed occupancy and availability\n• Patient information and lists\n• Assigning beds to patients\n• Checking specific ward availability\n\nTry asking:\n• 'What beds are available in ICU?'\n• 'Show me ICU department patients'\n• 'Patient list'\n• 'PAT123' (for specific patient info)\n• 'Assign a patient to an ICU bed'"

    def get_session_info(self):
        """Get comprehensive session information"""
        return {
            "session_id": self.session_id,
            "conversation_summary": self.conversation_memory.get_conversation_summary(),
            "performance_stats": self.performance_monitor.get_performance_report(),
            "cache_stats": self.query_optimizer.get_performance_stats(),
            "error_stats": self.error_handler.get_error_statistics()
        }

# Enhanced Bed Agent is ready for use
# Example: agent = EnhancedBedAgent(session_id="your_session_id")
