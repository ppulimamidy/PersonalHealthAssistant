"""
Nutrition Recommendations Models

Models for nutrition recommendations, meal planning, and dietary suggestions.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class RecommendationType(str, Enum):
    """Types of nutrition recommendations."""
    MEAL_PLANNING = "meal_planning"
    FOOD_SUBSTITUTION = "food_substitution"
    PORTION_CONTROL = "portion_control"
    TIMING_OPTIMIZATION = "timing_optimization"
    NUTRIENT_BALANCE = "nutrient_balance"
    CULTURAL_ADAPTATION = "cultural_adaptation"
    ALLERGEN_AVOIDANCE = "allergen_avoidance"
    HEALTH_CONDITION = "health_condition"
    LIFESTYLE_INTEGRATION = "lifestyle_integration"
    COST_OPTIMIZATION = "cost_optimization"


class RecommendationPriority(str, Enum):
    """Recommendation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MealType(str, Enum):
    """Types of meals."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"


class DietaryRestriction(BaseModel):
    """Dietary restrictions and preferences."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Dietary restrictions
    vegetarian: bool = Field(False, description="Vegetarian diet")
    vegan: bool = Field(False, description="Vegan diet")
    gluten_free: bool = Field(False, description="Gluten-free diet")
    dairy_free: bool = Field(False, description="Dairy-free diet")
    nut_free: bool = Field(False, description="Nut-free diet")
    low_sodium: bool = Field(False, description="Low-sodium diet")
    low_sugar: bool = Field(False, description="Low-sugar diet")
    low_fat: bool = Field(False, description="Low-fat diet")
    low_carb: bool = Field(False, description="Low-carbohydrate diet")
    keto: bool = Field(False, description="Ketogenic diet")
    paleo: bool = Field(False, description="Paleo diet")
    mediterranean: bool = Field(False, description="Mediterranean diet")
    
    # Allergies and intolerances
    allergies: List[str] = Field(default_factory=list, description="Food allergies")
    intolerances: List[str] = Field(default_factory=list, description="Food intolerances")
    
    # Preferences
    preferred_cuisines: List[str] = Field(default_factory=list, description="Preferred cuisines")
    disliked_foods: List[str] = Field(default_factory=list, description="Disliked foods")
    preferred_cooking_methods: List[str] = Field(default_factory=list, description="Preferred cooking methods")
    
    # Religious/cultural restrictions
    halal: bool = Field(False, description="Halal diet")
    kosher: bool = Field(False, description="Kosher diet")
    religious_restrictions: List[str] = Field(default_factory=list, description="Religious dietary restrictions")
    
    # Health-based restrictions
    medical_conditions: List[str] = Field(default_factory=list, description="Medical conditions affecting diet")
    medications: List[str] = Field(default_factory=list, description="Medications affecting diet")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "vegetarian": True,
                "gluten_free": False,
                "allergies": ["peanuts", "shellfish"],
                "intolerances": ["lactose"],
                "preferred_cuisines": ["mediterranean", "indian"],
                "disliked_foods": ["mushrooms", "olives"],
                "medical_conditions": ["diabetes"]
            }
        }


