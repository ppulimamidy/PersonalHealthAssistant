"""
Audit models for the Personal Health Assistant Consent Audit Service.

This module defines comprehensive audit models for consent tracking,
GDPR compliance, HIPAA validation, and data processing audits.

Includes both SQLAlchemy ORM models (for DB persistence) and
Pydantic schemas (for API request/response validation).
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, Float, Integer, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator
from uuid import uuid4
import uuid

from common.models.base import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AuditEventType(str, Enum):
    """Audit event type enumeration."""

    CONSENT_GRANTED = "consent_granted"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    CONSENT_EXPIRED = "consent_expired"
    CONSENT_MODIFIED = "consent_modified"
    DATA_ACCESS = "data_access"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    RIGHT_TO_ACCESS = "right_to_access"
    RIGHT_TO_RECTIFICATION = "right_to_rectification"
    RIGHT_TO_ERASURE = "right_to_erasure"
    RIGHT_TO_PORTABILITY = "right_to_portability"
    RIGHT_TO_RESTRICTION = "right_to_restriction"
    RIGHT_TO_OBJECT = "right_to_object"
    CONSENT_VERIFICATION = "consent_verification"
    COMPLIANCE_CHECK = "compliance_check"
    SECURITY_BREACH = "security_breach"
    POLICY_UPDATE = "policy_update"


class AuditSeverity(str, Enum):
    """Audit severity level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    """Compliance status enumeration."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPT = "exempt"


class DataProcessingPurpose(str, Enum):
    """Data processing purpose enumeration."""

    TREATMENT = "treatment"
    PAYMENT = "payment"
    HEALTHCARE_OPERATIONS = "healthcare_operations"
    RESEARCH = "research"
    PUBLIC_HEALTH = "public_health"
    LEGAL_REQUIREMENT = "legal_requirement"
    EMERGENCY = "emergency"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    MACHINE_LEARNING = "machine_learning"
    QUALITY_IMPROVEMENT = "quality_improvement"
    PATIENT_SAFETY = "patient_safety"


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------


class ConsentAuditLog(Base):
    """SQLAlchemy model for consent audit log entries."""

    __tablename__ = "consent_audit_logs"
    __table_args__ = (
        Index("idx_cal_user_id", "user_id"),
        Index("idx_cal_event_type", "event_type"),
        Index("idx_cal_event_timestamp", "event_timestamp"),
        Index("idx_cal_severity", "severity"),
        {"schema": "consent_audit"},
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    event_description = Column(Text, nullable=False)
    event_data = Column(JSONB, nullable=False, default=dict)
    event_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(PGUUID(as_uuid=True), nullable=True)
    actor_id = Column(PGUUID(as_uuid=True), nullable=False)
    actor_type = Column(String(50), nullable=False)
    actor_role = Column(String(100), nullable=True)
    consent_record_id = Column(PGUUID(as_uuid=True), nullable=True)
    data_subject_id = Column(PGUUID(as_uuid=True), nullable=True)
    gdpr_compliant = Column(Boolean, nullable=False, default=True)
    hipaa_compliant = Column(Boolean, nullable=False, default=True)
    compliance_notes = Column(Text, nullable=True)
    compliance_issues = Column(JSONB, nullable=False, default=list)
    risk_level = Column(String(20), nullable=False, default="low")
    risk_factors = Column(JSONB, nullable=False, default=list)
    mitigation_actions = Column(JSONB, nullable=False, default=list)
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
    )


class DataProcessingAudit(Base):
    """SQLAlchemy model for data processing audit entries."""

    __tablename__ = "data_processing_audits"
    __table_args__ = (
        Index("idx_dpa_user_id", "user_id"),
        Index("idx_dpa_purpose", "processing_purpose"),
        Index("idx_dpa_timestamp", "processing_timestamp"),
        Index("idx_dpa_compliance", "compliance_status"),
        {"schema": "consent_audit"},
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    processing_purpose = Column(String(50), nullable=False)
    processing_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    processing_duration = Column(Integer, nullable=True)
    data_categories = Column(JSONB, nullable=False, default=list)
    data_volume = Column(Integer, nullable=True)
    data_sensitivity = Column(String(20), nullable=False, default="medium")
    consent_record_id = Column(PGUUID(as_uuid=True), nullable=True)
    data_subject_id = Column(PGUUID(as_uuid=True), nullable=True)
    processing_method = Column(String(50), nullable=False)
    processing_location = Column(String(255), nullable=True)
    processing_tools = Column(JSONB, nullable=False, default=list)
    third_parties_involved = Column(JSONB, nullable=False, default=list)
    data_shared_with = Column(JSONB, nullable=False, default=list)
    legal_basis = Column(String(100), nullable=False)
    consent_verified = Column(Boolean, nullable=False, default=False)
    consent_verification_method = Column(String(100), nullable=True)
    compliance_status = Column(String(30), nullable=False, default="pending_review")
    data_encrypted = Column(Boolean, nullable=False, default=True)
    access_controls = Column(JSONB, nullable=False, default=list)
    retention_period = Column(Integer, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )


class ComplianceReport(Base):
    """SQLAlchemy model for compliance reports."""

    __tablename__ = "compliance_reports"
    __table_args__ = (
        Index("idx_cr_report_type", "report_type"),
        Index("idx_cr_framework", "framework"),
        Index("idx_cr_status", "report_status"),
        Index("idx_cr_period", "report_period_start", "report_period_end"),
        {"schema": "consent_audit"},
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_type = Column(String(50), nullable=False)
    framework = Column(String(20), nullable=True)  # gdpr / hipaa / both
    report_period_start = Column(DateTime, nullable=False)
    report_period_end = Column(DateTime, nullable=False)
    report_status = Column(String(20), nullable=False, default="draft")
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    organization_id = Column(PGUUID(as_uuid=True), nullable=True)
    scope_description = Column(Text, nullable=False)
    total_consents = Column(Integer, nullable=False, default=0)
    active_consents = Column(Integer, nullable=False, default=0)
    expired_consents = Column(Integer, nullable=False, default=0)
    withdrawn_consents = Column(Integer, nullable=False, default=0)
    compliance_violations = Column(Integer, nullable=False, default=0)
    security_incidents = Column(Integer, nullable=False, default=0)
    data_breaches = Column(Integer, nullable=False, default=0)
    data_processing_events = Column(Integer, nullable=False, default=0)
    data_sharing_events = Column(Integer, nullable=False, default=0)
    data_access_events = Column(Integer, nullable=False, default=0)
    executive_summary = Column(Text, nullable=True)
    detailed_findings = Column(JSONB, nullable=False, default=dict)
    recommendations = Column(JSONB, nullable=False, default=list)
    action_items = Column(JSONB, nullable=False, default=list)
    gdpr_compliance_score = Column(Integer, nullable=True)
    hipaa_compliance_score = Column(Integer, nullable=True)
    overall_compliance_score = Column(Integer, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )
    submitted_at = Column(DateTime, nullable=True)


class ConsentRecord(Base):
    """SQLAlchemy model for consent records."""

    __tablename__ = "consent_records"
    __table_args__ = (
        Index("idx_crec_user_id", "user_id"),
        Index("idx_crec_consent_type", "consent_type"),
        Index("idx_crec_granted", "granted"),
        {"schema": "consent_audit"},
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    consent_type = Column(String(100), nullable=False)
    purpose = Column(String(255), nullable=False)
    granted = Column(Boolean, nullable=False, default=True)
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    version = Column(String(20), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now()
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )


# ---------------------------------------------------------------------------
# Pydantic Schemas  (kept for API request / response validation)
# ---------------------------------------------------------------------------


class ConsentAuditLogBase(BaseModel):
    """Base consent audit log model."""

    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.MEDIUM
    event_description: str = Field(..., min_length=1)
    event_data: Dict[str, Any] = {}
    gdpr_compliant: bool = True
    hipaa_compliant: bool = True
    compliance_notes: Optional[str] = None
    compliance_issues: List[str] = []
    risk_level: AuditSeverity = AuditSeverity.LOW
    risk_factors: List[str] = []
    mitigation_actions: List[str] = []


class ConsentAuditLogCreate(ConsentAuditLogBase):
    """Model for consent audit log creation."""

    user_id: uuid.UUID
    consent_record_id: Optional[uuid.UUID] = None
    data_subject_id: Optional[uuid.UUID] = None
    actor_id: uuid.UUID
    actor_type: str = Field(..., min_length=1)
    actor_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[uuid.UUID] = None


class ConsentAuditLogUpdate(BaseModel):
    """Model for consent audit log updates."""

    severity: Optional[AuditSeverity] = None
    compliance_notes: Optional[str] = None
    compliance_issues: Optional[List[str]] = None
    risk_level: Optional[AuditSeverity] = None
    risk_factors: Optional[List[str]] = None
    mitigation_actions: Optional[List[str]] = None


class ConsentAuditLogResponse(ConsentAuditLogBase):
    """Model for consent audit log API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    consent_record_id: Optional[uuid.UUID] = None
    data_subject_id: Optional[uuid.UUID] = None
    event_timestamp: datetime
    actor_id: uuid.UUID
    actor_type: str
    actor_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DataProcessingAuditBase(BaseModel):
    """Base data processing audit model."""

    processing_purpose: DataProcessingPurpose
    data_categories: List[str] = []
    data_volume: Optional[int] = None
    data_sensitivity: AuditSeverity = AuditSeverity.MEDIUM
    processing_method: str = Field(..., min_length=1)
    processing_location: Optional[str] = None
    processing_tools: List[str] = []
    third_parties_involved: List[Dict[str, Any]] = []
    data_shared_with: List[Dict[str, Any]] = []
    legal_basis: str = Field(..., min_length=1)
    data_encrypted: bool = True
    access_controls: List[str] = []
    retention_period: Optional[int] = None


