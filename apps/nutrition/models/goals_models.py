"""
Nutrition Goals Models

Models for nutrition goals, goal tracking, and progress monitoring.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class GoalType(str, Enum):
    """Types of nutrition goals."""
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    WEIGHT_MAINTENANCE = "weight_maintenance"
    MUSCLE_GAIN = "muscle_gain"
    DIABETES_MANAGEMENT = "diabetes_management"
    HEART_HEALTH = "heart_health"
    CHOLESTEROL_MANAGEMENT = "cholesterol_management"
    BLOOD_PRESSURE_MANAGEMENT = "blood_pressure_management"
    ENERGY_OPTIMIZATION = "energy_optimization"
    DIGESTIVE_HEALTH = "digestive_health"
    IMMUNE_BOOST = "immune_boost"
    ANTI_INFLAMMATORY = "anti_inflammatory"


class GoalStatus(str, Enum):
    """Goal status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GoalPriority(str, Enum):
    """Goal priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NutritionGoal(BaseModel):
    """A nutrition goal for a user."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    goal_type: GoalType = Field(..., description="Type of nutrition goal")
    
    # Goal details
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(None, description="Goal description")
    
    # Target values
    target_calories: Optional[float] = Field(None, description="Daily calorie target")
    target_protein: Optional[float] = Field(None, description="Daily protein target (g)")
    target_carbs: Optional[float] = Field(None, description="Daily carbohydrate target (g)")
    target_fat: Optional[float] = Field(None, description="Daily fat target (g)")
    target_fiber: Optional[float] = Field(None, description="Daily fiber target (g)")
    target_sugar: Optional[float] = Field(None, description="Daily sugar limit (g)")
    target_sodium: Optional[float] = Field(None, description="Daily sodium limit (mg)")
    
    # Weight goals
    target_weight: Optional[float] = Field(None, description="Target weight (kg)")
    current_weight: Optional[float] = Field(None, description="Current weight (kg)")
    weight_change_rate: Optional[float] = Field(None, description="Target weight change per week (kg)")
    
    # Health parameter goals
    target_blood_sugar: Optional[float] = Field(None, description="Target blood sugar (mg/dL)")
    target_cholesterol: Optional[float] = Field(None, description="Target cholesterol (mg/dL)")
    target_blood_pressure_systolic: Optional[int] = Field(None, description="Target systolic BP (mmHg)")
    target_blood_pressure_diastolic: Optional[int] = Field(None, description="Target diastolic BP (mmHg)")
    
    # Goal timeline
    start_date: date = Field(..., description="Goal start date")
    target_date: Optional[date] = Field(None, description="Goal target date")
    duration_weeks: Optional[int] = Field(None, description="Goal duration in weeks")
    
    # Goal status
    status: GoalStatus = Field(GoalStatus.ACTIVE, description="Goal status")
    priority: GoalPriority = Field(GoalPriority.MEDIUM, description="Goal priority")
    progress_percentage: float = Field(0.0, description="Progress percentage (0-100)")
    
    # Dietary preferences
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    food_preferences: Optional[List[str]] = Field(None, description="Food preferences")
    allergies: Optional[List[str]] = Field(None, description="Food allergies")
    
    # Medical context
    medical_conditions: Optional[List[str]] = Field(None, description="Relevant medical conditions")
    medications: Optional[List[str]] = Field(None, description="Current medications")
    
    # Activity level
    activity_level: Optional[str] = Field(None, description="Activity level (sedentary, light, moderate, active, very_active)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Who created the goal (user or healthcare provider)")
    
    @validator('progress_percentage')
    def validate_progress_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        return v
    
    @validator('target_date')
    def validate_target_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError("Target date must be after start date")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user123",
                "goal_type": "weight_loss",
                "title": "Lose 10kg in 12 weeks",
                "description": "Healthy weight loss through balanced nutrition",
                "target_calories": 1800.0,
                "target_protein": 120.0,
                "target_carbs": 200.0,
                "target_fat": 60.0,
                "target_fiber": 25.0,
                "target_weight": 70.0,
                "current_weight": 80.0,
                "weight_change_rate": 0.8,
                "start_date": "2024-01-01",
                "target_date": "2024-03-25",
                "duration_weeks": 12,
                "dietary_restrictions": ["vegetarian"],
                "activity_level": "moderate"
            }
        }
    }


