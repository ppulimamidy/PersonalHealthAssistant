"""
Multi-factor authentication models for the Personal Health Assistant.

This module defines MFA models for TOTP (Time-based One-Time Password),
backup codes, and device management.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
import uuid
from ..models import Base


class MFAType(str, Enum):
    """MFA type enumeration."""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"    # SMS-based codes
    EMAIL = "email"  # Email-based codes
    BACKUP = "backup"  # Backup codes


class MFADeviceStatus(str, Enum):
    """MFA device status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOST = "lost"


class MFADevice(Base):
    """MFA device model for managing user MFA devices."""
    
    __tablename__ = "mfa_devices"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Device information
    device_name = Column(String, nullable=False)  # e.g., "iPhone 12", "Google Authenticator"
    device_type = Column(SQLEnum(MFAType), nullable=False)
    device_id = Column(String, unique=True, nullable=False, index=True)  # Unique device identifier
    
    # TOTP configuration
    secret_key = Column(String, nullable=True)  # Encrypted TOTP secret
    algorithm = Column(String, default="SHA1")  # TOTP algorithm
    digits = Column(Integer, default=6)  # Number of digits in code
    period = Column(Integer, default=30)  # Time period in seconds
    
    # Device status
    status = Column(SQLEnum(MFADeviceStatus), default=MFADeviceStatus.ACTIVE)
    is_primary = Column(Boolean, default=False)  # Primary MFA device
    
    # Security
    last_used_at = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Verification
    verified_at = Column(DateTime, nullable=True)
    verification_code = Column(String, nullable=True)  # For initial setup
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="mfa_devices")
    backup_codes = relationship("MFABackupCode", back_populates="device")
    
    def __repr__(self):
        return f"<MFADevice(id={self.id}, user_id={self.user_id}, type={self.device_type}, name={self.device_name})>"
    
    @property
    def is_active(self) -> bool:
        """Check if device is active and not locked."""
        if self.status != MFADeviceStatus.ACTIVE:
            return False
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return False
        return True
    
    def increment_failed_attempts(self):
        """Increment failed attempts and potentially lock device."""
        self.failed_attempts += 1
        self.last_used_at = datetime.utcnow()
        
        # Lock device after 5 failed attempts for 30 minutes
        if self.failed_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_attempts(self):
        """Reset failed attempts."""
        self.failed_attempts = 0
        self.locked_until = None
    
    def mark_as_used(self):
        """Mark device as used."""
        self.last_used_at = datetime.utcnow()
        self.reset_failed_attempts()
    
    def suspend(self, reason: str = "security_concern"):
        """Suspend the device."""
        self.status = MFADeviceStatus.SUSPENDED
    
    def activate(self):
        """Activate the device."""
        self.status = MFADeviceStatus.ACTIVE
        self.reset_failed_attempts()


class MFABackupCode(Base):
    """MFA backup code model for emergency access."""
    
    __tablename__ = "mfa_backup_codes"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("auth.mfa_devices.id"), nullable=True)
    
    # Code information
    code_hash = Column(String, nullable=False, index=True)  # Hashed backup code
    code_display = Column(String, nullable=False)  # Display version (first 4 chars + ...)
    
    # Usage tracking
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    used_from_ip = Column(String, nullable=True)
    used_from_user_agent = Column(Text, nullable=True)
    
    # Security
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    device = relationship("MFADevice", back_populates="backup_codes")
    
    def __repr__(self):
        return f"<MFABackupCode(id={self.id}, user_id={self.user_id}, used={self.is_used})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if backup code is valid and not expired."""
        if self.is_used:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def use(self, ip_address: str = None, user_agent: str = None):
        """Mark backup code as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.used_from_ip = ip_address
        self.used_from_user_agent = user_agent


class MFAAttempt(Base):
    """MFA attempt tracking for security monitoring."""
    
    __tablename__ = "mfa_attempts"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("auth.mfa_devices.id"), nullable=True)
    
    # Attempt information
    mfa_type = Column(SQLEnum(MFAType), nullable=False)
    code_provided = Column(String, nullable=True)  # Partial code for audit
    is_successful = Column(Boolean, nullable=False)
    
    # Context information
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=True)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100 risk score
    
    # Timestamps
    attempted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    device = relationship("MFADevice")
    session = relationship("Session")
    
    def __repr__(self):
        return f"<MFAAttempt(id={self.id}, user_id={self.user_id}, type={self.mfa_type}, success={self.is_successful})>"


# Pydantic models for API
class MFADeviceBase(BaseModel):
    """Base MFA device model."""
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: MFAType
    algorithm: str = "SHA1"
    digits: int = 6
    period: int = 30


class MFADeviceCreate(MFADeviceBase):
    """Model for MFA device creation."""
    pass


class MFADeviceUpdate(BaseModel):
    """Model for MFA device updates."""
    device_name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[MFADeviceStatus] = None
    is_primary: Optional[bool] = None


class MFADeviceResponse(MFADeviceBase):
    """Model for MFA device API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: str
    status: MFADeviceStatus
    is_primary: bool
    last_used_at: Optional[datetime] = None
    failed_attempts: int
    locked_until: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MFABackupCodeBase(BaseModel):
    """Base MFA backup code model."""
    code_display: str
    expires_at: Optional[datetime] = None


class MFABackupCodeCreate(MFABackupCodeBase):
    """Model for MFA backup code creation."""
    pass


class MFABackupCodeResponse(MFABackupCodeBase):
    """Model for MFA backup code API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: Optional[uuid.UUID] = None
    is_used: bool
    used_at: Optional[datetime] = None
    used_from_ip: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MFAAttemptBase(BaseModel):
    """Base MFA attempt model."""
    mfa_type: MFAType
    is_successful: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_suspicious: bool = False
    risk_score: int = 0


class MFAAttemptCreate(MFAAttemptBase):
    """Model for MFA attempt creation."""
    user_id: uuid.UUID
    device_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None


class MFAAttemptResponse(MFAAttemptBase):
    """Model for MFA attempt API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    attempted_at: datetime
    
    class Config:
        from_attributes = True


class MFASetupRequest(BaseModel):
    """Model for MFA setup requests."""
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: MFAType = MFAType.TOTP
    is_primary: bool = False


class MFAVerificationRequest(BaseModel):
    """Model for MFA verification requests."""
    code: str = Field(..., min_length=6, max_length=8)
    device_id: Optional[uuid.UUID] = None
    backup_code: bool = False


class MFASetupResponse(BaseModel):
    """Model for MFA setup responses."""
    device_id: uuid.UUID
    secret_key: str  # For TOTP setup
    qr_code_url: str  # QR code URL for authenticator apps
    backup_codes: List[str]  # List of backup codes
    verification_required: bool = True


# MFA configuration
MFA_CONFIG = {
    "totp": {
        "algorithm": "SHA1",
        "digits": 6,
        "period": 30,
        "window": 1,  # Allow 1 period before/after for clock skew
    },
    "backup_codes": {
        "count": 10,
        "length": 8,
        "format": "alphanumeric",
        "expires_after": None,  # No expiration by default
    },
    "security": {
        "max_failed_attempts": 5,
        "lockout_duration": timedelta(minutes=30),
        "require_verification": True,
        "suspicious_activity_threshold": 3,
    },
    "devices": {
        "max_devices_per_user": 5,
        "require_primary_device": True,
        "allow_multiple_primary": False,
    }
} 