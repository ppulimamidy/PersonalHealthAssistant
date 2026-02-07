"""
Health Analysis API Router

Main endpoints for health image analysis and medical condition detection.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from apps.health_analysis.models.health_analysis_models import (
    HealthAnalysisRequest,
    HealthAnalysisResponse,
    ConditionDetectionRequest,
    ConditionDetectionResponse,
    MedicalQueryRequest,
    MedicalQueryResponse,
    AnalysisHistoryResponse
)
from apps.health_analysis.services.health_analysis_service import HealthAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter()

# Global service instance (will be set in main.py)
health_analysis_service: HealthAnalysisService = None


def get_health_analysis_service() -> HealthAnalysisService:
    """Get health analysis service instance."""
    if not health_analysis_service:
        raise HTTPException(status_code=503, detail="Service not available")
    return health_analysis_service


@router.post("/analyze", response_model=HealthAnalysisResponse)
async def analyze_health_image(
    image: UploadFile = File(..., description="Health-related image to analyze"),
    user_query: Optional[str] = Form(None, description="User's specific health question or concern"),
    body_part: Optional[str] = Form(None, description="Body part affected (e.g., arm, leg, face)"),
    symptoms: Optional[str] = Form(None, description="Additional symptoms description"),
    urgency_level: Optional[str] = Form("normal", description="Urgency level: low, normal, high, emergency"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Analyze a health-related image and provide comprehensive medical insights.
    
    This endpoint analyzes images for various health conditions including:
    - Skin conditions (rashes, burns, bites, infections)
    - Injuries (cuts, bruises, broken bones)
    - Eye problems
    - Dental issues
    - And other medical concerns
    """
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Create analysis request
        request_data = {
            "user_id": current_user["id"],
            "image_data": image_data,
            "image_format": image.content_type.split('/')[-1],
            "user_query": user_query,
            "body_part": body_part,
            "symptoms": symptoms,
            "urgency_level": urgency_level,
            "timestamp": datetime.utcnow()
        }
        
        # Perform analysis
        analysis_result = await service.analyze_health_image(request_data)
        
        # Store analysis in database
        await service.store_analysis_result(current_user["id"], analysis_result)
        
        logger.info(f"Health analysis completed for user {current_user['id']}")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Health analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.post("/detect-condition", response_model=ConditionDetectionResponse)
async def detect_medical_condition(
    image: UploadFile = File(..., description="Image to analyze for condition detection"),
    condition_type: str = Form(..., description="Type of condition to detect (skin, injury, eye, dental, etc.)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Detect specific medical conditions from images.
    
    Supported condition types:
    - skin: rashes, burns, bites, infections, moles, acne
    - injury: cuts, bruises, fractures, sprains
    - eye: redness, swelling, discharge, vision issues
    - dental: cavities, gum disease, tooth damage
    - respiratory: breathing issues, chest problems
    - gastrointestinal: abdominal issues, digestive problems
    """
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Create detection request
        request_data = {
            "user_id": current_user["id"],
            "image_data": image_data,
            "condition_type": condition_type,
            "timestamp": datetime.utcnow()
        }
        
        # Perform condition detection
        detection_result = await service.detect_medical_condition(request_data)
        
        logger.info(f"Condition detection completed for user {current_user['id']}")
        
        return detection_result
        
    except Exception as e:
        logger.error(f"Condition detection failed: {e}")
        raise HTTPException(status_code=500, detail="Detection failed")


@router.post("/medical-query", response_model=MedicalQueryResponse)
async def process_medical_query(
    request: MedicalQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Process medical queries with or without images.
    
    This endpoint can handle:
    - Text-only medical questions
    - Image-based medical queries
    - Symptom analysis
    - Treatment recommendations
    - Medication information
    """
    try:
        # Add user ID to request
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Process medical query
        query_result = await service.process_medical_query(request)
        
        logger.info(f"Medical query processed for user {current_user['id']}")
        
        return query_result
        
    except Exception as e:
        logger.error(f"Medical query processing failed: {e}")
        raise HTTPException(status_code=500, detail="Query processing failed")


@router.get("/test-history", response_model=List[AnalysisHistoryResponse])
async def test_get_analysis_history(
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """Test endpoint for analysis history (bypasses authentication)."""
    try:
        # Use a test user ID
        test_user_id = "test-user-123"
        
        history = await service.get_analysis_history(
            user_id=test_user_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get analysis history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/history", response_model=List[AnalysisHistoryResponse])
async def get_analysis_history(
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """Get user's health analysis history."""
    try:
        history = await service.get_analysis_history(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get analysis history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/statistics")
async def get_analysis_statistics(
    timeframe: str = Query("30_days", description="Timeframe for statistics"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """Get health analysis statistics for the user."""
    try:
        stats = await service.get_analysis_statistics(
            user_id=current_user["id"],
            timeframe=timeframe
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get analysis statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/supported-conditions")
async def get_supported_conditions(
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """Get list of supported medical conditions for detection."""
    try:
        conditions = await service.get_supported_conditions()
        return conditions
        
    except Exception as e:
        logger.error(f"Failed to get supported conditions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve supported conditions")


@router.get("/model-performance")
async def get_model_performance(
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """Get performance metrics for health analysis models."""
    try:
        performance = await service.get_model_performance()
        return performance
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model performance") 


 