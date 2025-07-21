"""
Main FastAPI application for Hospital Agent Platform
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import logging
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

try:
    from .config import settings
    from .database import get_db, create_tables, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from .schemas import BedResponse, PatientResponse, DashboardMetrics, ChatRequest, ChatResponse
except ImportError:
    from config import settings
    from database import get_db, create_tables, Bed, Patient, BedOccupancyHistory, AgentLog, Staff
    from schemas import BedResponse, PatientResponse, DashboardMetrics, ChatRequest, ChatResponse

# Configure logging first
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Import real-time systems (after logger is defined)
try:
    from .alert_system import alert_system
    from .websocket_manager import websocket_manager, real_time_updater
    from .workflow_engine import workflow_engine
    from .admission_system import admission_system, AdmissionRequest, AdmissionType, AdmissionPriority
    from .clinical_decision_support import clinical_decision_support
    from .real_time_bed_monitor import initialize_bed_monitor, get_bed_monitor
    from .autonomous_bed_agent import autonomous_bed_agent
    from .predictive_analytics import predictive_analytics
    from .intelligent_bed_assignment import intelligent_bed_assignment
    from .autonomous_scheduler import autonomous_scheduler
    from .proactive_action_system import proactive_action_system
    logger.info("✅ Real-time and autonomous systems imported successfully")
except ImportError as e:
    # Fallback if real-time systems not available
    logger.warning(f"⚠️ Import error details: {e}")
    try:
        from alert_system import alert_system
        from websocket_manager import websocket_manager, real_time_updater
        from workflow_engine import workflow_engine
        from admission_system import admission_system, AdmissionRequest, AdmissionType, AdmissionPriority
        from clinical_decision_support import clinical_decision_support
        from real_time_bed_monitor import initialize_bed_monitor, get_bed_monitor
        from autonomous_bed_agent import autonomous_bed_agent
        from predictive_analytics import predictive_analytics
        from intelligent_bed_assignment import intelligent_bed_assignment
        from autonomous_scheduler import autonomous_scheduler
        from proactive_action_system import proactive_action_system
        logger.info("✅ Real-time and autonomous systems imported successfully (fallback)")
    except ImportError as e2:
        # Final fallback if real-time systems not available
        logger.warning(f"⚠️ Real-time and autonomous systems not available: {e2}")
        alert_system = None
        websocket_manager = None
        real_time_updater = None
        workflow_engine = None
        admission_system = None
        clinical_decision_support = None
        initialize_bed_monitor = None
        get_bed_monitor = None
        autonomous_bed_agent = None
        predictive_analytics = None
        intelligent_bed_assignment = None
        autonomous_scheduler = None
        proactive_action_system = None

# Bed monitor will be managed by singleton pattern

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and real-time services"""
    try:
        create_tables()
        logger.info("Database tables created")

        # Start systems individually to avoid dependency issues
        systems_started = []

        # Start alert system (most critical)
        if alert_system:
            try:
                await alert_system.start_monitoring()
                systems_started.append("Alert System")
                logger.info("🚨 Alert system started successfully")

                # Create initial alerts
                await create_initial_alerts()

            except Exception as e:
                logger.error(f"Failed to start alert system: {e}")

        # Start real-time updates if available
        if real_time_updater:
            try:
                await real_time_updater.start_updates()
                systems_started.append("Real-time Updates")
                logger.info("🔄 Real-time updates started")
            except Exception as e:
                logger.error(f"Failed to start real-time updates: {e}")

        # Start bed monitoring if available
        if initialize_bed_monitor and websocket_manager:
            try:
                bed_monitor = initialize_bed_monitor(websocket_manager)
                await bed_monitor.start_monitoring()
                systems_started.append("Bed Monitor")
                logger.info("🛏️ Real-time bed monitoring started")
            except Exception as e:
                logger.error(f"Failed to start bed monitoring: {e}")

        # Subscribe alert system to websocket if both available
        if alert_system and websocket_manager:
            try:
                alert_system.subscribe_to_alerts(websocket_manager.send_alert_update)
                logger.info("🔗 Alert system connected to WebSocket")
            except Exception as e:
                logger.error(f"Failed to connect alert system to WebSocket: {e}")

        logger.info(f"✅ Started {len(systems_started)} core systems: {', '.join(systems_started)}")

        # Start workflow engine
        if workflow_engine:
            try:
                await workflow_engine.start_engine()
                logger.info("⚙️ Workflow engine started")
            except Exception as e:
                logger.error(f"Failed to start workflow engine: {e}")

        # Start autonomous systems
        autonomous_systems_started = []

        if autonomous_scheduler:
            try:
                await autonomous_scheduler.start_scheduler()
                autonomous_systems_started.append("Scheduler")
                logger.info("🤖 Autonomous scheduler started")
            except Exception as e:
                logger.error(f"Failed to start autonomous scheduler: {e}")

        if autonomous_bed_agent:
            try:
                await autonomous_bed_agent.start_monitoring()
                autonomous_systems_started.append("Bed Agent")
                logger.info("🛏️ Autonomous bed agent started")
            except Exception as e:
                logger.error(f"Failed to start autonomous bed agent: {e}")

        if proactive_action_system:
            try:
                await proactive_action_system.start_proactive_system()
                autonomous_systems_started.append("Proactive Actions")
                logger.info("🚀 Proactive action system started")
            except Exception as e:
                logger.error(f"Failed to start proactive action system: {e}")

        if intelligent_bed_assignment:
            try:
                # Initialize intelligent bed assignment (no start method needed)
                autonomous_systems_started.append("Intelligent Assignment")
                logger.info("🧠 Intelligent bed assignment ready")
            except Exception as e:
                logger.error(f"Failed to initialize intelligent bed assignment: {e}")

        if predictive_analytics:
            try:
                # Initialize predictive analytics (no start method needed)
                autonomous_systems_started.append("Predictive Analytics")
                logger.info("🔮 Predictive analytics ready")
            except Exception as e:
                logger.error(f"Failed to initialize predictive analytics: {e}")

        # Start admission system
        if admission_system:
            try:
                await admission_system.start_system()
                autonomous_systems_started.append("Admission System")
                logger.info("🏥 Admission system started")
            except Exception as e:
                logger.error(f"Failed to start admission system: {e}")

        # Start clinical decision support
        if clinical_decision_support:
            try:
                await clinical_decision_support.start_system()
                autonomous_systems_started.append("Clinical Support")
                logger.info("🧠 Clinical decision support started")
            except Exception as e:
                logger.error(f"Failed to start clinical decision support: {e}")

        logger.info(f"🤖 Started {len(autonomous_systems_started)} autonomous systems: {', '.join(autonomous_systems_started)}")
        logger.info("🏥 Hospital Agent Platform started successfully!")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Continue anyway - database might already exist

