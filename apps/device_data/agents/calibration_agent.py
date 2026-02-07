"""
Calibration Agent
Autonomously calibrates device readings and maintains accuracy.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseDeviceAgent, AgentResult
from ..models.data_point import DeviceDataPoint, DataQuality, DataType
from ..models.device import Device, DeviceStatus
from common.utils.logging import get_logger
from apps.device_data.services.event_producer import get_event_producer

logger = get_logger(__name__)

class CalibrationAgent(BaseDeviceAgent):
    """
    Autonomous agent for monitoring device accuracy and suggesting calibration.
    Analyzes data consistency and drift to determine when calibration is needed.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="calibration_monitor",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Calibration thresholds
        self.calibration_thresholds = {
            "drift_threshold": 0.05,  # 5% drift
            "consistency_threshold": 0.1,  # 10% inconsistency
            "accuracy_threshold": 0.95,  # 95% accuracy
            "calibration_interval_days": 30,  # Days between calibrations
        }
        
        # Reference ranges for different metrics
        self.reference_ranges = {
            DataType.HEART_RATE: {"min": 60, "max": 100, "unit": "bpm"},
            DataType.BLOOD_PRESSURE_SYSTOLIC: {"min": 90, "max": 140, "unit": "mmHg"},
            DataType.BLOOD_PRESSURE_DIASTOLIC: {"min": 60, "max": 90, "unit": "mmHg"},
            DataType.BODY_TEMPERATURE: {"min": 97.0, "max": 99.5, "unit": "°F"},
            DataType.OXYGEN_SATURATION: {"min": 95, "max": 100, "unit": "%"},
            DataType.BLOOD_GLUCOSE: {"min": 70, "max": 140, "unit": "mg/dL"},
            DataType.WEIGHT: {"min": 50, "max": 300, "unit": "kg"},
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process device data to assess calibration needs.
        
        Args:
            data: Dictionary containing user_id and optional device_id filter
            db: Database session
            
        Returns:
            AgentResult with calibration assessment and recommendations
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
                    data={"calibration_issues": [], "message": "No devices found"}
                )
            
            calibration_issues = []
            insights = []
            alerts = []
            recommendations = []
            
            # Analyze each device
            for device in devices:
                device_issues = await self._analyze_device_calibration(device, db)
                calibration_issues.extend(device_issues)
                
                # Generate device-specific insights
                device_insights = self._generate_device_insights(device, device_issues)
                insights.extend(device_insights)
                
                # Generate alerts for critical calibration issues
                device_alerts = self._generate_device_alerts(device, device_issues)
                alerts.extend(device_alerts)
                
                # Generate recommendations
                device_recommendations = self._generate_device_recommendations(device, device_issues)
                recommendations.extend(device_recommendations)
            
            return AgentResult(
                success=True,
                data={
                    "calibration_issues": calibration_issues,
                    "total_devices_analyzed": len(devices),
                    "calibration_needed_count": len([i for i in calibration_issues if i["needs_calibration"]])
                },
                insights=insights,
                alerts=alerts,
                recommendations=recommendations,
                confidence=0.80
            )
            
        except Exception as e:
            logger.error(f"Calibration analysis failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Calibration analysis failed: {str(e)}"
            )
    
    async def _get_user_devices(self, user_id: str, device_id: Optional[str], db: AsyncSession) -> List[Device]:
        """Get user's devices for analysis"""
        query = select(Device).where(Device.user_id == user_id)
        
        if device_id:
            query = query.where(Device.id == device_id)
        
        query = query.where(Device.is_active == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _analyze_device_calibration(self, device: Device, db: AsyncSession) -> List[Dict[str, Any]]:
        """Analyze device for calibration needs"""
        calibration_issues = []
        event_producer = await get_event_producer()
        supported_metrics = device.supported_metrics
        for metric in supported_metrics:
            try:
                metric_type = DataType(metric)
            except ValueError:
                continue
            drift_issues = await self._check_measurement_drift(device, metric_type, db)
            calibration_issues.extend(drift_issues)
            for issue in drift_issues:
                await event_producer.publish_calibration_event(issue)
            consistency_issues = await self._check_measurement_consistency(device, metric_type, db)
            calibration_issues.extend(consistency_issues)
            for issue in consistency_issues:
                await event_producer.publish_calibration_event(issue)
            accuracy_issues = await self._check_measurement_accuracy(device, metric_type, db)
            calibration_issues.extend(accuracy_issues)
            for issue in accuracy_issues:
                await event_producer.publish_calibration_event(issue)
        return calibration_issues
    
    async def _check_measurement_drift(self, device: Device, metric_type: DataType, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for measurement drift over time"""
        issues = []
        
        # Get data from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        query = select(DeviceDataPoint).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.data_type == metric_type,
                DeviceDataPoint.timestamp >= thirty_days_ago,
                DeviceDataPoint.quality != DataQuality.POOR
            )
        ).order_by(DeviceDataPoint.timestamp)
        
        result = await db.execute(query)
        data_points = result.scalars().all()
        
        if len(data_points) < 10:  # Need at least 10 data points
            return issues
        
        # Calculate trend over time
        timestamps = [dp.timestamp for dp in data_points]
        values = [float(dp.value) for dp in data_points]
        
        # Convert timestamps to days since first measurement
        first_timestamp = timestamps[0]
        days_since_first = [(t - first_timestamp).days for t in timestamps]
        
        # Calculate linear regression
        if len(set(days_since_first)) > 1:  # Need at least 2 different time points
            slope, intercept = np.polyfit(days_since_first, values, 1)
            
            # Calculate drift percentage
            mean_value = np.mean(values)
            if mean_value != 0:
                drift_percentage = abs(slope * 30) / abs(mean_value)  # Drift over 30 days
                
                if drift_percentage > self.calibration_thresholds["drift_threshold"]:
                    issues.append({
                        "device_id": str(device.id),
                        "device_name": device.name,
                        "metric": metric_type,
                        "issue_type": "measurement_drift",
                        "drift_percentage": drift_percentage * 100,
                        "drift_direction": "increasing" if slope > 0 else "decreasing",
                        "severity": "medium" if drift_percentage < 0.1 else "high",
                        "needs_calibration": True,
                        "description": f"Device {device.name} shows {drift_percentage*100:.1f}% drift in {metric_type} measurements",
                        "recommendation": f"Calibrate {device.name} for {metric_type} measurements"
                    })
        
        return issues
    
    async def _check_measurement_consistency(self, device: Device, metric_type: DataType, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for measurement consistency issues"""
        issues = []
        
        # Get recent data (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        query = select(DeviceDataPoint).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.data_type == metric_type,
                DeviceDataPoint.timestamp >= seven_days_ago,
                DeviceDataPoint.quality != DataQuality.POOR
            )
        ).order_by(DeviceDataPoint.timestamp)
        
        result = await db.execute(query)
        data_points = result.scalars().all()
        
        if len(data_points) < 5:  # Need at least 5 data points
            return issues
        
        values = [float(dp.value) for dp in data_points]
        
        # Calculate coefficient of variation (CV)
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        if mean_value != 0:
            cv = std_value / abs(mean_value)
            
            if cv > self.calibration_thresholds["consistency_threshold"]:
                issues.append({
                    "device_id": str(device.id),
                    "device_name": device.name,
                    "metric": metric_type,
                    "issue_type": "inconsistent_measurements",
                    "coefficient_of_variation": cv,
                    "mean_value": mean_value,
                    "std_value": std_value,
                    "severity": "medium",
                    "needs_calibration": True,
                    "description": f"Device {device.name} shows inconsistent {metric_type} measurements (CV: {cv*100:.1f}%)",
                    "recommendation": f"Check {device.name} sensor stability and consider recalibration"
                })
        
        return issues
    
    async def _check_measurement_accuracy(self, device: Device, metric_type: DataType, db: AsyncSession) -> List[Dict[str, Any]]:
        """Check for measurement accuracy issues"""
        issues = []
        
        # Get reference range for this metric
        reference_range = self.reference_ranges.get(metric_type)
        if not reference_range:
            return issues
        
        # Get recent data
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        query = select(DeviceDataPoint).where(
            and_(
                DeviceDataPoint.device_id == device.id,
                DeviceDataPoint.data_type == metric_type,
                DeviceDataPoint.timestamp >= seven_days_ago,
                DeviceDataPoint.quality != DataQuality.POOR
            )
        )
        
        result = await db.execute(query)
        data_points = result.scalars().all()
        
        if len(data_points) < 3:  # Need at least 3 data points
            return issues
        
        values = [float(dp.value) for dp in data_points]
        
        # Check for values outside expected range
        min_val = reference_range["min"]
        max_val = reference_range["max"]
        
        out_of_range_count = sum(1 for v in values if v < min_val or v > max_val)
        accuracy_rate = (len(values) - out_of_range_count) / len(values)
        
        if accuracy_rate < self.calibration_thresholds["accuracy_threshold"]:
            issues.append({
                "device_id": str(device.id),
                "device_name": device.name,
                "metric": metric_type,
                "issue_type": "accuracy_issues",
                "accuracy_rate": accuracy_rate * 100,
                "out_of_range_count": out_of_range_count,
                "total_measurements": len(values),
                "expected_range": f"{min_val}-{max_val} {reference_range['unit']}",
                "severity": "high" if accuracy_rate < 0.8 else "medium",
                "needs_calibration": True,
                "description": f"Device {device.name} accuracy for {metric_type}: {accuracy_rate*100:.1f}%",
                "recommendation": f"Calibrate {device.name} against known reference values"
            })
        
        return issues
    
    def _generate_device_insights(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about device calibration"""
        insights = []
        
        if not issues:
            insights.append(f"Device {device.name} measurements appear accurate")
            return insights
        
        issue_types = [issue["issue_type"] for issue in issues]
        
        if "measurement_drift" in issue_types:
            insights.append(f"Device {device.name} shows measurement drift over time")
        
        if "inconsistent_measurements" in issue_types:
            insights.append(f"Device {device.name} produces inconsistent readings")
        
        if "accuracy_issues" in issue_types:
            insights.append(f"Device {device.name} accuracy may need attention")
        
        calibration_needed = any(issue.get("needs_calibration", False) for issue in issues)
        if calibration_needed:
            insights.append(f"Device {device.name} may benefit from calibration")
        
        return insights
    
    def _generate_device_alerts(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate alerts for critical calibration issues"""
        alerts = []
        
        for issue in issues:
            if issue["severity"] == "high":
                alerts.append(f"CALIBRATION NEEDED: {issue['description']}")
        
        return alerts
    
    def _generate_device_recommendations(self, device: Device, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for device calibration"""
        recommendations = []
        
        for issue in issues:
            if "recommendation" in issue:
                recommendations.append(f"{device.name}: {issue['recommendation']}")
        
        # Add general calibration recommendations
        calibration_needed = any(issue.get("needs_calibration", False) for issue in issues)
        if calibration_needed:
            recommendations.append(f"{device.name}: Schedule professional calibration if available")
            recommendations.append(f"{device.name}: Compare readings with known reference devices")
        
        return recommendations 