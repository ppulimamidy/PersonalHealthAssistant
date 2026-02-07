"""
Goals Service

Handles nutrition goal management, tracking, and recommendations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from common.database.connection import get_db_manager
from common.utils.logging import get_logger
from apps.nutrition.models.database_models import NutritionGoal
from apps.nutrition.services.user_profile_client import UserProfileClient

logger = get_logger(__name__)


class GoalsService:
    """Service for managing nutrition goals."""
    
    def __init__(self):
        self.user_profile_client = UserProfileClient()
    
    async def create_goal(self, user_id: str, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new nutrition goal for a user."""
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            
            async with async_session_factory() as session:
                goal = NutritionGoal(
                    user_id=user_id,
                    goal_name=goal_data.get("goal_name"),
                    goal_type=goal_data.get("goal_type"),
                    goal_description=goal_data.get("goal_description"),
                    target_calories=goal_data.get("target_calories"),
                    target_protein_g=goal_data.get("target_protein_g"),
                    target_carbs_g=goal_data.get("target_carbs_g"),
                    target_fat_g=goal_data.get("target_fat_g"),
                    target_fiber_g=goal_data.get("target_fiber_g"),
                    target_sodium_mg=goal_data.get("target_sodium_mg"),
                    start_date=goal_data.get("start_date"),
                    target_date=goal_data.get("target_date"),
                    is_active=True
                )
                
                session.add(goal)
                await session.commit()
                await session.refresh(goal)
                
                logger.info(f"Created nutrition goal for user {user_id}")
                return {
                    "id": str(goal.id),
                    "user_id": goal.user_id,
                    "goal_name": goal.goal_name,
                    "goal_type": goal.goal_type,
                    "is_active": goal.is_active,
                    "created_at": goal.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create goal: {e}")
            raise
    
    async def get_user_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all goals for a user."""
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            
            async with async_session_factory() as session:
                result = await session.execute(
                    select(NutritionGoal).where(NutritionGoal.user_id == user_id)
                )
                goals = result.scalars().all()
                
                return [
                    {
                        "id": str(goal.id),
                        "goal_name": goal.goal_name,
                        "goal_type": goal.goal_type,
                        "goal_description": goal.goal_description,
                        "is_active": goal.is_active,
                        "target_calories": goal.target_calories,
                        "target_protein_g": goal.target_protein_g,
                        "target_carbs_g": goal.target_carbs_g,
                        "target_fat_g": goal.target_fat_g,
                        "target_fiber_g": goal.target_fiber_g,
                        "target_sodium_mg": goal.target_sodium_mg,
                        "start_date": goal.start_date.isoformat() if goal.start_date else None,
                        "target_date": goal.target_date.isoformat() if goal.target_date else None,
                        "progress_percentage": goal.progress_percentage,
                        "created_at": goal.created_at.isoformat(),
                        "updated_at": goal.updated_at.isoformat()
                    }
                    for goal in goals
                ]
                
        except Exception as e:
            logger.error(f"Failed to get user goals: {e}")
            raise
    
    async def get_goal(self, goal_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific goal by ID."""
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            
            async with async_session_factory() as session:
                result = await session.execute(
                    select(NutritionGoal).where(
                        NutritionGoal.id == goal_id,
                        NutritionGoal.user_id == user_id
                    )
                )
                goal = result.scalar_one_or_none()
                
                if not goal:
                    return None
                
                return {
                    "id": str(goal.id),
                    "goal_name": goal.goal_name,
                    "goal_type": goal.goal_type,
                    "goal_description": goal.goal_description,
                    "is_active": goal.is_active,
                    "target_calories": goal.target_calories,
                    "target_protein_g": goal.target_protein_g,
                    "target_carbs_g": goal.target_carbs_g,
                    "target_fat_g": goal.target_fat_g,
                    "target_fiber_g": goal.target_fiber_g,
                    "target_sodium_mg": goal.target_sodium_mg,
                    "start_date": goal.start_date.isoformat() if goal.start_date else None,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "progress_percentage": goal.progress_percentage,
                    "created_at": goal.created_at.isoformat(),
                    "updated_at": goal.updated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get goal: {e}")
            raise
    
    async def update_goal(self, goal_id: str, user_id: str, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a nutrition goal."""
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            
            async with async_session_factory() as session:
                result = await session.execute(
                    select(NutritionGoal).where(
                        NutritionGoal.id == goal_id,
                        NutritionGoal.user_id == user_id
                    )
                )
                goal = result.scalar_one_or_none()
                
                if not goal:
                    raise ValueError("Goal not found")
                
                # Update fields
                for key, value in goal_data.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                
                goal.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(goal)
                
                logger.info(f"Updated goal {goal_id} for user {user_id}")
                return {
                    "id": str(goal.id),
                    "goal_name": goal.goal_name,
                    "goal_type": goal.goal_type,
                    "is_active": goal.is_active,
                    "updated_at": goal.updated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to update goal: {e}")
            raise
    
    async def delete_goal(self, goal_id: str, user_id: str) -> bool:
        """Delete a nutrition goal."""
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            
            async with async_session_factory() as session:
                result = await session.execute(
                    delete(NutritionGoal).where(
                        NutritionGoal.id == goal_id,
                        NutritionGoal.user_id == user_id
                    )
                )
                await session.commit()
                
                logger.info(f"Deleted goal {goal_id} for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete goal: {e}")
            raise
    
    async def update_goal_progress(self, goal_id: str, user_id: str, progress_percentage: float) -> Dict[str, Any]:
        """Update the progress percentage of a goal."""
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            
            async with async_session_factory() as session:
                result = await session.execute(
                    update(NutritionGoal)
                    .where(
                        NutritionGoal.id == goal_id,
                        NutritionGoal.user_id == user_id
                    )
                    .values(
                        progress_percentage=progress_percentage,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
                
                logger.info(f"Updated progress for goal {goal_id}: {progress_percentage}%")
                return {
                    "goal_id": goal_id,
                    "progress_percentage": progress_percentage,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to update goal progress: {e}")
            raise
    
    async def get_goal_recommendations(self, user_id: str, token: str) -> List[Dict[str, Any]]:
        """Get personalized goal recommendations based on user profile."""
        try:
            # Get user preferences
            user_prefs = await self.user_profile_client.get_nutrition_preferences(user_id, token)
            
            # Get current goals
            current_goals = await self.get_user_goals(user_id)
            active_goals = [goal for goal in current_goals if goal["is_active"]]
            
            recommendations = []
            
            # If no active goals, suggest creating one
            if not active_goals:
                recommendations.append({
                    "type": "create_goal",
                    "title": "Set Your First Nutrition Goal",
                    "description": "Start your nutrition journey by setting a specific goal",
                    "priority": "high",
                    "suggested_goals": [
                        {
                            "goal_type": "weight_loss",
                            "goal_name": "Healthy Weight Loss",
                            "description": "Lose weight gradually and sustainably"
                        },
                        {
                            "goal_type": "muscle_gain",
                            "goal_name": "Build Muscle",
                            "description": "Increase muscle mass and strength"
                        },
                        {
                            "goal_type": "maintenance",
                            "goal_name": "Maintain Health",
                            "description": "Maintain current weight and improve overall health"
                        }
                    ]
                })
            
            # Suggest goal adjustments based on user preferences
            if user_prefs.get("health_goals"):
                for health_goal in user_prefs["health_goals"]:
                    recommendations.append({
                        "type": "goal_adjustment",
                        "title": f"Optimize for {health_goal}",
                        "description": f"Adjust your nutrition goals to better support {health_goal}",
                        "priority": "medium"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get goal recommendations: {e}")
            return []
    
    async def calculate_goal_progress(self, user_id: str, goal_id: str) -> Dict[str, Any]:
        """Calculate progress towards a specific goal."""
        try:
            goal = await self.get_goal(goal_id, user_id)
            if not goal:
                raise ValueError("Goal not found")
            
            # This would typically involve comparing current nutrition data
            # with goal targets. For now, return a placeholder calculation.
            
            progress = {
                "goal_id": goal_id,
                "current_progress": goal.get("progress_percentage", 0.0),
                "target_calories": goal.get("target_calories"),
                "target_protein_g": goal.get("target_protein_g"),
                "target_carbs_g": goal.get("target_carbs_g"),
                "target_fat_g": goal.get("target_fat_g"),
                "last_updated": goal.get("updated_at"),
                "days_remaining": None
            }
            
            # Calculate days remaining if target date is set
            if goal.get("target_date"):
                target_date = datetime.fromisoformat(goal["target_date"]).date()
                days_remaining = (target_date - date.today()).days
                progress["days_remaining"] = max(0, days_remaining)
            
            return progress
            
        except Exception as e:
            logger.error(f"Failed to calculate goal progress: {e}")
            raise 