class GoalProgress(BaseModel):
    """Progress tracking for a nutrition goal."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    goal_id: str = Field(..., description="Goal identifier")
    user_id: str = Field(..., description="User identifier")
    progress_date: date = Field(..., description="Progress date")
    
    # Daily progress
    calories_consumed: float = Field(0.0, description="Calories consumed")
    protein_consumed: float = Field(0.0, description="Protein consumed (g)")
    carbs_consumed: float = Field(0.0, description="Carbohydrates consumed (g)")
    fat_consumed: float = Field(0.0, description="Fat consumed (g)")
    fiber_consumed: float = Field(0.0, description="Fiber consumed (g)")
    sugar_consumed: float = Field(0.0, description="Sugar consumed (g)")
    sodium_consumed: float = Field(0.0, description="Sodium consumed (mg)")
    
    # Goal comparison
    calories_progress: float = Field(0.0, description="Calorie goal progress percentage")
    protein_progress: float = Field(0.0, description="Protein goal progress percentage")
    carbs_progress: float = Field(0.0, description="Carbohydrate goal progress percentage")
    fat_progress: float = Field(0.0, description="Fat goal progress percentage")
    fiber_progress: float = Field(0.0, description="Fiber goal progress percentage")
    
    # Weight tracking
    current_weight: Optional[float] = Field(None, description="Current weight (kg)")
    weight_change: Optional[float] = Field(None, description="Weight change from start (kg)")
    
    # Health metrics
    blood_sugar: Optional[float] = Field(None, description="Blood sugar reading (mg/dL)")
    cholesterol: Optional[float] = Field(None, description="Cholesterol reading (mg/dL)")
    blood_pressure_systolic: Optional[int] = Field(None, description="Systolic blood pressure (mmHg)")
    blood_pressure_diastolic: Optional[int] = Field(None, description="Diastolic blood pressure (mmHg)")
    
    # Compliance metrics
    meals_logged: int = Field(0, description="Number of meals logged")
    goal_compliance_score: float = Field(0.0, description="Overall goal compliance score (0-100)")
    
    # Notes and observations
    notes: Optional[str] = Field(None, description="User notes for the day")
    challenges: Optional[List[str]] = Field(None, description="Challenges faced")
    achievements: Optional[List[str]] = Field(None, description="Achievements for the day")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "goal_id": "goal123",
                "user_id": "user123",
                "progress_date": "2024-01-15",
                "calories_consumed": 1750.0,
                "protein_consumed": 115.0,
                "carbs_consumed": 195.0,
                "fat_consumed": 58.0,
                "fiber_consumed": 23.0,
                "calories_progress": 97.2,
                "protein_progress": 95.8,
                "carbs_progress": 97.5,
                "fat_progress": 96.7,
                "fiber_progress": 92.0,
                "current_weight": 78.5,
                "weight_change": -1.5,
                "meals_logged": 3,
                "goal_compliance_score": 95.8,
                "notes": "Feeling great today! Had a good workout."
            }
        }
    }


class GoalSummary(BaseModel):
    """Summary of goal progress over time."""
    
    goal_id: str = Field(..., description="Goal identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Overall progress
    total_days: int = Field(..., description="Total days since goal start")
    days_completed: int = Field(..., description="Days with logged data")
    completion_rate: float = Field(..., description="Data completion rate percentage")
    
    # Progress trends
    average_calories: float = Field(0.0, description="Average daily calories")
    average_protein: float = Field(0.0, description="Average daily protein")
    average_carbs: float = Field(0.0, description="Average daily carbohydrates")
    average_fat: float = Field(0.0, description="Average daily fat")
    average_fiber: float = Field(0.0, description="Average daily fiber")
    
    # Goal achievement
    calories_goal_achievement: float = Field(0.0, description="Calorie goal achievement percentage")
    protein_goal_achievement: float = Field(0.0, description="Protein goal achievement percentage")
    carbs_goal_achievement: float = Field(0.0, description="Carbohydrate goal achievement percentage")
    fat_goal_achievement: float = Field(0.0, description="Fat goal achievement percentage")
    fiber_goal_achievement: float = Field(0.0, description="Fiber goal achievement percentage")
    
    # Weight progress
    starting_weight: Optional[float] = Field(None, description="Starting weight (kg)")
    current_weight: Optional[float] = Field(None, description="Current weight (kg)")
    total_weight_change: Optional[float] = Field(None, description="Total weight change (kg)")
    weight_change_rate: Optional[float] = Field(None, description="Average weekly weight change (kg)")
    
    # Health improvements
    health_improvements: Optional[List[str]] = Field(None, description="Health improvements observed")
    
    # Streaks and consistency
    longest_streak: int = Field(0, description="Longest consecutive days of logging")
    current_streak: int = Field(0, description="Current consecutive days of logging")
    
    # Recommendations
    recommendations: Optional[List[str]] = Field(None, description="Recommendations for improvement")
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "goal_id": "goal123",
                "user_id": "user123",
                "total_days": 15,
                "days_completed": 14,
                "completion_rate": 93.3,
                "average_calories": 1780.0,
                "average_protein": 118.0,
                "average_carbs": 198.0,
                "average_fat": 59.0,
                "average_fiber": 24.0,
                "calories_goal_achievement": 98.9,
                "protein_goal_achievement": 98.3,
                "carbs_goal_achievement": 99.0,
                "fat_goal_achievement": 98.3,
                "fiber_goal_achievement": 96.0,
                "starting_weight": 80.0,
                "current_weight": 78.5,
                "total_weight_change": -1.5,
                "weight_change_rate": -0.75,
                "longest_streak": 8,
                "current_streak": 5,
                "recommendations": ["Consider adding more fiber-rich foods", "Great progress on protein intake"]
            }
        }


class GoalRecommendation(BaseModel):
    """Recommendations for achieving nutrition goals."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    goal_id: str = Field(..., description="Goal identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Recommendation details
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    category: str = Field(..., description="Recommendation category")
    priority: GoalPriority = Field(..., description="Recommendation priority")
    
    # Action items
    action_items: List[str] = Field(..., description="Specific action items")
    expected_impact: str = Field(..., description="Expected impact of following recommendation")
    
    # Implementation
    difficulty: str = Field(..., description="Implementation difficulty (easy, medium, hard)")
    time_commitment: str = Field(..., description="Time commitment required")
    resources_needed: Optional[List[str]] = Field(None, description="Resources needed")
    
    # Tracking
    is_implemented: bool = Field(False, description="Whether recommendation has been implemented")
    implementation_date: Optional[datetime] = Field(None, description="Implementation date")
    effectiveness_score: Optional[float] = Field(None, description="Effectiveness score (0-100)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Recommendation expiration date")
    
    class Config:
        schema_extra = {
            "example": {
                "goal_id": "goal123",
                "user_id": "user123",
                "title": "Increase Fiber Intake",
                "description": "Add more fiber-rich foods to improve digestive health and satiety",
                "category": "nutrition",
                "priority": "medium",
                "action_items": [
                    "Add 1 cup of berries to breakfast",
                    "Include leafy greens in lunch",
                    "Choose whole grain options"
                ],
                "expected_impact": "Improved digestive health and better appetite control",
                "difficulty": "easy",
                "time_commitment": "5 minutes per meal"
            }
        } 