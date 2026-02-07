"""
Sync Monitor Agent
Autonomously monitors device synchronization patterns and optimizes sync schedules.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseDeviceAgent, AgentResult
from ..models.device import Device, DeviceStatus
from ..models.data_point import DeviceDataPoint
from common.utils.logging import get_logger
from apps.device_data.services.event_producer import get_event_producer

logger = get_logger(__name__)

class SyncMonitorAgent(BaseDeviceAgent):
    """
    Autonomous agent for monitoring device synchronization patterns.
    Optimizes sync schedules and detects sync-related issues.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="sync_monitor",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Sync monitoring thresholds
        self.sync_thresholds = {
            "sync_failure_threshold": 3,  # Number of consecutive failures
            "sync_latency_threshold": 300,  # 5 minutes in seconds
            "data_loss_threshold": 0.1,  # 10% data loss
            "sync_frequency_min": 1,  # Minimum sync frequency in hours
            "sync_frequency_max": 24,  # Maximum sync frequency in hours
        }
        
        # Optimal sync frequencies by device type
        self.optimal_sync_frequencies = {
            "smartwatch": 1,  # Every hour
            "fitness_tracker": 2,  # Every 2 hours
            "smart_ring": 4,  # Every 4 hours
            "blood_pressure_monitor": 24,  # Daily
            "glucose_monitor": 1,  # Every hour
            "scale": 24,  # Daily
            "thermometer": 24,  # Daily
            "mobile_app": 6,  # Every 6 hours
            "continuous_glucose_monitor": 0.5,  # Every 30 minutes
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process device sync patterns and optimize synchronization.
        
        Args:
            data: Dictionary containing user_id and optional device_id filter
            db: Database session
            
        Returns:
            AgentResult with sync analysis and optimization recommendations
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
                    data={"sync_issues": [], "message": "No devices found"}
                )
            
            sync_issues = []
            insights = []
            alerts = []
            recommendations = []
            
            # Analyze each device
            for device in devices:
                device_issues = await self._analyze_device_sync(device, db)
                sync_issues.extend(device_issues)
                
                # Generate device-specific insights
                device_insights = self._generate_device_insights(device, device_issues)
                insights.extend(device_insights)
                
                # Generate alerts for critical sync issues
                device_alerts = self._generate_device_alerts(device, device_issues)
                alerts.extend(device_alerts)
                
                # Generate recommendations
                device_recommendations = self._generate_device_recommendations(device, device_issues)
                recommendations.extend(device_recommendations)
            
            return AgentResult(
                success=True,
                data={
                    "sync_issues": sync_issues,
                    "total_devices_analyzed": len(devices),
                    "sync_optimization_count": len([i for i in sync_issues if i["needs_optimization"]])
                },
                insights=insights,
                alerts=alerts,
                recommendations=recommendations,
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Sync monitoring failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Sync monitoring failed: {str(e)}"
            )
    
    async def _get_user_devices(self, user_id: str, device_id: Optional[str], db: AsyncSession) -> List[Device]:
        """Get user's devices for analysis"""
        query = select(Device).where(Device.user_id == user_id)
        
        if device_id:
            query = query.where(Device.id == device_id)
        
        query = query.where(Device.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _analyze_device_sync(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Analyze device synchronization patterns"""
        sync_issues = []
        event_producer = await get_event_producer()
        
        # Check sync frequency
        frequency_issues = await self._check_sync_frequency(device, db)
        sync_issues.extend(frequency_issues)
        for issue in frequency_issues:
            await event_producer.publish_sync_event(issue)
        
        # Check sync reliability
        reliability_issues = await self._check_sync_reliability(device, db)
        sync_issues.extend(reliability_issues)
        for issue in reliability_issues:
            await event_producer.publish_sync_event(issue)
        
        # Check data completeness
        completeness_issues = await self._check_data_completeness(device, db)
        sync_issues.extend(completeness_issues)
        for issue in completeness_issues:
            await event_producer.publish_sync_event(issue)
        
        # Check sync latency
        latency_issues = await self._check_sync_latency(device, db)
        sync_issues.extend(latency_issues)
        for issue in latency_issues:
            await event_producer.publish_sync_event(issue)
        
        return sync_issues
    
    async def _check_sync_frequency(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check if device sync frequency is optimal"""
        issues = []
        
        if not device.last_sync_at:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "never_synced",
                "severity": "high",
                "needs_optimization": True,
                "description": f"Device {device.name} has never synced data",
                "recommendation": "Check device connection and authentication settings"
            })
            return issues
        
        # Calculate current sync frequency
        hours_since_sync = (datetime.utcnow() - device.last_sync_at).total_seconds() / 3600
        
        # Get optimal frequency for this device type
        optimal_frequency = self.optimal_sync_frequencies.get(device.device_type, 12)
        
        # Check if sync is too infrequent
        if hours_since_sync > optimal_frequency * 2:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "infrequent_sync",
                "current_frequency_hours": hours_since_sync,
                "optimal_frequency_hours": optimal_frequency,
                "severity": "medium",
                "needs_optimization": True,
                "description": f"Device {device.name} syncs every {hours_since_sync:.1f} hours (optimal: {optimal_frequency}h)",
                "recommendation": f"Increase sync frequency to every {optimal_frequency} hours"
            })
        
        # Check if sync is too frequent (wasteful)
        elif hours_since_sync < optimal_frequency * 0.5:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "over_syncing",
                "current_frequency_hours": hours_since_sync,
                "optimal_frequency_hours": optimal_frequency,
                "severity": "low",
                "needs_optimization": True,
                "description": f"Device {device.name} syncs too frequently: {hours_since_sync:.1f}h (optimal: {optimal_frequency}h)",
                "recommendation": f"Reduce sync frequency to every {optimal_frequency} hours to save battery"
            })
        
        return issues
    
    async def _check_sync_reliability(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check sync reliability and failure patterns"""
        issues = []
        
        # This would require sync logs - for now, we'll check device status
        if device.status in [DeviceStatus.ERROR, DeviceStatus.DISCONNECTED]:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "sync_failure",
                "device_status": device.status,
                "severity": "high",
                "needs_optimization": True,
                "description": f"Device {device.name} sync failed due to status: {device.status}",
                "recommendation": "Check device connection and restart if necessary"
            })
        
        # Check for devices stuck in connecting state
        if device.status == DeviceStatus.CONNECTING:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "connection_timeout",
                "severity": "medium",
                "needs_optimization": True,
                "description": f"Device {device.name} is stuck in connecting state",
                "recommendation": "Check device proximity and network connectivity"
            })
        
        return issues
    
    async def _check_data_completeness(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check if all expected data is being synced"""
        issues = []
        
        # Get expected metrics for this device
        expected_metrics = device.supported_metrics
        
        # Check data completeness for each expected metric
        for metric in expected_metrics:
            # Get data from last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            query = select(func.count(DeviceDataPoint.id)).where(
                and_(
                    DeviceDataPoint.device_id == device.id,
                    DeviceDataPoint.data_type == metric,
                    DeviceDataPoint.timestamp >= seven_days_ago
                )
            )
            
            result = await db.execute(query)
            data_count = result.scalar()
            
            # Calculate expected data points based on device type
            expected_count = self._get_expected_data_count(device.device_type, metric, 7)
            
            if expected_count > 0 and data_count < expected_count * (1 - self.sync_thresholds["data_loss_threshold"]):
                completeness_rate = data_count / expected_count
                issues.append({
                    "device_id": str(device.id),
                    "device_name": device.name,
                    "issue_type": "incomplete_data",
                    "metric": metric,
                    "actual_count": data_count,
                    "expected_count": expected_count,
                    "completeness_rate": completeness_rate * 100,
                    "severity": "medium" if completeness_rate > 0.5 else "high",
                    "needs_optimization": True,
                    "description": f"Device {device.name} missing {metric} data: {completeness_rate*100:.1f}% complete",
                    "recommendation": "Check device sensor functionality and sync settings"
                })
        
        return issues
    
    async def _check_sync_latency(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check sync latency and performance"""
        issues = []
        
        # This would require sync timing logs
        # For now, we'll check if device is currently syncing
        if device.status == DeviceStatus.SYNCING:
            # Simulate latency check
            # In real implementation, you'd track actual sync times
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "sync_in_progress",
                "severity": "low",
                "needs_optimization": False,
                "description": f"Device {device.name} is currently syncing",
                "recommendation": "Wait for sync to complete"
            })
        
        return issues
    
    def _get_expected_data_count(self, device_type: str, metric: str, days: int) -> int:
        """Get expected data count for a device type and metric over given days"""
        # Base frequencies by device type
        base_frequencies = {
            "smartwatch": 24,  # Daily readings
            "fitness_tracker": 12,  # Twice daily
            "smart_ring": 6,  # 4 times daily
            "blood_pressure_monitor": 1,  # Daily
            "glucose_monitor": 24,  # Daily
            "scale": 1,  # Daily
            "thermometer": 1,  # Daily
            "mobile_app": 4,  # 6 times daily
            "continuous_glucose_monitor": 48,  # Every 30 minutes
        }
        
        base_frequency = base_frequencies.get(device_type, 1)
        return base_frequency * days
    
    def _generate_device_insights(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about device sync patterns"""
        insights = []
        
        if not issues:
            insights.append(f"Device {device.name} sync patterns are optimal")
            return insights
        
        issue_types = [issue["issue_type"] for issue in issues]
        
        if "never_synced" in issue_types:
            insights.append(f"Device {device.name} needs initial setup and connection")
        
        if "infrequent_sync" in issue_types:
            insights.append(f"Device {device.name} syncs less frequently than recommended")
        
        if "over_syncing" in issue_types:
            insights.append(f"Device {device.name} syncs more frequently than needed")
        
        if "incomplete_data" in issue_types:
            insights.append(f"Device {device.name} is missing some expected data")
        
        if "sync_failure" in issue_types:
            insights.append(f"Device {device.name} has sync reliability issues")
        
        return insights
    
    def _generate_device_alerts(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate alerts for critical sync issues"""
        alerts = []
        
        for issue in issues:
            if issue["severity"] == "high":
                alerts.append(f"SYNC ISSUE: {issue['description']}")
        
        return alerts
    
    def _generate_device_recommendations(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for device sync optimization"""
        recommendations = []
        
        for issue in issues:
            if "recommendation" in issue:
                recommendations.append(f"{device.name}: {issue['recommendation']}")
        
        # Add general sync optimization recommendations
        optimization_needed = any(issue.get("needs_optimization", False) for issue in issues)
        if optimization_needed:
            recommendations.append(f"{device.name}: Consider adjusting sync schedule based on usage patterns")
            recommendations.append(f"{device.name}: Monitor battery usage and adjust sync frequency accordingly")
        
        return recommendations 