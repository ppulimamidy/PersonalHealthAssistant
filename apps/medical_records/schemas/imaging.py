"""
Imaging Schemas
Pydantic models for medical imaging data validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator


class ModalityType(str, Enum):
    """Medical imaging modalities."""
    CT = "CT"
    MRI = "MRI"
    XRAY = "XRAY"
    ULTRASOUND = "ULTRASOUND"
    PET = "PET"
    SPECT = "SPECT"
    FLUOROSCOPY = "FLUOROSCOPY"
    MAMMOGRAPHY = "MAMMOGRAPHY"
    DEXA = "DEXA"
    ANGIOGRAPHY = "ANGIOGRAPHY"
    OTHER = "OTHER"


class BodyPartType(str, Enum):
    """Anatomical body parts for imaging."""
    HEAD = "HEAD"
    NECK = "NECK"
    CHEST = "CHEST"
    ABDOMEN = "ABDOMEN"
    PELVIS = "PELVIS"
    SPINE = "SPINE"
    UPPER_EXTREMITY = "UPPER_EXTREMITY"
    LOWER_EXTREMITY = "LOWER_EXTREMITY"
    HEART = "HEART"
    LUNGS = "LUNGS"
    BRAIN = "BRAIN"
    OTHER = "OTHER"


class StudyStatus(str, Enum):
    """Imaging study status."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class ImageFormat(str, Enum):
    """Medical image formats."""
    DICOM = "DICOM"
    JPEG = "JPEG"
    PNG = "PNG"
    TIFF = "TIFF"
    BMP = "BMP"
    OTHER = "OTHER"


class ImageQuality(str, Enum):
    """Image quality levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXCELLENT = "EXCELLENT"


# Imaging Study Schemas
class ImagingStudyCreate(BaseModel):
    """Schema for creating an imaging study."""
    patient_id: UUID = Field(..., description="Patient ID")
    study_name: str = Field(..., min_length=1, max_length=255, description="Study name")
    modality: ModalityType = Field(..., description="Imaging modality")
    body_part: BodyPartType = Field(..., description="Body part being imaged")
    study_date: Optional[datetime] = Field(None, description="Study date")
    study_description: Optional[str] = Field(None, max_length=1000, description="Study description")
    referring_physician: Optional[str] = Field(None, max_length=255, description="Referring physician")
    performing_physician: Optional[str] = Field(None, max_length=255, description="Performing physician")
    study_status: StudyStatus = Field(StudyStatus.SCHEDULED, description="Study status")
    study_notes: Optional[str] = Field(None, max_length=2000, description="Study notes")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    study_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional study metadata")


class ImagingStudyUpdate(BaseModel):
    """Schema for updating an imaging study."""
    study_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Study name")
    modality: Optional[ModalityType] = Field(None, description="Imaging modality")
    body_part: Optional[BodyPartType] = Field(None, description="Body part being imaged")
    study_date: Optional[datetime] = Field(None, description="Study date")
    study_description: Optional[str] = Field(None, max_length=1000, description="Study description")
    referring_physician: Optional[str] = Field(None, max_length=255, description="Referring physician")
    performing_physician: Optional[str] = Field(None, max_length=255, description="Performing physician")
    study_status: Optional[StudyStatus] = Field(None, description="Study status")
    study_notes: Optional[str] = Field(None, max_length=2000, description="Study notes")
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, max_length=255, description="FHIR resource ID")
    study_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional study metadata")


class ImagingStudyResponse(BaseModel):
    """Schema for imaging study response."""
    id: UUID = Field(..., description="Study ID")
    patient_id: UUID = Field(..., description="Patient ID")
    study_name: str = Field(..., description="Study name")
    modality: ModalityType = Field(..., description="Imaging modality")
    body_part: BodyPartType = Field(..., description="Body part being imaged")
    study_date: datetime = Field(..., description="Study date")
    study_description: Optional[str] = Field(None, description="Study description")
    referring_physician: Optional[str] = Field(None, description="Referring physician")
    performing_physician: Optional[str] = Field(None, description="Performing physician")
    study_status: StudyStatus = Field(..., description="Study status")
    study_notes: Optional[str] = Field(None, description="Study notes")
    external_id: Optional[str] = Field(None, description="External system ID")
    fhir_resource_id: Optional[str] = Field(None, description="FHIR resource ID")
    study_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional study metadata")
    image_count: int = Field(0, description="Number of images in study")
    total_size_bytes: int = Field(0, description="Total size of all images in bytes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ImagingStudyListResponse(BaseModel):
    """Schema for imaging study list response."""
    studies: List[ImagingStudyResponse] = Field(..., description="List of imaging studies")
    total: int = Field(..., description="Total number of studies")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Medical Image Schemas
class MedicalImageCreate(BaseModel):
    """Schema for creating a medical image."""
    study_id: UUID = Field(..., description="Associated imaging study ID")
    image_name: str = Field(..., min_length=1, max_length=255, description="Image name")
    image_description: Optional[str] = Field(None, max_length=1000, description="Image description")
    image_format: ImageFormat = Field(..., description="Image format")
    image_quality: ImageQuality = Field(ImageQuality.MEDIUM, description="Image quality")
    image_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional image metadata")
    dicom_series_id: Optional[UUID] = Field(None, description="Associated DICOM series ID")
    dicom_instance_id: Optional[UUID] = Field(None, description="Associated DICOM instance ID")


class MedicalImageUpdate(BaseModel):
    """Schema for updating a medical image."""
    image_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Image name")
    image_description: Optional[str] = Field(None, max_length=1000, description="Image description")
    image_format: Optional[ImageFormat] = Field(None, description="Image format")
    image_quality: Optional[ImageQuality] = Field(None, description="Image quality")
    image_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional image metadata")
    dicom_series_id: Optional[UUID] = Field(None, description="Associated DICOM series ID")
    dicom_instance_id: Optional[UUID] = Field(None, description="Associated DICOM instance ID")


class MedicalImageResponse(BaseModel):
    """Schema for medical image response."""
    id: UUID = Field(..., description="Image ID")
    study_id: UUID = Field(..., description="Associated imaging study ID")
    image_name: str = Field(..., description="Image name")
    image_description: Optional[str] = Field(None, description="Image description")
    image_format: ImageFormat = Field(..., description="Image format")
    image_quality: ImageQuality = Field(..., description="Image quality")
    file_path: Optional[str] = Field(None, description="File path on storage")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    thumbnail_path: Optional[str] = Field(None, description="Thumbnail file path")
    image_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional image metadata")
    dicom_series_id: Optional[UUID] = Field(None, description="Associated DICOM series ID")
    dicom_instance_id: Optional[UUID] = Field(None, description="Associated DICOM instance ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class MedicalImageListResponse(BaseModel):
    """Schema for medical image list response."""
    images: List[MedicalImageResponse] = Field(..., description="List of medical images")
    total: int = Field(..., description="Total number of images")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages") 