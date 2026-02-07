"""
Appointments API endpoints for Doctor Collaboration Service.
"""

from datetime import datetime, timedelta
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

from ..models.appointment import (
    Appointment, AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentStatus, AppointmentType, AppointmentFilter, AppointmentConflict
)
from ..services.appointment_service import AppointmentService

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new appointment.
    
    This endpoint allows patients to schedule appointments with doctors.
    """
    try:
        service = AppointmentService(db)
        
        # Check if user has permission to create appointment
        if current_user["user_type"] not in ["patient", "doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create appointments"
            )
        
        # Create appointment
        appointment = await service.create_appointment(
            appointment_data=appointment_data,
            created_by=current_user["id"]
        )
        
        logger.info(f"Appointment created: {appointment.id} by user {current_user['id']}")
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create appointment"
        )


@router.get("/", response_model=List[AppointmentResponse])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def list_appointments(
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[UUID] = Query(None, description="Filter by doctor ID"),
    appointment_type: Optional[AppointmentType] = Query(None, description="Filter by appointment type"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by appointment status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=100, description="Number of appointments to return"),
    offset: int = Query(0, ge=0, description="Number of appointments to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List appointments with optional filtering.
    
    This endpoint returns appointments based on the provided filters.
    Users can only see appointments they are involved in.
    """
    try:
        service = AppointmentService(db)
        
        # Create filter object
        appointment_filter = AppointmentFilter(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_type=appointment_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Get appointments
        appointments = await service.list_appointments(
            filter_params=appointment_filter,
            current_user=current_user
        )
        
        return appointments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list appointments"
        )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_appointment(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get appointment by ID.
    
    This endpoint returns detailed information about a specific appointment.
    Users can only access appointments they are involved in.
    """
    try:
        service = AppointmentService(db)
        
        appointment = await service.get_appointment(
            appointment_id=appointment_id,
            current_user=current_user
        )
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get appointment"
        )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def update_appointment(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    appointment_data: AppointmentUpdate = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update appointment.
    
    This endpoint allows updating appointment details.
    Only participants or admins can update appointments.
    """
    try:
        service = AppointmentService(db)
        
        appointment = await service.update_appointment(
            appointment_id=appointment_id,
            appointment_data=appointment_data,
            current_user=current_user
        )
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        logger.info(f"Appointment updated: {appointment_id} by user {current_user['id']}")
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appointment"
        )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit(requests_per_minute=5)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=10, timeout=30.0, max_retries=3)
async def delete_appointment(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete appointment.
    
    This endpoint allows deleting appointments.
    Only participants or admins can delete appointments.
    """
    try:
        service = AppointmentService(db)
        
        success = await service.delete_appointment(
            appointment_id=appointment_id,
            current_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        logger.info(f"Appointment deleted: {appointment_id} by user {current_user['id']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete appointment"
        )


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def confirm_appointment(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Confirm appointment.
    
    This endpoint allows confirming a scheduled appointment.
    """
    try:
        service = AppointmentService(db)
        
        appointment = await service.confirm_appointment(
            appointment_id=appointment_id,
            current_user=current_user
        )
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        logger.info(f"Appointment confirmed: {appointment_id} by user {current_user['id']}")
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm appointment"
        )


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
@rate_limit(requests_per_minute=5)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=10, timeout=30.0, max_retries=3)
async def cancel_appointment(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    reason: str = Query(..., description="Cancellation reason"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cancel appointment.
    
    This endpoint allows cancelling an appointment with a reason.
    """
    try:
        service = AppointmentService(db)
        
        appointment = await service.cancel_appointment(
            appointment_id=appointment_id,
            reason=reason,
            current_user=current_user
        )
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        logger.info(f"Appointment cancelled: {appointment_id} by user {current_user['id']}")
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel appointment"
        )


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
@rate_limit(requests_per_minute=5)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=10, timeout=30.0, max_retries=3)
async def reschedule_appointment(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    new_date: datetime = Query(..., description="New appointment date"),
    new_duration: Optional[int] = Query(None, description="New duration in minutes"),
    reason: Optional[str] = Query(None, description="Rescheduling reason"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reschedule appointment.
    
    This endpoint allows rescheduling an appointment to a new date/time.
    """
    try:
        service = AppointmentService(db)
        
        appointment = await service.reschedule_appointment(
            appointment_id=appointment_id,
            new_date=new_date,
            new_duration=new_duration,
            reason=reason,
            current_user=current_user
        )
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        logger.info(f"Appointment rescheduled: {appointment_id} by user {current_user['id']}")
        
        return appointment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reschedule appointment"
        )


@router.get("/{appointment_id}/conflicts", response_model=List[AppointmentConflict])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def check_appointment_conflicts(
    appointment_id: UUID = Path(..., description="Appointment ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Check for appointment conflicts.
    
    This endpoint checks if an appointment conflicts with other appointments.
    """
    try:
        service = AppointmentService(db)
        
        conflicts = await service.check_conflicts(
            appointment_id=appointment_id,
            current_user=current_user
        )
        
        return conflicts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking conflicts for appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check appointment conflicts"
        )


@router.get("/upcoming/", response_model=List[AppointmentResponse])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_upcoming_appointments(
    days: int = Query(7, ge=1, le=30, description="Number of days to look ahead"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get upcoming appointments.
    
    This endpoint returns upcoming appointments for the current user.
    """
    try:
        service = AppointmentService(db)
        
        end_date = datetime.utcnow() + timedelta(days=days)
        
        appointments = await service.get_upcoming_appointments(
            end_date=end_date,
            current_user=current_user
        )
        
        return appointments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upcoming appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upcoming appointments"
        )


@router.get("/overdue/", response_model=List[AppointmentResponse])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_overdue_appointments(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get overdue appointments.
    
    This endpoint returns overdue appointments for the current user.
    """
    try:
        service = AppointmentService(db)
        
        appointments = await service.get_overdue_appointments(
            current_user=current_user
        )
        
        return appointments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting overdue appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get overdue appointments"
        ) 