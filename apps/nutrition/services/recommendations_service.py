import os
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from common.utils.logging import get_logger

logger = get_logger(__name__)

class RecommendationsService:
    """
    Service for generating personalized nutrition recommendations.
    """
    
    def __init__(self):
        self.user_profile_service_url = os.getenv("USER_PROFILE_SERVICE_URL", "http://user-profile-service:8001")
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def get_recommendations(
        self, 
        user_id: str, 
        nutrition_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized nutrition recommendations.
        
        Args:
            user_id: User identifier
            nutrition_data: Current nutrition data
            user_preferences: Optional user preferences from profile service
        
        Returns:
            List of personalized recommendations
        """
        try:
            recommendations = []
            
            # Get user profile if not provided
            if not user_preferences:
                user_preferences = await self._get_user_profile(user_id)
            
            # Generate recommendations based on nutrition data and preferences
            recommendations.extend(self._generate_calorie_recommendations(nutrition_data, user_preferences))
            recommendations.extend(self._generate_macro_recommendations(nutrition_data, user_preferences))
            recommendations.extend(self._generate_dietary_recommendations(nutrition_data, user_preferences))
            recommendations.extend(self._generate_health_goal_recommendations(nutrition_data, user_preferences))
            
            # Sort by priority
            recommendations.sort(key=lambda x: self._get_priority_score(x["priority"]), reverse=True)
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return self._get_fallback_recommendations(nutrition_data)

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from user profile service."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.user_profile_service_url}/api/v1/user-profile/{user_id}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get user profile: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    def _generate_calorie_recommendations(self, nutrition_data: Dict[str, Any], user_preferences: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate calorie-based recommendations."""
        recommendations = []
        calories = nutrition_data.get("calories", 0)
        
        if user_preferences:
            target_calories = user_preferences.get("calorie_target")
            if target_calories:
                if calories > target_calories * 1.2:
                    recommendations.append({
                        "type": "portion_control",
                        "message": "This meal is quite high in calories. Consider reducing portion sizes or choosing lower-calorie alternatives.",
                        "priority": "high",
                        "rationale": "High calorie intake may not align with weight management goals."
                    })
                elif calories < target_calories * 0.8:
                    recommendations.append({
                        "type": "calorie_boost",
                        "message": "This meal is quite low in calories. Consider adding nutrient-dense foods to meet your energy needs.",
                        "priority": "medium",
                        "rationale": "Adequate calorie intake supports overall health and energy levels."
                    })
        else:
            # Default recommendations without user preferences
            if calories > 800:
                recommendations.append({
                    "type": "portion_control",
                    "message": "This meal is quite high in calories. Consider reducing portion sizes or choosing lower-calorie alternatives.",
                    "priority": "high",
                    "rationale": "High calorie intake may not align with weight management goals."
                })
        
        return recommendations

    def _generate_macro_recommendations(self, nutrition_data: Dict[str, Any], user_preferences: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate macronutrient-based recommendations."""
        recommendations = []
        protein = nutrition_data.get("protein_g", 0)
        carbs = nutrition_data.get("carbs_g", 0)
        fat = nutrition_data.get("fat_g", 0)
        
        # Protein recommendations
        if protein < 20:
            recommendations.append({
                "type": "protein_boost",
                "message": "Increase protein intake for better muscle maintenance and satiety.",
                "priority": "medium",
                "rationale": "Adequate protein supports muscle health and helps with feeling full."
            })
        
        # Carb recommendations
        if carbs > 100:
            recommendations.append({
                "type": "carb_management",
                "message": "Consider reducing carbohydrate intake or choosing complex carbs.",
                "priority": "medium",
                "rationale": "Managing carb intake can help with blood sugar control."
            })
        
        # Fat recommendations
        if fat > 50:
            recommendations.append({
                "type": "fat_management",
                "message": "Consider reducing fat intake or choosing healthier fat sources.",
                "priority": "medium",
                "rationale": "Excessive fat intake may impact heart health."
            })
        
        return recommendations

    def _generate_dietary_recommendations(self, nutrition_data: Dict[str, Any], user_preferences: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate dietary restriction-based recommendations."""
        recommendations = []
        
        if user_preferences:
            dietary_restrictions = user_preferences.get("dietary_restrictions", [])
            allergies = user_preferences.get("allergies", [])
            
            # Check for fiber intake
            fiber = nutrition_data.get("fiber_g", 0)
            if fiber < 5:
                recommendations.append({
                    "type": "fiber_boost",
                    "message": "Add more fiber-rich foods like vegetables, fruits, or whole grains.",
                    "priority": "medium",
                    "rationale": "Fiber supports digestive health and helps maintain stable blood sugar."
                })
            
            # Check for sodium intake
            sodium = nutrition_data.get("sodium_mg", 0)
            if sodium > 1000:
                recommendations.append({
                    "type": "sodium_reduction",
                    "message": "Consider reducing sodium intake by choosing lower-salt options.",
                    "priority": "medium",
                    "rationale": "High sodium intake may impact blood pressure."
                })
        
        return recommendations

    def _generate_health_goal_recommendations(self, nutrition_data: Dict[str, Any], user_preferences: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate health goal-based recommendations."""
        recommendations = []
        
        if user_preferences:
            health_goals = user_preferences.get("health_goals", [])
            
            for goal in health_goals:
                if goal == "weight_loss":
                    calories = nutrition_data.get("calories", 0)
                    if calories > 600:
                        recommendations.append({
                            "type": "weight_loss_support",
                            "message": "For weight loss goals, consider smaller portions or lower-calorie alternatives.",
                            "priority": "high",
                            "rationale": "Calorie control is essential for weight loss."
                        })
                
                elif goal == "muscle_gain":
                    protein = nutrition_data.get("protein_g", 0)
                    if protein < 30:
                        recommendations.append({
                            "type": "muscle_gain_support",
                            "message": "For muscle gain goals, increase protein intake with lean meats, eggs, or plant proteins.",
                            "priority": "high",
                            "rationale": "Adequate protein is essential for muscle building."
                        })
                
                elif goal == "heart_health":
                    fat = nutrition_data.get("fat_g", 0)
                    if fat > 40:
                        recommendations.append({
                            "type": "heart_health_support",
                            "message": "For heart health, choose lean proteins and healthy fats like olive oil or nuts.",
                            "priority": "medium",
                            "rationale": "Managing fat intake supports cardiovascular health."
                        })
        
        return recommendations

    def _get_priority_score(self, priority: str) -> int:
        """Get numeric score for priority sorting."""
        priority_scores = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return priority_scores.get(priority, 1)

    def _get_fallback_recommendations(self, nutrition_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get fallback recommendations when user profile is unavailable."""
        recommendations = []
        
        calories = nutrition_data.get("calories", 0)
        protein = nutrition_data.get("protein_g", 0)
        fiber = nutrition_data.get("fiber_g", 0)
        
        if calories > 800:
            recommendations.append({
                "type": "portion_control",
                "message": "This meal is quite high in calories. Consider reducing portion sizes or choosing lower-calorie alternatives.",
                "priority": "high",
                "rationale": "High calorie intake may not align with weight management goals."
            })
        
        if protein < 20:
            recommendations.append({
                "type": "protein_boost",
                "message": "Increase protein intake for better muscle maintenance and satiety.",
                "priority": "medium",
                "rationale": "Adequate protein supports muscle health and helps with feeling full."
            })
        
        if fiber < 5:
            recommendations.append({
                "type": "fiber_boost",
                "message": "Add more fiber-rich foods like vegetables, fruits, or whole grains.",
                "priority": "medium",
                "rationale": "Fiber supports digestive health and helps maintain stable blood sugar."
            })
        
        return recommendations

    async def get_meal_suggestions(self, user_id: str, meal_type: str, user_preferences: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get meal suggestions based on user preferences and meal type."""
        try:
            suggestions = []
            
            if not user_preferences:
                user_preferences = await self._get_user_profile(user_id)
            
            # Generate meal suggestions based on preferences
            if user_preferences:
                dietary_restrictions = user_preferences.get("dietary_restrictions", [])
                preferred_cuisines = user_preferences.get("preferred_cuisines", [])
                
                # Add meal suggestions based on restrictions and preferences
                if "vegetarian" in dietary_restrictions:
                    suggestions.extend(self._get_vegetarian_suggestions(meal_type))
                elif "vegan" in dietary_restrictions:
                    suggestions.extend(self._get_vegan_suggestions(meal_type))
                else:
                    suggestions.extend(self._get_general_suggestions(meal_type))
                
                # Filter by preferred cuisines if specified
                if preferred_cuisines:
                    suggestions = [s for s in suggestions if any(cuisine in s.get("cuisine", "").lower() for cuisine in preferred_cuisines)]
            
            else:
                # Fallback suggestions
                suggestions.extend(self._get_general_suggestions(meal_type))
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Failed to get meal suggestions: {e}")
            return self._get_general_suggestions(meal_type)

    def _get_vegetarian_suggestions(self, meal_type: str) -> List[Dict[str, Any]]:
        """Get vegetarian meal suggestions."""
        suggestions = {
            "breakfast": [
                {"name": "Greek yogurt with berries and granola", "calories": 300, "protein": 15, "cuisine": "mediterranean"},
                {"name": "Avocado toast with eggs", "calories": 350, "protein": 12, "cuisine": "american"},
                {"name": "Oatmeal with nuts and honey", "calories": 280, "protein": 8, "cuisine": "american"}
            ],
            "lunch": [
                {"name": "Quinoa salad with vegetables", "calories": 400, "protein": 12, "cuisine": "mediterranean"},
                {"name": "Lentil soup with bread", "calories": 350, "protein": 18, "cuisine": "mediterranean"},
                {"name": "Grilled cheese with tomato soup", "calories": 450, "protein": 15, "cuisine": "american"}
            ],
            "dinner": [
                {"name": "Vegetable stir-fry with tofu", "calories": 380, "protein": 20, "cuisine": "asian"},
                {"name": "Pasta with marinara and vegetables", "calories": 420, "protein": 12, "cuisine": "italian"},
                {"name": "Bean and rice burrito", "calories": 400, "protein": 15, "cuisine": "mexican"}
            ]
        }
        return suggestions.get(meal_type, [])

    def _get_vegan_suggestions(self, meal_type: str) -> List[Dict[str, Any]]:
        """Get vegan meal suggestions."""
        suggestions = {
            "breakfast": [
                {"name": "Smoothie bowl with granola", "calories": 320, "protein": 8, "cuisine": "american"},
                {"name": "Tofu scramble with vegetables", "calories": 280, "protein": 15, "cuisine": "american"},
                {"name": "Overnight oats with almond milk", "calories": 300, "protein": 10, "cuisine": "american"}
            ],
            "lunch": [
                {"name": "Chickpea salad sandwich", "calories": 380, "protein": 14, "cuisine": "american"},
                {"name": "Vegetable curry with rice", "calories": 420, "protein": 12, "cuisine": "indian"},
                {"name": "Hummus and vegetable wrap", "calories": 350, "protein": 12, "cuisine": "mediterranean"}
            ],
            "dinner": [
                {"name": "Lentil curry with quinoa", "calories": 400, "protein": 18, "cuisine": "indian"},
                {"name": "Vegetable lasagna", "calories": 380, "protein": 12, "cuisine": "italian"},
                {"name": "Tempeh stir-fry with vegetables", "calories": 360, "protein": 20, "cuisine": "asian"}
            ]
        }
        return suggestions.get(meal_type, [])

    def _get_general_suggestions(self, meal_type: str) -> List[Dict[str, Any]]:
        """Get general meal suggestions."""
        suggestions = {
            "breakfast": [
                {"name": "Scrambled eggs with whole grain toast", "calories": 350, "protein": 18, "cuisine": "american"},
                {"name": "Greek yogurt parfait", "calories": 300, "protein": 15, "cuisine": "mediterranean"},
                {"name": "Oatmeal with berries", "calories": 280, "protein": 8, "cuisine": "american"}
            ],
            "lunch": [
                {"name": "Grilled chicken salad", "calories": 400, "protein": 25, "cuisine": "american"},
                {"name": "Turkey sandwich with vegetables", "calories": 380, "protein": 20, "cuisine": "american"},
                {"name": "Salmon with quinoa", "calories": 420, "protein": 28, "cuisine": "mediterranean"}
            ],
            "dinner": [
                {"name": "Grilled salmon with vegetables", "calories": 450, "protein": 30, "cuisine": "mediterranean"},
                {"name": "Lean beef stir-fry", "calories": 400, "protein": 25, "cuisine": "asian"},
                {"name": "Chicken breast with sweet potato", "calories": 380, "protein": 28, "cuisine": "american"}
            ]
        }
        return suggestions.get(meal_type, []) 