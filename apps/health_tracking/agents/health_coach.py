"""
Health Coach Agent
Autonomous agent for providing personalized health coaching recommendations.
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

class HealthCoachAgent(BaseHealthAgent):
    """
    Autonomous agent for providing personalized health coaching.
    Analyzes user's health data and provides actionable coaching recommendations.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="health_coach",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 30
            }
        )
        
        # Coaching strategies and recommendations
        self.coaching_strategies = {
            "weight_management": {
                "nutrition": [
                    "Focus on whole foods and reduce processed foods",
                    "Practice portion control and mindful eating",
                    "Stay hydrated with water throughout the day",
                    "Include protein in every meal for satiety"
                ],
                "exercise": [
                    "Start with 30 minutes of moderate activity daily",
                    "Include both cardio and strength training",
                    "Find activities you enjoy to maintain consistency",
                    "Gradually increase intensity and duration"
                ],
                "lifestyle": [
                    "Get 7-9 hours of quality sleep each night",
                    "Manage stress through meditation or yoga",
                    "Keep a food diary to track eating patterns",
                    "Set realistic, achievable goals"
                ]
            },
            "cardiovascular_health": {
                "nutrition": [
                    "Reduce sodium intake to less than 2,300mg daily",
                    "Increase potassium-rich foods like bananas and spinach",
                    "Choose lean proteins and limit saturated fats",
                    "Include heart-healthy fats like olive oil and nuts"
                ],
                "exercise": [
                    "Aim for 150 minutes of moderate cardio weekly",
                    "Include interval training for heart health",
                    "Monitor heart rate during exercise",
                    "Start slowly and build endurance gradually"
                ],
                "lifestyle": [
                    "Quit smoking and avoid secondhand smoke",
                    "Limit alcohol consumption",
                    "Practice stress management techniques",
                    "Monitor blood pressure regularly"
                ]
            },
            "diabetes_management": {
                "nutrition": [
                    "Follow a consistent carbohydrate counting plan",
                    "Choose low glycemic index foods",
                    "Eat regular meals and snacks",
                    "Limit added sugars and refined carbohydrates"
                ],
                "exercise": [
                    "Exercise regularly to improve insulin sensitivity",
                    "Monitor blood glucose before and after exercise",
                    "Include both aerobic and resistance training",
                    "Stay active throughout the day"
                ],
                "lifestyle": [
                    "Monitor blood glucose as recommended",
                    "Take medications as prescribed",
                    "Regular foot care and eye exams",
                    "Maintain a healthy weight"
                ]
            },
            "general_wellness": {
                "nutrition": [
                    "Eat a balanced diet with plenty of fruits and vegetables",
                    "Stay hydrated with water and limit sugary drinks",
                    "Practice mindful eating and listen to hunger cues",
                    "Include a variety of nutrients in your diet"
                ],
                "exercise": [
                    "Find physical activities you enjoy",
                    "Set realistic fitness goals",
                    "Include flexibility and balance exercises",
                    "Make movement a part of your daily routine"
                ],
                "lifestyle": [
                    "Prioritize sleep and establish a bedtime routine",
                    "Practice stress management and relaxation techniques",
                    "Maintain social connections and relationships",
                    "Schedule regular health check-ups"
                ]
            }
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Process health data to provide coaching recommendations.
        
        Args:
            data: Dictionary containing user_id and optional parameters
            db: Database session
            
        Returns:
            AgentResult with coaching recommendations
        """
        user_id = data.get("user_id")
        coaching_focus = data.get("coaching_focus")  # Specific area to focus on
        coaching_level = data.get("coaching_level", "beginner")  # beginner, intermediate, advanced
        
        if not user_id:
            return AgentResult(
                success=False,
                error="user_id is required"
            )
        
        try:
            # Analyze user's health profile
            health_profile = await self._analyze_health_profile(user_id, db)
            
            # Get user's goals and progress
            goals_progress = await self._analyze_goals_progress(user_id, db)
            
            # Generate coaching recommendations
            coaching_plan = await self._generate_coaching_plan(
                health_profile, goals_progress, coaching_focus, coaching_level
            )
            
            # Generate insights and recommendations
            insights = self._generate_coaching_insights(health_profile, goals_progress)
            recommendations = self._generate_coaching_recommendations(coaching_plan, coaching_level)
            
            return AgentResult(
                success=True,
                data={
                    "coaching_plan": coaching_plan,
                    "health_profile": health_profile,
                    "goals_progress": goals_progress,
                    "coaching_level": coaching_level
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.90
            )
            
        except Exception as e:
            logger.error(f"Health coaching failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Health coaching failed: {str(e)}"
            )
    
    async def _analyze_health_profile(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Analyze user's overall health profile"""
        profile = {
            "health_score": 0,
            "risk_factors": [],
            "strengths": [],
            "areas_for_improvement": [],
            "metrics_summary": {},
            "trends": {}
        }
        
        # Get recent metrics (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Analyze different health areas
        health_areas = {
            "weight_management": [MetricType.WEIGHT, MetricType.BODY_MASS_INDEX],
            "cardiovascular": [MetricType.BLOOD_PRESSURE_SYSTOLIC, MetricType.HEART_RATE],
            "diabetes": [MetricType.BLOOD_GLUCOSE],
            "activity": [MetricType.STEPS, MetricType.EXERCISE_DURATION],
            "sleep": [MetricType.SLEEP_DURATION, MetricType.SLEEP_QUALITY]
        }
        
        total_score = 0
        area_count = 0
        
        for area, metric_types in health_areas.items():
            area_score = 0
            area_metrics = 0
            
            for metric_type in metric_types:
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
                    latest = values[0]
                    
                    # Score the metric based on health ranges
                    metric_score = self._score_metric(metric_type, latest)
                    area_score += metric_score
                    area_metrics += 1
                    
                    profile["metrics_summary"][metric_type.value] = {
                        "latest": latest,
                        "average": sum(values) / len(values),
                        "trend": self._calculate_trend(values),
                        "score": metric_score
                    }
            
            if area_metrics > 0:
                area_average = area_score / area_metrics
                profile["trends"][area] = area_average
                total_score += area_average
                area_count += 1
                
                # Identify areas for improvement
                if area_average < 70:
                    profile["areas_for_improvement"].append(area)
                elif area_average > 85:
                    profile["strengths"].append(area)
        
        # Calculate overall health score
        if area_count > 0:
            profile["health_score"] = total_score / area_count
        
        # Identify risk factors
        profile["risk_factors"] = self._identify_risk_factors(profile["metrics_summary"])
        
        return profile
    
    async def _analyze_goals_progress(self, user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Analyze user's goals and progress"""
        query = select(HealthGoal).where(
            and_(
                HealthGoal.user_id == user_id,
                HealthGoal.status.in_([GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS, GoalStatus.COMPLETED])
            )
        ).order_by(desc(HealthGoal.created_at))
        
        result = await db.execute(query)
        goals = result.scalars().all()
        
        progress_analysis = {
            "total_goals": len(goals),
            "active_goals": len([g for g in goals if g.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]]),
            "completed_goals": len([g for g in goals if g.status == GoalStatus.COMPLETED]),
            "completion_rate": 0,
            "goal_categories": {},
            "recent_progress": []
        }
        
        if goals:
            completed = len([g for g in goals if g.status == GoalStatus.COMPLETED])
            progress_analysis["completion_rate"] = (completed / len(goals)) * 100
            
            # Analyze goal categories
            for goal in goals:
                category = goal.metric_type.value if goal.metric_type else "general"
                if category not in progress_analysis["goal_categories"]:
                    progress_analysis["goal_categories"][category] = {
                        "total": 0,
                        "completed": 0,
                        "in_progress": 0
                    }
                
                progress_analysis["goal_categories"][category]["total"] += 1
                if goal.status == GoalStatus.COMPLETED:
                    progress_analysis["goal_categories"][category]["completed"] += 1
                elif goal.status in [GoalStatus.ACTIVE, GoalStatus.IN_PROGRESS]:
                    progress_analysis["goal_categories"][category]["in_progress"] += 1
        
        return progress_analysis
    
    async def _generate_coaching_plan(
        self, 
        health_profile: Dict[str, Any], 
        goals_progress: Dict[str, Any],
        coaching_focus: Optional[str],
        coaching_level: str
    ) -> Dict[str, Any]:
        """Generate personalized coaching plan"""
        coaching_plan = {
            "focus_areas": [],
            "strategies": {},
            "weekly_plan": {},
            "milestones": [],
            "motivation_tips": []
        }
        
        # Determine focus areas
        if coaching_focus:
            focus_areas = [coaching_focus]
        else:
            # Prioritize areas for improvement
            focus_areas = health_profile.get("areas_for_improvement", [])
            if not focus_areas:
                focus_areas = ["general_wellness"]
        
        coaching_plan["focus_areas"] = focus_areas[:3]  # Limit to top 3 areas
        
        # Generate strategies for each focus area
        for area in coaching_plan["focus_areas"]:
            if area in self.coaching_strategies:
                strategies = self.coaching_strategies[area]
                coaching_plan["strategies"][area] = self._adapt_strategies(
                    strategies, coaching_level
                )
        
        # Create weekly plan
        coaching_plan["weekly_plan"] = self._create_weekly_plan(
            coaching_plan["focus_areas"], coaching_level
        )
        
        # Set milestones
        coaching_plan["milestones"] = self._set_milestones(
            health_profile, goals_progress, coaching_level
        )
        
        # Generate motivation tips
        coaching_plan["motivation_tips"] = self._generate_motivation_tips(
            health_profile, goals_progress, coaching_level
        )
        
        return coaching_plan
    
    def _score_metric(self, metric_type: MetricType, value: float) -> float:
        """Score a metric based on health ranges"""
        scoring_rules = {
            MetricType.WEIGHT: {
                "ranges": [(50, 80, 100), (80, 100, 80), (100, 150, 60), (150, 200, 40)]
            },
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {
                "ranges": [(90, 120, 100), (120, 140, 80), (140, 160, 60), (160, 200, 40)]
            },
            MetricType.HEART_RATE: {
                "ranges": [(60, 80, 100), (80, 100, 80), (100, 120, 60), (120, 200, 40)]
            },
            MetricType.BLOOD_GLUCOSE: {
                "ranges": [(70, 100, 100), (100, 140, 80), (140, 200, 60), (200, 300, 40)]
            },
            MetricType.STEPS: {
                "ranges": [(10000, 15000, 100), (8000, 10000, 80), (5000, 8000, 60), (0, 5000, 40)]
            },
            MetricType.SLEEP_DURATION: {
                "ranges": [(7, 9, 100), (6, 7, 80), (5, 6, 60), (0, 5, 40)]
            }
        }
        
        rule = scoring_rules.get(metric_type)
        if not rule:
            return 70  # Default score
        
        for min_val, max_val, score in rule["ranges"]:
            if min_val <= value <= max_val:
                return score
        
        return 40  # Default low score
    
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
            return "improving"
        elif change_percent < -5:
            return "declining"
        else:
            return "stable"
    
    def _identify_risk_factors(self, metrics_summary: Dict[str, Any]) -> List[str]:
        """Identify health risk factors from metrics"""
        risk_factors = []
        
        for metric_type, data in metrics_summary.items():
            latest = data.get("latest")
            if not latest:
                continue
            
            if metric_type == MetricType.BLOOD_PRESSURE_SYSTOLIC.value and latest > 140:
                risk_factors.append("High blood pressure")
            elif metric_type == MetricType.HEART_RATE.value and latest > 100:
                risk_factors.append("Elevated heart rate")
            elif metric_type == MetricType.BLOOD_GLUCOSE.value and latest > 140:
                risk_factors.append("Elevated blood glucose")
            elif metric_type == MetricType.WEIGHT.value and latest > 100:
                risk_factors.append("Overweight")
            elif metric_type == MetricType.STEPS.value and latest < 5000:
                risk_factors.append("Low physical activity")
            elif metric_type == MetricType.SLEEP_DURATION.value and latest < 6:
                risk_factors.append("Insufficient sleep")
        
        return risk_factors
    
    def _adapt_strategies(self, strategies: Dict[str, List[str]], level: str) -> Dict[str, List[str]]:
        """Adapt strategies based on coaching level"""
        adapted_strategies = {}
        
        for category, recommendations in strategies.items():
            if level == "beginner":
                # Start with 2-3 basic recommendations
                adapted_strategies[category] = recommendations[:3]
            elif level == "intermediate":
                # Include more detailed recommendations
                adapted_strategies[category] = recommendations[:5]
            else:  # advanced
                # Include all recommendations
                adapted_strategies[category] = recommendations
        
        return adapted_strategies
    
    def _create_weekly_plan(self, focus_areas: List[str], level: str) -> Dict[str, Any]:
        """Create a weekly coaching plan"""
        weekly_plan = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": []
        }
        
        # Distribute focus areas across the week
        for i, area in enumerate(focus_areas):
            day = list(weekly_plan.keys())[i % 7]
            
            if area == "weight_management":
                weekly_plan[day].append("Track food intake and plan meals")
                weekly_plan[day].append("30 minutes of physical activity")
            elif area == "cardiovascular_health":
                weekly_plan[day].append("Cardio exercise session")
                weekly_plan[day].append("Monitor blood pressure")
            elif area == "diabetes_management":
                weekly_plan[day].append("Blood glucose monitoring")
                weekly_plan[day].append("Meal planning for diabetes")
            else:  # general_wellness
                weekly_plan[day].append("Mindful movement or exercise")
                weekly_plan[day].append("Stress management practice")
        
        return weekly_plan
    
    def _set_milestones(self, health_profile: Dict[str, Any], goals_progress: Dict[str, Any], level: str) -> List[Dict[str, Any]]:
        """Set achievable milestones"""
        milestones = []
        
        health_score = health_profile.get("health_score", 0)
        
        # Set score-based milestones
        if health_score < 70:
            milestones.append({
                "description": "Improve overall health score to 75",
                "target": 75,
                "timeline": "4 weeks",
                "type": "health_score"
            })
        elif health_score < 85:
            milestones.append({
                "description": "Achieve excellent health score of 85+",
                "target": 85,
                "timeline": "6 weeks",
                "type": "health_score"
            })
        
        # Set goal-based milestones
        active_goals = goals_progress.get("active_goals", 0)
        if active_goals > 0:
            milestones.append({
                "description": f"Complete {min(2, active_goals)} active goals",
                "target": min(2, active_goals),
                "timeline": "8 weeks",
                "type": "goal_completion"
            })
        
        # Set habit-based milestones
        milestones.append({
            "description": "Establish consistent daily health tracking",
            "target": "7 days",
            "timeline": "2 weeks",
            "type": "habit_formation"
        })
        
        return milestones
    
    def _generate_motivation_tips(self, health_profile: Dict[str, Any], goals_progress: Dict[str, Any], level: str) -> List[str]:
        """Generate motivational tips"""
        tips = []
        
        health_score = health_profile.get("health_score", 0)
        completion_rate = goals_progress.get("completion_rate", 0)
        
        if health_score < 70:
            tips.append("Every small step counts! Focus on progress, not perfection.")
            tips.append("You're taking the first step toward better health - that's already a win!")
        elif health_score < 85:
            tips.append("You're doing great! Keep building on your healthy habits.")
            tips.append("Consistency is key - you're building a strong foundation.")
        else:
            tips.append("Excellent work! You're maintaining great health habits.")
            tips.append("Share your success - you might inspire others!")
        
        if completion_rate > 80:
            tips.append("Your goal completion rate is impressive! Keep up the great work.")
        elif completion_rate > 50:
            tips.append("You're making good progress on your goals. Stay focused!")
        else:
            tips.append("Remember: every goal started with a single step. You've got this!")
        
        tips.append("Celebrate your victories, no matter how small they seem.")
        tips.append("Health is a journey, not a destination. Enjoy the process!")
        
        return tips[:5]  # Limit to 5 tips
    
    def _generate_coaching_insights(self, health_profile: Dict[str, Any], goals_progress: Dict[str, Any]) -> List[str]:
        """Generate coaching insights"""
        insights = []
        
        health_score = health_profile.get("health_score", 0)
        risk_factors = health_profile.get("risk_factors", [])
        strengths = health_profile.get("strengths", [])
        areas_for_improvement = health_profile.get("areas_for_improvement", [])
        
        if health_score > 85:
            insights.append("Your overall health score is excellent! Focus on maintenance and optimization.")
        elif health_score > 70:
            insights.append("You're in good health with room for improvement in specific areas.")
        else:
            insights.append("There are several areas where we can work together to improve your health.")
        
        if risk_factors:
            insights.append(f"Key areas to address: {', '.join(risk_factors[:3])}")
        
        if strengths:
            insights.append(f"Your strengths: {', '.join(strengths)} - build on these!")
        
        if areas_for_improvement:
            insights.append(f"Focus areas: {', '.join(areas_for_improvement[:3])}")
        
        completion_rate = goals_progress.get("completion_rate", 0)
        if completion_rate > 80:
            insights.append("You have excellent goal completion rates - you're very goal-oriented!")
        elif completion_rate > 50:
            insights.append("You're making steady progress toward your goals.")
        else:
            insights.append("Let's work on setting more achievable goals and building consistency.")
        
        return insights
    
    def _generate_coaching_recommendations(self, coaching_plan: Dict[str, Any], level: str) -> List[str]:
        """Generate coaching recommendations"""
        recommendations = []
        
        focus_areas = coaching_plan.get("focus_areas", [])
        strategies = coaching_plan.get("strategies", {})
        
        recommendations.append(f"Focus on {len(focus_areas)} key areas: {', '.join(focus_areas)}")
        
        for area, area_strategies in strategies.items():
            if area_strategies.get("nutrition"):
                recommendations.append(f"For {area}: Start with nutrition basics and build from there")
            if area_strategies.get("exercise"):
                recommendations.append(f"For {area}: Include regular physical activity in your routine")
            if area_strategies.get("lifestyle"):
                recommendations.append(f"For {area}: Focus on sustainable lifestyle changes")
        
        if level == "beginner":
            recommendations.append("Start with small, manageable changes and build consistency")
            recommendations.append("Track your progress to stay motivated")
        elif level == "intermediate":
            recommendations.append("Challenge yourself with more specific goals and advanced strategies")
            recommendations.append("Consider working with a health professional for personalized guidance")
        else:  # advanced
            recommendations.append("Optimize your routine with advanced techniques and fine-tuning")
            recommendations.append("Consider becoming a health mentor for others")
        
        return recommendations 