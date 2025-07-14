from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .database import get_db, Bed, Patient, BedOccupancyHistory

router = APIRouter()

# Get all beds (with optional filters)
@router.get("/beds", response_model=List[dict])
def get_beds(status: Optional[str] = None, ward: Optional[str] = None, bed_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Bed)
    if status:
        query = query.filter(Bed.status == status)
    if ward:
        query = query.filter(Bed.ward == ward)
    if bed_type:
        query = query.filter(Bed.bed_type == bed_type)
    beds = query.all()
    return [bed.__dict__ for bed in beds]

# Get bed by ID
@router.get("/beds/{bed_id}", response_model=dict)
def get_bed(bed_id: int, db: Session = Depends(get_db)):
    bed = db.query(Bed).get(bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return bed.__dict__

# Assign patient to bed
@router.post("/beds/{bed_id}/assign", response_model=dict)
def assign_patient(bed_id: int, patient_id: str, db: Session = Depends(get_db)):
    bed = db.query(Bed).get(bed_id)
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not bed or not patient:
        raise HTTPException(status_code=404, detail="Bed or patient not found")
    if bed.status != "vacant":
        raise HTTPException(status_code=400, detail="Bed is not vacant")
    bed.status = "occupied"
    bed.admission_time = datetime.now()
    bed.expected_discharge = patient.expected_discharge_date
    patient.current_bed_id = bed.id
    db.add(bed)
    db.add(patient)
    db.commit()
    db.refresh(bed)
    db.refresh(patient)
    # Log occupancy history
    history = BedOccupancyHistory(
        bed_id=bed.id,
        patient_id=patient.patient_id,
        status="occupied",
        reason="admission",
        start_time=datetime.now(),
        created_at=datetime.now()
    )
    db.add(history)
    db.commit()
    return bed.__dict__

# Discharge patient from bed
@router.post("/beds/{bed_id}/discharge", response_model=dict)
def discharge_patient(bed_id: int, db: Session = Depends(get_db)):
    bed = db.query(Bed).get(bed_id)
    if not bed or bed.status != "occupied":
        raise HTTPException(status_code=404, detail="Bed not occupied or not found")
    patient = db.query(Patient).filter(Patient.current_bed_id == bed.id).first()
    if patient:
        patient.current_bed_id = None
        patient.status = "discharged"
        db.add(patient)
    # Update bed status
    bed.status = "vacant"
    bed.admission_time = None
    bed.expected_discharge = None
    db.add(bed)
    db.commit()
    db.refresh(bed)
    # Update occupancy history
    history = db.query(BedOccupancyHistory).filter(BedOccupancyHistory.bed_id == bed.id, BedOccupancyHistory.end_time == None).first()
    if history:
        history.end_time = datetime.now()
        history.duration_hours = (history.end_time - history.start_time).total_seconds() / 3600.0
        history.reason = "discharge"
        db.add(history)
        db.commit()
    return bed.__dict__

# Mark bed for cleaning/maintenance
@router.post("/beds/{bed_id}/clean", response_model=dict)
def mark_bed_cleaning(bed_id: int, db: Session = Depends(get_db)):
    bed = db.query(Bed).get(bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    bed.status = "cleaning"
    bed.is_cleaning_required = True
    db.add(bed)
    db.commit()
    db.refresh(bed)
    # Log occupancy history
    history = BedOccupancyHistory(
        bed_id=bed.id,
        status="cleaning",
        reason="cleaning",
        start_time=datetime.now(),
        created_at=datetime.now()
    )
    db.add(history)
    db.commit()
    return bed.__dict__

# Get bed occupancy history
@router.get("/beds/{bed_id}/history", response_model=List[dict])
def get_bed_history(bed_id: int, db: Session = Depends(get_db)):
    history = db.query(BedOccupancyHistory).filter(BedOccupancyHistory.bed_id == bed_id).order_by(BedOccupancyHistory.start_time.desc()).all()
    return [h.__dict__ for h in history]
