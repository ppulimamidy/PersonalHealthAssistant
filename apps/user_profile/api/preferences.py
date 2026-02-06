"""
Preferences API Endpoints

This module provides endpoints for managing user preferences, including:
- CRUD operations
- Validation
- Notification settings
- Privacy and health tracking preferences
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

from ..models.preferences import PreferencesCreate, PreferencesUpdate, PreferencesResponse
from ..services.preferences_service import PreferencesService, get_preferences_service

logger = get_logger(__name__)

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.post("/", response_model=PreferencesResponse)
@rate_limit(requests_per_hour=10)
@security_headers
async def create_preferences(
    request: Request,
    preferences_data: PreferencesCreate,
    current_user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Create user preferences.
    """
    try:
        if preferences_data.user_id != current_user['id']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only create preferences for authenticated user")
        preferences = await preferences_service.create_preferences(preferences_data)
        logger.info(f"Preferences created for user {current_user['id']}")
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create preferences")


@router.get("/me", response_model=PreferencesResponse)
@security_headers
async def get_my_preferences(
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Get the current user's preferences.
    """
    try:
        preferences = await preferences_service.get_preferences(current_user['id'])
        if not preferences:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferences not found")
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve preferences")


@router.put("/me", response_model=PreferencesResponse)
@rate_limit(requests_per_minute=10)
@security_headers
async def update_my_preferences(
    request: Request,
    preferences_data: PreferencesUpdate,
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Update the current user's preferences.
    """
    try:
        preferences = await preferences_service.update_preferences(current_user['id'], preferences_data)
        logger.info(f"Preferences updated for user {current_user['id']}")
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update preferences")


@router.delete("/me")
@security_headers
async def delete_my_preferences(
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Delete the current user's preferences.
    """
    try:
        success = await preferences_service.delete_preferences(current_user['id'])
        logger.info(f"Preferences deleted for user {current_user['id']}")
        return {"message": "Preferences deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete preferences")


@router.post("/me/validate")
@security_headers
async def validate_preferences_data(
    request: Request,
    preferences_data: PreferencesUpdate,
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Validate preferences data without saving.
    """
    try:
        validation_results = await preferences_service.validate_preferences_data(preferences_data)
        return {"validation_results": validation_results, "message": "Preferences data validation completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate preferences")


@router.get("/me/export")
@security_headers
async def export_preferences_data(
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Export the current user's preferences data.
    """
    try:
        export_data = await preferences_service.export_preferences(current_user['id'])
        return {"export_data": export_data, "message": "Preferences data export completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export preferences")


@router.post("/me/import")
@rate_limit(requests_per_hour=5)
@security_headers
async def import_preferences_data(
    request: Request,
    import_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Import preferences data for the current user.
    """
    try:
        preferences = await preferences_service.import_preferences(current_user['id'], import_data)
        logger.info(f"Preferences imported for user {current_user['id']}")
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import preferences for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to import preferences")


@router.get("/me/summary")
@security_headers
async def get_preferences_summary(
    current_user: Any = Depends(get_current_user),
    preferences_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Get a summary of the current user's preferences.
    """
    try:
        summary = await preferences_service.get_preferences_summary(current_user['id'])
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preferences summary for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve preferences summary") 