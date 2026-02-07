"""
Clinical Reports Schemas
Pydantic models for clinical reports data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator, model_validator

from apps.medical_records.models.clinical_reports import (
    ReportType, ReportStatus, ReportPriority, ReportCategory, ReportTemplate
)


# Clinical Report Schemas
class ClinicalReportCreate(BaseModel):
    """Schema for creating a clinical report."""
    patient_id: UUID = Field(..., description="Patient ID")
    title: str = Field(..., min_length=1, max_length=500, description="Report title")
    report_type: ReportType = Field(..., description="Type of clinical report")
    category: ReportCategory = Field(..., description="Report category")
    template: ReportTemplate = Field(ReportTemplate.FREE_TEXT, description="Report template")
    
    # Content
    content: str = Field(..., min_length=1, description="Report content")
    summary: Optional[str] = Field(None, max_length=2000, description="Report summary")
    keywords: Optional[List[str]] = Field(None, description="Keywords for search")
    
    # Status and workflow
    status: ReportStatus = Field(ReportStatus.DRAFT, description="Report status")
    priority: ReportPriority = Field(ReportPriority.NORMAL, description="Report priority")
    is_confidential: bool = Field(False, description="Confidentiality flag")
    requires_review: bool = Field(False, description="Review requirement flag")
    
    # Versioning
    parent_report_id: Optional[UUID] = Field(None, description="Parent report ID for versioning")
    
    # Dates
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    
    # External references
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    source_system: Optional[str] = Field(None, max_length=100, description="Source system")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Report tags")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Attachments")
    report_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError("Maximum 50 keywords allowed")
            if any(len(kw) > 100 for kw in v):
                raise ValueError("Keywords must be 100 characters or less")
        return v

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            if any(len(tag) > 50 for tag in v):
                raise ValueError("Tags must be 50 characters or less")
        return v

    @model_validator(mode='after')
    def validate_dates(self):
        effective_date = self.effective_date
        expiry_date = self.expiry_date
        
        if effective_date and expiry_date and effective_date >= expiry_date:
            raise ValueError("Effective date must be before expiry date")
        
        return self


class ClinicalReportUpdate(BaseModel):
    """Schema for updating a clinical report."""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Report title")
    report_type: Optional[ReportType] = Field(None, description="Type of clinical report")
    category: Optional[ReportCategory] = Field(None, description="Report category")
    template: Optional[ReportTemplate] = Field(None, description="Report template")
    
    # Content
    content: Optional[str] = Field(None, min_length=1, description="Report content")
    summary: Optional[str] = Field(None, max_length=2000, description="Report summary")
    keywords: Optional[List[str]] = Field(None, description="Keywords for search")
    
    # Status and workflow
    status: Optional[ReportStatus] = Field(None, description="Report status")
    priority: Optional[ReportPriority] = Field(None, description="Report priority")
    is_confidential: Optional[bool] = Field(None, description="Confidentiality flag")
    requires_review: Optional[bool] = Field(None, description="Review requirement flag")
    
    # Dates
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    
    # External references
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    source_system: Optional[str] = Field(None, max_length=100, description="Source system")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Report tags")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Attachments")
    report_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('keywords')
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError("Maximum 50 keywords allowed")
            if any(len(kw) > 100 for kw in v):
                raise ValueError("Keywords must be 100 characters or less")
        return v

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            if any(len(tag) > 50 for tag in v):
                raise ValueError("Tags must be 50 characters or less")
        return v


class ClinicalReportResponse(BaseModel):
    """Schema for clinical report response."""
    id: UUID = Field(..., description="Report ID")
    patient_id: UUID = Field(..., description="Patient ID")
    author_id: UUID = Field(..., description="Author ID")
    reviewer_id: Optional[UUID] = Field(None, description="Reviewer ID")
    
    # Report identification
    title: str = Field(..., description="Report title")
    report_type: ReportType = Field(..., description="Type of clinical report")
    category: ReportCategory = Field(..., description="Report category")
    template: ReportTemplate = Field(..., description="Report template")
    
    # Content
    content: str = Field(..., description="Report content")
    summary: Optional[str] = Field(None, description="Report summary")
    keywords: Optional[List[str]] = Field(None, description="Keywords for search")
    
    # Status and workflow
    status: ReportStatus = Field(..., description="Report status")
    priority: ReportPriority = Field(..., description="Report priority")
    is_confidential: bool = Field(..., description="Confidentiality flag")
    requires_review: bool = Field(..., description="Review requirement flag")
    
    # Versioning
    version: int = Field(..., description="Report version")
    parent_report_id: Optional[UUID] = Field(None, description="Parent report ID")
    is_latest_version: bool = Field(..., description="Latest version flag")
    version_count: int = Field(0, description="Total number of versions")
    
    # Dates
    created_date: datetime = Field(..., description="Creation date")
    modified_date: datetime = Field(..., description="Last modification date")
    reviewed_date: Optional[datetime] = Field(None, description="Review date")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    
    # External references
    external_id: Optional[str] = Field(None, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")
    source_system: Optional[str] = Field(None, description="Source system")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Report tags")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Attachments")
    report_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ClinicalReportListResponse(BaseModel):
    """Schema for clinical report list response."""
    reports: List[ClinicalReportResponse] = Field(..., description="List of clinical reports")
    total: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Report Version Schemas
class ReportVersionResponse(BaseModel):
    """Schema for report version response."""
    id: UUID = Field(..., description="Version ID")
    report_id: UUID = Field(..., description="Report ID")
    version_number: int = Field(..., description="Version number")
    
    # Version content
    content: str = Field(..., description="Version content")
    summary: Optional[str] = Field(None, description="Version summary")
    changes_summary: Optional[str] = Field(None, description="Changes summary")
    
    # Version metadata
    author_id: UUID = Field(..., description="Author ID")
    created_date: datetime = Field(..., description="Creation date")
    version_metadata: Optional[Dict[str, Any]] = Field(None, description="Version metadata")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ReportVersionListResponse(BaseModel):
    """Schema for report version list response."""
    versions: List[ReportVersionResponse] = Field(..., description="List of report versions")
    total: int = Field(..., description="Total number of versions")
    current_version: int = Field(..., description="Current version number")


# Report Template Schemas
class ReportTemplateCreate(BaseModel):
    """Schema for creating a report template."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    version: str = Field(..., min_length=1, max_length=50, description="Template version")
    template_type: ReportTemplate = Field(..., description="Template type")
    category: ReportCategory = Field(..., description="Template category")
    
    # Template content
    template_content: str = Field(..., min_length=1, description="Template content")
    template_schema: Optional[Dict[str, Any]] = Field(None, description="Template schema")
    default_values: Optional[Dict[str, Any]] = Field(None, description="Default values")
    
    # Template metadata
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    is_system_template: bool = Field(False, description="System template flag")


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    template_type: Optional[ReportTemplate] = Field(None, description="Template type")
    category: Optional[ReportCategory] = Field(None, description="Template category")
    
    # Template content
    template_content: Optional[str] = Field(None, min_length=1, description="Template content")
    template_schema: Optional[Dict[str, Any]] = Field(None, description="Template schema")
    default_values: Optional[Dict[str, Any]] = Field(None, description="Default values")
    
    # Template metadata
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    is_active: Optional[bool] = Field(None, description="Active status")


