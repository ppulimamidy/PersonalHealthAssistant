"""
Health Attributes API Endpoints

This module provides endpoints for managing user health attributes, including:
- CRUD operations
- Validation
- Export/import
- Summary and analytics
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger

from ..models.health_attributes import HealthAttributesCreate, HealthAttributesUpdate, HealthAttributesResponse
from ..services.health_attributes_service import HealthAttributesService, get_health_attributes_service

logger = get_logger(__name__)

router = APIRouter(prefix="/health-attributes", tags=["Health Attributes"])


@router.post("/", response_model=HealthAttributesResponse)
@rate_limit(requests_per_hour=10)
@security_headers
async def create_health_attributes(
    request: Request,
    health_data: HealthAttributesCreate,
    current_user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Create user health attributes.
    """
    try:
        if health_data.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only create health attributes for authenticated user")
        health = await health_service.create_health_attributes(health_data)
        logger.info(f"Health attributes created for user {current_user.id}")
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create health attributes")


@router.get("/me", response_model=HealthAttributesResponse)
@security_headers
async def get_my_health_attributes(
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Get the current user's health attributes.
    """
    try:
        health = await health_service.get_health_attributes(current_user.id)
        if not health:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health attributes not found")
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve health attributes")


@router.put("/me", response_model=HealthAttributesResponse)
@rate_limit(requests_per_minute=10)
@security_headers
async def update_my_health_attributes(
    request: Request,
    health_data: HealthAttributesUpdate,
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Update the current user's health attributes.
    """
    try:
        health = await health_service.update_health_attributes(current_user.id, health_data)
        logger.info(f"Health attributes updated for user {current_user.id}")
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update health attributes")


@router.delete("/me")
@security_headers
async def delete_my_health_attributes(
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Delete the current user's health attributes.
    """
    try:
        success = await health_service.delete_health_attributes(current_user.id)
        logger.info(f"Health attributes deleted for user {current_user.id}")
        return {"message": "Health attributes deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete health attributes")


@router.post("/me/validate")
@security_headers
async def validate_health_data(
    request: Request,
    health_data: HealthAttributesCreate,
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Validate health attributes data without saving.
    """
    try:
        validation_results = await health_service.validate_health_data(health_data)
        return {"validation_results": validation_results, "message": "Health data validation completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate health attributes")


@router.get("/me/export")
@security_headers
async def export_health_data(
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Export the current user's health attributes data.
    """
    try:
        export_data = await health_service.export_health_attributes(current_user.id)
        return {"export_data": export_data, "message": "Health data export completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export health attributes")


@router.post("/me/import")
@rate_limit(requests_per_hour=5)
@security_headers
async def import_health_data(
    request: Request,
    import_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Import health attributes data for the current user.
    """
    try:
        health = await health_service.import_health_attributes(current_user.id, import_data)
        logger.info(f"Health attributes imported for user {current_user.id}")
        return health
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import health attributes for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to import health attributes")


@router.get("/me/summary")
@security_headers
async def get_health_summary(
    current_user: Any = Depends(get_current_user),
    health_service: HealthAttributesService = Depends(get_health_attributes_service)
):
    """
    Get a summary of the current user's health attributes.
    """
    try:
        summary = await health_service.get_health_summary(current_user.id)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health summary for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve health summary") 