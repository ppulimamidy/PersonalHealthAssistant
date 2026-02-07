"""
Device API Endpoints
Handles device registration, management, and operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from pydantic import BaseModel

from common.database.connection import get_async_db
from common.middleware.rate_limiter import rate_limit
from common.utils.logging import get_logger
from common.config.settings import get_settings

from ..models.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceSummary,
    DeviceConnectionRequest, DeviceSyncRequest, DeviceHealthCheck,
    DeviceType, DeviceStatus, ConnectionType
)
from ..services.device_service import DeviceService, get_device_service

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])


class UserStub(BaseModel):
    """Stub user model for device data service"""
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: Optional[str] = None


async def get_current_user(request: Request) -> UserStub:
    """Get current user from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
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
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return UserStub(
            id=UUID(user_id),
            email=email
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new health device for the current user.
    
    - **name**: Device name (e.g., "Apple Watch Series 7")
    - **device_type**: Type of health device
    - **manufacturer**: Device manufacturer (e.g., "Apple")
    - **model**: Device model (e.g., "Series 7")
    - **connection_type**: How the device connects
    - **supported_metrics**: List of health metrics this device can track
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        device = await device_service.create_device(user_id, device_data)
        
        logger.info(f"Device created for user {user_id}: {device.id}")
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device"
        )


@router.get("/", response_model=List[DeviceSummary])
async def get_devices(
    active_only: bool = Query(True, description="Return only active devices"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all devices for the current user.
    
    - **active_only**: If true, return only active devices
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        devices = await device_service.get_user_devices(user_id, active_only)
        
        return [DeviceSummary.from_orm(device) for device in devices]
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices"
        )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific device by ID.
    
    - **device_id**: Unique device identifier
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        device = await device_service.get_device(device_id, user_id)
        
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device"
        )


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update device information (full update).
    
    - **device_id**: Unique device identifier
    - **device_data**: Updated device information
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        device = await device_service.update_device(device_id, user_id, device_data)
        
        logger.info(f"Device {device_id} updated for user {user_id}")
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )


