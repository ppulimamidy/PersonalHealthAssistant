import os
import logging
import aiohttp
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from apps.nutrition.services.food_recognition_service import FoodRecognitionService
from apps.nutrition.services.recommendations_service import RecommendationsService
from apps.nutrition.services.user_profile_client import UserProfileClient
from apps.nutrition.repositories.nutrition_repository import NutritionRepository
from common.database.connection import get_db_manager
from common.utils.logging import get_logger

logger = get_logger(__name__)

class NutritionService:
    """
    Service for nutrition analysis, meal logging, and nutrition data management.
    """
    def __init__(self):
        self.food_recognition_service = FoodRecognitionService()
        self.recommendations_service = RecommendationsService()
        self.user_profile_client = UserProfileClient()
        
        # API Keys
        self.nutritionix_api_key = os.getenv("NUTRITIONIX_API_KEY")
        self.nutritionix_app_id = os.getenv("NUTRITIONIX_APP_ID")
        self.usda_api_key = os.getenv("USDA_API_KEY")
        
        # Service availability flags
        self.nutritionix_available = bool(self.nutritionix_api_key and self.nutritionix_app_id)
        self.usda_available = bool(self.usda_api_key)

    async def _get_repository(self) -> NutritionRepository:
        """Get database repository instance."""
        db_manager = get_db_manager()
        async_session_factory = db_manager.get_async_session_factory()
        async with async_session_factory() as session:
            return NutritionRepository(session)

    async def analyze_meal(self, user_id: str, meal_data: Dict[str, Any], token: str = None) -> Any:
        """
        Analyze a meal and return nutritional breakdown and recommendations.
        Steps:
        1. If image provided, recognize foods and estimate portions.
        2. Fetch nutrition data for each food item.
        3. Aggregate macro/micro nutrients and calories.
        4. Generate personalized recommendations using user profile data.
        """
        # Get user preferences if token is provided
        user_preferences = None
        if token:
            try:
                user_preferences = await self.user_profile_client.get_nutrition_preferences(user_id, token)
            except Exception as e:
                logger.warning(f"Failed to get user preferences: {e}")
        
        # 1. Food recognition (if image provided)
        food_items = meal_data.get("food_items", [])
        if "image" in meal_data:
            image_bytes = meal_data["image"]  # Should be bytes
            # Recognize foods in image
            recognized = await self.food_recognition_service.recognize_foods_in_image(image_bytes, user_id)
            # Estimate portion sizes
            food_items = await self.food_recognition_service.estimate_portion_size(image_bytes, recognized)
            # Optionally merge with user-provided food_items
        
        # 2. Fetch nutrition data for each food item
        nutrition_results = []
        for item in food_items:
            # Lookup nutrition info from local DB or external API
            nutrition_info = await self._fetch_nutrition_data(item)
            nutrition_results.append({**item, **nutrition_info})
        
        # 3. Aggregate nutrients
        aggregated = self._aggregate_nutrition(nutrition_results)
        
        # 4. Generate recommendations with user preferences
        recommendations = await self.recommendations_service.get_recommendations(
            user_id, 
            aggregated,
            user_preferences=user_preferences
        )
        
        # Compose response
        return {
            "food_items": nutrition_results,
            "totals": aggregated,
            "recommendations": recommendations,
            "user_preferences_used": user_preferences is not None
        }

    async def log_meal(self, user_id: str, meal_data: Dict[str, Any], token: str = None) -> Any:
        """
        Log a meal for the user and return the logged meal analysis.
        Steps:
        1. Analyze the meal (reuse analyze_meal).
        2. Store meal log in DB.
        3. Log nutrition to health tracking service.
        4. Return analysis.
        """
        try:
            # 1. Analyze meal
            analysis = await self.analyze_meal(user_id, meal_data, token)
            
            # 2. Store meal log in DB
            repository = await self._get_repository()
            
            meal_log_data = {
                "user_id": user_id,
                "recognition_result_id": meal_data.get("recognition_result_id"),
                "meal_type": meal_data.get("meal_type", "unknown"),
                "meal_name": meal_data.get("meal_name"),
                "meal_description": meal_data.get("meal_description"),
                "food_items": analysis["food_items"],
                "total_calories": analysis["totals"]["calories"],
                "total_protein_g": analysis["totals"]["protein_g"],
                "total_carbs_g": analysis["totals"]["carbs_g"],
                "total_fat_g": analysis["totals"]["fat_g"],
                "total_fiber_g": analysis["totals"]["fiber_g"],
                "total_sodium_mg": analysis["totals"]["sodium_mg"],
                "total_sugar_g": analysis["totals"]["sugar_g"],
                "micronutrients": analysis["totals"]["micronutrients"],
                "user_notes": meal_data.get("user_notes"),
                "mood_before": meal_data.get("mood_before"),
                "mood_after": meal_data.get("mood_after")
            }
            
            meal_log = await repository.create_meal_log(meal_log_data)
            
            # 3. Log nutrition to health tracking service (TODO)
            # TODO: POST nutrition data to health tracking microservice
            
            # 4. Return analysis with meal log ID
            analysis["meal_log_id"] = str(meal_log.id)
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to log meal: {e}")
            raise

    async def get_personalized_recommendations(self, user_id: str, token: str, nutrition_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get personalized nutrition recommendations based on user profile and preferences.
        """
        try:
            # Get user preferences
            user_preferences = await self.user_profile_client.get_nutrition_preferences(user_id, token)
            
            # If no nutrition data provided, get recent nutrition data
            if not nutrition_data:
                nutrition_data = await self.get_daily_nutrition(user_id, date.today())
            
            # Generate recommendations
            recommendations = await self.recommendations_service.get_recommendations(
                user_id,
                nutrition_data,
                user_preferences=user_preferences
            )
            
            return {
                "recommendations": recommendations,
                "user_preferences": user_preferences,
                "nutrition_data": nutrition_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get personalized recommendations: {e}")
            raise

    async def get_user_nutrition_summary(self, user_id: str, token: str, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive nutrition summary for a user including preferences and recent data.
        """
        try:
            # Get user preferences
            user_preferences = await self.user_profile_client.get_nutrition_preferences(user_id, token)
            
            # Get recent nutrition data
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            nutrition_history = await self.get_nutrition_history(user_id, start_date, end_date)
            
            # Calculate averages
            if nutrition_history:
                total_calories = sum(day.get("total_calories", 0) for day in nutrition_history)
                total_protein = sum(day.get("total_protein_g", 0) for day in nutrition_history)
                total_carbs = sum(day.get("total_carbs_g", 0) for day in nutrition_history)
                total_fat = sum(day.get("total_fat_g", 0) for day in nutrition_history)
                
                avg_calories = total_calories / len(nutrition_history)
                avg_protein = total_protein / len(nutrition_history)
                avg_carbs = total_carbs / len(nutrition_history)
                avg_fat = total_fat / len(nutrition_history)
            else:
                avg_calories = avg_protein = avg_carbs = avg_fat = 0
            
            return {
                "user_preferences": user_preferences,
                "nutrition_summary": {
                    "period_days": days,
                    "average_daily_calories": avg_calories,
                    "average_daily_protein_g": avg_protein,
                    "average_daily_carbs_g": avg_carbs,
                    "average_daily_fat_g": avg_fat,
                    "days_with_data": len(nutrition_history),
                    "recent_nutrition_data": nutrition_history
                },
                "recommendations": await self.recommendations_service.get_recommendations(
                    user_id,
                    {"calories": avg_calories, "protein": avg_protein, "carbs": avg_carbs, "fat": avg_fat},
                    user_preferences=user_preferences
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get nutrition summary: {e}")
            raise

    async def _fetch_nutrition_data(self, food_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch nutrition data for a food item from local cache, Nutritionix, or USDA.
        """
        food_name = food_item.get('name', '')
        portion_g = food_item.get('portion_g', 100)
        
        try:
            # First, check local database cache
            repository = await self._get_repository()
            cached_food = await repository.get_food_from_database(food_name)
            
            if cached_food:
                # Use cached data
                multiplier = portion_g / 100
                return {
                    "calories": int(cached_food.calories_per_100g * multiplier),
                    "protein_g": round(cached_food.protein_g_per_100g * multiplier, 1),
                    "carbs_g": round(cached_food.carbs_g_per_100g * multiplier, 1),
                    "fat_g": round(cached_food.fat_g_per_100g * multiplier, 1),
                    "fiber_g": round(cached_food.fiber_g_per_100g * multiplier, 1),
                    "sodium_mg": int(cached_food.sodium_mg_per_100g * multiplier),
                    "sugar_g": round(cached_food.sugar_g_per_100g * multiplier, 1),
                    "micronutrients": cached_food.micronutrients or {}
                }
            
            # Try Nutritionix first
            if self.nutritionix_available:
                try:
                    nutrition_data = await self._fetch_from_nutritionix(food_name, portion_g)
                    if nutrition_data:
                        # Cache the data
                        await self._cache_nutrition_data(food_name, nutrition_data, "nutritionix")
                        return nutrition_data
                except Exception as e:
                    logger.warning(f"Nutritionix API failed for {food_name}: {e}")
            
            # Fallback to USDA
            if self.usda_available:
                try:
                    nutrition_data = await self._fetch_from_usda(food_name, portion_g)
                    if nutrition_data:
                        # Cache the data
                        await self._cache_nutrition_data(food_name, nutrition_data, "usda")
                        return nutrition_data
                except Exception as e:
                    logger.warning(f"USDA API failed for {food_name}: {e}")
            
            # Fallback to mock data
            logger.warning(f"Using mock nutrition data for {food_name}")
            return self._get_mock_nutrition_data(portion_g)
            
        except Exception as e:
            logger.error(f"Failed to fetch nutrition data for {food_name}: {e}")
            return self._get_mock_nutrition_data(portion_g)

    async def _cache_nutrition_data(self, food_name: str, nutrition_data: Dict[str, Any], source: str):
        """Cache nutrition data in local database."""
        try:
            repository = await self._get_repository()
            
            # Convert nutrition data to per-100g format for caching
            portion_g = nutrition_data.get("portion_g", 100)
            multiplier = 100 / portion_g
            
            cache_data = {
                "food_name": food_name,
                "food_category": nutrition_data.get("category", "other"),
                "source": source,
                "calories_per_100g": nutrition_data.get("calories", 0) * multiplier,
                "protein_g_per_100g": nutrition_data.get("protein_g", 0) * multiplier,
                "carbs_g_per_100g": nutrition_data.get("carbs_g", 0) * multiplier,
                "fat_g_per_100g": nutrition_data.get("fat_g", 0) * multiplier,
                "fiber_g_per_100g": nutrition_data.get("fiber_g", 0) * multiplier,
                "sodium_mg_per_100g": nutrition_data.get("sodium_mg", 0) * multiplier,
                "sugar_g_per_100g": nutrition_data.get("sugar_g", 0) * multiplier,
                "micronutrients": nutrition_data.get("micronutrients", {})
            }
            
            await repository.cache_food_data(cache_data)
            logger.info(f"Cached nutrition data for {food_name} from {source}")
            
        except Exception as e:
            logger.error(f"Failed to cache nutrition data for {food_name}: {e}")

    async def _fetch_from_nutritionix(self, food_name: str, portion_g: int) -> Optional[Dict[str, Any]]:
        """Fetch nutrition data from Nutritionix API."""
        try:
            url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
            headers = {
                "x-app-id": self.nutritionix_app_id,
                "x-app-key": self.nutritionix_api_key,
                "x-remote-user-id": "0",
                "Content-Type": "application/json"
            }
            data = {
                "query": food_name,
                "timezone": "US/Eastern"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_nutritionix_response(result, portion_g)
                    else:
                        logger.warning(f"Nutritionix API returned {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Nutritionix API error: {e}")
            return None

    async def _fetch_from_usda(self, food_name: str, portion_g: int) -> Optional[Dict[str, Any]]:
        """Fetch nutrition data from USDA API."""
        try:
            url = f"https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {
                "api_key": self.usda_api_key,
                "query": food_name,
                "pageSize": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_usda_response(result, portion_g)
                    else:
                        logger.warning(f"USDA API returned {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"USDA API error: {e}")
            return None

    def _parse_nutritionix_response(self, data: Dict[str, Any], portion_g: int) -> Dict[str, Any]:
        """Parse Nutritionix API response."""
        try:
            if "foods" in data and data["foods"]:
                food = data["foods"][0]
                
                # Calculate multiplier based on portion
                serving_qty = food.get("serving_qty", 1)
                serving_unit = food.get("serving_unit", "g")
                multiplier = portion_g / (serving_qty * 100)  # Assume 100g per serving if unit is g
                
                return {
                    "calories": int(food.get("nf_calories", 0) * multiplier),
                    "protein_g": round(food.get("nf_protein", 0) * multiplier, 1),
                    "carbs_g": round(food.get("nf_total_carbohydrate", 0) * multiplier, 1),
                    "fat_g": round(food.get("nf_total_fat", 0) * multiplier, 1),
                    "fiber_g": round(food.get("nf_dietary_fiber", 0) * multiplier, 1),
                    "sodium_mg": int(food.get("nf_sodium", 0) * multiplier),
                    "sugar_g": round(food.get("nf_sugars", 0) * multiplier, 1),
                    "category": food.get("food_category", "other"),
                    "portion_g": portion_g,
                    "micronutrients": {}
                }
            return {}
        except Exception as e:
            logger.error(f"Error parsing Nutritionix response: {e}")
            return {}

    def _parse_usda_response(self, data: Dict[str, Any], portion_g: int) -> Dict[str, Any]:
        """Parse USDA API response."""
        try:
            if "foods" in data and data["foods"]:
                food = data["foods"][0]
                nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}
                
                # Calculate multiplier based on portion
                multiplier = portion_g / 100
                
                return {
                    "calories": int(nutrients.get("Energy", 0) * multiplier),
                    "protein_g": round(nutrients.get("Protein", 0) * multiplier, 1),
                    "carbs_g": round(nutrients.get("Carbohydrate, by difference", 0) * multiplier, 1),
                    "fat_g": round(nutrients.get("Total lipid (fat)", 0) * multiplier, 1),
                    "fiber_g": round(nutrients.get("Fiber, total dietary", 0) * multiplier, 1),
                    "sodium_mg": int(nutrients.get("Sodium, Na", 0) * multiplier),
                    "sugar_g": round(nutrients.get("Sugars, total including NLEA", 0) * multiplier, 1),
                    "category": food.get("foodCategory", "other"),
                    "portion_g": portion_g,
                    "micronutrients": {}
                }
            return {}
        except Exception as e:
            logger.error(f"Error parsing USDA response: {e}")
            return {}

    def _get_mock_nutrition_data(self, portion_g: int) -> Dict[str, Any]:
        """Get mock nutrition data for testing."""
        multiplier = portion_g / 100
        return {
            "calories": int(100 * multiplier),
            "protein_g": round(5.0 * multiplier, 1),
            "carbs_g": round(20.0 * multiplier, 1),
            "fat_g": round(2.0 * multiplier, 1),
            "fiber_g": round(3.0 * multiplier, 1),
            "sodium_mg": int(200 * multiplier),
            "sugar_g": round(4.0 * multiplier, 1),
            "category": "other",
            "portion_g": portion_g,
            "micronutrients": {
                "vitamin_c_mg": 10.0 * multiplier,
                "iron_mg": 1.0 * multiplier,
                "calcium_mg": 50.0 * multiplier
            }
        }

    def _aggregate_nutrition(self, nutrition_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate nutrition data from multiple food items."""
        total_calories = sum(item.get("calories", 0) for item in nutrition_results)
        total_protein = sum(item.get("protein_g", 0) for item in nutrition_results)
        total_carbs = sum(item.get("carbs_g", 0) for item in nutrition_results)
        total_fat = sum(item.get("fat_g", 0) for item in nutrition_results)
        total_fiber = sum(item.get("fiber_g", 0) for item in nutrition_results)
        total_sodium = sum(item.get("sodium_mg", 0) for item in nutrition_results)
        total_sugar = sum(item.get("sugar_g", 0) for item in nutrition_results)
        
        # Aggregate micronutrients
        micronutrients = {}
        for item in nutrition_results:
            item_micronutrients = item.get("micronutrients", {})
            for nutrient, value in item_micronutrients.items():
                micronutrients[nutrient] = micronutrients.get(nutrient, 0) + value
        
        return {
            "calories": total_calories,
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
            "fiber_g": round(total_fiber, 1),
            "sodium_mg": total_sodium,
            "sugar_g": round(total_sugar, 1),
            "micronutrients": micronutrients
        }

    async def get_daily_nutrition(self, user_id: str, target_date: date) -> Any:
        """Get daily nutrition summary for a user."""
        repository = await self._get_repository()
        return await repository.get_daily_nutrition_summary(user_id, target_date)

    async def get_nutrition_history(self, user_id: str, start_date: date, end_date: date) -> List[Any]:
        """Get nutrition history for a user over a date range."""
        repository = await self._get_repository()
        return await repository.get_user_meal_logs(user_id, start_date, end_date)

    async def create_food_item(self, user_id: str, food_data: Dict[str, Any]) -> Any:
        """Create a custom food item for a user."""
        repository = await self._get_repository()
        return await repository.cache_food_data(food_data)

    async def get_food_item(self, food_id: str) -> Any:
        """Get a specific food item by ID."""
        repository = await self._get_repository()
        return await repository.get_food_from_database(food_id)

    async def search_foods(self, query: str, category: Optional[str], limit: int) -> List[Any]:
        """Search for foods in the database."""
        repository = await self._get_repository()
        # This would need to be implemented in the repository
        return []

    async def calculate_nutrition(self, food_items: List[Dict[str, Any]]) -> Any:
        """Calculate nutrition for a list of food items."""
        nutrition_results = []
        for item in food_items:
            nutrition_info = await self._fetch_nutrition_data(item)
            nutrition_results.append({**item, **nutrition_info})
        
        return {
            "food_items": nutrition_results,
            "totals": self._aggregate_nutrition(nutrition_results)
        }

    async def get_nutritional_trends(self, user_id: str, nutrient: str, period: str) -> Any:
        """Get nutritional trends for a user."""
        try:
            end_date = date.today()
            if period == "7_days":
                start_date = end_date - timedelta(days=7)
            elif period == "30_days":
                start_date = end_date - timedelta(days=30)
            elif period == "90_days":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=7)
            
            nutrition_history = await self.get_nutrition_history(user_id, start_date, end_date)
            
            # Calculate trends
            trends = []
            for day_data in nutrition_history:
                trends.append({
                    "date": day_data.timestamp.date().isoformat(),
                    "value": day_data.get(f"total_{nutrient}", 0)
                })
            
            return {
                "user_id": user_id,
                "nutrient": nutrient,
                "period": period,
                "trends": trends
            }
            
        except Exception as e:
            logger.error(f"Failed to get nutritional trends: {e}")
            raise

    async def delete_meal(self, meal_id: str) -> None:
        """Delete a meal log."""
        repository = await self._get_repository()
        await repository.delete_meal_log(meal_id)

    async def get_nutritional_insights(self, user_id: str, timeframe: str) -> Any:
        """Get nutritional insights for a user."""
        try:
            # Get nutrition data for the timeframe
            end_date = date.today()
            if timeframe == "week":
                start_date = end_date - timedelta(days=7)
            elif timeframe == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            nutrition_history = await self.get_nutrition_history(user_id, start_date, end_date)
            
            # Calculate insights
            if nutrition_history:
                total_calories = sum(day.total_calories for day in nutrition_history)
                total_protein = sum(day.total_protein_g for day in nutrition_history)
                total_carbs = sum(day.total_carbs_g for day in nutrition_history)
                total_fat = sum(day.total_fat_g for day in nutrition_history)
                
                avg_calories = total_calories / len(nutrition_history)
                avg_protein = total_protein / len(nutrition_history)
                avg_carbs = total_carbs / len(nutrition_history)
                avg_fat = total_fat / len(nutrition_history)
                
                insights = {
                    "timeframe": timeframe,
                    "average_daily_calories": avg_calories,
                    "average_daily_protein_g": avg_protein,
                    "average_daily_carbs_g": avg_carbs,
                    "average_daily_fat_g": avg_fat,
                    "days_analyzed": len(nutrition_history),
                    "recommendations": []
                }
                
                # Generate insights based on averages
                if avg_calories > 2500:
                    insights["recommendations"].append("Consider reducing daily calorie intake")
                if avg_protein < 50:
                    insights["recommendations"].append("Increase protein intake for better muscle health")
                if avg_carbs > 300:
                    insights["recommendations"].append("Consider reducing carbohydrate intake")
                
                return insights
            else:
                return {
                    "timeframe": timeframe,
                    "message": "No nutrition data available for this timeframe"
                }
                
        except Exception as e:
            logger.error(f"Failed to get nutritional insights: {e}")
            raise 