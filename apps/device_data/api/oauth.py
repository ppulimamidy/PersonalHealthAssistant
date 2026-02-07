"""
OAuth API Endpoints
Handles OAuth flows for device integrations.
"""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from pydantic import BaseModel

from common.database.connection import get_async_db
from common.utils.logging import get_logger
from common.config.settings import get_settings

from ..models.device import Device, DeviceType, DeviceStatus
from ..services.device_service import get_device_service

logger = get_logger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])


class UserStub(BaseModel):
    """Stub user model for device data service"""
    id: UUID
    email: str
    first_name: str = None
    last_name: str = None
    user_type: str = None


async def get_current_user(request: Request) -> UserStub:
    """Get current user from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        
        token = auth_header.split(" ")[1]
        settings = get_settings()
        
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )
        
        return UserStub(
            id=UUID(user_id),
            email=email
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


@router.get("/{device_id}/authorize", response_model=Dict[str, Any])
async def dexcom_oauth_authorize(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Start Dexcom OAuth flow - returns authorization URL for sandbox.
    
    - **device_id**: Device to authorize
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Verify it's a Dexcom device
        if device.device_type != DeviceType.CONTINUOUS_GLUCOSE_MONITOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth authorization is only available for Dexcom CGM devices"
            )
        
        # For sandbox mode, we'll use a simplified OAuth flow
        from ..config.dexcom_config import dexcom_config
        
        if dexcom_config.use_sandbox or device.device_metadata.get("sandbox", False):
            # Sandbox OAuth flow - return sandbox user selection
            return {
                "success": True,
                "oauth_type": "sandbox",
                "sandbox_users": list(dexcom_config.sandbox_users.keys()),
                "message": "Select a sandbox user for testing",
                "device_id": device_id
            }
        else:
            # Real OAuth flow (not implemented yet)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Real Dexcom OAuth flow not implemented yet. Use sandbox mode."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Dexcom OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start OAuth flow"
        )


@router.post("/{device_id}/callback", response_model=Dict[str, Any])
async def dexcom_oauth_callback(
    device_id: UUID,
    sandbox_user: str,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Complete Dexcom OAuth flow with sandbox user selection.
    
    - **device_id**: Device to authorize
    - **sandbox_user**: Selected sandbox user (User7, User8, User6, User4)
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Verify it's a Dexcom device
        if device.device_type != DeviceType.CONTINUOUS_GLUCOSE_MONITOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth callback is only available for Dexcom CGM devices"
            )
        
        # Verify sandbox user is valid
        from ..config.dexcom_config import dexcom_config
        if sandbox_user not in dexcom_config.sandbox_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sandbox user. Must be one of: {list(dexcom_config.sandbox_users.keys())}"
            )
        
        # Update device with sandbox user and access token
        device.metadata = {
            **device.metadata,
            "sandbox": True,
            "sandbox_user": sandbox_user,
            "oauth_completed": True,
            "oauth_completed_at": datetime.utcnow().isoformat()
        }
        
        # Set a mock access token for sandbox
        device.api_key = f"sandbox_token_{sandbox_user}_{user_id}"
        
        # Update device status
        device.status = DeviceStatus.ACTIVE
        device.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Dexcom OAuth completed for device {device_id} with sandbox user {sandbox_user}")
        
        return {
            "success": True,
            "message": f"OAuth completed successfully with sandbox user {sandbox_user}",
            "device_id": device_id,
            "sandbox_user": sandbox_user,
            "device_status": device.status.value,
            "oauth_completed": True
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing Dexcom OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete OAuth flow"
        )


@router.get("/{device_id}/status", response_model=Dict[str, Any])
async def dexcom_oauth_status(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get OAuth status for Dexcom device.
    
    - **device_id**: Device to check
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Check OAuth status
        oauth_completed = device.metadata.get("oauth_completed", False)
        sandbox_user = device.metadata.get("sandbox_user")
        oauth_completed_at = device.metadata.get("oauth_completed_at")
        
        return {
            "success": True,
            "device_id": device_id,
            "oauth_completed": oauth_completed,
            "sandbox_user": sandbox_user,
            "oauth_completed_at": oauth_completed_at,
            "device_status": device.status.value,
            "has_access_token": bool(device.api_key)
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check OAuth status"
        ) 