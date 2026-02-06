"""
Real-time Analytics Agent
Streaming analytics and complex event processing for real-time health insights.
"""

import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum
from dataclasses import dataclass
from collections import deque, defaultdict
import json

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from common.utils.logging import get_logger

logger = get_logger(__name__)

class EventType(Enum):
    """Event types for complex event processing"""
    METRIC_UPDATE = "metric_update"
    THRESHOLD_BREACH = "threshold_breach"
    TREND_CHANGE = "trend_change"
    ANOMALY_DETECTED = "anomaly_detected"
    PATTERN_EMERGED = "pattern_emerged"
    CORRELATION_FOUND = "correlation_found"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class HealthEvent:
    """Health event for real-time processing"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    user_id: str
    metric_type: str
    value: float
    severity: AlertSeverity
    description: str
    metadata: Dict[str, Any]

@dataclass
class RealTimeAlert:
    """Real-time alert"""
    alert_id: str
    timestamp: datetime
    user_id: str
    severity: AlertSeverity
    title: str
    description: str
    affected_metrics: List[str]
    recommendations: List[str]
    correlation_events: List[str]
    requires_immediate_action: bool

class RealTimeAnalyticsAgent(BaseHealthAgent):
    """
    Real-time analytics agent for streaming health data analysis.
    Implements complex event processing, real-time alert correlation, and dynamic threshold adjustment.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="realtime_analytics",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Real-time data structures
        self.event_streams = defaultdict(deque)  # user_id -> event stream
        self.alert_history = defaultdict(list)   # user_id -> alert history
        self.correlation_patterns = defaultdict(list)  # user_id -> correlation patterns
        self.dynamic_thresholds = defaultdict(dict)    # user_id -> metric thresholds
        
        # Configuration
        self.stream_window_size = 100  # Number of events to keep in memory
        self.correlation_window = 300   # Seconds to look for correlations
        self.alert_cooldown = 3600     # Seconds between similar alerts
        
        # Threshold configurations
        self.base_thresholds = {
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {"warning": 140, "critical": 160},
            MetricType.BLOOD_PRESSURE_DIASTOLIC: {"warning": 90, "critical": 100},
            MetricType.HEART_RATE: {"warning": 100, "critical": 120},
            MetricType.BLOOD_GLUCOSE: {"warning": 140, "critical": 200},
            MetricType.OXYGEN_SATURATION: {"warning": 95, "critical": 90},
            MetricType.TEMPERATURE: {"warning": 37.5, "critical": 38.5}
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process real-time health data and generate immediate insights.
        
        Args:
            data: Dictionary containing user_id and optional parameters
            db: Database session
            
        Returns:
            AgentResult with real-time analytics
        """
        user_id = data.get("user_id")
        analysis_window = data.get("analysis_window", 3600)  # seconds
        include_correlations = data.get("include_correlations", True)
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Get recent health data
            recent_data = await self._get_recent_health_data(user_id, analysis_window, db)
            
            if not recent_data:
                return AgentResult(
                    success=True,
                    data={"alerts": [], "insights": [], "message": "No recent data for real-time analysis"}
                )
            
            # Process real-time events
            events = await self._process_real_time_events(user_id, recent_data)
            
            # Generate real-time alerts
            alerts = await self._generate_real_time_alerts(user_id, events)
            
            # Detect correlations
            correlations = []
            if include_correlations:
                correlations = await self._detect_correlations(user_id, events)
            
            # Update dynamic thresholds
            await self._update_dynamic_thresholds(user_id, recent_data)
            
            # Generate insights
            insights = self._generate_realtime_insights(events, alerts, correlations)
            recommendations = self._generate_realtime_recommendations(alerts, correlations)
            
            return AgentResult(
                success=True,
                data={
                    "events": [self._event_to_dict(event) for event in events],
                    "alerts": [self._alert_to_dict(alert) for alert in alerts],
                    "correlations": correlations,
                    "dynamic_thresholds": self.dynamic_thresholds.get(user_id, {}),
                    "analysis_window_seconds": analysis_window
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.95  # Very high confidence for real-time data
            )
            
        except Exception as e:
            logger.error(f"Real-time analytics failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Real-time analytics failed: {str(e)}"
            )
    
    async def _get_recent_health_data(self, user_id: str, analysis_window: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get recent health data for real-time analysis"""
        start_time = datetime.utcnow() - timedelta(seconds=analysis_window)
        
        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.created_at >= start_time
            )
        ).order_by(HealthMetric.created_at.desc())
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        return [
            {
                "id": metric.id,
                "metric_type": metric.metric_type.value,
                "value": metric.value,
                "timestamp": metric.created_at,
                "metadata": metric.metric_metadata
            }
            for metric in metrics
        ]
    
    async def _process_real_time_events(self, user_id: str, recent_data: List[Dict[str, Any]]) -> List[HealthEvent]:
        """Process health data into real-time events"""
        events = []
        
        for data_point in recent_data:
            # Create base event
            event = HealthEvent(
                event_id=f"{user_id}_{data_point['id']}",
                event_type=EventType.METRIC_UPDATE,
                timestamp=data_point["timestamp"],
                user_id=user_id,
                metric_type=data_point["metric_type"],
                value=data_point["value"],
                severity=AlertSeverity.INFO,
                description=f"Updated {data_point['metric_type']} to {data_point['value']}",
                metadata=data_point["metadata"]
            )
            
            # Check for threshold breaches
            threshold_event = self._check_threshold_breach(event)
            if threshold_event:
                events.append(threshold_event)
            
            # Check for trend changes
            trend_event = await self._check_trend_change(user_id, event)
            if trend_event:
                events.append(trend_event)
            
            # Check for anomalies
            anomaly_event = await self._check_anomaly(user_id, event)
            if anomaly_event:
                events.append(anomaly_event)
            
            # Add base event
            events.append(event)
            
            # Update event stream
            self.event_streams[user_id].append(event)
            if len(self.event_streams[user_id]) > self.stream_window_size:
                self.event_streams[user_id].popleft()
        
        return events
    
    def _check_threshold_breach(self, event: HealthEvent) -> Optional[HealthEvent]:
        """Check if event breaches thresholds"""
        metric_type = MetricType(event.metric_type)
        thresholds = self.base_thresholds.get(metric_type, {})
        
        if not thresholds:
            return None
        
        value = event.value
        severity = None
        
        if "critical" in thresholds and value >= thresholds["critical"]:
            severity = AlertSeverity.CRITICAL
        elif "warning" in thresholds and value >= thresholds["warning"]:
            severity = AlertSeverity.WARNING
        
        if severity:
            return HealthEvent(
                event_id=f"{event.event_id}_threshold",
                event_type=EventType.THRESHOLD_BREACH,
                timestamp=event.timestamp,
                user_id=event.user_id,
                metric_type=event.metric_type,
                value=event.value,
                severity=severity,
                description=f"{event.metric_type} breached {severity.value} threshold: {event.value}",
                metadata={"threshold": thresholds, "breach_type": severity.value}
            )
        
        return None
    
    async def _check_trend_change(self, user_id: str, event: HealthEvent) -> Optional[HealthEvent]:
        """Check for trend changes in real-time"""
        user_events = self.event_streams[user_id]
        
        if len(user_events) < 5:
            return None
        
        # Get recent events for same metric
        metric_events = [e for e in user_events if e.metric_type == event.metric_type]
        
        if len(metric_events) < 5:
            return None
        
        # Calculate trend
        recent_values = [e.value for e in metric_events[-5:]]
        trend = self._calculate_trend(recent_values)
        
        # Check for significant trend change
        if abs(trend) > 0.1:  # 10% change threshold
            return HealthEvent(
                event_id=f"{event.event_id}_trend",
                event_type=EventType.TREND_CHANGE,
                timestamp=event.timestamp,
                user_id=event.user_id,
                metric_type=event.metric_type,
                value=event.value,
                severity=AlertSeverity.WARNING if abs(trend) > 0.2 else AlertSeverity.INFO,
                description=f"{event.metric_type} showing {'increasing' if trend > 0 else 'decreasing'} trend",
                metadata={"trend": trend, "trend_direction": "increasing" if trend > 0 else "decreasing"}
            )
        
        return None
    
    async def _check_anomaly(self, user_id: str, event: HealthEvent) -> Optional[HealthEvent]:
        """Check for anomalies in real-time"""
        user_events = self.event_streams[user_id]
        
        if len(user_events) < 10:
            return None
        
        # Get recent events for same metric
        metric_events = [e for e in user_events if e.metric_type == event.metric_type]
        
        if len(metric_events) < 10:
            return None
        
        # Calculate statistical anomaly
        values = [e.value for e in metric_events]
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return None
        
        z_score = abs((event.value - mean_val) / std_val)
        
        if z_score > 2.5:  # Anomaly threshold
            return HealthEvent(
                event_id=f"{event.event_id}_anomaly",
                event_type=EventType.ANOMALY_DETECTED,
                timestamp=event.timestamp,
                user_id=event.user_id,
                metric_type=event.metric_type,
                value=event.value,
                severity=AlertSeverity.WARNING if z_score > 3.0 else AlertSeverity.INFO,
                description=f"Anomaly detected in {event.metric_type}: {event.value} (z-score: {z_score:.2f})",
                metadata={"z_score": z_score, "mean": mean_val, "std": std_val}
            )
        
        return None
    
    async def _generate_real_time_alerts(self, user_id: str, events: List[HealthEvent]) -> List[RealTimeAlert]:
        """Generate real-time alerts from events"""
        alerts = []
        
        # Group events by severity and type
        critical_events = [e for e in events if e.severity == AlertSeverity.CRITICAL]
        warning_events = [e for e in events if e.severity == AlertSeverity.WARNING]
        
        # Generate critical alerts
        if critical_events:
            alert = RealTimeAlert(
                alert_id=f"{user_id}_critical_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                severity=AlertSeverity.CRITICAL,
                title="Critical Health Alert",
                description=f"Critical health issues detected: {len(critical_events)} events",
                affected_metrics=list(set([e.metric_type for e in critical_events])),
                recommendations=self._generate_critical_recommendations(critical_events),
                correlation_events=[e.event_id for e in critical_events],
                requires_immediate_action=True
            )
            alerts.append(alert)
        
        # Generate warning alerts
        if warning_events:
            alert = RealTimeAlert(
                alert_id=f"{user_id}_warning_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                severity=AlertSeverity.WARNING,
                title="Health Warning",
                description=f"Health warnings detected: {len(warning_events)} events",
                affected_metrics=list(set([e.metric_type for e in warning_events])),
                recommendations=self._generate_warning_recommendations(warning_events),
                correlation_events=[e.event_id for e in warning_events],
                requires_immediate_action=False
            )
            alerts.append(alert)
        
        # Check for pattern-based alerts
        pattern_alerts = await self._generate_pattern_alerts(user_id, events)
        alerts.extend(pattern_alerts)
        
        # Update alert history
        self.alert_history[user_id].extend(alerts)
        
        return alerts
    
    async def _detect_correlations(self, user_id: str, events: List[HealthEvent]) -> List[Dict[str, Any]]:
        """Detect correlations between different metrics"""
        correlations = []
        
        if len(events) < 10:
            return correlations
        
        # Group events by metric type
        metric_groups = defaultdict(list)
        for event in events:
            metric_groups[event.metric_type].append(event)
        
        # Find correlations between different metrics
        metric_types = list(metric_groups.keys())
        
        for i, metric1 in enumerate(metric_types):
            for metric2 in metric_types[i+1:]:
                if len(metric_groups[metric1]) >= 5 and len(metric_groups[metric2]) >= 5:
                    correlation = self._calculate_correlation(
                        [e.value for e in metric_groups[metric1]],
                        [e.value for e in metric_groups[metric2]]
                    )
                    
                    if abs(correlation) > 0.7:  # Strong correlation threshold
                        correlations.append({
                            "metric1": metric1,
                            "metric2": metric2,
                            "correlation": correlation,
                            "strength": "strong" if abs(correlation) > 0.8 else "moderate",
                            "description": f"Strong correlation between {metric1} and {metric2}"
                        })
        
        # Store correlation patterns
        self.correlation_patterns[user_id].extend(correlations)
        
        return correlations
    
    async def _update_dynamic_thresholds(self, user_id: str, recent_data: List[Dict[str, Any]]) -> None:
        """Update dynamic thresholds based on user's historical data"""
        if not recent_data:
            return
        
        # Group data by metric type
        metric_groups = defaultdict(list)
        for data_point in recent_data:
            metric_groups[data_point["metric_type"]].append(data_point["value"])
        
        # Calculate adaptive thresholds
        for metric_type, values in metric_groups.items():
            if len(values) < 10:
                continue
            
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            # Dynamic thresholds based on user's baseline
            self.dynamic_thresholds[user_id][metric_type] = {
                "warning": mean_val + (1.5 * std_val),
                "critical": mean_val + (2.5 * std_val),
                "baseline_mean": mean_val,
                "baseline_std": std_val
            }
    
    async def _generate_pattern_alerts(self, user_id: str, events: List[HealthEvent]) -> List[RealTimeAlert]:
        """Generate alerts based on detected patterns"""
        alerts = []
        
        if len(events) < 5:
            return alerts
        
        # Check for rapid changes
        rapid_changes = self._detect_rapid_changes(events)
        if rapid_changes:
            alert = RealTimeAlert(
                alert_id=f"{user_id}_rapid_change_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow(),
                user_id=user_id,
                severity=AlertSeverity.WARNING,
                title="Rapid Health Changes Detected",
                description=f"Rapid changes detected in {len(rapid_changes)} metrics",
                affected_metrics=list(set([e.metric_type for e in rapid_changes])),
                recommendations=["Monitor these changes closely", "Consider lifestyle factors"],
                correlation_events=[e.event_id for e in rapid_changes],
                requires_immediate_action=False
            )
            alerts.append(alert)
        
        return alerts
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend from values"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        return coeffs[0]  # Slope
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate correlation between two value lists"""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        return np.corrcoef(values1, values2)[0, 1]
    
    def _detect_rapid_changes(self, events: List[HealthEvent]) -> List[HealthEvent]:
        """Detect rapid changes in health metrics"""
        rapid_changes = []
        
        # Group by metric type
        metric_events = defaultdict(list)
        for event in events:
            metric_events[event.metric_type].append(event)
        
        for metric_type, metric_event_list in metric_events.items():
            if len(metric_event_list) < 3:
                continue
            
            # Sort by timestamp
            sorted_events = sorted(metric_event_list, key=lambda x: x.timestamp)
            
            # Check for rapid changes
            for i in range(1, len(sorted_events)):
                current_event = sorted_events[i]
                previous_event = sorted_events[i-1]
                
                time_diff = (current_event.timestamp - previous_event.timestamp).total_seconds()
                value_diff = abs(current_event.value - previous_event.value)
                
                if time_diff > 0:
                    change_rate = value_diff / time_diff
                    
                    # Define rapid change threshold based on metric type
                    threshold = self._get_rapid_change_threshold(metric_type)
                    
                    if change_rate > threshold:
                        rapid_changes.append(current_event)
        
        return rapid_changes
    
    def _get_rapid_change_threshold(self, metric_type: str) -> float:
        """Get rapid change threshold for metric type"""
        thresholds = {
            "heart_rate": 10.0,  # bpm per second
            "blood_pressure_systolic": 5.0,  # mmHg per second
            "blood_glucose": 2.0,  # mg/dL per second
            "temperature": 0.1,  # °C per second
            "oxygen_saturation": 1.0,  # % per second
        }
        
        return thresholds.get(metric_type, 1.0)
    
    def _generate_critical_recommendations(self, events: List[HealthEvent]) -> List[str]:
        """Generate recommendations for critical events"""
        recommendations = []
        
        for event in events:
            if event.metric_type == "blood_pressure_systolic" and event.value > 160:
                recommendations.append("Seek immediate medical attention for high blood pressure")
            elif event.metric_type == "heart_rate" and event.value > 120:
                recommendations.append("Rest and monitor heart rate - seek medical attention if persistent")
            elif event.metric_type == "blood_glucose" and event.value > 200:
                recommendations.append("Check blood glucose management - consult healthcare provider")
            elif event.metric_type == "oxygen_saturation" and event.value < 90:
                recommendations.append("Seek immediate medical attention for low oxygen levels")
        
        recommendations.extend([
            "Contact healthcare provider immediately",
            "Monitor symptoms closely",
            "Follow emergency protocols if necessary"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_warning_recommendations(self, events: List[HealthEvent]) -> List[str]:
        """Generate recommendations for warning events"""
        recommendations = []
        
        for event in events:
            if event.metric_type == "blood_pressure_systolic" and event.value > 140:
                recommendations.append("Monitor blood pressure regularly and reduce sodium intake")
            elif event.metric_type == "heart_rate" and event.value > 100:
                recommendations.append("Practice stress reduction techniques and monitor heart rate")
            elif event.metric_type == "blood_glucose" and event.value > 140:
                recommendations.append("Monitor carbohydrate intake and exercise regularly")
        
        recommendations.extend([
            "Continue monitoring health metrics",
            "Consider lifestyle modifications",
            "Schedule follow-up with healthcare provider"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_realtime_insights(self, events: List[HealthEvent], alerts: List[RealTimeAlert], correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate real-time insights"""
        insights = []
        
        if events:
            insights.append(f"Processed {len(events)} health events in real-time")
        
        if alerts:
            critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
            if critical_alerts:
                insights.append(f"Generated {len(critical_alerts)} critical alerts requiring immediate attention")
        
        if correlations:
            insights.append(f"Detected {len(correlations)} strong correlations between health metrics")
        
        # Trend insights
        trend_events = [e for e in events if e.event_type == EventType.TREND_CHANGE]
        if trend_events:
            insights.append(f"Identified {len(trend_events)} significant trend changes")
        
        # Anomaly insights
        anomaly_events = [e for e in events if e.event_type == EventType.ANOMALY_DETECTED]
        if anomaly_events:
            insights.append(f"Detected {len(anomaly_events)} anomalies in health data")
        
        return insights
    
    def _generate_realtime_recommendations(self, alerts: List[RealTimeAlert], correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate real-time recommendations"""
        recommendations = []
        
        if alerts:
            recommendations.append("Review and respond to generated alerts promptly")
        
        if correlations:
            recommendations.append("Consider how correlated metrics affect each other")
        
        recommendations.extend([
            "Continue real-time monitoring for early detection",
            "Use insights to make proactive health decisions",
            "Share findings with healthcare providers"
        ])
        
        return recommendations
    
    def _event_to_dict(self, event: HealthEvent) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "metric_type": event.metric_type,
            "value": event.value,
            "severity": event.severity.value,
            "description": event.description,
            "metadata": event.metadata
        }
    
    def _alert_to_dict(self, alert: RealTimeAlert) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "alert_id": alert.alert_id,
            "timestamp": alert.timestamp.isoformat(),
            "user_id": alert.user_id,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "affected_metrics": alert.affected_metrics,
            "recommendations": alert.recommendations,
            "correlation_events": alert.correlation_events,
            "requires_immediate_action": alert.requires_immediate_action
        } 