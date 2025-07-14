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
    from .database import get_db, create_tables, Bed, Patient, BedOccupancyHistory, AgentLog
    from .schemas import BedResponse, PatientResponse, DashboardMetrics, ChatRequest, ChatResponse
except ImportError:
    from config import settings
    from database import get_db, create_tables, Bed, Patient, BedOccupancyHistory, AgentLog
    from schemas import BedResponse, PatientResponse, DashboardMetrics, ChatRequest, ChatResponse

# Configure logging first
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Import real-time systems (after logger is defined)
try:
    from alert_system import alert_system
    from websocket_manager import websocket_manager, real_time_updater
    from workflow_engine import workflow_engine
    from admission_system import admission_system, AdmissionRequest, AdmissionType, AdmissionPriority
    from clinical_decision_support import clinical_decision_support
    logger.info("✅ Real-time systems imported successfully")
except ImportError as e:
    # Fallback if real-time systems not available
    logger.warning(f"⚠️ Real-time systems not available: {e}")
    alert_system = None
    websocket_manager = None
    real_time_updater = None
    workflow_engine = None
    admission_system = None
    clinical_decision_support = None

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

        # Start real-time systems if available
        if alert_system and websocket_manager and real_time_updater:
            try:
                # Start alert monitoring
                await alert_system.start_monitoring()

                # Start real-time updates
                await real_time_updater.start_updates()

                # Subscribe alert system to websocket manager
                alert_system.subscribe_to_alerts(websocket_manager.send_alert_update)

                logger.info("🚨 Real-time alert system started")
                logger.info("🔄 Real-time updates started")
            except Exception as e:
                logger.error(f"Failed to start real-time systems: {e}")

        # Start workflow engine
        if workflow_engine:
            try:
                await workflow_engine.start_engine()
                logger.info("⚙️ Workflow engine started")
            except Exception as e:
                logger.error(f"Failed to start workflow engine: {e}")

        # Start admission system
        if admission_system:
            try:
                await admission_system.start_system()
                logger.info("🏥 Admission system started")
            except Exception as e:
                logger.error(f"Failed to start admission system: {e}")

        # Start clinical decision support
        if clinical_decision_support:
            try:
                await clinical_decision_support.start_system()
                logger.info("🧠 Clinical decision support started")
            except Exception as e:
                logger.error(f"Failed to start clinical decision support: {e}")

        logger.info("🏥 Hospital Agent Platform started successfully!")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Continue anyway - database might already exist

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
                medical_conditions=request.get('primary_condition', ''),
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
        bed = db.query(Bed).filter(Bed.bed_id == bed_id).first()
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
        patient.bed_id = bed_id
        patient.status = "admitted"
        patient.admission_date = datetime.now()

        # Create occupancy history record
        occupancy_record = BedOccupancyHistory(
            bed_id=bed_id,
            patient_id=patient_id,
            admission_date=datetime.now(),
            status="admitted"
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
    """Chat with the bed management agent"""
    try:
        # Import MCP-powered agent for intelligent responses
        try:
            from agents.bed_management.mcp_agent import MCPBedManagementAgent
            agent = MCPBedManagementAgent(use_mcp=True)
            result = agent.process_query(request.message)
        except ImportError:
            # Fallback to regular agent
            try:
                from agents.bed_management.agent import BedManagementAgent
                agent = BedManagementAgent()
                result = agent.process_query(request.message)
            except ImportError:
                # Final fallback
                result = {
                    "response": f"I received your message: '{request.message}'. The bed management system is currently being set up.",
                    "timestamp": datetime.now().isoformat(),
                    "agent": "fallback_agent"
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

# Admission Management
@app.post("/api/admissions/submit")
async def submit_admission_request(request_data: dict):
    """Submit a new admission request"""
    if not admission_system:
        raise HTTPException(status_code=503, detail="Admission system not available")

    try:
        # Convert dict to AdmissionRequest
        admission_request = AdmissionRequest(
            patient_id=request_data["patient_id"],
            patient_name=request_data["patient_name"],
            age=request_data["age"],
            gender=request_data["gender"],
            admission_type=AdmissionType(request_data["admission_type"]),
            priority=AdmissionPriority(request_data["priority"]),
            primary_condition=request_data["primary_condition"],
            secondary_conditions=request_data.get("secondary_conditions", []),
            allergies=request_data.get("allergies", []),
            medications=request_data.get("medications", []),
            attending_physician=request_data["attending_physician"],
            requested_ward=request_data.get("requested_ward"),
            insurance_id=request_data.get("insurance_id"),
            emergency_contact=request_data.get("emergency_contact"),
            special_needs=request_data.get("special_needs", []),
            estimated_los=request_data.get("estimated_los")
        )

        request_id = await admission_system.submit_admission_request(admission_request)
        return {"request_id": request_id, "status": "submitted"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

# Real-time API endpoints
@app.get("/api/alerts/active")
async def get_active_alerts():
    """Get all active real-time alerts"""
    if not alert_system:
        return {"alerts": [], "message": "Real-time alerts not available"}

    return {"alerts": alert_system.get_active_alerts()}

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
