"""
Pydantic schemas for Hospital Agent Platform
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class BedResponse(BaseModel):
    """Bed response schema"""
    id: int
    bed_number: str
    room_number: str
    ward: str
    bed_type: str
    status: str
    patient_id: Optional[str] = None
    admission_time: Optional[datetime] = None
    expected_discharge: Optional[datetime] = None
    last_updated: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientResponse(BaseModel):
    """Patient response schema"""
    id: int
    patient_id: str
    name: str
    age: int
    gender: str
    condition: str
    severity: str
    admission_date: datetime
    expected_discharge_date: Optional[datetime] = None
    current_bed_id: Optional[int] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    """Dashboard metrics schema"""
    bed_occupancy: float
    patient_satisfaction: float
    available_staff: int
    resource_utilization: float
    total_beds: int
    occupied_beds: int
    vacant_beds: int
    cleaning_beds: int


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str
    timestamp: datetime
    agent: str
    confidence: Optional[float] = None
    suggestions: Optional[List[str]] = None


class AgentLogResponse(BaseModel):
    """Agent log response schema"""
    id: int
    agent_name: str
    action: str
    details: Optional[str] = None
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
