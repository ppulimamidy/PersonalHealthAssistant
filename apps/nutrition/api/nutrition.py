"""
Nutrition API endpoints for meal logging, nutrition analysis, and data management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from apps.nutrition.services.nutrition_service import NutritionService

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()

def get_nutrition_service(request: Request) -> NutritionService:
    """Get nutrition service from app state."""
    return request.app.state.nutrition_service

@router.post("/analyze-meal")
async def analyze_meal(
    request: Request,
    meal_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Analyze a meal and return nutritional breakdown and recommendations.
    
    Args:
        meal_data: Dictionary containing meal information including:
            - food_items: List of food items with names and portions
            - image: Optional base64 encoded image for food recognition
            - meal_type: Type of meal (breakfast, lunch, dinner, snack)
            - meal_name: Optional name for the meal
            - meal_description: Optional description
            - user_notes: Optional user notes
            - mood_before: Optional mood before meal
            - mood_after: Optional mood after meal
    
    Returns:
        Dictionary containing:
            - food_items: List of recognized foods with nutrition data
            - totals: Aggregated nutrition totals
            - recommendations: Personalized nutrition recommendations
            - user_preferences_used: Whether user preferences were used
    """
    try:
        user_id = current_user["id"]
        
        # Get token from request headers for user profile service
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        
        result = await nutrition_service.analyze_meal(user_id, meal_data, token)
        
        logger.info(f"Meal analysis completed for user {user_id}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Meal analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze meal"
        )

@router.post("/log-meal")
async def log_meal(
    request: Request,
    meal_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Log a meal for the user and return the logged meal analysis.
    
    Args:
        meal_data: Dictionary containing meal information (same as analyze_meal)
    
    Returns:
        Dictionary containing meal analysis with meal_log_id
    """
    try:
        user_id = current_user["id"]
        
        # Get token from request headers for user profile service
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        
        result = await nutrition_service.log_meal(user_id, meal_data, token)
        
        logger.info(f"Meal logged for user {user_id}, meal_log_id: {result.get('meal_log_id')}")
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Meal logging failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log meal"
        )

@router.get("/daily-nutrition/{target_date}")
async def get_daily_nutrition(
    target_date: date,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get daily nutrition summary for a user.
    
    Args:
        target_date: Date to get nutrition summary for (YYYY-MM-DD)
    
    Returns:
        Dictionary containing daily nutrition summary
    """
    try:
        user_id = current_user["id"]
        result = await nutrition_service.get_daily_nutrition(user_id, target_date)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get daily nutrition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get daily nutrition"
        )

@router.get("/nutrition-history")
async def get_nutrition_history(
    start_date: date,
    end_date: date,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get nutrition history for a user over a date range.
    
    Args:
        start_date: Start date for history (YYYY-MM-DD)
        end_date: End date for history (YYYY-MM-DD)
    
    Returns:
        Dictionary containing nutrition history
    """
    try:
        user_id = current_user["id"]
        result = await nutrition_service.get_nutrition_history(user_id, start_date, end_date)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get nutrition history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nutrition history"
        )

@router.get("/personalized-recommendations")
async def get_personalized_recommendations(
    request: Request,
    nutrition_data: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get personalized nutrition recommendations based on user profile and preferences.
    
    Args:
        nutrition_data: Optional nutrition data to base recommendations on
    
    Returns:
        Dictionary containing personalized recommendations
    """
    try:
        user_id = current_user["id"]
        
        # Get token from request headers for user profile service
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required for personalized recommendations"
            )
        
        result = await nutrition_service.get_personalized_recommendations(user_id, token, nutrition_data)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get personalized recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personalized recommendations"
        )

@router.get("/nutrition-summary")
async def get_nutrition_summary(
    request: Request,
    days: int = 7,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get comprehensive nutrition summary for a user including preferences and recent data.
    
    Args:
        days: Number of days to include in summary (default: 7)
    
    Returns:
        Dictionary containing comprehensive nutrition summary
    """
    try:
        user_id = current_user["id"]
        
        # Get token from request headers for user profile service
        auth_header = request.headers.get("Authorization")
        token = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required for nutrition summary"
            )
        
        result = await nutrition_service.get_user_nutrition_summary(user_id, token, days)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get nutrition summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nutrition summary"
        )

@router.post("/calculate-nutrition")
async def calculate_nutrition(
    food_items: List[Dict[str, Any]],
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Calculate nutrition for a list of food items.
    
    Args:
        food_items: List of food items with names and portions
    
    Returns:
        Dictionary containing calculated nutrition data
    """
    try:
        result = await nutrition_service.calculate_nutrition(food_items)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate nutrition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate nutrition"
        )

@router.get("/nutritional-trends/{nutrient}")
async def get_nutritional_trends(
    nutrient: str,
    period: str = "7_days",
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get nutritional trends for a user.
    
    Args:
        nutrient: Nutrient to analyze (calories, protein, carbs, fat)
        period: Time period (7_days, 30_days, 90_days)
    
    Returns:
        Dictionary containing nutritional trends
    """
    try:
        user_id = current_user["id"]
        result = await nutrition_service.get_nutritional_trends(user_id, nutrient, period)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get nutritional trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nutritional trends"
        )

@router.get("/nutritional-insights")
async def get_nutritional_insights(
    timeframe: str = "week",
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get nutritional insights for a user.
    
    Args:
        timeframe: Time frame for insights (week, month)
    
    Returns:
        Dictionary containing nutritional insights
    """
    try:
        user_id = current_user["id"]
        result = await nutrition_service.get_nutritional_insights(user_id, timeframe)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get nutritional insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nutritional insights"
        )

@router.delete("/meals/{meal_id}")
async def delete_meal(
    meal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Delete a meal log.
    
    Args:
        meal_id: ID of the meal to delete
    
    Returns:
        Success message
    """
    try:
        user_id = current_user["id"]
        await nutrition_service.delete_meal(meal_id)
        
        logger.info(f"Meal {meal_id} deleted for user {user_id}")
        return {
            "success": True,
            "message": "Meal deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete meal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete meal"
        )

@router.post("/food-items")
async def create_food_item(
    food_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Create a custom food item for a user.
    
    Args:
        food_data: Dictionary containing food item data
    
    Returns:
        Dictionary containing created food item
    """
    try:
        user_id = current_user["id"]
        result = await nutrition_service.create_food_item(user_id, food_data)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to create food item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create food item"
        )

@router.get("/food-items/{food_id}")
async def get_food_item(
    food_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Get a specific food item by ID.
    
    Args:
        food_id: ID of the food item
    
    Returns:
        Dictionary containing food item data
    """
    try:
        result = await nutrition_service.get_food_item(food_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food item not found"
            )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get food item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get food item"
        )

@router.get("/search-foods")
async def search_foods(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service)
) -> Dict[str, Any]:
    """
    Search for foods in the database.
    
    Args:
        query: Search query
        category: Optional food category filter
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results
    """
    try:
        result = await nutrition_service.search_foods(query, category, limit)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to search foods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search foods"
        )

# Export the router
nutrition_router = router 