"""Clinical reports models for medical records."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, ForeignKey, 
    JSON, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, ENUM
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

from common.models.base import Base


class ReportType(str, Enum):
    """Types of clinical reports."""
    CLINICAL_NOTE = "CLINICAL_NOTE"
    PROGRESS_NOTE = "PROGRESS_NOTE"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    CONSULTATION_NOTE = "CONSULTATION_NOTE"
    OPERATION_REPORT = "OPERATION_REPORT"
    PATHOLOGY_REPORT = "PATHOLOGY_REPORT"
    RADIOLOGY_REPORT = "RADIOLOGY_REPORT"
    LABORATORY_REPORT = "LABORATORY_REPORT"
    MEDICATION_REVIEW = "MEDICATION_REVIEW"
    ALLERGY_ASSESSMENT = "ALLERGY_ASSESSMENT"
    VITAL_SIGNS_REPORT = "VITAL_SIGNS_REPORT"
    TREATMENT_PLAN = "TREATMENT_PLAN"
    CARE_PLAN = "CARE_PLAN"
    REFERRAL_LETTER = "REFERRAL_LETTER"
    CONSENT_FORM = "CONSENT_FORM"
    ADVANCE_DIRECTIVE = "ADVANCE_DIRECTIVE"
    OTHER = "OTHER"


class ReportStatus(str, Enum):
    """Status of clinical reports."""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"
    RETRACTED = "RETRACTED"


class ReportPriority(str, Enum):
    """Priority levels for clinical reports."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class ReportCategory(str, Enum):
    """Categories for clinical reports."""
    ADMISSION = "ADMISSION"
    DISCHARGE = "DISCHARGE"
    CONSULTATION = "CONSULTATION"
    PROCEDURE = "PROCEDURE"
    DIAGNOSTIC = "DIAGNOSTIC"
    THERAPEUTIC = "THERAPEUTIC"
    MONITORING = "MONITORING"
    EDUCATION = "EDUCATION"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    LEGAL = "LEGAL"
    RESEARCH = "RESEARCH"
    OTHER = "OTHER"


class ReportTemplate(str, Enum):
    """Standard report templates."""
    SOAP_NOTE = "SOAP_NOTE"
    PROBLEM_ORIENTED = "PROBLEM_ORIENTED"
    NARRATIVE = "NARRATIVE"
    STRUCTURED = "STRUCTURED"
    TEMPLATE_BASED = "TEMPLATE_BASED"
    FREE_TEXT = "FREE_TEXT"


class ClinicalReportDB(Base):
    """Clinical report database model."""
    __tablename__ = "clinical_reports"
    __table_args__ = (
        Index('ix_clinical_reports_patient_id', 'patient_id'),
        Index('ix_clinical_reports_author_id', 'author_id'),
        Index('ix_clinical_reports_report_type', 'report_type'),
        Index('ix_clinical_reports_status', 'status'),
        Index('ix_clinical_reports_category', 'category'),
        Index('ix_clinical_reports_created_date', 'created_date'),
        Index('ix_clinical_reports_priority', 'priority'),
        Index('ix_clinical_reports_external_id', 'external_id'),
        UniqueConstraint('patient_id', 'external_id', name='uq_clinical_reports_patient_external'),
        {"schema": "medical_records"},
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    author_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    reviewer_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Report identification
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(ENUM(ReportType), nullable=False)
    category: Mapped[ReportCategory] = mapped_column(ENUM(ReportCategory), nullable=False)
    template: Mapped[ReportTemplate] = mapped_column(ENUM(ReportTemplate), nullable=False)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Status and workflow
    status: Mapped[ReportStatus] = mapped_column(ENUM(ReportStatus), default=ReportStatus.DRAFT)
    priority: Mapped[ReportPriority] = mapped_column(ENUM(ReportPriority), default=ReportPriority.NORMAL)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_report_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    is_latest_version: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Dates
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # External references
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fhir_resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    attachments: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    report_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    versions: Mapped[List["ReportVersionDB"]] = relationship(
        "ReportVersionDB",
        backref="report",
        cascade="all, delete-orphan"
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportVersionDB(Base):
    """Report version tracking model."""
    __tablename__ = "report_versions"
    __table_args__ = (
        Index('ix_report_versions_report_id', 'report_id'),
        Index('ix_report_versions_version_number', 'version_number'),
        Index('ix_report_versions_created_date', 'created_date'),
        UniqueConstraint('report_id', 'version_number', name='uq_report_versions_report_version'),
        {"schema": "medical_records"},
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('medical_records.clinical_reports.id'), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Version content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changes_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Version metadata
    author_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    version_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportTemplateDB(Base):
    """Report template database model."""
    __tablename__ = "report_templates"
    __table_args__ = (
        Index('ix_report_templates_template_type', 'template_type'),
        Index('ix_report_templates_category', 'category'),
        Index('ix_report_templates_is_active', 'is_active'),
        UniqueConstraint('name', 'version', name='uq_report_templates_name_version'),
        {"schema": "medical_records"},
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    template_type: Mapped[ReportTemplate] = mapped_column(ENUM(ReportTemplate), nullable=False)
    category: Mapped[ReportCategory] = mapped_column(ENUM(ReportCategory), nullable=False)
    
    # Template content
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    template_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Template metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportCategoryDB(Base):
    """Report category management model."""
    __tablename__ = "report_categories"
    __table_args__ = (
        Index('ix_report_categories_parent_id', 'parent_id'),
        Index('ix_report_categories_is_active', 'is_active'),
        UniqueConstraint('name', 'parent_id', name='uq_report_categories_name_parent'),
        {"schema": "medical_records"},
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('medical_records.report_categories.id'), nullable=True)
    
    # Category metadata
    color_code: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Usage tracking
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    subcategories: Mapped[List["ReportCategoryDB"]] = relationship(
        "ReportCategoryDB",
        backref="parent_category",
        remote_side=[id]
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportAuditLogDB(Base):
    """Report audit logging model."""
    __tablename__ = "report_audit_logs"
    __table_args__ = (
        Index('ix_report_audit_logs_report_id', 'report_id'),
        Index('ix_report_audit_logs_user_id', 'user_id'),
        Index('ix_report_audit_logs_action', 'action'),
        Index('ix_report_audit_logs_timestamp', 'timestamp'),
        {"schema": "medical_records"},
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey('medical_records.clinical_reports.id'), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    
    # Audit details
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Change details
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    changes_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