class ReportTemplateResponse(BaseModel):
    """Schema for report template response."""
    id: UUID = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    version: str = Field(..., description="Template version")
    template_type: ReportTemplate = Field(..., description="Template type")
    category: ReportCategory = Field(..., description="Template category")
    
    # Template content
    template_content: str = Field(..., description="Template content")
    template_schema: Optional[Dict[str, Any]] = Field(None, description="Template schema")
    default_values: Optional[Dict[str, Any]] = Field(None, description="Default values")
    
    # Template metadata
    description: Optional[str] = Field(None, description="Template description")
    author_id: UUID = Field(..., description="Author ID")
    is_active: bool = Field(..., description="Active status")
    is_system_template: bool = Field(..., description="System template flag")
    
    # Usage tracking
    usage_count: int = Field(..., description="Usage count")
    last_used_date: Optional[datetime] = Field(None, description="Last used date")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ReportTemplateListResponse(BaseModel):
    """Schema for report template list response."""
    templates: List[ReportTemplateResponse] = Field(..., description="List of report templates")
    total: int = Field(..., description="Total number of templates")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Report Category Schemas
class ReportCategoryCreate(BaseModel):
    """Schema for creating a report category."""
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    parent_id: Optional[UUID] = Field(None, description="Parent category ID")
    
    # Category metadata
    color_code: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    icon_name: Optional[str] = Field(None, max_length=100, description="Icon name")
    sort_order: int = Field(0, description="Sort order")