@router.patch("/{device_id}", response_model=DeviceResponse)
async def patch_device(
    device_id: UUID,
    device_data: DeviceUpdate,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Partially update device information.
    
    - **device_id**: Unique device identifier
    - **device_data**: Partial device information to update
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        device = await device_service.update_device(device_id, user_id, device_data)
        
        logger.info(f"Device {device_id} patched for user {user_id}")
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch device"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a device (soft delete).
    
    - **device_id**: Unique device identifier
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        await device_service.delete_device(device_id, user_id)
        
        logger.info(f"Device {device_id} deleted for user {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device"
        )


@router.post("/{device_id}/connect", response_model=DeviceResponse)
async def connect_device(
    device_id: UUID,
    connection_data: DeviceConnectionRequest,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Connect a device to start data collection.
    
    - **device_id**: Unique device identifier
    - **connection_data**: Connection configuration
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        device = await device_service.connect_device(device_id, user_id, connection_data)
        
        logger.info(f"Device {device_id} connection initiated for user {user_id}")
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect device"
        )


@router.post("/{device_id}/sync", response_model=Dict[str, Any])
async def sync_device(
    device_id: UUID,
    sync_data: DeviceSyncRequest,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Sync data from a connected device.
    
    - **device_id**: Unique device identifier
    - **sync_data**: Sync configuration
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        sync_result = await device_service.sync_device(device_id, user_id, sync_data)
        
        logger.info(f"Device {device_id} sync completed for user {user_id}")
        return sync_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync device"
        )


@router.get("/{device_id}/sync", response_model=Dict[str, Any])
async def get_device_sync_info(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get device sync information and status.
    
    - **device_id**: Unique device identifier
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Get data summary for this device
        from ..services.data_service import get_data_service
        data_service = await get_data_service(db)
        data_summary = await data_service.get_data_summary(user_id, device_id)
        
        return {
            "success": True,
            "device_id": device_id,
            "device_status": device.status.value,
            "last_sync_at": device.last_sync_at.isoformat() if device.last_sync_at else None,
            "last_used_at": device.last_used_at.isoformat() if device.last_used_at else None,
            "total_data_points": data_summary.get("total_data_points", 0),
            "data_types": data_summary.get("data_types", {}),
            "sync_available": device.status in [DeviceStatus.ACTIVE, DeviceStatus.INACTIVE],
            "needs_oauth": device.status == DeviceStatus.INACTIVE and device.device_type == DeviceType.CONTINUOUS_GLUCOSE_MONITOR,
            "message": "Device sync information retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device sync info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device sync information"
        )


@router.get("/{device_id}/health", response_model=DeviceHealthCheck)
async def get_device_health(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get device health status and connection information.
    
    - **device_id**: Unique device identifier
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        health = await device_service.get_device_health(device_id, user_id)
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device health {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device health"
        )


@router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_device_statistics(
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get device statistics for the current user.
    
    Returns summary of device counts, status distribution, and sync information.
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        statistics = await device_service.get_device_statistics(user_id)
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting device statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device statistics"
        )


@router.get("/types/supported", response_model=List[Dict[str, str]])
async def get_supported_device_types():
    """
    Get list of supported device types.
    
    Returns all available device types that can be registered.
    """
    try:
        device_type_descriptions = {
            "wearable": "General wearable health device",
            "smartwatch": "Smart watch with health tracking capabilities",
            "fitness_tracker": "Dedicated fitness and activity tracker",
            "smart_ring": "Smart ring for health monitoring (Oura, etc.)",
            "smart_band": "Smart wristband or bracelet",
            "smart_clothing": "Smart clothing with embedded sensors",
            "smart_shoes": "Smart shoes with activity tracking",
            "smart_glasses": "Smart glasses with health features",
            "smart_earbuds": "Smart earbuds with health monitoring",
            "blood_pressure_monitor": "Blood pressure monitoring device",
            "glucose_monitor": "Blood glucose monitoring device",
            "thermometer": "Digital thermometer",
            "scale": "Smart scale with body composition",
            "sleep_tracker": "Dedicated sleep tracking device",
            "heart_rate_monitor": "Heart rate monitoring device",
            "oxygen_monitor": "Blood oxygen saturation monitor",
            "ecg_monitor": "Electrocardiogram monitoring device",
            "blood_glucose_meter": "Traditional blood glucose meter",
            "insulin_pump": "Insulin pump device",
            "continuous_glucose_monitor": "Continuous glucose monitoring system",
            "pulse_oximeter": "Pulse oximeter for oxygen levels",
            "blood_pressure_cuff": "Blood pressure cuff monitor",
            "therapy_device": "Medical therapy device",
            "medication_dispenser": "Smart medication dispenser",
            "cpap_machine": "CPAP machine for sleep apnea",
            "inhaler": "Smart inhaler device",
            "hearing_aid": "Smart hearing aid",
            "prosthetic": "Smart prosthetic device",
            "mobile_app": "Mobile health application",
            "health_platform": "Health platform or service",
            "fitness_app": "Fitness tracking application",
            "nutrition_app": "Nutrition tracking application",
            "meditation_app": "Meditation and wellness app",
            "smart_mirror": "Smart mirror with health features",
            "smart_toilet": "Smart toilet with health monitoring",
            "smart_shower": "Smart shower with health tracking",
            "air_quality_monitor": "Air quality monitoring device",
            "water_quality_monitor": "Water quality monitoring device",
            "fertility_tracker": "Fertility tracking device",
            "pregnancy_monitor": "Pregnancy monitoring device",
            "baby_monitor": "Smart baby monitor",
            "pet_health_tracker": "Pet health tracking device",
            "athletic_performance": "Athletic performance tracker",
            "clinical_device": "Clinical medical device",
            "research_device": "Research and development device",
            "lab_equipment": "Laboratory equipment",
            "other": "Other health device"
        }
        
        device_types = [
            {
                "name": device_type.value,
                "description": device_type_descriptions.get(device_type.value, "Health device")
            }
            for device_type in DeviceType
        ]
        
        return device_types
        
    except Exception as e:
        logger.error(f"Error getting device types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device types"
        )


@router.get("/connection-types/supported", response_model=List[Dict[str, str]])
async def get_supported_connection_types():
    """
    Get list of supported connection types.
    
    Returns all available connection methods for devices.
    """
    try:
        connection_type_descriptions = {
            "bluetooth": "Bluetooth wireless connection",
            "wifi": "WiFi wireless connection",
            "usb": "USB wired connection",
            "nfc": "Near Field Communication",
            "cellular": "Cellular network connection",
            "manual": "Manual data entry",
            "api": "Application Programming Interface"
        }
        
        connection_types = [
            {
                "name": conn_type.value,
                "description": connection_type_descriptions.get(conn_type.value, "Connection method")
            }
            for conn_type in ConnectionType
        ]
        
        return connection_types
        
    except Exception as e:
        logger.error(f"Error getting connection types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connection types"
        )


@router.post("/{device_id}/disconnect", response_model=DeviceResponse)
async def disconnect_device(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Disconnect a device to stop data collection.
    
    - **device_id**: Unique device identifier
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Update device status to disconnected
        device_data = DeviceUpdate(status=DeviceStatus.DISCONNECTED)
        device = await device_service.update_device(device_id, user_id, device_data)
        
        logger.info(f"Device {device_id} disconnected for user {user_id}")
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect device"
        )


@router.post("/{device_id}/set-primary", response_model=DeviceResponse)
async def set_primary_device(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Set a device as the primary device for the user.
    
    - **device_id**: Unique device identifier
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # First, unset all other devices as primary
        devices = await device_service.get_user_devices(user_id, active_only=True)
        for device in devices:
            if device.is_primary:
                await device_service.update_device(
                    device.id, 
                    user_id, 
                    DeviceUpdate(is_primary=False)
                )
        
        # Set the specified device as primary
        device = await device_service.update_device(
            device_id, 
            user_id, 
            DeviceUpdate(is_primary=True)
        )
        
        logger.info(f"Device {device_id} set as primary for user {user_id}")
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting primary device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set primary device"
        ) 