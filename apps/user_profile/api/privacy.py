"""
Privacy Settings API Endpoints

This module provides endpoints for managing user privacy settings, including:
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

from ..models.privacy_settings import PrivacySettingsCreate, PrivacySettingsUpdate, PrivacySettingsResponse
from ..services.privacy_service import PrivacyService, get_privacy_service

logger = get_logger(__name__)

router = APIRouter(prefix="/privacy", tags=["Privacy Settings"])


@router.post("/", response_model=PrivacySettingsResponse)
@rate_limit(requests_per_hour=10)
@security_headers
async def create_privacy_settings(
    request: Request,
    privacy_data: PrivacySettingsCreate,
    current_user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Create user privacy settings.
    """
    try:
        if privacy_data.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only create privacy settings for authenticated user")
        privacy = await privacy_service.create_privacy_settings(privacy_data)
        logger.info(f"Privacy settings created for user {current_user.id}")
        return privacy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create privacy settings")


@router.get("/me", response_model=PrivacySettingsResponse)
@security_headers
async def get_my_privacy_settings(
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Get the current user's privacy settings.
    """
    try:
        privacy = await privacy_service.get_privacy_settings(current_user.id)
        if not privacy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Privacy settings not found")
        return privacy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve privacy settings")


@router.put("/me", response_model=PrivacySettingsResponse)
@rate_limit(requests_per_minute=10)
@security_headers
async def update_my_privacy_settings(
    request: Request,
    privacy_data: PrivacySettingsUpdate,
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Update the current user's privacy settings.
    """
    try:
        privacy = await privacy_service.update_privacy_settings(current_user.id, privacy_data)
        logger.info(f"Privacy settings updated for user {current_user.id}")
        return privacy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update privacy settings")


@router.delete("/me")
@security_headers
async def delete_my_privacy_settings(
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Delete the current user's privacy settings.
    """
    try:
        success = await privacy_service.delete_privacy_settings(current_user.id)
        logger.info(f"Privacy settings deleted for user {current_user.id}")
        return {"message": "Privacy settings deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete privacy settings")


@router.post("/me/validate")
@security_headers
async def validate_privacy_data(
    request: Request,
    privacy_data: PrivacySettingsCreate,
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Validate privacy settings data without saving.
    """
    try:
        validation_results = await privacy_service.validate_privacy_data(privacy_data)
        return {"validation_results": validation_results, "message": "Privacy data validation completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate privacy settings")


@router.get("/me/export")
@security_headers
async def export_privacy_data(
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Export the current user's privacy settings data.
    """
    try:
        export_data = await privacy_service.export_privacy_settings(current_user.id)
        return {"export_data": export_data, "message": "Privacy data export completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export privacy settings")


@router.post("/me/import")
@rate_limit(requests_per_hour=5)
@security_headers
async def import_privacy_data(
    request: Request,
    import_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Import privacy settings data for the current user.
    """
    try:
        privacy = await privacy_service.import_privacy_settings(current_user.id, import_data)
        logger.info(f"Privacy settings imported for user {current_user.id}")
        return privacy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import privacy settings for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to import privacy settings")


@router.get("/me/summary")
@security_headers
async def get_privacy_summary(
    current_user: Any = Depends(get_current_user),
    privacy_service: PrivacyService = Depends(get_privacy_service)
):
    """
    Get a summary of the current user's privacy settings.
    """
    try:
        summary = await privacy_service.get_privacy_summary(current_user.id)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get privacy summary for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve privacy summary") 