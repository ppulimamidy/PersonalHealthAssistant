"""
Document Models for Medical Records
Handles document uploads, OCR processing, and metadata management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from common.models.base import Base


class DocumentType(str, Enum):
    """Document type enumeration."""
    LAB_REPORT = "lab_report"
    IMAGING_REPORT = "imaging_report"
    CLINICAL_NOTE = "clinical_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    OPERATIVE_REPORT = "operative_report"
    PROGRESS_NOTE = "progress_note"
    SOAP_NOTE = "soap_note"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    CONSULTATION = "consultation"
    PATHOLOGY_REPORT = "pathology_report"
    RADIOLOGY_REPORT = "radiology_report"
    EKG_REPORT = "ekg_report"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETED = "ocr_completed"
    METADATA_EXTRACTED = "metadata_extracted"
    VALIDATED = "validated"
    ERROR = "error"


class ProcessingStatus(str, Enum):
    """OCR and processing status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Pydantic Models for API
class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    patient_id: UUID
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    source: Optional[str] = "manual"  # manual, fhir, hl7, ocr
    external_id: Optional[str] = None
    fhir_resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentCreate(BaseModel):
    """Create model for documents."""
    patient_id: UUID
    document_type: DocumentType
    title: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: str = "manual"
    external_id: Optional[str] = None
    fhir_resource_id: Optional[str] = None
    document_document_metadata: Dict[str, Any] = Field(default_factory=dict)
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    document_status: DocumentStatus = DocumentStatus.UPLOADED


class DocumentUpdate(BaseModel):
    """Update model for documents."""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    document_metadata: Optional[Dict[str, Any]] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_status: Optional[ProcessingStatus] = None
    document_status: Optional[DocumentStatus] = None


class DocumentResponse(BaseModel):
    """Response model for documents."""
    id: UUID
    patient_id: UUID
    document_type: DocumentType
    title: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    tags: List[str]
    source: str
    external_id: Optional[str] = None
    fhir_resource_id: Optional[str] = None
    document_metadata: Dict[str, Any]
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_status: ProcessingStatus
    document_status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document lists."""
    items: List[DocumentResponse]
    total: int
    page: int
    size: int
    pages: int


# SQLAlchemy Models
class DocumentDB(Base):
    """Database model for medical documents."""
    __tablename__ = "documents"
    __table_args__ = {"schema": "medical_records"}

    # Primary key
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Document metadata
    patient_id: UUID = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    document_type: DocumentType = Column(SQLEnum(DocumentType), nullable=False, index=True)
    title: str = Column(String(500), nullable=False)
    content: Optional[str] = Column(Text)
    
    # File information
    file_path: Optional[str] = Column(String(1000))
    file_url: Optional[str] = Column(String(1000))
    file_size: Optional[int] = Column(String(50))
    mime_type: Optional[str] = Column(String(100))
    
    # Processing information
    tags: List[str] = Column(JSON, default=list)
    source: str = Column(String(50), default="manual", index=True)
    external_id: Optional[str] = Column(String(255), index=True)
    fhir_resource_id: Optional[str] = Column(String(255))
    document_document_metadata: Dict[str, Any] = Column(JSON, default=dict)
    
    # OCR information
    ocr_text: Optional[str] = Column(Text)
    ocr_confidence: Optional[float] = Column(String(10))
    processing_status: ProcessingStatus = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    document_status: DocumentStatus = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentProcessingLogDB(Base):
    """Database model for document processing logs."""
    __tablename__ = "document_processing_logs"
    __table_args__ = {"schema": "medical_records"}

    # Primary key
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to document
    document_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("medical_records.documents.id"), nullable=False)
    
    # Processing information
    step: str = Column(String(100), nullable=False)  # upload, ocr, metadata_extraction, validation
    status: ProcessingStatus = Column(SQLEnum(ProcessingStatus), nullable=False)
    message: Optional[str] = Column(Text)
    error_details: Optional[str] = Column(Text)
    processing_time_ms: Optional[int] = Column(String(20))
    document_document_metadata: Dict[str, Any] = Column(JSON, default=dict)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
