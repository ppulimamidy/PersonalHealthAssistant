"""
Device Anomaly Agent
Autonomously detects anomalies in device behavior and performance.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseDeviceAgent, AgentResult
from ..models.device import Device, DeviceStatus
from ..models.data_point import DeviceDataPoint, DataType
from common.utils.logging import get_logger
from apps.device_data.services.event_producer import get_event_producer

logger = get_logger(__name__)

class DeviceAnomalyAgent(BaseDeviceAgent):
    """
    Autonomous agent for detecting anomalies in device behavior.
    Monitors device performance, connection stability, and data patterns.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="device_anomaly_detector",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "connection_drop_threshold": 3,  # Number of connection drops
            "battery_drain_threshold": 0.3,  # 30% battery drop per day
            "data_volume_threshold": 0.5,  # 50% change in data volume
            "error_rate_threshold": 0.1,  # 10% error rate
            "sync_failure_threshold": 2,  # Number of sync failures
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process device data to detect behavioral anomalies.
        
        Args:
            data: Dictionary containing user_id and optional device_id filter
            db: Database session
            
        Returns:
            AgentResult with detected anomalies and recommendations
        """
        user_id = data.get("user_id")
        device_id = data.get("device_id")
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Get user's devices
            devices = await self._get_user_devices(user_id, device_id, db)
            
            if not devices:
                return AgentResult(
                    success=True,
                    data={"anomalies": [], "message": "No devices found"}
                )
            
            anomalies = []
            insights = []
            alerts = []
            recommendations = []
            
            # Analyze each device
            for device in devices:
                device_anomalies = await self._analyze_device_anomalies(device, db)
                anomalies.extend(device_anomalies)
                
                # Generate device-specific insights
                device_insights = self._generate_device_insights(device, device_anomalies)
                insights.extend(device_insights)
                
                # Generate alerts for critical anomalies
                device_alerts = self._generate_device_alerts(device, device_anomalies)
                alerts.extend(device_alerts)
                
                # Generate recommendations
                device_recommendations = self._generate_device_recommendations(device, device_anomalies)
                recommendations.extend(device_recommendations)
            
            return AgentResult(
                success=True,
                data={
                    "anomalies": anomalies,
                    "total_devices_analyzed": len(devices),
                    "anomaly_count": len(anomalies)
                },
                insights=insights,
                alerts=alerts,
                recommendations=recommendations,
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Device anomaly detection failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Device anomaly detection failed: {str(e)}"
            )
    
    async def _get_user_devices(self, user_id: str, device_id: Optional[str], db: AsyncSession) -> List[Device]:
        """Get user's devices for analysis"""
        query = select(Device).where(Device.user_id == user_id)
        
        if device_id:
            query = query.where(Device.id == device_id)
        
        query = query.where(Device.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _analyze_device_anomalies(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Analyze device for behavioral anomalies"""
        anomalies = []
        event_producer = await get_event_producer()
        
        # Check connection stability
        connection_anomalies = await self._check_connection_stability(device, db)
        anomalies.extend(connection_anomalies)
        for anomaly in connection_anomalies:
            await event_producer.publish_device_anomaly(anomaly)
        
        # Check battery behavior
        battery_anomalies = await self._check_battery_behavior(device, db)
        anomalies.extend(battery_anomalies)
        for anomaly in battery_anomalies:
            await event_producer.publish_device_anomaly(anomaly)
        
        # Check data volume patterns
        volume_anomalies = await self._check_data_volume_patterns(device, db)
        anomalies.extend(volume_anomalies)
        for anomaly in volume_anomalies:
            await event_producer.publish_device_anomaly(anomaly)
        
        # Check sync behavior
        sync_anomalies = await self._check_sync_behavior(device, db)
        anomalies.extend(sync_anomalies)
        for anomaly in sync_anomalies:
            await event_producer.publish_device_anomaly(anomaly)
        
        # Check device status changes
        status_anomalies = await self._check_status_changes(device, db)
        anomalies.extend(status_anomalies)
        for anomaly in status_anomalies:
            await event_producer.publish_device_anomaly(anomaly)
        
        return anomalies
    
    async def _check_connection_stability(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for connection stability issues"""
        anomalies = []
        
        # Analyze connection patterns over the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # This would require connection logs - for now, we'll simulate
        # In a real implementation, you'd have a connection_logs table
        
        # Check if device is currently disconnected
        if device.status == DeviceStatus.DISCONNECTED:
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "connection_lost",
                "severity": "high",
                "description": f"Device {device.name} is currently disconnected",
                "timestamp": datetime.utcnow(),
                "recommendation": "Check device power and connection settings"
            })
        
        # Check for frequent status changes
        if device.status in [DeviceStatus.CONNECTING, DeviceStatus.ERROR]:
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "connection_instability",
                "severity": "medium",
                "description": f"Device {device.name} has unstable connection status: {device.status}",
                "timestamp": datetime.utcnow(),
                "recommendation": "Check network connectivity and device proximity"
            })
        
        return anomalies
    
    async def _check_battery_behavior(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for unusual battery behavior"""
        anomalies = []
        
        if device.battery_level is None:
            return anomalies
        
        # Check for critically low battery
        if device.battery_level < 10:
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "low_battery",
                "severity": "medium",
                "description": f"Device {device.name} has low battery: {device.battery_level}%",
                "timestamp": datetime.utcnow(),
                "recommendation": "Charge device to ensure continuous monitoring"
            })
        
        # Check for rapid battery drain (would need historical data)
        # This is a simplified check - in reality you'd track battery over time
        
        return anomalies
    
    async def _check_data_volume_patterns(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for unusual data volume patterns"""
        anomalies = []
        
        # Compare data volume over different time periods
        now = datetime.utcnow()
        
        # Last 24 hours
        one_day_ago = now - timedelta(days=1)
        recent_data_query = select(func.count(DeviceDataPoint.id)).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.timestamp >= one_day_ago
            )
        )
        recent_result = await db.execute(recent_data_query)
        recent_count = recent_result.scalar()
        
        # Previous 24 hours
        two_days_ago = now - timedelta(days=2)
        previous_data_query = select(func.count(DeviceDataPoint.id)).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.timestamp >= two_days_ago,
                DeviceDataPoint.timestamp < one_day_ago
            )
        )
        previous_result = await db.execute(previous_data_query)
        previous_count = previous_result.scalar()
        
        if previous_count > 0:
            volume_change = abs(recent_count - previous_count) / previous_count
            
            if volume_change > self.anomaly_thresholds["data_volume_threshold"]:
                change_type = "increase" if recent_count > previous_count else "decrease"
                anomalies.append({
                    "device_id": str(device.id),
                    "device_name": device.name,
                    "anomaly_type": "data_volume_change",
                    "severity": "medium",
                    "description": f"Device {device.name} data volume {change_type}d by {volume_change*100:.1f}%",
                    "recent_count": recent_count,
                    "previous_count": previous_count,
                    "volume_change": volume_change,
                    "timestamp": datetime.utcnow(),
                    "recommendation": "Check device usage patterns and sensor functionality"
                })
        
        return anomalies
    
    async def _check_sync_behavior(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for unusual sync behavior"""
        anomalies = []
        
        if not device.last_sync_at:
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "no_sync_history",
                "severity": "high",
                "description": f"Device {device.name} has never synced data",
                "timestamp": datetime.utcnow(),
                "recommendation": "Check device setup and authentication"
            })
            return anomalies
        
        # Check sync frequency
        hours_since_sync = (datetime.utcnow() - device.last_sync_at).total_seconds() / 3600
        
        # Expected sync frequency depends on device type
        expected_sync_hours = self._get_expected_sync_frequency(device.device_type)
        
        if hours_since_sync > expected_sync_hours * 2:  # More than 2x expected
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "infrequent_sync",
                "severity": "medium",
                "description": f"Device {device.name} hasn't synced in {hours_since_sync:.1f} hours",
                "expected_frequency_hours": expected_sync_hours,
                "actual_hours": hours_since_sync,
                "timestamp": datetime.utcnow(),
                "recommendation": "Check device connectivity and sync settings"
            })
        
        return anomalies
    
    async def _check_status_changes(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for unusual status changes"""
        anomalies = []
        
        # Check for error status
        if device.status == DeviceStatus.ERROR:
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "device_error",
                "severity": "high",
                "description": f"Device {device.name} is in error state",
                "timestamp": datetime.utcnow(),
                "recommendation": "Check device logs and restart if necessary"
            })
        
        # Check for maintenance status
        if device.status == DeviceStatus.MAINTENANCE:
            anomalies.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "anomaly_type": "maintenance_mode",
                "severity": "low",
                "description": f"Device {device.name} is in maintenance mode",
                "timestamp": datetime.utcnow(),
                "recommendation": "Device is being maintained, check back later"
            })
        
        return anomalies
    
    def _get_expected_sync_frequency(self, device_type: str) -> float:
        """Get expected sync frequency in hours for device type"""
        sync_frequencies = {
            "smartwatch": 1.0,  # Every hour
            "fitness_tracker": 2.0,  # Every 2 hours
            "smart_ring": 4.0,  # Every 4 hours
            "blood_pressure_monitor": 24.0,  # Daily
            "glucose_monitor": 1.0,  # Every hour
            "scale": 24.0,  # Daily
            "thermometer": 24.0,  # Daily
            "mobile_app": 6.0,  # Every 6 hours
        }
        
        return sync_frequencies.get(device_type, 12.0)  # Default: every 12 hours
    
    def _generate_device_insights(self, device: Device, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about device anomalies"""
        insights = []
        
        if not anomalies:
            insights.append(f"Device {device.name} is operating normally")
            return insights
        
        anomaly_types = [anomaly["anomaly_type"] for anomaly in anomalies]
        
        if "connection_lost" in anomaly_types:
            insights.append(f"Device {device.name} has connectivity issues")
        
        if "data_volume_change" in anomaly_types:
            insights.append(f"Device {device.name} data patterns have changed")
        
        if "infrequent_sync" in anomaly_types:
            insights.append(f"Device {device.name} syncs less frequently than expected")
        
        if "device_error" in anomaly_types:
            insights.append(f"Device {device.name} is experiencing technical issues")
        
        return insights
    
    def _generate_device_alerts(self, device: Device, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate alerts for critical device anomalies"""
        alerts = []
        
        for anomaly in anomalies:
            if anomaly["severity"] == "high":
                alerts.append(f"CRITICAL: {anomaly['description']}")
        
        return alerts
    
    def _generate_device_recommendations(self, device: Device, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for device anomalies"""
        recommendations = []
        
        for anomaly in anomalies:
            if "recommendation" in anomaly:
                recommendations.append(f"{device.name}: {anomaly['recommendation']}")
        
        return recommendations 