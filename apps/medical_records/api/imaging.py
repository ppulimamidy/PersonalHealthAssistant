"""
Imaging API endpoints for Medical Records
Handles imaging studies, medical images, and DICOM management.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import logging

from ..schemas.imaging import (
    ImagingStudyCreate, ImagingStudyUpdate, ImagingStudyResponse,
    MedicalImageCreate, MedicalImageUpdate, MedicalImageResponse,
    ImagingStudyListResponse, MedicalImageListResponse,
    ModalityType, BodyPartType, StudyStatus, ImageFormat, ImageQuality
)
from ..services.imaging_service import imaging_service
from ..services import service_integration
from common.database.connection import get_session
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/imaging", tags=["Medical Imaging"])

# Security scheme
security = HTTPBearer()

# Get current user from auth service
async def get_current_user(request: Request, credentials: HTTPBearer = Depends(security)):
    """Get current user from auth service"""
    try:
        # Validate user access with required permissions
        user_info = await service_integration.validate_user_access(
            credentials.credentials,
            required_permissions=["medical_records:read"]
        )
        
        # Add user info to request state for logging
        request.state.user_id = user_info["user_id"]
        request.state.user_profile = user_info["user_profile"]
        
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


@router.post("/studies", response_model=ImagingStudyResponse)
async def create_imaging_study(
    study_data: ImagingStudyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Create a new imaging study.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # Check if user has access to the patient
        if str(study_data.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this patient")
        
        return await imaging_service.create_imaging_study(study_data, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating imaging study: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/studies/{study_id}", response_model=ImagingStudyResponse)
async def get_imaging_study(
    study_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get an imaging study by ID.
    
    Requires authentication and appropriate permissions.
    """
    try:
        study = await imaging_service.get_imaging_study(study_id, db)
        
        # Check if user has access to the patient
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this study")
        
        return study
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting imaging study: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/studies/{study_id}", response_model=ImagingStudyResponse)
async def update_imaging_study(
    study_id: UUID,
    study_data: ImagingStudyUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Update an imaging study.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # Get study to check access
        study = await imaging_service.get_imaging_study(study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this study")
        
        return await imaging_service.update_imaging_study(study_id, study_data, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating imaging study: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/studies/{study_id}")
async def delete_imaging_study(
    study_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Delete an imaging study and all associated images.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # Get study to check access
        study = await imaging_service.get_imaging_study(study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this study")
        
        success = await imaging_service.delete_imaging_study(study_id, db)
        return {"success": success, "message": "Imaging study deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting imaging study: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/studies", response_model=ImagingStudyListResponse)
async def list_imaging_studies(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    modality: Optional[ModalityType] = Query(None, description="Filter by modality"),
    status: Optional[StudyStatus] = Query(None, description="Filter by study status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    List imaging studies with filtering and pagination.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # If patient_id not specified, use current user's ID
        if patient_id is None:
            patient_id = UUID(current_user.get('sub'))
        elif str(patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this patient")
        
        return await imaging_service.list_imaging_studies(
            patient_id=patient_id,
            modality=modality,
            status=status,
            page=page,
            size=size,
            db=db
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing imaging studies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/studies/{study_id}/images", response_model=MedicalImageResponse)
async def upload_medical_image(
    study_id: UUID,
    image_file: UploadFile = File(..., description="Medical image file"),
    image_name: str = Form(..., description="Image name"),
    image_format: ImageFormat = Form(ImageFormat.PNG, description="Image format"),
    image_quality: ImageQuality = Form(ImageQuality.HIGH, description="Image quality"),
    image_description: Optional[str] = Form(None, description="Image description"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Upload a medical image to a study.
    
    Requires authentication and appropriate permissions.
    Supports various image formats including DICOM.
    """
    try:
        # Get study to check access
        study = await imaging_service.get_imaging_study(study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this study")
        
        # Create image data
        image_data = MedicalImageCreate(
            study_id=study_id,
            image_name=image_name,
            image_format=image_format,
            image_quality=image_quality,
            image_description=image_description,
            image_metadata={},
            dicom_metadata=None,
            file_path=None,
            file_url=None,
            file_size_bytes=None,
            width_pixels=None,
            height_pixels=None,
            bit_depth=None,
            color_space=None
        )
        
        return await imaging_service.upload_medical_image(study_id, image_file, image_data, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading medical image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/studies/{study_id}/dicom")
async def upload_dicom_file(
    study_id: UUID,
    dicom_file: UploadFile = File(..., description="DICOM file"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Upload a DICOM file to a study.
    
    Requires authentication and appropriate permissions.
    Automatically processes DICOM metadata and creates series/instance records.
    """
    try:
        # Get study to check access
        study = await imaging_service.get_imaging_study(study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this study")
        
        # Validate file type
        if not dicom_file.filename.lower().endswith(('.dcm', '.dicom')):
            raise HTTPException(status_code=400, detail="File must be a DICOM file (.dcm or .dicom)")
        
        result = await imaging_service.upload_dicom_file(study_id, dicom_file, db)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading DICOM file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/studies/{study_id}/images", response_model=MedicalImageListResponse)
async def list_medical_images(
    study_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    List medical images in a study.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # Get study to check access
        study = await imaging_service.get_imaging_study(study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this study")
        
        return await imaging_service.list_medical_images(study_id, page, size, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing medical images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/images/{image_id}", response_model=MedicalImageResponse)
async def get_medical_image(
    image_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get a medical image by ID.
    
    Requires authentication and appropriate permissions.
    """
    try:
        image = await imaging_service.get_medical_image(image_id, db)
        
        # Get study to check access
        study = await imaging_service.get_imaging_study(image.study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this image")
        
        return image
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting medical image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/images/{image_id}")
async def delete_medical_image(
    image_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Delete a medical image.
    
    Requires authentication and appropriate permissions.
    """
    try:
        # Get image to check access
        image = await imaging_service.get_medical_image(image_id, db)
        study = await imaging_service.get_imaging_study(image.study_id, db)
        if str(study.patient_id) != current_user.get('sub'):
            raise HTTPException(status_code=403, detail="Access denied to this image")
        
        success = await imaging_service.delete_medical_image(image_id, db)
        return {"success": success, "message": "Medical image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting medical image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/modalities", response_model=List[str])
async def get_supported_modalities():
    """
    Get list of supported imaging modalities.
    
    No authentication required.
    """
    return [modality.value for modality in ModalityType]


@router.get("/body-parts", response_model=List[str])
async def get_supported_body_parts():
    """
    Get list of supported body parts.
    
    No authentication required.
    """
    return [body_part.value for body_part in BodyPartType]


@router.get("/image-formats", response_model=List[str])
async def get_supported_image_formats():
    """
    Get list of supported image formats.
    
    No authentication required.
    """
    return [format.value for format in ImageFormat]


@router.get("/study-statuses", response_model=List[str])
async def get_study_statuses():
    """
    Get list of study statuses.
    
    No authentication required.
    """
    return [status.value for status in StudyStatus]
