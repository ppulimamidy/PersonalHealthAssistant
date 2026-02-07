"""
User Profile Client Service

Handles communication with the User Profile Service to retrieve user preferences,
health attributes, and other profile information needed for nutrition recommendations.
"""

import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker

logger = get_logger(__name__)

class UserProfileClient:
    """
    Client for communicating with the User Profile Service.
    """
    
    def __init__(self):
        self.base_url = os.getenv("USER_PROFILE_SERVICE_URL", "http://user-profile-service:8001")
        self.timeout = aiohttp.ClientTimeout(total=10)
        
        # Circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=Exception
        )
    
    async def get_user_profile(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile information including preferences and health attributes.
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/api/v1/user-profile/{user_id}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved user profile for user {user_id}")
                        return data
                    elif response.status == 404:
                        logger.warning(f"User profile not found for user {user_id}")
                        return None
                    else:
                        logger.error(f"Failed to get user profile: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def get_user_preferences(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences specifically for nutrition.
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/api/v1/user-profile/{user_id}/preferences"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved user preferences for user {user_id}")
                        return data
                    elif response.status == 404:
                        logger.warning(f"User preferences not found for user {user_id}")
                        return None
                    else:
                        logger.error(f"Failed to get user preferences: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None
    
    async def get_health_attributes(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user health attributes for nutrition recommendations.
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/api/v1/user-profile/{user_id}/health-attributes"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved health attributes for user {user_id}")
                        return data
                    elif response.status == 404:
                        logger.warning(f"Health attributes not found for user {user_id}")
                        return None
                    else:
                        logger.error(f"Failed to get health attributes: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting health attributes: {e}")
            return None
    
    async def get_dietary_restrictions(self, user_id: str, token: str) -> List[str]:
        """
        Get user's dietary restrictions.
        """
        try:
            preferences = await self.get_user_preferences(user_id, token)
            if preferences and "dietary_restrictions" in preferences:
                return preferences["dietary_restrictions"]
            return []
        except Exception as e:
            logger.error(f"Error getting dietary restrictions: {e}")
            return []
    
    async def get_health_goals(self, user_id: str, token: str) -> List[str]:
        """
        Get user's health goals.
        """
        try:
            preferences = await self.get_user_preferences(user_id, token)
            if preferences and "health_goals" in preferences:
                return preferences["health_goals"]
            return []
        except Exception as e:
            logger.error(f"Error getting health goals: {e}")
            return []
    
    async def get_allergies(self, user_id: str, token: str) -> List[str]:
        """
        Get user's food allergies.
        """
        try:
            preferences = await self.get_user_preferences(user_id, token)
            if preferences and "allergies" in preferences:
                return preferences["allergies"]
            return []
        except Exception as e:
            logger.error(f"Error getting allergies: {e}")
            return []
    
    async def get_nutrition_preferences(self, user_id: str, token: str) -> Dict[str, Any]:
        """
        Get comprehensive nutrition preferences for the user.
        """
        try:
            profile = await self.get_user_profile(user_id, token)
            preferences = await self.get_user_preferences(user_id, token)
            health_attrs = await self.get_health_attributes(user_id, token)
            
            nutrition_prefs = {
                "dietary_restrictions": [],
                "allergies": [],
                "health_goals": [],
                "preferred_cuisines": [],
                "calorie_target": None,
                "protein_target": None,
                "carb_target": None,
                "fat_target": None,
                "activity_level": "moderate",
                "weight": None,
                "height": None,
                "age": None,
                "gender": None
            }
            
            # Extract from preferences
            if preferences:
                nutrition_prefs.update({
                    "dietary_restrictions": preferences.get("dietary_restrictions", []),
                    "allergies": preferences.get("allergies", []),
                    "health_goals": preferences.get("health_goals", []),
                    "preferred_cuisines": preferences.get("preferred_cuisines", []),
                    "calorie_target": preferences.get("calorie_target"),
                    "protein_target": preferences.get("protein_target"),
                    "carb_target": preferences.get("carb_target"),
                    "fat_target": preferences.get("fat_target")
                })
            
            # Extract from health attributes
            if health_attrs:
                nutrition_prefs.update({
                    "activity_level": health_attrs.get("activity_level", "moderate"),
                    "weight": health_attrs.get("weight"),
                    "height": health_attrs.get("height"),
                    "age": health_attrs.get("age"),
                    "gender": health_attrs.get("gender")
                })
            
            # Extract from profile
            if profile:
                if "age" not in nutrition_prefs or not nutrition_prefs["age"]:
                    nutrition_prefs["age"] = profile.get("age")
                if "gender" not in nutrition_prefs or not nutrition_prefs["gender"]:
                    nutrition_prefs["gender"] = profile.get("gender")
            
            logger.info(f"Retrieved comprehensive nutrition preferences for user {user_id}")
            return nutrition_prefs
            
        except Exception as e:
            logger.error(f"Error getting nutrition preferences: {e}")
            return {
                "dietary_restrictions": [],
                "allergies": [],
                "health_goals": [],
                "preferred_cuisines": [],
                "calorie_target": None,
                "protein_target": None,
                "carb_target": None,
                "fat_target": None,
                "activity_level": "moderate",
                "weight": None,
                "height": None,
                "age": None,
                "gender": None
            }
    
    async def is_service_healthy(self) -> bool:
        """
        Check if the user profile service is healthy.
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/health"
                
                async with session.get(url) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"User profile service health check failed: {e}")
            return False 