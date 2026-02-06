"""
Goal Suggester Agent
Autonomous agent for suggesting personalized health goals based on user data.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseHealthAgent, AgentResult
from ..models.health_metrics import HealthMetric, MetricType
from ..models.health_goals import HealthGoal, GoalStatus
from ..models.vital_signs import VitalSigns, VitalSignType
from common.utils.logging import get_logger

logger = get_logger(__name__)

class GoalSuggesterAgent(BaseHealthAgent):
    """
    Autonomous agent for suggesting personalized health goals.
    Analyzes user's health data and current goals to suggest new objectives.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="goal_suggester",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Goal suggestion rules and thresholds
        self.goal_rules = {
            MetricType.WEIGHT: {
                "overweight_threshold": 25.0,  # BMI
                "underweight_threshold": 18.5,
                "suggest_weight_loss": True,
                "suggest_weight_gain": True
            },
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {
                "high_threshold": 140,
                "very_high_threshold": 160,
                "suggest_reduction": True
            },
            MetricType.HEART_RATE: {
                "high_threshold": 100,
                "low_threshold": 60,
                "suggest_optimization": True
            },
            MetricType.GLUCOSE: {
                "high_threshold": 140,
                "very_high_threshold": 200,
                "suggest_management": True
            },
            MetricType.TEMPERATURE: {
                "normal_range": (36.5, 37.5),
                "suggest_monitoring": True
            }
        }
        
        # Define target ranges for different metrics
        self.target_ranges = {
            MetricType.WEIGHT: {"high": 80, "low": 60},
            MetricType.HEART_RATE: {"high": 100, "low": 60},
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {"high": 140, "low": 90},
            MetricType.BLOOD_PRESSURE_DIASTOLIC: {"high": 90, "low": 60},
            MetricType.TEMPERATURE: {
                "high": 37.5, "low": 36.5
            },
            MetricType.OXYGEN_SATURATION: {"high": 100, "low": 95},
            MetricType.STEPS: {"high": 10000, "low": 8000},
            MetricType.SLEEP_DURATION: {"high": 9, "low": 7},
            MetricType.BLOOD_GLUCOSE: {"high": 140, "low": 70},
        }
        
        # Define target ranges for vital signs
        self.vital_sign_targets = {
            VitalSignType.BLOOD_PRESSURE: {"systolic_high": 140, "systolic_low": 90, "diastolic_high": 90, "diastolic_low": 60},
            VitalSignType.HEART_RATE: {"high": 100, "low": 60},
            VitalSignType.BODY_TEMPERATURE: {"high": 37.5, "low": 36.5},
            VitalSignType.OXYGEN_SATURATION: {"high": 100, "low": 95},
            VitalSignType.RESPIRATORY_RATE: {"high": 20, "low": 12},
            VitalSignType.BLOOD_GLUCOSE: {"high": 140, "low": 70},
            VitalSignType.WEIGHT: {"high": 80, "low": 60},
            VitalSignType.BODY_MASS_INDEX: {"high": 25, "low": 18.5},
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process health data to suggest personalized goals.
        
        Args:
            data: Dictionary containing user_id and optional parameters
            db: Database session
            
        Returns:
            AgentResult with suggested goals
        """
        user_id = data.get("user_id")
        goal_focus = data.get("goal_focus")  # Specific area to focus on
        goal_difficulty = data.get("goal_difficulty", "moderate")  # easy, moderate, challenging
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Analyze current health data
            health_analysis = await self._analyze_health_data(user_id, db)
            
            # Get current goals
            current_goals = await self._get_current_goals(user_id, db)
            
            # Generate goal suggestions
            suggestions = await self._generate_goal_suggestions(
                health_analysis, current_goals, goal_focus, goal_difficulty
            )
            
            # Generate insights and recommendations
            insights = self._generate_insights(health_analysis, suggestions)
            recommendations = self._generate_recommendations(suggestions, goal_difficulty)
            
            return AgentResult(
                success=True,
                data={
                    "suggestions": suggestions,
                    "health_analysis": health_analysis,
                    "current_goals_count": len(current_goals),
                    "suggestions_count": len(suggestions)
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Goal suggestion failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Goal suggestion failed: {str(e)}"
            )
    
    async def _analyze_health_data(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Analyze user's health data to identify areas for improvement"""
        analysis = {}
        
        # Get recent metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Analyze different metric types
        for metric_type in MetricType:
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.created_at >= thirty_days_ago
                )
            ).order_by(desc(HealthMetric.created_at))
            
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            if metrics:
                values = [m.value for m in metrics]
                analysis[metric_type.value] = {
                    "count": len(values),
                    "latest": values[0] if values else None,
                    "average": sum(values) / len(values) if values else None,
                    "min": min(values) if values else None,
                    "max": max(values) if values else None,
                    "trend": self._calculate_trend(values),
                    "needs_improvement": self._assess_improvement_needed(metric_type, values)
                }
        
        # Analyze vital signs
        for vital_type in VitalSignType:
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.user_id == user_id,
                    VitalSigns.vital_sign_type == vital_type.value,
                    VitalSigns.created_at >= thirty_days_ago
                )
            ).order_by(desc(VitalSigns.created_at))
            
            result = await db.execute(query)
            vital_signs = result.scalars().all()
            
            if vital_signs:
                values = [self._get_vital_sign_value(vs, vital_type.value) for vs in vital_signs]
                values = [v for v in values if v is not None]
                
                if values:
                    analysis[vital_type.value] = {
                        "count": len(values),
                        "latest": values[0] if values else None,
                        "average": sum(values) / len(values) if values else None,
                        "min": min(values) if values else None,
                        "max": max(values) if values else None,
                        "trend": self._calculate_trend(values),
                        "needs_improvement": self._assess_vital_improvement_needed(vital_type, values)
                    }
        
        return analysis
    
    async def _get_current_goals(self, user_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get user's current active goals"""
        query = select(HealthGoal).where(
            and_(
                HealthGoal.user_id == user_id,
                HealthGoal.status.in_([GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS])
            )
        ).order_by(desc(HealthGoal.created_at))
        
        result = await db.execute(query)
        goals = result.scalars().all()
        
        return [goal.to_dict() for goal in goals]
    
    async def _generate_goal_suggestions(
        self, 
        health_analysis: Dict[str, Any], 
        current_goals: List[Dict[str, Any]], 
        goal_focus: Optional[str],
        goal_difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate personalized goal suggestions"""
        suggestions = []
        
        # Define goal templates based on difficulty
        goal_templates = self._get_goal_templates(goal_difficulty)
        
        # Check each health metric for improvement opportunities
        for metric_type, analysis in health_analysis.items():
            if not analysis.get("needs_improvement"):
                continue
            
            # Skip if user already has a goal for this metric
            if self._has_existing_goal(current_goals, metric_type):
                continue
            
            # Generate suggestions based on metric type
            metric_suggestions = self._generate_metric_goals(
                metric_type, analysis, goal_templates, goal_focus
            )
            suggestions.extend(metric_suggestions)
        
        # Add general wellness goals if no specific focus
        if not goal_focus and len(suggestions) < 3:
            general_goals = self._generate_general_goals(goal_templates, goal_difficulty)
            suggestions.extend(general_goals)
        
        # Limit suggestions to top 5
        return suggestions[:5]
    
    def _get_goal_templates(self, difficulty: str) -> Dict[str, Any]:
        """Get goal templates based on difficulty level"""
        templates = {
            "easy": {
                "duration_weeks": 2,
                "frequency": "daily",
                "intensity": "light",
                "description_modifier": "start with"
            },
            "moderate": {
                "duration_weeks": 4,
                "frequency": "3-4 times per week",
                "intensity": "moderate",
                "description_modifier": "work towards"
            },
            "challenging": {
                "duration_weeks": 8,
                "frequency": "5-6 times per week",
                "intensity": "intense",
                "description_modifier": "achieve"
            }
        }
        
        return templates.get(difficulty, templates["moderate"])
    
    def _generate_metric_goals(
        self, 
        metric_type: str, 
        analysis: Dict[str, Any], 
        templates: Dict[str, Any],
        goal_focus: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate goals for a specific metric type"""
        suggestions = []
        
        if metric_type == MetricType.WEIGHT.value:
            latest = analysis.get("latest")
            if latest and latest > 80:  # Assuming kg
                suggestions.append({
                    "title": f"Weight Management Goal",
                    "description": f"{templates['description_modifier']} maintaining a healthy weight",
                    "metric_type": MetricType.WEIGHT,
                    "goal_type": "maintenance",
                    "target_value": latest * 0.95,  # 5% reduction
                    "unit": "kg",
                    "duration_weeks": templates["duration_weeks"],
                    "frequency": templates["frequency"],
                    "difficulty": templates["intensity"],
                    "priority": "high" if goal_focus == "weight" else "medium"
                })
        
        elif metric_type == MetricType.BLOOD_PRESSURE_SYSTOLIC.value:
            latest = analysis.get("latest")
            if latest and latest > 140:
                suggestions.append({
                    "title": "Blood Pressure Management",
                    "description": f"{templates['description_modifier']} healthy blood pressure levels",
                    "metric_type": MetricType.BLOOD_PRESSURE_SYSTOLIC,
                    "goal_type": "reduction",
                    "target_value": 130,
                    "unit": "mmHg",
                    "duration_weeks": templates["duration_weeks"],
                    "frequency": "daily monitoring",
                    "difficulty": templates["intensity"],
                    "priority": "high" if goal_focus == "cardiovascular" else "medium"
                })
        
        elif metric_type == MetricType.HEART_RATE.value:
            latest = analysis.get("latest")
            if latest and latest > 100:
                suggestions.append({
                    "title": "Heart Rate Optimization",
                    "description": f"{templates['description_modifier']} a healthy resting heart rate",
                    "metric_type": MetricType.HEART_RATE,
                    "goal_type": "reduction",
                    "target_value": 80,
                    "unit": "bpm",
                    "duration_weeks": templates["duration_weeks"],
                    "frequency": templates["frequency"],
                    "difficulty": templates["intensity"],
                    "priority": "high" if goal_focus == "cardiovascular" else "medium"
                })
        
        elif metric_type == MetricType.GLUCOSE.value:
            latest = analysis.get("latest")
            if latest and latest > 140:
                suggestions.append({
                    "title": "Blood Glucose Management",
                    "description": f"{templates['description_modifier']} healthy blood glucose levels",
                    "metric_type": MetricType.GLUCOSE,
                    "goal_type": "maintenance",
                    "target_value": 120,
                    "unit": "mg/dL",
                    "duration_weeks": templates["duration_weeks"],
                    "frequency": "daily monitoring",
                    "difficulty": templates["intensity"],
                    "priority": "high" if goal_focus == "diabetes" else "medium"
                })
        
        return suggestions
    
    def _generate_general_goals(self, templates: Dict[str, Any], difficulty: str) -> List[Dict[str, Any]]:
        """Generate general wellness goals"""
        general_goals = [
            {
                "title": "Physical Activity",
                "description": f"{templates['description_modifier']} regular physical activity",
                "metric_type": MetricType.STEPS,
                "goal_type": "increase",
                "target_value": 8000 if difficulty == "easy" else 10000 if difficulty == "moderate" else 12000,
                "unit": "steps",
                "duration_weeks": templates["duration_weeks"],
                "frequency": templates["frequency"],
                "difficulty": templates["intensity"],
                "priority": "medium"
            },
            {
                "title": "Sleep Quality",
                "description": f"{templates['description_modifier']} better sleep habits",
                "metric_type": MetricType.SLEEP_DURATION,
                "goal_type": "increase",
                "target_value": 7.5,
                "unit": "hours",
                "duration_weeks": templates["duration_weeks"],
                "frequency": "daily",
                "difficulty": templates["intensity"],
                "priority": "medium"
            }
        ]
        
        return general_goals
    
    def _has_existing_goal(self, current_goals: List[Dict[str, Any]], metric_type: str) -> bool:
        """Check if user already has a goal for this metric type"""
        for goal in current_goals:
            if goal.get("metric_type") == metric_type:
                return True
        return False
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    def _assess_improvement_needed(self, metric_type: MetricType, values: List[float]) -> bool:
        """Assess if a metric needs improvement"""
        if not values:
            return False
        
        latest = values[0]
        
        # Define thresholds for different metrics
        thresholds = {
            MetricType.WEIGHT: {"high": 100, "low": 50},  # kg
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {"high": 140, "low": 90},
            MetricType.HEART_RATE: {"high": 100, "low": 60},
            MetricType.GLUCOSE: {"high": 140, "low": 70},
            MetricType.STEPS: {"low": 5000},  # Minimum steps
            MetricType.SLEEP_DURATION: {"low": 6, "high": 9}  # hours
        }
        
        threshold = thresholds.get(metric_type)
        if not threshold:
            return False
        
        if "high" in threshold and latest > threshold["high"]:
            return True
        if "low" in threshold and latest < threshold["low"]:
            return True
        
        return False
    
    def _assess_vital_improvement_needed(self, vital_type: VitalSignType, values: List[float]) -> bool:
        """Assess if vital signs need improvement"""
        if not values:
            return False
        
        latest = values[0]
        
        # Define thresholds for vital signs
        thresholds = {
            VitalSignType.BLOOD_PRESSURE_SYSTOLIC: {"high": 140, "low": 90},
            VitalSignType.HEART_RATE: {"high": 100, "low": 60},
            VitalSignType.GLUCOSE: {"high": 140, "low": 70},
            VitalSignType.OXYGEN_SATURATION: {"low": 95},
            VitalSignType.BODY_TEMPERATURE: {"high": 37.5, "low": 36.5}
        }
        
        threshold = thresholds.get(vital_type)
        if not threshold:
            return False
        
        if "high" in threshold and latest > threshold["high"]:
            return True
        if "low" in threshold and latest < threshold["low"]:
            return True
        
        return False
    
    def _get_vital_sign_value(self, vital_sign: VitalSigns, vital_type: str) -> Optional[float]:
        """Get the relevant value for a vital sign type"""
        value_mapping = {
            VitalSignType.BLOOD_PRESSURE_SYSTOLIC.value: vital_sign.systolic,
            VitalSignType.HEART_RATE.value: vital_sign.heart_rate,
            VitalSignType.BODY_TEMPERATURE.value: vital_sign.temperature,
            VitalSignType.OXYGEN_SATURATION.value: vital_sign.oxygen_saturation,
            VitalSignType.GLUCOSE.value: vital_sign.blood_glucose,
        }
        
        return value_mapping.get(vital_type)
    
    def _generate_insights(self, health_analysis: Dict[str, Any], suggestions: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from goal suggestions"""
        insights = []
        
        if not suggestions:
            insights.append("Your health metrics are within healthy ranges. Consider setting maintenance goals.")
            return insights
        
        # Count suggestions by priority
        high_priority = [s for s in suggestions if s.get("priority") == "high"]
        if high_priority:
            insights.append(f"Found {len(high_priority)} high-priority health areas that need attention.")
        
        # Identify most common goal types
        goal_types = [s.get("goal_type") for s in suggestions]
        if goal_types:
            most_common = max(set(goal_types), key=goal_types.count)
            insights.append(f"Most suggested goal type: {most_common} goals")
        
        # Check for cardiovascular focus
        cardio_goals = [s for s in suggestions if "cardiovascular" in s.get("title", "").lower()]
        if cardio_goals:
            insights.append("Cardiovascular health appears to be a key focus area.")
        
        return insights
    
    def _generate_recommendations(self, suggestions: List[Dict[str, Any]], difficulty: str) -> List[str]:
        """Generate recommendations based on goal suggestions"""
        recommendations = []
        
        if not suggestions:
            recommendations.append("Continue monitoring your health metrics to identify improvement opportunities.")
            return recommendations
        
        # General recommendations
        recommendations.append(f"Start with {len(suggestions)} focused goals to avoid overwhelming yourself.")
        
        if difficulty == "challenging":
            recommendations.append("Consider breaking down challenging goals into smaller, manageable steps.")
        elif difficulty == "easy":
            recommendations.append("These easy goals will help build healthy habits gradually.")
        
        # Specific recommendations based on goal types
        reduction_goals = [s for s in suggestions if s.get("goal_type") == "reduction"]
        if reduction_goals:
            recommendations.append("Focus on one reduction goal at a time for better success rates.")
        
        maintenance_goals = [s for s in suggestions if s.get("goal_type") == "maintenance"]
        if maintenance_goals:
            recommendations.append("Maintenance goals are great for sustaining healthy habits.")
        
        return recommendations 