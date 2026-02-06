"""
Authentication API routes for the Personal Health Assistant.

This module contains all authentication-related API endpoints including:
- User authentication endpoints
- Session management endpoints
- MFA endpoints
- Role and permission endpoints
- Audit and compliance endpoints
"""

from fastapi import APIRouter

from .auth import router as auth_router

# Create main auth router
auth_api_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Include auth router
auth_api_router.include_router(auth_router, prefix="/auth")

__all__ = ["auth_api_router"] 