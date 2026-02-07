"""
Food Recognition Models

Pydantic models for food recognition requests, responses, and data structures.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class RecognitionModel(str, Enum):
    """Available food recognition models."""
    OPENAI_VISION = "openai_vision"
    GOOGLE_VISION = "google_vision"
    AZURE_VISION = "azure_vision"
    CUSTOM_CNN = "custom_cnn"
    NUTRITIONIX = "nutritionix"
    USDA = "usda"


class ImageFormat(str, Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    HEIC = "heic"


class PortionEstimate(BaseModel):
    """Portion size estimation for a food item."""
    
    food_name: str = Field(..., description="Name of the recognized food")
    estimated_quantity: float = Field(..., description="Estimated quantity")
    unit: str = Field(..., description="Unit of measurement")
    confidence: float = Field(..., description="Confidence score (0-1)")
    
    # Visual cues used for estimation
    visual_cues: Optional[List[str]] = Field(None, description="Visual cues used for estimation")
    
    # Reference objects (e.g., "size of a tennis ball")
    reference_object: Optional[str] = Field(None, description="Reference object for size")
    
    # Bounding box coordinates (normalized 0-1)
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Bounding box coordinates")


class RecognizedFood(BaseModel):
    """A recognized food item from an image."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Recognized food name")
    confidence: float = Field(..., description="Recognition confidence (0-1)")
    
    # Alternative names/synonyms
    alternative_names: Optional[List[str]] = Field(None, description="Alternative food names")
    
    # Food category
    category: Optional[str] = Field(None, description="Food category")
    
    # Portion estimation
    portion_estimate: Optional[PortionEstimate] = Field(None, description="Portion size estimation")
    
    # Nutritional data (if available)
    nutrition_per_serving: Optional[Dict[str, float]] = Field(None, description="Nutritional data per serving")
    
    # Recognition metadata
    model_used: RecognitionModel = Field(..., description="Model used for recognition")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    
    # Cultural/regional information
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    region: Optional[str] = Field(None, description="Geographical region")
    
    # User corrections
    user_corrected_name: Optional[str] = Field(None, description="User-corrected food name")
    user_corrected_portion: Optional[float] = Field(None, description="User-corrected portion size")
    user_corrected_unit: Optional[str] = Field(None, description="User-corrected unit")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    model_config = {"protected_namespaces": ()}


class FoodRecognitionRequest(BaseModel):
    """Request for food recognition from image."""
    
    user_id: str = Field(..., description="User identifier")
    image_data: bytes = Field(..., description="Image data (base64 encoded)")
    image_format: ImageFormat = Field(..., description="Image format")
    
    # Recognition options
    models_to_use: List[RecognitionModel] = Field(
        default=[RecognitionModel.GOOGLE_VISION],
        description="Models to use for recognition"
    )
    
    # Processing options
    enable_portion_estimation: bool = Field(True, description="Enable portion size estimation")
    enable_nutrition_lookup: bool = Field(True, description="Enable nutritional data lookup")
    enable_cultural_recognition: bool = Field(True, description="Enable cultural/regional recognition")
    
    # Context information
    meal_type: Optional[str] = Field(None, description="Meal type (breakfast, lunch, dinner, snack)")
    cuisine_hint: Optional[str] = Field(None, description="Hint about cuisine type")
    region_hint: Optional[str] = Field(None, description="Hint about geographical region")
    
    # User preferences
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    preferred_units: Optional[str] = Field(None, description="Preferred measurement units")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")
    
    @validator('image_data')
    def validate_image_size(cls, v):
        # Check if image is not too large (max 10MB)
        if len(v) > 10 * 1024 * 1024:
            raise ValueError("Image size must be less than 10MB")
        return v


class FoodRecognitionResponse(BaseModel):
    """Response from food recognition service."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Recognition results
    recognized_foods: List[RecognizedFood] = Field(..., description="List of recognized foods")
    
    # Overall analysis
    total_calories: float = Field(0.0, description="Total estimated calories")
    total_protein: float = Field(0.0, description="Total estimated protein")
    total_carbs: float = Field(0.0, description="Total estimated carbohydrates")
    total_fat: float = Field(0.0, description="Total estimated fat")
    
    # Processing information
    processing_time: float = Field(..., description="Total processing time in seconds")
    models_used: List[RecognitionModel] = Field(..., description="Models used for recognition")
    
    # Quality metrics
    overall_confidence: float = Field(..., description="Overall confidence score")
    image_quality_score: Optional[float] = Field(None, description="Image quality assessment")
    
    # Recommendations
    suggestions: Optional[List[str]] = Field(None, description="Suggestions for better recognition")
    warnings: Optional[List[str]] = Field(None, description="Warnings about recognition")
    
    # Cultural/regional insights
    detected_cuisine: Optional[str] = Field(None, description="Detected cuisine type")
    detected_region: Optional[str] = Field(None, description="Detected geographical region")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    image_url: Optional[str] = Field(None, description="URL to stored image")


class BatchFoodRecognitionRequest(BaseModel):
    """Request for batch food recognition from multiple images."""
    
    user_id: str = Field(..., description="User identifier")
    images: List[Dict[str, Any]] = Field(..., description="List of images with metadata")
    
    # Batch processing options
    parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_concurrent_requests: int = Field(5, description="Maximum concurrent requests")
    
    # Recognition options (same as single request)
    models_to_use: List[RecognitionModel] = Field(
        default=[RecognitionModel.GOOGLE_VISION],
        description="Models to use for recognition"
    )
    enable_portion_estimation: bool = Field(True, description="Enable portion size estimation")
    enable_nutrition_lookup: bool = Field(True, description="Enable nutritional data lookup")


class BatchFoodRecognitionResponse(BaseModel):
    """Response from batch food recognition service."""
    
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Batch identifier")
    user_id: str = Field(..., description="User identifier")
    
    # Results for each image
    results: List[FoodRecognitionResponse] = Field(..., description="Recognition results for each image")
    
    # Batch statistics
    total_images: int = Field(..., description="Total number of images processed")
    successful_images: int = Field(..., description="Number of successfully processed images")
    failed_images: int = Field(..., description="Number of failed images")
    
    # Overall nutritional summary
    total_calories: float = Field(0.0, description="Total calories across all images")
    total_protein: float = Field(0.0, description="Total protein across all images")
    total_carbs: float = Field(0.0, description="Total carbohydrates across all images")
    total_fat: float = Field(0.0, description="Total fat across all images")
    
    # Processing information
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    average_processing_time: float = Field(..., description="Average processing time per image")
    
    # Quality metrics
    overall_confidence: float = Field(..., description="Overall confidence score")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp") 