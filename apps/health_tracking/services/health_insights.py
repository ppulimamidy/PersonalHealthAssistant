"""
Health Insights Service
Provides AI-powered health insights and recommendations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from ..models.health_metrics import HealthMetric, MetricType
from ..models.health_goals import HealthGoal, GoalStatus
from ..models.health_insights import (
    HealthInsight, InsightType, InsightSeverity, InsightStatus, INSIGHT_TEMPLATES
)

logger = get_logger(__name__)

class HealthInsightsService:
    """Service for generating health insights"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def initialize(self):
        """Initialize the insights service"""
        logger.info("Initializing Health Insights Service")
        self.cache.clear()
    
    async def cleanup(self):
        """Cleanup the insights service"""
        logger.info("Cleaning up Health Insights Service")
        self.cache.clear()
    
    @with_resilience("health_insights", max_concurrent=10, timeout=60.0, max_retries=3)
    async def generate_insights_for_metric(
        self,
        metric: HealthMetric,
        db: AsyncSession
    ) -> List[HealthInsight]:
        """Generate insights for a new metric"""
        try:
            insights = []
            
            # Get recent metrics for trend analysis
            recent_metrics = await self._get_recent_metrics(
                user_id=metric.user_id,
                metric_type=metric.metric_type,
                days=30,
                db=db
            )
            
            # Generate trend insights
            trend_insights = await self._generate_trend_insights(metric, recent_metrics)
            insights.extend(trend_insights)
            
            # Generate goal-related insights
            goal_insights = await self._generate_goal_insights(metric, db)
            insights.extend(goal_insights)
            
            # Generate health alert insights
            alert_insights = await self._generate_health_alert_insights(metric)
            insights.extend(alert_insights)
            
            # Generate pattern insights
            pattern_insights = await self._generate_pattern_insights(metric, recent_metrics)
            insights.extend(pattern_insights)
            
            # Save insights to database
            for insight in insights:
                db.add(insight)
            
            await db.commit()
            
            logger.info(f"Generated {len(insights)} insights for metric {metric.id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for metric: {e}")
            await db.rollback()
            raise
    
    @with_resilience("health_insights", max_concurrent=10, timeout=60.0, max_retries=3)
    async def generate_recommendations(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Generate personalized health recommendations"""
        try:
            recommendations = []
            
            # Get user's recent metrics
            recent_metrics = await self._get_recent_metrics(
                user_id=user_id,
                days=7,
                db=db
            )
            
            # Get user's active goals
            goals = await self._get_active_goals(user_id, db)
            
            # Generate recommendations based on metrics
            metric_recommendations = await self._generate_metric_recommendations(recent_metrics)
            recommendations.extend(metric_recommendations)
            
            # Generate goal-based recommendations
            goal_recommendations = await self._generate_goal_recommendations(goals, recent_metrics)
            recommendations.extend(goal_recommendations)
            
            # Generate lifestyle recommendations
            lifestyle_recommendations = await self._generate_lifestyle_recommendations(recent_metrics)
            recommendations.extend(lifestyle_recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
    
    @with_resilience("health_insights", max_concurrent=10, timeout=60.0, max_retries=3)
    async def generate_daily_insights(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> List[HealthInsight]:
        """Generate daily insights for a user"""
        try:
            insights = []
            
            # Get yesterday's metrics
            yesterday = datetime.utcnow() - timedelta(days=1)
            yesterday_metrics = await self._get_metrics_for_date(user_id, yesterday, db)
            
            # Generate daily summary insights
            summary_insights = await self._generate_daily_summary_insights(yesterday_metrics)
            insights.extend(summary_insights)
            
            # Generate goal progress insights
            goal_insights = await self._generate_daily_goal_insights(user_id, yesterday, db)
            insights.extend(goal_insights)
            
            # Generate trend insights
            trend_insights = await self._generate_daily_trend_insights(user_id, yesterday, db)
            insights.extend(trend_insights)
            
            # Save insights
            for insight in insights:
                db.add(insight)
            
            await db.commit()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating daily insights: {e}")
            await db.rollback()
            raise
    
    async def _get_recent_metrics(
        self,
        user_id: UUID,
        metric_type: Optional[MetricType] = None,
        days: int = 30,
        db: AsyncSession = None
    ) -> List[HealthMetric]:
        """Get recent metrics for a user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.timestamp >= start_date
            )
        )
        
        if metric_type:
            query = query.where(HealthMetric.metric_type == metric_type)
        
        query = query.order_by(HealthMetric.timestamp)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _get_active_goals(self, user_id: UUID, db: AsyncSession) -> List[HealthGoal]:
        """Get active goals for a user"""
        query = select(HealthGoal).where(
            and_(
                HealthGoal.user_id == user_id,
                HealthGoal.status == GoalStatus.ACTIVE
            )
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _get_metrics_for_date(
        self,
        user_id: UUID,
        date: datetime,
        db: AsyncSession
    ) -> List[HealthMetric]:
        """Get metrics for a specific date"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.timestamp >= start_of_day,
                HealthMetric.timestamp < end_of_day
            )
        ).order_by(HealthMetric.timestamp)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _generate_trend_insights(
        self,
        metric: HealthMetric,
        recent_metrics: List[HealthMetric]
    ) -> List[HealthInsight]:
        """Generate trend-based insights"""
        insights = []
        
        if len(recent_metrics) < 3:
            return insights
        
        # Calculate trend
        values = [m.value for m in recent_metrics[-5:]]  # Last 5 data points
        if len(values) < 2:
            return insights
        
        # Simple trend calculation
        first_value = values[0]
        last_value = values[-1]
        change = last_value - first_value
        change_percent = (change / first_value * 100) if first_value != 0 else 0
        
        # Determine trend direction
        if abs(change_percent) < 5:  # Less than 5% change
            trend = "stable"
        elif change_percent > 5:
            trend = "up"
        else:
            trend = "down"
        
        # Generate insight based on metric type and trend
        insight_data = self._get_trend_insight_data(metric.metric_type, trend, change, change_percent)
        
        if insight_data:
            insight = HealthInsight(
                id=uuid4(),
                user_id=metric.user_id,
                insight_type=insight_data["insight_type"],
                title=insight_data["title"],
                description=insight_data["description"],
                severity=insight_data["severity"],
                confidence=0.8,  # High confidence for trend insights
                related_metrics=[str(metric.id)],
                metadata={
                    "trend": trend,
                    "change": change,
                    "change_percent": change_percent,
                    "metric_type": metric.metric_type
                }
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_goal_insights(
        self,
        metric: HealthMetric,
        db: AsyncSession
    ) -> List[HealthInsight]:
        """Generate goal-related insights"""
        insights = []
        
        # Get goals related to this metric type
        goals_query = select(HealthGoal).where(
            and_(
                HealthGoal.user_id == metric.user_id,
                HealthGoal.metric_type == metric.metric_type,
                HealthGoal.status == GoalStatus.ACTIVE
            )
        )
        
        result = await db.execute(goals_query)
        goals = result.scalars().all()
        
        for goal in goals:
            # Update goal with current value
            goal.current_value = metric.value
            goal.progress = goal.calculate_progress()
            
            # Generate insight based on goal progress
            if goal.is_completed():
                insight_data = {
                    "insight_type": InsightType.GOAL_COMPLETED,
                    "title": f"Goal Achieved: {goal.title}",
                    "description": f"Congratulations! You've successfully achieved your goal of {goal.title}.",
                    "severity": InsightSeverity.LOW
                }
            elif goal.progress >= 80:
                insight_data = {
                    "insight_type": InsightType.GOAL_PROGRESS,
                    "title": f"Almost There: {goal.title}",
                    "description": f"You're {goal.progress:.1f}% of the way to your goal. Keep up the great work!",
                    "severity": InsightSeverity.LOW
                }
            elif goal.is_overdue():
                insight_data = {
                    "insight_type": InsightType.GOAL_AT_RISK,
                    "title": f"Goal at Risk: {goal.title}",
                    "description": f"Your goal '{goal.title}' is overdue. Consider reviewing your strategy.",
                    "severity": InsightSeverity.MEDIUM
                }
            else:
                continue
            
            insight = HealthInsight(
                id=uuid4(),
                user_id=metric.user_id,
                insight_type=insight_data["insight_type"],
                title=insight_data["title"],
                description=insight_data["description"],
                severity=insight_data["severity"],
                confidence=0.9,
                related_metrics=[str(metric.id)],
                related_goals=[str(goal.id)],
                metadata={
                    "goal_progress": goal.progress,
                    "goal_id": str(goal.id)
                }
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_health_alert_insights(self, metric: HealthMetric) -> List[HealthInsight]:
        """Generate health alert insights"""
        insights = []
        
        # Define health ranges for different metrics
        health_ranges = {
            MetricType.HEART_RATE: {"min": 60, "max": 100, "unit": "bpm"},
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {"min": 90, "max": 140, "unit": "mmHg"},
            MetricType.BLOOD_PRESSURE_DIASTOLIC: {"min": 60, "max": 90, "unit": "mmHg"},
            MetricType.TEMPERATURE: {"min": 36.1, "max": 37.2, "unit": "°C"},
            MetricType.OXYGEN_SATURATION: {"min": 95, "max": 100, "unit": "%"},
            MetricType.GLUCOSE: {"min": 70, "max": 140, "unit": "mg/dL"}
        }
        
        if metric.metric_type in health_ranges:
            range_config = health_ranges[metric.metric_type]
            
            if metric.value < range_config["min"] or metric.value > range_config["max"]:
                insight = HealthInsight(
                    id=uuid4(),
                    user_id=metric.user_id,
                    insight_type=InsightType.HEALTH_ALERT,
                    title=f"Health Alert: {metric.metric_type.replace('_', ' ').title()}",
                    description=f"Your {metric.metric_type.replace('_', ' ')} reading of {metric.value} {range_config['unit']} is outside the normal range ({range_config['min']}-{range_config['max']} {range_config['unit']}). Consider consulting with a healthcare provider.",
                    severity=InsightSeverity.HIGH,
                    confidence=0.95,
                    related_metrics=[str(metric.id)],
                    metadata={
                        "metric_value": metric.value,
                        "normal_range": f"{range_config['min']}-{range_config['max']}",
                        "unit": range_config["unit"]
                    }
                )
                insights.append(insight)
        
        return insights
    
    async def _generate_pattern_insights(
        self,
        metric: HealthMetric,
        recent_metrics: List[HealthMetric]
    ) -> List[HealthInsight]:
        """Generate pattern-based insights"""
        insights = []
        
        if len(recent_metrics) < 7:  # Need at least a week of data
            return insights
        
        # Check for anomalies
        values = [m.value for m in recent_metrics]
        mean_value = sum(values) / len(values)
        std_dev = (sum((x - mean_value) ** 2 for x in values) / len(values)) ** 0.5
        
        if std_dev > 0:
            z_score = abs(metric.value - mean_value) / std_dev
            
            if z_score > 2:  # More than 2 standard deviations from mean
                insight = HealthInsight(
                    id=uuid4(),
                    user_id=metric.user_id,
                    insight_type=InsightType.ANOMALY_DETECTED,
                    title=f"Unusual {metric.metric_type.replace('_', ' ').title()} Reading",
                    description=f"Your {metric.metric_type.replace('_', ' ')} reading of {metric.value} {metric.unit} is unusual compared to your typical pattern. This could be due to various factors including stress, diet, or activity changes.",
                    severity=InsightSeverity.MEDIUM,
                    confidence=0.7,
                    related_metrics=[str(metric.id)],
                    metadata={
                        "z_score": z_score,
                        "mean_value": mean_value,
                        "std_dev": std_dev
                    }
                )
                insights.append(insight)
        
        return insights
    
    async def _generate_metric_recommendations(
        self,
        metrics: List[HealthMetric]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # Generate recommendations for each metric type
        for metric_type, type_metrics in metrics_by_type.items():
            if len(type_metrics) < 2:
                continue
            
            latest_metric = type_metrics[-1]
            recommendation = self._get_metric_recommendation(metric_type, latest_metric, type_metrics)
            
            if recommendation:
                recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_goal_recommendations(
        self,
        goals: List[HealthGoal],
        metrics: List[HealthMetric]
    ) -> List[Dict[str, Any]]:
        """Generate goal-based recommendations"""
        recommendations = []
        
        for goal in goals:
            if goal.is_overdue():
                recommendation = {
                    "type": "goal_reminder",
                    "title": f"Goal Reminder: {goal.title}",
                    "description": f"Your goal '{goal.title}' is overdue. Consider reviewing your progress and adjusting your strategy.",
                    "priority": "medium",
                    "goal_id": str(goal.id)
                }
                recommendations.append(recommendation)
            elif goal.progress and goal.progress < 50:
                recommendation = {
                    "type": "goal_encouragement",
                    "title": f"Goal Progress: {goal.title}",
                    "description": f"You're {goal.progress:.1f}% of the way to your goal. Consider what adjustments might help you make more progress.",
                    "priority": "low",
                    "goal_id": str(goal.id)
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_lifestyle_recommendations(
        self,
        metrics: List[HealthMetric]
    ) -> List[Dict[str, Any]]:
        """Generate lifestyle recommendations"""
        recommendations = []
        
        # Check activity levels
        activity_metrics = [m for m in metrics if m.metric_type == MetricType.STEPS]
        if activity_metrics:
            avg_steps = sum(m.value for m in activity_metrics) / len(activity_metrics)
            if avg_steps < 8000:
                recommendations.append({
                    "type": "activity_recommendation",
                    "title": "Increase Daily Activity",
                    "description": f"Your average daily steps ({avg_steps:.0f}) are below the recommended 8,000-10,000 steps. Try taking short walks throughout the day.",
                    "priority": "medium"
                })
        
        # Check sleep patterns
        sleep_metrics = [m for m in metrics if m.metric_type == MetricType.SLEEP_DURATION]
        if sleep_metrics:
            avg_sleep = sum(m.value for m in sleep_metrics) / len(sleep_metrics)
            if avg_sleep < 7:
                recommendations.append({
                    "type": "sleep_recommendation",
                    "title": "Improve Sleep Duration",
                    "description": f"Your average sleep duration ({avg_sleep:.1f} hours) is below the recommended 7-9 hours. Consider improving your sleep hygiene.",
                    "priority": "medium"
                })
        
        return recommendations
    
    async def _generate_daily_summary_insights(
        self,
        daily_metrics: List[HealthMetric]
    ) -> List[HealthInsight]:
        """Generate daily summary insights"""
        insights = []
        
        if not daily_metrics:
            return insights
        
        # Count metrics by type
        metrics_by_type = {}
        for metric in daily_metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # Generate summary insight
        summary_text = f"You tracked {len(daily_metrics)} health metrics across {len(metrics_by_type)} categories yesterday."
        
        insight = HealthInsight(
            id=uuid4(),
            user_id=daily_metrics[0].user_id,
            insight_type=InsightType.HEALTH_RECOMMENDATION,
            title="Daily Health Summary",
            description=summary_text,
            severity=InsightSeverity.LOW,
            confidence=1.0,
            related_metrics=[str(m.id) for m in daily_metrics]
        )
        insights.append(insight)
        
        return insights
    
    async def _generate_daily_goal_insights(
        self,
        user_id: UUID,
        date: datetime,
        db: AsyncSession
    ) -> List[HealthInsight]:
        """Generate daily goal insights"""
        # This would check goal progress for the day
        # Implementation depends on specific goal tracking logic
        return []
    
    async def _generate_daily_trend_insights(
        self,
        user_id: UUID,
        date: datetime,
        db: AsyncSession
    ) -> List[HealthInsight]:
        """Generate daily trend insights"""
        # This would analyze trends over the past week
        # Implementation depends on specific trend analysis logic
        return []
    
    def _get_trend_insight_data(
        self,
        metric_type: str,
        trend: str,
        change: float,
        change_percent: float
    ) -> Optional[Dict[str, Any]]:
        """Get insight data for a trend"""
        if metric_type == MetricType.WEIGHT:
            if trend == "up":
                return {
                    "insight_type": InsightType.TREND_UP,
                    "title": "Weight Trending Upward",
                    "description": f"Your weight has increased by {abs(change):.1f} kg ({abs(change_percent):.1f}%) recently. Consider reviewing your nutrition and activity levels.",
                    "severity": InsightSeverity.MEDIUM
                }
            elif trend == "down":
                return {
                    "insight_type": InsightType.TREND_DOWN,
                    "title": "Weight Trending Downward",
                    "description": f"Great progress! Your weight has decreased by {abs(change):.1f} kg ({abs(change_percent):.1f}%) recently. Keep up the healthy habits!",
                    "severity": InsightSeverity.LOW
                }
        
        elif metric_type == MetricType.HEART_RATE:
            if trend == "up":
                return {
                    "insight_type": InsightType.HEALTH_ALERT,
                    "title": "Heart Rate Elevated",
                    "description": f"Your heart rate has increased by {abs(change_percent):.1f}% recently. Consider stress management techniques.",
                    "severity": InsightSeverity.HIGH
                }
        
        elif metric_type == MetricType.STEPS:
            if trend == "down":
                return {
                    "insight_type": InsightType.ACTIVITY_RECOMMENDATION,
                    "title": "Activity Level Decreasing",
                    "description": f"Your daily step count has decreased by {abs(change_percent):.1f}%. Try to increase your daily activity.",
                    "severity": InsightSeverity.MEDIUM
                }
        
        return None
    
    def _get_metric_recommendation(
        self,
        metric_type: str,
        latest_metric: HealthMetric,
        all_metrics: List[HealthMetric]
    ) -> Optional[Dict[str, Any]]:
        """Get recommendation for a specific metric"""
        # This would contain logic for generating specific recommendations
        # based on metric type and values
        return None 