import os
import logging
import aiohttp
import ssl
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.exc import ProgrammingError, OperationalError

from apps.nutrition.services.food_recognition_service import FoodRecognitionService
from apps.nutrition.services.recommendations_service import RecommendationsService
from apps.nutrition.services.user_profile_client import UserProfileClient
from apps.nutrition.repositories.nutrition_repository import NutritionRepository
from common.database.connection import get_db_manager
from common.utils.logging import get_logger

logger = get_logger(__name__)


def _certifi_ssl_context() -> ssl.SSLContext:
    """
    Create an SSL context using certifi CA bundle.

    This avoids local dev issues where the Python runtime can't locate system CAs
    (common on macOS python.org installs).
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _looks_like_missing_table(exc: Exception) -> bool:
    """
    Return True if the exception looks like a missing table/schema.

    This happens in fresh dev environments where the Nutrition schema/tables
    haven't been migrated yet.
    """
    msg = str(exc) or ""
    return (
        "UndefinedTableError" in msg
        or "does not exist" in msg
        or "relation" in msg and "does not exist" in msg
    )


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
        self.openfoodfacts_available = True

    @asynccontextmanager
    async def _repository(self):
        """
        Yield a NutritionRepository with a live AsyncSession.

        Important: the previous implementation returned a repository bound to a session
        that was already closed (because it was created inside an `async with` block).
        """
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
        except Exception as e:
            logger.warning(f"Nutrition DB not available: {e}")
            yield None
            return

        async with async_session_factory() as session:
            yield NutritionRepository(session)

    async def analyze_meal(self, user_id: str, meal_data: Dict[str, Any], token: Optional[str] = None) -> Any:
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

    async def log_meal(self, user_id: str, meal_data: Dict[str, Any], token: Optional[str] = None) -> Any:
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
            async with self._repository() as repository:
                if repository is None:
                    logger.warning("Skipping meal log persistence (no DB available)")
                    analysis["meal_log_id"] = None
                    return analysis
            
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

    async def get_personalized_recommendations(
        self, user_id: str, token: str, nutrition_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
            
            nutrition_history: List[Dict[str, Any]] = []
            try:
                nutrition_history = await self.get_nutrition_history(user_id, start_date, end_date)
            except (ProgrammingError, OperationalError) as e:
                # Treat missing tables as "no data yet" for MVP
                if _looks_like_missing_table(e):
                    logger.warning("Nutrition tables not found yet; returning empty summary")
                    nutrition_history = []
                else:
                    raise
            
            # The repository currently returns meal logs, not daily aggregates.
            # For the MVP UI we want:
            # - per-day totals (for averages)
            # - per-day rows aggregated by meal_type (for a simple breakdown table)
            daily_totals: Dict[str, Dict[str, float]] = {}
            daily_by_meal_type: Dict[str, Dict[str, Dict[str, float]]] = {}
            daily_meal_type_counts: Dict[str, Dict[str, int]] = {}
            for meal in nutrition_history:
                ts = meal.get("timestamp") or ""
                day_key = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else None
                if not day_key:
                    continue

                meal_type = (meal.get("meal_type") or "unknown").strip() or "unknown"

                if day_key not in daily_totals:
                    daily_totals[day_key] = {
                        "total_calories": 0.0,
                        "total_protein_g": 0.0,
                        "total_carbs_g": 0.0,
                        "total_fat_g": 0.0,
                    }

                daily_totals[day_key]["total_calories"] += float(meal.get("total_calories", 0) or 0)
                daily_totals[day_key]["total_protein_g"] += float(meal.get("total_protein_g", 0) or 0)
                daily_totals[day_key]["total_carbs_g"] += float(meal.get("total_carbs_g", 0) or 0)
                daily_totals[day_key]["total_fat_g"] += float(meal.get("total_fat_g", 0) or 0)

                if day_key not in daily_by_meal_type:
                    daily_by_meal_type[day_key] = {}
                    daily_meal_type_counts[day_key] = {}

                if meal_type not in daily_by_meal_type[day_key]:
                    daily_by_meal_type[day_key][meal_type] = {
                        "total_calories": 0.0,
                        "total_protein_g": 0.0,
                        "total_carbs_g": 0.0,
                        "total_fat_g": 0.0,
                    }
                    daily_meal_type_counts[day_key][meal_type] = 0

                daily_by_meal_type[day_key][meal_type]["total_calories"] += float(meal.get("total_calories", 0) or 0)
                daily_by_meal_type[day_key][meal_type]["total_protein_g"] += float(meal.get("total_protein_g", 0) or 0)
                daily_by_meal_type[day_key][meal_type]["total_carbs_g"] += float(meal.get("total_carbs_g", 0) or 0)
                daily_by_meal_type[day_key][meal_type]["total_fat_g"] += float(meal.get("total_fat_g", 0) or 0)
                daily_meal_type_counts[day_key][meal_type] += 1

            daily_rows = [
                {
                    "date": day,
                    "total_calories": totals["total_calories"],
                    "total_protein_g": totals["total_protein_g"],
                    "total_carbs_g": totals["total_carbs_g"],
                    "total_fat_g": totals["total_fat_g"],
                }
                for day, totals in daily_totals.items()
            ]
            daily_rows.sort(key=lambda r: str(r.get("date") or ""), reverse=True)

            daily_breakdown_rows: List[Dict[str, Any]] = []
            for day in sorted(daily_totals.keys(), reverse=True):
                meal_type_rows: List[Dict[str, Any]] = []
                meal_types = sorted((daily_by_meal_type.get(day) or {}).keys())
                for mt in meal_types:
                    mt_totals = daily_by_meal_type[day][mt]
                    meal_type_rows.append(
                        {
                            "meal_type": mt,
                            "meal_count": int((daily_meal_type_counts.get(day) or {}).get(mt, 0)),
                            "total_calories": mt_totals["total_calories"],
                            "total_protein_g": mt_totals["total_protein_g"],
                            "total_carbs_g": mt_totals["total_carbs_g"],
                            "total_fat_g": mt_totals["total_fat_g"],
                        }
                    )

                day_totals = daily_totals[day]
                daily_breakdown_rows.append(
                    {
                        "date": day,
                        "rows": meal_type_rows,
                        "total": {
                            "total_calories": day_totals["total_calories"],
                            "total_protein_g": day_totals["total_protein_g"],
                            "total_carbs_g": day_totals["total_carbs_g"],
                            "total_fat_g": day_totals["total_fat_g"],
                        },
                    }
                )

            days_with_data = len(daily_rows)
            if days_with_data:
                total_calories = sum(float(d.get("total_calories", 0) or 0) for d in daily_rows)
                total_protein = sum(float(d.get("total_protein_g", 0) or 0) for d in daily_rows)
                total_carbs = sum(float(d.get("total_carbs_g", 0) or 0) for d in daily_rows)
                total_fat = sum(float(d.get("total_fat_g", 0) or 0) for d in daily_rows)

                avg_calories = total_calories / days_with_data
                avg_protein = total_protein / days_with_data
                avg_carbs = total_carbs / days_with_data
                avg_fat = total_fat / days_with_data
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
                    "days_with_data": days_with_data,
                    "recent_nutrition_data": daily_rows,
                    "daily_breakdown": daily_breakdown_rows,
                },
                "recommendations": await self.recommendations_service.get_recommendations(
                    user_id,
                    {
                        "calories": avg_calories,
                        "protein_g": avg_protein,
                        "carbs_g": avg_carbs,
                        "fat_g": avg_fat,
                    },
                    user_preferences=user_preferences
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get nutrition summary: {e}")
            # MVP-friendly: don't hard fail the entire page if nutrition tables aren't ready.
            if _looks_like_missing_table(e):
                return {
                    "user_preferences": {},
                    "nutrition_summary": {
                        "period_days": days,
                        "average_daily_calories": 0,
                        "average_daily_protein_g": 0,
                        "average_daily_carbs_g": 0,
                        "average_daily_fat_g": 0,
                        "days_with_data": 0,
                        "recent_nutrition_data": [],
                    },
                    "recommendations": [],
                }
            raise

    async def _fetch_nutrition_data(self, food_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch nutrition data for a food item from local cache, Nutritionix, or USDA.
        """
        food_name = food_item.get('name', '')
        portion_g = food_item.get('portion_g', 100)
        
        try:
            # First, check local database cache
            cached_food = None
            async with self._repository() as repository:
                if repository is not None:
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
                    "micronutrients": cached_food.micronutrients or {},
                    "nutrition_source": cached_food.source,
                }
            
            # Try Nutritionix first
            if self.nutritionix_available:
                try:
                    nutrition_data = await self._fetch_from_nutritionix(food_name, portion_g)
                    if nutrition_data:
                        # Cache the data
                        await self._cache_nutrition_data(food_name, nutrition_data, "nutritionix")
                        nutrition_data["nutrition_source"] = "nutritionix"
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
                        nutrition_data["nutrition_source"] = "usda"
                        return nutrition_data
                except Exception as e:
                    logger.warning(f"USDA API failed for {food_name}: {e}")

            # Fallback to OpenFoodFacts (no API key required)
            if self.openfoodfacts_available:
                try:
                    nutrition_data = await self._fetch_from_openfoodfacts(food_name, portion_g)
                    if nutrition_data:
                        await self._cache_nutrition_data(food_name, nutrition_data, "openfoodfacts")
                        nutrition_data["nutrition_source"] = "openfoodfacts"
                        return nutrition_data
                except Exception as e:
                    logger.warning(f"OpenFoodFacts lookup failed for {food_name}: {e}")
            
            # Fallback to a small built-in table for common foods (better than a generic 100 kcal/100g)
            builtin = self._get_builtin_nutrition_data(food_name=food_name, portion_g=portion_g)
            if builtin:
                builtin["nutrition_source"] = "builtin"
                return builtin

            # Final fallback to mock data
            logger.warning(f"Using mock nutrition data for {food_name}")
            mock = self._get_mock_nutrition_data(portion_g)
            mock["nutrition_source"] = "mock"
            return mock
            
        except Exception as e:
            logger.error(f"Failed to fetch nutrition data for {food_name}: {e}")
            mock = self._get_mock_nutrition_data(portion_g)
            mock["nutrition_source"] = "mock"
            return mock

    async def _cache_nutrition_data(self, food_name: str, nutrition_data: Dict[str, Any], source: str):
        """Cache nutrition data in local database."""
        try:
            async with self._repository() as repository:
                if repository is None:
                    return

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
                    "micronutrients": nutrition_data.get("micronutrients", {}),
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
            
            ssl_ctx = _certifi_ssl_context()
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, ssl=ssl_ctx) as response:
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
            
            ssl_ctx = _certifi_ssl_context()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, ssl=ssl_ctx) as response:
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

                # Nutritionix gives nutrients per "serving" and provides serving_weight_grams.
                serving_weight_g = food.get("serving_weight_grams")
                if serving_weight_g:
                    base_g = float(serving_weight_g)
                else:
                    # Best-effort fallback
                    serving_qty = food.get("serving_qty", 1) or 1
                    serving_unit = (food.get("serving_unit") or "g").lower()
                    base_g = float(serving_qty) if serving_unit == "g" else 100.0

                multiplier = (float(portion_g) / base_g) if base_g > 0 else (float(portion_g) / 100.0)

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

    def _get_builtin_nutrition_data(self, food_name: str, portion_g: int) -> Optional[Dict[str, Any]]:
        """Best-effort nutrition values for common foods (per 100g), scaled to portion."""
        name = (food_name or "").strip().lower()
        if not name:
            return None

        # Very small, high-signal list for MVP robustness.
        # Values are approximate kcal per 100g for common "raw/cooked generic" items.
        kcal_per_100g_map = {
            "chicken": 165.0,
            "chicken breast": 165.0,
            "egg": 155.0,
            "rice": 130.0,  # cooked white rice
            "oatmeal": 68.0,  # cooked, water
            "banana": 89.0,
            "apple": 52.0,
        }

        kcal_100g = None
        # direct match first
        if name in kcal_per_100g_map:
            kcal_100g = kcal_per_100g_map[name]
        else:
            # partial match
            for k, v in kcal_per_100g_map.items():
                if k in name:
                    kcal_100g = v
                    break

        if kcal_100g is None:
            return None

        multiplier = float(portion_g) / 100.0
        calories = int(kcal_100g * multiplier)

        return {
            "calories": calories,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sodium_mg": 0,
            "sugar_g": 0.0,
            "category": "other",
            "portion_g": portion_g,
            "micronutrients": {},
        }

    async def _fetch_from_openfoodfacts(self, food_name: str, portion_g: int) -> Optional[Dict[str, Any]]:
        """Fetch nutrition data from OpenFoodFacts (no API key)."""
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                "search_terms": food_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 1,
            }

            ssl_ctx = _certifi_ssl_context()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, ssl=ssl_ctx) as response:
                    if response.status != 200:
                        logger.warning(f"OpenFoodFacts returned {response.status}")
                        return None

                    data = await response.json()
                    products = data.get("products") or []
                    if not products:
                        return None

                    prod = products[0] or {}
                    nutr = prod.get("nutriments") or {}

                    def _num(x) -> float:
                        try:
                            return float(x)
                        except Exception:
                            return 0.0

                    def _kcal_per_100g() -> float:
                        # OFF may provide kcal directly or energy in kJ.
                        kcal = _num(nutr.get("energy-kcal_100g") or nutr.get("energy-kcal"))
                        if kcal > 0:
                            return kcal
                        kj = _num(nutr.get("energy-kj_100g") or nutr.get("energy_100g") or nutr.get("energy"))
                        if kj > 0:
                            return kj / 4.184
                        return 0.0

                    multiplier = float(portion_g) / 100.0

                    kcal_100g = _kcal_per_100g()
                    protein_100g = _num(nutr.get("proteins_100g"))
                    carbs_100g = _num(nutr.get("carbohydrates_100g"))
                    fat_100g = _num(nutr.get("fat_100g"))
                    fiber_100g = _num(nutr.get("fiber_100g"))
                    sugar_100g = _num(nutr.get("sugars_100g"))

                    # sodium_100g is typically in grams in OFF
                    sodium_g_100g = _num(nutr.get("sodium_100g"))
                    sodium_mg_100g = sodium_g_100g * 1000.0

                    category = (prod.get("categories") or "other").split(",")[0].strip() or "other"

                    if kcal_100g <= 0:
                        return None

                    return {
                        "calories": int(kcal_100g * multiplier),
                        "protein_g": round(protein_100g * multiplier, 1),
                        "carbs_g": round(carbs_100g * multiplier, 1),
                        "fat_g": round(fat_100g * multiplier, 1),
                        "fiber_g": round(fiber_100g * multiplier, 1),
                        "sodium_mg": int(sodium_mg_100g * multiplier),
                        "sugar_g": round(sugar_100g * multiplier, 1),
                        "category": category,
                        "portion_g": portion_g,
                        "micronutrients": {},
                    }

        except Exception as e:
            logger.error(f"OpenFoodFacts error: {e}")
            return None

    def _parse_usda_response(self, data: Dict[str, Any], portion_g: int) -> Dict[str, Any]:
        """Parse USDA API response."""
        try:
            if "foods" in data and data["foods"]:
                food = data["foods"][0]
                food_nutrients = food.get("foodNutrients", []) or []
                nutrients = {
                    (n.get("nutrientName") or ""): n.get("value")
                    for n in food_nutrients
                    if isinstance(n, dict)
                }

                def _value(name: str) -> float:
                    try:
                        v = nutrients.get(name, 0) or 0
                        return float(v)
                    except Exception:
                        return 0.0

                def _micro_to_mg(nutrient_name: str) -> float:
                    # USDA search response does not always include units in a consistent field.
                    # Try to read unitName if present and normalize to mg.
                    unit = None
                    val = 0.0
                    for n in food_nutrients:
                        if (n.get("nutrientName") or "") == nutrient_name:
                            unit = (n.get("unitName") or "").lower() if isinstance(n.get("unitName"), str) else None
                            try:
                                val = float(n.get("value") or 0)
                            except Exception:
                                val = 0.0
                            break
                    if not unit:
                        return val  # best effort
                    if unit == "mg":
                        return val
                    if unit in ("µg", "ug", "mcg"):
                        return val / 1000.0
                    if unit == "g":
                        return val * 1000.0
                    return val
                
                # Calculate multiplier based on portion
                multiplier = portion_g / 100

                # Best-effort micronutrients (stored in mg unless noted)
                micronutrients = {
                    "vitamin_c_mg": _micro_to_mg("Vitamin C, total ascorbic acid") * multiplier,
                    "vitamin_d_mcg": (_value("Vitamin D (D2 + D3)") * multiplier),
                    "vitamin_a_mcg_rae": (_value("Vitamin A, RAE") * multiplier),
                    "calcium_mg": _micro_to_mg("Calcium, Ca") * multiplier,
                    "iron_mg": _micro_to_mg("Iron, Fe") * multiplier,
                    "potassium_mg": _micro_to_mg("Potassium, K") * multiplier,
                    "magnesium_mg": _micro_to_mg("Magnesium, Mg") * multiplier,
                    "zinc_mg": _micro_to_mg("Zinc, Zn") * multiplier,
                    "cholesterol_mg": _micro_to_mg("Cholesterol") * multiplier,
                }

                # Drop zeros to keep payload tidy
                micronutrients = {k: round(v, 3) for k, v in micronutrients.items() if v and v > 0}
                
                return {
                    "calories": int(_value("Energy") * multiplier),
                    "protein_g": round(_value("Protein") * multiplier, 1),
                    "carbs_g": round(_value("Carbohydrate, by difference") * multiplier, 1),
                    "fat_g": round(_value("Total lipid (fat)") * multiplier, 1),
                    "fiber_g": round(_value("Fiber, total dietary") * multiplier, 1),
                    "sodium_mg": int(_value("Sodium, Na") * multiplier),
                    "sugar_g": round(_value("Sugars, total including NLEA") * multiplier, 1),
                    "category": food.get("foodCategory", "other"),
                    "portion_g": portion_g,
                    "micronutrients": micronutrients
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
        micronutrients: Dict[str, float] = {}
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
        async with self._repository() as repository:
            if repository is None:
                return {
                    "date": target_date.isoformat(),
                    "total_calories": 0,
                    "total_protein_g": 0,
                    "total_carbs_g": 0,
                    "total_fat_g": 0,
                    "total_fiber_g": 0,
                    "total_sodium_mg": 0,
                    "total_sugar_g": 0,
                    "micronutrients": {},
                    "meals": [],
                    "meal_count": 0,
                }
            try:
                return await repository.get_daily_nutrition_summary(user_id, target_date)
            except (ProgrammingError, OperationalError) as e:
                if _looks_like_missing_table(e):
                    logger.warning("Nutrition tables not found yet; returning empty daily nutrition")
                    return {
                        "date": target_date.isoformat(),
                        "total_calories": 0,
                        "total_protein_g": 0,
                        "total_carbs_g": 0,
                        "total_fat_g": 0,
                        "total_fiber_g": 0,
                        "total_sodium_mg": 0,
                        "total_sugar_g": 0,
                        "micronutrients": {},
                        "meals": [],
                        "meal_count": 0,
                    }
                raise

    async def get_nutrition_history(self, user_id: str, start_date: date, end_date: date) -> List[Any]:
        """Get nutrition history for a user over a date range."""
        async with self._repository() as repository:
            if repository is None:
                return []
            try:
                return await repository.get_user_meal_logs(user_id, start_date, end_date)
            except (ProgrammingError, OperationalError) as e:
                if _looks_like_missing_table(e):
                    logger.warning("Nutrition tables not found yet; returning empty nutrition history")
                    return []
                raise

    async def create_food_item(self, user_id: str, food_data: Dict[str, Any]) -> Any:
        """Create a custom food item for a user."""
        async with self._repository() as repository:
            if repository is None:
                raise RuntimeError("Nutrition database unavailable")
            return await repository.cache_food_data(food_data)

    async def get_food_item(self, food_id: str) -> Any:
        """Get a specific food item by ID."""
        async with self._repository() as repository:
            if repository is None:
                raise RuntimeError("Nutrition database unavailable")
            return await repository.get_food_from_database(food_id)

    async def get_food_cache(
        self, query: Optional[str] = None, source: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Return cached foods from the food database table."""
        async with self._repository() as repository:
            if repository is None:
                return []
            return await repository.list_food_cache(query=query, source=source, limit=limit)

    async def search_foods(self, query: str, category: Optional[str], limit: int) -> List[Any]:
        """Search for foods in the database."""
        async with self._repository() as repository:
            if repository is None:
                raise RuntimeError("Nutrition database unavailable")
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
            nutrient_key_map = {
                "calories": "total_calories",
                "protein": "total_protein_g",
                "carbs": "total_carbs_g",
                "fat": "total_fat_g",
            }
            value_key = nutrient_key_map.get((nutrient or "").lower(), f"total_{nutrient}")

            trends = []
            for day_data in nutrition_history:
                ts = day_data.get("timestamp")
                day_str = (ts or "")[:10] if isinstance(ts, str) else None
                trends.append({
                    "date": day_str,
                    "value": day_data.get(value_key, 0),
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

    async def update_meal(
        self, user_id: str, meal_id: str, meal_data: Dict[str, Any], token: Optional[str] = None
    ) -> Any:
        """
        Update an existing meal log for a user and return the updated meal analysis.

        We recompute nutrition totals from the provided food_items, then persist the updated meal log.
        """
        # Re-analyze from the updated inputs
        analysis = await self.analyze_meal(user_id, meal_data, token)

        async with self._repository() as repository:
            if repository is None:
                # If DB isn't available, behave like a pure analysis endpoint
                analysis["meal_log_id"] = meal_id
                return analysis

            updates = {
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
                "mood_after": meal_data.get("mood_after"),
            }

            updated = await repository.update_meal_log(meal_id=meal_id, user_id=user_id, updates=updates)

        analysis["meal_log_id"] = updated.get("id")
        return analysis

    async def delete_meal(self, user_id: str, meal_id: str) -> None:
        """Delete a meal log (scoped to the user)."""
        async with self._repository() as repository:
            if repository is None:
                raise RuntimeError("Nutrition database unavailable")
            deleted = await repository.delete_meal_log(meal_id=meal_id, user_id=user_id)
            if not deleted:
                raise ValueError("Meal not found")

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
                total_calories = sum(day.get("total_calories", 0) for day in nutrition_history)
                total_protein = sum(day.get("total_protein_g", 0) for day in nutrition_history)
                total_carbs = sum(day.get("total_carbs_g", 0) for day in nutrition_history)
                total_fat = sum(day.get("total_fat_g", 0) for day in nutrition_history)
                
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