"""
Audit models for the Personal Health Assistant Consent Audit Service.

This module defines comprehensive audit models for consent tracking,
GDPR compliance, HIPAA validation, and data processing audits.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid

from common.models.base import Base


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


# Pydantic models for API responses (no SQLAlchemy models for now)
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