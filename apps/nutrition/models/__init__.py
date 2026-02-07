"""
Nutrition Service Models

Data models for food recognition, nutritional analysis, and recommendations.
"""

from .nutrition_models import *
from .food_recognition_models import *
from .goals_models import *
from .recommendations_models import *

__all__ = [
    # Nutrition models
    "NutritionalData",
    "FoodItem",
    "MealAnalysis",
    "DailyNutrition",
    
    # Food recognition models
    "FoodRecognitionRequest",
    "FoodRecognitionResponse",
    "RecognizedFood",
    "PortionEstimate",
    
    # Goals models
    "NutritionGoal",
    "GoalType",
    "GoalProgress",
    
    # Recommendations models
    "NutritionRecommendation",
    "MealRecommendation",
    "DietaryRestriction"
] 