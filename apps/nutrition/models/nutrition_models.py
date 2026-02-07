"""
Nutrition Data Models

Core models for nutritional data, food items, and meal analysis.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class NutrientType(str, Enum):
    """Types of nutrients."""
    CALORIES = "calories"
    PROTEIN = "protein"
    CARBS = "carbs"
    FAT = "fat"
    FIBER = "fiber"
    SUGAR = "sugar"
    SODIUM = "sodium"
    POTASSIUM = "potassium"
    CALCIUM = "calcium"
    IRON = "iron"
    VITAMIN_A = "vitamin_a"
    VITAMIN_C = "vitamin_c"
    VITAMIN_D = "vitamin_d"
    VITAMIN_E = "vitamin_e"
    VITAMIN_K = "vitamin_k"
    VITAMIN_B1 = "vitamin_b1"
    VITAMIN_B2 = "vitamin_b2"
    VITAMIN_B3 = "vitamin_b3"
    VITAMIN_B6 = "vitamin_b6"
    VITAMIN_B12 = "vitamin_b12"
    FOLATE = "folate"
    ZINC = "zinc"
    MAGNESIUM = "magnesium"
    PHOSPHORUS = "phosphorus"


class Unit(str, Enum):
    """Measurement units."""
    GRAMS = "g"
    MILLIGRAMS = "mg"
    MICROGRAMS = "mcg"
    CALORIES = "cal"
    KILOCALORIES = "kcal"
    CUPS = "cups"
    TABLESPOONS = "tbsp"
    TEASPOONS = "tsp"
    OUNCES = "oz"
    POUNDS = "lbs"
    MILLILITERS = "ml"
    LITERS = "L"


class FoodCategory(str, Enum):
    """Food categories."""
    FRUITS = "fruits"
    VEGETABLES = "vegetables"
    GRAINS = "grains"
    PROTEIN = "protein"
    DAIRY = "dairy"
    FATS = "fats"
    SWEETS = "sweets"
    BEVERAGES = "beverages"
    SNACKS = "snacks"
    CONDIMENTS = "condiments"
    HERBS_SPICES = "herbs_spices"


class NutritionalData(BaseModel):
    """Nutritional information for a food item."""
    
    calories: float = Field(..., description="Calories per serving")
    protein: float = Field(0.0, description="Protein in grams")
    carbs: float = Field(0.0, description="Carbohydrates in grams")
    fat: float = Field(0.0, description="Fat in grams")
    fiber: float = Field(0.0, description="Fiber in grams")
    sugar: float = Field(0.0, description="Sugar in grams")
    sodium: float = Field(0.0, description="Sodium in milligrams")
    potassium: float = Field(0.0, description="Potassium in milligrams")
    calcium: float = Field(0.0, description="Calcium in milligrams")
    iron: float = Field(0.0, description="Iron in milligrams")
    vitamin_a: float = Field(0.0, description="Vitamin A in micrograms")
    vitamin_c: float = Field(0.0, description="Vitamin C in milligrams")
    vitamin_d: float = Field(0.0, description="Vitamin D in micrograms")
    vitamin_e: float = Field(0.0, description="Vitamin E in milligrams")
    vitamin_k: float = Field(0.0, description="Vitamin K in micrograms")
    vitamin_b1: float = Field(0.0, description="Vitamin B1 (Thiamin) in milligrams")
    vitamin_b2: float = Field(0.0, description="Vitamin B2 (Riboflavin) in milligrams")
    vitamin_b3: float = Field(0.0, description="Vitamin B3 (Niacin) in milligrams")
    vitamin_b6: float = Field(0.0, description="Vitamin B6 in milligrams")
    vitamin_b12: float = Field(0.0, description="Vitamin B12 in micrograms")
    folate: float = Field(0.0, description="Folate in micrograms")
    zinc: float = Field(0.0, description="Zinc in milligrams")
    magnesium: float = Field(0.0, description="Magnesium in milligrams")
    phosphorus: float = Field(0.0, description="Phosphorus in milligrams")
    
    # Additional nutritional data
    saturated_fat: float = Field(0.0, description="Saturated fat in grams")
    trans_fat: float = Field(0.0, description="Trans fat in grams")
    cholesterol: float = Field(0.0, description="Cholesterol in milligrams")
    glycemic_index: Optional[float] = Field(None, description="Glycemic index")
    
    @validator('calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium', 
               'potassium', 'calcium', 'iron', 'vitamin_a', 'vitamin_c', 'vitamin_d',
               'vitamin_e', 'vitamin_k', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3',
               'vitamin_b6', 'vitamin_b12', 'folate', 'zinc', 'magnesium', 'phosphorus',
               'saturated_fat', 'trans_fat', 'cholesterol')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Nutritional values cannot be negative")
        return v


class FoodItem(BaseModel):
    """A food item with nutritional information."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    name: str = Field(..., description="Food name")
    brand: Optional[str] = Field(None, description="Brand name")
    category: FoodCategory = Field(..., description="Food category")
    serving_size: float = Field(..., description="Serving size")
    serving_unit: Unit = Field(..., description="Serving unit")
    nutrition: NutritionalData = Field(..., description="Nutritional information")
    
    # Additional metadata
    barcode: Optional[str] = Field(None, description="Product barcode")
    ingredients: Optional[List[str]] = Field(None, description="List of ingredients")
    allergens: Optional[List[str]] = Field(None, description="List of allergens")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    region: Optional[str] = Field(None, description="Geographical region")
    
    # Database fields
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    source: Optional[str] = Field(None, description="Data source (USDA, Nutritionix, etc.)")
    confidence_score: Optional[float] = Field(None, description="Recognition confidence score")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Grilled Chicken Breast",
                "brand": "Organic Valley",
                "category": "protein",
                "serving_size": 100.0,
                "serving_unit": "g",
                "nutrition": {
                    "calories": 165.0,
                    "protein": 31.0,
                    "carbs": 0.0,
                    "fat": 3.6,
                    "fiber": 0.0,
                    "sugar": 0.0,
                    "sodium": 74.0
                },
                "cuisine": "american",
                "region": "north_america"
            }
        }
    }


