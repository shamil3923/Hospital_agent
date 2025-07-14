"""
Initialize sample data for Hospital Agent Platform
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from backend.database import SessionLocal, create_tables, Bed, Patient, BedOccupancyHistory, AgentLog


def create_sample_beds(db: Session):
    """Create sample bed data"""
    beds_data = [
        # ICU Beds
        {"bed_number": "ICU-001", "room_number": "101", "ward": "ICU", "bed_type": "ICU", "status": "occupied"},
        {"bed_number": "ICU-002", "room_number": "102", "ward": "ICU", "bed_type": "ICU", "status": "occupied"},
        {"bed_number": "ICU-003", "room_number": "103", "ward": "ICU", "bed_type": "ICU", "status": "vacant"},
        {"bed_number": "ICU-004", "room_number": "104", "ward": "ICU", "bed_type": "ICU", "status": "cleaning"},
        {"bed_number": "ICU-005", "room_number": "105", "ward": "ICU", "bed_type": "ICU", "status": "occupied"},
        
        # General Ward Beds
        {"bed_number": "GEN-001", "room_number": "201", "ward": "General", "bed_type": "General", "status": "occupied"},
        {"bed_number": "GEN-002", "room_number": "202", "ward": "General", "bed_type": "General", "status": "occupied"},
        {"bed_number": "GEN-003", "room_number": "203", "ward": "General", "bed_type": "General", "status": "vacant"},
        {"bed_number": "GEN-004", "room_number": "204", "ward": "General", "bed_type": "General", "status": "occupied"},
        {"bed_number": "GEN-005", "room_number": "205", "ward": "General", "bed_type": "General", "status": "vacant"},
        {"bed_number": "GEN-006", "room_number": "206", "ward": "General", "bed_type": "General", "status": "cleaning"},
        {"bed_number": "GEN-007", "room_number": "207", "ward": "General", "bed_type": "General", "status": "occupied"},
        {"bed_number": "GEN-008", "room_number": "208", "ward": "General", "bed_type": "General", "status": "occupied"},
        
        # Emergency Beds
        {"bed_number": "ER-001", "room_number": "301", "ward": "Emergency", "bed_type": "Emergency", "status": "occupied"},
        {"bed_number": "ER-002", "room_number": "302", "ward": "Emergency", "bed_type": "Emergency", "status": "vacant"},
        {"bed_number": "ER-003", "room_number": "303", "ward": "Emergency", "bed_type": "Emergency", "status": "occupied"},
        {"bed_number": "ER-004", "room_number": "304", "ward": "Emergency", "bed_type": "Emergency", "status": "vacant"},
    ]
    
    for bed_data in beds_data:
        bed = Bed(**bed_data)
        if bed_data["status"] == "occupied":
            bed.admission_time = datetime.now() - timedelta(hours=random.randint(1, 72))
            bed.expected_discharge = datetime.now() + timedelta(hours=random.randint(12, 120))
        db.add(bed)
    
    print(f"Created {len(beds_data)} beds")


def create_sample_patients(db: Session):
    """Create sample patient data"""
    patients_data = [
        {"patient_id": "P001", "name": "John Doe", "age": 65, "gender": "Male", "condition": "Heart Attack", "severity": "critical"},
        {"patient_id": "P002", "name": "Jane Smith", "age": 45, "gender": "Female", "condition": "Pneumonia", "severity": "serious"},
        {"patient_id": "P003", "name": "Bob Johnson", "age": 30, "gender": "Male", "condition": "Broken Leg", "severity": "stable"},
        {"patient_id": "P004", "name": "Alice Brown", "age": 55, "gender": "Female", "condition": "Chest Pain", "severity": "serious"},
        {"patient_id": "P005", "name": "Charlie Wilson", "age": 70, "gender": "Male", "condition": "Stroke", "severity": "critical"},
        {"patient_id": "P006", "name": "Diana Davis", "age": 35, "gender": "Female", "condition": "Appendicitis", "severity": "stable"},
        {"patient_id": "P007", "name": "Edward Miller", "age": 50, "gender": "Male", "condition": "Car Accident", "severity": "serious"},
        {"patient_id": "P008", "name": "Fiona Garcia", "age": 28, "gender": "Female", "condition": "Food Poisoning", "severity": "stable"},
    ]
    
    # Get occupied beds
    occupied_beds = db.query(Bed).filter(Bed.status == "occupied").all()
    
    for i, patient_data in enumerate(patients_data):
        if i < len(occupied_beds):
            patient_data["current_bed_id"] = occupied_beds[i].id
            patient_data["admission_date"] = occupied_beds[i].admission_time or datetime.now()
            patient_data["expected_discharge_date"] = occupied_beds[i].expected_discharge
            patient_data["status"] = "admitted"
            
            # Update bed with patient ID
            occupied_beds[i].patient_id = patient_data["patient_id"]
        else:
            patient_data["admission_date"] = datetime.now() - timedelta(days=random.randint(1, 30))
            patient_data["status"] = "discharged"
        
        patient = Patient(**patient_data)
        db.add(patient)
    
    print(f"Created {len(patients_data)} patients")


def create_sample_history(db: Session):
    """Create sample bed occupancy history"""
    beds = db.query(Bed).all()
    
    for bed in beds:
        # Create 5-10 historical records per bed
        for i in range(random.randint(5, 10)):
            start_time = datetime.now() - timedelta(days=random.randint(1, 30))
            duration = random.randint(12, 168)  # 12 hours to 7 days
            end_time = start_time + timedelta(hours=duration)
            
            history = BedOccupancyHistory(
                bed_id=bed.id,
                patient_id=f"P{random.randint(100, 999)}",
                status=random.choice(["occupied", "vacant", "cleaning"]),
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration
            )
            db.add(history)
    
    print("Created sample bed occupancy history")


def create_sample_logs(db: Session):
    """Create sample agent logs"""
    log_entries = [
        {"agent_name": "bed_management_agent", "action": "bed_status_check", "details": "Routine bed occupancy check", "status": "success"},
        {"agent_name": "bed_management_agent", "action": "alert_generation", "details": "High occupancy alert generated", "status": "success"},
        {"agent_name": "bed_management_agent", "action": "discharge_prediction", "details": "Predicted 3 discharges in next 24 hours", "status": "success"},
        {"agent_name": "bed_management_agent", "action": "bed_assignment", "details": "Assigned bed ICU-003 to patient P009", "status": "success"},
        {"agent_name": "bed_management_agent", "action": "capacity_analysis", "details": "ICU capacity at 80%", "status": "warning"},
    ]
    
    for log_data in log_entries:
        log_data["timestamp"] = datetime.now() - timedelta(minutes=random.randint(1, 1440))
        log = AgentLog(**log_data)
        db.add(log)
    
    print(f"Created {len(log_entries)} agent log entries")


def main():
    """Initialize all sample data"""
    print("Initializing Hospital Agent Platform data...")
    
    # Create tables
    create_tables()
    print("Database tables created")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Bed).count() > 0:
            print("Data already exists. Skipping initialization.")
            return
        
        # Create sample data
        create_sample_beds(db)
        create_sample_patients(db)
        create_sample_history(db)
        create_sample_logs(db)
        
        # Commit all changes
        db.commit()
        print("Sample data initialization completed successfully!")
        
        # Print summary
        print("\nData Summary:")
        print(f"- Beds: {db.query(Bed).count()}")
        print(f"- Patients: {db.query(Patient).count()}")
        print(f"- History Records: {db.query(BedOccupancyHistory).count()}")
        print(f"- Agent Logs: {db.query(AgentLog).count()}")
        
    except Exception as e:
        print(f"Error initializing data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
