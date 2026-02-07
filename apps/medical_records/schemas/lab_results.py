"""
Lab Results Schemas
Pydantic models for laboratory test result data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator


class LabResultType(str, Enum):
    """Laboratory test result types."""
    BLOOD_TEST = "BLOOD_TEST"
    URINE_TEST = "URINE_TEST"
    STOOL_TEST = "STOOL_TEST"
    CULTURE_TEST = "CULTURE_TEST"
    GENETIC_TEST = "GENETIC_TEST"
    TOXICOLOGY_TEST = "TOXICOLOGY_TEST"
    MICROBIOLOGY_TEST = "MICROBIOLOGY_TEST"
    IMMUNOLOGY_TEST = "IMMUNOLOGY_TEST"
    OTHER = "OTHER"


class LabResultStatus(str, Enum):
    """Laboratory test result status."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


# Lab Result Schemas
class LabResultCreate(BaseModel):
    """Schema for creating a laboratory test result."""
    patient_id: UUID = Field(..., description="Patient ID")
    test_name: str = Field(..., min_length=1, max_length=255, description="Test name")
    test_type: LabResultType = Field(..., description="Test type")
    test_date: Optional[datetime] = Field(None, description="Test date")
    result_date: Optional[datetime] = Field(None, description="Result date")
    ordering_physician: Optional[str] = Field(None, max_length=255, description="Ordering physician")
    performing_lab: Optional[str] = Field(None, max_length=255, description="Performing laboratory")
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test results data")
    reference_ranges: Optional[Dict[str, Any]] = Field(None, description="Reference ranges")
    interpretation: Optional[str] = Field(None, max_length=2000, description="Result interpretation")
    clinical_notes: Optional[str] = Field(None, max_length=2000, description="Clinical notes")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    result_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional result metadata")


class LabResultUpdate(BaseModel):
    """Schema for updating a laboratory test result."""
    test_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Test name")
    test_type: Optional[LabResultType] = Field(None, description="Test type")
    test_date: Optional[datetime] = Field(None, description="Test date")
    result_date: Optional[datetime] = Field(None, description="Result date")
    ordering_physician: Optional[str] = Field(None, max_length=255, description="Ordering physician")
    performing_lab: Optional[str] = Field(None, max_length=255, description="Performing laboratory")
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test results data")
    reference_ranges: Optional[Dict[str, Any]] = Field(None, description="Reference ranges")
    interpretation: Optional[str] = Field(None, max_length=2000, description="Result interpretation")
    clinical_notes: Optional[str] = Field(None, max_length=2000, description="Clinical notes")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    result_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional result metadata")


class LabResultResponse(BaseModel):
    """Schema for laboratory test result response."""
    id: UUID = Field(..., description="Result ID")
    patient_id: UUID = Field(..., description="Patient ID")
    test_name: str = Field(..., description="Test name")
    test_type: LabResultType = Field(..., description="Test type")
    test_date: Optional[datetime] = Field(None, description="Test date")
    result_date: Optional[datetime] = Field(None, description="Result date")
    ordering_physician: Optional[str] = Field(None, description="Ordering physician")
    performing_lab: Optional[str] = Field(None, description="Performing laboratory")
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test results data")
    reference_ranges: Optional[Dict[str, Any]] = Field(None, description="Reference ranges")
    interpretation: Optional[str] = Field(None, description="Result interpretation")
    clinical_notes: Optional[str] = Field(None, description="Clinical notes")
    result_status: LabResultStatus = Field(..., description="Result status")
    external_id: Optional[str] = Field(None, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")
    result_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional result metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class LabResultListResponse(BaseModel):
    """Schema for laboratory test result list response."""
    results: List[LabResultResponse] = Field(..., description="List of laboratory test results")
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages") 