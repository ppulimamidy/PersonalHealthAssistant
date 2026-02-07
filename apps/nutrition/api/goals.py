"""
Nutrition Goals API Endpoints

Endpoints for nutrition goal management and progress tracking.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from common.middleware.auth import get_current_user
from apps.nutrition.models.goals_models import (
    NutritionGoal, GoalProgress, GoalSummary, GoalRecommendation, GoalType, GoalStatus
)
from apps.nutrition.services.goals_service import GoalsService

logger = logging.getLogger(__name__)

goals_router = APIRouter()


@goals_router.post("/create", response_model=NutritionGoal)
async def create_nutrition_goal(
    goal_data: NutritionGoal,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new nutrition goal for a user.
    
    Args:
        goal_data: Nutrition goal data
        current_user: Authenticated user information
    
    Returns:
        Created nutrition goal
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Creating nutrition goal for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Create goal
        created_goal = await goals_service.create_goal(
            user_id=user_id,
            goal_data=goal_data
        )
        
        logger.info(f"Nutrition goal created successfully for user {user_id}")
        return created_goal
        
    except Exception as e:
        logger.error(f"Error creating nutrition goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create nutrition goal"
        )


@goals_router.get("/{goal_id}", response_model=NutritionGoal)
async def get_nutrition_goal(
    goal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific nutrition goal by ID.
    
    Args:
        goal_id: Goal identifier
        current_user: Authenticated user information
    
    Returns:
        Nutrition goal details
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting nutrition goal {goal_id} for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Get goal
        goal = await goals_service.get_goal(goal_id)
        
        if not goal or goal.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition goal not found"
            )
        
        return goal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting nutrition goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get nutrition goal"
        )


@goals_router.get("/user/{user_id}", response_model=List[NutritionGoal])
async def get_user_goals(
    user_id: str,
    status_filter: Optional[GoalStatus] = None,
    goal_type: Optional[GoalType] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all nutrition goals for a user.
    
    Args:
        user_id: User identifier
        status_filter: Filter by goal status
        goal_type: Filter by goal type
        current_user: Authenticated user information
    
    Returns:
        List of user's nutrition goals
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting nutrition goals for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Get goals
        goals = await goals_service.get_user_goals(
            user_id=user_id,
            status_filter=status_filter,
            goal_type=goal_type
        )
        
        return goals
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user goals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user goals"
        )


@goals_router.put("/{goal_id}", response_model=NutritionGoal)
async def update_nutrition_goal(
    goal_id: str,
    goal_updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a nutrition goal.
    
    Args:
        goal_id: Goal identifier
        goal_updates: Goal update data
        current_user: Authenticated user information
    
    Returns:
        Updated nutrition goal
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Updating nutrition goal {goal_id} for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Verify ownership
        goal = await goals_service.get_goal(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition goal not found"
            )
        
        # Update goal
        updated_goal = await goals_service.update_goal(
            goal_id=goal_id,
            updates=goal_updates
        )
        
        logger.info(f"Nutrition goal {goal_id} updated successfully")
        return updated_goal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating nutrition goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update nutrition goal"
        )


@goals_router.delete("/{goal_id}")
async def delete_nutrition_goal(
    goal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a nutrition goal.
    
    Args:
        goal_id: Goal identifier
        current_user: Authenticated user information
    
    Returns:
        Success message
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Deleting nutrition goal {goal_id} for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Verify ownership
        goal = await goals_service.get_goal(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition goal not found"
            )
        
        # Delete goal
        await goals_service.delete_goal(goal_id)
        
        logger.info(f"Nutrition goal {goal_id} deleted successfully")
        return {"message": "Nutrition goal deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting nutrition goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete nutrition goal"
        )


@goals_router.post("/progress", response_model=GoalProgress)
async def log_goal_progress(
    progress_data: GoalProgress,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log progress for a nutrition goal.
    
    Args:
        progress_data: Goal progress data
        current_user: Authenticated user information
    
    Returns:
        Logged goal progress
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Logging goal progress for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Log progress
        logged_progress = await goals_service.log_progress(
            user_id=user_id,
            progress_data=progress_data
        )
        
        logger.info(f"Goal progress logged successfully for user {user_id}")
        return logged_progress
        
    except Exception as e:
        logger.error(f"Error logging goal progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log goal progress"
        )


@goals_router.get("/progress/{goal_id}", response_model=List[GoalProgress])
async def get_goal_progress(
    goal_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get progress history for a nutrition goal.
    
    Args:
        goal_id: Goal identifier
        start_date: Start date for progress history
        end_date: End date for progress history
        current_user: Authenticated user information
    
    Returns:
        List of goal progress entries
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting progress for goal {goal_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Verify ownership
        goal = await goals_service.get_goal(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition goal not found"
            )
        
        # Get progress
        progress = await goals_service.get_goal_progress(
            goal_id=goal_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goal progress"
        )


@goals_router.get("/summary/{goal_id}", response_model=GoalSummary)
async def get_goal_summary(
    goal_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a summary of progress for a nutrition goal.
    
    Args:
        goal_id: Goal identifier
        current_user: Authenticated user information
    
    Returns:
        Goal progress summary
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting summary for goal {goal_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Verify ownership
        goal = await goals_service.get_goal(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition goal not found"
            )
        
        # Get summary
        summary = await goals_service.get_goal_summary(goal_id)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goal summary"
        )


@goals_router.get("/recommendations/{goal_id}", response_model=List[GoalRecommendation])
async def get_goal_recommendations(
    goal_id: str,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get recommendations for achieving a nutrition goal.
    
    Args:
        goal_id: Goal identifier
        limit: Maximum number of recommendations
        current_user: Authenticated user information
    
    Returns:
        List of goal recommendations
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Getting recommendations for goal {goal_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Verify ownership
        goal = await goals_service.get_goal(goal_id)
        if not goal or goal.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition goal not found"
            )
        
        # Get recommendations
        recommendations = await goals_service.get_goal_recommendations(
            goal_id=goal_id,
            limit=limit
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goal recommendations"
        )


@goals_router.post("/recommendation-feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    feedback: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback for a goal recommendation.
    
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
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Submit feedback
        result = await goals_service.submit_recommendation_feedback(
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


@goals_router.get("/analytics/{user_id}")
async def get_goals_analytics(
    user_id: str,
    timeframe: str = "30_days",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get analytics and insights for user's nutrition goals.
    
    Args:
        user_id: User identifier
        timeframe: Analysis timeframe
        current_user: Authenticated user information
    
    Returns:
        Goals analytics and insights
    """
    try:
        # Verify user can access this data
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting goals analytics for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Get analytics
        analytics = await goals_service.get_goals_analytics(
            user_id=user_id,
            timeframe=timeframe
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goals analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goals analytics"
        )


@goals_router.post("/calculate-targets")
async def calculate_nutrition_targets(
    user_data: Dict[str, Any],
    goal_type: GoalType,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Calculate recommended nutrition targets based on user data and goal type.
    
    Args:
        user_data: User information (age, weight, height, activity level, etc.)
        goal_type: Type of nutrition goal
        current_user: Authenticated user information
    
    Returns:
        Calculated nutrition targets
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"Calculating nutrition targets for user {user_id}")
        
        # Initialize goals service
        goals_service = GoalsService()
        
        # Calculate targets
        targets = await goals_service.calculate_nutrition_targets(
            user_id=user_id,
            user_data=user_data,
            goal_type=goal_type
        )
        
        return targets
        
    except Exception as e:
        logger.error(f"Error calculating nutrition targets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate nutrition targets"
        ) 