"""
Pattern Recognizer Agent
Autonomous agent for recognizing patterns and correlations in health data.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from enum import Enum
from dataclasses import dataclass

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from ..models.vital_signs import VitalSigns, VitalSignType
from ..models.symptoms import Symptoms, SymptomCategory
from common.utils.logging import get_logger

logger = get_logger(__name__)

class PatternType(Enum):
    """Pattern type enumeration"""
    CORRELATION = "correlation"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    TREND = "trend"
    ANOMALY = "anomaly"
    HABIT = "habit"
    TRIGGER = "trigger"

@dataclass
class HealthPattern:
    """Health pattern recognition result"""
    pattern_type: PatternType
    description: str
    metrics_involved: List[str]
    strength: float  # 0-1 correlation strength
    confidence: float  # 0-1 confidence level
    time_period: str
    frequency: str
    significance: str  # "high", "medium", "low"
    insights: List[str]
    recommendations: List[str]

class PatternRecognizerAgent(BaseHealthAgent):
    """
    Autonomous agent for recognizing patterns and correlations in health data.
    Uses statistical methods and machine learning to identify meaningful patterns.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="pattern_recognizer",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Pattern recognition parameters
        self.min_data_points = 10
        self.correlation_threshold = 0.3
        self.confidence_threshold = 0.6
        
        # Pattern categories and their characteristics
        self.pattern_categories = {
            "daily_patterns": {
                "time_period": "24 hours",
                "frequency": "daily",
                "description": "Daily patterns in health metrics"
            },
            "weekly_patterns": {
                "time_period": "7 days",
                "frequency": "weekly",
                "description": "Weekly patterns in health metrics"
            },
            "monthly_patterns": {
                "time_period": "30 days",
                "frequency": "monthly",
                "description": "Monthly patterns in health metrics"
            },
            "seasonal_patterns": {
                "time_period": "90 days",
                "frequency": "seasonal",
                "description": "Seasonal patterns in health metrics"
            }
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Recognize patterns in health data.
        
        Args:
            data: Dictionary containing user_id and optional parameters
            db: Database session
            
        Returns:
            AgentResult with pattern recognition results
        """
        user_id = data.get("user_id")
        pattern_types = data.get("pattern_types", ["correlation", "trend", "seasonal"])
        time_period = data.get("time_period", 90)  # days
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Collect comprehensive health data
            health_data = await self._collect_pattern_data(user_id, time_period, db)
            
            # Recognize different types of patterns
            patterns = []
            
            if "correlation" in pattern_types:
                correlation_patterns = await self._find_correlations(health_data)
                patterns.extend(correlation_patterns)
            
            if "trend" in pattern_types:
                trend_patterns = await self._find_trends(health_data)
                patterns.extend(trend_patterns)
            
            if "seasonal" in pattern_types:
                seasonal_patterns = await self._find_seasonal_patterns(health_data)
                patterns.extend(seasonal_patterns)
            
            if "habit" in pattern_types:
                habit_patterns = await self._find_habit_patterns(health_data)
                patterns.extend(habit_patterns)
            
            # Analyze pattern significance and generate insights
            significant_patterns = self._filter_significant_patterns(patterns)
            insights = self._generate_pattern_insights(significant_patterns)
            recommendations = self._generate_pattern_recommendations(significant_patterns)
            
            return AgentResult(
                success=True,
                data={
                    "patterns": [pattern.__dict__ for pattern in significant_patterns],
                    "total_patterns_found": len(patterns),
                    "significant_patterns": len(significant_patterns),
                    "time_period_days": time_period,
                    "pattern_types_analyzed": pattern_types
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.82
            )
            
        except Exception as e:
            logger.error(f"Pattern recognition failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Pattern recognition failed: {str(e)}"
            )
    
    async def _collect_pattern_data(self, user_id: str, time_period: int, db: AsyncSession) -> Dict[str, Any]:
        """Collect health data for pattern analysis"""
        start_date = datetime.utcnow() - timedelta(days=time_period)
        
        health_data = {
            "metrics": {},
            "vital_signs": {},
            "symptoms": [],
            "timestamps": []
        }
        
        # Collect health metrics
        for metric_type in MetricType:
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.created_at >= start_date
                )
            ).order_by(HealthMetric.created_at)
            
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            if len(metrics) >= self.min_data_points:
                health_data["metrics"][metric_type.value] = {
                    "values": [m.value for m in metrics],
                    "timestamps": [m.created_at for m in metrics],
                    "count": len(metrics)
                }
        
        # Collect vital signs
        for vital_type in VitalSignType:
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.user_id == user_id,
                    VitalSigns.vital_sign_type == vital_type.value,
                    VitalSigns.created_at >= start_date
                )
            ).order_by(VitalSigns.created_at)
            
            result = await db.execute(query)
            vital_signs = result.scalars().all()
            
            if len(vital_signs) >= self.min_data_points:
                values = [self._get_vital_sign_value(vs, vital_type.value) for vs in vital_signs]
                values = [v for v in values if v is not None]
                
                if len(values) >= self.min_data_points:
                    health_data["vital_signs"][vital_type.value] = {
                        "values": values,
                        "timestamps": [vs.created_at for vs in vital_signs[:len(values)]],
                        "count": len(values)
                    }
        
        # Collect symptoms
        query = select(Symptoms).where(
            and_(
                Symptoms.user_id == user_id,
                Symptoms.created_at >= start_date
            )
        ).order_by(Symptoms.created_at)
        
        result = await db.execute(query)
        symptoms = result.scalars().all()
        
        health_data["symptoms"] = [
            {
                "name": symptom.symptom_name,
                "severity": symptom.severity,
                "frequency": symptom.frequency,
                "timestamp": symptom.created_at,
                "category": symptom.symptom_category
            }
            for symptom in symptoms
        ]
        
        return health_data
    
    async def _find_correlations(self, health_data: Dict[str, Any]) -> List[HealthPattern]:
        """Find correlations between different health metrics"""
        patterns = []
        
        # Get all metric data
        all_metrics = {}
        all_metrics.update(health_data["metrics"])
        all_metrics.update(health_data["vital_signs"])
        
        metric_names = list(all_metrics.keys())
        
        # Find correlations between pairs of metrics
        for i in range(len(metric_names)):
            for j in range(i + 1, len(metric_names)):
                metric1_name = metric_names[i]
                metric2_name = metric_names[j]
                
                metric1_data = all_metrics[metric1_name]
                metric2_data = all_metrics[metric2_name]
                
                # Align data by timestamps
                aligned_data = self._align_metric_data(
                    metric1_data, metric2_data
                )
                
                if len(aligned_data) >= self.min_data_points:
                    correlation = self._calculate_correlation(
                        aligned_data["values1"], aligned_data["values2"]
                    )
                    
                    if abs(correlation) >= self.correlation_threshold:
                        pattern = HealthPattern(
                            pattern_type=PatternType.CORRELATION,
                            description=f"Correlation between {metric1_name} and {metric2_name}",
                            metrics_involved=[metric1_name, metric2_name],
                            strength=abs(correlation),
                            confidence=self._calculate_correlation_confidence(
                                len(aligned_data), abs(correlation)
                            ),
                            time_period="variable",
                            frequency="continuous",
                            significance=self._determine_significance(abs(correlation)),
                            insights=self._generate_correlation_insights(
                                metric1_name, metric2_name, correlation
                            ),
                            recommendations=self._generate_correlation_recommendations(
                                metric1_name, metric2_name, correlation
                            )
                        )
                        patterns.append(pattern)
        
        return patterns
    
    async def _find_trends(self, health_data: Dict[str, Any]) -> List[HealthPattern]:
        """Find trend patterns in health data"""
        patterns = []
        
        # Analyze trends for each metric
        all_metrics = {}
        all_metrics.update(health_data["metrics"])
        all_metrics.update(health_data["vital_signs"])
        
        for metric_name, metric_data in all_metrics.items():
            values = metric_data["values"]
            timestamps = metric_data["timestamps"]
            
            if len(values) >= self.min_data_points:
                # Calculate trend
                trend_strength, trend_direction = self._calculate_trend_pattern(values, timestamps)
                
                if abs(trend_strength) >= 0.2:  # Minimum trend strength
                    pattern = HealthPattern(
                        pattern_type=PatternType.TREND,
                        description=f"{trend_direction} trend in {metric_name}",
                        metrics_involved=[metric_name],
                        strength=abs(trend_strength),
                        confidence=self._calculate_trend_confidence(len(values), abs(trend_strength)),
                        time_period=f"{len(values)} data points",
                        frequency="continuous",
                        significance=self._determine_significance(abs(trend_strength)),
                        insights=self._generate_trend_insights(metric_name, trend_direction, trend_strength),
                        recommendations=self._generate_trend_recommendations(metric_name, trend_direction)
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _find_seasonal_patterns(self, health_data: Dict[str, Any]) -> List[HealthPattern]:
        """Find seasonal patterns in health data"""
        patterns = []
        
        # Analyze seasonal patterns for each metric
        all_metrics = {}
        all_metrics.update(health_data["metrics"])
        all_metrics.update(health_data["vital_signs"])
        
        for metric_name, metric_data in all_metrics.items():
            values = metric_data["values"]
            timestamps = metric_data["timestamps"]
            
            if len(values) >= 30:  # Need more data for seasonal analysis
                seasonal_pattern = self._detect_seasonal_pattern(values, timestamps)
                
                if seasonal_pattern["detected"]:
                    pattern = HealthPattern(
                        pattern_type=PatternType.SEASONAL,
                        description=f"Seasonal pattern in {metric_name}",
                        metrics_involved=[metric_name],
                        strength=seasonal_pattern["strength"],
                        confidence=seasonal_pattern["confidence"],
                        time_period="seasonal",
                        frequency=seasonal_pattern["frequency"],
                        significance=self._determine_significance(seasonal_pattern["strength"]),
                        insights=self._generate_seasonal_insights(metric_name, seasonal_pattern),
                        recommendations=self._generate_seasonal_recommendations(metric_name, seasonal_pattern)
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def _find_habit_patterns(self, health_data: Dict[str, Any]) -> List[HealthPattern]:
        """Find habit patterns in health data"""
        patterns = []
        
        # Analyze daily and weekly patterns
        all_metrics = {}
        all_metrics.update(health_data["metrics"])
        all_metrics.update(health_data["vital_signs"])
        
        for metric_name, metric_data in all_metrics.items():
            values = metric_data["values"]
            timestamps = metric_data["timestamps"]
            
            if len(values) >= 14:  # At least 2 weeks of data
                # Check for daily patterns
                daily_pattern = self._detect_daily_pattern(values, timestamps)
                if daily_pattern["detected"]:
                    pattern = HealthPattern(
                        pattern_type=PatternType.HABIT,
                        description=f"Daily habit pattern in {metric_name}",
                        metrics_involved=[metric_name],
                        strength=daily_pattern["strength"],
                        confidence=daily_pattern["confidence"],
                        time_period="daily",
                        frequency="daily",
                        significance=self._determine_significance(daily_pattern["strength"]),
                        insights=self._generate_habit_insights(metric_name, "daily", daily_pattern),
                        recommendations=self._generate_habit_recommendations(metric_name, "daily")
                    )
                    patterns.append(pattern)
                
                # Check for weekly patterns
                weekly_pattern = self._detect_weekly_pattern(values, timestamps)
                if weekly_pattern["detected"]:
                    pattern = HealthPattern(
                        pattern_type=PatternType.HABIT,
                        description=f"Weekly habit pattern in {metric_name}",
                        metrics_involved=[metric_name],
                        strength=weekly_pattern["strength"],
                        confidence=weekly_pattern["confidence"],
                        time_period="weekly",
                        frequency="weekly",
                        significance=self._determine_significance(weekly_pattern["strength"]),
                        insights=self._generate_habit_insights(metric_name, "weekly", weekly_pattern),
                        recommendations=self._generate_habit_recommendations(metric_name, "weekly")
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _align_metric_data(self, metric1_data: Dict[str, Any], metric2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Align two metrics by timestamps"""
        aligned = {
            "values1": [],
            "values2": [],
            "timestamps": []
        }
        
        # Create timestamp mapping for metric1
        metric1_map = {}
        for i, timestamp in enumerate(metric1_data["timestamps"]):
            metric1_map[timestamp] = metric1_data["values"][i]
        
        # Align with metric2
        for i, timestamp in enumerate(metric2_data["timestamps"]):
            if timestamp in metric1_map:
                aligned["values1"].append(metric1_map[timestamp])
                aligned["values2"].append(metric2_data["values"][i])
                aligned["timestamps"].append(timestamp)
        
        return aligned
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate correlation coefficient between two sets of values"""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        try:
            correlation = np.corrcoef(values1, values2)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except:
            return 0.0
    
    def _calculate_correlation_confidence(self, sample_size: int, correlation: float) -> float:
        """Calculate confidence level for correlation"""
        # Simplified confidence calculation based on sample size and correlation strength
        base_confidence = min(sample_size / 50.0, 1.0)  # More data = higher confidence
        correlation_boost = correlation * 0.3  # Stronger correlation = higher confidence
        return min(base_confidence + correlation_boost, 1.0)
    
    def _calculate_trend_pattern(self, values: List[float], timestamps: List[datetime]) -> Tuple[float, str]:
        """Calculate trend pattern in values"""
        if len(values) < 2:
            return 0.0, "stable"
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        y = values
        
        try:
            # Calculate slope
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            
            # Normalize slope to 0-1 range
            max_slope = max(abs(max(y) - min(y)) / len(y), 1.0)
            normalized_slope = abs(slope) / max_slope
            
            direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            
            return normalized_slope, direction
        except:
            return 0.0, "stable"
    
    def _calculate_trend_confidence(self, sample_size: int, trend_strength: float) -> float:
        """Calculate confidence level for trend"""
        base_confidence = min(sample_size / 30.0, 1.0)
        trend_boost = trend_strength * 0.4
        return min(base_confidence + trend_boost, 1.0)
    
    def _detect_seasonal_pattern(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Detect seasonal patterns in data"""
        if len(values) < 30:
            return {"detected": False}
        
        # Simplified seasonal detection
        # Group by month and check for patterns
        monthly_averages = {}
        for i, timestamp in enumerate(timestamps):
            month = timestamp.month
            if month not in monthly_averages:
                monthly_averages[month] = []
            monthly_averages[month].append(values[i])
        
        if len(monthly_averages) < 3:
            return {"detected": False}
        
        # Calculate variance between months
        monthly_means = [np.mean(monthly_averages[month]) for month in sorted(monthly_averages.keys())]
        variance = np.var(monthly_means)
        mean_value = np.mean(values)
        
        if mean_value == 0:
            return {"detected": False}
        
        seasonal_strength = variance / (mean_value ** 2)
        
        return {
            "detected": seasonal_strength > 0.1,
            "strength": min(seasonal_strength, 1.0),
            "confidence": min(len(monthly_averages) / 12.0, 1.0),
            "frequency": "monthly"
        }
    
    def _detect_daily_pattern(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Detect daily patterns in data"""
        if len(values) < 7:
            return {"detected": False}
        
        # Group by hour of day
        hourly_averages = {}
        for i, timestamp in enumerate(timestamps):
            hour = timestamp.hour
            if hour not in hourly_averages:
                hourly_averages[hour] = []
            hourly_averages[hour].append(values[i])
        
        if len(hourly_averages) < 6:
            return {"detected": False}
        
        # Calculate variance between hours
        hourly_means = [np.mean(hourly_averages[hour]) for hour in sorted(hourly_averages.keys())]
        variance = np.var(hourly_means)
        mean_value = np.mean(values)
        
        if mean_value == 0:
            return {"detected": False}
        
        daily_strength = variance / (mean_value ** 2)
        
        return {
            "detected": daily_strength > 0.05,
            "strength": min(daily_strength, 1.0),
            "confidence": min(len(hourly_averages) / 24.0, 1.0),
            "frequency": "daily"
        }
    
    def _detect_weekly_pattern(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Detect weekly patterns in data"""
        if len(values) < 14:
            return {"detected": False}
        
        # Group by day of week
        daily_averages = {}
        for i, timestamp in enumerate(timestamps):
            day = timestamp.weekday()
            if day not in daily_averages:
                daily_averages[day] = []
            daily_averages[day].append(values[i])
        
        if len(daily_averages) < 4:
            return {"detected": False}
        
        # Calculate variance between days
        daily_means = [np.mean(daily_averages[day]) for day in sorted(daily_averages.keys())]
        variance = np.var(daily_means)
        mean_value = np.mean(values)
        
        if mean_value == 0:
            return {"detected": False}
        
        weekly_strength = variance / (mean_value ** 2)
        
        return {
            "detected": weekly_strength > 0.05,
            "strength": min(weekly_strength, 1.0),
            "confidence": min(len(daily_averages) / 7.0, 1.0),
            "frequency": "weekly"
        }
    
    def _determine_significance(self, strength: float) -> str:
        """Determine significance level based on strength"""
        if strength >= 0.7:
            return "high"
        elif strength >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _filter_significant_patterns(self, patterns: List[HealthPattern]) -> List[HealthPattern]:
        """Filter patterns based on significance and confidence"""
        return [
            pattern for pattern in patterns
            if pattern.confidence >= self.confidence_threshold and pattern.significance != "low"
        ]
    
    def _get_vital_sign_value(self, vital_sign: VitalSigns, vital_type: str) -> Optional[float]:
        """Get the relevant value for a vital sign type"""
        value_mapping = {
            VitalSignType.BLOOD_PRESSURE_SYSTOLIC.value: vital_sign.systolic,
            VitalSignType.HEART_RATE.value: vital_sign.heart_rate,
            VitalSignType.BODY_TEMPERATURE.value: vital_sign.temperature,
            VitalSignType.OXYGEN_SATURATION.value: vital_sign.oxygen_saturation,
            VitalSignType.RESPIRATORY_RATE.value: vital_sign.respiratory_rate,
            VitalSignType.BLOOD_GLUCOSE.value: vital_sign.blood_glucose,
        }
        
        return value_mapping.get(vital_type)
    
    def _generate_correlation_insights(self, metric1: str, metric2: str, correlation: float) -> List[str]:
        """Generate insights for correlation patterns"""
        insights = []
        
        if abs(correlation) >= 0.7:
            insights.append(f"Strong correlation between {metric1} and {metric2}")
        elif abs(correlation) >= 0.4:
            insights.append(f"Moderate correlation between {metric1} and {metric2}")
        else:
            insights.append(f"Weak correlation between {metric1} and {metric2}")
        
        if correlation > 0:
            insights.append(f"When {metric1} increases, {metric2} tends to increase")
        else:
            insights.append(f"When {metric1} increases, {metric2} tends to decrease")
        
        return insights
    
    def _generate_correlation_recommendations(self, metric1: str, metric2: str, correlation: float) -> List[str]:
        """Generate recommendations for correlation patterns"""
        recommendations = []
        
        if abs(correlation) >= 0.5:
            recommendations.append(f"Monitor both {metric1} and {metric2} together")
            recommendations.append(f"Consider how changes in {metric1} affect {metric2}")
        
        if correlation > 0.7:
            recommendations.append(f"Strong positive relationship - focus on improving both metrics")
        elif correlation < -0.7:
            recommendations.append(f"Strong inverse relationship - balance improvements between metrics")
        
        return recommendations
    
    def _generate_trend_insights(self, metric: str, direction: str, strength: float) -> List[str]:
        """Generate insights for trend patterns"""
        insights = []
        
        if direction == "increasing":
            insights.append(f"{metric} shows an upward trend")
            if strength >= 0.7:
                insights.append(f"Strong increasing trend in {metric}")
        elif direction == "decreasing":
            insights.append(f"{metric} shows a downward trend")
            if strength >= 0.7:
                insights.append(f"Strong decreasing trend in {metric}")
        else:
            insights.append(f"{metric} shows a stable pattern")
        
        return insights
    
    def _generate_trend_recommendations(self, metric: str, direction: str) -> List[str]:
        """Generate recommendations for trend patterns"""
        recommendations = []
        
        if direction == "increasing":
            if "blood_pressure" in metric.lower() or "glucose" in metric.lower():
                recommendations.append(f"Monitor {metric} closely - consider lifestyle interventions")
            else:
                recommendations.append(f"Continue positive trend in {metric}")
        elif direction == "decreasing":
            if "steps" in metric.lower() or "activity" in metric.lower():
                recommendations.append(f"Focus on increasing {metric} levels")
            else:
                recommendations.append(f"Monitor {metric} - ensure healthy levels are maintained")
        
        return recommendations
    
    def _generate_seasonal_insights(self, metric: str, seasonal_pattern: Dict[str, Any]) -> List[str]:
        """Generate insights for seasonal patterns"""
        insights = []
        
        insights.append(f"{metric} shows seasonal variation")
        insights.append(f"Pattern strength: {seasonal_pattern['strength']:.2f}")
        
        return insights
    
    def _generate_seasonal_recommendations(self, metric: str, seasonal_pattern: Dict[str, Any]) -> List[str]:
        """Generate recommendations for seasonal patterns"""
        recommendations = []
        
        recommendations.append(f"Account for seasonal variations in {metric}")
        recommendations.append(f"Adjust expectations based on seasonal patterns")
        
        return recommendations
    
    def _generate_habit_insights(self, metric: str, frequency: str, pattern: Dict[str, Any]) -> List[str]:
        """Generate insights for habit patterns"""
        insights = []
        
        insights.append(f"{metric} shows {frequency} habit patterns")
        insights.append(f"Pattern strength: {pattern['strength']:.2f}")
        
        return insights
    
    def _generate_habit_recommendations(self, metric: str, frequency: str) -> List[str]:
        """Generate recommendations for habit patterns"""
        recommendations = []
        
        if frequency == "daily":
            recommendations.append(f"Leverage daily patterns in {metric} for better planning")
            recommendations.append(f"Establish consistent daily routines for {metric}")
        elif frequency == "weekly":
            recommendations.append(f"Use weekly patterns in {metric} for goal setting")
            recommendations.append(f"Plan activities around weekly {metric} patterns")
        
        return recommendations
    
    def _generate_pattern_insights(self, patterns: List[HealthPattern]) -> List[str]:
        """Generate overall pattern insights"""
        insights = []
        
        if not patterns:
            insights.append("No significant patterns detected in your health data")
            return insights
        
        pattern_types = [p.pattern_type.value for p in patterns]
        unique_types = list(set(pattern_types))
        
        insights.append(f"Detected {len(patterns)} significant patterns across {len(unique_types)} categories")
        
        # Count by type
        for pattern_type in unique_types:
            count = pattern_types.count(pattern_type)
            insights.append(f"Found {count} {pattern_type} patterns")
        
        # High significance patterns
        high_significance = [p for p in patterns if p.significance == "high"]
        if high_significance:
            insights.append(f"Identified {len(high_significance)} highly significant patterns")
        
        return insights
    
    def _generate_pattern_recommendations(self, patterns: List[HealthPattern]) -> List[str]:
        """Generate overall pattern recommendations"""
        recommendations = []
        
        if not patterns:
            recommendations.append("Continue monitoring your health data to identify patterns")
            return recommendations
        
        # Group by pattern type
        correlation_patterns = [p for p in patterns if p.pattern_type == PatternType.CORRELATION]
        trend_patterns = [p for p in patterns if p.pattern_type == PatternType.TREND]
        habit_patterns = [p for p in patterns if p.pattern_type == PatternType.HABIT]
        
        if correlation_patterns:
            recommendations.append("Use correlation insights to optimize multiple health metrics together")
        
        if trend_patterns:
            recommendations.append("Monitor trend patterns to track long-term health changes")
        
        if habit_patterns:
            recommendations.append("Leverage habit patterns to build consistent health routines")
        
        recommendations.append("Use pattern insights to make informed health decisions")
        recommendations.append("Continue tracking to refine pattern understanding")
        
        return recommendations 