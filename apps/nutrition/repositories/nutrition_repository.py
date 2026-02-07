"""
Nutrition Repository

Database operations for nutrition service data management.
"""

import logging
from datetime import datetime, date, timedelta, time
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from apps.nutrition.models.database_models import (
    FoodRecognitionResult, UserCorrection, MealLog, NutritionGoal,
    FoodDatabase, ModelPerformance, UserPreferences
)

logger = logging.getLogger(__name__)


class NutritionRepository:
    """Repository for nutrition-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    # Food Recognition Results
    async def create_recognition_result(self, recognition_data: Dict[str, Any]) -> FoodRecognitionResult:
        """Create a new food recognition result."""
        try:
            recognition_result = FoodRecognitionResult(**recognition_data)
            self.session.add(recognition_result)
            await self.session.commit()
            await self.session.refresh(recognition_result)
            return recognition_result
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create recognition result: {e}")
            raise

    async def get_recognition_result(self, recognition_id: str) -> Optional[FoodRecognitionResult]:
        """Get a recognition result by ID."""
        try:
            query = select(FoodRecognitionResult).where(
                FoodRecognitionResult.recognition_id == recognition_id
            ).options(selectinload(FoodRecognitionResult.corrections))
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get recognition result: {e}")
            raise

    async def get_user_recognition_history(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[FoodRecognitionResult]:
        """Get user's recognition history."""
        try:
            query = select(FoodRecognitionResult).where(
                FoodRecognitionResult.user_id == user_id
            ).order_by(
                FoodRecognitionResult.timestamp.desc()
            ).offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recognition history: {e}")
            raise

    async def update_recognition_result(
        self, 
        recognition_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[FoodRecognitionResult]:
        """Update a recognition result."""
        try:
            query = update(FoodRecognitionResult).where(
                FoodRecognitionResult.recognition_id == recognition_id
            ).values(**update_data)
            
            await self.session.execute(query)
            await self.session.commit()
            
            return await self.get_recognition_result(recognition_id)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update recognition result: {e}")
            raise

    # User Corrections
    async def create_user_correction(self, correction_data: Dict[str, Any]) -> UserCorrection:
        """Create a new user correction."""
        try:
            correction = UserCorrection(**correction_data)
            self.session.add(correction)
            await self.session.commit()
            await self.session.refresh(correction)
            return correction
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create user correction: {e}")
            raise

    async def get_corrections_for_recognition(
        self, 
        recognition_result_id: str
    ) -> List[UserCorrection]:
        """Get all corrections for a recognition result."""
        try:
            query = select(UserCorrection).where(
                UserCorrection.recognition_result_id == recognition_result_id
            ).order_by(UserCorrection.timestamp.desc())
            
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get corrections: {e}")
            raise

    # Meal Logs
    async def create_meal_log(self, meal_data: Dict[str, Any]) -> MealLog:
        """Create a new meal log."""
        try:
            meal_log = MealLog(**meal_data)
            self.session.add(meal_log)
            await self.session.commit()
            await self.session.refresh(meal_log)
            return meal_log
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create meal log: {e}")
            raise

    async def get_meal_log(self, meal_id: str) -> Optional[MealLog]:
        """Get a meal log by ID."""
        try:
            query = select(MealLog).where(MealLog.id == meal_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get meal log: {e}")
            raise

    async def get_user_meal_logs(
        self, 
        user_id: str, 
        start_date: date, 
        end_date: date
    ) -> List[MealLog]:
        """Get user's meal logs for a date range (all times in each day)."""
        try:
            start_datetime = datetime.combine(start_date, time.min)
            end_datetime = datetime.combine(end_date, time.max)
            query = select(MealLog).where(
                and_(
                    MealLog.user_id == user_id,
                    MealLog.timestamp >= start_datetime,
                    MealLog.timestamp <= end_datetime
                )
            ).order_by(MealLog.timestamp.desc())
            result = await self.session.execute(query)
            meals = result.scalars().all()
            return [
                {
                    "id": str(meal.id),
                    "meal_type": meal.meal_type,
                    "meal_name": meal.meal_name,
                    "meal_description": meal.meal_description,
                    "food_items": meal.food_items,
                    "total_calories": meal.total_calories,
                    "total_protein_g": meal.total_protein_g,
                    "total_carbs_g": meal.total_carbs_g,
                    "total_fat_g": meal.total_fat_g,
                    "total_fiber_g": meal.total_fiber_g,
                    "total_sodium_mg": meal.total_sodium_mg,
                    "total_sugar_g": meal.total_sugar_g,
                    "micronutrients": meal.micronutrients,
                    "user_notes": meal.user_notes,
                    "mood_before": meal.mood_before,
                    "mood_after": meal.mood_after,
                    "timestamp": meal.timestamp.isoformat() if meal.timestamp else None,
                }
                for meal in meals
            ]
        except Exception as e:
            logger.error(f"Failed to get meal logs: {e}")
            raise

    async def get_daily_nutrition_summary(
        self, 
        user_id: str, 
        target_date: date
    ) -> Dict[str, Any]:
        """Get daily nutrition summary for a user (all times in the day)."""
        try:
            start_datetime = datetime.combine(target_date, time.min)
            end_datetime = datetime.combine(target_date, time.max)
            # Get all meals for the day
            meals = await self.get_user_meal_logs(user_id, target_date, target_date)
            
            # Aggregate nutrition data
            total_calories = sum(meal["total_calories"] for meal in meals)
            total_protein = sum(meal["total_protein_g"] for meal in meals)
            total_carbs = sum(meal["total_carbs_g"] for meal in meals)
            total_fat = sum(meal["total_fat_g"] for meal in meals)
            total_fiber = sum(meal["total_fiber_g"] for meal in meals)
            total_sodium = sum(meal["total_sodium_mg"] for meal in meals)
            total_sugar = sum(meal["total_sugar_g"] for meal in meals)
            
            # Aggregate micronutrients
            micronutrients = {}
            for meal in meals:
                if meal["micronutrients"]:
                    for nutrient, value in meal["micronutrients"].items():
                        micronutrients[nutrient] = micronutrients.get(nutrient, 0) + value
            
            return {
                "date": target_date.isoformat(),
                "total_calories": total_calories,
                "total_protein_g": total_protein,
                "total_carbs_g": total_carbs,
                "total_fat_g": total_fat,
                "total_fiber_g": total_fiber,
                "total_sodium_mg": total_sodium,
                "total_sugar_g": total_sugar,
                "micronutrients": micronutrients,
                "meals": meals,
                "meal_count": len(meals)
            }
        except Exception as e:
            logger.error(f"Failed to get daily nutrition summary: {e}")
            raise

    async def delete_meal_log(self, meal_id: str) -> bool:
        """Delete a meal log."""
        try:
            query = delete(MealLog).where(MealLog.id == meal_id)
            result = await self.session.execute(query)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete meal log: {e}")
            raise

    # Nutrition Goals
    async def create_nutrition_goal(self, goal_data: Dict[str, Any]) -> NutritionGoal:
        """Create a new nutrition goal."""
        try:
            goal = NutritionGoal(**goal_data)
            self.session.add(goal)
            await self.session.commit()
            await self.session.refresh(goal)
            return goal
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create nutrition goal: {e}")
            raise

    async def get_user_goals(self, user_id: str, active_only: bool = True) -> List[NutritionGoal]:
        """Get user's nutrition goals."""
        try:
            query = select(NutritionGoal).where(NutritionGoal.user_id == user_id)
            if active_only:
                query = query.where(NutritionGoal.is_active == True)
            
            query = query.order_by(NutritionGoal.created_at.desc())
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get user goals: {e}")
            raise

    async def update_goal_progress(self, goal_id: str, progress_percentage: float) -> Optional[NutritionGoal]:
        """Update goal progress."""
        try:
            query = update(NutritionGoal).where(
                NutritionGoal.id == goal_id
            ).values(progress_percentage=progress_percentage)
            
            await self.session.execute(query)
            await self.session.commit()
            
            # Return updated goal
            result = await self.session.execute(
                select(NutritionGoal).where(NutritionGoal.id == goal_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update goal progress: {e}")
            raise

    # Food Database
    async def get_food_from_database(self, food_name: str) -> Optional[FoodDatabase]:
        """Get food from local database."""
        try:
            query = select(FoodDatabase).where(
                FoodDatabase.food_name.ilike(f"%{food_name}%")
            ).order_by(FoodDatabase.access_count.desc()).limit(1)
            
            result = await self.session.execute(query)
            food = result.scalar_one_or_none()
            
            if food:
                # Update access count and last accessed
                food.access_count += 1
                food.last_accessed = datetime.utcnow()
                await self.session.commit()
            
            return food
        except Exception as e:
            logger.error(f"Failed to get food from database: {e}")
            raise

    async def cache_food_data(self, food_data: Dict[str, Any]) -> FoodDatabase:
        """Cache food data in local database."""
        try:
            food = FoodDatabase(**food_data)
            self.session.add(food)
            await self.session.commit()
            await self.session.refresh(food)
            return food
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to cache food data: {e}")
            raise

    # User Preferences
    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences."""
        try:
            query = select(UserPreferences).where(UserPreferences.user_id == user_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            raise

    async def create_or_update_preferences(
        self, 
        user_id: str, 
        preferences_data: Dict[str, Any]
    ) -> UserPreferences:
        """Create or update user preferences."""
        try:
            existing = await self.get_user_preferences(user_id)
            if existing:
                # Update existing preferences
                for key, value in preferences_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                await self.session.commit()
                await self.session.refresh(existing)
                return existing
            else:
                # Create new preferences
                preferences_data["user_id"] = user_id
                preferences = UserPreferences(**preferences_data)
                self.session.add(preferences)
                await self.session.commit()
                await self.session.refresh(preferences)
                return preferences
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create/update preferences: {e}")
            raise

    # Model Performance
    async def log_model_performance(self, performance_data: Dict[str, Any]) -> ModelPerformance:
        """Log model performance metrics."""
        try:
            performance = ModelPerformance(**performance_data)
            self.session.add(performance)
            await self.session.commit()
            await self.session.refresh(performance)
            return performance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to log model performance: {e}")
            raise

    async def get_model_performance_stats(
        self, 
        model_name: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get model performance statistics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(
                func.avg(ModelPerformance.accuracy).label("avg_accuracy"),
                func.avg(ModelPerformance.processing_time_ms).label("avg_processing_time"),
                func.avg(ModelPerformance.success_rate).label("avg_success_rate"),
                func.avg(ModelPerformance.user_satisfaction_score).label("avg_satisfaction"),
                func.count(ModelPerformance.id).label("total_requests")
            ).where(
                and_(
                    ModelPerformance.model_name == model_name,
                    ModelPerformance.timestamp >= cutoff_date
                )
            )
            
            result = await self.session.execute(query)
            stats = result.fetchone()
            
            return {
                "model_name": model_name,
                "period_days": days,
                "average_accuracy": float(stats.avg_accuracy) if stats.avg_accuracy else 0,
                "average_processing_time_ms": float(stats.avg_processing_time) if stats.avg_processing_time else 0,
                "average_success_rate": float(stats.avg_success_rate) if stats.avg_success_rate else 0,
                "average_satisfaction": float(stats.avg_satisfaction) if stats.avg_satisfaction else 0,
                "total_requests": stats.total_requests or 0
            }
        except Exception as e:
            logger.error(f"Failed to get model performance stats: {e}")
            raise 