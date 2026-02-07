"""
Lab Results Models
Pydantic models for laboratory test results and clinical chemistry data.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator
from common.models.base import BaseModel as DBBaseModel


class LabResultBase(BaseModel):
    """Base model for lab results with common fields."""
    
    test_name: str = Field(..., description="Name of the laboratory test")
    test_code: Optional[str] = Field(None, description="LOINC code for the test")
    value: Optional[Decimal] = Field(None, description="Test result value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range_low: Optional[Decimal] = Field(None, description="Lower bound of reference range")
    reference_range_high: Optional[Decimal] = Field(None, description="Upper bound of reference range")
    reference_range_text: Optional[str] = Field(None, description="Text description of reference range")
    abnormal: bool = Field(False, description="Whether the result is abnormal")
    critical: bool = Field(False, description="Whether the result is critical")
    test_date: datetime = Field(..., description="Date when the test was performed")
    result_date: Optional[datetime] = Field(None, description="Date when the result was available")
    lab_name: Optional[str] = Field(None, description="Name of the laboratory")
    ordering_provider: Optional[str] = Field(None, description="Name of the ordering provider")
    specimen_type: Optional[str] = Field(None, description="Type of specimen collected")
    status: str = Field("final", description="Status of the result (preliminary, final, corrected, cancelled)")
    source: str = Field("manual", description="Source of the data (manual, fhir, ocr, epic, cerner)")
    external_id: Optional[str] = Field(None, description="External system ID (Epic MRN, etc.)")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR Observation ID")
    record_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('value', 'reference_range_low', 'reference_range_high', pre=True)
    def validate_decimal(cls, v):
        """Convert string to Decimal if needed."""
        if v is not None and isinstance(v, str):
            try:
                return Decimal(v)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid decimal value: {v}")
        return v

    @validator('test_date', 'result_date', pre=True)
    def validate_datetime(cls, v):
        """Convert string to datetime if needed."""
        if v is not None and isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid datetime value: {v}")
        return v


class LabResultCreate(LabResultBase):
    """Model for creating a new lab result."""
    
    patient_id: UUID = Field(..., description="ID of the patient")


class LabResultUpdate(BaseModel):
    """Model for updating an existing lab result."""
    
    test_name: Optional[str] = Field(None, description="Name of the laboratory test")
    test_code: Optional[str] = Field(None, description="LOINC code for the test")
    value: Optional[Decimal] = Field(None, description="Test result value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range_low: Optional[Decimal] = Field(None, description="Lower bound of reference range")
    reference_range_high: Optional[Decimal] = Field(None, description="Upper bound of reference range")
    reference_range_text: Optional[str] = Field(None, description="Text description of reference range")
    abnormal: Optional[bool] = Field(None, description="Whether the result is abnormal")
    critical: Optional[bool] = Field(None, description="Whether the result is critical")
    test_date: Optional[datetime] = Field(None, description="Date when the test was performed")
    result_date: Optional[datetime] = Field(None, description="Date when the result was available")
    lab_name: Optional[str] = Field(None, description="Name of the laboratory")
    ordering_provider: Optional[str] = Field(None, description="Name of the ordering provider")
    specimen_type: Optional[str] = Field(None, description="Type of specimen collected")
    status: Optional[str] = Field(None, description="Status of the result")
    source: Optional[str] = Field(None, description="Source of the data")
    external_id: Optional[str] = Field(None, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR Observation ID")
    record_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('value', 'reference_range_low', 'reference_range_high', pre=True)
    def validate_decimal(cls, v):
        """Convert string to Decimal if needed."""
        if v is not None and isinstance(v, str):
            try:
                return Decimal(v)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid decimal value: {v}")
        return v

    @validator('test_date', 'result_date', pre=True)
    def validate_datetime(cls, v):
        """Convert string to datetime if needed."""
        if v is not None and isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid datetime value: {v}")
        return v


class LabResult(LabResultBase):
    """Complete lab result model with database fields."""
    
    id: UUID = Field(..., description="Unique identifier")
    patient_id: UUID = Field(..., description="ID of the patient")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class LabResultResponse(BaseModel):
    """Response model for lab results."""
    
    id: str = Field(..., description="Unique identifier")
    patient_id: str = Field(..., description="ID of the patient")
    test_name: str = Field(..., description="Name of the laboratory test")
    test_code: Optional[str] = Field(None, description="LOINC code for the test")
    value: Optional[str] = Field(None, description="Test result value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range_low: Optional[str] = Field(None, description="Lower bound of reference range")
    reference_range_high: Optional[str] = Field(None, description="Upper bound of reference range")
    reference_range_text: Optional[str] = Field(None, description="Text description of reference range")
    abnormal: bool = Field(..., description="Whether the result is abnormal")
    critical: bool = Field(..., description="Whether the result is critical")
    test_date: str = Field(..., description="Date when the test was performed")
    result_date: Optional[str] = Field(None, description="Date when the result was available")
    lab_name: Optional[str] = Field(None, description="Name of the laboratory")
    ordering_provider: Optional[str] = Field(None, description="Name of the ordering provider")
    specimen_type: Optional[str] = Field(None, description="Type of specimen collected")
    status: str = Field(..., description="Status of the result")
    source: str = Field(..., description="Source of the data")
    external_id: Optional[str] = Field(None, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR Observation ID")
    record_metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    @classmethod
    def from_orm(cls, obj):
        """Create response model from ORM object."""
        return cls(
            id=str(obj.id),
            patient_id=str(obj.patient_id),
            test_name=obj.test_name,
            test_code=obj.test_code,
            value=str(obj.value) if obj.value is not None else None,
            unit=obj.unit,
            reference_range_low=str(obj.reference_range_low) if obj.reference_range_low is not None else None,
            reference_range_high=str(obj.reference_range_high) if obj.reference_range_high is not None else None,
            reference_range_text=obj.reference_range_text,
            abnormal=obj.abnormal,
            critical=obj.critical,
            test_date=obj.test_date.isoformat(),
            result_date=obj.result_date.isoformat() if obj.result_date else None,
            lab_name=obj.lab_name,
            ordering_provider=obj.ordering_provider,
            specimen_type=obj.specimen_type,
            status=obj.status,
            source=obj.source,
            external_id=obj.external_id,
            fhir_resource_id=obj.fhir_resource_id,
            record_metadata=obj.record_metadata,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat()
        )


class LabResultListResponse(BaseModel):
    """Response model for list of lab results."""
    
    items: list[LabResultResponse] = Field(..., description="List of lab results")
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class LabResultSummary(BaseModel):
    """Summary model for lab results."""
    
    total_count: int = Field(..., description="Total number of lab results")
    abnormal_count: int = Field(..., description="Number of abnormal results")
    critical_count: int = Field(..., description="Number of critical results")
    latest_date: Optional[str] = Field(None, description="Date of most recent result")
    test_types: list[str] = Field(..., description="List of test types")
    sources: list[str] = Field(..., description="List of data sources") 