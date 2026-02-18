"""
Authentication Dependencies
Provides authentication dependencies for MVP API endpoints
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.utils.logging import get_logger
from apps.auth.services.auth_service import AuthService, get_auth_service
from apps.auth.models import User

logger = get_logger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP authorization credentials
        db: Database session
        auth_service: Auth service instance

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = auth_service.verify_token(token)

        if not payload:
            logger.error("Invalid token: no payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.error("Invalid token payload: no sub")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Get user from database
        user = await auth_service.get_user_by_id(user_id, db)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from e


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_async_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise

    Args:
        credentials: HTTP authorization credentials (optional)
        db: Database session
        auth_service: Auth service instance

    Returns:
        Optional[User]: Current user or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db, auth_service)
    except HTTPException:
        return None
