"""
Nutrition Service API

API endpoints for nutrition analysis, food recognition, and recommendations.
"""

from .nutrition import nutrition_router
from .food_recognition import food_recognition_router
from .recommendations import recommendations_router
from .goals import goals_router

__all__ = [
    "nutrition_router",
    "food_recognition_router", 
    "recommendations_router",
    "goals_router"
] 