class NutritionRecommendation(BaseModel):
    """A nutrition recommendation for a user."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Recommendation details
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation description")
    recommendation_type: RecommendationType = Field(..., description="Type of recommendation")
    priority: RecommendationPriority = Field(..., description="Recommendation priority")
    
    # Context
    goal_id: Optional[str] = Field(None, description="Related goal identifier")
    health_condition: Optional[str] = Field(None, description="Related health condition")
    
    # Action items
    action_items: List[str] = Field(..., description="Specific action items")
    expected_outcome: str = Field(..., description="Expected outcome")
    timeframe: str = Field(..., description="Recommended timeframe")
    
    # Implementation details
    difficulty: str = Field(..., description="Implementation difficulty (easy, medium, hard)")
    time_commitment: str = Field(..., description="Time commitment required")
    cost_impact: str = Field(..., description="Cost impact (low, medium, high)")
    
    # Evidence and reasoning
    evidence_level: str = Field(..., description="Evidence level (low, medium, high)")
    scientific_basis: Optional[str] = Field(None, description="Scientific basis for recommendation")
    studies_referenced: Optional[List[str]] = Field(None, description="Referenced studies")
    
    # Personalization
    personalized_for: Dict[str, Any] = Field(default_factory=dict, description="Personalization factors")
    cultural_considerations: Optional[List[str]] = Field(None, description="Cultural considerations")
    
    # Tracking
    is_implemented: bool = Field(False, description="Whether recommendation has been implemented")
    implementation_date: Optional[datetime] = Field(None, description="Implementation date")
    effectiveness_score: Optional[float] = Field(None, description="Effectiveness score (0-100)")
    user_feedback: Optional[str] = Field(None, description="User feedback")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Recommendation expiration date")
    source: str = Field(..., description="Source of recommendation (AI, healthcare provider, etc.)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user123",
                "title": "Increase Protein Intake for Muscle Building",
                "description": "Add more lean protein sources to support muscle growth and recovery",
                "recommendation_type": "nutrient_balance",
                "priority": "high",
                "action_items": [
                    "Include 20-30g protein in each meal",
                    "Add Greek yogurt to breakfast",
                    "Choose lean meats for lunch and dinner"
                ],
                "expected_outcome": "Improved muscle growth and recovery",
                "timeframe": "2-4 weeks",
                "difficulty": "medium",
                "time_commitment": "10 minutes per meal",
                "cost_impact": "medium",
                "evidence_level": "high",
                "personalized_for": {
                    "goal": "muscle_gain",
                    "activity_level": "moderate"
                }
            }
        }
    }


class MealRecommendation(BaseModel):
    """A specific meal recommendation."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    meal_type: MealType = Field(..., description="Type of meal")
    
    # Meal details
    title: str = Field(..., description="Meal title")
    description: str = Field(..., description="Meal description")
    
    # Nutritional targets
    target_calories: float = Field(..., description="Target calories")
    target_protein: float = Field(..., description="Target protein (g)")
    target_carbs: float = Field(..., description="Target carbohydrates (g)")
    target_fat: float = Field(..., description="Target fat (g)")
    target_fiber: float = Field(..., description="Target fiber (g)")
    
    # Food items
    food_items: List[Dict[str, Any]] = Field(..., description="Recommended food items")
    alternatives: Optional[List[Dict[str, Any]]] = Field(None, description="Alternative food items")
    
    # Preparation
    preparation_time: str = Field(..., description="Preparation time")
    cooking_time: str = Field(..., description="Cooking time")
    difficulty: str = Field(..., description="Preparation difficulty")
    ingredients: List[str] = Field(..., description="Required ingredients")
    instructions: List[str] = Field(..., description="Preparation instructions")
    
    # Nutritional analysis
    estimated_nutrition: Dict[str, float] = Field(..., description="Estimated nutritional values")
    health_score: float = Field(..., description="Health score (0-100)")
    
    # Personalization
    dietary_compliance: Dict[str, bool] = Field(..., description="Dietary restriction compliance")
    cultural_appropriateness: float = Field(..., description="Cultural appropriateness score (0-100)")
    
    # Cost and availability
    estimated_cost: str = Field(..., description="Estimated cost (low, medium, high)")
    seasonal_availability: List[str] = Field(..., description="Seasonal availability")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    source: str = Field(..., description="Source of recommendation")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "meal_type": "breakfast",
                "title": "Protein-Rich Greek Yogurt Bowl",
                "description": "A balanced breakfast with protein, fiber, and healthy fats",
                "target_calories": 350.0,
                "target_protein": 25.0,
                "target_carbs": 35.0,
                "target_fat": 12.0,
                "target_fiber": 8.0,
                "food_items": [
                    {
                        "name": "Greek Yogurt",
                        "quantity": 1.0,
                        "unit": "cup",
                        "calories": 130.0,
                        "protein": 22.0
                    }
                ],
                "preparation_time": "5 minutes",
                "cooking_time": "0 minutes",
                "difficulty": "easy",
                "ingredients": ["Greek yogurt", "berries", "nuts", "honey"],
                "estimated_nutrition": {
                    "calories": 350.0,
                    "protein": 25.0,
                    "carbs": 35.0,
                    "fat": 12.0,
                    "fiber": 8.0
                },
                "health_score": 85.0,
                "dietary_compliance": {
                    "vegetarian": True,
                    "gluten_free": True,
                    "dairy_free": False
                }
            }
        }


