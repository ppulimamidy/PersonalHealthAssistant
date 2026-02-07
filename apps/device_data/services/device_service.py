"""
Device Service
Handles device registration, management, and health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, update, func
from fastapi import HTTPException, status

from common.services.base import BaseService
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience

from ..models.device import (
    Device, DeviceType, DeviceStatus, ConnectionType,
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceSummary,
    DeviceConnectionRequest, DeviceSyncRequest, DeviceHealthCheck
)

logger = get_logger(__name__)


class DeviceService(BaseService):
    """Service for managing health devices"""
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
    
    @property
    def model_class(self):
        return Device
    
    @property
    def schema_class(self):
        return DeviceResponse
    
    @property
    def create_schema_class(self):
        return DeviceCreate
    
    @property
    def update_schema_class(self):
        return DeviceUpdate
    
    async def create_device(self, user_id: UUID, device_data: DeviceCreate) -> Device:
        """Create a new device for a user"""
        try:
            logger.info(f"Creating device for user {user_id}: {device_data.name}")
            
            # Check if device with same serial number or MAC address already exists
            if device_data.serial_number:
                existing = await self._get_device_by_serial(device_data.serial_number)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Device with this serial number already exists"
                    )
            
            if device_data.mac_address:
                existing = await self._get_device_by_mac(device_data.mac_address)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Device with this MAC address already exists"
                    )
            
            # Create device
            device = Device(
                user_id=user_id,
                **device_data.dict()
            )
            
            self.db.add(device)
            await self.db.commit()
            await self.db.refresh(device)
            
            logger.info(f"Device created successfully: {device.id}")
            return device
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create device"
            )
    
    async def get_user_devices(self, user_id: UUID, active_only: bool = True) -> List[Device]:
        """Get all devices for a user"""
        try:
            query = select(Device).where(Device.user_id == user_id)
            
            if active_only:
                query = query.where(Device.is_active == True)
            
            query = query.order_by(Device.created_at.desc())
            
            result = await self.db.execute(query)
            devices = result.scalars().all()
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve devices"
            )
    
    async def get_device(self, device_id: UUID, user_id: UUID) -> Optional[Device]:
        """Get a specific device by ID"""
        try:
            query = select(Device).where(
                and_(
                    Device.id == device_id,
                    Device.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()
            
            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Device not found"
                )
            
            return device
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting device {device_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve device"
            )
    
    async def update_device(self, device_id: UUID, user_id: UUID, device_data: DeviceUpdate) -> Device:
        """Update device information"""
        try:
            device = await self.get_device(device_id, user_id)
            
            # Update fields
            update_data = device_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(device, field, value)
            
            device.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(device)
            
            logger.info(f"Device {device_id} updated successfully")
            return device
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating device {device_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update device"
            )
    
    async def delete_device(self, device_id: UUID, user_id: UUID) -> bool:
        """Delete a device (soft delete)"""
        try:
            device = await self.get_device(device_id, user_id)
            
            device.is_active = False
            device.status = DeviceStatus.INACTIVE
            device.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Device {device_id} deleted successfully")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting device {device_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete device"
            )
    
    async def connect_device(self, device_id: UUID, user_id: UUID, connection_data: DeviceConnectionRequest) -> Device:
        """Connect a device"""
        try:
            device = await self.get_device(device_id, user_id)
            
            # Update connection details
            device.connection_type = connection_data.connection_type
            device.connection_id = connection_data.connection_id
            device.api_key = connection_data.api_key
            device.api_secret = connection_data.api_secret
            
            if connection_data.device_info:
                device.metadata.update(connection_data.device_info)
            
            # Update status
            device.status = DeviceStatus.CONNECTING
            device.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(device)
            
            # Simulate connection process
            await self._simulate_connection(device)
            
            logger.info(f"Device {device_id} connection initiated")
            return device
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error connecting device {device_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect device"
            )
    
    async def sync_device(self, device_id: UUID, user_id: UUID, sync_data: DeviceSyncRequest) -> Dict[str, Any]:
        """Sync data from a device"""
        try:
            device = await self.get_device(device_id, user_id)
            
            # Update sync status
            device.status = DeviceStatus.SYNCING
            device.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Simulate sync process
            sync_result = await self._simulate_sync(device, sync_data)
            
            # Update device after sync
            device.status = DeviceStatus.ACTIVE
            device.last_sync_at = datetime.utcnow()
            device.last_used_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Device {device_id} sync completed: {sync_result}")
            return sync_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error syncing device {device_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to sync device"
            )
    
    async def get_device_health(self, device_id: UUID, user_id: UUID) -> DeviceHealthCheck:
        """Get device health status"""
        try:
            device = await self.get_device(device_id, user_id)
            
            # Calculate health metrics
            health = DeviceHealthCheck(
                device_id=device.id,
                status=device.status,
                battery_level=device.battery_level,
                firmware_version=device.firmware_version,
                connection_quality=self._calculate_connection_quality(device),
                last_sync_status=self._get_last_sync_status(device),
                sync_latency=self._calculate_sync_latency(device)
            )
            
            return health
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting device health {device_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get device health"
            )
    
    async def get_device_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get device statistics for a user"""
        try:
            # Get all devices for the user
            devices_query = select(Device).where(
                and_(
                    Device.user_id == user_id,
                    Device.is_active == True
                )
            )
            
            result = await self.db.execute(devices_query)
            devices = result.scalars().all()
            
            # Count devices by type with details
            devices_by_type = {}
            for device in devices:
                device_type = device.device_type.value
                if device_type not in devices_by_type:
                    devices_by_type[device_type] = {
                        "count": 0,
                        "devices": []
                    }
                devices_by_type[device_type]["count"] += 1
                devices_by_type[device_type]["devices"].append({
                    "id": str(device.id),
                    "name": device.name,
                    "model": device.model,
                    "manufacturer": device.manufacturer,
                    "status": device.status.value,
                    "serial_number": device.serial_number
                })
            
            # Count devices by status
            status_stats = {}
            for device in devices:
                status = device.status.value
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            
            # Get last sync information
            last_sync_query = select(
                func.max(Device.last_sync_at)
            ).where(
                and_(
                    Device.user_id == user_id,
                    Device.is_active == True
                )
            )
            
            result = await self.db.execute(last_sync_query)
            last_sync = result.scalar()
            
            return {
                "total_devices": len(devices),
                "devices_by_type": devices_by_type,
                "devices_by_status": status_stats,
                "last_sync": last_sync,
                "active_devices": status_stats.get(DeviceStatus.ACTIVE.value, 0),
                "connected_devices": sum([
                    status_stats.get(DeviceStatus.ACTIVE.value, 0),
                    status_stats.get(DeviceStatus.SYNCING.value, 0)
                ])
            }
            
        except Exception as e:
            logger.error(f"Error getting device statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get device statistics"
            )
    
    # Private helper methods
    async def _get_device_by_serial(self, serial_number: str) -> Optional[Device]:
        """Get device by serial number"""
        query = select(Device).where(Device.serial_number == serial_number)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_device_by_mac(self, mac_address: str) -> Optional[Device]:
        """Get device by MAC address"""
        query = select(Device).where(Device.mac_address == mac_address)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _simulate_connection(self, device: Device):
        """Simulate device connection process"""
        await asyncio.sleep(2)  # Simulate connection time
        
        # Update device status
        device.status = DeviceStatus.ACTIVE
        device.battery_level = 85  # Simulate battery level
        device.firmware_version = "1.2.3"  # Simulate firmware version
        
        await self.db.commit()
    
    async def _simulate_sync(self, device: Device, sync_data: DeviceSyncRequest) -> Dict[str, Any]:
        """Simulate device sync process"""
        await asyncio.sleep(3)  # Simulate sync time
        
        # Simulate sync results
        return {
            "sync_id": f"sync_{device.id}_{datetime.utcnow().timestamp()}",
            "status": "completed",
            "data_points_synced": 150,
            "sync_duration": 3.2,
            "errors": [],
            "warnings": []
        }
    
    def _calculate_connection_quality(self, device: Device) -> str:
        """Calculate connection quality based on device status and metadata"""
        if device.status == DeviceStatus.ACTIVE:
            return "excellent"
        elif device.status == DeviceStatus.SYNCING:
            return "good"
        elif device.status == DeviceStatus.CONNECTING:
            return "fair"
        else:
            return "poor"
    
    def _get_last_sync_status(self, device: Device) -> str:
        """Get last sync status"""
        if device.last_sync_at:
            time_diff = datetime.utcnow() - device.last_sync_at
            if time_diff < timedelta(hours=1):
                return "recent"
            elif time_diff < timedelta(days=1):
                return "within_24h"
            else:
                return "stale"
        return "never"
    
    def _calculate_sync_latency(self, device: Device) -> Optional[float]:
        """Calculate sync latency"""
        if device.last_sync_at:
            # Simulate latency calculation
            return 2.5
        return None


# Service factory
async def get_device_service(db: AsyncSession) -> DeviceService:
    """Get device service instance"""
    return DeviceService(db) 