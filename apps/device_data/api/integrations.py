"""
Device Integration API Endpoints
Handles integrations with various health device APIs and platforms.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from pydantic import BaseModel

from common.database.connection import get_async_db
from common.middleware.rate_limiter import rate_limit
from common.utils.logging import get_logger
from common.config.settings import get_settings

from ..models.device import Device, DeviceType, DeviceStatus
from ..models.data_point import DataPointCreate, DataPointResponse
from ..services.device_service import DeviceService, get_device_service
from ..services.data_service import DataService, get_data_service
from ..services.device_integrations import get_device_integration_service, DeviceIntegrationError
from ..models.integration import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse, IntegrationSummary,
    IntegrationConnectionRequest, IntegrationSyncRequest, IntegrationHealthCheck
)

logger = get_logger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


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


@router.post("/{device_id}/connect", response_model=Dict[str, Any])
async def connect_device_integration(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Connect to a device integration (Apple Health, Fitbit, Whoop, CGM).
    
    - **device_id**: Device to connect
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        integration_service = await get_device_integration_service()
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Test connection
        connection_success = await integration_service.test_device_connection(device)
        
        if connection_success:
            # Update device status
            device.status = DeviceStatus.ACTIVE
            device.updated_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Device {device_id} integration connected successfully")
            return {
                "success": True,
                "message": "Device connected successfully",
                "device_id": device_id,
                "status": "connected"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to connect to device integration"
            )
            
    except HTTPException:
        raise
    except DeviceIntegrationError as e:
        logger.error(f"Device integration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error connecting device integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect device integration"
        )


@router.post("/{device_id}/sync", response_model=Dict[str, Any])
async def sync_device_data(
    device_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for sync"),
    end_date: Optional[datetime] = Query(None, description="End date for sync"),
    background_tasks: BackgroundTasks = None,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Sync data from a device integration.
    
    - **device_id**: Device to sync
    - **start_date**: Start date for data sync (default: 7 days ago)
    - **end_date**: End date for data sync (default: now)
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        data_service = await get_data_service(db)
        integration_service = await get_device_integration_service()
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Update device status to syncing
        device.status = DeviceStatus.SYNCING
        device.updated_at = datetime.utcnow()
        await db.commit()
        
        # Sync data from integration
        data_points = await integration_service.sync_device_data(device, start_date, end_date)
        
        # Save data points to database
        saved_points = []
        for data_point in data_points:
            # Convert to DataPointCreate format
            point_data = DataPointCreate(
                device_id=device_id,
                data_type=data_point.data_type,
                value=data_point.value,
                unit=data_point.unit,
                timestamp=data_point.timestamp,
                source=data_point.source,
                quality=data_point.quality,
                raw_value=data_point.raw_value,
                data_metadata=data_point.data_metadata if hasattr(data_point, 'data_metadata') and data_point.data_metadata is not None else {},
                tags=data_point.tags if data_point.tags is not None else []
            )
            
            saved_point = await data_service.create_data_point(user_id, point_data)
            saved_points.append(saved_point)
        
        # Update device status
        device.status = DeviceStatus.ACTIVE
        device.last_sync_at = datetime.utcnow()
        device.last_used_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Device {device_id} sync completed: {len(saved_points)} data points")
        return {
            "success": True,
            "message": "Device sync completed successfully",
            "device_id": device_id,
            "data_points_synced": len(saved_points),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "sync_id": f"sync_{device_id}_{datetime.utcnow().timestamp()}"
        }
        
    except HTTPException:
        raise
    except DeviceIntegrationError as e:
        logger.error(f"Device integration error: {e}")
        # Update device status to error
        device.status = DeviceStatus.ERROR
        device.updated_at = datetime.utcnow()
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error syncing device data: {e}")
        # Update device status to error
        device.status = DeviceStatus.ERROR
        device.updated_at = datetime.utcnow()
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync device data"
        )


@router.get("/{device_id}/info", response_model=Dict[str, Any])
async def get_device_integration_info(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get device integration information and status.
    
    - **device_id**: Device to get info for
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        integration_service = await get_device_integration_service()
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Get integration info
        integration_info = await integration_service.get_device_info(device)
        
        return {
            "device_id": device_id,
            "device_name": device.name,
            "device_type": device.device_type,
            "integration_info": integration_info,
            "last_sync": device.last_sync_at.isoformat() if device.last_sync_at else None,
            "status": device.status.value,
            "connection_status": "connected" if device.status == DeviceStatus.ACTIVE else "disconnected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device integration info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device integration info"
        )


@router.post("/{device_id}/test", response_model=Dict[str, Any])
async def test_device_integration(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Test device integration connection.
    
    - **device_id**: Device to test
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        integration_service = await get_device_integration_service()
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Test connection
        connection_success = await integration_service.test_device_connection(device)
        
        return {
            "device_id": device_id,
            "connection_success": connection_success,
            "tested_at": datetime.utcnow().isoformat(),
            "message": "Connection test completed successfully" if connection_success else "Connection test failed"
        }
        
    except HTTPException:
        raise
    except DeviceIntegrationError as e:
        logger.error(f"Device integration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error testing device integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test device integration"
        )


@router.get("/supported", response_model=List[Dict[str, Any]])
async def get_supported_integrations():
    """
    Get list of supported device integrations.
    """
    try:
        return [
            {
                "name": "Apple Health",
                "type": "apple_health",
                "description": "Apple HealthKit integration for iOS devices",
                "supported_metrics": [
                    "heart_rate", "steps", "sleep", "weight", "blood_pressure",
                    "blood_glucose", "oxygen_saturation", "respiratory_rate"
                ],
                "authentication": "OAuth 2.0 with HealthKit entitlements",
                "api_docs": "https://developer.apple.com/documentation/healthkit"
            },
            {
                "name": "Fitbit",
                "type": "fitbit",
                "description": "Fitbit wearable device integration",
                "supported_metrics": [
                    "heart_rate", "steps", "sleep", "weight", "calories_burned",
                    "distance_walked", "active_minutes", "exercise_duration"
                ],
                "authentication": "OAuth 2.0",
                "api_docs": "https://dev.fitbit.com/build/reference/web-api/"
            },
            {
                "name": "Whoop",
                "type": "whoop",
                "description": "Whoop fitness tracker integration",
                "supported_metrics": [
                    "heart_rate", "sleep", "recovery", "strain", "respiratory_rate"
                ],
                "authentication": "OAuth 2.0",
                "api_docs": "https://developer.whoop.com/"
            },
            {
                "name": "Continuous Glucose Monitor (CGM)",
                "type": "cgm",
                "description": "CGM device integration (Dexcom, etc.)",
                "supported_metrics": [
                    "blood_glucose", "calibration", "events"
                ],
                "authentication": "OAuth 2.0",
                "api_docs": "https://developer.dexcom.com/"
            },
            {
                "name": "Oura Ring",
                "type": "oura_ring",
                "description": "Oura smart ring for sleep and recovery",
                "supported_metrics": [
                    "heart_rate", "sleep", "readiness", "activity", "temperature"
                ],
                "authentication": "OAuth 2.0",
                "api_docs": "https://cloud.ouraring.com/docs/"
            }
        ]
        
    except Exception as e:
        logger.error(f"Error getting supported integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported integrations"
        )


@router.post("/{device_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_device_integration(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Disconnect from a device integration.
    
    - **device_id**: Device to disconnect
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Update device status
        device.status = DeviceStatus.DISCONNECTED
        device.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Device {device_id} integration disconnected")
        return {
            "success": True,
            "message": "Device disconnected successfully",
            "device_id": device_id,
            "status": "disconnected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting device integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect device integration"
        )


@router.get("/{device_id}/sync-status", response_model=Dict[str, Any])
async def get_device_sync_status(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get device sync status and history.
    
    - **device_id**: Device to get sync status for
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Get recent data points count
        data_service = await get_data_service(db)
        recent_points, _ = await data_service.get_data_points(
            user_id,
            data_service.DataPointQuery(
                device_id=device_id,
                limit=1,
                offset=0
            )
        )
        
        return {
            "device_id": device_id,
            "device_name": device.name,
            "device_type": device.device_type,
            "status": device.status,
            "last_sync_at": device.last_sync_at.isoformat() if device.last_sync_at else None,
            "last_used_at": device.last_used_at.isoformat() if device.last_used_at else None,
            "total_data_points": len(recent_points) if recent_points else 0,
            "connection_quality": "good" if device.status == DeviceStatus.ACTIVE else "poor"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device sync status"
        )


@router.post("/{device_id}/sync-schedule", response_model=Dict[str, Any])
async def schedule_device_sync(
    device_id: UUID,
    sync_interval_hours: int = Query(24, description="Sync interval in hours"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Schedule automatic device sync.
    
    - **device_id**: Device to schedule sync for
    - **sync_interval_hours**: Sync interval in hours
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Update device settings with sync schedule
        device.settings["sync_schedule"] = {
            "enabled": True,
            "interval_hours": sync_interval_hours,
            "last_scheduled": datetime.utcnow().isoformat()
        }
        device.updated_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Device {device_id} sync scheduled every {sync_interval_hours} hours")
        return {
            "success": True,
            "message": f"Device sync scheduled every {sync_interval_hours} hours",
            "device_id": device_id,
            "sync_interval_hours": sync_interval_hours,
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling device sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule device sync"
        )


@router.get("/discover", response_model=List[Dict[str, Any]])
async def discover_available_devices(
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Discover available devices that can be integrated.
    
    Returns a list of discoverable devices and their capabilities.
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        
        # Get user's existing devices
        existing_devices = await device_service.get_user_devices(user_id)
        existing_device_types = {device.device_type for device in existing_devices}
        
        # Define discoverable device types and their capabilities
        discoverable_devices = [
            {
                "device_type": "apple_health",
                "name": "Apple Health",
                "description": "iOS Health app integration",
                "capabilities": ["heart_rate", "steps", "sleep", "weight", "blood_pressure", "blood_glucose"],
                "connection_type": "oauth2",
                "is_connected": "apple_health" in existing_device_types,
                "icon": "🍎",
                "category": "mobile_platform"
            },
            {
                "device_type": "fitbit",
                "name": "Fitbit",
                "description": "Fitbit wearable devices and app",
                "capabilities": ["heart_rate", "steps", "sleep", "weight", "calories", "activity"],
                "connection_type": "oauth2",
                "is_connected": "fitbit" in existing_device_types,
                "icon": "📱",
                "category": "wearable"
            },
            {
                "device_type": "whoop",
                "name": "WHOOP",
                "description": "WHOOP fitness and recovery tracker",
                "capabilities": ["heart_rate", "sleep", "recovery", "strain", "respiratory_rate"],
                "connection_type": "oauth2",
                "is_connected": "whoop" in existing_device_types,
                "icon": "💪",
                "category": "wearable"
            },
            {
                "device_type": "oura_ring",
                "name": "Oura Ring",
                "description": "Oura smart ring for sleep and recovery",
                "capabilities": ["heart_rate", "sleep", "readiness", "activity", "temperature"],
                "connection_type": "oauth2",
                "is_connected": "oura_ring" in existing_device_types,
                "icon": "💍",
                "category": "smart_ring"
            },
            {
                "device_type": "garmin",
                "name": "Garmin Connect",
                "description": "Garmin fitness devices and platform",
                "capabilities": ["heart_rate", "steps", "sleep", "activity", "gps", "training"],
                "connection_type": "oauth2",
                "is_connected": "garmin" in existing_device_types,
                "icon": "🏃",
                "category": "wearable"
            },
            {
                "device_type": "samsung_health",
                "name": "Samsung Health",
                "description": "Samsung Health app and devices",
                "capabilities": ["heart_rate", "steps", "sleep", "weight", "exercise"],
                "connection_type": "oauth2",
                "is_connected": "samsung_health" in existing_device_types,
                "icon": "📱",
                "category": "mobile_platform"
            },
            {
                "device_type": "google_fit",
                "name": "Google Fit",
                "description": "Google Fit health platform",
                "capabilities": ["heart_rate", "steps", "sleep", "weight", "activity"],
                "connection_type": "oauth2",
                "is_connected": "google_fit" in existing_device_types,
                "icon": "🤖",
                "category": "mobile_platform"
            },
            {
                "device_type": "dexcom_g6",
                "name": "Dexcom G6",
                "description": "Dexcom G6 Continuous Glucose Monitor",
                "capabilities": ["glucose", "calibration", "alerts"],
                "connection_type": "oauth2",
                "is_connected": "dexcom_g6" in existing_device_types,
                "icon": "🩸",
                "category": "medical_device"
            },
            {
                "device_type": "dexcom_g7",
                "name": "Dexcom G7",
                "description": "Dexcom G7 Continuous Glucose Monitor",
                "capabilities": ["glucose", "calibration", "alerts"],
                "connection_type": "oauth2",
                "is_connected": "dexcom_g7" in existing_device_types,
                "icon": "🩸",
                "category": "medical_device"
            },
            {
                "device_type": "freestyle_libre",
                "name": "FreeStyle Libre",
                "description": "Abbott FreeStyle Libre CGM",
                "capabilities": ["glucose", "calibration", "trends"],
                "connection_type": "oauth2",
                "is_connected": "freestyle_libre" in existing_device_types,
                "icon": "🩸",
                "category": "medical_device"
            }
        ]
        
        return discoverable_devices
        
    except Exception as e:
        logger.error(f"Error discovering devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover devices"
        )


@router.post("/bulk-sync", response_model=Dict[str, Any])
async def bulk_sync_devices(
    device_ids: List[UUID],
    start_date: Optional[datetime] = Query(None, description="Start date for sync"),
    end_date: Optional[datetime] = Query(None, description="End date for sync"),
    background_tasks: BackgroundTasks = None,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Sync data from multiple devices in bulk.
    
    - **device_ids**: List of device IDs to sync
    - **start_date**: Start date for data sync (default: 7 days ago)
    - **end_date**: End date for data sync (default: now)
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        data_service = await get_data_service(db)
        integration_service = await get_device_integration_service()
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        results = []
        total_data_points = 0
        
        for device_id in device_ids:
            try:
                # Get device
                device = await device_service.get_device(device_id, user_id)
                
                # Update device status to syncing
                device.status = DeviceStatus.SYNCING
                device.updated_at = datetime.utcnow()
                await db.commit()
                
                # Sync data from integration
                data_points = await integration_service.sync_device_data(device, start_date, end_date)
                
                # Save data points to database
                saved_points = []
                for data_point in data_points:
                    point_data = DataPointCreate(
                        device_id=device_id,
                        data_type=data_point.data_type,
                        value=data_point.value,
                        unit=data_point.unit,
                        timestamp=data_point.timestamp,
                        source=data_point.source,
                        quality=data_point.quality,
                        raw_value=data_point.raw_value,
                        metadata=data_point.metadata,
                        tags=data_point.tags
                    )
                    
                    saved_point = await data_service.create_data_point(user_id, point_data)
                    saved_points.append(saved_point)
                
                # Update device status
                device.status = DeviceStatus.ACTIVE
                device.last_sync_at = datetime.utcnow()
                device.last_used_at = datetime.utcnow()
                await db.commit()
                
                total_data_points += len(saved_points)
                results.append({
                    "device_id": device_id,
                    "device_name": device.name,
                    "device_type": device.device_type,
                    "status": "success",
                    "data_points_synced": len(saved_points),
                    "error": None
                })
                
            except Exception as e:
                logger.error(f"Error syncing device {device_id}: {e}")
                # Update device status to error
                device.status = DeviceStatus.ERROR
                device.updated_at = datetime.utcnow()
                await db.commit()
                
                results.append({
                    "device_id": device_id,
                    "device_name": device.name if 'device' in locals() else "Unknown",
                    "device_type": device.device_type if 'device' in locals() else "Unknown",
                    "status": "error",
                    "data_points_synced": 0,
                    "error": str(e)
                })
        
        logger.info(f"Bulk sync completed: {len(results)} devices, {total_data_points} total data points")
        return {
            "success": True,
            "message": "Bulk sync completed",
            "total_devices": len(device_ids),
            "successful_syncs": len([r for r in results if r["status"] == "success"]),
            "failed_syncs": len([r for r in results if r["status"] == "error"]),
            "total_data_points": total_data_points,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk sync"
        )


@router.get("/{device_id}/data-export", response_model=Dict[str, Any])
async def export_device_data(
    device_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    format: str = Query("json", description="Export format (json, csv, excel)"),
    data_types: Optional[List[str]] = Query(None, description="Specific data types to export"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Export device data in various formats.
    
    - **device_id**: Device to export data from
    - **start_date**: Start date for export (default: 30 days ago)
    - **end_date**: End date for export (default: now)
    - **format**: Export format (json, csv, excel)
    - **data_types**: Specific data types to export
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        data_service = await get_data_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get data points
        data_points = await data_service.get_device_data_points(
            user_id, device_id, start_date, end_date, data_types
        )
        
        # Convert to export format
        export_data = []
        for point in data_points:
            export_data.append({
                "timestamp": point.timestamp.isoformat(),
                "data_type": point.data_type,
                "value": point.value,
                "unit": point.unit,
                "quality": point.quality,
                "source": point.source,
                "metadata": point.metadata
            })
        
        # Generate export based on format
        if format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "timestamp", "data_type", "value", "unit", "quality", "source", "metadata"
            ])
            writer.writeheader()
            writer.writerows(export_data)
            
            return {
                "success": True,
                "format": "csv",
                "device_id": device_id,
                "device_name": device.name,
                "data_points": len(export_data),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data": output.getvalue()
            }
        
        elif format.lower() == "excel":
            # For Excel export, we'd need to implement Excel generation
            # For now, return JSON with a note
            return {
                "success": True,
                "format": "excel",
                "device_id": device_id,
                "device_name": device.name,
                "data_points": len(export_data),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "note": "Excel export not yet implemented, returning JSON format",
                "data": export_data
            }
        
        else:  # Default to JSON
            return {
                "success": True,
                "format": "json",
                "device_id": device_id,
                "device_name": device.name,
                "data_points": len(export_data),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data": export_data
            }
        
    except Exception as e:
        logger.error(f"Error exporting device data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export device data"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_integrations_health(
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get health status of all device integrations.
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        integration_service = await get_device_integration_service()
        
        # Get user's devices
        devices = await device_service.get_user_devices(user_id)
        
        health_status = []
        for device in devices:
            try:
                # Test connection
                connection_healthy = await integration_service.test_device_connection(device)
                
                # Get device info
                device_info = await integration_service.get_device_info(device)
                
                health_status.append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "device_type": device.device_type,
                    "status": device.status,
                    "connection_healthy": connection_healthy,
                    "last_sync": device.last_sync_at.isoformat() if device.last_sync_at else None,
                    "last_used": device.last_used_at.isoformat() if device.last_used_at else None,
                    "device_info": device_info,
                    "error": None
                })
                
            except Exception as e:
                health_status.append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "device_type": device.device_type,
                    "status": device.status,
                    "connection_healthy": False,
                    "last_sync": device.last_sync_at.isoformat() if device.last_sync_at else None,
                    "last_used": device.last_used_at.isoformat() if device.last_used_at else None,
                    "device_info": None,
                    "error": str(e)
                })
        
        # Calculate overall health
        total_devices = len(health_status)
        healthy_devices = len([d for d in health_status if d["connection_healthy"]])
        active_devices = len([d for d in health_status if d["status"] == DeviceStatus.ACTIVE])
        
        return {
            "success": True,
            "overall_health": {
                "total_devices": total_devices,
                "healthy_connections": healthy_devices,
                "active_devices": active_devices,
                "health_percentage": (healthy_devices / total_devices * 100) if total_devices > 0 else 0
            },
            "devices": health_status
        }
        
    except Exception as e:
        logger.error(f"Error getting integrations health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get integrations health"
        )


@router.post("/{device_id}/reconnect", response_model=Dict[str, Any])
async def reconnect_device_integration(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reconnect a device integration (useful for expired tokens).
    
    - **device_id**: Device to reconnect
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        integration_service = await get_device_integration_service()
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Test connection
        connection_success = await integration_service.test_device_connection(device)
        
        if connection_success:
            # Update device status
            device.status = DeviceStatus.ACTIVE
            device.updated_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Device {device_id} reconnected successfully")
            return {
                "success": True,
                "message": "Device reconnected successfully",
                "device_id": device_id,
                "status": "reconnected"
            }
        else:
            # Update device status to error
            device.status = DeviceStatus.ERROR
            device.updated_at = datetime.utcnow()
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reconnect device integration"
            )
            
    except HTTPException:
        raise
    except DeviceIntegrationError as e:
        logger.error(f"Device integration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reconnecting device integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reconnect device integration"
        ) 

# Dexcom OAuth Endpoints
@router.get("/{device_id}/oauth/authorize", response_model=Dict[str, Any])
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
        
        if dexcom_config.use_sandbox or device.metadata.get("sandbox", False):
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


@router.post("/{device_id}/oauth/callback", response_model=Dict[str, Any])
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


@router.get("/{device_id}/oauth/status", response_model=Dict[str, Any])
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

@router.get("/{device_id}/sync", response_model=Dict[str, Any])
async def get_device_sync_info(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get device sync information and status.
    
    - **device_id**: Device to get sync info for
    """
    try:
        user_id = current_user.id
        device_service = await get_device_service(db)
        data_service = await get_data_service(db)
        
        # Get device
        device = await device_service.get_device(device_id, user_id)
        
        # Get recent data points count
        recent_data_points = await data_service.get_data_points(
            user_id=user_id,
            device_id=device_id,
            limit=1
        )
        
        # Get data summary for this device
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