async def create_initial_alerts():
    """Create initial alerts for testing"""
    try:
        if alert_system:
            from alert_system import Alert, AlertType, AlertPriority
            from database import SessionLocal, Bed
            from datetime import datetime

            # Check ICU capacity and create alert if needed
            with SessionLocal() as db:
                icu_total = db.query(Bed).filter(Bed.ward == "ICU").count()
                icu_occupied = db.query(Bed).filter(Bed.ward == "ICU", Bed.status == "occupied").count()
                icu_rate = (icu_occupied / icu_total * 100) if icu_total > 0 else 0

                if icu_rate >= 90:
                    alert = Alert(
                        id="",
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.CRITICAL,
                        title="ICU Capacity Critical",
                        message=f"ICU at {icu_rate:.1f}% capacity ({icu_occupied}/{icu_total} beds). Immediate action required!",
                        department="ICU",
                        action_required=True,
                        metadata={
                            "icu_occupancy_rate": icu_rate,
                            "icu_total": icu_total,
                            "icu_occupied": icu_occupied,
                            "alert_type": "capacity_critical",
                            "auto_generated": True
                        }
                    )
                    await alert_system.create_alert(alert)
                    logger.info(f"🚨 Created initial ICU alert: {icu_rate:.1f}% occupancy")

                # Create a general capacity alert
                total_beds = db.query(Bed).count()
                occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
                occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

                if occupancy_rate >= 60:
                    alert = Alert(
                        id="",
                        type=AlertType.CAPACITY_CRITICAL,
                        priority=AlertPriority.HIGH,
                        title="Hospital Capacity Alert",
                        message=f"Hospital at {occupancy_rate:.1f}% capacity ({occupied_beds}/{total_beds} beds occupied).",
                        department="Administration",
                        action_required=True,
                        metadata={
                            "occupancy_rate": occupancy_rate,
                            "total_beds": total_beds,
                            "occupied_beds": occupied_beds,
                            "alert_type": "general_capacity",
                            "auto_generated": True
                        }
                    )
                    await alert_system.create_alert(alert)
                    logger.info(f"🏥 Created general capacity alert: {occupancy_rate:.1f}% occupancy")

    except Exception as e:
        logger.error(f"Error creating initial alerts: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Stop all systems
    systems_to_stop = [
        (alert_system, "stop_monitoring", "Real-time alert system"),
        (real_time_updater, "stop_updates", "Real-time updates"),
        (workflow_engine, "stop_engine", "Workflow engine"),
        (admission_system, "stop_system", "Admission system"),
        (clinical_decision_support, "stop_system", "Clinical decision support")
    ]

    # Stop bed monitor if available
    if get_bed_monitor:
        try:
            bed_monitor = get_bed_monitor()
            if bed_monitor:
                await bed_monitor.stop_monitoring()
                logger.info("🛏️ Real-time bed monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping bed monitor: {e}")

    for system, method_name, system_name in systems_to_stop:
        if system:
            try:
                method = getattr(system, method_name)
                await method()
                logger.info(f"🛑 {system_name} stopped")
            except Exception as e:
                logger.error(f"Error stopping {system_name}: {e}")





# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hospital Operations & Logistics Agentic Platform", "version": settings.version}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}


@app.get("/api/beds", response_model=List[BedResponse])
async def get_beds(db: Session = Depends(get_db)):
    """Get all beds"""
    beds = db.query(Bed).all()
    return beds


@app.get("/api/patients", response_model=List[PatientResponse])
async def get_patients(db: Session = Depends(get_db)):
    """Get all patients"""
    patients = db.query(Patient).all()
    return patients


@app.get("/api/beds/occupancy")
async def get_bed_occupancy_simple(db: Session = Depends(get_db)):
    """Get bed occupancy status (simplified for real-time dashboard)"""
    try:
        # Calculate occupancy statistics
        total_beds = db.query(Bed).count()
        occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
        vacant_beds = db.query(Bed).filter(Bed.status == "vacant").count()
        cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
        maintenance_beds = db.query(Bed).filter(Bed.status == "maintenance").count()

        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0

        # Get ward breakdown
        ward_breakdown = []
        wards = db.query(Bed.ward).distinct().all()

        for (ward_name,) in wards:
            ward_total = db.query(Bed).filter(Bed.ward == ward_name).count()
            ward_occupied = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == "occupied").count()
            ward_vacant = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == "vacant").count()
            ward_cleaning = db.query(Bed).filter(Bed.ward == ward_name, Bed.status == "cleaning").count()
            ward_rate = (ward_occupied / ward_total * 100) if ward_total > 0 else 0

            ward_breakdown.append({
                "ward": ward_name,
                "total_beds": ward_total,
                "occupied": ward_occupied,
                "vacant": ward_vacant,
                "cleaning": ward_cleaning,
                "occupancy_rate": round(ward_rate, 1)
            })

        return {
            "overall": {
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "vacant_beds": vacant_beds,
                "cleaning_beds": cleaning_beds,
                "maintenance_beds": maintenance_beds,
                "occupancy_rate": round(occupancy_rate, 1)
            },
            "ward_breakdown": ward_breakdown,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admissions/submit")
async def submit_admission_request(request: dict, db: Session = Depends(get_db)):
    """Submit a new patient admission request"""
    try:
        if admission_system:
            # Use the enhanced admission system
            from admission_system import AdmissionRequest, AdmissionType, AdmissionPriority

            # Map request data to admission system format
            admission_type = getattr(AdmissionType, request.get('admission_type', 'scheduled').upper(), AdmissionType.SCHEDULED)
            priority = getattr(AdmissionPriority, request.get('priority', 'routine').upper(), AdmissionPriority.ROUTINE)

            admission_request = AdmissionRequest(
                patient_id=request.get('patient_id'),
                patient_name=request.get('patient_name'),
                age=int(request.get('age', 0)),
                gender=request.get('gender', 'unknown'),
                primary_condition=request.get('primary_condition'),
                severity=request.get('severity', 'stable'),
                admission_type=admission_type,
                priority=priority,
                attending_physician=request.get('attending_physician'),
                special_requirements=request.get('special_needs', []),
                estimated_los=int(request.get('estimated_los', 1)) if request.get('estimated_los') else None
            )

            result = await admission_system.submit_request(admission_request)
            return {
                "success": True,
                "request_id": result.request_id,
                "status": result.status,
                "message": "Admission request submitted successfully"
            }
        else:
            # Fallback: Create patient record directly
            patient = Patient(
                patient_id=request.get('patient_id'),
                name=request.get('patient_name'),
                age=int(request.get('age', 0)),
                gender=request.get('gender', 'unknown'),
                phone=request.get('phone', ''),
                emergency_contact=request.get('emergency_contact', ''),
                primary_condition=request.get('primary_condition', ''),
                severity=request.get('severity', 'stable'),
                attending_physician=request.get('attending_physician', ''),
                admission_date=datetime.now(),
                status='pending_assignment'
            )

            db.add(patient)
            db.commit()
            db.refresh(patient)

            return {
                "success": True,
                "request_id": f"ADM{patient.id}",
                "status": "submitted",
                "message": "Patient record created successfully"
            }

    except Exception as e:
        logger.error(f"Admission submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/beds/{bed_id}/assign")
async def assign_bed_to_patient(bed_id: str, request: dict, db: Session = Depends(get_db)):
    """Assign a specific bed to a patient"""
    try:
        # Find the bed
        bed = db.query(Bed).filter(Bed.bed_number == bed_id).first()
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")

        if bed.status != "vacant":
            raise HTTPException(status_code=400, detail="Bed is not available")

        # Find the patient
        patient_id = request.get('patient_id')
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Update bed status
        bed.status = "occupied"
        bed.patient_id = patient_id
        bed.last_updated = datetime.now()

        # Update patient status
        patient.current_bed_id = bed.id
        patient.status = "admitted"
        patient.admission_date = datetime.now()

        # Create occupancy history record
        occupancy_record = BedOccupancyHistory(
            bed_id=bed.id,
            patient_id=patient_id,
            start_time=datetime.now(),
            status="occupied"
        )

        db.add(occupancy_record)
        db.commit()

        # Log the assignment
        log_entry = AgentLog(
            agent_type="bed_management",
            action="bed_assignment",
            details=f"Assigned bed {bed_id} to patient {patient_id}",
            timestamp=datetime.now()
        )
        db.add(log_entry)
        db.commit()

        # Trigger workflow if available
        workflow_id = None
        if workflow_engine:
            try:
                workflow_id = await workflow_engine.start_admission_workflow(
                    patient_id=patient_id,
                    bed_id=bed_id,
                    admission_type=request.get('admission_type', 'scheduled')
                )
            except Exception as e:
                logger.warning(f"Workflow engine error: {e}")

        return {
            "success": True,
            "bed_id": bed_id,
            "patient_id": patient_id,
            "workflow_id": workflow_id,
            "message": f"Patient {patient_id} successfully assigned to bed {bed_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bed assignment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Get dashboard metrics"""
    total_beds = db.query(Bed).count()
    occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
    vacant_beds = db.query(Bed).filter(Bed.status == "vacant").count()
    cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
    
    occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    
    # Patient satisfaction (mock data)
    patient_satisfaction = 8.5
    
    # Available staff (mock data)
    available_staff = 70
    
    # Resource utilization (mock data)
    resource_utilization = 75.0
    
    return DashboardMetrics(
        bed_occupancy=occupancy_rate,
        patient_satisfaction=patient_satisfaction,
        available_staff=available_staff,
        resource_utilization=resource_utilization,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        vacant_beds=vacant_beds,
        cleaning_beds=cleaning_beds
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with the enhanced bed management agent with MCP integration"""
    try:
        # Try MCP agent first for advanced capabilities
        try:
            from agents.bed_management.mcp_agent import MCPBedManagementAgent

            mcp_agent = MCPBedManagementAgent(use_mcp=True)
            result = mcp_agent.process_query(request.message)

            logger.info(f"MCP Agent processed query: {request.message[:50]}...")

        except Exception as mcp_error:
            logger.warning(f"MCP agent failed, falling back to enhanced agent: {mcp_error}")

            # Fallback to enhanced chat agent
            from enhanced_chat_agent import EnhancedChatAgent

            agent = EnhancedChatAgent()
            result = agent.process_query(request.message, db)

            # Ensure result has required fields
            if not isinstance(result, dict):
                result = {
                    "response": str(result),
                    "timestamp": datetime.now().isoformat(),
                    "agent": "enhanced_chat_agent_fallback"
                }

        # Log the interaction
        log_entry = AgentLog(
            agent_name="bed_management_agent",
            action="chat_interaction",
            details=f"User: {request.message} | Tools: {result.get('tools_used', [])}",
            status="success"
        )
        db.add(log_entry)
        db.commit()

        return ChatResponse(
            response=result["response"],
            timestamp=datetime.fromisoformat(result["timestamp"]),
            agent=result["agent"]
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")

        # Log the error
        log_entry = AgentLog(
            agent_name="bed_management_agent",
            action="chat_interaction",
            details=f"User: {request.message} | Error: {str(e)}",
            status="error"
        )
        db.add(log_entry)
        db.commit()

        return ChatResponse(
            response="I apologize, but I encountered an error while processing your request. Please try again.",
            timestamp=datetime.now(),
            agent="bed_management_agent"
        )

@app.post("/api/chat/assign-patient")
async def assign_patient_from_chat(
    patient_name: str,
    bed_id: int,
    doctor_id: int = None,
    db: Session = Depends(get_db)
):
    """Assign patient to bed from chat interface"""
    try:
        from enhanced_chat_agent import EnhancedChatAgent

        agent = EnhancedChatAgent()

        # If no doctor specified, find available doctor
        if not doctor_id:
            bed = db.query(Bed).filter(Bed.id == bed_id).first()
            if bed and bed.ward:
                doctors = agent.get_available_doctors(db, bed.ward)
                if doctors:
                    doctor_id = doctors[0]['id']

        result = agent.create_patient_assignment_workflow(patient_name, bed_id, doctor_id, db)

        if result['success']:
            return {
                "success": True,
                "message": f"✅ Patient {patient_name} successfully assigned to bed {result['bed_number']}",
                "details": result
            }
        else:
            return {
                "success": False,
                "message": f"❌ Failed to assign patient: {result['error']}"
            }

    except Exception as e:
        logger.error(f"Error in patient assignment: {e}")
        return {
            "success": False,
            "message": f"❌ Error: {str(e)}"
        }

@app.get("/api/chat/available-beds/{ward_type}")
async def get_available_beds_by_ward(ward_type: str, db: Session = Depends(get_db)):
    """Get available beds by ward type for chat interface"""
    try:
        beds = db.query(Bed).filter(
            Bed.status == 'vacant',
            Bed.ward.ilike(f'%{ward_type}%')
        ).all()

        return {
            "beds": [
                {
                    "id": bed.id,
                    "bed_number": bed.bed_number,
                    "ward": bed.ward,
                    "status": bed.status
                }
                for bed in beds
            ],
            "count": len(beds),
            "ward_type": ward_type
        }

    except Exception as e:
        logger.error(f"Error getting beds by ward: {e}")
        return {"beds": [], "count": 0, "error": str(e)}

@app.get("/api/patients")
async def get_patients(db: Session = Depends(get_db)):
    """Get all patients in the database"""
    try:
        patients = db.query(Patient).all()
        return {
            "patients": [
                {
                    "id": patient.id,
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "status": patient.status,
                    "admission_date": patient.admission_date.isoformat() if patient.admission_date else None,
                    "age": getattr(patient, 'age', None),
                    "gender": getattr(patient, 'gender', None),
                    "condition": getattr(patient, 'condition', None)
                }
                for patient in patients
            ],
            "count": len(patients)
        }
    except Exception as e:
        logger.error(f"Error getting patients: {e}")
        return {"patients": [], "count": 0, "error": str(e)}

@app.get("/api/staff")
async def get_staff(db: Session = Depends(get_db)):
    """Get all staff/doctors in the database"""
    try:
        staff = db.query(Staff).all()
        return {
            "staff": [
                {
                    "id": person.id,
                    "staff_id": person.staff_id,
                    "name": person.name,
                    "role": person.role,
                    "specialization": getattr(person, 'specialization', 'General Medicine'),
                    "department_id": getattr(person, 'department_id', None),
                    "shift": getattr(person, 'shift', 'Day'),
                    "available": True  # Simplified - in real system check schedule
                }
                for person in staff
            ],
            "count": len(staff)
        }
    except Exception as e:
        logger.error(f"Error getting staff: {e}")
        return {"staff": [], "count": 0, "error": str(e)}

@app.get("/api/doctors")
async def get_doctors(specialty: str = None, db: Session = Depends(get_db)):
    """Get doctors, optionally filtered by specialty"""
    try:
        query = db.query(Staff).filter(Staff.role.ilike('%doctor%'))
        if specialty:
            query = query.filter(Staff.specialization.ilike(f'%{specialty}%'))

        doctors = query.all()
        return {
            "doctors": [
                {
                    "id": doc.id,
                    "staff_id": doc.staff_id,
                    "name": doc.name,
                    "specialization": getattr(doc, 'specialization', 'General Medicine'),
                    "department_id": getattr(doc, 'department_id', None),
                    "available": True  # Simplified
                }
                for doc in doctors
            ],
            "count": len(doctors),
            "specialty_filter": specialty
        }
    except Exception as e:
        logger.error(f"Error getting doctors: {e}")
        return {"doctors": [], "count": 0, "error": str(e)}

@app.post("/api/chat/mcp")
async def chat_with_mcp_agent(request: ChatRequest):
    """Chat specifically with MCP-enabled agent for advanced capabilities"""
    try:
        from agents.bed_management.mcp_agent import MCPBedManagementAgent

        mcp_agent = MCPBedManagementAgent(use_mcp=True)
        result = mcp_agent.process_query(request.message)

        return ChatResponse(
            response=result.get("response", "No response generated"),
            timestamp=datetime.fromisoformat(result.get("timestamp", datetime.now().isoformat())),
            agent=result.get("agent", "mcp_bed_management_agent"),
            tools_used=result.get("tools_used", []),
            mcp_enabled=result.get("mcp_enabled", True)
        )

    except Exception as e:
        logger.error(f"MCP agent error: {e}")
        return ChatResponse(
            response=f"MCP agent encountered an error: {str(e)}. Please check MCP server status.",
            timestamp=datetime.now(),
            agent="mcp_bed_management_agent",
            tools_used=[],
            mcp_enabled=False
        )

@app.get("/api/mcp/status")
async def get_mcp_status():
    """Check MCP server status and available tools"""
    try:
        from agents.bed_management.mcp_agent import MCPBedManagementAgent

        agent = MCPBedManagementAgent(use_mcp=True)

        # Test MCP connection by trying to get bed status
        test_result = agent.process_query("What is the current bed status?")

        return {
            "mcp_enabled": True,
            "status": "connected",
            "tools_available": test_result.get("tools_used", []),
            "last_test": datetime.now().isoformat(),
            "agent_type": test_result.get("agent", "unknown")
        }

    except Exception as e:
        logger.error(f"MCP status check failed: {e}")
        return {
            "mcp_enabled": False,
            "status": "disconnected",
            "error": str(e),
            "last_test": datetime.now().isoformat()
        }


# Advanced Hospital Management API Endpoints

# Workflow Management
@app.post("/api/workflows/create")
async def create_workflow(workflow_type: str, parameters: dict):
    """Create a new workflow"""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        workflow_id = await workflow_engine.create_workflow(workflow_type, parameters)
        return {"workflow_id": workflow_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/workflows/active")
async def get_active_workflows():
    """Get all active workflows"""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    return {"workflows": workflow_engine.get_active_workflows()}

@app.get("/api/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    status = workflow_engine.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return status

@app.post("/api/workflows/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """Cancel a workflow"""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    await workflow_engine.cancel_workflow(workflow_id)
    return {"message": f"Workflow {workflow_id} cancelled"}

# Combined endpoint for patient admission and bed assignment
@app.post("/api/beds/{bed_id}/assign-new-patient")
async def assign_new_patient_to_bed(bed_id: str, request: dict, db: Session = Depends(get_db)):
    """Create a new patient and assign them to a specific bed in one operation"""
    try:
        # Find the bed
        bed = db.query(Bed).filter(Bed.bed_number == bed_id).first()
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")

        if bed.status != "vacant":
            raise HTTPException(status_code=400, detail="Bed is not available")

        # Create new patient record
        patient = Patient(
            patient_id=request.get('patient_id'),
            name=request.get('patient_name'),
            age=int(request.get('age', 0)),
            gender=request.get('gender', 'unknown'),
            phone=request.get('phone', ''),
            emergency_contact=request.get('emergency_contact', ''),
            primary_condition=request.get('primary_condition', ''),
            severity=request.get('severity', 'stable'),
            attending_physician=request.get('attending_physician', ''),
            admission_date=datetime.now(),
            current_bed_id=bed.id,
            status='admitted'
        )

        db.add(patient)
        db.flush()  # Get the patient ID

        # Update bed status
        bed.status = "occupied"
        bed.patient_id = patient.patient_id
        bed.last_updated = datetime.now()

        # Create occupancy history record
        occupancy_record = BedOccupancyHistory(
            bed_id=bed.id,
            patient_id=patient.patient_id,
            start_time=datetime.now(),
            status="occupied"
        )

        db.add(occupancy_record)
        db.commit()

        # Log the assignment
        log_entry = AgentLog(
            agent_name="bed_management_agent",
            action="bed_assignment",
            details=f"Assigned new patient {patient.name} (ID: {patient.patient_id}) to bed {bed.bed_number}",
            status="success"
        )
        db.add(log_entry)
        db.commit()

        return {
            "success": True,
            "workflow_id": f"WF{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "bed_number": bed.bed_number,
            "patient_id": patient.patient_id,
            "patient_name": patient.name,
            "message": f"Successfully assigned {patient.name} to bed {bed.bed_number}"
        }

    except Exception as e:
        logger.error(f"Bed assignment error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign patient to bed: {str(e)}")


@app.get("/api/doctors")
async def get_doctors(db: Session = Depends(get_db)):
    """Get list of doctors from staff table"""
    try:
        doctors = db.query(Staff).filter(Staff.role == 'doctor').all()

        return [{
            "id": doctor.staff_id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "department": doctor.department_id
        } for doctor in doctors]

    except Exception as e:
        logger.error(f"Error fetching doctors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information and statistics"""
    try:
        from agents.bed_management.simple_agent import EnhancedBedAgent
        agent = EnhancedBedAgent(session_id=session_id)
        return agent.get_session_info()
    except Exception as e:
        logger.error(f"Session info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/performance")
async def get_performance_stats():
    """Get overall chatbot performance statistics"""
    try:
        from agents.bed_management.simple_agent import EnhancedBedAgent
        # Create a temporary agent to get performance stats
        agent = EnhancedBedAgent()
        return {
            "performance_stats": agent.performance_monitor.get_performance_report(),
            "cache_stats": agent.query_optimizer.get_performance_stats(),
            "error_stats": agent.error_handler.get_error_statistics(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admissions/queue")
async def get_admission_queue():
    """Get admission queue status"""
    if not admission_system:
        raise HTTPException(status_code=503, detail="Admission system not available")

    return admission_system.get_admission_queue_status()

# Clinical Decision Support
@app.post("/api/clinical/recommendations")
async def get_clinical_recommendations(query: str, context: dict = None):
    """Get clinical recommendations"""
    if not clinical_decision_support:
        raise HTTPException(status_code=503, detail="Clinical decision support not available")

    try:
        recommendations = await clinical_decision_support.get_recommendation(query, context)
        return {
            "recommendations": [
                {
                    "id": rec.id,
                    "type": rec.type.value,
                    "priority": rec.priority.value,
                    "title": rec.title,
                    "description": rec.description,
                    "rationale": rec.rationale,
                    "recommended_actions": rec.recommended_actions,
                    "confidence_score": rec.confidence_score,
                    "department": rec.department
                }
                for rec in recommendations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/clinical/recommendations/active")
async def get_active_clinical_recommendations():
    """Get all active clinical recommendations"""
    if not clinical_decision_support:
        raise HTTPException(status_code=503, detail="Clinical decision support not available")

    return {"recommendations": clinical_decision_support.get_active_recommendations()}

# Bed Management Operations
@app.post("/api/beds/{bed_id}/assign")
async def assign_bed(bed_id: int, patient_id: str):
    """Assign a bed to a patient"""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        workflow_id = await workflow_engine.create_workflow(
            "bed_assignment",
            {"patient_id": patient_id, "preferred_bed_id": bed_id}
        )
        return {"workflow_id": workflow_id, "message": "Bed assignment workflow started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/beds/{bed_id}/clean")
async def initiate_bed_cleaning(bed_id: int):
    """Initiate bed cleaning workflow"""
    if not workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not available")

    try:
        workflow_id = await workflow_engine.create_workflow(
            "bed_cleaning",
            {"bed_id": bed_id}
        )
        return {"workflow_id": workflow_id, "message": "Bed cleaning workflow started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# System Status and Analytics
@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "systems": {
            "alert_system": alert_system is not None and alert_system.running if alert_system else False,
            "workflow_engine": workflow_engine is not None and workflow_engine.running if workflow_engine else False,
            "admission_system": admission_system is not None and admission_system.running if admission_system else False,
            "clinical_decision_support": clinical_decision_support is not None and clinical_decision_support.running if clinical_decision_support else False,
            "websocket_manager": websocket_manager is not None
        }
    }

    # Add connection stats if available
    if websocket_manager:
        status["websocket_connections"] = websocket_manager.get_connection_stats()

    return status

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        db = get_db()

        # Basic metrics
        total_beds = db.query(Bed).count()
        occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
        total_patients = db.query(Patient).filter(Patient.status == "admitted").count()

        # System metrics
        analytics = {
            "timestamp": datetime.now().isoformat(),
            "bed_metrics": {
                "total_beds": total_beds,
                "occupied_beds": occupied_beds,
                "occupancy_rate": (occupied_beds / total_beds * 100) if total_beds > 0 else 0,
                "available_beds": total_beds - occupied_beds
            },
            "patient_metrics": {
                "total_admitted": total_patients,
                "average_los": 3.2,  # This would be calculated from actual data
                "discharge_rate": 85.5  # This would be calculated from actual data
            },
            "system_metrics": {
                "active_workflows": len(workflow_engine.get_active_workflows()) if workflow_engine else 0,
                "pending_admissions": len(admission_system.pending_admissions) if admission_system else 0,
                "active_alerts": len(alert_system.get_active_alerts()) if alert_system else 0,
                "active_recommendations": len(clinical_decision_support.get_active_recommendations()) if clinical_decision_support else 0
            }
        }

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoints for Real-time Updates
@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates"""
    if not websocket_manager:
        await websocket.close(code=1000, reason="Real-time features not available")
        return

    await websocket_manager.connect_dashboard(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data) if data else {}

            # Handle client requests
            if message.get("type") == "request_update":
                await websocket_manager.send_initial_dashboard_data(websocket)
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    if not websocket_manager:
        await websocket.close(code=1000, reason="Real-time features not available")
        return

    await websocket_manager.connect_alerts(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data) if data else {}

            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Alerts WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

@app.websocket("/ws/bed-status")
async def websocket_bed_status(websocket: WebSocket):
    """WebSocket endpoint for bed status updates"""
    if not websocket_manager:
        await websocket.close(code=1000, reason="Real-time features not available")
        return

    await websocket_manager.connect_bed_status(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data) if data else {}

            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Bed status WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# Debug endpoint
@app.get("/api/debug/alert-system")
async def debug_alert_system():
    """Debug alert system status"""
    return {
        "alert_system_exists": alert_system is not None,
        "alert_system_type": str(type(alert_system)),
        "alert_system_running": getattr(alert_system, 'running', False) if alert_system else False,
        "active_alerts_count": len(getattr(alert_system, 'active_alerts', {})) if alert_system else 0
    }

# Real-time API endpoints
@app.get("/api/alerts/active")
async def get_active_alerts():
    """Get all active real-time alerts using MCP tools"""
    try:
        # Use MCP tools to get real-time alerts
        from hospital_mcp.simple_client import SimpleMCPToolsManager

        # Get alerts from MCP (use await since we're already in async function)
        manager = SimpleMCPToolsManager()
        await manager.initialize()
        alerts = await manager.execute_tool('get_critical_bed_alerts')

        # Ensure alerts is a list
        if not isinstance(alerts, list):
            alerts = []

        # Add IDs and created_at timestamps to MCP alerts if missing
        from datetime import datetime
        current_time = datetime.now().isoformat()

        for alert in alerts:
            if 'id' not in alert:
                alert['id'] = f"{alert.get('type', 'alert')}_{int(datetime.now().timestamp())}"
            if 'created_at' not in alert:
                alert['created_at'] = alert.get('timestamp', current_time)

        logger.info(f"Generated {len(alerts)} MCP alerts")
        return {"alerts": alerts, "count": len(alerts), "timestamp": current_time}

    except Exception as e:
        logger.error(f"Error generating alerts: {e}")
        # Return fallback alerts on error
        from datetime import datetime
        fallback_alerts = [
            {
                "id": "system_error",
                "type": "system_error",
                "priority": "medium",
                "title": "Alert System Error",
                "message": "Alert system temporarily unavailable. Using fallback mode.",
                "department": "System",
                "action_required": False,
                "created_at": datetime.now().isoformat(),
                "metadata": {"error": str(e)}
            }
        ]
        return {"alerts": fallback_alerts, "count": 1, "error": str(e)}

@app.post("/api/alerts/create")
async def create_alert_endpoint(alert_data: dict):
    """Create a new alert"""
    try:
        # Try to import alert system directly
        try:
            from alert_system import alert_system as direct_alert_system, Alert, AlertType, AlertPriority
        except ImportError:
            try:
                from backend.alert_system import alert_system as direct_alert_system, Alert, AlertType, AlertPriority
            except ImportError:
                direct_alert_system = alert_system

        if not direct_alert_system:
            return {"success": False, "error": "Alert system not available"}

        # Create alert object
        alert = Alert(
            id="",  # Will be generated
            type=getattr(AlertType, alert_data.get("type", "GENERAL").upper(), AlertType.GENERAL),
            priority=getattr(AlertPriority, alert_data.get("priority", "MEDIUM").upper(), AlertPriority.MEDIUM),
            title=alert_data.get("title", "Alert"),
            message=alert_data.get("message", "No message"),
            department=alert_data.get("department", "General"),
            action_required=alert_data.get("action_required", False),
            metadata=alert_data.get("metadata", {})
        )

        # Create the alert
        await direct_alert_system.create_alert(alert)

        return {
            "success": True,
            "alert_id": alert.id,
            "message": f"Alert '{alert.title}' created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/alerts/create-test")
async def create_test_alert():
    """Create a test alert for debugging"""
    try:
        # Import alert system directly
        try:
            from alert_system import alert_system as direct_alert_system, Alert, AlertType, AlertPriority
        except ImportError:
            try:
                from .alert_system import alert_system as direct_alert_system, Alert, AlertType, AlertPriority
            except ImportError:
                return {"error": "Could not import alert system"}

        if not direct_alert_system:
            return {"error": "Alert system not available"}

        # Start alert system if not running
        if not direct_alert_system.running:
            await direct_alert_system.start_monitoring()

        # Create test alert
        from datetime import datetime
        test_alert = Alert(
            id="",  # Will be set by create_alert
            type=AlertType.CAPACITY_CRITICAL,
            priority=AlertPriority.HIGH,
            title="Dashboard Test Alert",
            message=f"Test alert created at {datetime.now().strftime('%H:%M:%S')} for dashboard testing",
            department="Dashboard",
            action_required=True,
            metadata={"created_via": "api", "test": True}
        )

        alert_id = await direct_alert_system.create_alert(test_alert)
        active_count = len(direct_alert_system.get_active_alerts())

        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Test alert created successfully",
            "active_alerts_count": active_count
        }

    except Exception as e:
        logger.error(f"Error creating test alert: {e}")
        return {"error": f"Failed to create test alert: {str(e)}"}

@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an active alert"""
    if not alert_system:
        raise HTTPException(status_code=503, detail="Real-time alerts not available")

    await alert_system.resolve_alert(alert_id)
    return {"message": f"Alert {alert_id} resolved"}

@app.get("/api/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    if not websocket_manager:
        return {"message": "WebSocket manager not available"}

    return websocket_manager.get_connection_stats()

# Real-time Bed Monitoring API Endpoints
@app.get("/api/beds/real-time/test")
async def test_bed_monitoring():
    """Test endpoint for bed monitoring"""
    return {
        "message": "Bed monitoring endpoint is working",
        "timestamp": datetime.now().isoformat(),
        "get_bed_monitor_available": get_bed_monitor is not None,
        "initialize_bed_monitor_available": initialize_bed_monitor is not None
    }

@app.get("/api/beds/real-time/status")
async def get_real_time_bed_status():
    """Get current real-time bed status"""
    logger.info(f"🔍 Debug: get_bed_monitor function available: {get_bed_monitor is not None}")

    if not get_bed_monitor:
        logger.warning("❌ get_bed_monitor function not available")
        return {"message": "Real-time bed monitoring not available", "beds": []}

    try:
        bed_monitor = get_bed_monitor()
        logger.info(f"🔍 Debug: bed_monitor instance: {bed_monitor is not None}")

        if not bed_monitor:
            logger.warning("❌ Bed monitor not initialized")
            return {"message": "Bed monitor not initialized", "beds": []}

        logger.info(f"🔍 Debug: bed_monitor.is_monitoring: {bed_monitor.is_monitoring}")
        bed_summary = await bed_monitor.get_bed_summary()
        logger.info(f"🔍 Debug: bed_summary: {bed_summary}")

        return {
            "status": "active" if bed_monitor.is_monitoring else "inactive",
            "summary": bed_summary,
            "metrics": bed_monitor.get_monitoring_metrics(),
            "last_update": bed_monitor.last_update.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting real-time bed status: {e}")
        return {"error": str(e)}

@app.get("/api/beds/real-time/changes")
async def get_bed_changes(limit: int = 50):
    """Get recent bed status changes"""
    if not get_bed_monitor:
        return {"message": "Real-time bed monitoring not available", "changes": []}

    try:
        bed_monitor = get_bed_monitor()
        if not bed_monitor:
            return {"message": "Bed monitor not initialized", "changes": []}

        changes = bed_monitor.get_change_history(limit)
        return {
            "changes": changes,
            "total": len(changes),
            "monitoring_active": bed_monitor.is_monitoring
        }
    except Exception as e:
        logger.error(f"Error getting bed changes: {e}")
        return {"error": str(e)}

@app.post("/api/beds/real-time/force-update")
async def force_bed_update():
    """Force an immediate bed status update"""
    if not get_bed_monitor:
        return {"message": "Real-time bed monitoring not available"}

    try:
        bed_monitor = get_bed_monitor()
        if not bed_monitor:
            return {"message": "Bed monitor not initialized"}

        changes = await bed_monitor.force_update()
        return {
            "message": "Forced update completed",
            "changes_detected": len(changes),
            "changes": changes
        }
    except Exception as e:
        logger.error(f"Error forcing bed update: {e}")
        return {"error": str(e)}

@app.get("/api/beds/real-time/metrics")
async def get_bed_monitoring_metrics():
    """Get bed monitoring performance metrics"""
    if not get_bed_monitor:
        return {"message": "Real-time bed monitoring not available"}

    try:
        bed_monitor = get_bed_monitor()
        if not bed_monitor:
            return {"message": "Bed monitor not initialized"}

        return bed_monitor.get_monitoring_metrics()
    except Exception as e:
        logger.error(f"Error getting bed monitoring metrics: {e}")
        return {"error": str(e)}

@app.get("/api/beds/predicted-occupancy")
async def get_predicted_occupancy():
    """Get predicted occupancy curve and risk days for the next 24 hours"""
    try:
        # Try multiple sources for predictions
        predictions = None

        if get_bed_monitor:
            try:
                bed_monitor = get_bed_monitor()
                if bed_monitor:
                    predictions = {
                        "predicted_occupancy_curve": bed_monitor.get_predicted_occupancy_curve(),
                        "risk_days": bed_monitor.get_risk_days()
                    }
            except:
                pass

        # Fallback to autonomous predictions
        if not predictions and autonomous_bed_agent:
            try:
                autonomous_predictions = autonomous_bed_agent.get_current_predictions()
                if autonomous_predictions:
                    predictions = {
                        "predicted_occupancy_curve": autonomous_predictions,
                        "risk_days": [p for p in autonomous_predictions if p.get("risk_level") == "high"]
                    }
            except:
                pass

        # Generate mock predictions if nothing available
        if not predictions:
            from datetime import datetime, timedelta
            import random

            current_time = datetime.now()
            mock_curve = []
            risk_days = []

            for i in range(24):
                hour_time = current_time + timedelta(hours=i)
                base_occupancy = 55.6
                variation = random.uniform(-10, 15)
                predicted_occupancy = max(30, min(95, base_occupancy + variation))

                point = {
                    "hour": i,
                    "timestamp": hour_time.isoformat(),
                    "predicted_occupancy": round(predicted_occupancy, 1),
                    "confidence": random.uniform(0.7, 0.95)
                }

                mock_curve.append(point)

                if predicted_occupancy > 85:
                    risk_days.append({
                        "day": hour_time.strftime("%Y-%m-%d"),
                        "hour": i,
                        "risk_level": "high",
                        "predicted_occupancy": round(predicted_occupancy, 1)
                    })

            predictions = {
                "predicted_occupancy_curve": mock_curve,
                "risk_days": risk_days
            }

        return predictions

    except Exception as e:
        logger.error(f"Error getting predicted occupancy: {e}")
        return {"error": str(e)}

# Discharge Process API Endpoints
@app.post("/api/beds/{bed_number}/discharge")
async def discharge_patient(bed_number: str, db: Session = Depends(get_db)):
    """Discharge patient from bed"""
    try:
        # Find the bed
        bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
        if not bed:
            raise HTTPException(status_code=404, detail=f"Bed {bed_number} not found")

        if bed.status != "occupied":
            raise HTTPException(status_code=400, detail=f"Bed {bed_number} is not occupied")

        if not bed.patient_id:
            raise HTTPException(status_code=400, detail=f"No patient assigned to bed {bed_number}")

        # Get patient info for logging
        patient = db.query(Patient).filter(Patient.id == bed.patient_id).first()
        patient_name = patient.name if patient else "Unknown"

        # Create discharge record in bed occupancy history
        discharge_record = BedOccupancyHistory(
            bed_id=bed.id,
            patient_id=bed.patient_id,
            start_time=bed.last_updated or datetime.now(),
            end_time=datetime.now(),
            status="discharged",
            discharge_reason="normal_discharge"
        )
        db.add(discharge_record)

        # Update bed status
        old_patient_id = bed.patient_id
        bed.patient_id = None
        bed.status = "cleaning"  # Bed needs cleaning after discharge
        bed.last_updated = datetime.now()

        # Log the discharge action
        agent_log = AgentLog(
            agent_name="discharge_system",
            action="patient_discharge",
            details=f"Patient {patient_name} (ID: {old_patient_id}) discharged from bed {bed_number}",
            status="success",
            related_bed_id=bed.id,
            related_patient_id=old_patient_id
        )
        db.add(agent_log)

        db.commit()

        # Force real-time update
        if get_bed_monitor:
            bed_monitor = get_bed_monitor()
            if bed_monitor:
                await bed_monitor.force_update()

        logger.info(f"✅ Patient {patient_name} discharged from bed {bed_number}")

        return {
            "message": f"Patient successfully discharged from bed {bed_number}",
            "bed_number": bed_number,
            "patient_name": patient_name,
            "patient_id": old_patient_id,
            "discharge_time": datetime.now().isoformat(),
            "bed_status": "cleaning"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discharging patient from bed {bed_number}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to discharge patient: {str(e)}")

@app.post("/api/beds/{bed_number}/complete-cleaning")
async def complete_bed_cleaning(bed_number: str, db: Session = Depends(get_db)):
    """Mark bed cleaning as complete"""
    try:
        # Find the bed
        bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
        if not bed:
            raise HTTPException(status_code=404, detail=f"Bed {bed_number} not found")

        if bed.status != "cleaning":
            raise HTTPException(status_code=400, detail=f"Bed {bed_number} is not in cleaning status")

        # Update bed status to vacant
        bed.status = "vacant"
        bed.last_updated = datetime.now()

        # Log the cleaning completion
        agent_log = AgentLog(
            agent_name="housekeeping_system",
            action="cleaning_completed",
            details=f"Cleaning completed for bed {bed_number} - now available",
            status="success",
            related_bed_id=bed.id
        )
        db.add(agent_log)

        db.commit()

        # Force real-time update
        if get_bed_monitor:
            bed_monitor = get_bed_monitor()
            if bed_monitor:
                await bed_monitor.force_update()

        logger.info(f"✅ Cleaning completed for bed {bed_number}")

        return {
            "message": f"Cleaning completed for bed {bed_number}",
            "bed_number": bed_number,
            "bed_status": "vacant",
            "completion_time": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing cleaning for bed {bed_number}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete cleaning: {str(e)}")

@app.get("/api/beds/{bed_number}/discharge-info")
async def get_discharge_info(bed_number: str, db: Session = Depends(get_db)):
    """Get discharge information for a bed"""
    try:
        # Find the bed with patient info
        bed = db.query(Bed).filter(Bed.bed_number == bed_number).first()
        if not bed:
            raise HTTPException(status_code=404, detail=f"Bed {bed_number} not found")

        if bed.status != "occupied" or not bed.patient_id:
            return {
                "can_discharge": False,
                "message": "Bed is not occupied or no patient assigned"
            }

        # Get patient information
        patient = db.query(Patient).filter(Patient.id == bed.patient_id).first()
        if not patient:
            return {
                "can_discharge": False,
                "message": "Patient information not found"
            }

        # Calculate length of stay
        admission_time = bed.last_updated or datetime.now()
        length_of_stay = datetime.now() - admission_time

        return {
            "can_discharge": True,
            "bed_number": bed_number,
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "condition": patient.primary_condition,
                "admission_time": admission_time.isoformat(),
                "length_of_stay_hours": round(length_of_stay.total_seconds() / 3600, 1)
            },
            "bed": {
                "ward": bed.ward,
                "room_number": bed.room_number,
                "bed_type": bed.bed_type
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discharge info for bed {bed_number}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get discharge info: {str(e)}")


# Autonomous Systems API Endpoints

@app.get("/api/autonomous/status")
async def get_autonomous_status():
    """Get status of all autonomous systems"""
    try:
        # Get system status with safe attribute checking
        def safe_get_attr(obj, attr, default=False):
            try:
                return getattr(obj, attr, default) if obj else default
            except:
                return default

        def safe_call_method(obj, method_name, default={}):
            try:
                if obj and hasattr(obj, method_name):
                    method = getattr(obj, method_name)
                    return method() if callable(method) else default
                return default
            except:
                return default

        status = {
            "autonomous_scheduler": {
                "available": autonomous_scheduler is not None,
                "running": safe_get_attr(autonomous_scheduler, 'running', False),
                "metrics": safe_call_method(autonomous_scheduler, 'get_performance_metrics', {}),
                "task_status": safe_call_method(autonomous_scheduler, 'get_task_status', {})
            },
            "autonomous_bed_agent": {
                "available": autonomous_bed_agent is not None,
                "running": safe_get_attr(autonomous_bed_agent, 'running', False),
                "metrics": safe_call_method(autonomous_bed_agent, 'get_performance_metrics', {}),
                "action_queue": safe_call_method(autonomous_bed_agent, 'get_action_queue_status', {})
            },
            "intelligent_bed_assignment": {
                "available": intelligent_bed_assignment is not None,
                "running": True if intelligent_bed_assignment else False,  # Always running if available
                "metrics": safe_call_method(intelligent_bed_assignment, 'get_assignment_metrics', {}),
                "queue_status": safe_call_method(intelligent_bed_assignment, 'get_assignment_queue_status', {})
            },
            "proactive_action_system": {
                "available": proactive_action_system is not None,
                "running": safe_get_attr(proactive_action_system, 'running', False),
                "metrics": safe_call_method(proactive_action_system, 'get_performance_metrics', {}),
                "action_queue": safe_call_method(proactive_action_system, 'get_action_queue_status', {})
            },
            "predictive_analytics": {
                "available": predictive_analytics is not None,
                "running": True if predictive_analytics else False,  # Always running if available
                "model_performance": safe_call_method(predictive_analytics, 'get_model_performance', {})
            },
            "alert_system": {
                "available": alert_system is not None,
                "running": safe_get_attr(alert_system, 'running', False),
                "active_alerts": len(safe_call_method(alert_system, 'get_active_alerts', []))
            }
        }

        return status

    except Exception as e:
        logger.error(f"Error getting autonomous status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/autonomous/predictions")
async def get_bed_predictions():
    """Get 24-hour bed occupancy predictions"""
    try:
        # Try multiple sources for predictions
        predictions = None

        if autonomous_bed_agent:
            try:
                predictions = autonomous_bed_agent.get_current_predictions()
            except:
                pass

        if not predictions and predictive_analytics:
            try:
                predictions = predictive_analytics.get_24_hour_predictions()
            except:
                pass

        # Generate mock predictions if no real ones available
        if not predictions:
            from datetime import datetime, timedelta
            import random

            current_time = datetime.now()
            mock_predictions = []

            for i in range(24):
                hour_time = current_time + timedelta(hours=i)
                # Generate realistic occupancy predictions
                base_occupancy = 55.6  # Current occupancy
                variation = random.uniform(-10, 15)  # Some variation
                predicted_occupancy = max(30, min(95, base_occupancy + variation))

                mock_predictions.append({
                    "hour": i,
                    "timestamp": hour_time.isoformat(),
                    "predicted_occupancy": round(predicted_occupancy, 1),
                    "confidence": random.uniform(0.7, 0.95),
                    "risk_level": "high" if predicted_occupancy > 85 else "medium" if predicted_occupancy > 70 else "low"
                })

            predictions = mock_predictions

        return {
            "predictions": predictions,
            "generated_at": datetime.now().isoformat(),
            "prediction_window_hours": 24,
            "source": "autonomous_bed_agent" if autonomous_bed_agent else "predictive_analytics" if predictive_analytics else "mock_data"
        }

    except Exception as e:
        logger.error(f"Error getting bed predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/autonomous/actions/history")
async def get_autonomous_actions_history(limit: int = 20):
    """Get history of autonomous actions"""
    try:
        history = {
            "autonomous_agent_actions": autonomous_bed_agent.get_decision_history() if autonomous_bed_agent else [],
            "bed_assignments": intelligent_bed_assignment.get_assignment_history(limit) if intelligent_bed_assignment else [],
            "proactive_actions": proactive_action_system.get_action_history(limit) if proactive_action_system else [],
            "scheduler_tasks": autonomous_scheduler.get_task_history(limit) if autonomous_scheduler else []
        }

        return history

    except Exception as e:
        logger.error(f"Error getting autonomous actions history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/bed-assignment/request")
async def request_autonomous_bed_assignment(
    patient_id: str,
    priority: str = "medium",
    medical_requirements: dict = None,
    preferences: dict = None
):
    """Request autonomous bed assignment for a patient"""
    try:
        if not intelligent_bed_assignment:
            raise HTTPException(status_code=503, detail="Intelligent bed assignment not available")

        # Convert priority string to enum
        priority_map = {
            "emergency": intelligent_bed_assignment.AssignmentPriority.EMERGENCY,
            "urgent": intelligent_bed_assignment.AssignmentPriority.URGENT,
            "high": intelligent_bed_assignment.AssignmentPriority.HIGH,
            "medium": intelligent_bed_assignment.AssignmentPriority.MEDIUM,
            "low": intelligent_bed_assignment.AssignmentPriority.LOW
        }

        assignment_priority = priority_map.get(priority.lower(), intelligent_bed_assignment.AssignmentPriority.MEDIUM)

        request_id = await intelligent_bed_assignment.request_bed_assignment(
            patient_id=patient_id,
            priority=assignment_priority,
            medical_requirements=medical_requirements or {},
            preferences=preferences or {}
        )

        return {
            "request_id": request_id,
            "patient_id": patient_id,
            "priority": priority,
            "status": "queued",
            "message": "Bed assignment request queued for processing"
        }

    except Exception as e:
        logger.error(f"Error requesting bed assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/autonomous/bed-recommendations/{patient_id}")
async def get_bed_recommendations(patient_id: str, top_n: int = 5):
    """Get bed recommendations for a patient"""
    try:
        if not intelligent_bed_assignment:
            raise HTTPException(status_code=503, detail="Intelligent bed assignment not available")

        recommendations = await intelligent_bed_assignment.get_bed_recommendations(patient_id, top_n)

        return {
            "patient_id": patient_id,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting bed recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/autonomous/system-health")
async def get_autonomous_system_health():
    """Get comprehensive autonomous system health status"""
    try:
        health_status = {}

        if autonomous_scheduler:
            health_status = await autonomous_scheduler.get_system_health()
        else:
            health_status = {
                "status": "unavailable",
                "message": "Autonomous scheduler not available",
                "timestamp": datetime.now().isoformat()
            }

        return health_status

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/actions/approve/{action_id}")
async def approve_autonomous_action(action_id: str):
    """Approve a pending autonomous action"""
    try:
        if not proactive_action_system:
            raise HTTPException(status_code=503, detail="Proactive action system not available")

        success = await proactive_action_system.approve_action(action_id)

        if success:
            return {"message": f"Action {action_id} approved", "status": "approved"}
        else:
            raise HTTPException(status_code=404, detail="Action not found or cannot be approved")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous/actions/cancel/{action_id}")
async def cancel_autonomous_action(action_id: str):
    """Cancel a pending autonomous action"""
    try:
        if not proactive_action_system:
            raise HTTPException(status_code=503, detail="Proactive action system not available")

        success = await proactive_action_system.cancel_action(action_id)

        if success:
            return {"message": f"Action {action_id} cancelled", "status": "cancelled"}
        else:
            raise HTTPException(status_code=404, detail="Action not found or cannot be cancelled")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/frontend-test")
async def frontend_test():
    """Simple endpoint to test frontend connectivity"""
    from datetime import datetime
    return {
        "status": "success",
        "message": "Frontend can reach backend",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True,
        "test_alerts": [
            {
                "id": "frontend_test_alert",
                "priority": "high",
                "title": "Frontend Test Alert",
                "message": "This alert confirms frontend-backend connectivity",
                "department": "System",
                "created_at": datetime.now().isoformat()
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
