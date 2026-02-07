"""
Nutrition Recommendations API Endpoints

Endpoints for personalized nutrition recommendations and meal planning.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from common.middleware.auth import get_current_user
from apps.nutrition.models.recommendations_models import (
    NutritionRecommendation, MealRecommendation, MealPlan, ShoppingList,
    DietaryRestriction, RecommendationType
)
from apps.nutrition.services.recommendations_service import RecommendationsService

logger = logging.getLogger(__name__)

recommendations_router = APIRouter()


@recommendations_router.get("/personalized/{user_id}", response_model=List[NutritionRecommendation])
async def get_personalized_recommendations(
    user_id: str,
    goal_id: Optional[str] = None,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get personalized nutrition recommendations for a user.
    
    Args:
        user_id: User identifier
        goal_id: Optional goal identifier to filter recommendations
        limit: Maximum number of recommendations
        current_user: Authenticated user information
    
    Returns:
        List of personalized nutrition recommendations
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting personalized recommendations for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Get recommendations
        recommendations = await recommendations_service.get_personalized_recommendations(
            user_id=user_id,
            goal_id=goal_id,
            limit=limit
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personalized recommendations"
        )


@recommendations_router.post("/meal-plan", response_model=MealPlan)
async def create_meal_plan(
    meal_plan_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a personalized meal plan for a user.
    
    Args:
        meal_plan_data: Meal plan configuration data
        current_user: Authenticated user information
    
    Returns:
        Created meal plan
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Creating meal plan for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Create meal plan
        meal_plan = await recommendations_service.create_meal_plan(
            user_id=user_id,
            meal_plan_data=meal_plan_data
        )
        
        logger.info(f"Meal plan created successfully for user {user_id}")
        return meal_plan
        
    except Exception as e:
        logger.error(f"Error creating meal plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create meal plan"
        )


@recommendations_router.get("/meal-plan/{plan_id}", response_model=MealPlan)
async def get_meal_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific meal plan by ID.
    
    Args:
        plan_id: Meal plan identifier
        current_user: Authenticated user information
    
    Returns:
        Meal plan details
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting meal plan {plan_id} for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Get meal plan
        meal_plan = await recommendations_service.get_meal_plan(plan_id)
        
        if not meal_plan or meal_plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        return meal_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meal plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get meal plan"
        )


@recommendations_router.get("/meal-plans/{user_id}", response_model=List[MealPlan])
async def get_user_meal_plans(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all meal plans for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated user information
    
    Returns:
        List of user's meal plans
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting meal plans for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Get meal plans
        meal_plans = await recommendations_service.get_user_meal_plans(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return meal_plans
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meal plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get meal plans"
        )


@recommendations_router.post("/meal-suggestion", response_model=MealRecommendation)
async def get_meal_suggestion(
    meal_type: str,
    user_id: str,
    dietary_restrictions: Optional[List[str]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a meal suggestion for a specific meal type.
    
    Args:
        meal_type: Type of meal (breakfast, lunch, dinner, snack)
        user_id: User identifier
        dietary_restrictions: List of dietary restrictions
        current_user: Authenticated user information
    
    Returns:
        Meal recommendation
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting meal suggestion for user {user_id}, meal type: {meal_type}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Get meal suggestion
        meal_suggestion = await recommendations_service.get_meal_suggestion(
            user_id=user_id,
            meal_type=meal_type,
            dietary_restrictions=dietary_restrictions
        )
        
        return meal_suggestion
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meal suggestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get meal suggestion"
        )


@recommendations_router.post("/shopping-list", response_model=ShoppingList)
async def generate_shopping_list(
    meal_plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate a shopping list based on a meal plan.
    
    Args:
        meal_plan_id: Meal plan identifier
        current_user: Authenticated user information
    
    Returns:
        Generated shopping list
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Generating shopping list for meal plan {meal_plan_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Generate shopping list
        shopping_list = await recommendations_service.generate_shopping_list(
            meal_plan_id=meal_plan_id,
            user_id=user_id
        )
        
        logger.info(f"Shopping list generated successfully for meal plan {meal_plan_id}")
        return shopping_list
        
    except Exception as e:
        logger.error(f"Error generating shopping list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate shopping list"
        )


@recommendations_router.get("/dietary-restrictions/{user_id}", response_model=DietaryRestriction)
async def get_dietary_restrictions(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get dietary restrictions for a user.
    
    Args:
        user_id: User identifier
        current_user: Authenticated user information
    
    Returns:
        User's dietary restrictions
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting dietary restrictions for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Get dietary restrictions
        restrictions = await recommendations_service.get_dietary_restrictions(user_id)
        
        return restrictions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dietary restrictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dietary restrictions"
        )


@recommendations_router.put("/dietary-restrictions/{user_id}", response_model=DietaryRestriction)
async def update_dietary_restrictions(
    user_id: str,
    restrictions: DietaryRestriction,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update dietary restrictions for a user.
    
    Args:
        user_id: User identifier
        restrictions: Updated dietary restrictions
        current_user: Authenticated user information
    
    Returns:
        Updated dietary restrictions
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Updating dietary restrictions for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Update dietary restrictions
        updated_restrictions = await recommendations_service.update_dietary_restrictions(
            user_id=user_id,
            restrictions=restrictions
        )
        
        logger.info(f"Dietary restrictions updated successfully for user {user_id}")
        return updated_restrictions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dietary restrictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update dietary restrictions"
        )


@recommendations_router.post("/recommendation-feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    feedback: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback for a nutrition recommendation.
    
    Args:
        recommendation_id: Recommendation identifier
        feedback: User feedback data
        current_user: Authenticated user information
    
    Returns:
        Feedback submission confirmation
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Submitting feedback for recommendation {recommendation_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Submit feedback
        result = await recommendations_service.submit_recommendation_feedback(
            recommendation_id=recommendation_id,
            user_id=user_id,
            feedback=feedback
        )
        
        logger.info(f"Feedback submitted successfully for recommendation {recommendation_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error submitting recommendation feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit recommendation feedback"
        )


@recommendations_router.get("/recommendation-history/{user_id}")
async def get_recommendation_history(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's recommendation history.
    
    Args:
        user_id: User identifier
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated user information
    
    Returns:
        List of past recommendations
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting recommendation history for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Get history
        history = await recommendations_service.get_recommendation_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendation history"
        )


@recommendations_router.delete("/meal-plan/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a meal plan.
    
    Args:
        plan_id: Meal plan identifier
        current_user: Authenticated user information
    
    Returns:
        Success message
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Deleting meal plan {plan_id} for user {user_id}")
        
        # Initialize recommendations service
        recommendations_service = RecommendationsService()
        
        # Verify ownership
        meal_plan = await recommendations_service.get_meal_plan(plan_id)
        if not meal_plan or meal_plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        # Delete meal plan
        await recommendations_service.delete_meal_plan(plan_id)
        
        logger.info(f"Meal plan {plan_id} deleted successfully")
        return {"message": "Meal plan deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meal plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete meal plan"
        ) 