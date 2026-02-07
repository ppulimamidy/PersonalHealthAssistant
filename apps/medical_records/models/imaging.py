"""
Imaging Models for Medical Records
Handles medical imaging studies, DICOM files, and image metadata management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Enum as SQLEnum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from common.models.base import Base


class ModalityType(str, Enum):
    """Medical imaging modality types."""
    CT = "CT"  # Computed Tomography
    MRI = "MRI"  # Magnetic Resonance Imaging
    XRAY = "XRAY"  # X-Ray
    US = "US"  # Ultrasound
    PET = "PET"  # Positron Emission Tomography
    SPECT = "SPECT"  # Single Photon Emission Computed Tomography
    CR = "CR"  # Computed Radiography
    DX = "DX"  # Digital Radiography
    MG = "MG"  # Mammography
    NM = "NM"  # Nuclear Medicine
    OT = "OT"  # Other


class BodyPartType(str, Enum):
    """Anatomical body parts for imaging studies."""
    HEAD = "HEAD"
    NECK = "NECK"
    CHEST = "CHEST"
    ABDOMEN = "ABDOMEN"
    PELVIS = "PELVIS"
    SPINE = "SPINE"
    UPPER_EXTREMITY = "UPPER_EXTREMITY"
    LOWER_EXTREMITY = "LOWER_EXTREMITY"
    HEART = "HEART"
    LUNG = "LUNG"
    LIVER = "LIVER"
    KIDNEY = "KIDNEY"
    BRAIN = "BRAIN"
    BREAST = "BREAST"
    PROSTATE = "PROSTATE"
    UTERUS = "UTERUS"
    OTHER = "OTHER"


class StudyStatus(str, Enum):
    """Imaging study status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ImageFormat(str, Enum):
    """Image file formats."""
    DICOM = "dicom"
    JPEG = "jpeg"
    PNG = "png"
    TIFF = "tiff"
    BMP = "bmp"
    GIF = "gif"


