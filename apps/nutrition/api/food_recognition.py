"""
Food Recognition API Endpoints

Endpoints for image-based food recognition and nutritional analysis.
"""

import logging
import base64
import io
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse

from common.middleware.auth import get_current_user
from apps.nutrition.models.food_recognition_models import (
    FoodRecognitionRequest, FoodRecognitionResponse, BatchFoodRecognitionRequest,
    BatchFoodRecognitionResponse, RecognizedFood, RecognitionModel
)
from apps.nutrition.services.food_recognition_service import FoodRecognitionService

logger = logging.getLogger(__name__)

food_recognition_router = APIRouter()


@food_recognition_router.post("/recognize", response_model=FoodRecognitionResponse)
async def recognize_food_from_image(
    image: UploadFile = File(...),
    user_id: str = Form(...),
    meal_type: Optional[str] = Form(None),
    cuisine_hint: Optional[str] = Form(None),
    region_hint: Optional[str] = Form(None),
    dietary_restrictions: Optional[str] = Form(None),
    preferred_units: Optional[str] = Form(None),
    enable_portion_estimation: bool = Form(True),
    enable_nutrition_lookup: bool = Form(True),
    enable_cultural_recognition: bool = Form(True),
    models_to_use: Optional[str] = Form("google_vision"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Recognize food items from an uploaded image and provide nutritional analysis.
    
    Args:
        image: Food image file
        user_id: User identifier
        meal_type: Type of meal (breakfast, lunch, dinner, snack)
        cuisine_hint: Hint about cuisine type
        region_hint: Hint about geographical region
        dietary_restrictions: Comma-separated dietary restrictions
        preferred_units: Preferred measurement units
        enable_portion_estimation: Enable portion size estimation
        enable_nutrition_lookup: Enable nutritional data lookup
        enable_cultural_recognition: Enable cultural/regional recognition
        models_to_use: Comma-separated list of recognition models
        current_user: Authenticated user information
    
    Returns:
        Food recognition results with nutritional analysis
    """
    try:
        # Verify user can access this data
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Processing food recognition for user {user_id}")
        
        # Read image data
        image_data = await image.read()
        
        # Parse models to use
        model_list = [RecognitionModel(model.strip()) for model in models_to_use.split(",")]
        
        # Parse dietary restrictions
        restrictions = []
        if dietary_restrictions:
            restrictions = [r.strip() for r in dietary_restrictions.split(",")]
        
        # Create recognition request
        request_data = {
            "user_id": user_id,
            "image_data": image_data,
            "image_format": image.filename.split(".")[-1].lower(),
            "models_to_use": model_list,
            "enable_portion_estimation": enable_portion_estimation,
            "enable_nutrition_lookup": enable_nutrition_lookup,
            "enable_cultural_recognition": enable_cultural_recognition,
            "meal_type": meal_type,
            "cuisine_hint": cuisine_hint,
            "region_hint": region_hint,
            "dietary_restrictions": restrictions,
            "preferred_units": preferred_units
        }
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Process the image
        recognition_result = await recognition_service.recognize_food(request_data)
        
        logger.info(f"Food recognition completed for user {user_id}")
        return recognition_result
        
    except Exception as e:
        logger.error(f"Error in food recognition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recognize food from image"
        )


@food_recognition_router.post("/recognize-batch", response_model=BatchFoodRecognitionResponse)
async def recognize_food_batch(
    batch_request: BatchFoodRecognitionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process multiple food images in batch for recognition and analysis.
    
    Args:
        batch_request: Batch recognition request with multiple images
        current_user: Authenticated user information
    
    Returns:
        Batch recognition results
    """
    try:
        # Verify user can access this data
        if current_user["id"] != batch_request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Processing batch food recognition for user {batch_request.user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Process batch
        batch_result = await recognition_service.recognize_food_batch(batch_request)
        
        logger.info(f"Batch food recognition completed for user {batch_request.user_id}")
        return batch_result
        
    except Exception as e:
        logger.error(f"Error in batch food recognition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch food recognition"
        )


@food_recognition_router.post("/correct-recognition")
async def correct_food_recognition(
    recognition_id: str,
    corrections: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Allow users to correct food recognition results and improve future recognition.
    
    Args:
        recognition_id: Recognition result identifier
        corrections: User corrections for food items
        current_user: Authenticated user information
    
    Returns:
        Updated recognition results
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Processing recognition corrections for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Apply corrections
        updated_result = await recognition_service.correct_recognition(
            recognition_id=recognition_id,
            user_id=user_id,
            corrections=corrections
        )
        
        logger.info(f"Recognition corrections applied for user {user_id}")
        return updated_result
        
    except Exception as e:
        logger.error(f"Error applying recognition corrections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply recognition corrections"
        )


@food_recognition_router.get("/recognition-history/{user_id}")
async def get_recognition_history(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's food recognition history.
    
    Args:
        user_id: User identifier
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated user information
    
    Returns:
        List of past recognition results
    """
    try:
        # Verify user can access this data
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting recognition history for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Get history
        history = await recognition_service.get_recognition_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recognition history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recognition history"
        )


@food_recognition_router.get("/recognition-stats/{user_id}")
async def get_recognition_statistics(
    user_id: str,
    timeframe: str = "30_days",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get food recognition statistics for a user.
    
    Args:
        user_id: User identifier
        timeframe: Time period for statistics (7_days, 30_days, 90_days, 1_year)
        current_user: Authenticated user information
    
    Returns:
        Recognition statistics
    """
    try:
        # Verify user can access this data
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Getting recognition statistics for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Get statistics
        stats = await recognition_service.get_recognition_statistics(
            user_id=user_id,
            timeframe=timeframe
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recognition statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recognition statistics"
        )


@food_recognition_router.post("/estimate-portion")
async def estimate_portion_size(
    food_name: str,
    image_data: bytes,
    reference_object: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Estimate portion size for a specific food item from an image.
    
    Args:
        food_name: Name of the food item
        image_data: Image data for portion estimation
        reference_object: Optional reference object for size comparison
        current_user: Authenticated user information
    
    Returns:
        Portion size estimation
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Estimating portion size for {food_name} for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Estimate portion
        portion_estimate = await recognition_service.estimate_portion_size(
            food_name=food_name,
            image_data=image_data,
            reference_object=reference_object
        )
        
        return portion_estimate
        
    except Exception as e:
        logger.error(f"Error estimating portion size: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate portion size"
        )


@food_recognition_router.get("/supported-models")
async def get_supported_models():
    """
    Get list of supported food recognition models.
    
    Returns:
        List of available models with capabilities
    """
    try:
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Get supported models
        models = await recognition_service.get_supported_models()
        
        return {
            "models": models,
            "default_model": "google_vision",
            "recommendations": {
                "high_accuracy": "google_vision",
                "fast_processing": "azure_vision",
                "cost_effective": "custom_cnn"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting supported models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported models"
        )


@food_recognition_router.get("/model-performance")
async def get_model_performance(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get performance metrics for food recognition models.
    
    Args:
        current_user: Authenticated user information
    
    Returns:
        Model performance metrics
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Getting model performance for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Get performance metrics
        performance = await recognition_service.get_model_performance()
        
        return performance
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model performance"
        )


@food_recognition_router.post("/improve-recognition")
async def improve_recognition_model(
    training_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit training data to improve recognition models.
    
    Args:
        training_data: Training data for model improvement
        current_user: Authenticated user information
    
    Returns:
        Training submission confirmation
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Submitting training data for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Submit training data
        result = await recognition_service.submit_training_data(
            user_id=user_id,
            training_data=training_data
        )
        
        logger.info(f"Training data submitted successfully for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error submitting training data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit training data"
        )


@food_recognition_router.delete("/recognition/{recognition_id}")
async def delete_recognition_result(
    recognition_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a food recognition result.
    
    Args:
        recognition_id: Recognition result identifier
        current_user: Authenticated user information
    
    Returns:
        Deletion confirmation
    """
    try:
        user_id = current_user["id"]
        logger.info(f"Deleting recognition result {recognition_id} for user {user_id}")
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Delete recognition result
        result = await recognition_service.delete_recognition_result(
            recognition_id=recognition_id,
            user_id=user_id
        )
        
        logger.info(f"Recognition result {recognition_id} deleted for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error deleting recognition result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recognition result"
        ) 


@food_recognition_router.post("/analyze-nutrition", response_model=FoodRecognitionResponse)
async def analyze_food_nutrition(
    image: UploadFile = File(...),
    user_id: str = Form(...),
    meal_type: Optional[str] = Form(None),
    enable_detailed_analysis: bool = Form(True),
    include_micronutrients: bool = Form(True),
    include_allergen_check: bool = Form(True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Comprehensive food nutrition analysis from image with detailed calorie and macronutrient calculations.
    
    This endpoint provides:
    - Food recognition from image
    - Portion size estimation
    - Detailed calorie calculations
    - Macronutrient breakdown (protein, carbs, fat)
    - Micronutrient analysis (if enabled)
    - Allergen warnings (if enabled)
    - Nutrition suggestions and warnings
    
    Args:
        image: Food image file
        user_id: User identifier
        meal_type: Type of meal (breakfast, lunch, dinner, snack)
        enable_detailed_analysis: Enable detailed nutrition analysis
        include_micronutrients: Include micronutrient calculations
        include_allergen_check: Include allergen warnings
        current_user: Authenticated user information
    
    Returns:
        Comprehensive nutrition analysis with calorie and macronutrient breakdown
    """
    try:
        # Verify user can access this data
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info(f"Processing comprehensive nutrition analysis for user {user_id}")
        
        # Read image data
        image_data = await image.read()
        
        # Create comprehensive analysis request
        request_data = {
            "user_id": user_id,
            "image_data": image_data,
            "image_format": image.filename.split(".")[-1].lower(),
            "models_to_use": ["openai_vision", "google_vision"],
            "enable_portion_estimation": True,
            "enable_nutrition_lookup": True,
            "enable_cultural_recognition": True,
            "meal_type": meal_type,
            "enable_detailed_analysis": enable_detailed_analysis,
            "include_micronutrients": include_micronutrients,
            "include_allergen_check": include_allergen_check
        }
        
        # Initialize recognition service
        recognition_service = FoodRecognitionService()
        
        # Process the image with comprehensive nutrition analysis
        analysis_result = await recognition_service.recognize_food(request_data)
        
        # Add additional nutrition insights
        if enable_detailed_analysis:
            analysis_result["nutrition_insights"] = _generate_detailed_nutrition_insights(analysis_result)
        
        logger.info(f"Comprehensive nutrition analysis completed for user {user_id}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error in comprehensive nutrition analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze food nutrition from image"
        )


def _generate_detailed_nutrition_insights(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate detailed nutrition insights from analysis results.
    """
    total_calories = analysis_result.get("total_calories", 0)
    total_protein = analysis_result.get("total_protein", 0)
    total_carbs = analysis_result.get("total_carbs", 0)
    total_fat = analysis_result.get("total_fat", 0)
    
    # Calculate macronutrient percentages
    total_macros = total_protein + total_carbs + total_fat
    if total_macros > 0:
        protein_percentage = (total_protein * 4 / total_calories * 100) if total_calories > 0 else 0
        carbs_percentage = (total_carbs * 4 / total_calories * 100) if total_calories > 0 else 0
        fat_percentage = (total_fat * 9 / total_calories * 100) if total_calories > 0 else 0
    else:
        protein_percentage = carbs_percentage = fat_percentage = 0
    
    # Calculate daily value percentages (based on 2000 calorie diet)
    daily_values = {
        "calories": (total_calories / 2000) * 100,
        "protein": (total_protein / 50) * 100,  # 50g daily value
        "carbs": (total_carbs / 275) * 100,     # 275g daily value
        "fat": (total_fat / 65) * 100,          # 65g daily value
        "fiber": sum(food.get("fiber_g", 0) for food in analysis_result.get("recognized_foods", [])) / 28 * 100,  # 28g daily value
        "sodium": sum(food.get("sodium_mg", 0) for food in analysis_result.get("recognized_foods", [])) / 2300 * 100  # 2300mg daily value
    }
    
    # Generate meal type recommendations
    meal_recommendations = []
    if total_calories < 300:
        meal_recommendations.append("Light meal - suitable for snacks or small meals")
    elif 300 <= total_calories <= 600:
        meal_recommendations.append("Moderate meal - good for lunch or dinner")
    elif total_calories > 600:
        meal_recommendations.append("Heavy meal - consider portion control")
    
    # Macronutrient balance assessment
    macro_balance = "balanced"
    if protein_percentage < 10:
        macro_balance = "low protein"
    elif protein_percentage > 35:
        macro_balance = "high protein"
    elif carbs_percentage > 70:
        macro_balance = "high carb"
    elif fat_percentage > 45:
        macro_balance = "high fat"
    
    return {
        "macronutrient_breakdown": {
            "protein_g": total_protein,
            "protein_percentage": round(protein_percentage, 1),
            "carbs_g": total_carbs,
            "carbs_percentage": round(carbs_percentage, 1),
            "fat_g": total_fat,
            "fat_percentage": round(fat_percentage, 1),
            "balance": macro_balance
        },
        "daily_value_percentages": {
            "calories": round(daily_values["calories"], 1),
            "protein": round(daily_values["protein"], 1),
            "carbs": round(daily_values["carbs"], 1),
            "fat": round(daily_values["fat"], 1),
            "fiber": round(daily_values["fiber"], 1),
            "sodium": round(daily_values["sodium"], 1)
        },
        "meal_assessment": {
            "calorie_level": "light" if total_calories < 300 else "moderate" if total_calories <= 600 else "heavy",
            "recommendations": meal_recommendations,
            "suitable_for": _determine_meal_suitability(total_calories, total_protein, total_carbs, total_fat)
        },
        "nutrition_score": _calculate_nutrition_score(analysis_result),
        "health_indicators": _generate_health_indicators(analysis_result)
    }


def _determine_meal_suitability(calories: float, protein: float, carbs: float, fat: float) -> List[str]:
    """
    Determine what meal types this nutrition profile is suitable for.
    """
    suitable_for = []
    
    if calories < 200:
        suitable_for.append("snack")
    elif 200 <= calories <= 400:
        suitable_for.append("breakfast")
        suitable_for.append("light lunch")
    elif 400 <= calories <= 600:
        suitable_for.append("lunch")
        suitable_for.append("dinner")
    elif calories > 600:
        suitable_for.append("main meal")
    
    if protein > 25:
        suitable_for.append("post-workout")
    
    if carbs > 50:
        suitable_for.append("pre-workout")
    
    return list(set(suitable_for))  # Remove duplicates


def _calculate_nutrition_score(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a nutrition score based on various factors.
    """
    total_calories = analysis_result.get("total_calories", 0)
    total_protein = analysis_result.get("total_protein", 0)
    total_carbs = analysis_result.get("total_carbs", 0)
    total_fat = analysis_result.get("total_fat", 0)
    
    score = 0
    max_score = 100
    
    # Calorie appropriateness (20 points)
    if 200 <= total_calories <= 800:
        score += 20
    elif 100 <= total_calories <= 1000:
        score += 15
    else:
        score += 5
    
    # Protein adequacy (25 points)
    if total_protein >= 15:
        score += 25
    elif total_protein >= 10:
        score += 15
    elif total_protein >= 5:
        score += 10
    else:
        score += 5
    
    # Macronutrient balance (25 points)
    total_macros = total_protein + total_carbs + total_fat
    if total_macros > 0:
        protein_ratio = total_protein / total_macros
        carbs_ratio = total_carbs / total_macros
        fat_ratio = total_fat / total_macros
        
        if 0.1 <= protein_ratio <= 0.35 and 0.3 <= carbs_ratio <= 0.7 and 0.1 <= fat_ratio <= 0.45:
            score += 25
        elif 0.05 <= protein_ratio <= 0.4 and 0.2 <= carbs_ratio <= 0.8 and 0.05 <= fat_ratio <= 0.5:
            score += 20
        else:
            score += 10
    
    # Food variety (15 points)
    food_count = len(analysis_result.get("recognized_foods", []))
    if food_count >= 3:
        score += 15
    elif food_count >= 2:
        score += 10
    else:
        score += 5
    
    # Warnings deduction (15 points)
    warnings = analysis_result.get("warnings", [])
    score -= len(warnings) * 3
    score = max(0, score)  # Don't go below 0
    
    return {
        "overall_score": score,
        "max_score": max_score,
        "percentage": round((score / max_score) * 100, 1),
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D" if score >= 20 else "F"
    }


def _generate_health_indicators(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate health indicators based on nutrition analysis.
    """
    total_calories = analysis_result.get("total_calories", 0)
    total_protein = analysis_result.get("total_protein", 0)
    total_carbs = analysis_result.get("total_carbs", 0)
    total_fat = analysis_result.get("total_fat", 0)
    
    indicators = {
        "heart_health": "good",
        "weight_management": "neutral",
        "muscle_building": "neutral",
        "energy_levels": "good",
        "digestive_health": "good"
    }
    
    # Heart health indicators
    if total_fat > 30:
        indicators["heart_health"] = "moderate"
    if total_fat > 50:
        indicators["heart_health"] = "poor"
    
    # Weight management indicators
    if total_calories > 800:
        indicators["weight_management"] = "challenging"
    elif total_calories < 200:
        indicators["weight_management"] = "supportive"
    
    # Muscle building indicators
    if total_protein >= 25:
        indicators["muscle_building"] = "supportive"
    elif total_protein < 10:
        indicators["muscle_building"] = "challenging"
    
    # Energy levels
    if total_carbs >= 30:
        indicators["energy_levels"] = "good"
    elif total_carbs < 15:
        indicators["energy_levels"] = "moderate"
    
    return indicators 