"""
Consultations API endpoints for Doctor Collaboration Service.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience

from ..models.consultation import (
    Consultation, ConsultationCreate, ConsultationUpdate, ConsultationResponse,
    ConsultationType, ConsultationStatus, ConsultationPriority, ConsultationFilter,
    ConsultationNotes, ConsultationDiagnosis, ConsultationPrescription
)
from ..services.consultation_service import ConsultationService

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_consultation(
    consultation_data: ConsultationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new consultation.
    
    This endpoint allows creating medical consultations between doctors and patients.
    """
    try:
        service = ConsultationService(db)
        
        # Check if user has permission to create consultations
        if current_user["user_type"] not in ["doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only doctors can create consultations"
            )
        
        # Create consultation
        consultation = await service.create_consultation(
            consultation_data=consultation_data,
            created_by=current_user["id"]
        )
        
        logger.info(f"Consultation created: {consultation.id} by doctor {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating consultation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create consultation"
        )


@router.get("/", response_model=List[ConsultationResponse])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def list_consultations(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[UUID] = Query(None, description="Filter by doctor ID"),
    consultation_type: Optional[ConsultationType] = Query(None, description="Filter by consultation type"),
    status: Optional[ConsultationStatus] = Query(None, description="Filter by consultation status"),
    priority: Optional[ConsultationPriority] = Query(None, description="Filter by priority"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    modality: Optional[str] = Query(None, description="Filter by modality"),
    appointment_id: Optional[UUID] = Query(None, description="Filter by appointment ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of consultations to return"),
    offset: int = Query(0, ge=0, description="Number of consultations to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List consultations with optional filtering.
    
    This endpoint returns consultations based on the provided filters.
    Users can only see consultations they are involved in.
    """
    try:
        service = ConsultationService(db)
        
        # Create filter object
        consultation_filter = ConsultationFilter(
            patient_id=patient_id,
            doctor_id=doctor_id,
            consultation_type=consultation_type,
            status=status,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            modality=modality,
            appointment_id=appointment_id,
            limit=limit,
            offset=offset
        )
        
        # Get consultations
        consultations = await service.list_consultations(
            filter_params=consultation_filter,
            current_user=current_user
        )
        
        return consultations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing consultations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list consultations"
        )


@router.get("/{consultation_id}", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def get_consultation(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get consultation by ID.
    
    This endpoint returns detailed information about a specific consultation.
    Users can only access consultations they are involved in.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.get_consultation(
            consultation_id=consultation_id,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consultation {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get consultation"
        )


@router.put("/{consultation_id}", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def update_consultation(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    consultation_data: ConsultationUpdate = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update consultation.
    
    This endpoint allows updating consultation details.
    Only the doctor or admin can update consultations.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.update_consultation(
            consultation_id=consultation_id,
            consultation_data=consultation_data,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation updated: {consultation_id} by user {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating consultation {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consultation"
        )


@router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit(requests_per_minute=5)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=10, timeout=30.0, max_retries=3)
async def delete_consultation(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete consultation.
    
    This endpoint allows deleting consultations.
    Only admins can delete consultations.
    """
    try:
        service = ConsultationService(db)
        
        success = await service.delete_consultation(
            consultation_id=consultation_id,
            current_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation deleted: {consultation_id} by user {current_user['id']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting consultation {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete consultation"
        )


@router.post("/{consultation_id}/start", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def start_consultation(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Start consultation.
    
    This endpoint allows starting a scheduled consultation.
    Only the doctor can start consultations.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.start_consultation(
            consultation_id=consultation_id,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation started: {consultation_id} by doctor {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting consultation {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start consultation"
        )


@router.post("/{consultation_id}/complete", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def complete_consultation(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Complete consultation.
    
    This endpoint allows completing an active consultation.
    Only the doctor can complete consultations.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.complete_consultation(
            consultation_id=consultation_id,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation completed: {consultation_id} by doctor {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing consultation {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete consultation"
        )


@router.post("/{consultation_id}/notes", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=30, timeout=30.0, max_retries=3)
async def add_consultation_notes(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    notes_data: ConsultationNotes = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add consultation notes.
    
    This endpoint allows adding or updating consultation notes.
    Only the doctor can add notes.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.add_consultation_notes(
            consultation_id=consultation_id,
            notes_data=notes_data,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation notes added: {consultation_id} by doctor {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding consultation notes {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add consultation notes"
        )


@router.post("/{consultation_id}/diagnosis", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def add_consultation_diagnosis(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    diagnosis_data: ConsultationDiagnosis = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add consultation diagnosis.
    
    This endpoint allows adding diagnoses to consultations.
    Only the doctor can add diagnoses.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.add_consultation_diagnosis(
            consultation_id=consultation_id,
            diagnosis_data=diagnosis_data,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation diagnosis added: {consultation_id} by doctor {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding consultation diagnosis {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add consultation diagnosis"
        )


@router.post("/{consultation_id}/prescription", response_model=ConsultationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def add_consultation_prescription(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    prescription_data: ConsultationPrescription = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add consultation prescription.
    
    This endpoint allows adding prescriptions to consultations.
    Only the doctor can add prescriptions.
    """
    try:
        service = ConsultationService(db)
        
        consultation = await service.add_consultation_prescription(
            consultation_id=consultation_id,
            prescription_data=prescription_data,
            current_user=current_user
        )
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found"
            )
        
        logger.info(f"Consultation prescription added: {consultation_id} by doctor {current_user['id']}")
        
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding consultation prescription {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add consultation prescription"
        )


@router.get("/{consultation_id}/history", response_model=List[ConsultationResponse])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_consultation_history(
    consultation_id: UUID = Path(..., description="Consultation ID"),
    limit: int = Query(10, ge=1, le=50, description="Number of history items to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get consultation history.
    
    This endpoint returns the history of changes for a consultation.
    """
    try:
        service = ConsultationService(db)
        
        history = await service.get_consultation_history(
            consultation_id=consultation_id,
            current_user=current_user,
            limit=limit
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consultation history {consultation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get consultation history"
        )


@router.get("/stats/", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_consultation_stats(
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get consultation statistics.
    
    This endpoint returns consultation statistics for the current user.
    """
    try:
        service = ConsultationService(db)
        
        stats = await service.get_consultation_stats(
            current_user=current_user,
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consultation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get consultation statistics"
        ) 