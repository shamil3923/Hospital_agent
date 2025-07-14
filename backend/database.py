"""
Database configuration and models for Hospital Agent Platform
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Generator

try:
    from .config import settings
except ImportError:
    from config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class Bed(Base):
    """Enhanced bed model for tracking hospital beds"""
    __tablename__ = "beds"

    id = Column(Integer, primary_key=True, index=True)
    bed_number = Column(String, unique=True, index=True, nullable=False)
    room_number = Column(String, nullable=False)
    ward = Column(String, nullable=False)
    bed_type = Column(String, nullable=False)  # ICU, General, Emergency, Pediatric, Maternity
    status = Column(String, nullable=False)  # occupied, vacant, cleaning, maintenance, reserved
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=True)
    floor_number = Column(Integer, nullable=False, default=1)
    wing = Column(String, nullable=True)  # North, South, East, West
    equipment = Column(Text, nullable=True)  # JSON string of available equipment
    isolation_required = Column(Boolean, default=False)
    private_room = Column(Boolean, default=False)
    daily_rate = Column(Float, nullable=True)  # cost per day
    last_cleaned = Column(DateTime, nullable=True)
    maintenance_notes = Column(Text, nullable=True)
    admission_time = Column(DateTime, nullable=True)
    expected_discharge = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Enhanced Relationships
    current_patient = relationship("Patient", foreign_keys=[patient_id], backref="current_bed")


class Patient(Base):
    """Enhanced patient model for tracking patient information"""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    emergency_contact = Column(String, nullable=True)
    emergency_phone = Column(String, nullable=True)
    insurance_id = Column(String, nullable=True)
    primary_condition = Column(String, nullable=False)
    secondary_conditions = Column(Text, nullable=True)  # JSON array of conditions
    allergies = Column(Text, nullable=True)  # JSON array of allergies
    medications = Column(Text, nullable=True)  # JSON array of current medications
    severity = Column(String, nullable=False)  # critical, serious, stable, improving
    admission_date = Column(DateTime, nullable=False)
    expected_discharge_date = Column(DateTime, nullable=True)
    actual_discharge_date = Column(DateTime, nullable=True)
    discharge_reason = Column(String, nullable=True)  # recovered, transferred, deceased
    attending_physician = Column(String, nullable=True)
    assigned_nurse = Column(String, nullable=True)
    diet_restrictions = Column(Text, nullable=True)
    mobility_status = Column(String, nullable=True)  # ambulatory, wheelchair, bedbound
    isolation_required = Column(Boolean, default=False)
    dnr_status = Column(Boolean, default=False)  # Do Not Resuscitate
    current_bed_id = Column(Integer, nullable=True)  # Will be linked via relationship
    status = Column(String, nullable=False)  # admitted, discharged, transferred, deceased
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BedOccupancyHistory(Base):
    """Historical bed occupancy data"""
    __tablename__ = "bed_occupancy_history"

    id = Column(Integer, primary_key=True, index=True)
    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=True)
    status = Column(String, nullable=False)
    reason = Column(String, nullable=True)  # reason for status change
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_hours = Column(Float, nullable=True)
    assigned_by = Column(String, nullable=True)  # staff member who assigned
    discharge_reason = Column(String, nullable=True)  # reason for discharge
    transfer_to_bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)  # if transferred
    created_at = Column(DateTime, default=func.now())

    # Enhanced Relationships
    bed = relationship("Bed", foreign_keys=[bed_id], backref="occupancy_history")
    patient = relationship("Patient", backref="bed_history")
    transfer_to_bed = relationship("Bed", foreign_keys=[transfer_to_bed_id], backref="transfer_history")


class AgentLog(Base):
    """Agent activity logging"""
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String, nullable=False)  # success, error, warning
    user_query = Column(Text, nullable=True)  # original user query
    response = Column(Text, nullable=True)  # agent response
    tools_used = Column(String, nullable=True)  # comma-separated tool names
    execution_time_ms = Column(Float, nullable=True)  # response time
    related_bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)
    related_patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=True)
    session_id = Column(String, nullable=True)  # user session tracking
    timestamp = Column(DateTime, default=func.now())

    # Enhanced Relationships
    related_bed = relationship("Bed", backref="agent_logs")
    related_patient = relationship("Patient", backref="agent_logs")


class Department(Base):
    """Hospital departments/wards"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # ICU, Emergency, General, etc.
    description = Column(Text, nullable=True)
    floor_number = Column(Integer, nullable=False)
    wing = Column(String, nullable=True)
    head_of_department = Column(String, nullable=True)
    contact_extension = Column(String, nullable=True)
    total_beds = Column(Integer, nullable=False, default=0)
    available_beds = Column(Integer, nullable=False, default=0)
    specialization = Column(String, nullable=True)  # cardiology, neurology, etc.
    equipment_available = Column(Text, nullable=True)  # JSON array
    operating_hours = Column(String, nullable=True)  # 24/7, business hours, etc.
    emergency_contact = Column(String, nullable=True)
    budget_allocated = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Staff(Base):
    """Hospital staff members"""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # doctor, nurse, technician, admin
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    specialization = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    shift_schedule = Column(String, nullable=True)  # day, night, rotating
    hire_date = Column(DateTime, nullable=True)
    license_number = Column(String, nullable=True)
    certifications = Column(Text, nullable=True)  # JSON array
    status = Column(String, nullable=False, default="active")  # active, inactive, on_leave
    created_at = Column(DateTime, default=func.now())

    # Relationships
    department = relationship("Department", backref="staff_members")


class Equipment(Base):
    """Medical equipment tracking"""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False)  # ventilator, monitor, pump, etc.
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    current_location = Column(String, nullable=True)  # room, ward, storage
    assigned_bed_id = Column(Integer, ForeignKey("beds.id"), nullable=True)
    status = Column(String, nullable=False)  # available, in_use, maintenance, broken
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    warranty_expiry = Column(DateTime, nullable=True)
    cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    assigned_bed = relationship("Bed", backref="equipment_list")


# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
