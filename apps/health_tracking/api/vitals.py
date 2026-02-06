"""
Vital Signs API Router
Comprehensive API endpoints for vital signs management.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from common.middleware.auth import get_current_user
from common.database.connection import get_async_db
from common.models.base import (
    create_success_response, create_error_response, create_paginated_response,
    ErrorCode, ErrorSeverity, ResourceNotFoundException, ValidationException,
    PaginatedResponse
)
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers

from ..models.vital_signs import (
    VitalSigns, VitalSignType, MeasurementMethod, VitalSignsBase,
    BloodPressureCreate, HeartRateCreate, TemperatureCreate, OxygenSaturationCreate,
    RespiratoryRateCreate, BloodGlucoseCreate, BodyCompositionCreate,
    VitalSignsResponse, VitalSignsFilter
)
from ..services.vital_signs_service import VitalSignsService

logger = get_logger(__name__)

router = APIRouter(prefix="/vitals", tags=["Vital Signs"])

# Initialize service
vital_signs_service = VitalSignsService()

@router.post("/blood-pressure", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_blood_pressure(
    blood_pressure: BloodPressureCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new blood pressure measurement.
    
    Records systolic and diastolic blood pressure with optional mean arterial pressure.
    """
    try:
        result = await vital_signs_service.create_blood_pressure(
            user_id=current_user["id"],
            blood_pressure_data=blood_pressure.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating blood pressure measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record blood pressure measurement")

@router.post("/heart-rate", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=15)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_heart_rate(
    heart_rate: HeartRateCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new heart rate measurement.
    
    Records heart rate with optional heart rate variability and irregular heartbeat detection.
    """
    try:
        result = await vital_signs_service.create_heart_rate(
            user_id=current_user["id"],
            heart_rate_data=heart_rate.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating heart rate measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record heart rate measurement")

@router.post("/temperature", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_temperature(
    temperature: TemperatureCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new body temperature measurement.
    
    Records body temperature with measurement method specification.
    """
    try:
        result = await vital_signs_service.create_temperature(
            user_id=current_user["id"],
            temperature_data=temperature.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating temperature measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record temperature measurement")

@router.post("/oxygen-saturation", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_oxygen_saturation(
    oxygen_sat: OxygenSaturationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new oxygen saturation measurement.
    
    Records oxygen saturation percentage with optional perfusion index.
    """
    try:
        result = await vital_signs_service.create_oxygen_saturation(
            user_id=current_user["id"],
            oxygen_data=oxygen_sat.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating oxygen saturation measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record oxygen saturation measurement")

@router.post("/respiratory-rate", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_respiratory_rate(
    respiratory_rate: RespiratoryRateCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new respiratory rate measurement.
    
    Records respiratory rate with optional respiratory pattern.
    """
    try:
        result = await vital_signs_service.create_respiratory_rate(
            user_id=current_user["id"],
            respiratory_data=respiratory_rate.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating respiratory rate measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record respiratory rate measurement")

@router.post("/blood-glucose", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_blood_glucose(
    blood_glucose: BloodGlucoseCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new blood glucose measurement.
    
    Records blood glucose level with unit specification and context.
    """
    try:
        result = await vital_signs_service.create_blood_glucose(
            user_id=current_user["id"],
            glucose_data=blood_glucose.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating blood glucose measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record blood glucose measurement")

@router.post("/body-composition", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=5)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def create_body_composition(
    body_comp: BodyCompositionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new body composition measurement.
    
    Records weight, height, BMI, and other body composition metrics.
    """
    try:
        result = await vital_signs_service.create_body_composition(
            user_id=current_user["id"],
            composition_data=body_comp.dict(),
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating body composition measurement: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to record body composition measurement")

@router.get("/", response_model=PaginatedResponse)
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def get_vital_signs(
    vital_sign_type: Optional[VitalSignType] = Query(None, description="Filter by vital sign type"),
    measurement_method: Optional[MeasurementMethod] = Query(None, description="Filter by measurement method"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    measurement_quality: Optional[str] = Query(None, description="Filter by measurement quality"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get vital signs measurements for the current user.
    
    Supports filtering by type, method, date range, device, and quality.
    """
    try:
        filter_params = VitalSignsFilter(
            vital_sign_type=vital_sign_type,
            measurement_method=measurement_method,
            start_date=start_date,
            end_date=end_date,
            device_id=device_id,
            measurement_quality=measurement_quality,
            limit=limit,
            offset=offset
        )
        
        result = await vital_signs_service.get_vital_signs(
            user_id=current_user["id"],
            filter_params=filter_params,
            db=db
        )
        
        return create_paginated_response(
            data=result["data"],
            total=result["total"],
            page=(offset // limit) + 1,
            size=limit,
            message="Vital signs retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving vital signs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vital signs")

@router.get("/{vital_sign_id}", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def get_vital_sign(
    vital_sign_id: uuid.UUID = Path(..., description="Vital sign ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific vital sign measurement by ID.
    """
    try:
        result = await vital_signs_service.get_vital_sign(
            vital_sign_id=vital_sign_id,
            user_id=current_user["id"],
            db=db
        )
        
        return result
        
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving vital sign: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vital sign")

@router.put("/{vital_sign_id}", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def update_vital_sign(
    vital_sign_id: uuid.UUID = Path(..., description="Vital sign ID"),
    update_data: Dict[str, Any] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a vital sign measurement.
    
    Only allows updating certain fields like notes, metadata, and measurement quality.
    """
    try:
        result = await vital_signs_service.update_vital_sign(
            vital_sign_id=vital_sign_id,
            user_id=current_user["id"],
            update_data=update_data or {},
            db=db
        )
        
        return result
        
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating vital sign: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update vital sign")

@router.delete("/{vital_sign_id}", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def delete_vital_sign(
    vital_sign_id: uuid.UUID = Path(..., description="Vital sign ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a vital sign measurement.
    
    This action cannot be undone.
    """
    try:
        await vital_signs_service.delete_vital_sign(
            vital_sign_id=vital_sign_id,
            user_id=current_user["id"],
            db=db
        )
        
        return result
        
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting vital sign: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete vital sign")

@router.get("/summary/recent", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=30.0, max_retries=3)
async def get_recent_vital_signs_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a summary of recent vital signs measurements.
    
    Returns aggregated data for the specified time period.
    """
    try:
        result = await vital_signs_service.get_recent_summary(
            user_id=current_user["id"],
            days=days,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving vital signs summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vital signs summary")

@router.get("/trends/{vital_sign_type}", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("vital_signs", max_concurrent=20, timeout=60.0, max_retries=3)
async def get_vital_sign_trends(
    vital_sign_type: VitalSignType = Path(..., description="Vital sign type to analyze"),
    period: str = Query("30d", regex="^(7d|30d|90d|180d|365d)$", description="Analysis period"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get trend analysis for a specific vital sign type.
    
    Returns statistical analysis and trend patterns.
    """
    try:
        result = await vital_signs_service.get_trends(
            user_id=current_user["id"],
            vital_sign_type=vital_sign_type,
            period=period,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving vital sign trends: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve vital sign trends") 