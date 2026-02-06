"""
Trend Analyzer Agent
Autonomously analyzes trends and patterns in health data over time.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from scipy import stats
from enum import Enum
from dataclasses import dataclass

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from common.utils.logging import get_logger

logger = get_logger(__name__)

class TrendDirection(Enum):
    """Trend direction enumeration"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    metric_type: MetricType
    direction: TrendDirection
    slope: float
    r_squared: float
    p_value: float
    confidence: float
    data_points: int
    time_period_days: int
    description: str
    significance: str  # "high", "medium", "low"

class TrendAnalyzerAgent(BaseHealthAgent):
    """
    Autonomous agent for analyzing trends in health data.
    Uses statistical methods to identify patterns and predict future values.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="trend_analyzer",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Minimum data points for trend analysis
        self.min_data_points = 5
        self.optimal_data_points = 14  # 2 weeks of daily data
        
        # Trend significance thresholds
        self.significance_thresholds = {
            "high": 0.01,    # p < 0.01
            "medium": 0.05,  # p < 0.05
            "low": 0.1       # p < 0.1
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Analyze trends in health data.
        
        Args:
            data: Dictionary containing user_id and optional parameters
            db: Database session
            
        Returns:
            AgentResult with trend analysis
        """
        user_id = data.get("user_id")
        metric_type = data.get("metric_type")
        time_period = data.get("time_period", 30)  # days
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Get health data for trend analysis
            metrics = await self._get_trend_data(user_id, metric_type, time_period, db)
            
            if not metrics:
                return AgentResult(
                    success=True,
                    data={"trends": [], "message": "Insufficient data for trend analysis"}
                )
            
            # Analyze trends
            trends = await self._analyze_trends(metrics, time_period)
            
            # Generate insights and predictions
            insights = self._generate_trend_insights(trends)
            predictions = self._generate_predictions(trends)
            recommendations = self._generate_trend_recommendations(trends)
            
            return AgentResult(
                success=True,
                data={
                    "trends": [self._trend_to_dict(trend) for trend in trends],
                    "total_metrics_analyzed": len(metrics),
                    "trend_count": len(trends),
                    "time_period_days": time_period
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.80  # Good confidence for statistical analysis
            )
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Trend analysis failed: {str(e)}"
            )
    
    async def _get_trend_data(self, user_id: str, metric_type: Optional[MetricType], time_period: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get health data for trend analysis"""
        start_date = datetime.utcnow() - timedelta(days=time_period)
        
        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.created_at >= start_date
            )
        )
        
        if metric_type:
            query = query.where(HealthMetric.metric_type == metric_type)
        
        query = query.order_by(HealthMetric.created_at.asc())
        
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
    
    async def _analyze_trends(self, metrics: List[Dict[str, Any]], time_period: int) -> List[TrendAnalysis]:
        """Analyze trends in health data"""
        trends = []
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            metric_type = metric["metric_type"]
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric)
        
        # Analyze trends for each metric type
        for metric_type, type_metrics in metrics_by_type.items():
            if len(type_metrics) < self.min_data_points:
                continue
            
            # Sort by timestamp
            sorted_metrics = sorted(type_metrics, key=lambda x: x["created_at"])
            
            # Extract time series data
            timestamps = [m["created_at"] for m in sorted_metrics]
            values = [m["value"] for m in sorted_metrics]
            
            # Convert timestamps to days since first measurement
            start_time = timestamps[0]
            days_since_start = [(t - start_time).days for t in timestamps]
            
            # Perform linear regression
            trend = self._perform_linear_regression(
                days_since_start, values, metric_type, len(sorted_metrics), time_period
            )
            
            if trend:
                trends.append(trend)
        
        return trends
    
    def _perform_linear_regression(self, x: List[float], y: List[float], metric_type: MetricType, data_points: int, time_period: int) -> Optional[TrendAnalysis]:
        """Perform linear regression analysis"""
        try:
            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            r_squared = r_value ** 2
            
            # Determine trend direction
            direction = self._determine_trend_direction(slope, r_squared, p_value)
            
            # Calculate confidence
            confidence = self._calculate_confidence(r_squared, p_value, data_points)
            
            # Determine significance
            significance = self._determine_significance(p_value)
            
            # Generate description
            description = self._generate_trend_description(
                metric_type, direction, slope, r_squared, significance
            )
            
            return TrendAnalysis(
                metric_type=metric_type,
                direction=direction,
                slope=slope,
                r_squared=r_squared,
                p_value=p_value,
                confidence=confidence,
                data_points=data_points,
                time_period_days=time_period,
                description=description,
                significance=significance
            )
            
        except Exception as e:
            logger.error(f"Linear regression failed for {metric_type}: {str(e)}")
            return None
    
    def _determine_trend_direction(self, slope: float, r_squared: float, p_value: float) -> TrendDirection:
        """Determine the direction of the trend"""
        if p_value > 0.1:  # Not statistically significant
            return TrendDirection.STABLE
        
        if r_squared < 0.1:  # Low correlation
            return TrendDirection.FLUCTUATING
        
        if slope > 0:
            return TrendDirection.INCREASING
        else:
            return TrendDirection.DECREASING
    
    def _calculate_confidence(self, r_squared: float, p_value: float, data_points: int) -> float:
        """Calculate confidence level for the trend"""
        # Base confidence on R-squared
        base_confidence = min(r_squared * 100, 95.0)
        
        # Adjust for statistical significance
        if p_value < 0.01:
            significance_bonus = 10.0
        elif p_value < 0.05:
            significance_bonus = 5.0
        else:
            significance_bonus = 0.0
        
        # Adjust for sample size
        if data_points >= self.optimal_data_points:
            sample_bonus = 5.0
        elif data_points >= self.min_data_points:
            sample_bonus = 2.0
        else:
            sample_bonus = 0.0
        
        confidence = base_confidence + significance_bonus + sample_bonus
        return min(confidence, 100.0)
    
    def _determine_significance(self, p_value: float) -> str:
        """Determine statistical significance"""
        if p_value < self.significance_thresholds["high"]:
            return "high"
        elif p_value < self.significance_thresholds["medium"]:
            return "medium"
        elif p_value < self.significance_thresholds["low"]:
            return "low"
        else:
            return "none"
    
    def _generate_trend_description(self, metric_type: MetricType, direction: TrendDirection, slope: float, r_squared: float, significance: str) -> str:
        """Generate human-readable trend description"""
        metric_name = metric_type.value.replace("_", " ").title()
        
        if direction == TrendDirection.STABLE:
            return f"{metric_name} shows a stable trend with no significant change over time."
        elif direction == TrendDirection.FLUCTUATING:
            return f"{metric_name} shows fluctuating values with no clear trend pattern."
        else:
            trend_word = "increasing" if direction == TrendDirection.INCREASING else "decreasing"
            significance_word = "strong" if significance == "high" else "moderate" if significance == "medium" else "weak"
            
            return f"{metric_name} shows a {significance_word} {trend_word} trend (R² = {r_squared:.2f})."
    
    def _trend_to_dict(self, trend: TrendAnalysis) -> Dict[str, Any]:
        """Convert TrendAnalysis to dictionary"""
        return {
            "metric_type": trend.metric_type.value,
            "direction": trend.direction.value,
            "slope": trend.slope,
            "r_squared": trend.r_squared,
            "p_value": trend.p_value,
            "confidence": trend.confidence,
            "data_points": trend.data_points,
            "time_period_days": trend.time_period_days,
            "description": trend.description,
            "significance": trend.significance
        }
    
    def _generate_trend_insights(self, trends: List[TrendAnalysis]) -> List[str]:
        """Generate insights from trend analysis"""
        insights = []
        
        if not trends:
            insights.append("No significant trends detected in the analyzed time period.")
            return insights
        
        # Count trends by direction
        direction_counts = {}
        for trend in trends:
            direction = trend.direction.value
            if direction not in direction_counts:
                direction_counts[direction] = 0
            direction_counts[direction] += 1
        
        # Generate insights
        for direction, count in direction_counts.items():
            if count == 1:
                insights.append(f"Found 1 {direction} trend in your health metrics.")
            else:
                insights.append(f"Found {count} {direction} trends in your health metrics.")
        
        # High significance trends
        high_significance = [t for t in trends if t.significance == "high"]
        if high_significance:
            insights.append(f"Detected {len(high_significance)} highly significant trends requiring attention.")
        
        # Concerning trends
        concerning_trends = self._identify_concerning_trends(trends)
        if concerning_trends:
            insights.append(f"Identified {len(concerning_trends)} concerning trends that may require intervention.")
        
        return insights
    
    def _identify_concerning_trends(self, trends: List[TrendAnalysis]) -> List[TrendAnalysis]:
        """Identify trends that may be concerning"""
        concerning = []
        
        for trend in trends:
            if trend.significance == "high":
                # Check for concerning patterns
                if (trend.metric_type in [MetricType.BLOOD_PRESSURE_SYSTOLIC, MetricType.BLOOD_PRESSURE_DIASTOLIC] and 
                    trend.direction == TrendDirection.INCREASING):
                    concerning.append(trend)
                elif (trend.metric_type == MetricType.HEART_RATE and 
                      trend.direction == TrendDirection.INCREASING):
                    concerning.append(trend)
                elif (trend.metric_type == MetricType.BLOOD_GLUCOSE and 
                      trend.direction == TrendDirection.INCREASING):
                    concerning.append(trend)
                elif (trend.metric_type == MetricType.OXYGEN_SATURATION and 
                      trend.direction == TrendDirection.DECREASING):
                    concerning.append(trend)
        
        return concerning
    
    def _generate_predictions(self, trends: List[TrendAnalysis]) -> List[str]:
        """Generate predictions based on trends"""
        predictions = []
        
        for trend in trends:
            if trend.significance in ["high", "medium"]:
                metric_name = trend.metric_type.value.replace("_", " ").title()
                direction = trend.direction.value
                
                if trend.direction in [TrendDirection.INCREASING, TrendDirection.DECREASING]:
                    predictions.append(f"Based on current trends, {metric_name} is likely to continue {direction}.")
        
        return predictions
    
    def _generate_trend_recommendations(self, trends: List[TrendAnalysis]) -> List[str]:
        """Generate recommendations based on trends"""
        recommendations = []
        
        if not trends:
            recommendations.append("Continue monitoring your health metrics to establish baseline patterns.")
            return recommendations
        
        # Analyze concerning trends
        concerning_trends = self._identify_concerning_trends(trends)
        
        for trend in concerning_trends:
            if trend.metric_type in [MetricType.BLOOD_PRESSURE_SYSTOLIC, MetricType.BLOOD_PRESSURE_DIASTOLIC]:
                recommendations.append("Consider lifestyle modifications to manage blood pressure trends.")
            elif trend.metric_type == MetricType.HEART_RATE:
                recommendations.append("Focus on stress management and cardiovascular health.")
            elif trend.metric_type == MetricType.BLOOD_GLUCOSE:
                recommendations.append("Review diet and medication management with your healthcare provider.")
            elif trend.metric_type == MetricType.OXYGEN_SATURATION:
                recommendations.append("Consult with your healthcare provider about respiratory health.")
        
        # General recommendations
        if len(concerning_trends) > 2:
            recommendations.append("Multiple concerning trends detected. Consider scheduling a comprehensive health review.")
        
        # Positive trends
        positive_trends = [t for t in trends if t.direction == TrendDirection.DECREASING and 
                          t.metric_type in [MetricType.BLOOD_PRESSURE_SYSTOLIC, MetricType.BLOOD_PRESSURE_DIASTOLIC, MetricType.WEIGHT]]
        
        if positive_trends:
            recommendations.append("Continue your current health practices as they're showing positive results.")
        
        return recommendations 