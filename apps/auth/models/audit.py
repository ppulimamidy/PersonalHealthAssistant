"""
Audit logging models for the Personal Health Assistant.

This module defines comprehensive audit logging models for HIPAA compliance,
security monitoring, and regulatory requirements.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
import uuid

# Import the shared Base from common models
from common.models.base import Base

# Import related models to ensure they're available for relationships
from .user import User
from .session import Session
from .mfa import MFADevice


class AuditEventType(str, Enum):
    """Audit event type enumeration."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    
    # MFA events
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFICATION_SUCCESS = "mfa_verification_success"
    MFA_VERIFICATION_FAILURE = "mfa_verification_failure"
    MFA_DEVICE_ADDED = "mfa_device_added"
    MFA_DEVICE_REMOVED = "mfa_device_removed"
    BACKUP_CODE_USED = "backup_code_used"
    
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_REVOKED = "session_revoked"
    SESSION_EXPIRED = "session_expired"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"
    
    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # Data access events
    DATA_ACCESSED = "data_accessed"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    DATA_SHARED = "data_shared"
    
    # Consent events
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    CONSENT_UPDATED = "consent_updated"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_ALERT = "security_alert"
    BREACH_DETECTED = "breach_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"
    
    # System events
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    BACKUP_CREATED = "backup_created"
    MAINTENANCE_MODE = "maintenance_mode"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(str, Enum):
    """Audit event severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """Audit event status enumeration."""
    PENDING = "pending"
    PROCESSED = "processed"
    REVIEWED = "reviewed"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AuthAuditLog(Base):
    """Authentication audit log model for comprehensive security monitoring."""
    
    __tablename__ = "auth_audit_logs"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)  # Null for anonymous events
    
    # Event information
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.LOW)
    status = Column(SQLEnum(AuditStatus), default=AuditStatus.PENDING)
    
    # Event details
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)  # Structured event details
    
    # Context information
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=True)
    device_id = Column(String, nullable=True)
    
    # Geographic and network information
    location = Column(String, nullable=True)  # Country/City
    timezone = Column(String, nullable=True)
    isp = Column(String, nullable=True)
    
    # Security information
    risk_score = Column(Integer, default=0)  # 0-100 risk assessment
    is_suspicious = Column(Boolean, default=False)
    threat_indicators = Column(JSON, default=list)  # List of threat indicators
    
    # HIPAA compliance
    hipaa_relevant = Column(Boolean, default=False)
    phi_accessed = Column(Boolean, default=False)  # Protected Health Information
    data_subject_id = Column(UUID(as_uuid=True), nullable=True)  # Patient whose data was accessed
    
    # Related entities
    related_user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    related_session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=True)
    related_device_id = Column(UUID(as_uuid=True), ForeignKey("auth.mfa_devices.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("Session", foreign_keys=[session_id])
    related_user = relationship("User", foreign_keys=[related_user_id])
    related_session = relationship("Session", foreign_keys=[related_session_id])
    
    def __repr__(self):
        return f"<AuthAuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id}, timestamp={self.event_timestamp})>"
    
    @property
    def is_high_priority(self) -> bool:
        """Check if event is high priority for immediate review."""
        return self.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL] or self.is_suspicious
    
    def add_threat_indicator(self, indicator: str):
        """Add a threat indicator to the event."""
        if not self.threat_indicators:
            self.threat_indicators = []
        self.threat_indicators.append(indicator)
    
    def mark_as_suspicious(self, reason: str):
        """Mark event as suspicious."""
        self.is_suspicious = True
        self.add_threat_indicator(reason)
    
    def update_risk_score(self, score: int):
        """Update the risk score for the event."""
        self.risk_score = max(0, min(100, score))


class SecurityAlert(Base):
    """Security alert model for threat detection and response."""
    
    __tablename__ = "security_alerts"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert information
    alert_type = Column(String, nullable=False, index=True)  # "brute_force", "suspicious_login", etc.
    severity = Column(SQLEnum(AuditSeverity), nullable=False)
    status = Column(SQLEnum(AuditStatus), default=AuditStatus.PENDING)
    
    # Alert details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    
    # Affected entities
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=True)
    ip_address = Column(String, nullable=True)
    
    # Threat information
    threat_level = Column(String, default="low")  # "low", "medium", "high", "critical"
    threat_indicators = Column(JSON, default=list)
    recommended_actions = Column(JSON, default=list)
    
    # Response tracking
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    response_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("Session")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<SecurityAlert(id={self.id}, type={self.alert_type}, severity={self.severity}, status={self.status})>"
    
    def resolve(self, notes: str = None, resolved_by: uuid.UUID = None):
        """Resolve the security alert."""
        self.status = AuditStatus.RESOLVED
        self.response_notes = notes
        self.resolved_at = datetime.utcnow()
        if resolved_by:
            self.assigned_to = resolved_by


# Pydantic models for API
class AuthAuditLogBase(BaseModel):
    """Base audit log model."""
    event_type: AuditEventType
    description: str
    severity: AuditSeverity = AuditSeverity.LOW
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    risk_score: int = 0
    is_suspicious: bool = False
    hipaa_relevant: bool = False
    phi_accessed: bool = False


class AuthAuditLogCreate(AuthAuditLogBase):
    """Model for audit log creation."""
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    data_subject_id: Optional[uuid.UUID] = None
    related_user_id: Optional[uuid.UUID] = None
    related_session_id: Optional[uuid.UUID] = None
    related_device_id: Optional[uuid.UUID] = None


class AuthAuditLogResponse(AuthAuditLogBase):
    """Model for audit log API responses."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    event_timestamp: datetime
    status: AuditStatus
    session_id: Optional[uuid.UUID] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    threat_indicators: List[str] = []
    data_subject_id: Optional[uuid.UUID] = None
    related_user_id: Optional[uuid.UUID] = None
    related_session_id: Optional[uuid.UUID] = None
    related_device_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SecurityAlertBase(BaseModel):
    """Base security alert model."""
    alert_type: str
    severity: AuditSeverity
    title: str
    description: str
    threat_level: str = "low"
    details: Dict[str, Any] = {}
    threat_indicators: List[str] = []
    recommended_actions: List[str] = []


class SecurityAlertCreate(SecurityAlertBase):
    """Model for security alert creation."""
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None


class SecurityAlertUpdate(BaseModel):
    """Model for security alert updates."""
    status: Optional[AuditStatus] = None
    assigned_to: Optional[uuid.UUID] = None
    response_notes: Optional[str] = None


class SecurityAlertResponse(SecurityAlertBase):
    """Model for security alert API responses."""
    id: uuid.UUID
    status: AuditStatus
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    response_notes: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Audit configuration
AUDIT_CONFIG = {
    "retention": {
        "auth_logs_days": 365 * 7,  # 7 years for HIPAA compliance
        "data_access_logs_days": 365 * 7,  # 7 years for HIPAA compliance
        "security_alerts_days": 365 * 3,  # 3 years
    },
    "alerting": {
        "high_risk_threshold": 75,
        "critical_risk_threshold": 90,
        "suspicious_activity_threshold": 3,
        "failed_login_threshold": 5,
    },
    "compliance": {
        "hipaa_logging": True,
        "gdpr_logging": True,
        "data_subject_tracking": True,
        "consent_tracking": True,
    }
} 