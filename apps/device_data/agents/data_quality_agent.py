"""
Data Quality Agent
Autonomously monitors data quality from devices and flags issues.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseDeviceAgent, AgentResult
from ..models.data_point import DeviceDataPoint, DataQuality, DataType
from ..models.device import Device, DeviceStatus
from common.utils.logging import get_logger
from apps.device_data.services.event_producer import get_event_producer

logger = get_logger(__name__)

class DataQualityAgent(BaseDeviceAgent):
    """
    Autonomous agent for monitoring data quality from health devices.
    Detects missing data, inconsistent readings, and quality issues.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="data_quality_monitor",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Quality thresholds
        self.quality_thresholds = {
            "missing_data_threshold": 0.1,  # 10% missing data is concerning
            "inconsistent_readings_threshold": 0.2,  # 20% inconsistent readings
            "outlier_threshold": 3.0,  # 3 standard deviations
            "sync_frequency_threshold": 24,  # Hours between syncs
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process device data to monitor quality and detect issues.
        
        Args:
            data: Dictionary containing user_id and optional device_id filter
            db: Database session
            
        Returns:
            AgentResult with quality assessment and recommendations
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
                    data={"quality_issues": [], "message": "No devices found"}
                )
            
            quality_issues = []
            insights = []
            alerts = []
            recommendations = []
            
            # Analyze each device
            for device in devices:
                device_issues = await self._analyze_device_quality(device, db)
                quality_issues.extend(device_issues)
                
                # Generate device-specific insights
                device_insights = self._generate_device_insights(device, device_issues)
                insights.extend(device_insights)
                
                # Generate alerts for critical issues
                device_alerts = self._generate_device_alerts(device, device_issues)
                alerts.extend(device_alerts)
                
                # Generate recommendations
                device_recommendations = self._generate_device_recommendations(device, device_issues)
                recommendations.extend(device_recommendations)
            
            return AgentResult(
                success=True,
                data={
                    "quality_issues": quality_issues,
                    "total_devices_analyzed": len(devices),
                    "issue_count": len(quality_issues)
                },
                insights=insights,
                alerts=alerts,
                recommendations=recommendations,
                confidence=0.90
            )
            
        except Exception as e:
            logger.error(f"Data quality analysis failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Data quality analysis failed: {str(e)}"
            )
    
    async def _get_user_devices(self, user_id: str, device_id: Optional[str], db: AsyncSession) -> List[Device]:
        """Get user's devices for analysis"""
        query = select(Device).where(Device.user_id == user_id)
        
        if device_id:
            query = query.where(Device.id == device_id)
        
        query = query.where(Device.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _analyze_device_quality(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Analyze data quality for a specific device and publish issues to Kafka"""
        issues = []
        event_producer = await get_event_producer()
        missing_data_issues = await self._check_missing_data(device, db)
        issues.extend(missing_data_issues)
        for issue in missing_data_issues:
            await event_producer.publish_data_quality_issue(issue)
        inconsistent_issues = await self._check_inconsistent_readings(device, db)
        issues.extend(inconsistent_issues)
        for issue in inconsistent_issues:
            await event_producer.publish_data_quality_issue(issue)
        sync_issues = await self._check_sync_frequency(device)
        issues.extend(sync_issues)
        for issue in sync_issues:
            await event_producer.publish_data_quality_issue(issue)
        quality_issues = await self._check_data_quality_distribution(device, db)
        issues.extend(quality_issues)
        for issue in quality_issues:
            await event_producer.publish_data_quality_issue(issue)
        return issues
    
    async def _check_missing_data(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for missing data patterns"""
        issues = []
        
        # Get expected data types for this device
        expected_metrics = device.supported_metrics
        
        for metric in expected_metrics:
            # Check last 7 days of data
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
            
            # Calculate expected data points (assuming daily readings)
            expected_count = 7
            
            if data_count < expected_count * (1 - self.quality_thresholds["missing_data_threshold"]):
                issues.append({
                    "device_id": str(device.id),
                    "device_name": device.name,
                    "issue_type": "missing_data",
                    "metric": metric,
                    "actual_count": data_count,
                    "expected_count": expected_count,
                    "missing_percentage": (expected_count - data_count) / expected_count * 100,
                    "severity": "high" if data_count < expected_count * 0.5 else "medium",
                    "description": f"Missing {metric} data for device {device.name}",
                    "recommendation": "Check device connection and sync settings"
                })
        
        return issues
    
    async def _check_inconsistent_readings(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for inconsistent or outlier readings"""
        issues = []
        
        # Get recent data points
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        query = select(DeviceDataPoint).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.timestamp >= one_day_ago
            )
        ).order_by(DeviceDataPoint.timestamp.desc())
        
        result = await db.execute(query)
        data_points = result.scalars().all()
        
        # Group by data type
        data_by_type = {}
        for dp in data_points:
            if dp.data_type not in data_by_type:
                data_by_type[dp.data_type] = []
            data_by_type[dp.data_type].append(dp)
        
        # Check for outliers in each data type
        for data_type, points in data_by_type.items():
            if len(points) < 3:  # Need at least 3 points for outlier detection
                continue
            
            values = [float(p.value) for p in points]
            mean_val = sum(values) / len(values)
            
            # Calculate standard deviation
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            # Check for outliers
            for point in points:
                value = float(point.value)
                z_score = abs(value - mean_val) / std_dev if std_dev > 0 else 0
                
                if z_score > self.quality_thresholds["outlier_threshold"]:
                    issues.append({
                        "device_id": str(device.id),
                        "device_name": device.name,
                        "issue_type": "outlier_reading",
                        "metric": data_type,
                        "value": value,
                        "expected_range": f"{mean_val - 2*std_dev:.2f} - {mean_val + 2*std_dev:.2f}",
                        "z_score": z_score,
                        "timestamp": point.timestamp,
                        "severity": "medium",
                        "description": f"Outlier reading for {data_type}: {value}",
                        "recommendation": "Verify reading accuracy or check device calibration"
                    })
        
        return issues
    
    async def _check_sync_frequency(self, device: Device) -> List[Dict[str, Any]]:
        """Check device sync frequency"""
        issues = []
        
        if not device.last_sync_at:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "never_synced",
                "severity": "high",
                "description": f"Device {device.name} has never synced data",
                "recommendation": "Check device connection and authentication"
            })
            return issues
        
        # Check if last sync was too long ago
        hours_since_sync = (datetime.utcnow() - device.last_sync_at).total_seconds() / 3600
        
        if hours_since_sync > self.quality_thresholds["sync_frequency_threshold"]:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "infrequent_sync",
                "hours_since_sync": hours_since_sync,
                "threshold": self.quality_thresholds["sync_frequency_threshold"],
                "severity": "medium" if hours_since_sync < 48 else "high",
                "description": f"Device {device.name} hasn't synced in {hours_since_sync:.1f} hours",
                "recommendation": "Check device battery and connection status"
            })
        
        return issues
    
    async def _check_data_quality_distribution(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check distribution of data quality levels"""
        issues = []
        
        # Get quality distribution for last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        query = select(
            DeviceDataPoint.quality,
            func.count(DeviceDataPoint.id)
        ).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.timestamp >= seven_days_ago
            )
        ).group_by(DeviceDataPoint.quality)
        
        result = await db.execute(query)
        quality_distribution = result.all()
        
        total_points = sum(count for _, count in quality_distribution)
        if total_points == 0:
            return issues
        
        # Check for poor quality data
        poor_quality_count = sum(
            count for quality, count in quality_distribution 
            if quality in [DataQuality.POOR, DataQuality.UNKNOWN]
        )
        
        poor_quality_percentage = (poor_quality_count / total_points) * 100
        
        if poor_quality_percentage > 20:  # More than 20% poor quality
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "issue_type": "poor_data_quality",
                "poor_quality_percentage": poor_quality_percentage,
                "total_data_points": total_points,
                "severity": "medium" if poor_quality_percentage < 50 else "high",
                "description": f"{poor_quality_percentage:.1f}% of data from {device.name} is poor quality",
                "recommendation": "Check device sensors and calibration"
            })
        
        return issues
    
    def _generate_device_insights(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about device data quality"""
        insights = []
        
        if not issues:
            insights.append(f"Device {device.name} has good data quality")
            return insights
        
        issue_types = [issue["issue_type"] for issue in issues]
        
        if "missing_data" in issue_types:
            insights.append(f"Device {device.name} has data gaps that may affect analysis")
        
        if "outlier_reading" in issue_types:
            insights.append(f"Device {device.name} is producing some unusual readings")
        
        if "infrequent_sync" in issue_types:
            insights.append(f"Device {device.name} syncs infrequently, data may be stale")
        
        if "poor_data_quality" in issue_types:
            insights.append(f"Device {device.name} data quality needs attention")
        
        return insights
    
    def _generate_device_alerts(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate alerts for critical device issues"""
        alerts = []
        
        for issue in issues:
            if issue["severity"] == "high":
                alerts.append(f"CRITICAL: {issue['description']}")
        
        return alerts
    
    def _generate_device_recommendations(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for device issues"""
        recommendations = []
        
        for issue in issues:
            if "recommendation" in issue:
                recommendations.append(f"{device.name}: {issue['recommendation']}")
        
        return recommendations 