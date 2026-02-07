"""
Device Integration Service
Handles integrations with various health device APIs and platforms.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import json
import aiohttp
from abc import ABC, abstractmethod

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience

from ..models.device import Device, DeviceType, DeviceStatus, ConnectionType
from ..models.data_point import DeviceDataPoint, DataType, DataQuality, DataSource
from ..config.oura_config import oura_config

logger = get_logger(__name__)


class DeviceIntegrationError(Exception):
    """Base exception for device integration errors"""
    pass


class DeviceIntegrationBase(ABC):
    """Base class for device integrations"""
    
    def __init__(self, device: Device):
        self.device = device
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the device API"""
        pass
    
    @abstractmethod
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from the device"""
        pass
    
    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the device API"""
        pass


class AppleHealthIntegration(DeviceIntegrationBase):
    """Apple HealthKit integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://health.apple.com/api"
        self.access_token = device.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with Apple HealthKit"""
        try:
            # Apple HealthKit uses OAuth 2.0 with HealthKit entitlements
            # In a real implementation, this would use HealthKit framework
            # For now, we'll simulate the authentication
            
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for Apple Health")
            
            # Simulate HealthKit authentication
            await asyncio.sleep(1)
            
            self.logger.info(f"Apple Health authentication successful for device {self.device.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Apple Health authentication failed: {e}")
            raise DeviceIntegrationError(f"Apple Health authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Apple HealthKit"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            # Simulate Apple HealthKit data sync
            # In real implementation, this would use HealthKit queries
            data_points = []
            
            # Simulate heart rate data
            heart_rate_data = await self._simulate_heart_rate_data(start_date, end_date)
            data_points.extend(heart_rate_data)
            
            # Simulate steps data
            steps_data = await self._simulate_steps_data(start_date, end_date)
            data_points.extend(steps_data)
            
            # Simulate sleep data
            sleep_data = await self._simulate_sleep_data(start_date, end_date)
            data_points.extend(sleep_data)
            
            # Simulate weight data
            weight_data = await self._simulate_weight_data(start_date, end_date)
            data_points.extend(weight_data)
            
            self.logger.info(f"Apple Health sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Apple Health sync failed: {e}")
            raise DeviceIntegrationError(f"Apple Health sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Apple Health device information"""
        try:
            return {
                "device_type": "apple_health",
                "platform": "iOS",
                "version": "15.0+",
                "capabilities": [
                    "heart_rate", "steps", "sleep", "weight", "blood_pressure",
                    "blood_glucose", "oxygen_saturation", "respiratory_rate"
                ],
                "last_sync": datetime.utcnow().isoformat(),
                "status": "connected"
            }
        except Exception as e:
            self.logger.error(f"Failed to get Apple Health device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Apple HealthKit"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Apple Health connection test failed: {e}")
            return False
    
    async def _simulate_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Simulate heart rate data from Apple Health"""
        data_points = []
        current_date = start_date
        
        while current_date <= end_date:
            # Simulate multiple heart rate readings per day
            for hour in range(0, 24, 2):  # Every 2 hours
                timestamp = current_date.replace(hour=hour, minute=0, second=0)
                value = 60 + (hour % 12) * 5 + (timestamp.minute % 30)  # Varying heart rate
                
                data_point = DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.HEART_RATE,
                    value=value,
                    unit="bpm",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "apple_health", "type": "heart_rate"}
                )
                data_points.append(data_point)
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _simulate_steps_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Simulate steps data from Apple Health"""
        data_points = []
        current_date = start_date
        
        while current_date <= end_date:
            # Simulate daily step count
            steps = 8000 + (current_date.day % 7) * 500  # Varying daily steps
            
            data_point = DeviceDataPoint(
                user_id=self.device.user_id,
                device_id=self.device.id,
                data_type=DataType.STEPS_COUNT,
                value=steps,
                unit="steps",
                timestamp=current_date.replace(hour=23, minute=59, second=59),
                source=DataSource.DEVICE_SYNC,
                quality=DataQuality.GOOD,
                metadata={"source": "apple_health", "type": "steps"}
            )
            data_points.append(data_point)
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _simulate_sleep_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Simulate sleep data from Apple Health"""
        data_points = []
        current_date = start_date
        
        while current_date <= end_date:
            # Simulate sleep duration (6-8 hours)
            sleep_hours = 6.5 + (current_date.day % 3) * 0.5
            
            data_point = DeviceDataPoint(
                user_id=self.device.user_id,
                device_id=self.device.id,
                data_type=DataType.SLEEP_DURATION,
                value=sleep_hours,
                unit="hours",
                timestamp=current_date.replace(hour=6, minute=0, second=0),  # Wake up time
                source=DataSource.DEVICE_SYNC,
                quality=DataQuality.GOOD,
                metadata={"source": "apple_health", "type": "sleep"}
            )
            data_points.append(data_point)
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _simulate_weight_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Simulate weight data from Apple Health"""
        data_points = []
        current_date = start_date
        base_weight = 70.0  # kg
        
        while current_date <= end_date:
            # Simulate slight weight variations
            weight = base_weight + (current_date.day % 7) * 0.2 - 0.6
            
            data_point = DeviceDataPoint(
                user_id=self.device.user_id,
                device_id=self.device.id,
                data_type=DataType.BODY_WEIGHT,
                value=weight,
                unit="kg",
                timestamp=current_date.replace(hour=8, minute=0, second=0),
                source=DataSource.DEVICE_SYNC,
                quality=DataQuality.GOOD,
                metadata={"source": "apple_health", "type": "weight"}
            )
            data_points.append(data_point)
            
            current_date += timedelta(days=1)
        
        return data_points


class FitbitIntegration(DeviceIntegrationBase):
    """Fitbit integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://api.fitbit.com/1"
        self.access_token = device.api_key
        self.user_id = device.connection_id
        
    async def authenticate(self) -> bool:
        """Authenticate with Fitbit API"""
        try:
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for Fitbit")
            
            # Test authentication with Fitbit API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/user/-/profile.json", headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Fitbit authentication successful for device {self.device.id}")
                        return True
                    else:
                        raise DeviceIntegrationError(f"Fitbit authentication failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Fitbit authentication failed: {e}")
            raise DeviceIntegrationError(f"Fitbit authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Fitbit"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            # Sync heart rate data
            heart_rate_data = await self._sync_heart_rate_data(start_date, end_date)
            data_points.extend(heart_rate_data)
            
            # Sync steps data
            steps_data = await self._sync_steps_data(start_date, end_date)
            data_points.extend(steps_data)
            
            # Sync sleep data
            sleep_data = await self._sync_sleep_data(start_date, end_date)
            data_points.extend(sleep_data)
            
            # Sync weight data
            weight_data = await self._sync_weight_data(start_date, end_date)
            data_points.extend(weight_data)
            
            self.logger.info(f"Fitbit sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Fitbit sync failed: {e}")
            raise DeviceIntegrationError(f"Fitbit sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Fitbit device information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/user/-/devices.json", headers=headers) as response:
                    if response.status == 200:
                        devices_data = await response.json()
                        return {
                            "device_type": "fitbit",
                            "devices": devices_data,
                            "last_sync": datetime.utcnow().isoformat(),
                            "status": "connected"
                        }
                    else:
                        raise DeviceIntegrationError(f"Failed to get Fitbit devices: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to get Fitbit device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Fitbit API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Fitbit connection test failed: {e}")
            return False
    
    async def _sync_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync heart rate data from Fitbit"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/user/-/activities/heart/date/{date_str}/1d.json"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            # Process heart rate data from Fitbit response
                            # This is a simplified version - real implementation would parse the actual response
                            for interval in data.get('activities-heart-intraday', {}).get('dataset', []):
                                timestamp = datetime.fromisoformat(f"{date_str}T{interval['time']}")
                                value = interval['value']
                                
                                data_point = DeviceDataPoint(
                                    user_id=self.device.user_id,
                                    device_id=self.device.id,
                                    data_type=DataType.HEART_RATE,
                                    value=value,
                                    unit="bpm",
                                    timestamp=timestamp,
                                    source=DataSource.DEVICE_SYNC,
                                    quality=DataQuality.GOOD,
                                    metadata={"source": "fitbit", "type": "heart_rate"}
                                )
                                data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get heart rate data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing heart rate data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _sync_steps_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync steps data from Fitbit"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/user/-/activities/steps/date/{date_str}/1d.json"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            steps = data.get('summary', {}).get('steps', 0)
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.STEPS_COUNT,
                                value=steps,
                                unit="steps",
                                timestamp=current_date.replace(hour=23, minute=59, second=59),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "fitbit", "type": "steps"}
                            )
                            data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get steps data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing steps data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _sync_sleep_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync sleep data from Fitbit"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/user/-/sleep/date/{date_str}.json"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            for sleep in data.get('sleep', []):
                                duration = sleep.get('duration', 0) / 1000 / 60 / 60  # Convert to hours
                                
                                data_point = DeviceDataPoint(
                                    user_id=self.device.user_id,
                                    device_id=self.device.id,
                                    data_type=DataType.SLEEP_DURATION,
                                    value=duration,
                                    unit="hours",
                                    timestamp=datetime.fromisoformat(sleep.get('startTime', '')),
                                    source=DataSource.DEVICE_SYNC,
                                    quality=DataQuality.GOOD,
                                    metadata={"source": "fitbit", "type": "sleep"}
                                )
                                data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get sleep data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing sleep data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _sync_weight_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync weight data from Fitbit"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/user/-/body/log/weight/date/{date_str}.json"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            for weight_log in data.get('weight', []):
                                weight = weight_log.get('weight', 0)
                                
                                data_point = DeviceDataPoint(
                                    user_id=self.device.user_id,
                                    device_id=self.device.id,
                                    data_type=DataType.BODY_WEIGHT,
                                    value=weight,
                                    unit="kg",
                                    timestamp=datetime.fromisoformat(weight_log.get('date', '')),
                                    source=DataSource.DEVICE_SYNC,
                                    quality=DataQuality.GOOD,
                                    metadata={"source": "fitbit", "type": "weight"}
                                )
                                data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get weight data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing weight data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points


class WhoopIntegration(DeviceIntegrationBase):
    """Whoop integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://api.whoop.com/developer/v1"
        self.access_token = device.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with Whoop API"""
        try:
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for Whoop")
            
            # Test authentication with Whoop API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/user/profile", headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Whoop authentication successful for device {self.device.id}")
                        return True
                    else:
                        raise DeviceIntegrationError(f"Whoop authentication failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Whoop authentication failed: {e}")
            raise DeviceIntegrationError(f"Whoop authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Whoop"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            # Sync recovery data
            recovery_data = await self._sync_recovery_data(start_date, end_date)
            data_points.extend(recovery_data)
            
            # Sync sleep data
            sleep_data = await self._sync_sleep_data(start_date, end_date)
            data_points.extend(sleep_data)
            
            # Sync strain data
            strain_data = await self._sync_strain_data(start_date, end_date)
            data_points.extend(strain_data)
            
            # Sync heart rate data
            heart_rate_data = await self._sync_heart_rate_data(start_date, end_date)
            data_points.extend(heart_rate_data)
            
            self.logger.info(f"Whoop sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Whoop sync failed: {e}")
            raise DeviceIntegrationError(f"Whoop sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Whoop device information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/user/profile", headers=headers) as response:
                    if response.status == 200:
                        profile_data = await response.json()
                        return {
                            "device_type": "whoop",
                            "profile": profile_data,
                            "last_sync": datetime.utcnow().isoformat(),
                            "status": "connected"
                        }
                    else:
                        raise DeviceIntegrationError(f"Failed to get Whoop profile: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to get Whoop device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Whoop API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Whoop connection test failed: {e}")
            return False
    
    async def _sync_recovery_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync recovery data from Whoop"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/cycle/{date_str}/recovery"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            recovery_score = data.get('recovery_score', {}).get('score', 0)
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.STRESS_LEVEL,  # Using stress level for recovery
                                value=recovery_score,
                                unit="percentage",
                                timestamp=current_date.replace(hour=6, minute=0, second=0),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "whoop", "type": "recovery"}
                            )
                            data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get recovery data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing recovery data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _sync_sleep_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync sleep data from Whoop"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/cycle/{date_str}/sleep"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            for sleep in data.get('sleep', []):
                                duration = sleep.get('sleep_duration', 0) / 60 / 60  # Convert to hours
                                
                                data_point = DeviceDataPoint(
                                    user_id=self.device.user_id,
                                    device_id=self.device.id,
                                    data_type=DataType.SLEEP_DURATION,
                                    value=duration,
                                    unit="hours",
                                    timestamp=datetime.fromisoformat(sleep.get('start', '')),
                                    source=DataSource.DEVICE_SYNC,
                                    quality=DataQuality.GOOD,
                                    metadata={"source": "whoop", "type": "sleep"}
                                )
                                data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get sleep data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing sleep data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _sync_strain_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync strain data from Whoop"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/cycle/{date_str}/strain"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            strain_score = data.get('strain', {}).get('score', 0)
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.EXERCISE_INTENSITY,  # Using exercise intensity for strain
                                value=strain_score,
                                unit="strain",
                                timestamp=current_date.replace(hour=23, minute=59, second=59),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "whoop", "type": "strain"}
                            )
                            data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get strain data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing strain data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points
    
    async def _sync_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync heart rate data from Whoop"""
        data_points = []
        current_date = start_date
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.api_base_url}/cycle/{date_str}/heart_rate"
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            for hr_data in data.get('heart_rate', []):
                                value = hr_data.get('heart_rate', 0)
                                timestamp = datetime.fromisoformat(hr_data.get('timestamp', ''))
                                
                                data_point = DeviceDataPoint(
                                    user_id=self.device.user_id,
                                    device_id=self.device.id,
                                    data_type=DataType.HEART_RATE,
                                    value=value,
                                    unit="bpm",
                                    timestamp=timestamp,
                                    source=DataSource.DEVICE_SYNC,
                                    quality=DataQuality.GOOD,
                                    metadata={"source": "whoop", "type": "heart_rate"}
                                )
                                data_points.append(data_point)
                        else:
                            self.logger.warning(f"Failed to get heart rate data for {date_str}: {response.status}")
                            
            except Exception as e:
                self.logger.error(f"Error syncing heart rate data for {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        return data_points


class CGMIntegration(DeviceIntegrationBase):
    """Continuous Glucose Monitor integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://api.dexcom.com/v2"
        self.access_token = device.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with CGM API (Dexcom example)"""
        try:
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for CGM")
            
            # Test authentication with CGM API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/users/self", headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"CGM authentication successful for device {self.device.id}")
                        return True
                    else:
                        raise DeviceIntegrationError(f"CGM authentication failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"CGM authentication failed: {e}")
            raise DeviceIntegrationError(f"CGM authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from CGM"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            # Sync glucose readings
            glucose_data = await self._sync_glucose_data(start_date, end_date)
            data_points.extend(glucose_data)
            
            # Sync calibration data
            calibration_data = await self._sync_calibration_data(start_date, end_date)
            data_points.extend(calibration_data)
            
            # Sync events (meals, exercise, etc.)
            events_data = await self._sync_events_data(start_date, end_date)
            data_points.extend(events_data)
            
            self.logger.info(f"CGM sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"CGM sync failed: {e}")
            raise DeviceIntegrationError(f"CGM sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get CGM device information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/users/self", headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        return {
                            "device_type": "cgm",
                            "user": user_data,
                            "last_sync": datetime.utcnow().isoformat(),
                            "status": "connected"
                        }
                    else:
                        raise DeviceIntegrationError(f"Failed to get CGM user info: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to get CGM device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to CGM API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"CGM connection test failed: {e}")
            return False
    
    async def _sync_glucose_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync glucose readings from CGM"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/self/egvs?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for egv in data.get('egvs', []):
                            value = egv.get('value', 0)
                            timestamp = datetime.fromisoformat(egv.get('systemTime', ''))
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.BLOOD_GLUCOSE,
                                value=value,
                                unit="mg/dL",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "cgm", "type": "glucose"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get glucose data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing glucose data: {e}")
        
        return data_points
    
    async def _sync_calibration_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync calibration data from CGM"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/self/calibrations?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for cal in data.get('calibrations', []):
                            value = cal.get('value', 0)
                            timestamp = datetime.fromisoformat(cal.get('systemTime', ''))
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.BLOOD_GLUCOSE,  # Calibration affects glucose readings
                                value=value,
                                unit="mg/dL",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.EXCELLENT,
                                metadata={"source": "cgm", "type": "calibration"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get calibration data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing calibration data: {e}")
        
        return data_points
    
    async def _sync_events_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync events data from CGM"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/self/events?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for event in data.get('events', []):
                            event_type = event.get('eventType', '')
                            timestamp = datetime.fromisoformat(event.get('systemTime', ''))
                            
                            # Map event types to data types
                            if event_type == 'meal':
                                data_type = DataType.HUNGER_LEVEL
                                value = 100  # Full after meal
                                unit = "percentage"
                            elif event_type == 'exercise':
                                data_type = DataType.EXERCISE_INTENSITY
                                value = 75  # Moderate exercise
                                unit = "intensity"
                            else:
                                continue
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=data_type,
                                value=value,
                                unit=unit,
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "cgm", "type": "event", "event_type": event_type}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get events data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing events data: {e}")
        
        return data_points


class OuraRingIntegration(DeviceIntegrationBase):
    """Oura Ring integration using dedicated API client"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.access_token = device.api_key
        from .oura_client import OuraAPIClient
        
        # Check if sandbox mode is enabled
        use_sandbox = oura_config.use_sandbox or device.metadata.get("sandbox", False)
        self.client = OuraAPIClient(
            access_token=self.access_token, 
            use_sandbox=use_sandbox,
            user_id=str(device.user_id)  # Pass user_id for sandbox data generation
        )
        
    async def authenticate(self) -> bool:
        """Authenticate with Oura Ring API"""
        try:
            # In sandbox mode, we don't need an access token
            if not self.access_token and not self.client.use_sandbox:
                raise DeviceIntegrationError("No access token provided for Oura Ring")
            
            async with self.client as client:
                return await client.test_connection()
                        
        except Exception as e:
            self.logger.error(f"Oura Ring authentication failed: {e}")
            raise DeviceIntegrationError(f"Oura Ring authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Oura Ring"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            async with self.client as client:
                # Get all data types concurrently
                all_data = await client.get_all_data(start_date, end_date)
                
                # Process sleep data
            if all_data.get("daily_sleep"):
                sleep_data = await self._process_sleep_data(all_data["daily_sleep"])
                data_points.extend(sleep_data)
            
            # Process activity data
            if all_data.get("daily_activity"):
                activity_data = await self._process_activity_data(all_data["daily_activity"])
                data_points.extend(activity_data)
            
            # Process readiness data
            if all_data.get("daily_readiness"):
                readiness_data = await self._process_readiness_data(all_data["daily_readiness"])
                data_points.extend(readiness_data)
            
            # Process heart rate data
            if all_data.get("heart_rate"):
                heart_rate_data = await self._process_heart_rate_data(all_data["heart_rate"])
                data_points.extend(heart_rate_data)
            
            # Process workout data
            if all_data.get("workout"):
                workout_data = await self._process_workout_data(all_data["workout"])
                data_points.extend(workout_data)
            
            # Process session data
            if all_data.get("session"):
                session_data = await self._process_session_data(all_data["session"])
                data_points.extend(session_data)
            
            self.logger.info(f"Oura Ring sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Oura Ring sync failed: {e}")
            raise DeviceIntegrationError(f"Oura Ring sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Oura Ring device information"""
        try:
            async with self.client as client:
                user_info = await client.get_user_info()
                personal_info = await client.get_personal_info()
                
                return {
                    "device_type": "oura_ring",
                    "user": user_info,
                    "personal_info": personal_info,
                    "last_sync": datetime.utcnow().isoformat(),
                    "status": "connected",
                    "supported_data_types": [
                        "sleep", "activity", "readiness", "heart_rate", 
                        "workout", "session", "temperature"
                    ]
                }
                        
        except Exception as e:
            self.logger.error(f"Failed to get Oura Ring device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Oura Ring API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Oura Ring connection test failed: {e}")
            return False
    
    async def _process_sleep_data(self, sleep_data: Dict[str, Any]) -> List[DeviceDataPoint]:
        """Process sleep data from Oura API response"""
        data_points = []
        
        for sleep in sleep_data.get('data', []):
            day = sleep.get('day')
            sleep_info = sleep.get('sleep', {})
            
            if not day or not sleep_info:
                continue
                
            timestamp = datetime.fromisoformat(day)
            
            # Sleep duration (convert seconds to hours)
            duration = sleep_info.get('total_sleep_duration', 0) / 3600
            if duration > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.SLEEP_DURATION,
                    value=duration,
                    unit="hours",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "total_sleep_duration"}
                ))
                            
            # Sleep efficiency
            efficiency = sleep_info.get('sleep_efficiency', 0)
            if efficiency > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.SLEEP_EFFICIENCY,
                    value=efficiency,
                    unit="percentage",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "sleep_efficiency"}
                ))
            
            # Sleep latency (time to fall asleep in minutes)
            latency = sleep_info.get('sleep_latency', 0)
            if latency > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.SLEEP_LATENCY,
                    value=latency,
                    unit="minutes",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "sleep_latency"}
                ))
            
            # Sleep stages (REM, Deep, Light, Awake)
            for stage, field in [
                ("rem", "rem_sleep_duration"),
                ("deep", "deep_sleep_duration"),
                ("light", "light_sleep_duration"),
                ("awake", "awake_time")
            ]:
                duration = sleep_info.get(field, 0) / 3600  # Convert to hours
                if duration > 0:
                    data_points.append(DeviceDataPoint(
                        user_id=self.device.user_id,
                        device_id=self.device.id,
                        data_type=DataType.SLEEP_STAGES,
                        value=duration,
                        unit="hours",
                        timestamp=timestamp,
                        source=DataSource.DEVICE_SYNC,
                        quality=DataQuality.GOOD,
                        metadata={"source": "oura_ring", "type": "sleep", "stage": stage, "field": field}
                    ))
            
            # Sleep score
            score = sleep_info.get('sleep_score', 0)
            if score > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.SLEEP_SCORE,
                    value=score,
                    unit="score",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "sleep_score"}
                ))
            
            # Heart rate during sleep
            hr_lowest = sleep_info.get('hr_lowest', 0)
            if hr_lowest > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.HEART_RATE,
                    value=hr_lowest,
                    unit="bpm",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "hr_lowest"}
                ))
            
            hr_average = sleep_info.get('hr_average', 0)
            if hr_average > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.HEART_RATE,
                    value=hr_average,
                    unit="bpm",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "hr_average"}
                ))
            
            # Respiratory rate
            resp_rate = sleep_info.get('respiratory_rate', 0)
            if resp_rate > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.RESPIRATORY_RATE,
                    value=resp_rate,
                    unit="breaths_per_minute",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "respiratory_rate"}
                ))
            
            # Temperature deviation
            temp_deviation = sleep_info.get('temperature_deviation', 0)
            if temp_deviation != 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.BODY_TEMPERATURE,
                    value=temp_deviation,
                    unit="celsius_deviation",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "sleep", "field": "temperature_deviation"}
                ))
        
        return data_points
    
    async def _process_activity_data(self, activity_data: Dict[str, Any]) -> List[DeviceDataPoint]:
        """Process activity data from Oura API response"""
        data_points = []
        
        for activity in activity_data.get('data', []):
            day = activity.get('day')
            activity_info = activity.get('activity', {})
            
            if not day or not activity_info:
                continue
                
            timestamp = datetime.fromisoformat(day)
            
                            # Steps
            steps = activity_info.get('steps', 0)
            if steps > 0:
                data_points.append(DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.STEPS_COUNT,
                                value=steps,
                                unit="steps",
                    timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "activity", "field": "steps"}
                ))
            
            # Total calories
            calories_total = activity_info.get('calories_total', 0)
            if calories_total > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.CALORIES_BURNED,
                    value=calories_total,
                    unit="calories",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "activity", "field": "calories_total"}
                ))
            
            # Active calories
            calories_active = activity_info.get('calories_active', 0)
            if calories_active > 0:
                data_points.append(DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.CALORIES_BURNED,
                    value=calories_active,
                                unit="calories",
                    timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "activity", "field": "calories_active"}
                ))
            
            # Activity score
            activity_score = activity_info.get('score', 0)
            if activity_score > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.ACTIVE_MINUTES,
                    value=activity_score,
                    unit="score",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "activity", "field": "score"}
                ))
            
            # Daily movement
            daily_movement = activity_info.get('daily_movement', 0)
            if daily_movement > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.ACTIVE_MINUTES,
                    value=daily_movement,
                    unit="score",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "activity", "field": "daily_movement"}
                ))
            
            # MET minutes by intensity
            for intensity, field in [
                ("inactive", "met_min_inactive"),
                ("low", "met_min_low"),
                ("medium", "met_min_medium"),
                ("high", "met_min_high")
            ]:
                met_min = activity_info.get(field, 0)
                if met_min > 0:
                    data_points.append(DeviceDataPoint(
                        user_id=self.device.user_id,
                        device_id=self.device.id,
                        data_type=DataType.ACTIVE_MINUTES,
                        value=met_min,
                        unit="minutes",
                        timestamp=timestamp,
                        source=DataSource.DEVICE_SYNC,
                        quality=DataQuality.GOOD,
                        metadata={"source": "oura_ring", "type": "activity", "intensity": intensity, "field": field}
                    ))
        
        return data_points
    
    async def _process_readiness_data(self, readiness_data: Dict[str, Any]) -> List[DeviceDataPoint]:
        """Process readiness data from Oura API response"""
        data_points = []
        
        for readiness in readiness_data.get('data', []):
            day = readiness.get('day')
            readiness_info = readiness.get('readiness', {})
            
            if not day or not readiness_info:
                continue
                
            timestamp = datetime.fromisoformat(day)
            
            # Overall readiness score
            score = readiness_info.get('score', 0)
            if score > 0:
                data_points.append(DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.READINESS_SCORE,
                                value=score,
                                unit="score",
                    timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "readiness", "field": "score"}
                ))
            
            # Component scores
            for component, field in [
                ("previous_night", "score_previous_night"),
                ("sleep_balance", "score_sleep_balance"),
                ("previous_day_activity", "score_previous_day_activity"),
                ("activity_balance", "score_activity_balance"),
                ("resting_hr", "score_resting_hr"),
                ("hrv_balance", "score_hrv_balance"),
                ("recovery_index", "score_recovery_index"),
                ("temperature", "score_temperature")
            ]:
                component_score = readiness_info.get(field, 0)
                if component_score > 0:
                    data_points.append(DeviceDataPoint(
                        user_id=self.device.user_id,
                        device_id=self.device.id,
                        data_type=DataType.RECOVERY_SCORE,
                        value=component_score,
                        unit="score",
                        timestamp=timestamp,
                        source=DataSource.DEVICE_SYNC,
                        quality=DataQuality.GOOD,
                        metadata={"source": "oura_ring", "type": "readiness", "component": component, "field": field}
                    ))
            
            # Resting heart rate
            resting_hr = readiness_info.get('resting_hr', 0)
            if resting_hr > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.HEART_RATE,
                    value=resting_hr,
                    unit="bpm",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "readiness", "field": "resting_hr"}
                ))
            
            # HRV balance
            hrv_balance = readiness_info.get('hrv_balance', 0)
            if hrv_balance > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.HEART_RATE_VARIABILITY,
                    value=hrv_balance,
                    unit="score",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "readiness", "field": "hrv_balance"}
                ))
        
        return data_points
    
    async def _process_heart_rate_data(self, heart_rate_data: Dict[str, Any]) -> List[DeviceDataPoint]:
        """Process heart rate data from Oura API response"""
        data_points = []
        
        for hr_data in heart_rate_data.get('data', []):
            timestamp_str = hr_data.get('timestamp')
            hr = hr_data.get('heart_rate', 0)
            
            if not timestamp_str or hr <= 0:
                continue
                
            timestamp = datetime.fromisoformat(timestamp_str)
                            
            data_points.append(DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.HEART_RATE,
                value=hr,
                                unit="bpm",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "oura_ring", "type": "heart_rate"}
            ))
        
        return data_points
    
    async def _process_workout_data(self, workout_data: Dict[str, Any]) -> List[DeviceDataPoint]:
        """Process workout data from Oura API response"""
        data_points = []
        
        for workout in workout_data.get('data', []):
            day = workout.get('day')
            workout_info = workout.get('workout', {})
            
            if not day or not workout_info:
                continue
                
            timestamp = datetime.fromisoformat(day)
            
            # Workout duration
            duration = workout_info.get('duration', 0) / 60  # Convert to minutes
            if duration > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.EXERCISE_DURATION,
                    value=duration,
                    unit="minutes",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "workout", "field": "duration"}
                ))
            
            # Calories burned during workout
            calories = workout_info.get('calories', 0)
            if calories > 0:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.CALORIES_BURNED,
                    value=calories,
                    unit="calories",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "workout", "field": "calories"}
                ))
        
        return data_points
    
    async def _process_session_data(self, session_data: Dict[str, Any]) -> List[DeviceDataPoint]:
        """Process session data from Oura API response"""
        data_points = []
        
        for session in session_data.get('data', []):
            day = session.get('day')
            session_info = session.get('session', {})
            
            if not day or not session_info:
                continue
                
            timestamp = datetime.fromisoformat(day)
            
            # Session duration
            duration = session_info.get('duration', 0) / 60  # Convert to minutes
            if duration > 0:
                data_points.append(DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                    data_type=DataType.EXERCISE_DURATION,
                    value=duration,
                    unit="minutes",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "session", "field": "duration"}
                ))
            
            # Session type
            session_type = session_info.get('type', '')
            if session_type:
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.WORKOUT_TYPE,
                    value=1,  # Use 1 to indicate presence of session type
                    unit="count",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    metadata={"source": "oura_ring", "type": "session", "session_type": session_type}
                ))
        
        return data_points


