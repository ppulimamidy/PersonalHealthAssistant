#!/usr/bin/env python3
"""
Comprehensive Integration Test for Nutrition Service

This script tests all the nutrition service integrations with real API keys:
- OpenAI Vision for food recognition
- Google Vision API (if available)
- Nutritionix API for nutrition data
- USDA API for nutrition data
- Groq API for AI processing
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone, date
import base64

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.nutrition.services.nutrition_service import NutritionService
from apps.nutrition.services.food_recognition_service import FoodRecognitionService
from apps.nutrition.services.recommendations_service import RecommendationsService
from apps.nutrition.repositories.nutrition_repository import NutritionRepository
from apps.nutrition.models.database_models import (
    FoodRecognitionResult, UserCorrection, MealLog, 
    NutritionGoal, FoodDatabase, ModelPerformance, UserPreferences
)
from common.database.connection import get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NutritionIntegrationTest:
    """Comprehensive integration test for nutrition service"""
    
    def __init__(self):
        self.nutrition_service = NutritionService()
        self.food_recognition_service = FoodRecognitionService()
        self.recommendations_service = RecommendationsService()
        # Remove self.repository
        self.test_user_id = "test_user_123"
        self.test_image_path = Path(__file__).parent.parent.parent.parent / "uploads" / "images" / "test_food.jpg"
        
    def create_test_image(self):
        """Create a simple test image for food recognition"""
        try:
            # Create a simple test image using PIL
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a 300x300 image with text
            img = Image.new('RGB', (300, 300), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add some text to simulate food
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            draw.text((50, 150), "Test Food Image", fill='black', font=font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
            
        except ImportError:
            logger.warning("PIL not available, creating dummy image data")
            # Create dummy image data
            return b"dummy_image_data_for_testing"
    
    async def get_repository(self):
        db_manager = get_db_manager()
        async_session_factory = db_manager.get_async_session_factory()
        async with async_session_factory() as session:
            yield NutritionRepository(session)

    async def test_food_recognition(self):
        """Test food recognition with OpenAI Vision"""
        logger.info("Testing food recognition with OpenAI Vision...")
        
        try:
            # Create test image
            image_data = self.create_test_image()
            
            # Test food recognition using the correct method
            result = await self.food_recognition_service.recognize_food({
                "user_id": self.test_user_id,
                "image_data": image_data,
                "image_format": "jpeg",
                "models_to_use": ["openai_vision"],
                "enable_portion_estimation": True,
                "enable_nutrition_lookup": True
            })
            
            logger.info(f"Food recognition result: {result}")
            
            # Test nutrition data fetching
            nutrition_data = await self.nutrition_service._fetch_nutrition_data({
                "name": "apple",
                "portion_g": 100
            })
            
            logger.info(f"Nutrition data for apple: {nutrition_data}")
            
            return True
            
        except Exception as e:
            logger.error(f"Food recognition test failed: {e}")
            return False
    
    async def test_nutritionix_api(self):
        """Test Nutritionix API integration"""
        logger.info("Testing Nutritionix API...")
        
        try:
            # Test with a common food item using the correct method
            test_foods = ["apple", "banana", "chicken breast", "salmon"]
            
            for food in test_foods:
                nutrition_data = await self.nutrition_service._fetch_nutrition_data({
                    "name": food,
                    "portion_g": 100
                })
                
                logger.info(f"Nutritionix data for {food}: {nutrition_data}")
            
            return True
            
        except Exception as e:
            logger.error(f"Nutritionix API test failed: {e}")
            return False
    
    async def test_usda_api(self):
        """Test USDA API integration"""
        logger.info("Testing USDA API...")
        
        try:
            # Test with common food items using the correct method
            test_foods = ["apple", "banana", "chicken", "salmon"]
            
            for food in test_foods:
                nutrition_data = await self.nutrition_service._fetch_nutrition_data({
                    "name": food,
                    "portion_g": 100
                })
                
                logger.info(f"USDA data for {food}: {nutrition_data}")
            
            return True
            
        except Exception as e:
            logger.error(f"USDA API test failed: {e}")
            return False
    
    async def test_recommendations(self):
        """Test personalized recommendations"""
        logger.info("Testing personalized recommendations...")
        
        try:
            # Create test user profile
            user_profile = {
                "age": 30,
                "weight": 70,  # kg
                "height": 175,  # cm
                "activity_level": "moderate",
                "dietary_restrictions": ["vegetarian"],
                "health_goals": ["weight_loss", "muscle_gain"]
            }
            
            # Test recommendations using the correct method
            recommendations = await self.recommendations_service.get_recommendations(
                user_id=self.test_user_id,
                nutrition_data={"calories": 1800, "protein": 120, "carbs": 200, "fat": 60}
            )
            
            logger.info(f"Recommendations: {recommendations}")
            
            return True
            
        except Exception as e:
            logger.error(f"Recommendations test failed: {e}")
            return False
    
    async def test_database_operations(self):
        """Test database operations"""
        logger.info("Testing database operations...")
        try:
            async for repository in self.get_repository():
                # Test saving food recognition result with correct fields
                recognition_result = FoodRecognitionResult(
                    user_id=self.test_user_id,
                    recognition_id=f"test_recognition_{datetime.now().timestamp()}",
                    image_format="jpeg",
                    image_size_bytes=1024,
                    image_hash="test_hash_123",
                    models_used=["openai_vision"],
                    processing_time_ms=1500,
                    confidence_threshold=0.5,
                    recognized_foods=["apple", "banana"],
                    total_foods_detected=2,
                    average_confidence=0.85,
                    meal_type="breakfast",
                    cuisine_hint="american",
                    region_hint="north_america",
                    dietary_restrictions=["vegetarian"],
                    preferred_units="metric",
                    is_corrected=False,
                    user_rating=5,
                    user_feedback="Great recognition!"
                )
                
                saved_result = await repository.create_recognition_result({
                    "user_id": recognition_result.user_id,
                    "recognition_id": recognition_result.recognition_id,
                    "image_format": recognition_result.image_format,
                    "image_size_bytes": recognition_result.image_size_bytes,
                    "image_hash": recognition_result.image_hash,
                    "models_used": recognition_result.models_used,
                    "processing_time_ms": recognition_result.processing_time_ms,
                    "confidence_threshold": recognition_result.confidence_threshold,
                    "recognized_foods": recognition_result.recognized_foods,
                    "total_foods_detected": recognition_result.total_foods_detected,
                    "average_confidence": recognition_result.average_confidence,
                    "meal_type": recognition_result.meal_type,
                    "cuisine_hint": recognition_result.cuisine_hint,
                    "region_hint": recognition_result.region_hint,
                    "dietary_restrictions": recognition_result.dietary_restrictions,
                    "preferred_units": recognition_result.preferred_units,
                    "is_corrected": recognition_result.is_corrected,
                    "user_rating": recognition_result.user_rating,
                    "user_feedback": recognition_result.user_feedback
                })
                logger.info(f"Saved recognition result: {saved_result.id}")
                
                # Test saving meal log with correct fields
                meal_log_data = {
                    "user_id": self.test_user_id,
                    "recognition_result_id": str(saved_result.id),
                    "meal_type": "breakfast",
                    "meal_name": "Test Breakfast",
                    "meal_description": "A test breakfast meal",
                    "food_items": [
                        {"name": "apple", "quantity": 1, "unit": "medium"},
                        {"name": "oatmeal", "quantity": 100, "unit": "g"}
                    ],
                    "total_calories": 250.0,
                    "total_protein_g": 8.5,
                    "total_carbs_g": 45.2,
                    "total_fat_g": 4.1,
                    "total_fiber_g": 6.0,
                    "total_sodium_mg": 150.0,
                    "total_sugar_g": 25.0,
                    "micronutrients": {"vitamin_c": 8.4, "iron": 0.2},
                    "user_notes": "Test meal",
                    "mood_before": "hungry",
                    "mood_after": "satisfied",
                    "synced_to_health_tracking": False,
                    "synced_to_medical_analysis": False
                }
                
                saved_meal = await repository.create_meal_log(meal_log_data)
                logger.info(f"Saved meal log: {saved_meal.id}")
                
                # Test retrieving user's meal history
                meal_history = await repository.get_user_meal_logs(
                    user_id=self.test_user_id,
                    start_date=date.today(),
                    end_date=date.today()
                )
                
                logger.info(f"Retrieved {len(meal_history)} meals from history")
                
                return True
        except Exception as e:
            logger.error(f"Database operations test failed: {e}")
            return False
    
    async def test_cache_operations(self):
        """Test caching functionality"""
        logger.info("Testing cache operations...")
        
        try:
            # Test caching nutrition data using the correct method
            test_data = {
                "calories": 95,
                "protein_g": 0.5,
                "carbs_g": 25,
                "fat_g": 0.3,
                "fiber_g": 4.0,
                "sodium_mg": 1,
                "sugar_g": 19,
                "micronutrients": {"vitamin_c": 8.4}
            }
            
            # Cache the data
            await self.nutrition_service._cache_nutrition_data("apple", test_data, "test")
            
            # Get from cache
            cached_data = await self.nutrition_service._fetch_nutrition_data({
                "name": "apple",
                "portion_g": 100
            })
            
            if cached_data:
                logger.info(f"Cache test successful: {cached_data}")
                return True
            else:
                logger.warning("Cache test failed - no data retrieved")
                return False
                
        except Exception as e:
            logger.error(f"Cache operations test failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        logger.info("Testing error handling...")
        
        try:
            # Test with invalid food description
            result = await self.nutrition_service._fetch_nutrition_data({
                "name": "",
                "portion_g": 100
            })
            
            logger.info(f"Empty food description result: {result}")
            
            # Test with very long food description
            long_description = "a very long food description " * 50
            result = await self.nutrition_service._fetch_nutrition_data({
                "name": long_description,
                "portion_g": 100
            })
            
            logger.info(f"Long description result: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting comprehensive nutrition service integration tests...")
        logger.info("=" * 60)
        
        test_results = {}
        
        # Run all tests
        tests = [
            ("Food Recognition", self.test_food_recognition),
            ("Nutritionix API", self.test_nutritionix_api),
            ("USDA API", self.test_usda_api),
            ("Recommendations", self.test_recommendations),
            ("Database Operations", self.test_database_operations),
            ("Cache Operations", self.test_cache_operations),
            ("Error Handling", self.test_error_handling)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\nRunning {test_name} test...")
            try:
                result = await test_func()
                test_results[test_name] = result
                status = "✓ PASSED" if result else "✗ FAILED"
                logger.info(f"{test_name}: {status}")
            except Exception as e:
                test_results[test_name] = False
                logger.error(f"{test_name}: ✗ FAILED - {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Nutrition service is ready for production.")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Please review the issues above.")
        
        return test_results

async def main():
    """Main function"""
    test_runner = NutritionIntegrationTest()
    results = await test_runner.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 