class MealAnalysis(BaseModel):
    """Analysis of a complete meal."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    meal_type: str = Field(..., description="Breakfast, lunch, dinner, snack")
    timestamp: datetime = Field(..., description="Meal timestamp")
    
    # Food items in the meal
    food_items: List[FoodItem] = Field(..., description="List of food items")
    
    # Total nutritional values
    total_nutrition: NutritionalData = Field(..., description="Total nutritional values")
    
    # Analysis results
    health_score: Optional[float] = Field(None, description="Overall health score (0-100)")
    balance_score: Optional[float] = Field(None, description="Nutritional balance score")
    variety_score: Optional[float] = Field(None, description="Food variety score")
    
    # Recommendations
    recommendations: Optional[List[str]] = Field(None, description="Nutritional recommendations")
    warnings: Optional[List[str]] = Field(None, description="Nutritional warnings")
    
    # Metadata
    image_url: Optional[str] = Field(None, description="URL to meal image")
    notes: Optional[str] = Field(None, description="User notes")
    location: Optional[str] = Field(None, description="Meal location")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "meal_type": "lunch",
                "timestamp": "2024-01-01T12:00:00Z",
                "food_items": [
                    {
                        "name": "Grilled Chicken Breast",
                        "category": "protein",
                        "serving_size": 100.0,
                        "serving_unit": "g",
                        "nutrition": {
                            "calories": 165.0,
                            "protein": 31.0,
                            "carbs": 0.0,
                            "fat": 3.6
                        }
                    }
                ],
                "total_nutrition": {
                    "calories": 165.0,
                    "protein": 31.0,
                    "carbs": 0.0,
                    "fat": 3.6
                },
                "health_score": 85.0,
                "recommendations": ["Add more vegetables for fiber"]
            }
        }


class DailyNutrition(BaseModel):
    """Daily nutritional summary."""
    
    user_id: str = Field(..., description="User identifier")
    date: datetime = Field(..., description="Date")
    
    # Daily totals
    total_calories: float = Field(0.0, description="Total calories consumed")
    total_protein: float = Field(0.0, description="Total protein in grams")
    total_carbs: float = Field(0.0, description="Total carbohydrates in grams")
    total_fat: float = Field(0.0, description="Total fat in grams")
    total_fiber: float = Field(0.0, description="Total fiber in grams")
    total_sugar: float = Field(0.0, description="Total sugar in grams")
    total_sodium: float = Field(0.0, description="Total sodium in milligrams")
    
    # Goal comparison
    calorie_goal: Optional[float] = Field(None, description="Daily calorie goal")
    protein_goal: Optional[float] = Field(None, description="Daily protein goal")
    carb_goal: Optional[float] = Field(None, description="Daily carbohydrate goal")
    fat_goal: Optional[float] = Field(None, description="Daily fat goal")
    
    # Progress percentages
    calorie_progress: Optional[float] = Field(None, description="Calorie goal progress %")
    protein_progress: Optional[float] = Field(None, description="Protein goal progress %")
    carb_progress: Optional[float] = Field(None, description="Carb goal progress %")
    fat_progress: Optional[float] = Field(None, description="Fat goal progress %")
    
    # Meals
    meals: List[MealAnalysis] = Field(default_factory=list, description="List of meals")
    
    # Analysis
    daily_score: Optional[float] = Field(None, description="Daily nutrition score")
    recommendations: Optional[List[str]] = Field(None, description="Daily recommendations")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "date": "2024-01-01T00:00:00Z",
                "total_calories": 1850.0,
                "total_protein": 120.0,
                "total_carbs": 200.0,
                "total_fat": 65.0,
                "calorie_goal": 2000.0,
                "calorie_progress": 92.5,
                "daily_score": 88.0,
                "recommendations": ["Consider adding more fiber-rich foods"]
            }
        } 