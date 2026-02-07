"""
Messaging models for Doctor Collaboration Service.
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


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    SYSTEM = "system"
    NOTIFICATION = "notification"


class MessagePriority(str, Enum):
    """Message priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(str, Enum):
    """Message status enumeration."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class Message(Base):
    """Message model for doctor-patient communication."""
    
    __tablename__ = "messages"
    __table_args__ = {'schema': 'doctor_collaboration', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Participants
    sender_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    
    # Message details
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT, nullable=False)
    priority = Column(SQLEnum(MessagePriority), default=MessagePriority.NORMAL, nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    subject = Column(String, nullable=True)
    
    # Attachments and media
    attachments = Column(JSON, default=list)  # List of attachment metadata
    media_url = Column(String, nullable=True)  # URL to media file
    media_type = Column(String, nullable=True)  # MIME type of media
    
    # Context
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.appointments.id"), nullable=True)
    consultation_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.consultations.id"), nullable=True)
    thread_id = Column(UUID(as_uuid=True), nullable=True)  # For message threading
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("doctor_collaboration.messages.id"), nullable=True)
    
    # Delivery and read status
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    delivery_attempts = Column(Integer, default=0)
    
    # Security and privacy
    encrypted = Column(Boolean, default=True)
    retention_days = Column(Integer, default=2555)  # 7 years for medical records
    auto_delete = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    meta_data = Column(JSON, default=dict)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], backref="received_messages")
    appointment = relationship("Appointment", back_populates="messages")
    consultation = relationship("Consultation", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id], backref="replies")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id}, type={self.message_type})>"
    
    @property
    def is_read(self) -> bool:
        """Check if message has been read."""
        return self.status == MessageStatus.READ
    
    @property
    def is_delivered(self) -> bool:
        """Check if message has been delivered."""
        return self.status in [MessageStatus.DELIVERED, MessageStatus.READ]
    
    @property
    def is_urgent(self) -> bool:
        """Check if message is urgent."""
        return self.priority == MessagePriority.URGENT
    
    @property
    def has_attachments(self) -> bool:
        """Check if message has attachments."""
        return bool(self.attachments and len(self.attachments) > 0)


# Pydantic models for API
class MessageBase(BaseModel):
    """Base message model for API requests/responses."""
    recipient_id: uuid.UUID
    message_type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    content: str = Field(..., min_length=1, max_length=10000)
    subject: Optional[str] = Field(None, max_length=200)
    attachments: List[Dict[str, Any]] = []
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    appointment_id: Optional[uuid.UUID] = None
    consultation_id: Optional[uuid.UUID] = None
    thread_id: Optional[uuid.UUID] = None
    parent_message_id: Optional[uuid.UUID] = None
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class MessageCreate(MessageBase):
    """Model for message creation."""
    pass


class MessageUpdate(BaseModel):
    """Model for message updates."""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    subject: Optional[str] = Field(None, max_length=200)
    priority: Optional[MessagePriority] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None


class MessageResponse(MessageBase):
    """Model for message API responses."""
    id: uuid.UUID
    sender_id: uuid.UUID
    status: MessageStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_attempts: int
    encrypted: bool
    retention_days: int
    auto_delete: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
    # Computed properties
    is_read: bool
    is_delivered: bool
    is_urgent: bool
    has_attachments: bool
    is_encrypted: bool
    meta_data: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class MessageFilter(BaseModel):
    """Model for message filtering."""
    sender_id: Optional[uuid.UUID] = None
    recipient_id: Optional[uuid.UUID] = None
    message_type: Optional[MessageType] = None
    priority: Optional[MessagePriority] = None
    status: Optional[MessageStatus] = None
    appointment_id: Optional[uuid.UUID] = None
    consultation_id: Optional[uuid.UUID] = None
    thread_id: Optional[uuid.UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    unread_only: bool = False
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class MessageThread(BaseModel):
    """Model for message threading."""
    thread_id: uuid.UUID
    participants: List[uuid.UUID]
    messages: List[MessageResponse]
    unread_count: int
    last_message_at: datetime
    created_at: datetime


class MessageAttachment(BaseModel):
    """Model for message attachments."""
    id: uuid.UUID
    message_id: uuid.UUID
    filename: str
    file_size: int
    mime_type: str
    url: str
    uploaded_at: datetime
    metadata: Dict[str, Any] = {}


class MessageDeliveryStatus(BaseModel):
    """Model for message delivery status."""
    message_id: uuid.UUID
    status: MessageStatus
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_attempts: int
    error_message: Optional[str] = None 