class DexcomIntegration(DeviceIntegrationBase):
    """Dexcom CGM integration using dedicated API client"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.access_token = device.api_key
        from .dexcom_sandbox_client import DexcomSandboxClient
        from ..config.dexcom_config import dexcom_config
        
        # Check if sandbox mode is enabled
        use_sandbox = dexcom_config.use_sandbox or device.device_metadata.get("sandbox", False)
        
        if use_sandbox:
            # Use sandbox user from device metadata if available
            sandbox_user = device.device_metadata.get("sandbox_user", "User7")  # Default to User7
            self.client = DexcomSandboxClient(user_id=sandbox_user)
            self.logger.info(f"🔧 Using Dexcom Sandbox Client for device {device.id} with sandbox user {sandbox_user}")
        else:
            # TODO: Implement real Dexcom API client
            self.client = DexcomSandboxClient(user_id=str(device.user_id))
            self.logger.warning(f"⚠️ Real Dexcom API client not implemented yet, using sandbox for device {device.id}")
        
    async def authenticate(self) -> bool:
        """Authenticate with Dexcom API"""
        try:
            # Check if OAuth is completed for sandbox mode
            if self.device.device_metadata.get("sandbox", False):
                if not self.device.device_metadata.get("oauth_completed", False):
                    raise DeviceIntegrationError("OAuth not completed for Dexcom sandbox. Please complete OAuth flow first.")
                # In sandbox mode, we don't need a real access token
                self.logger.info(f"🔧 Sandbox authentication successful for device {self.device.id}")
                return True
            else:
                # For real API, we need an access token
                if not self.access_token:
                    raise DeviceIntegrationError("No access token provided for Dexcom")
            
            async with self.client as client:
                return await client.test_connection()
                        
        except Exception as e:
            self.logger.error(f"Dexcom authentication failed: {e}")
            raise DeviceIntegrationError(f"Dexcom authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Dexcom CGM"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            async with self.client as client:
                # Get all data types concurrently
                all_data = await client.get_all_data(start_date, end_date)
                
                # Process glucose data (EGVs)
                if all_data.get("egvs"):
                    glucose_data = await self._process_glucose_data(all_data["egvs"])
                    data_points.extend(glucose_data)
                
                # Process calibration data
                if all_data.get("calibrations"):
                    calibration_data = await self._process_calibration_data(all_data["calibrations"])
                    data_points.extend(calibration_data)
                
                # Process events (insulin, carbs, etc.)
                if all_data.get("events"):
                    events_data = await self._process_events_data(all_data["events"])
                    data_points.extend(events_data)
                
                # Process alerts
                if all_data.get("alerts"):
                    alerts_data = await self._process_alerts_data(all_data["alerts"])
                    data_points.extend(alerts_data)
            
            self.logger.info(f"Dexcom sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Dexcom sync failed: {e}")
            raise DeviceIntegrationError(f"Dexcom sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Dexcom device information"""
        try:
            async with self.client as client:
                user_info = await client.get_user_info()
                devices = await client.get_devices()
                statistics = await client.get_statistics()
                
                return {
                    "device_type": "dexcom_cgm",
                    "user": user_info,
                    "devices": devices.get("devices", []),
                    "statistics": statistics.get("statistics", {}),
                    "last_sync": datetime.utcnow().isoformat(),
                    "status": "connected",
                    "supported_data_types": [
                        "continuous_glucose", "glucose_calibration", "insulin_event", 
                        "carb_event", "glucose_alert", "glucose_trend", 
                        "sensor_status", "transmitter_status"
                    ]
                }
                        
        except Exception as e:
            self.logger.error(f"Failed to get Dexcom device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Dexcom API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Dexcom connection test failed: {e}")
            return False
    
    async def _process_glucose_data(self, egvs: List[Dict[str, Any]]) -> List[DeviceDataPoint]:
        """Process Estimated Glucose Values (EGVs)"""
        data_points = []
        
        for egv in egvs:
            try:
                timestamp = datetime.fromisoformat(egv.get("systemTime", egv.get("displayTime")))
                value = egv.get("value", 0)
                trend = egv.get("trend", "NotComputable")
                status = egv.get("status", "OK")
                
                # Create glucose data point
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.CONTINUOUS_GLUCOSE,
                    value=value,
                    unit="mg/dL",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD if status == "OK" else DataQuality.FAIR,
                    raw_value=str(egv),
                    data_metadata={
                        "trend": trend,
                        "trend_rate": egv.get("trendRate"),
                        "glucose_change_rate": egv.get("glucoseChangeRate"),
                        "status": status,
                        "source": "dexcom_egv"
                    },
                    tags=["glucose", "cgm", "dexcom"]
                ))
                
                # Create trend data point if trend is available
                if trend and trend != "NotComputable":
                    trend_value = self._convert_trend_to_value(trend)
                    data_points.append(DeviceDataPoint(
                        user_id=self.device.user_id,
                        device_id=self.device.id,
                        data_type=DataType.GLUCOSE_TREND,
                        value=trend_value,
                        unit="trend_index",
                        timestamp=timestamp,
                        source=DataSource.DEVICE_SYNC,
                        quality=DataQuality.GOOD,
                        raw_value=trend,
                        data_metadata={
                            "trend": trend,
                            "source": "dexcom_trend"
                        },
                        tags=["glucose_trend", "cgm", "dexcom"]
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error processing glucose data point: {e}")
                continue
        
        return data_points
    
    async def _process_calibration_data(self, calibrations: List[Dict[str, Any]]) -> List[DeviceDataPoint]:
        """Process calibration data"""
        data_points = []
        
        for calibration in calibrations:
            try:
                timestamp = datetime.fromisoformat(calibration.get("systemTime", calibration.get("displayTime")))
                value = calibration.get("value", 0)
                calib_type = calibration.get("type", "Finger")
                
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.GLUCOSE_CALIBRATION,
                    value=value,
                    unit="mg/dL",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.EXCELLENT,
                    raw_value=str(calibration),
                    data_metadata={
                        "calibration_type": calib_type,
                        "transmitter_id": calibration.get("transmitterId"),
                        "transmitter_ticks": calibration.get("transmitterTicks"),
                        "source": "dexcom_calibration"
                    },
                    tags=["calibration", "cgm", "dexcom"]
                ))
                
            except Exception as e:
                self.logger.error(f"Error processing calibration data point: {e}")
                continue
        
        return data_points
    
    async def _process_events_data(self, events: List[Dict[str, Any]]) -> List[DeviceDataPoint]:
        """Process events data (insulin, carbs, etc.)"""
        data_points = []
        
        for event in events:
            try:
                timestamp = datetime.fromisoformat(event.get("systemTime", event.get("displayTime")))
                event_type = event.get("eventType", "")
                value = event.get("value", 0)
                unit = event.get("unit", "")
                sub_type = event.get("eventSubType", "")
                
                if event_type == "Insulin":
                    data_type = DataType.INSULIN_EVENT
                    tags = ["insulin", "medication", "dexcom"]
                elif event_type == "Carbs":
                    data_type = DataType.CARB_EVENT
                    tags = ["carbs", "nutrition", "dexcom"]
                else:
                    # Skip unknown event types
                    continue
                
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=data_type,
                    value=value,
                    unit=unit,
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD,
                    raw_value=str(event),
                    data_metadata={
                        "event_type": event_type,
                        "event_sub_type": sub_type,
                        "source": "dexcom_event"
                    },
                    tags=tags
                ))
                
            except Exception as e:
                self.logger.error(f"Error processing event data point: {e}")
                continue
        
        return data_points
    
    async def _process_alerts_data(self, alerts: List[Dict[str, Any]]) -> List[DeviceDataPoint]:
        """Process alerts data"""
        data_points = []
        
        for alert in alerts:
            try:
                timestamp = datetime.fromisoformat(alert.get("systemTime", alert.get("displayTime")))
                alert_type = alert.get("alertType", "")
                value = alert.get("value", 0)
                status = alert.get("status", "Active")
                
                data_points.append(DeviceDataPoint(
                    user_id=self.device.user_id,
                    device_id=self.device.id,
                    data_type=DataType.GLUCOSE_ALERT,
                    value=value,
                    unit="mg/dL",
                    timestamp=timestamp,
                    source=DataSource.DEVICE_SYNC,
                    quality=DataQuality.GOOD if status == "Active" else DataQuality.FAIR,
                    raw_value=str(alert),
                    data_metadata={
                        "alert_type": alert_type,
                        "status": status,
                        "source": "dexcom_alert"
                    },
                    tags=["alert", "glucose", "cgm", "dexcom"]
                ))
                
            except Exception as e:
                self.logger.error(f"Error processing alert data point: {e}")
                continue
        
        return data_points
    
    def _convert_trend_to_value(self, trend: str) -> int:
        """Convert Dexcom trend string to numeric value"""
        trend_map = {
            "DoubleUp": 7,
            "SingleUp": 6,
            "FortyFiveUp": 5,
            "Flat": 4,
            "FortyFiveDown": 3,
            "SingleDown": 2,
            "DoubleDown": 1,
            "NotComputable": 0,
            "RateOutOfRange": -1
        }
        return trend_map.get(trend, 0)