class MealPlan(BaseModel):
    """A complete meal plan for a user."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Plan details
    title: str = Field(..., description="Meal plan title")
    description: str = Field(..., description="Meal plan description")
    start_date: date = Field(..., description="Plan start date")
    end_date: date = Field(..., description="Plan end date")
    
    # Goals and targets
    goal_id: Optional[str] = Field(None, description="Related goal identifier")
    daily_calorie_target: float = Field(..., description="Daily calorie target")
    daily_protein_target: float = Field(..., description="Daily protein target")
    daily_carb_target: float = Field(..., description="Daily carbohydrate target")
    daily_fat_target: float = Field(..., description="Daily fat target")
    
    # Meals
    meals: Dict[str, List[MealRecommendation]] = Field(..., description="Meals by date")
    
    # Nutritional summary
    average_daily_calories: float = Field(0.0, description="Average daily calories")
    average_daily_protein: float = Field(0.0, description="Average daily protein")
    average_daily_carbs: float = Field(0.0, description="Average daily carbohydrates")
    average_daily_fat: float = Field(0.0, description="Average daily fat")
    
    # Compliance tracking
    adherence_rate: float = Field(0.0, description="Plan adherence rate (0-100)")
    completed_meals: int = Field(0, description="Number of completed meals")
    total_meals: int = Field(0, description="Total number of planned meals")
    
    # User feedback
    user_rating: Optional[float] = Field(None, description="User rating (1-5)")
    user_feedback: Optional[str] = Field(None, description="User feedback")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: str = Field(..., description="Who created the plan")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "title": "7-Day Weight Loss Meal Plan",
                "description": "Balanced meal plan for healthy weight loss",
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "daily_calorie_target": 1800.0,
                "daily_protein_target": 120.0,
                "daily_carb_target": 200.0,
                "daily_fat_target": 60.0,
                "average_daily_calories": 1780.0,
                "adherence_rate": 85.0,
                "completed_meals": 17,
                "total_meals": 20
            }
        }


class ShoppingList(BaseModel):
    """A shopping list based on meal recommendations."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    meal_plan_id: Optional[str] = Field(None, description="Related meal plan identifier")
    
    # List details
    title: str = Field(..., description="Shopping list title")
    description: Optional[str] = Field(None, description="Shopping list description")
    
    # Items
    items: List[Dict[str, Any]] = Field(..., description="Shopping list items")
    
    # Organization
    categories: Dict[str, List[str]] = Field(default_factory=dict, description="Items organized by category")
    
    # Cost estimation
    estimated_total_cost: Optional[float] = Field(None, description="Estimated total cost")
    cost_breakdown: Optional[Dict[str, float]] = Field(None, description="Cost breakdown by category")
    
    # Shopping information
    store_recommendations: Optional[List[str]] = Field(None, description="Recommended stores")
    shopping_tips: Optional[List[str]] = Field(None, description="Shopping tips")
    
    # Status
    is_completed: bool = Field(False, description="Whether shopping is completed")
    completed_items: List[str] = Field(default_factory=list, description="Completed items")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "title": "Weekly Shopping List",
                "description": "Shopping list for 7-day meal plan",
                "items": [
                    {
                        "name": "Greek Yogurt",
                        "quantity": 2,
                        "unit": "cups",
                        "category": "dairy",
                        "estimated_cost": 4.50
                    }
                ],
                "categories": {
                    "dairy": ["Greek Yogurt", "Milk"],
                    "produce": ["Berries", "Spinach", "Tomatoes"]
                },
                "estimated_total_cost": 45.75,
                "store_recommendations": ["Whole Foods", "Trader Joe's"]
            }
        } 