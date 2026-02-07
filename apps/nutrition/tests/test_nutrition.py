"""Unit tests for Nutrition service models."""
import pytest
from datetime import datetime, date


class TestNutritionModels:
    def test_nutritional_data_creation(self):
        """Test NutritionalData model with valid data."""
        from apps.nutrition.models.nutrition_models import NutritionalData

        data = NutritionalData(
            calories=250.0,
            protein=20.0,
            carbs=30.0,
            fat=8.0,
            fiber=5.0,
            sugar=3.0,
            sodium=150.0,
        )
        assert data.calories == 250.0
        assert data.protein == 20.0
        assert data.fiber == 5.0

    def test_nutritional_data_negative_rejected(self):
        """Test NutritionalData rejects negative values."""
        from apps.nutrition.models.nutrition_models import NutritionalData

        with pytest.raises(Exception):
            NutritionalData(calories=-100.0)

    def test_food_item_creation(self):
        """Test FoodItem model with full data."""
        from apps.nutrition.models.nutrition_models import FoodItem, NutritionalData

        nutrition = NutritionalData(
            calories=165.0,
            protein=31.0,
            carbs=0.0,
            fat=3.6,
        )
        food = FoodItem(
            name="Grilled Chicken Breast",
            category="protein",
            serving_size=100.0,
            serving_unit="g",
            nutrition=nutrition,
        )
        assert food.name == "Grilled Chicken Breast"
        assert food.nutrition.protein == 31.0
        assert food.category == "protein"

    def test_food_item_missing_required(self):
        """Test FoodItem fails without required fields."""
        from apps.nutrition.models.nutrition_models import FoodItem

        with pytest.raises(Exception):
            FoodItem(name="Incomplete")

    def test_meal_analysis_creation(self):
        """Test MealAnalysis model."""
        from apps.nutrition.models.nutrition_models import (
            MealAnalysis,
            FoodItem,
            NutritionalData,
        )

        nutrition = NutritionalData(calories=165.0, protein=31.0, carbs=0.0, fat=3.6)
        food = FoodItem(
            name="Chicken",
            category="protein",
            serving_size=100.0,
            serving_unit="g",
            nutrition=nutrition,
        )
        meal = MealAnalysis(
            user_id="user-123",
            meal_type="lunch",
            timestamp=datetime.utcnow(),
            food_items=[food],
            total_nutrition=nutrition,
            health_score=85.0,
        )
        assert meal.meal_type == "lunch"
        assert len(meal.food_items) == 1
        assert meal.health_score == 85.0


class TestNutritionGoalModels:
    def test_nutrition_goal_creation(self):
        """Test NutritionGoal model with valid data."""
        from apps.nutrition.models.goals_models import NutritionGoal

        goal = NutritionGoal(
            user_id="user-123",
            goal_type="weight_loss",
            title="Lose 5kg in 8 weeks",
            target_calories=1800.0,
            target_protein=120.0,
            start_date=date(2026, 1, 1),
            target_date=date(2026, 3, 1),
        )
        assert goal.title == "Lose 5kg in 8 weeks"
        assert goal.target_calories == 1800.0
        assert goal.status == "active"
        assert goal.progress_percentage == 0.0

    def test_nutrition_goal_invalid_progress(self):
        """Test NutritionGoal rejects invalid progress percentage."""
        from apps.nutrition.models.goals_models import NutritionGoal

        with pytest.raises(Exception):
            NutritionGoal(
                user_id="user-123",
                goal_type="weight_loss",
                title="Test Goal",
                start_date=date(2026, 1, 1),
                progress_percentage=150.0,
            )

    def test_nutrition_goal_target_before_start(self):
        """Test NutritionGoal rejects target_date before start_date."""
        from apps.nutrition.models.goals_models import NutritionGoal

        with pytest.raises(Exception):
            NutritionGoal(
                user_id="user-123",
                goal_type="weight_loss",
                title="Bad dates",
                start_date=date(2026, 6, 1),
                target_date=date(2026, 1, 1),
            )

    def test_goal_progress_creation(self):
        """Test GoalProgress model."""
        from apps.nutrition.models.goals_models import GoalProgress

        progress = GoalProgress(
            goal_id="goal-123",
            user_id="user-123",
            progress_date=date(2026, 1, 15),
            calories_consumed=1750.0,
            protein_consumed=115.0,
            meals_logged=3,
            goal_compliance_score=95.0,
        )
        assert progress.calories_consumed == 1750.0
        assert progress.meals_logged == 3

    def test_goal_type_enum(self):
        """Test GoalType enum values."""
        from apps.nutrition.models.goals_models import GoalType

        assert GoalType.WEIGHT_LOSS == "weight_loss"
        assert GoalType.MUSCLE_GAIN == "muscle_gain"
        assert GoalType.DIABETES_MANAGEMENT == "diabetes_management"

    def test_nutrition_goal_missing_required(self):
        """Test NutritionGoal fails without required fields."""
        from apps.nutrition.models.goals_models import NutritionGoal

        with pytest.raises(Exception):
            NutritionGoal(user_id="user-123")
