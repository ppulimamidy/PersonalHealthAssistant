"""
Document Schemas
Pydantic models for medical document data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    """Medical document types."""
    LAB_REPORT = "LAB_REPORT"
    IMAGING_REPORT = "IMAGING_REPORT"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    PRESCRIPTION = "PRESCRIPTION"
    REFERRAL = "REFERRAL"
    CONSENT_FORM = "CONSENT_FORM"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    OPERATION_REPORT = "OPERATION_REPORT"
    PATHOLOGY_REPORT = "PATHOLOGY_REPORT"
    OTHER = "OTHER"


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


# Document Schemas
class DocumentCreate(BaseModel):
    """Schema for creating a medical document."""
    patient_id: UUID = Field(..., description="Patient ID")
    document_type: DocumentType = Field(..., description="Document type")
    document_name: str = Field(..., min_length=1, max_length=255, description="Document name")
    document_description: Optional[str] = Field(None, max_length=1000, description="Document description")
    document_date: Optional[datetime] = Field(None, description="Document date")
    author: Optional[str] = Field(None, max_length=255, description="Document author")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    document_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional document metadata")


class DocumentUpdate(BaseModel):
    """Schema for updating a medical document."""
    document_type: Optional[DocumentType] = Field(None, description="Document type")
    document_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Document name")
    document_description: Optional[str] = Field(None, max_length=1000, description="Document description")
    document_date: Optional[datetime] = Field(None, description="Document date")
    author: Optional[str] = Field(None, max_length=255, description="Document author")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    document_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional document metadata")


class DocumentResponse(BaseModel):
    """Schema for medical document response."""
    id: UUID = Field(..., description="Document ID")
    patient_id: UUID = Field(..., description="Patient ID")
    document_type: DocumentType = Field(..., description="Document type")
    document_name: str = Field(..., description="Document name")
    document_description: Optional[str] = Field(None, description="Document description")
    document_date: Optional[datetime] = Field(None, description="Document date")
    author: Optional[str] = Field(None, description="Document author")
    file_path: Optional[str] = Field(None, description="File path on storage")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    ocr_text: Optional[str] = Field(None, description="OCR extracted text")
    ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="OCR confidence score")
    processing_status: DocumentStatus = Field(..., description="Processing status")
    external_id: Optional[str] = Field(None, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")
    document_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for medical document list response."""
    documents: List[DocumentResponse] = Field(..., description="List of medical documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages") 