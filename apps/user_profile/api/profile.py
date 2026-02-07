"""
Profile API Endpoints

This module provides comprehensive profile management endpoints including:
- Profile CRUD operations
- Profile validation
- Profile completion tracking
- Profile data export/import
- Profile privacy controls
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from common.database.connection import get_async_db

# from common.middleware.auth import get_current_user  # REMOVE THIS IMPORT
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger

from ..models.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileSummary,
)
from ..services.profile_service import ProfileService, get_profile_service

# from ..models.user_stub import User  # Use a stub or actual User ORM as appropriate

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()

# Local dependency to get the current authenticated user as a User ORM object
def get_current_user():
    async def _get_user(request: Request, db: AsyncSession = Depends(get_async_db)):
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = auth_header.split(" ", 1)[1]

        # Use PyJWT for decoding
        import jwt as pyjwt
        import os

        try:
            jwt_secret = os.getenv(
                "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
            )
            logger.info(f"JWT secret used for decoding: {jwt_secret}")
            payload = pyjwt.decode(token, jwt_secret, algorithms=["HS256"])
            logger.info(f"Decoded JWT payload: {payload}")
            user_id = payload.get("sub")
            email = payload.get("email")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            # Create a User instance with required fields
            return User(id=user_id, email=email)
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    return _get_user


# Import the User model from user_stub
from ..models.user_stub import User


@router.post("/", response_model=ProfileResponse)
@rate_limit(requests_per_hour=10)
async def create_profile(
    request: Request,
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user()),
    db: AsyncSession = Depends(get_async_db),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Create a new user profile.

    This endpoint creates a complete profile with default preferences and privacy settings.
    """
    try:
        # Ensure user can only create their own profile
        current_user_uuid = uuid.UUID(current_user.id)
        if profile_data.user_id != current_user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create profile for authenticated user",
            )

        profile = await profile_service.create_profile(profile_data)

        logger.info(f"Profile created for user {current_user.id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile",
        )


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Get the current user's profile.
    """
    try:
        profile = await profile_service.get_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


@router.get("/me/summary", response_model=ProfileSummary)
async def get_my_profile_summary(
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Get a summary of the current user's profile.
    """
    try:
        summary = await profile_service.get_profile_summary(current_user.id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile summary for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile summary",
        )


@router.put("/me", response_model=ProfileResponse)
@rate_limit(requests_per_minute=10)
async def update_my_profile(
    request: Request,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Update the current user's profile.
    """
    try:
        profile = await profile_service.update_profile(current_user.id, profile_data)

        logger.info(f"Profile updated for user {current_user.id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


@router.delete("/me")
async def delete_my_profile(
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Delete the current user's profile (soft delete).
    """
    try:
        success = await profile_service.delete_profile(current_user.id)

        logger.info(f"Profile deleted for user {current_user.id}")
        return {"message": "Profile deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile",
        )


@router.post("/me/validate")
async def validate_profile_data(
    request: Request,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Validate profile data without saving.
    """
    try:
        validation_results = await profile_service.validate_profile_data(profile_data)

        return {
            "validation_results": validation_results,
            "message": "Profile data validation completed",
        }

    except Exception as e:
        logger.error(f"Failed to validate profile data for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate profile data",
        )


@router.get("/me/export")
async def export_profile_data(
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Export all profile data for the current user.
    """
    try:
        export_data = await profile_service.export_profile_data(current_user.id)

        logger.info(f"Profile data exported for user {current_user.id}")
        return export_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export profile data for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export profile data",
        )


@router.post("/me/import")
@rate_limit(requests_per_hour=5)
async def import_profile_data(
    request: Request,
    import_data: Dict[str, Any],
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Import profile data for the current user.
    """
    try:
        profile = await profile_service.import_profile_data(
            current_user.id, import_data
        )

        logger.info(f"Profile data imported for user {current_user.id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import profile data for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import profile data",
        )


@router.get("/me/completion")
async def get_profile_completion(
    current_user: User = Depends(get_current_user()),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """
    Get profile completion status and percentage.
    """
    try:
        profile = await profile_service.get_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )

        return {
            "completion_percentage": profile.completion_percentage,
            "is_complete": profile.is_complete,
            "missing_fields": await _get_missing_fields(profile),
            "next_steps": await _get_next_steps(profile),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get profile completion for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile completion",
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the profile service.
    """
    return {
        "status": "healthy",
        "service": "user-profile-service",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for the profile service.
    """
    return {
        "status": "ready",
        "service": "user-profile-service",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Helper functions
async def _get_missing_fields(profile: ProfileResponse) -> List[str]:
    """Get list of missing required fields."""
    missing_fields = []

    required_fields = [
        ("first_name", "First Name"),
        ("last_name", "Last Name"),
        ("date_of_birth", "Date of Birth"),
        ("gender", "Gender"),
        ("email", "Email"),
    ]

    for field, display_name in required_fields:
        if not getattr(profile, field, None):
            missing_fields.append(display_name)

    return missing_fields


async def _get_next_steps(profile: ProfileResponse) -> List[str]:
    """Get suggested next steps for profile completion."""
    next_steps = []

    if not profile.phone_number:
        next_steps.append("Add your phone number for emergency contacts")

    if not profile.emergency_contact_name:
        next_steps.append("Add emergency contact information")

    if not profile.address_line_1:
        next_steps.append("Add your address information")

    if not profile.blood_type:
        next_steps.append("Add your blood type for medical emergencies")

    if not profile.height_cm or not profile.weight_kg:
        next_steps.append("Add your height and weight for health tracking")

    if not profile.allergies:
        next_steps.append("Add any allergies or medical conditions")

    return next_steps
