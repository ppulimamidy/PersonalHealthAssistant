"""
User stub model to avoid circular imports between auth and user-profile services.
This is a minimal User model that only contains the fields needed by the user-profile service.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum
from datetime import datetime
import uuid

from common.models.base import Base


class UserStatus(str, Enum):
    """User account status enumeration."""
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending_verification = "pending_verification"
    locked = "locked"


class UserType(str, Enum):
    """User type enumeration for different personas."""
    patient = "patient"
    doctor = "doctor"
    admin = "admin"
    pharma = "pharma"
    insurance = "insurance"
    retail_store = "retail_store"
    researcher = "researcher"
    caregiver = "caregiver"
    lab_technician = "lab_technician"
    nurse = "nurse"
    specialist = "specialist"
    emergency_contact = "emergency_contact"


class User(Base):
    """Minimal user model for user-profile service to avoid circular imports."""
    
    __tablename__ = "users"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Profile information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    user_type = Column(SQLEnum(UserType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    
    # Account status
    status = Column(SQLEnum(UserStatus, values_callable=lambda obj: [e.value for e in obj]), default=UserStatus.pending_verification)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - temporarily disabled to fix SQLAlchemy conflict
    # profile = relationship("Profile", back_populates=None, uselist=False, foreign_keys="Profile.user_id")
    # preferences = relationship("Preferences", back_populates=None, uselist=False, foreign_keys="Preferences.user_id")
    # privacy_settings = relationship("PrivacySettings", back_populates=None, uselist=False, foreign_keys="PrivacySettings.user_id")
    # health_attributes = relationship("HealthAttributes", back_populates=None, uselist=False, foreign_keys="HealthAttributes.user_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>" 