class ReportCategoryUpdate(BaseModel):
    """Schema for updating a report category."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    parent_id: Optional[UUID] = Field(None, description="Parent category ID")
    
    # Category metadata
    color_code: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    icon_name: Optional[str] = Field(None, max_length=100, description="Icon name")
    sort_order: Optional[int] = Field(None, description="Sort order")
    is_active: Optional[bool] = Field(None, description="Active status")


class ReportCategoryResponse(BaseModel):
    """Schema for report category response."""
    id: UUID = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[UUID] = Field(None, description="Parent category ID")
    
    # Category metadata
    color_code: Optional[str] = Field(None, description="Hex color code")
    icon_name: Optional[str] = Field(None, description="Icon name")
    sort_order: int = Field(..., description="Sort order")
    is_active: bool = Field(..., description="Active status")
    
    # Usage tracking
    report_count: int = Field(..., description="Report count")
    
    # Relationships
    subcategories: List["ReportCategoryResponse"] = Field([], description="Subcategories")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ReportCategoryListResponse(BaseModel):
    """Schema for report category list response."""
    categories: List[ReportCategoryResponse] = Field(..., description="List of report categories")
    total: int = Field(..., description="Total number of categories")


# Report Audit Log Schemas
class ReportAuditLogResponse(BaseModel):
    """Schema for report audit log response."""
    id: UUID = Field(..., description="Audit log ID")
    report_id: UUID = Field(..., description="Report ID")
    user_id: UUID = Field(..., description="User ID")
    
    # Audit details
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(..., description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    # Change details
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    changes_summary: Optional[str] = Field(None, description="Changes summary")
    
    # Context
    session_id: Optional[str] = Field(None, description="Session ID")
    request_id: Optional[str] = Field(None, description="Request ID")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class ReportAuditLogListResponse(BaseModel):
    """Schema for report audit log list response."""
    audit_logs: List[ReportAuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of audit logs")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Search and Filter Schemas
class ReportSearchRequest(BaseModel):
    """Schema for report search request."""
    query: Optional[str] = Field(None, description="Search query")
    patient_id: Optional[UUID] = Field(None, description="Patient ID filter")
    report_type: Optional[ReportType] = Field(None, description="Report type filter")
    category: Optional[ReportCategory] = Field(None, description="Category filter")
    status: Optional[ReportStatus] = Field(None, description="Status filter")
    priority: Optional[ReportPriority] = Field(None, description="Priority filter")
    author_id: Optional[UUID] = Field(None, description="Author ID filter")
    tags: Optional[List[str]] = Field(None, description="Tags filter")
    date_from: Optional[datetime] = Field(None, description="Date from")
    date_to: Optional[datetime] = Field(None, description="Date to")
    is_confidential: Optional[bool] = Field(None, description="Confidentiality filter")
    requires_review: Optional[bool] = Field(None, description="Review requirement filter")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    sort_by: str = Field("created_date", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class ReportStatisticsResponse(BaseModel):
    """Schema for report statistics response."""
    total_reports: int = Field(..., description="Total number of reports")
    reports_by_type: Dict[str, int] = Field(..., description="Reports by type")
    reports_by_status: Dict[str, int] = Field(..., description="Reports by status")
    reports_by_category: Dict[str, int] = Field(..., description="Reports by category")
    reports_by_priority: Dict[str, int] = Field(..., description="Reports by priority")
    reports_by_month: Dict[str, int] = Field(..., description="Reports by month")
    average_versions_per_report: float = Field(..., description="Average versions per report")
    reports_requiring_review: int = Field(..., description="Reports requiring review")
    confidential_reports: int = Field(..., description="Confidential reports count") 