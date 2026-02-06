"""
Session management models for the Personal Health Assistant.

This module defines session and token management models with security features,
refresh token rotation, and audit capabilities.
"""

from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
import uuid
from ..models import Base


class SessionStatus(str, Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


class TokenType(str, Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"
    MFA = "mfa"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"


class Session(Base):
    """Session model for managing user sessions."""
    
    __tablename__ = "sessions"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Session identification
    session_token = Column(String, unique=True, nullable=False, index=True)
    refresh_token = Column(String, unique=True, nullable=False, index=True)
    
    # Session metadata
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    device_id = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet
    
    # Security information
    fingerprint = Column(String, nullable=True)  # Browser/device fingerprint
    location = Column(String, nullable=True)  # Geographic location
    
    # Session status
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)
    is_mfa_verified = Column(Boolean, default=False)
    
    # Token information
    access_token_expires_at = Column(DateTime, nullable=False)
    refresh_token_expires_at = Column(DateTime, nullable=False)
    
    # Security tracking
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    login_at = Column(DateTime, default=datetime.utcnow)
    logout_at = Column(DateTime, nullable=True)
    
    # Audit information
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if session is active and not expired."""
        if self.status != SessionStatus.ACTIVE:
            return False
        if datetime.utcnow() > self.access_token_expires_at:
            return False
        return True
    
    @property
    def is_refresh_valid(self) -> bool:
        """Check if refresh token is still valid."""
        if self.status != SessionStatus.ACTIVE:
            return False
        if datetime.utcnow() > self.refresh_token_expires_at:
            return False
        return True
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()
    
    def revoke(self, reason: str = "manual_logout"):
        """Revoke the session."""
        self.status = SessionStatus.REVOKED
        self.logout_at = datetime.utcnow()
    
    def expire(self):
        """Mark session as expired."""
        self.status = SessionStatus.EXPIRED
        self.logout_at = datetime.utcnow()


class RefreshToken(Base):
    """Refresh token model for token rotation and security."""
    
    __tablename__ = "refresh_tokens"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=False)
    
    # Token information
    token_hash = Column(String, nullable=False, index=True)
    token_type = Column(SQLEnum(TokenType), default=TokenType.REFRESH)
    
    # Token lifecycle
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Security
    is_revoked = Column(Boolean, default=False)
    revocation_reason = Column(String, nullable=True)
    
    # Token rotation
    replaced_by_token_id = Column(UUID(as_uuid=True), ForeignKey("auth.refresh_tokens.id"), nullable=True)
    replaces_token_id = Column(UUID(as_uuid=True), ForeignKey("auth.refresh_tokens.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("Session")
    replaced_by = relationship("RefreshToken", remote_side=[id], foreign_keys=[replaced_by_token_id])
    replaces = relationship("RefreshToken", remote_side=[id], foreign_keys=[replaces_token_id])
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, session_id={self.session_id}, type={self.token_type})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid and not expired."""
        if self.is_revoked:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def revoke(self, reason: str = "manual_revocation"):
        """Revoke the token."""
        self.is_revoked = True
        self.revocation_reason = reason
        self.revoked_at = datetime.utcnow()
    
    def use(self):
        """Mark token as used."""
        self.used_at = datetime.utcnow()


class TokenBlacklist(Base):
    """Token blacklist for revoked tokens."""
    
    __tablename__ = "token_blacklist"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Token information
    token_hash = Column(String, nullable=False, index=True)
    token_type = Column(SQLEnum(TokenType), nullable=False)
    
    # Blacklist information
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # When the token would have expired
    reason = Column(String, nullable=True)
    
    # Metadata
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, token_hash={self.token_hash[:10]}..., reason={self.reason})>"


# Pydantic models for API
class SessionBase(BaseModel):
    """Base session model."""
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    fingerprint: Optional[str] = None
    location: Optional[str] = None


class SessionCreate(SessionBase):
    """Model for session creation."""
    user_id: uuid.UUID
    session_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime


class SessionUpdate(BaseModel):
    """Model for session updates."""
    status: Optional[SessionStatus] = None
    is_mfa_verified: Optional[bool] = None
    last_activity_at: Optional[datetime] = None


class SessionResponse(SessionBase):
    """Model for session API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    session_token: str
    refresh_token: str
    status: SessionStatus
    is_mfa_verified: bool
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    last_activity_at: datetime
    login_at: datetime
    logout_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RefreshTokenBase(BaseModel):
    """Base refresh token model."""
    token_hash: str
    token_type: TokenType = TokenType.REFRESH
    issued_at: datetime
    expires_at: datetime


class RefreshTokenCreate(RefreshTokenBase):
    """Model for refresh token creation."""
    session_id: uuid.UUID


class RefreshTokenUpdate(BaseModel):
    """Model for refresh token updates."""
    used_at: Optional[datetime] = None
    is_revoked: Optional[bool] = None
    revocation_reason: Optional[str] = None


class RefreshTokenResponse(RefreshTokenBase):
    """Model for refresh token API responses."""
    id: uuid.UUID
    session_id: uuid.UUID
    used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_revoked: bool
    revocation_reason: Optional[str] = None
    replaced_by_token_id: Optional[uuid.UUID] = None
    replaces_token_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenBlacklistBase(BaseModel):
    """Base token blacklist model."""
    token_hash: str
    token_type: TokenType
    blacklisted_at: datetime
    expires_at: datetime
    reason: Optional[str] = None


class TokenBlacklistCreate(TokenBlacklistBase):
    """Model for token blacklist creation."""
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None


class TokenBlacklistResponse(TokenBlacklistBase):
    """Model for token blacklist API responses."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Session configuration
SESSION_CONFIG = {
    "access_token_expiry": timedelta(minutes=15),  # Short-lived access tokens
    "refresh_token_expiry": timedelta(days=7),     # Longer-lived refresh tokens
    "mfa_token_expiry": timedelta(minutes=5),      # Short-lived MFA tokens
    "max_sessions_per_user": 5,                    # Maximum concurrent sessions
    "session_timeout": timedelta(hours=24),        # Session timeout for inactivity
    "token_rotation": True,                        # Enable token rotation
    "blacklist_expiry_buffer": timedelta(hours=1), # Buffer for blacklisted tokens
} 