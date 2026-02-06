"""
Symptoms API Router
Handles symptom tracking and management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.models.base import BaseModel, PaginatedResponse, create_paginated_response
from ..models.symptoms import (
    SymptomCreate, SymptomUpdate, SymptomResponse, SymptomFilter,
    SymptomCategory, SymptomSeverity, SymptomFrequency, SymptomDuration
)
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/symptoms", tags=["symptoms"])

@router.post("/", response_model=SymptomResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom(
    symptom: SymptomCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new symptom entry"""
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.create_symptom(
            user_id=current_user["id"],
            symptom_data=symptom.dict()
        )
        return SymptomResponse(**result)
    except ValueError as e:
        import logging
        logging.error(f"Validation error creating symptom for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to create symptom for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create symptom")

@router.get("/", response_model=PaginatedResponse)
async def get_symptoms(
    category: Optional[SymptomCategory] = Query(None),
    severity: Optional[SymptomSeverity] = Query(None),
    frequency: Optional[SymptomFrequency] = Query(None),
    duration: Optional[SymptomDuration] = Query(None),
    body_location: Optional[str] = Query(None),
    is_recurring: Optional[bool] = Query(None),
    requires_medical_attention: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get symptoms with optional filtering"""
    try:
        analytics_service = HealthAnalyticsService(db)
        filter_params = SymptomFilter(
            symptom_category=category,
            severity=severity,
            frequency=frequency,
            duration=duration,
            body_location=body_location,
            is_recurring=is_recurring,
            requires_medical_attention=requires_medical_attention,
            limit=limit,
            offset=offset
        )
        result = await analytics_service.get_symptoms(
            user_id=current_user["id"],
            filter_params=filter_params
        )
        # result should be a dict with keys: data, total
        return create_paginated_response(
            data=[SymptomResponse(**symptom) for symptom in result["data"]],
            total=result["total"],
            page=(offset // limit) + 1,
            size=limit,
            message="Symptoms retrieved successfully"
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve symptoms for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve symptoms")

@router.get("/{symptom_id}", response_model=SymptomResponse)
async def get_symptom(
    symptom_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific symptom by ID"""
    try:
        analytics_service = HealthAnalyticsService(db)
        symptom = await analytics_service.get_symptom(
            user_id=current_user["id"],
            symptom_id=symptom_id
        )
        if not symptom:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom not found")
        return SymptomResponse(**symptom)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve symptom {symptom_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve symptom")

@router.put("/{symptom_id}", response_model=SymptomResponse)
async def update_symptom(
    symptom_id: str,
    symptom_update: SymptomUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a symptom entry"""
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.update_symptom(
            user_id=current_user["id"],
            symptom_id=symptom_id,
            update_data=symptom_update.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom not found")
        return SymptomResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        import logging
        logging.error(f"Validation error updating symptom {symptom_id} for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to update symptom {symptom_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update symptom")

@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom(
    symptom_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a symptom entry"""
    try:
        analytics_service = HealthAnalyticsService(db)
        success = await analytics_service.delete_symptom(
            user_id=current_user["id"],
            symptom_id=symptom_id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom not found")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to delete symptom {symptom_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete symptom")

@router.get("/categories/list")
async def get_symptom_categories():
    """Get list of available symptom categories"""
    return {
        "categories": [category.value for category in SymptomCategory],
        "severities": [severity.value for severity in SymptomSeverity],
        "frequencies": [frequency.value for frequency in SymptomFrequency],
        "durations": [duration.value for duration in SymptomDuration]
    } 