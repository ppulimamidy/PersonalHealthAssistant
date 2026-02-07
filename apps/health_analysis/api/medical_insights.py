"""
Medical Insights API Router

Endpoints for detailed medical analysis, insights, and recommendations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from apps.health_analysis.models.health_analysis_models import (
    MedicalInsightRequest,
    MedicalInsightResponse,
    TreatmentRecommendation,
    SymptomAnalysis,
    RiskAssessment
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


@router.post("/analyze-symptoms", response_model=SymptomAnalysis)
async def analyze_symptoms(
    request: MedicalInsightRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Analyze symptoms and provide detailed medical insights.
    
    This endpoint provides:
    - Symptom interpretation
    - Possible causes
    - Differential diagnosis
    - Severity assessment
    """
    try:
        # Add user context
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Analyze symptoms
        analysis = await service.analyze_symptoms(request)
        
        logger.info(f"Symptom analysis completed for user {current_user['id']}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Symptom analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Symptom analysis failed")


@router.post("/treatment-recommendations", response_model=List[TreatmentRecommendation])
async def get_treatment_recommendations(
    request: MedicalInsightRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Get personalized treatment recommendations based on symptoms and conditions.
    
    Provides:
    - Home care recommendations
    - Over-the-counter medications
    - Lifestyle changes
    - When to seek medical attention
    """
    try:
        # Add user context
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Get recommendations
        recommendations = await service.get_treatment_recommendations(request)
        
        logger.info(f"Treatment recommendations generated for user {current_user['id']}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Treatment recommendations failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.post("/risk-assessment", response_model=RiskAssessment)
async def assess_health_risks(
    request: MedicalInsightRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Assess health risks based on symptoms and conditions.
    
    Provides:
    - Risk level assessment
    - Potential complications
    - Emergency indicators
    - Preventive measures
    """
    try:
        # Add user context
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Assess risks
        assessment = await service.assess_health_risks(request)
        
        logger.info(f"Risk assessment completed for user {current_user['id']}")
        
        return assessment
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail="Risk assessment failed")


@router.get("/medical-literature")
async def search_medical_literature(
    query: str = Query(..., description="Medical search query"),
    condition_type: Optional[str] = Query(None, description="Type of medical condition"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Search medical literature and research for relevant information.
    
    Searches:
    - Medical journals
    - Clinical guidelines
    - Treatment protocols
    - Research studies
    """
    try:
        results = await service.search_medical_literature(
            query=query,
            condition_type=condition_type,
            limit=limit
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Medical literature search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/drug-interactions")
async def check_drug_interactions(
    medications: List[str] = Query(..., description="List of medications to check"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Check for potential drug interactions.
    
    Provides:
    - Interaction severity
    - Risk factors
    - Alternative medications
    - Recommendations
    """
    try:
        interactions = await service.check_drug_interactions(medications)
        
        return interactions
        
    except Exception as e:
        logger.error(f"Drug interaction check failed: {e}")
        raise HTTPException(status_code=500, detail="Drug interaction check failed")


@router.get("/medical-guidelines")
async def get_medical_guidelines(
    condition: str = Query(..., description="Medical condition"),
    specialty: Optional[str] = Query(None, description="Medical specialty"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Get relevant medical guidelines and protocols.
    
    Provides:
    - Clinical guidelines
    - Treatment protocols
    - Best practices
    - Evidence-based recommendations
    """
    try:
        guidelines = await service.get_medical_guidelines(
            condition=condition,
            specialty=specialty
        )
        
        return guidelines
        
    except Exception as e:
        logger.error(f"Medical guidelines retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve guidelines")


@router.post("/second-opinion")
async def get_second_opinion(
    request: MedicalInsightRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
    service: HealthAnalysisService = Depends(get_health_analysis_service)
):
    """
    Get a second medical opinion based on symptoms and analysis.
    
    Provides:
    - Alternative diagnoses
    - Different treatment approaches
    - Additional considerations
    - Expert insights
    """
    try:
        # Add user context
        request.user_id = current_user["id"]
        request.timestamp = datetime.utcnow()
        
        # Get second opinion
        opinion = await service.get_second_opinion(request)
        
        logger.info(f"Second opinion generated for user {current_user['id']}")
        
        return opinion
        
    except Exception as e:
        logger.error(f"Second opinion generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate second opinion") 