class GarminIntegration(DeviceIntegrationBase):
    """Garmin Connect integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://connect.garmin.com/modern/proxy"
        self.access_token = device.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with Garmin Connect API"""
        try:
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for Garmin")
            
            # Test authentication with Garmin API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/userprofile-service/socialProfile", headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Garmin authentication successful for device {self.device.id}")
                        return True
                    else:
                        raise DeviceIntegrationError(f"Garmin authentication failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Garmin authentication failed: {e}")
            raise DeviceIntegrationError(f"Garmin authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Garmin Connect"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            # Sync daily summary
            daily_data = await self._sync_daily_summary(start_date, end_date)
            data_points.extend(daily_data)
            
            # Sync heart rate data
            heart_rate_data = await self._sync_heart_rate_data(start_date, end_date)
            data_points.extend(heart_rate_data)
            
            # Sync sleep data
            sleep_data = await self._sync_sleep_data(start_date, end_date)
            data_points.extend(sleep_data)
            
            # Sync activities
            activity_data = await self._sync_activities(start_date, end_date)
            data_points.extend(activity_data)
            
            self.logger.info(f"Garmin sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Garmin sync failed: {e}")
            raise DeviceIntegrationError(f"Garmin sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Garmin device information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/userprofile-service/socialProfile", headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        return {
                            "device_type": "garmin",
                            "user": user_data,
                            "last_sync": datetime.utcnow().isoformat(),
                            "status": "connected"
                        }
                    else:
                        raise DeviceIntegrationError(f"Failed to get Garmin user info: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to get Garmin device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Garmin Connect API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Garmin connection test failed: {e}")
            return False
    
    async def _sync_daily_summary(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync daily summary data from Garmin"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/usersummary-service/stats/daily/{start_str}/{end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for day in data:
                            # Steps
                            steps = day.get('steps', 0)
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.STEPS_COUNT,
                                value=steps,
                                unit="steps",
                                timestamp=datetime.fromisoformat(day.get('calendarDate', '')),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "garmin", "type": "steps"}
                            )
                            data_points.append(data_point)
                            
                            # Calories
                            calories = day.get('calories', 0)
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.CALORIES_BURNED,
                                value=calories,
                                unit="calories",
                                timestamp=datetime.fromisoformat(day.get('calendarDate', '')),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "garmin", "type": "calories"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Garmin daily summary: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Garmin daily summary: {e}")
        
        return data_points
    
    async def _sync_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync heart rate data from Garmin"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/heartrate-service/rest/range/{start_str}/{end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for hr_data in data.get('heartRateValues', []):
                            value = hr_data.get('value', 0)
                            timestamp = datetime.fromtimestamp(hr_data.get('timestamp', 0) / 1000)
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.HEART_RATE,
                                value=value,
                                unit="bpm",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "garmin", "type": "heart_rate"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Garmin heart rate data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Garmin heart rate data: {e}")
        
        return data_points
    
    async def _sync_sleep_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync sleep data from Garmin"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/sleep-service/rest/sleeps/{start_str}/{end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for sleep in data.get('sleeps', []):
                            duration = sleep.get('sleep_duration', 0) / 3600  # Convert to hours
                            timestamp = datetime.fromisoformat(sleep.get('day', ''))
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.SLEEP_DURATION,
                                value=duration,
                                unit="hours",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "garmin", "type": "sleep"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Garmin sleep data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Garmin sleep data: {e}")
        
        return data_points
    
    async def _sync_activities(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync activity data from Garmin"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/activitylist-service/activities/{start_str}/{end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for activity in data.get('activities', []):
                            duration = activity.get('duration', 0) / 60  # Convert to minutes
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.EXERCISE_DURATION,
                                value=duration,
                                unit="minutes",
                                timestamp=datetime.fromisoformat(activity.get('startTime', '')),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "garmin", "type": "activity", "activity_type": activity.get('activityType', '')}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Garmin activities: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Garmin activities: {e}")
        
        return data_points


class SamsungHealthIntegration(DeviceIntegrationBase):
    """Samsung Health integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://api.samsung.com/health"
        self.access_token = device.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with Samsung Health API"""
        try:
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for Samsung Health")
            
            # Test authentication with Samsung Health API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/v1/user/profile", headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Samsung Health authentication successful for device {self.device.id}")
                        return True
                    else:
                        raise DeviceIntegrationError(f"Samsung Health authentication failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Samsung Health authentication failed: {e}")
            raise DeviceIntegrationError(f"Samsung Health authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Samsung Health"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            # Sync steps data
            steps_data = await self._sync_steps_data(start_date, end_date)
            data_points.extend(steps_data)
            
            # Sync heart rate data
            heart_rate_data = await self._sync_heart_rate_data(start_date, end_date)
            data_points.extend(heart_rate_data)
            
            # Sync sleep data
            sleep_data = await self._sync_sleep_data(start_date, end_date)
            data_points.extend(sleep_data)
            
            # Sync weight data
            weight_data = await self._sync_weight_data(start_date, end_date)
            data_points.extend(weight_data)
            
            self.logger.info(f"Samsung Health sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Samsung Health sync failed: {e}")
            raise DeviceIntegrationError(f"Samsung Health sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Samsung Health device information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/v1/user/profile", headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        return {
                            "device_type": "samsung_health",
                            "user": user_data,
                            "last_sync": datetime.utcnow().isoformat(),
                            "status": "connected"
                        }
                    else:
                        raise DeviceIntegrationError(f"Failed to get Samsung Health user info: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to get Samsung Health device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Samsung Health API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Samsung Health connection test failed: {e}")
            return False
    
    async def _sync_steps_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync steps data from Samsung Health"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/v1/data/steps?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for step_data in data.get('data', []):
                            value = step_data.get('value', 0)
                            timestamp = datetime.fromisoformat(step_data.get('date', ''))
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.STEPS_COUNT,
                                value=value,
                                unit="steps",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "samsung_health", "type": "steps"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Samsung Health steps data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Samsung Health steps data: {e}")
        
        return data_points
    
    async def _sync_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync heart rate data from Samsung Health"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/v1/data/heart_rate?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for hr_data in data.get('data', []):
                            value = hr_data.get('value', 0)
                            timestamp = datetime.fromisoformat(hr_data.get('date', ''))
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.HEART_RATE,
                                value=value,
                                unit="bpm",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "samsung_health", "type": "heart_rate"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Samsung Health heart rate data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Samsung Health heart rate data: {e}")
        
        return data_points
    
    async def _sync_sleep_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync sleep data from Samsung Health"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/v1/data/sleep?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for sleep in data.get('data', []):
                            duration = sleep.get('duration', 0) / 3600  # Convert to hours
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.SLEEP_DURATION,
                                value=duration,
                                unit="hours",
                                timestamp=datetime.fromisoformat(sleep.get('date', '')),
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "samsung_health", "type": "sleep"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Samsung Health sleep data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Samsung Health sleep data: {e}")
        
        return data_points
    
    async def _sync_weight_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync weight data from Samsung Health"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/v1/data/weight?startDate={start_str}&endDate={end_str}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for weight in data.get('data', []):
                            value = weight.get('value', 0)
                            timestamp = datetime.fromisoformat(weight.get('date', ''))
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.BODY_WEIGHT,
                                value=value,
                                unit="kg",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "samsung_health", "type": "weight"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Samsung Health weight data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Samsung Health weight data: {e}")
        
        return data_points


class GoogleFitIntegration(DeviceIntegrationBase):
    """Google Fit integration"""
    
    def __init__(self, device: Device):
        super().__init__(device)
        self.api_base_url = "https://www.googleapis.com/fitness/v1"
        self.access_token = device.api_key
        
    async def authenticate(self) -> bool:
        """Authenticate with Google Fit API"""
        try:
            if not self.access_token:
                raise DeviceIntegrationError("No access token provided for Google Fit")
            
            # Test authentication with Google Fit API
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/users/me/dataSources", headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Google Fit authentication successful for device {self.device.id}")
                        return True
                    else:
                        raise DeviceIntegrationError(f"Google Fit authentication failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Google Fit authentication failed: {e}")
            raise DeviceIntegrationError(f"Google Fit authentication failed: {e}")
    
    async def sync_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from Google Fit"""
        try:
            if not await self.authenticate():
                raise DeviceIntegrationError("Authentication failed")
            
            data_points = []
            
            # Sync steps data
            steps_data = await self._sync_steps_data(start_date, end_date)
            data_points.extend(steps_data)
            
            # Sync heart rate data
            heart_rate_data = await self._sync_heart_rate_data(start_date, end_date)
            data_points.extend(heart_rate_data)
            
            # Sync sleep data
            sleep_data = await self._sync_sleep_data(start_date, end_date)
            data_points.extend(sleep_data)
            
            # Sync weight data
            weight_data = await self._sync_weight_data(start_date, end_date)
            data_points.extend(weight_data)
            
            self.logger.info(f"Google Fit sync completed: {len(data_points)} data points")
            return data_points
            
        except Exception as e:
            self.logger.error(f"Google Fit sync failed: {e}")
            raise DeviceIntegrationError(f"Google Fit sync failed: {e}")
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Google Fit device information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/users/me/dataSources", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "device_type": "google_fit",
                            "data_sources": data.get('dataSource', []),
                            "last_sync": datetime.utcnow().isoformat(),
                            "status": "connected"
                        }
                    else:
                        raise DeviceIntegrationError(f"Failed to get Google Fit data sources: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to get Google Fit device info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to Google Fit API"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Google Fit connection test failed: {e}")
            return False
    
    async def _sync_steps_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync steps data from Google Fit"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_nanos = int(start_date.timestamp() * 1000000000)
        end_nanos = int(end_date.timestamp() * 1000000000)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/me/dataset:aggregate"
                payload = {
                    "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
                    "bucketByTime": {"durationMillis": 86400000},  # 24 hours
                    "startTimeMillis": start_nanos // 1000000,
                    "endTimeMillis": end_nanos // 1000000
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        for bucket in data.get('bucket', []):
                            for dataset in bucket.get('dataset', []):
                                for point in dataset.get('point', []):
                                    value = point.get('value', [{}])[0].get('intVal', 0)
                                    timestamp = datetime.fromtimestamp(point.get('startTimeNanos', 0) / 1000000000)
                                    
                                    data_point = DeviceDataPoint(
                                        user_id=self.device.user_id,
                                        device_id=self.device.id,
                                        data_type=DataType.STEPS_COUNT,
                                        value=value,
                                        unit="steps",
                                        timestamp=timestamp,
                                        source=DataSource.DEVICE_SYNC,
                                        quality=DataQuality.GOOD,
                                        metadata={"source": "google_fit", "type": "steps"}
                                    )
                                    data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Google Fit steps data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Google Fit steps data: {e}")
        
        return data_points
    
    async def _sync_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync heart rate data from Google Fit"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_nanos = int(start_date.timestamp() * 1000000000)
        end_nanos = int(end_date.timestamp() * 1000000000)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/me/dataset:aggregate"
                payload = {
                    "aggregateBy": [{"dataTypeName": "com.google.heart_rate.bpm"}],
                    "bucketByTime": {"durationMillis": 3600000},  # 1 hour
                    "startTimeMillis": start_nanos // 1000000,
                    "endTimeMillis": end_nanos // 1000000
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        for hr_data in data.get('heartRateValues', []):
                            value = hr_data.get('value', 0)
                            timestamp = datetime.fromtimestamp(hr_data.get('timestamp', 0) / 1000)
                            
                            data_point = DeviceDataPoint(
                                user_id=self.device.user_id,
                                device_id=self.device.id,
                                data_type=DataType.HEART_RATE,
                                value=value,
                                unit="bpm",
                                timestamp=timestamp,
                                source=DataSource.DEVICE_SYNC,
                                quality=DataQuality.GOOD,
                                metadata={"source": "google_fit", "type": "heart_rate"}
                            )
                            data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Google Fit heart rate data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Google Fit heart rate data: {e}")
        
        return data_points
    
    async def _sync_sleep_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync sleep data from Google Fit"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_nanos = int(start_date.timestamp() * 1000000000)
        end_nanos = int(end_date.timestamp() * 1000000000)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/me/dataset:aggregate"
                payload = {
                    "aggregateBy": [{"dataTypeName": "com.google.sleep.segment"}],
                    "bucketByTime": {"durationMillis": 86400000},  # 24 hours
                    "startTimeMillis": start_nanos // 1000000,
                    "endTimeMillis": end_nanos // 1000000
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        for bucket in data.get('bucket', []):
                            for dataset in bucket.get('dataset', []):
                                for point in dataset.get('point', []):
                                    duration = (point.get('endTimeNanos', 0) - point.get('startTimeNanos', 0)) / 3600000000000  # Convert to hours
                                    timestamp = datetime.fromtimestamp(point.get('startTimeNanos', 0) / 1000000000)
                                    
                                    data_point = DeviceDataPoint(
                                        user_id=self.device.user_id,
                                        device_id=self.device.id,
                                        data_type=DataType.SLEEP_DURATION,
                                        value=duration,
                                        unit="hours",
                                        timestamp=timestamp,
                                        source=DataSource.DEVICE_SYNC,
                                        quality=DataQuality.GOOD,
                                        metadata={"source": "google_fit", "type": "sleep"}
                                    )
                                    data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Google Fit sleep data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Google Fit sleep data: {e}")
        
        return data_points
    
    async def _sync_weight_data(self, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync weight data from Google Fit"""
        data_points = []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        start_nanos = int(start_date.timestamp() * 1000000000)
        end_nanos = int(end_date.timestamp() * 1000000000)
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/users/me/dataset:aggregate"
                payload = {
                    "aggregateBy": [{"dataTypeName": "com.google.weight"}],
                    "bucketByTime": {"durationMillis": 86400000},  # 24 hours
                    "startTimeMillis": start_nanos // 1000000,
                    "endTimeMillis": end_nanos // 1000000
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        for bucket in data.get('bucket', []):
                            for dataset in bucket.get('dataset', []):
                                for point in dataset.get('point', []):
                                    value = point.get('value', [{}])[0].get('fpVal', 0)
                                    timestamp = datetime.fromtimestamp(point.get('startTimeNanos', 0) / 1000000000)
                                    
                                    data_point = DeviceDataPoint(
                                        user_id=self.device.user_id,
                                        device_id=self.device.id,
                                        data_type=DataType.BODY_WEIGHT,
                                        value=value,
                                        unit="kg",
                                        timestamp=timestamp,
                                        source=DataSource.DEVICE_SYNC,
                                        quality=DataQuality.GOOD,
                                        metadata={"source": "google_fit", "type": "weight"}
                                    )
                                    data_points.append(data_point)
                    else:
                        self.logger.warning(f"Failed to get Google Fit weight data: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing Google Fit weight data: {e}")
        
        return data_points


class DeviceIntegrationFactory:
    """Factory for creating device integrations"""
    
    @staticmethod
    def create_integration(device: Device) -> DeviceIntegrationBase:
        """Create the appropriate integration based on device type"""
        device_type = device.device_type.lower()
        
        print(f"🔍 Creating integration for device type: '{device_type}'")
        
        # Map device types to integration classes
        integration_map = {
            # Wearables
            "apple_health": AppleHealthIntegration,
            "fitbit": FitbitIntegration,
            "whoop": WhoopIntegration,
            "oura_ring": OuraRingIntegration,
            "garmin": GarminIntegration,
            "samsung_health": SamsungHealthIntegration,
            "google_fit": GoogleFitIntegration,
            
            # Smart Watches
            "apple_watch": AppleHealthIntegration,
            "samsung_galaxy_watch": SamsungHealthIntegration,
            "garmin_fenix": GarminIntegration,
            "garmin_forerunner": GarminIntegration,
            "garmin_vivoactive": GarminIntegration,
            "fitbit_versa": FitbitIntegration,
            "fitbit_sense": FitbitIntegration,
            "fitbit_charge": FitbitIntegration,
            
            # Fitness Trackers
            "fitbit_inspire": FitbitIntegration,
            "fitbit_ace": FitbitIntegration,
            "garmin_vivosmart": GarminIntegration,
            "garmin_vivofit": GarminIntegration,
            
            # Smart Rings
            "oura_ring_gen3": OuraRingIntegration,
            "oura_ring_gen2": OuraRingIntegration,
            "motiv_ring": None,  # TODO: Implement Motiv Ring integration
            "mcube_ring": None,  # TODO: Implement Mcube Ring integration
            
            # Medical Devices
            "dexcom_g6": DexcomIntegration,
            "dexcom_g7": DexcomIntegration,
            "continuous_glucose_monitor": DexcomIntegration,
            "cgm": DexcomIntegration,
            "freestyle_libre": CGMIntegration,
            "medtronic_guardian": CGMIntegration,
            "tandem_tslim": CGMIntegration,
            "omnipod": CGMIntegration,
            
            # Blood Pressure Monitors
            "omron_blood_pressure": None,  # TODO: Implement Omron integration
            "qardio_arm": None,  # TODO: Implement Qardio integration
            "withings_bpm": None,  # TODO: Implement Withings integration
            
            # Scales
            "withings_body": None,  # TODO: Implement Withings integration
            "fitbit_aria": FitbitIntegration,
            "garmin_index": GarminIntegration,
            "qardio_base": None,  # TODO: Implement Qardio integration
            
            # Sleep Trackers
            "withings_sleep": None,  # TODO: Implement Withings integration
            "resmed_airsense": None,  # TODO: Implement ResMed integration
            "philips_dreamstation": None,  # TODO: Implement Philips integration
            
            # Smart Clothing
            "hexoskin": None,  # TODO: Implement Hexoskin integration
            "om_signal": None,  # TODO: Implement OMsignal integration
            "athos": None,  # TODO: Implement Athos integration
            
            # Smart Shoes
            "nike_adapt": None,  # TODO: Implement Nike integration
            "under_armour_hovr": None,  # TODO: Implement Under Armour integration
            
            # Smart Glasses
            "google_glass": GoogleFitIntegration,
            "vuzix": None,  # TODO: Implement Vuzix integration
            
            # Smart Earbuds
            "apple_airpods": AppleHealthIntegration,
            "samsung_galaxy_buds": SamsungHealthIntegration,
            "jabra_elite": None,  # TODO: Implement Jabra integration
            
            # Mobile Apps & Platforms
            "myfitnesspal": None,  # TODO: Implement MyFitnessPal integration
            "cronometer": None,  # TODO: Implement Cronometer integration
            "lose_it": None,  # TODO: Implement Lose It integration
            "noom": None,  # TODO: Implement Noom integration
            "headspace": None,  # TODO: Implement Headspace integration
            "calm": None,  # TODO: Implement Calm integration
            
            # Smart Home Health
            "withings_body_cardio": None,  # TODO: Implement Withings integration
            "qardio_base_2": None,  # TODO: Implement Qardio integration
            "nokia_body": None,  # TODO: Implement Nokia integration
            
            # Fertility Trackers
            "ava_bracelet": None,  # TODO: Implement Ava integration
            "tempdrop": None,  # TODO: Implement Tempdrop integration
            "ovusense": None,  # TODO: Implement OvuSense integration
            
            # Baby Monitors
            "owlet_smart_sock": None,  # TODO: Implement Owlet integration
            "snuza_hero": None,  # TODO: Implement Snuza integration
            
            # Pet Health Trackers
            "fitbark": None,  # TODO: Implement FitBark integration
            "whistle": None,  # TODO: Implement Whistle integration
            
            # Generic types that map to existing integrations
            "wearable": FitbitIntegration,  # Default to Fitbit for generic wearables
            "smartwatch": AppleHealthIntegration,  # Default to Apple Health for smartwatches
            "fitness_tracker": FitbitIntegration,  # Default to Fitbit for fitness trackers
            "smart_ring": OuraRingIntegration,  # Default to Oura for smart rings
            "glucose_monitor": CGMIntegration,  # Default to CGM for glucose monitors
            "blood_glucose_meter": CGMIntegration,
            "insulin_pump": CGMIntegration,
            "heart_rate_monitor": GarminIntegration,  # Default to Garmin for heart rate monitors
            "sleep_tracker": OuraRingIntegration,  # Default to Oura for sleep trackers
            "scale": None,  # TODO: Implement generic scale integration
            "blood_pressure_monitor": None,  # TODO: Implement generic BP monitor integration
            "thermometer": None,  # TODO: Implement generic thermometer integration
            "oxygen_monitor": None,  # TODO: Implement generic oxygen monitor integration
            "ecg_monitor": AppleHealthIntegration,  # Default to Apple Health for ECG
            "pulse_oximeter": None,  # TODO: Implement generic pulse oximeter integration
            "blood_pressure_cuff": None,  # TODO: Implement generic BP cuff integration
            "therapy_device": None,  # TODO: Implement generic therapy device integration
            "medication_dispenser": None,  # TODO: Implement generic medication dispenser integration
            "cpap_machine": None,  # TODO: Implement generic CPAP integration
            "inhaler": None,  # TODO: Implement generic inhaler integration
            "hearing_aid": None,  # TODO: Implement generic hearing aid integration
            "prosthetic": None,  # TODO: Implement generic prosthetic integration
            "mobile_app": GoogleFitIntegration,  # Default to Google Fit for mobile apps
            "health_platform": GoogleFitIntegration,  # Default to Google Fit for health platforms
            "fitness_app": GoogleFitIntegration,  # Default to Google Fit for fitness apps
            "nutrition_app": None,  # TODO: Implement generic nutrition app integration
            "meditation_app": None,  # TODO: Implement generic meditation app integration
            "smart_mirror": None,  # TODO: Implement generic smart mirror integration
            "smart_toilet": None,  # TODO: Implement generic smart toilet integration
            "smart_shower": None,  # TODO: Implement generic smart shower integration
            "air_quality_monitor": None,  # TODO: Implement generic air quality monitor integration
            "water_quality_monitor": None,  # TODO: Implement generic water quality monitor integration
            "fertility_tracker": None,  # TODO: Implement generic fertility tracker integration
            "pregnancy_monitor": None,  # TODO: Implement generic pregnancy monitor integration
            "baby_monitor": None,  # TODO: Implement generic baby monitor integration
            "pet_health_tracker": None,  # TODO: Implement generic pet health tracker integration
            "athletic_performance": GarminIntegration,  # Default to Garmin for athletic performance
            "clinical_device": None,  # TODO: Implement generic clinical device integration
            "research_device": None,  # TODO: Implement generic research device integration
            "lab_equipment": None,  # TODO: Implement generic lab equipment integration
            "other": None,  # No integration for other devices
        }
        
        # Get the integration class
        integration_class = integration_map.get(device_type)
        
        print(f"🔍 Integration class found: {integration_class}")
        
        if integration_class is None:
            raise DeviceIntegrationError(f"No integration available for device type: {device_type}")
        
        return integration_class(device)


class DeviceIntegrationService:
    """Service for managing device integrations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def sync_device_data(self, device: Device, start_date: datetime, end_date: datetime) -> List[DeviceDataPoint]:
        """Sync data from a device using the appropriate integration"""
        try:
            integration = DeviceIntegrationFactory.create_integration(device)
            return await integration.sync_data(start_date, end_date)
        except Exception as e:
            self.logger.error(f"Failed to sync device {device.id}: {e}")
            raise DeviceIntegrationError(f"Device sync failed: {e}")
    
    async def test_device_connection(self, device: Device) -> bool:
        """Test connection to a device"""
        try:
            integration = DeviceIntegrationFactory.create_integration(device)
            return await integration.test_connection()
        except Exception as e:
            self.logger.error(f"Failed to test device {device.id} connection: {e}")
            return False
    
    async def get_device_info(self, device: Device) -> Dict[str, Any]:
        """Get device information"""
        try:
            integration = DeviceIntegrationFactory.create_integration(device)
            return await integration.get_device_info()
        except Exception as e:
            self.logger.error(f"Failed to get device {device.id} info: {e}")
            raise DeviceIntegrationError(f"Failed to get device info: {e}")


# Service factory
async def get_device_integration_service() -> DeviceIntegrationService:
    """Get device integration service instance"""
    return DeviceIntegrationService() 