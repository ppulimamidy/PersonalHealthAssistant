"""
Consultation models for Doctor Collaboration Service.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid

from common.models.base import Base


class ConsultationType(str, Enum):
    """Consultation type enumeration."""
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    ROUTINE = "routine"
    SPECIALIST = "specialist"
    SECOND_OPINION = "second_opinion"
    TELEMEDICINE = "telemedicine"
    IN_PERSON = "in_person"
    PHONE = "phone"
    VIDEO = "video"


class ConsultationStatus(str, Enum):
    """Consultation status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"
    PENDING_REVIEW = "pending_review"


class ConsultationPriority(str, Enum):
    """Consultation priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class Consultation(Base):
    """Consultation model for doctor-patient consultations."""
    
    __tablename__ = "consultations"
    __table_args__ = {'schema': 'doctor_collaboration', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Participants
    patient_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    
    # Consultation details
    consultation_type = Column(SQLEnum(ConsultationType), nullable=False)
    status = Column(SQLEnum(ConsultationStatus), default=ConsultationStatus.SCHEDULED, nullable=False)
    priority = Column(SQLEnum(ConsultationPriority), default=ConsultationPriority.NORMAL, nullable=False)
    
    # Scheduling
    scheduled_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    timezone = Column(String, default="UTC", nullable=False)
    
    # Location and modality
    location = Column(String, nullable=True)
    modality = Column(String, default="in_person", nullable=False)  # in_person, telemedicine, phone, video
    
    # Medical information
    chief_complaint = Column(Text, nullable=True)
    symptoms = Column(JSON, default=list)
    medical_history = Column(Text, nullable=True)
    current_medications = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    vital_signs = Column(JSON, default=dict)
    
    # Consultation notes
    subjective_notes = Column(Text, nullable=True)  # Patient's subjective complaints
    objective_notes = Column(Text, nullable=True)   # Doctor's objective observations
    assessment_notes = Column(Text, nullable=True)  # Doctor's assessment
    plan_notes = Column(Text, nullable=True)        # Treatment plan
    
    # Diagnosis and treatment
    diagnosis = Column(JSON, default=list)
    treatment_plan = Column(JSON, default=list)
    prescriptions = Column(JSON, default=list)
    referrals = Column(JSON, default=list)
    follow_up_plan = Column(Text, nullable=True)
    
    # Appointment reference
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.appointments.id"), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_consultations")
    doctor = relationship("User", foreign_keys=[doctor_id], backref="doctor_consultations")
    appointment = relationship("Appointment", back_populates="consultations")
    messages = relationship("Message", back_populates="consultation")
    
    def __repr__(self):
        return f"<Consultation(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, type={self.consultation_type})>"
    
    @property
    def is_active(self) -> bool:
        """Check if consultation is currently active."""
        return self.status == ConsultationStatus.IN_PROGRESS
    
    @property
    def is_completed(self) -> bool:
        """Check if consultation is completed."""
        return self.status == ConsultationStatus.COMPLETED
    
    @property
    def duration_actual(self) -> Optional[int]:
        """Get actual duration of consultation in minutes."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() / 60)
        return None
    
    @property
    def end_time(self) -> datetime:
        """Calculate consultation end time."""
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)


# Pydantic models for API
class ConsultationBase(BaseModel):
    """Base consultation model for API requests/responses."""
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    consultation_type: ConsultationType
    priority: ConsultationPriority = ConsultationPriority.NORMAL
    scheduled_date: datetime
    duration_minutes: int = Field(30, ge=15, le=480)
    timezone: str = "UTC"
    location: Optional[str] = None
    modality: str = "in_person"
    chief_complaint: Optional[str] = None
    symptoms: List[str] = []
    medical_history: Optional[str] = None
    current_medications: List[str] = []
    allergies: List[str] = []
    vital_signs: Dict[str, Any] = {}
    appointment_id: Optional[uuid.UUID] = None
    
    @validator('scheduled_date')
    def validate_scheduled_date(cls, v):
        if v < datetime.utcnow():
            raise ValueError('Scheduled date cannot be in the past')
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v < 15 or v > 480:
            raise ValueError('Duration must be between 15 and 480 minutes')
        return v


class ConsultationCreate(ConsultationBase):
    """Model for consultation creation."""
    pass


class ConsultationUpdate(BaseModel):
    """Model for consultation updates."""
    consultation_type: Optional[ConsultationType] = None
    priority: Optional[ConsultationPriority] = None
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    timezone: Optional[str] = None
    location: Optional[str] = None
    modality: Optional[str] = None
    chief_complaint: Optional[str] = None
    symptoms: Optional[List[str]] = None
    medical_history: Optional[str] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    status: Optional[ConsultationStatus] = None
    subjective_notes: Optional[str] = None
    objective_notes: Optional[str] = None
    assessment_notes: Optional[str] = None
    plan_notes: Optional[str] = None
    diagnosis: Optional[List[Dict[str, Any]]] = None
    treatment_plan: Optional[List[Dict[str, Any]]] = None
    prescriptions: Optional[List[Dict[str, Any]]] = None
    referrals: Optional[List[Dict[str, Any]]] = None
    follow_up_plan: Optional[str] = None


class ConsultationResponse(ConsultationBase):
    """Model for consultation API responses."""
    id: uuid.UUID
    status: ConsultationStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    subjective_notes: Optional[str] = None
    objective_notes: Optional[str] = None
    assessment_notes: Optional[str] = None
    plan_notes: Optional[str] = None
    diagnosis: List[Dict[str, Any]] = []
    treatment_plan: List[Dict[str, Any]] = []
    prescriptions: List[Dict[str, Any]] = []
    referrals: List[Dict[str, Any]] = []
    follow_up_plan: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
    # Computed properties
    is_active: bool
    is_completed: bool
    is_overdue: bool
    duration_minutes: int
    meta_data: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class ConsultationFilter(BaseModel):
    """Model for consultation filtering."""
    patient_id: Optional[uuid.UUID] = None
    doctor_id: Optional[uuid.UUID] = None
    consultation_type: Optional[ConsultationType] = None
    status: Optional[ConsultationStatus] = None
    priority: Optional[ConsultationPriority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    modality: Optional[str] = None
    appointment_id: Optional[uuid.UUID] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ConsultationNotes(BaseModel):
    """Model for consultation notes."""
    consultation_id: uuid.UUID
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    notes_by: uuid.UUID
    notes_at: datetime = Field(default_factory=datetime.utcnow)


class ConsultationDiagnosis(BaseModel):
    """Model for consultation diagnosis."""
    consultation_id: uuid.UUID
    diagnosis_code: str
    diagnosis_name: str
    diagnosis_type: str  # primary, secondary, etc.
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None
    added_by: uuid.UUID
    added_at: datetime = Field(default_factory=datetime.utcnow)


class ConsultationPrescription(BaseModel):
    """Model for consultation prescription."""
    consultation_id: uuid.UUID
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None
    quantity: Optional[str] = None
    refills: int = 0
    prescribed_by: uuid.UUID
    prescribed_at: datetime = Field(default_factory=datetime.utcnow) 