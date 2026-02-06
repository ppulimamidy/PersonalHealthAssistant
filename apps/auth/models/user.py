"""
User models for the Personal Health Assistant.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr, Field, validator
import uuid

from common.models.base import Base


class UserStatus(str, Enum):
    """User account status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class UserType(str, Enum):
    """User type enumeration for different personas."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"
    PHARMA = "pharma"
    INSURANCE = "insurance"
    RETAIL_STORE = "retail_store"
    RESEARCHER = "researcher"
    CAREGIVER = "caregiver"
    LAB_TECHNICIAN = "lab_technician"
    NURSE = "nurse"
    SPECIALIST = "specialist"
    EMERGENCY_CONTACT = "emergency_contact"


class MFAStatus(str, Enum):
    """Multi-factor authentication status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    REQUIRED = "required"
    SETUP_REQUIRED = "setup_required"


class User(Base):
    """Main user model with comprehensive authentication and authorization features."""
    
    __tablename__ = "users"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, unique=True, nullable=True, index=True)
    
    # Authentication
    password_hash = Column(String, nullable=True)  # For local auth
    auth0_user_id = Column(String, nullable=True, index=True)
    mfa_status = Column(String, default="disabled", nullable=False)
    mfa_secret = Column(String, nullable=True)
    
    # Profile information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    user_type = Column(String, nullable=False)
    
    # Account status
    status = Column(String, default="pending_verification", nullable=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # HIPAA compliance
    hipaa_consent_given = Column(Boolean, default=False)
    hipaa_consent_date = Column(DateTime, nullable=True)
    data_processing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime, nullable=True)
    account_locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Metadata
    user_metadata = Column(JSON, default=dict)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    user_roles = relationship("UserRole", back_populates="user", foreign_keys="UserRole.user_id")
    sessions = relationship("Session", back_populates="user")
    mfa_devices = relationship("MFADevice", back_populates="user")
    audit_logs = relationship("AuthAuditLog", back_populates="user", foreign_keys="AuthAuditLog.user_id")
    consent_records = relationship("ConsentRecord", back_populates="user", foreign_keys="ConsentRecord.user_id")
    
    # Cross-service relationships (commented out to avoid circular imports)
    # insights = relationship("InsightDB", back_populates="patient", foreign_keys="InsightDB.patient_id")
    # health_patterns = relationship("HealthPatternDB", back_populates="patient", foreign_keys="HealthPatternDB.patient_id")
    # health_attributes = relationship("HealthAttributes", back_populates="user", foreign_keys="HealthAttributes.user_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, user_type={self.user_type})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            return True
        return False
    
    def increment_failed_login(self):
        """Increment failed login attempts and potentially lock account."""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login_attempts(self):
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None


# Pydantic models for API
class UserBase(BaseModel):
    """Base user model for API requests/responses."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    user_type: UserType
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None


class UserCreate(UserBase):
    """Model for user creation."""
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """Model for user updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None


class UserResponse(UserBase):
    """Model for user API responses."""
    id: uuid.UUID
    status: UserStatus
    email_verified: bool
    phone_verified: bool
    mfa_status: MFAStatus
    hipaa_consent_given: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Model for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseModel):
    """Model for email verification request."""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Model for email verification confirmation."""
    email: EmailStr
    token: str


class UserProfile(Base):
    """Extended user profile information."""
    
    __tablename__ = "user_profiles"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Personal information
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    language = Column(String, default="en")
    
    # Health-related information
    blood_type = Column(String, nullable=True)
    height = Column(Integer, nullable=True)  # in cm
    weight = Column(Integer, nullable=True)  # in kg
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_contact_relationship = Column(String, nullable=True)
    
    # Professional information (for healthcare providers)
    license_number = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    certifications = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id})>"


class UserPreferences(Base):
    """User preferences and settings."""
    
    __tablename__ = "user_preferences"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    
    # Privacy preferences
    profile_visibility = Column(String, default="private")  # private, friends, public
    data_sharing_preferences = Column(JSON, default=dict)
    
    # UI preferences
    theme = Column(String, default="light")  # light, dark, auto
    language = Column(String, default="en")
    
    # Health tracking preferences
    health_goal_reminders = Column(Boolean, default=True)
    medication_reminders = Column(Boolean, default=True)
    appointment_reminders = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"