class DataProcessingAuditCreate(DataProcessingAuditBase):
    """Model for data processing audit creation."""

    user_id: uuid.UUID
    consent_record_id: Optional[uuid.UUID] = None
    data_subject_id: Optional[uuid.UUID] = None
    processing_duration: Optional[int] = None
    consent_verified: bool = False
    consent_verification_method: Optional[str] = None


class DataProcessingAuditUpdate(BaseModel):
    """Model for data processing audit updates."""

    compliance_status: Optional[ComplianceStatus] = None
    processing_duration: Optional[int] = None
    consent_verified: Optional[bool] = None
    consent_verification_method: Optional[str] = None


class DataProcessingAuditResponse(DataProcessingAuditBase):
    """Model for data processing audit API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    consent_record_id: Optional[uuid.UUID] = None
    data_subject_id: Optional[uuid.UUID] = None
    processing_timestamp: datetime
    processing_duration: Optional[int] = None
    consent_verified: bool
    consent_verification_method: Optional[str] = None
    compliance_status: ComplianceStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplianceReportBase(BaseModel):
    """Base compliance report model."""

    report_type: str = Field(..., min_length=1)
    report_period_start: datetime
    report_period_end: datetime
    scope_description: str = Field(..., min_length=1)
    executive_summary: Optional[str] = None
    detailed_findings: Dict[str, Any] = {}
    recommendations: List[str] = []
    action_items: List[str] = []


class ComplianceReportCreate(ComplianceReportBase):
    """Model for compliance report creation."""

    user_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    framework: Optional[str] = None


class ComplianceReportUpdate(BaseModel):
    """Model for compliance report updates."""

    report_status: Optional[str] = None
    executive_summary: Optional[str] = None
    detailed_findings: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    gdpr_compliance_score: Optional[int] = Field(None, ge=0, le=100)
    hipaa_compliance_score: Optional[int] = Field(None, ge=0, le=100)
    overall_compliance_score: Optional[int] = Field(None, ge=0, le=100)


class ComplianceReportResponse(ComplianceReportBase):
    """Model for compliance report API responses."""

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    framework: Optional[str] = None
    report_status: str
    total_consents: int
    active_consents: int
    expired_consents: int
    withdrawn_consents: int
    compliance_violations: int
    security_incidents: int
    data_breaches: int
    data_processing_events: int
    data_sharing_events: int
    data_access_events: int
    gdpr_compliance_score: Optional[int] = None
    hipaa_compliance_score: Optional[int] = None
    overall_compliance_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConsentRecordCreate(BaseModel):
    """Model for consent record creation."""

    user_id: uuid.UUID
    consent_type: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    granted: bool = True
    expires_at: Optional[datetime] = None
    version: Optional[str] = None


class ConsentRecordResponse(BaseModel):
    """Model for consent record API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    consent_type: str
    purpose: str
    granted: bool
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditSummary(BaseModel):
    """Model for audit summary statistics."""

    total_events: int
    compliant_events: int
    non_compliant_events: int
    high_risk_events: int
    critical_events: int
    gdpr_violations: int
    hipaa_violations: int
    security_incidents: int
    data_breaches: int
    period_start: datetime
    period_end: datetime
    compliance_score: float = Field(..., ge=0, le=100)

    class Config:
        from_attributes = True
