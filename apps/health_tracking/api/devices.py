"""
Devices API Router
Handles endpoints for health device registration and management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from ..models.devices import DeviceCreate, DeviceUpdate, DeviceResponse
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/", response_model=DeviceResponse)
async def register_device(
    device: DeviceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.register_device(
            user_id=current_user["id"],
            device_data=device.dict()
        )
        return DeviceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        devices = await analytics_service.list_devices(
            user_id=current_user["id"]
        )
        return [DeviceResponse(**device) for device in devices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        device = await analytics_service.get_device(
            user_id=current_user["id"],
            device_id=device_id
        )
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return DeviceResponse(**device)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.update_device(
            user_id=current_user["id"],
            device_id=device_id,
            update_data=device_update.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
        return DeviceResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        analytics_service = HealthAnalyticsService(db)
        success = await analytics_service.delete_device(
            user_id=current_user["id"],
            device_id=device_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Device not found")
        return {"message": "Device deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 