class ImageQuality(str, Enum):
    """Image quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DIAGNOSTIC = "diagnostic"


# Pydantic Models for API
class ImagingStudyCreate(BaseModel):
    """Create model for imaging studies."""
    patient_id: UUID
    study_name: str
    modality: ModalityType
    body_part: BodyPartType
    study_date: Optional[datetime] = None
    study_description: Optional[str] = None
    referring_physician: Optional[str] = None
    performing_physician: Optional[str] = None
    study_status: StudyStatus = StudyStatus.SCHEDULED
    study_notes: Optional[str] = None
    external_id: Optional[str] = None
    fhir_resource_id: Optional[str] = None
    study_metadata: Dict[str, Any] = Field(default_factory=dict)


class ImagingStudyUpdate(BaseModel):
    """Update model for imaging studies."""
    study_name: Optional[str] = None
    modality: Optional[ModalityType] = None
    body_part: Optional[BodyPartType] = None
    study_date: Optional[datetime] = None
    study_description: Optional[str] = None
    referring_physician: Optional[str] = None
    performing_physician: Optional[str] = None
    study_status: Optional[StudyStatus] = None
    study_notes: Optional[str] = None
    study_metadata: Optional[Dict[str, Any]] = None


class ImagingStudyResponse(BaseModel):
    """Response model for imaging studies."""
    id: UUID
    patient_id: UUID
    study_name: str
    modality: ModalityType
    body_part: BodyPartType
    study_date: Optional[datetime]
    study_description: Optional[str]
    referring_physician: Optional[str]
    performing_physician: Optional[str]
    study_status: StudyStatus
    study_notes: Optional[str]
    external_id: Optional[str]
    fhir_resource_id: Optional[str]
    study_metadata: Dict[str, Any]
    image_count: int = 0
    total_size_bytes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicalImageCreate(BaseModel):
    """Create model for medical images."""
    study_id: UUID
    image_name: str
    image_format: ImageFormat
    image_quality: ImageQuality = ImageQuality.DIAGNOSTIC
    image_description: Optional[str] = None
    image_metadata: Dict[str, Any] = Field(default_factory=dict)
    dicom_metadata: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    width_pixels: Optional[int] = None
    height_pixels: Optional[int] = None
    bit_depth: Optional[int] = None
    color_space: Optional[str] = None


class MedicalImageUpdate(BaseModel):
    """Update model for medical images."""
    image_name: Optional[str] = None
    image_description: Optional[str] = None
    image_metadata: Optional[Dict[str, Any]] = None
    dicom_metadata: Optional[Dict[str, Any]] = None


class MedicalImageResponse(BaseModel):
    """Response model for medical images."""
    id: UUID
    study_id: UUID
    image_name: str
    image_format: ImageFormat
    image_quality: ImageQuality
    image_description: Optional[str]
    image_metadata: Dict[str, Any]
    dicom_metadata: Optional[Dict[str, Any]]
    file_path: Optional[str]
    file_url: Optional[str]
    file_size_bytes: Optional[int]
    width_pixels: Optional[int]
    height_pixels: Optional[int]
    bit_depth: Optional[int]
    color_space: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImagingStudyListResponse(BaseModel):
    """Response model for imaging study lists."""
    items: List[ImagingStudyResponse]
    total: int
    page: int
    size: int
    pages: int


class MedicalImageListResponse(BaseModel):
    """Response model for medical image lists."""
    items: List[MedicalImageResponse]
    total: int
    page: int
    size: int
    pages: int


# SQLAlchemy Models
class ImagingStudyDB(Base):
    """Database model for imaging studies."""
    __tablename__ = "imaging_studies"
    __table_args__ = {"schema": "medical_records"}

    # Primary key
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Study information
    patient_id: UUID = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    study_name: str = Column(String(500), nullable=False)
    modality: ModalityType = Column(SQLEnum(ModalityType), nullable=False, index=True)
    body_part: BodyPartType = Column(SQLEnum(BodyPartType), nullable=False, index=True)
    study_date: Optional[datetime] = Column(DateTime)
    study_description: Optional[str] = Column(Text)
    referring_physician: Optional[str] = Column(String(255))
    performing_physician: Optional[str] = Column(String(255))
    study_status: StudyStatus = Column(SQLEnum(StudyStatus), default=StudyStatus.SCHEDULED, index=True)
    study_notes: Optional[str] = Column(Text)
    
    # External references
    external_id: Optional[str] = Column(String(255), index=True)
    fhir_resource_id: Optional[str] = Column(String(255))
    study_metadata: Dict[str, Any] = Column(JSON, default=dict)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MedicalImageDB(Base):
    """Database model for medical images."""
    __tablename__ = "medical_images"
    __table_args__ = {"schema": "medical_records"}

    # Primary key
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to study
    study_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("medical_records.imaging_studies.id"), nullable=False, index=True)
    
    # Image information
    image_name: str = Column(String(500), nullable=False)
    image_format: ImageFormat = Column(SQLEnum(ImageFormat), nullable=False, index=True)
    image_quality: ImageQuality = Column(SQLEnum(ImageQuality), default=ImageQuality.DIAGNOSTIC)
    image_description: Optional[str] = Column(Text)
    
    # File information
    file_path: Optional[str] = Column(String(1000))
    file_url: Optional[str] = Column(String(1000))
    file_size_bytes: Optional[int] = Column(Integer)
    
    # Image properties
    width_pixels: Optional[int] = Column(Integer)
    height_pixels: Optional[int] = Column(Integer)
    bit_depth: Optional[int] = Column(Integer)
    color_space: Optional[str] = Column(String(50))
    
    # Metadata
    image_metadata: Dict[str, Any] = Column(JSON, default=dict)
    dicom_metadata: Optional[Dict[str, Any]] = Column(JSON)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DICOMSeriesDB(Base):
    """Database model for DICOM series."""
    __tablename__ = "dicom_series"
    __table_args__ = {"schema": "medical_records"}

    # Primary key
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to study
    study_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("medical_records.imaging_studies.id"), nullable=False, index=True)
    
    # DICOM information
    series_instance_uid: str = Column(String(255), nullable=False, unique=True)
    series_number: Optional[int] = Column(Integer)
    series_description: Optional[str] = Column(Text)
    modality: ModalityType = Column(SQLEnum(ModalityType), nullable=False)
    body_part_examined: Optional[str] = Column(String(100))
    series_date: Optional[datetime] = Column(DateTime)
    series_time: Optional[str] = Column(String(20))
    
    # Technical parameters
    manufacturer: Optional[str] = Column(String(255))
    model_name: Optional[str] = Column(String(255))
    station_name: Optional[str] = Column(String(255))
    
    # Series metadata
    series_metadata: Dict[str, Any] = Column(JSON, default=dict)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DICOMInstanceDB(Base):
    """Database model for DICOM instances."""
    __tablename__ = "dicom_instances"
    __table_args__ = {"schema": "medical_records"}

    # Primary key
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    series_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("medical_records.dicom_series.id"), nullable=False, index=True)
    image_id: Optional[UUID] = Column(PGUUID(as_uuid=True), ForeignKey("medical_records.medical_images.id"))
    
    # DICOM information
    sop_instance_uid: str = Column(String(255), nullable=False, unique=True)
    instance_number: Optional[int] = Column(Integer)
    acquisition_date: Optional[datetime] = Column(DateTime)
    acquisition_time: Optional[str] = Column(String(20))
    
    # Image properties
    rows: Optional[int] = Column(Integer)
    columns: Optional[int] = Column(Integer)
    bits_allocated: Optional[int] = Column(Integer)
    bits_stored: Optional[int] = Column(Integer)
    high_bit: Optional[int] = Column(Integer)
    pixel_representation: Optional[int] = Column(Integer)
    samples_per_pixel: Optional[int] = Column(Integer)
    photometric_interpretation: Optional[str] = Column(String(50))
    
    # File information
    file_path: Optional[str] = Column(String(1000))
    file_size_bytes: Optional[int] = Column(Integer)
    
    # Instance metadata
    instance_metadata: Dict[str, Any] = Column(JSON, default=dict)
    
    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
