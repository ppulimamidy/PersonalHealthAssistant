"""
Notification models for Doctor Collaboration Service.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid

from common.models.base import Base


class NotificationType(str, Enum):
    """Notification type enumeration."""
    APPOINTMENT = "appointment"
    MESSAGE = "message"
    CONSULTATION = "consultation"
    REMINDER = "reminder"
    ALERT = "alert"
    SYSTEM = "system"
    SECURITY = "security"
    UPDATE = "update"


class NotificationPriority(str, Enum):
    """Notification priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationChannel(str, Enum):
    """Notification channel enumeration."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class Notification(Base):
    """Notification model for doctor-patient notifications."""
    
    __tablename__ = "notifications"
    __table_args__ = {'schema': 'doctor_collaboration', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Recipient
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    
    # Notification details
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    
    # Content
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(String, nullable=True)
    
    # Delivery
    channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.IN_APP, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Related entities
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.appointments.id"), nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.messages.id"), nullable=True)
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.consultations.id"), nullable=True)
    
    # Delivery attempts and errors
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Expiration and retry
    expires_at = Column(DateTime, nullable=True)
    retry_until = Column(DateTime, nullable=True)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id], backref="notifications")
    appointment = relationship("Appointment", back_populates="notifications")
    message = relationship("Message", back_populates="notifications")
    consultation = relationship("Consultation", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, recipient_id={self.recipient_id}, type={self.notification_type})>"
    
    @property
    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.status == NotificationStatus.READ
    
    @property
    def is_delivered(self) -> bool:
        """Check if notification has been delivered."""
        return self.status in [NotificationStatus.DELIVERED, NotificationStatus.READ]
    
    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        if self.delivery_attempts >= self.max_retries:
            return False
        if not self.retry_until:
            return True
        return datetime.utcnow() < self.retry_until


# Pydantic models for API
class NotificationBase(BaseModel):
    """Base notification model for API requests/responses."""
    recipient_id: uuid.UUID
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)
    summary: Optional[str] = Field(None, max_length=500)
    channel: NotificationChannel = NotificationChannel.IN_APP
    scheduled_at: Optional[datetime] = None
    appointment_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
    consultation_id: Optional[uuid.UUID] = None
    expires_at: Optional[datetime] = None
    retry_until: Optional[datetime] = None
    max_retries: int = Field(3, ge=0, le=10)
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Notification title cannot be empty')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Notification content cannot be empty')
        return v.strip()


class NotificationCreate(NotificationBase):
    """Model for notification creation."""
    pass


class NotificationUpdate(BaseModel):
    """Model for notification updates."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    summary: Optional[str] = Field(None, max_length=500)
    priority: Optional[NotificationPriority] = None
    status: Optional[NotificationStatus] = None
    channel: Optional[NotificationChannel] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retry_until: Optional[datetime] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)


class NotificationResponse(NotificationBase):
    """Model for notification API responses."""
    id: uuid.UUID
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_attempts: int
    last_error: Optional[str] = None
    error_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
    # Computed properties
    is_sent: bool
    is_delivered: bool
    is_read: bool
    meta_data: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class NotificationFilter(BaseModel):
    """Model for notification filtering."""
    recipient_id: Optional[uuid.UUID] = None
    notification_type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    status: Optional[NotificationStatus] = None
    channel: Optional[NotificationChannel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    appointment_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
    consultation_id: Optional[uuid.UUID] = None
    unread_only: bool = False
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class NotificationPreferences(BaseModel):
    """Model for notification preferences."""
    user_id: uuid.UUID
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    in_app_notifications: bool = True
    
    # Type-specific preferences
    appointment_notifications: bool = True
    message_notifications: bool = True
    consultation_notifications: bool = True
    reminder_notifications: bool = True
    system_notifications: bool = True
    security_notifications: bool = True
    
    # Priority preferences
    low_priority: bool = True
    normal_priority: bool = True
    high_priority: bool = True
    urgent_priority: bool = True
    critical_priority: bool = True
    
    # Timing preferences
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None    # HH:MM format
    timezone: str = "UTC"
    
    # Frequency preferences
    max_notifications_per_day: int = Field(50, ge=1, le=1000)
    batch_notifications: bool = False
    batch_interval_minutes: int = Field(15, ge=1, le=1440)


class NotificationTemplate(BaseModel):
    """Model for notification templates."""
    id: uuid.UUID
    name: str
    notification_type: NotificationType
    title_template: str
    content_template: str
    summary_template: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    channel: NotificationChannel = NotificationChannel.IN_APP
    variables: List[str] = []  # List of template variables
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class NotificationDelivery(BaseModel):
    """Model for notification delivery tracking."""
    notification_id: uuid.UUID
    channel: NotificationChannel
    delivery_status: NotificationStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_attempts: int
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class NotificationStats(BaseModel):
    """Model for notification statistics."""
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    read_notifications: int
    failed_notifications: int
    unread_notifications: int
    
    # By type
    appointment_notifications: int
    message_notifications: int
    consultation_notifications: int
    reminder_notifications: int
    system_notifications: int
    
    # By priority
    low_priority: int
    normal_priority: int
    high_priority: int
    urgent_priority: int
    critical_priority: int
    
    # By channel
    email_notifications: int
    sms_notifications: int
    push_notifications: int
    in_app_notifications: int
    
    # Delivery rates
    delivery_rate: float
    read_rate: float
    failure_rate: float
    
    # Time-based stats
    notifications_today: int
    notifications_this_week: int
    notifications_this_month: int 