"""
User Profile API Module

This module contains all the API endpoints for the user profile service including:
- Profile management endpoints
- Preferences management endpoints
- Privacy settings endpoints
- Health attributes endpoints
"""

from .profile import router as profile_router
from .preferences import router as preferences_router
from .privacy import router as privacy_router
from .health_attributes import router as health_attributes_router

# Main router that includes all profile-related routes
from fastapi import APIRouter

router = APIRouter(tags=["User Profile"])

# Include all sub-routers
router.include_router(profile_router, prefix="/profile")
router.include_router(preferences_router, prefix="/preferences")
router.include_router(privacy_router, prefix="/privacy")
router.include_router(health_attributes_router, prefix="/health-attributes")

__all__ = [
    "router",
    "profile_router",
    "preferences_router", 
    "privacy_router",
    "health_attributes_router"
] 