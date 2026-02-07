"""
Health Scores API
RESTful API endpoints for health scores and assessments.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.health_score_models import (
    HealthScoreCreate, HealthScoreUpdate, HealthScoreResponse,
    HealthScoreTrendResponse, RiskAssessmentResponse, WellnessIndexResponse,
    ScoreType, RiskLevel, TrendDirection
)
from ..services.insight_service import InsightService
from common.database import get_db
from common.middleware.auth import get_current_user

# Import User model if available, otherwise use a simple type
try:
    from apps.auth.models import User
except ImportError:
    # Create a simple User type for type hints when auth models are not available
    from typing import TypeVar
    User = TypeVar('User')

router = APIRouter(prefix="/health-scores", tags=["health_scores"])


@router.get("/", response_model=List[HealthScoreResponse])
async def get_health_scores(
    request: Request,
    patient_id: UUID,
    score_type: Optional[ScoreType] = Query(None, description="Filter by score type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get health scores for a patient with optional filtering.
    
    Args:
        patient_id: Patient ID
        score_type: Filter by score type
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[HealthScoreResponse]: List of health scores
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        scores = await service.get_health_scores(
            patient_id=patient_id,
            db=db,
            score_type=score_type.value if score_type else None,
            limit=limit,
            offset=offset
        )
        
        return scores
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health scores: {str(e)}")


@router.get("/simple-health")
async def simple_health_check():
    """Simple health check endpoint without any imports."""
    return {
        "service": "health_scores",
        "status": "healthy",
        "message": "Health Scores API is running (simple endpoint)"
    }


@router.get("/{score_id}", response_model=HealthScoreResponse)
async def get_health_score_by_id(
    request: Request,
    score_id: UUID = Path(..., description="Health Score ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific health score by ID.
    
    Args:
        score_id: Health Score ID
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        HealthScoreResponse: Health score details
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        score = await service.get_health_score_by_id(score_id, patient_id, db)
        
        if not score:
            raise HTTPException(status_code=404, detail="Health score not found")
        
        return score
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health score: {str(e)}")


@router.post("/", response_model=HealthScoreResponse)
async def create_health_score(
    request: Request,
    score_data: HealthScoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new health score.
    
    Args:
        score_data: Health score creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        HealthScoreResponse: Created health score
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(score_data.patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        score = await service.create_health_score(score_data, db)
        
        return score
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create health score: {str(e)}")


@router.put("/{score_id}", response_model=HealthScoreResponse)
async def update_health_score(
    request: Request,
    score_id: UUID = Path(..., description="Health Score ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    update_data: HealthScoreUpdate = Body(..., description="Update data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a health score.
    
    Args:
        score_id: Health Score ID
        patient_id: Patient ID
        update_data: Update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        HealthScoreResponse: Updated health score
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        score = await service.update_health_score(score_id, patient_id, update_data, db)
        
        if not score:
            raise HTTPException(status_code=404, detail="Health score not found")
        
        return score
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update health score: {str(e)}")


@router.delete("/{score_id}")
async def delete_health_score(
    request: Request,
    score_id: UUID = Path(..., description="Health Score ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a health score.
    
    Args:
        score_id: Health Score ID
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Deletion confirmation
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        success = await service.delete_health_score(score_id, patient_id, db)
        
        if not success:
            raise HTTPException(status_code=404, detail="Health score not found")
        
        return {"message": "Health score deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete health score: {str(e)}")


@router.get("/summary/{patient_id}")
async def get_health_scores_summary(
    request: Request,
    patient_id: UUID = Path(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of health scores for a patient.
    
    Args:
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Health scores summary
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        summary = await service.get_health_scores_summary(patient_id, db)
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health scores summary: {str(e)}")


@router.get("/types")
async def get_score_types():
    """
    Get available health score types.
    
    Returns:
        dict: Available score types
    """
    return {
        "success": True,
        "data": {
            "score_types": [score_type.value for score_type in ScoreType],
            "risk_levels": [risk_level.value for risk_level in RiskLevel],
            "trend_directions": [trend.value for trend in TrendDirection]
        }
    }


@router.get("/test")
async def test_endpoint():
    """
    Test endpoint to verify router is working.
    
    Returns:
        dict: Simple test response
    """
    return {
        "message": "Health scores router is working",
        "timestamp": datetime.utcnow().isoformat()
    } 