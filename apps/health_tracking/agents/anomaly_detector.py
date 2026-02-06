"""
Anomaly Detection Agent
Autonomously detects anomalies in health metrics and vital signs.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from ..models.vital_signs import VitalSigns
from common.utils.logging import get_logger

logger = get_logger(__name__)

class AnomalyDetectorAgent(BaseHealthAgent):
    """
    Autonomous agent for detecting anomalies in health data.
    Uses statistical methods and machine learning to identify unusual patterns.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="anomaly_detector",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Anomaly detection thresholds
        self.thresholds = {
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {"min": 90, "max": 140, "std_threshold": 2.5},
            MetricType.BLOOD_PRESSURE_DIASTOLIC: {"min": 60, "max": 90, "std_threshold": 2.5},
            MetricType.HEART_RATE: {"min": 60, "max": 100, "std_threshold": 2.0},
            MetricType.TEMPERATURE: {"min": 97.0, "max": 99.5, "std_threshold": 2.0},
            MetricType.OXYGEN_SATURATION: {"min": 95, "max": 100, "std_threshold": 1.5},
            MetricType.GLUCOSE: {"min": 70, "max": 140, "std_threshold": 2.0},
            MetricType.WEIGHT: {"std_threshold": 3.0},  # Percentage change
            MetricType.BMI: {"min": 18.5, "max": 24.9, "std_threshold": 2.0}
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process health data to detect anomalies.
        
        Args:
            data: Dictionary containing user_id and optional metric_type filter
            db: Database session
            
        Returns:
            AgentResult with detected anomalies
        """
        user_id = data.get("user_id")
        metric_type = data.get("metric_type")
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Get recent health metrics for the user
            metrics = await self._get_recent_metrics(user_id, metric_type, db)
            
            if not metrics:
                return AgentResult(
                    success=True,
                    data={"anomalies": [], "message": "No recent metrics found"}
                )
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(metrics, user_id)
            
            # Generate insights and alerts
            insights = self._generate_insights(anomalies)
            alerts = self._generate_alerts(anomalies)
            recommendations = self._generate_recommendations(anomalies)
            
            return AgentResult(
                success=True,
                data={
                    "anomalies": anomalies,
                    "total_metrics_analyzed": len(metrics),
                    "anomaly_count": len(anomalies)
                },
                insights=insights,
                alerts=alerts,
                recommendations=recommendations,
                confidence=0.85  # High confidence for statistical methods
            )
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Anomaly detection failed: {str(e)}"
            )
    
    async def _get_recent_metrics(self, user_id: str, metric_type: Optional[MetricType], db: AsyncSession) -> List[Dict[str, Any]]:
        """Get recent health metrics for analysis"""
        # Get metrics from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.created_at >= thirty_days_ago
            )
        )
        
        if metric_type:
            query = query.where(HealthMetric.metric_type == metric_type)
        
        query = query.order_by(HealthMetric.created_at.desc())
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        return [
            {
                "id": metric.id,
                "metric_type": metric.metric_type,
                "value": metric.value,
                "unit": metric.unit,
                "created_at": metric.created_at,
                "metadata": metric.metric_metadata
            }
            for metric in metrics
        ]
    
    async def _detect_anomalies(self, metrics: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        anomalies = []
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            metric_type = metric["metric_type"]
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric)
        
        # Analyze each metric type
        for metric_type, type_metrics in metrics_by_type.items():
            if len(type_metrics) < 3:  # Need at least 3 data points
                continue
            
            # Extract values
            values = [m["value"] for m in type_metrics]
            
            # Get thresholds for this metric type
            threshold_config = self.thresholds.get(metric_type, {})
            
            # Detect range anomalies
            range_anomalies = self._detect_range_anomalies(values, type_metrics, threshold_config)
            anomalies.extend(range_anomalies)
            
            # Detect statistical anomalies (outliers)
            if len(values) >= 5:  # Need more data for statistical analysis
                stat_anomalies = self._detect_statistical_anomalies(values, type_metrics, threshold_config)
                anomalies.extend(stat_anomalies)
            
            # Detect trend anomalies
            trend_anomalies = self._detect_trend_anomalies(values, type_metrics, metric_type)
            anomalies.extend(trend_anomalies)
        
        return anomalies
    
    def _detect_range_anomalies(self, values: List[float], metrics: List[Dict[str, Any]], threshold_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies based on absolute range thresholds"""
        anomalies = []
        
        min_threshold = threshold_config.get("min")
        max_threshold = threshold_config.get("max")
        
        if min_threshold is None or max_threshold is None:
            return anomalies
        
        for metric in metrics:
            value = metric["value"]
            
            if value < min_threshold or value > max_threshold:
                anomalies.append({
                    "metric_id": metric["id"],
                    "metric_type": metric["metric_type"],
                    "value": value,
                    "unit": metric["unit"],
                    "timestamp": metric["created_at"],
                    "anomaly_type": "range_violation",
                    "severity": "high" if abs(value - (min_threshold + max_threshold) / 2) > (max_threshold - min_threshold) * 0.3 else "medium",
                    "description": f"{metric['metric_type'].value} value {value} {metric['unit']} is outside normal range ({min_threshold}-{max_threshold})",
                    "threshold_min": min_threshold,
                    "threshold_max": max_threshold
                })
        
        return anomalies
    
    def _detect_statistical_anomalies(self, values: List[float], metrics: List[Dict[str, Any]], threshold_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods (Z-score)"""
        anomalies = []
        
        if len(values) < 5:
            return anomalies
        
        # Calculate statistics
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return anomalies
        
        std_threshold = threshold_config.get("std_threshold", 2.0)
        
        for i, metric in enumerate(metrics):
            value = metric["value"]
            z_score = abs((value - mean_val) / std_val)
            
            if z_score > std_threshold:
                anomalies.append({
                    "metric_id": metric["id"],
                    "metric_type": metric["metric_type"],
                    "value": value,
                    "unit": metric["unit"],
                    "timestamp": metric["created_at"],
                    "anomaly_type": "statistical_outlier",
                    "severity": "high" if z_score > std_threshold * 1.5 else "medium",
                    "description": f"{metric['metric_type'].value} value {value} {metric['unit']} is {z_score:.1f} standard deviations from mean ({mean_val:.1f})",
                    "z_score": z_score,
                    "mean": mean_val,
                    "std": std_val
                })
        
        return anomalies
    
    def _detect_trend_anomalies(self, values: List[float], metrics: List[Dict[str, Any]], metric_type: MetricType) -> List[Dict[str, Any]]:
        """Detect anomalies based on trends"""
        anomalies = []
        
        if len(values) < 3:
            return anomalies
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda x: x["created_at"])
        sorted_values = [m["value"] for m in sorted_metrics]
        
        # Detect rapid changes
        for i in range(1, len(sorted_values)):
            change = abs(sorted_values[i] - sorted_values[i-1])
            change_percent = (change / sorted_values[i-1]) * 100 if sorted_values[i-1] != 0 else 0
            
            # Define rapid change thresholds based on metric type
            rapid_change_threshold = self._get_rapid_change_threshold(metric_type)
            
            if change_percent > rapid_change_threshold:
                anomalies.append({
                    "metric_id": sorted_metrics[i]["id"],
                    "metric_type": metric_type,
                    "value": sorted_values[i],
                    "unit": sorted_metrics[i]["unit"],
                    "timestamp": sorted_metrics[i]["created_at"],
                    "anomaly_type": "rapid_change",
                    "severity": "high" if change_percent > rapid_change_threshold * 1.5 else "medium",
                    "description": f"Rapid {change_percent:.1f}% change in {metric_type.value} from {sorted_values[i-1]:.1f} to {sorted_values[i]:.1f}",
                    "change_percent": change_percent,
                    "previous_value": sorted_values[i-1]
                })
        
        return anomalies
    
    def _get_rapid_change_threshold(self, metric_type: MetricType) -> float:
        """Get rapid change threshold for different metric types"""
        thresholds = {
            MetricType.BLOOD_PRESSURE_SYSTOLIC: 20.0,  # 20% change
            MetricType.BLOOD_PRESSURE_DIASTOLIC: 25.0,  # 25% change
            MetricType.HEART_RATE: 30.0,  # 30% change
            MetricType.TEMPERATURE: 5.0,  # 5% change
            MetricType.OXYGEN_SATURATION: 3.0,  # 3% change
            MetricType.GLUCOSE: 25.0,  # 25% change
            MetricType.WEIGHT: 5.0,  # 5% change
            MetricType.BMI: 8.0,  # 8% change
        }
        
        return thresholds.get(metric_type, 15.0)  # Default 15%
    
    def _generate_insights(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from detected anomalies"""
        insights = []
        
        if not anomalies:
            insights.append("No anomalies detected in recent health data.")
            return insights
        
        # Group by type
        anomaly_types = {}
        for anomaly in anomalies:
            anomaly_type = anomaly["anomaly_type"]
            if anomaly_type not in anomaly_types:
                anomaly_types[anomaly_type] = []
            anomaly_types[anomaly_type].append(anomaly)
        
        # Generate insights
        for anomaly_type, type_anomalies in anomaly_types.items():
            count = len(type_anomalies)
            if count == 1:
                insights.append(f"Detected 1 {anomaly_type.replace('_', ' ')} anomaly.")
            else:
                insights.append(f"Detected {count} {anomaly_type.replace('_', ' ')} anomalies.")
        
        # High severity insights
        high_severity = [a for a in anomalies if a["severity"] == "high"]
        if high_severity:
            insights.append(f"Found {len(high_severity)} high-severity anomalies requiring attention.")
        
        return insights
    
    def _generate_alerts(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate alerts for concerning anomalies"""
        alerts = []
        
        for anomaly in anomalies:
            if anomaly["severity"] == "high":
                alerts.append(f"🚨 {anomaly['description']}")
            elif anomaly["severity"] == "medium":
                alerts.append(f"⚠️ {anomaly['description']}")
        
        return alerts
    
    def _generate_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on anomalies"""
        recommendations = []
        
        if not anomalies:
            recommendations.append("Continue monitoring your health metrics regularly.")
            return recommendations
        
        # Group by metric type
        metric_types = {}
        for anomaly in anomalies:
            metric_type = anomaly["metric_type"]
            if metric_type not in metric_types:
                metric_types[metric_type] = []
            metric_types[metric_type].append(anomaly)
        
        # Generate recommendations
        for metric_type, type_anomalies in metric_types.items():
            if metric_type == MetricType.BLOOD_PRESSURE_SYSTOLIC or metric_type == MetricType.BLOOD_PRESSURE_DIASTOLIC:
                recommendations.append("Consider monitoring blood pressure more frequently and consult with your healthcare provider.")
            elif metric_type == MetricType.HEART_RATE:
                recommendations.append("Monitor your heart rate patterns and consider stress management techniques.")
            elif metric_type == MetricType.GLUCOSE:
                recommendations.append("Review your diet and medication schedule, and consult with your healthcare provider.")
            elif metric_type == MetricType.WEIGHT:
                recommendations.append("Track your weight changes and consider lifestyle modifications if needed.")
        
        # General recommendations
        if len(anomalies) > 3:
            recommendations.append("Multiple anomalies detected. Consider scheduling a comprehensive health review.")
        
        return recommendations 