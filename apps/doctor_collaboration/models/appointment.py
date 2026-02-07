"""
Appointment models for Doctor Collaboration Service.
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


class AppointmentStatus(str, Enum):
    """Appointment status enumeration."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    """Appointment type enumeration."""
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    ROUTINE_CHECKUP = "routine_checkup"
    SPECIALIST_REFERRAL = "specialist_referral"
    LAB_TEST = "lab_test"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    TELEMEDICINE = "telemedicine"
    IN_PERSON = "in_person"


class Appointment(Base):
    """Appointment model for doctor-patient appointments."""
    
    __tablename__ = "appointments"
    __table_args__ = {'schema': 'doctor_collaboration', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Participants
    patient_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    
    # Appointment details
    appointment_type = Column(SQLEnum(AppointmentType), nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, nullable=False)
    
    # Scheduling
    scheduled_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    timezone = Column(String, default="UTC", nullable=False)
    
    # Location and modality
    location = Column(String, nullable=True)  # Physical location or virtual meeting link
    modality = Column(String, default="in_person", nullable=False)  # in_person, telemedicine, phone
    
    # Notes and documentation
    notes = Column(Text, nullable=True)
    patient_notes = Column(Text, nullable=True)  # Notes from patient
    doctor_notes = Column(Text, nullable=True)   # Notes from doctor
    medical_notes = Column(Text, nullable=True)  # Medical observations
    
    # Reminders and notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    
    # Cancellation and rescheduling
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(UUID(as_uuid=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    rescheduled_from = Column(UUID(as_uuid=True), nullable=True)  # Reference to original appointment
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_appointments")
    doctor = relationship("User", foreign_keys=[doctor_id], backref="doctor_appointments")
    consultations = relationship("Consultation", back_populates="appointment")
    messages = relationship("Message", back_populates="appointment")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, scheduled_date={self.scheduled_date})>"
    
    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is in the future."""
        return self.scheduled_date > datetime.utcnow() and self.status in [
            AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED
        ]
    
    @property
    def is_overdue(self) -> bool:
        """Check if appointment is overdue."""
        return self.scheduled_date < datetime.utcnow() and self.status == AppointmentStatus.SCHEDULED
    
    @property
    def end_time(self) -> datetime:
        """Calculate appointment end time."""
        return self.scheduled_date + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_conflict(self) -> bool:
        """Check if appointment conflicts with doctor's schedule."""
        # This would be implemented with business logic
        return False


# Pydantic models for API
class AppointmentBase(BaseModel):
    """Base appointment model for API requests/responses."""
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_type: AppointmentType
    scheduled_date: datetime
    duration_minutes: int = Field(30, ge=15, le=480)  # 15 minutes to 8 hours
    timezone: str = "UTC"
    location: Optional[str] = None
    modality: str = "in_person"
    notes: Optional[str] = None
    patient_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    medical_notes: Optional[str] = None
    
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


class AppointmentCreate(AppointmentBase):
    """Model for appointment creation."""
    pass


class AppointmentUpdate(BaseModel):
    """Model for appointment updates."""
    appointment_type: Optional[AppointmentType] = None
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    timezone: Optional[str] = None
    location: Optional[str] = None
    modality: Optional[str] = None
    notes: Optional[str] = None
    patient_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    medical_notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    
    @validator('scheduled_date')
    def validate_scheduled_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError('Scheduled date cannot be in the past')
        return v


class AppointmentResponse(AppointmentBase):
    """Model for appointment API responses."""
    id: uuid.UUID
    status: AppointmentStatus
    reminder_sent: bool
    reminder_sent_at: Optional[datetime] = None
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[uuid.UUID] = None
    cancellation_reason: Optional[str] = None
    rescheduled_from: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    meta_data: Dict[str, Any] = {}
    
    # Computed properties
    is_upcoming: bool
    is_overdue: bool
    end_time: datetime
    
    class Config:
        from_attributes = True


class AppointmentFilter(BaseModel):
    """Model for appointment filtering."""
    patient_id: Optional[uuid.UUID] = None
    doctor_id: Optional[uuid.UUID] = None
    appointment_type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    modality: Optional[str] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class AppointmentConflict(BaseModel):
    """Model for appointment conflict detection."""
    appointment_id: uuid.UUID
    conflicting_appointment_id: uuid.UUID
    conflict_type: str  # overlap, same_time, etc.
    conflict_details: str
    severity: str  # low, medium, high


class AppointmentReminder(BaseModel):
    """Model for appointment reminders."""
    appointment_id: uuid.UUID
    reminder_type: str  # email, sms, push
    reminder_time: datetime
    sent: bool = False
    sent_at: Optional[datetime] = None
    recipient_id: uuid.UUID
    message: str 