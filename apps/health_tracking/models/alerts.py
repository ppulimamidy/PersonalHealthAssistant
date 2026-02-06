"""
Health Alerts Models
Defines database models and Pydantic schemas for health alert management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from common.models.base import Base


class AlertType(str, Enum):
    """Health alert types"""
    VITAL_SIGN_ANOMALY = "vital_sign_anomaly"
    GOAL_DEADLINE = "goal_deadline"
    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    EXERCISE_REMINDER = "exercise_reminder"
    HYDRATION_REMINDER = "hydration_reminder"
    SLEEP_REMINDER = "sleep_reminder"
    NUTRITION_REMINDER = "nutrition_reminder"
    DEVICE_CONNECTION = "device_connection"
    DATA_SYNC = "data_sync"
    SECURITY = "security"
    OTHER = "other"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Alert(Base):
    """Health alert database model"""
    __tablename__ = "alerts"
    __table_args__ = {"schema": "health_tracking"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    alert_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default=AlertSeverity.MEDIUM.value)
    status = Column(String(20), default=AlertStatus.ACTIVE.value)
    is_read = Column(Boolean, default=False)
    is_actionable = Column(Boolean, default=True)
    action_taken = Column(Text)
    action_taken_at = Column(DateTime)
    scheduled_for = Column(DateTime)
    expires_at = Column(DateTime)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "alert_type": self.alert_type,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "status": self.status,
            "is_read": self.is_read,
            "is_actionable": self.is_actionable,
            "action_taken": self.action_taken,
            "action_taken_at": self.action_taken_at.isoformat() if self.action_taken_at else None,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "alert_metadata": self.alert_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Pydantic Models
class AlertBase(BaseModel):
    """Base alert model"""
    alert_type: AlertType = Field(..., description="Type of health alert")
    title: str = Field(..., min_length=1, max_length=255, description="Alert title")
    message: str = Field(..., min_length=1, description="Alert message")
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM, description="Alert severity level")
    is_actionable: bool = Field(default=True, description="Whether the alert requires action")
    scheduled_for: Optional[datetime] = Field(None, description="When the alert should be triggered")
    expires_at: Optional[datetime] = Field(None, description="When the alert expires")
    alert_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional alert metadata")


class AlertCreate(AlertBase):
    """Alert creation model"""
    pass


class AlertUpdate(BaseModel):
    """Alert update model"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    is_read: Optional[bool] = None
    is_actionable: Optional[bool] = None
    action_taken: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    alert_metadata: Optional[Dict[str, Any]] = None


class AlertResponse(AlertBase):
    """Alert response model"""
    id: str
    user_id: str
    status: str
    is_read: bool
    action_taken: Optional[str] = None
    action_taken_at: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AlertFilter(BaseModel):
    """Alert filter model"""
    alert_type: Optional[AlertType] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    is_read: Optional[bool] = None
    is_actionable: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0) 