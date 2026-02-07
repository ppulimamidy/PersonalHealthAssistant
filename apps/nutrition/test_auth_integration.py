"""
Integration test for Nutrition Service with Authentication and User Profile Integration.

This test verifies that the nutrition service properly integrates with:
1. Authentication service for user verification
2. User profile service for personalized recommendations
3. Database operations with authenticated users
4. Traefik routing and middleware
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
from datetime import datetime, date, timezone, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.utils.logging import get_logger

logger = get_logger(__name__)

class NutritionAuthIntegrationTest:
    """Integration test for nutrition service with authentication."""
    
    def __init__(self):
        # Service URLs
        self.auth_service_url = "http://localhost:8000"
        self.user_profile_service_url = "http://localhost:8001"
        self.nutrition_service_url = "http://localhost:8007"
        self.traefik_url = "http://nutrition.localhost"
        
        # Test data
        self.test_user = {
            "email": "test@nutrition.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        self.test_user_id = None
        self.auth_token = None
        self.user_profile_data = None
        
        # HTTP client
        self.session = None
    
    async def setup(self):
        """Setup test environment."""
        logger.info("Setting up Nutrition Auth Integration Test...")
        
        self.session = aiohttp.ClientSession()
        
        # Wait for services to be ready
        await self._wait_for_services()
        
        # Create test user and get authentication token
        await self._setup_test_user()
        
        # Setup user profile data
        await self._setup_user_profile()
        
        logger.info("Setup completed successfully")
    
    async def teardown(self):
        """Cleanup test environment."""
        logger.info("Cleaning up test environment...")
        
        if self.session:
            await self.session.close()
        
        logger.info("Cleanup completed")
    
    async def _wait_for_services(self):
        """Wait for all services to be ready."""
        services = [
            (self.auth_service_url, "Auth Service"),
            (self.user_profile_service_url, "User Profile Service"),
            (self.nutrition_service_url, "Nutrition Service")
        ]
        
        for url, name in services:
            max_retries = 30
            for attempt in range(max_retries):
                try:
                    async with self.session.get(f"{url}/health") as response:
                        if response.status == 200:
                            logger.info(f"{name} is ready")
                            break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"{name} failed to start: {e}")
                    logger.info(f"Waiting for {name}... (attempt {attempt + 1})")
                    await asyncio.sleep(2)
    
    async def _setup_test_user(self):
        """Create test user and get authentication token."""
        logger.info("Setting up test user...")
        
        # Register user
        register_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"],
            "first_name": self.test_user["first_name"],
            "last_name": self.test_user["last_name"]
        }
        
        async with self.session.post(
            f"{self.auth_service_url}/api/v1/auth/register",
            json=register_data
        ) as response:
            if response.status == 201:
                result = await response.json()
                self.test_user_id = result["data"]["user"]["id"]
                logger.info(f"Test user created with ID: {self.test_user_id}")
            else:
                # User might already exist, try to login
                logger.info("User might already exist, attempting login...")
        
        # Login to get token
        auth_data = {
            "username": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        async with self.session.post(
            f"{self.auth_service_url}/api/v1/auth/login",
            json=auth_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                self.auth_token = result["data"]["session"]["session_token"]
                logger.info("Authentication token obtained")
            else:
                raise Exception(f"Failed to login: {response.status}")
    
    async def _setup_user_profile(self):
        """Setup user profile data for testing."""
        logger.info("Setting up user profile...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Create user profile
        profile_data = {
            "first_name": self.test_user["first_name"],
            "last_name": self.test_user["last_name"],
            "date_of_birth": "1990-01-01",
            "gender": "other",
            "height_cm": 170,
            "weight_kg": 70,
            "activity_level": "moderate"
        }
        
        async with self.session.post(
            f"{self.user_profile_service_url}/api/v1/user-profile",
            json=profile_data,
            headers=headers
        ) as response:
            if response.status in [200, 201]:
                self.user_profile_data = await response.json()
                logger.info("User profile created")
            else:
                logger.warning(f"Failed to create user profile: {response.status}")
        
        # Create user preferences
        preferences_data = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": ["nuts"],
            "health_goals": ["weight_loss", "heart_health"],
            "preferred_cuisines": ["mediterranean", "asian"],
            "calorie_target": 1800,
            "protein_target": 120,
            "carb_target": 200,
            "fat_target": 60
        }
        
        async with self.session.post(
            f"{self.user_profile_service_url}/api/v1/user-profile/preferences",
            json=preferences_data,
            headers=headers
        ) as response:
            if response.status in [200, 201]:
                logger.info("User preferences created")
            else:
                logger.warning(f"Failed to create user preferences: {response.status}")
    
    async def test_authentication_required(self):
        """Test that authentication is required for protected endpoints."""
        logger.info("Testing authentication requirements...")
        
        # Test without authentication
        async with self.session.post(
            f"{self.nutrition_service_url}/api/v1/nutrition/analyze-meal",
            json={"food_items": [{"name": "apple", "portion_g": 100}]}
        ) as response:
            assert response.status == 401, f"Expected 401, got {response.status}"
        
        logger.info("✓ Authentication requirement verified")
    
    async def test_meal_analysis_with_auth(self):
        """Test meal analysis with authentication."""
        logger.info("Testing meal analysis with authentication...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        meal_data = {
            "food_items": [
                {"name": "apple", "portion_g": 100},
                {"name": "banana", "portion_g": 120}
            ],
            "meal_type": "snack",
            "meal_name": "Test Snack"
        }
        
        async with self.session.post(
            f"{self.nutrition_service_url}/api/v1/nutrition/analyze-meal",
            json=meal_data,
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            assert "data" in result
            assert "food_items" in result["data"]
            assert "totals" in result["data"]
            assert "recommendations" in result["data"]
            assert "user_preferences_used" in result["data"]
            
            # Verify user preferences were used
            assert result["data"]["user_preferences_used"] is True
            
            logger.info("✓ Meal analysis with authentication successful")
    
    async def test_meal_logging_with_auth(self):
        """Test meal logging with authentication."""
        logger.info("Testing meal logging with authentication...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        meal_data = {
            "food_items": [
                {"name": "chicken breast", "portion_g": 150},
                {"name": "brown rice", "portion_g": 100},
                {"name": "broccoli", "portion_g": 80}
            ],
            "meal_type": "dinner",
            "meal_name": "Test Dinner",
            "user_notes": "Test meal for integration testing"
        }
        
        async with self.session.post(
            f"{self.nutrition_service_url}/api/v1/nutrition/log-meal",
            json=meal_data,
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            assert "data" in result
            assert "meal_log_id" in result["data"]
            
            logger.info(f"✓ Meal logged successfully with ID: {result['data']['meal_log_id']}")
    
    async def test_personalized_recommendations(self):
        """Test personalized recommendations using user profile data."""
        logger.info("Testing personalized recommendations...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(
            f"{self.nutrition_service_url}/api/v1/nutrition/personalized-recommendations",
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            assert "data" in result
            assert "recommendations" in result["data"]
            assert "user_preferences" in result["data"]
            
            # Verify user preferences are included
            user_prefs = result["data"]["user_preferences"]
            assert "dietary_restrictions" in user_prefs
            assert "health_goals" in user_prefs
            assert "calorie_target" in user_prefs
            
            # Verify recommendations are personalized
            recommendations = result["data"]["recommendations"]
            assert len(recommendations) > 0
            
            logger.info("✓ Personalized recommendations generated successfully")
    
    async def test_nutrition_summary(self):
        """Test comprehensive nutrition summary with user profile integration."""
        logger.info("Testing nutrition summary...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(
            f"{self.nutrition_service_url}/api/v1/nutrition/nutrition-summary?days=7",
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            assert "data" in result
            assert "user_preferences" in result["data"]
            assert "nutrition_summary" in result["data"]
            assert "recommendations" in result["data"]
            
            logger.info("✓ Nutrition summary generated successfully")
    
    async def test_daily_nutrition(self):
        """Test daily nutrition retrieval."""
        logger.info("Testing daily nutrition retrieval...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        today = date.today().isoformat()
        
        async with self.session.get(
            f"{self.nutrition_service_url}/api/v1/nutrition/daily-nutrition/{today}",
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            
            logger.info("✓ Daily nutrition retrieved successfully")
    
    async def test_nutrition_history(self):
        """Test nutrition history retrieval."""
        logger.info("Testing nutrition history retrieval...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=7)).isoformat()
        
        async with self.session.get(
            f"{self.nutrition_service_url}/api/v1/nutrition/nutrition-history",
            params={"start_date": start_date, "end_date": end_date},
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            
            logger.info("✓ Nutrition history retrieved successfully")
    
    async def test_calculate_nutrition(self):
        """Test nutrition calculation."""
        logger.info("Testing nutrition calculation...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        food_items = [
            {"name": "salmon", "portion_g": 200},
            {"name": "quinoa", "portion_g": 100},
            {"name": "spinach", "portion_g": 50}
        ]
        
        async with self.session.post(
            f"{self.nutrition_service_url}/api/v1/nutrition/calculate-nutrition",
            json=food_items,
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            assert "data" in result
            assert "food_items" in result["data"]
            assert "totals" in result["data"]
            
            logger.info("✓ Nutrition calculation successful")
    
    async def test_nutritional_insights(self):
        """Test nutritional insights generation."""
        logger.info("Testing nutritional insights...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with self.session.get(
            f"{self.nutrition_service_url}/api/v1/nutrition/nutritional-insights?timeframe=week",
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["success"] is True
            assert "data" in result
            
            logger.info("✓ Nutritional insights generated successfully")
    
    async def test_traefik_routing(self):
        """Test Traefik routing and middleware."""
        logger.info("Testing Traefik routing...")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test through Traefik
        async with self.session.get(
            f"{self.traefik_url}/health",
            headers=headers
        ) as response:
            assert response.status == 200, f"Expected 200, got {response.status}"
            
            result = await response.json()
            assert result["service"] == "nutrition"
            
            logger.info("✓ Traefik routing successful")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting Nutrition Auth Integration Tests...")
        
        try:
            await self.setup()
            
            # Run tests
            await self.test_authentication_required()
            await self.test_meal_analysis_with_auth()
            await self.test_meal_logging_with_auth()
            await self.test_personalized_recommendations()
            await self.test_nutrition_summary()
            await self.test_daily_nutrition()
            await self.test_nutrition_history()
            await self.test_calculate_nutrition()
            await self.test_nutritional_insights()
            await self.test_traefik_routing()
            
            logger.info("🎉 All Nutrition Auth Integration Tests PASSED!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise
        
        finally:
            await self.teardown()


async def main():
    """Main test runner."""
    test = NutritionAuthIntegrationTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 