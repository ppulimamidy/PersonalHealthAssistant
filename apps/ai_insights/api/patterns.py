"""
Patterns API
RESTful API endpoints for health patterns.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.insight_models import (
    HealthPatternCreate, HealthPatternUpdate, HealthPatternResponse
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

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("/", response_model=List[HealthPatternResponse])
async def get_patterns(
    request: Request,
    patient_id: UUID,
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get health patterns for a patient with optional filtering.
    
    Args:
        patient_id: Patient ID
        pattern_type: Filter by pattern type
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[HealthPatternResponse]: List of health patterns
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        patterns = await service.get_health_patterns(
            patient_id=patient_id,
            db=db,
            pattern_type=pattern_type,
            limit=limit,
            offset=offset
        )
        
        return patterns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.get("/{pattern_id}", response_model=HealthPatternResponse)
async def get_pattern_by_id(
    request: Request,
    pattern_id: UUID = Path(..., description="Pattern ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific health pattern by ID.
    
    Args:
        pattern_id: Pattern ID
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        HealthPatternResponse: Pattern details
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        pattern = await service.get_health_pattern_by_id(pattern_id, patient_id, db)
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return pattern
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pattern: {str(e)}")


@router.post("/", response_model=HealthPatternResponse)
async def create_pattern(
    request: Request,
    pattern_data: HealthPatternCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new health pattern.
    
    Args:
        pattern_data: Pattern creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        HealthPatternResponse: Created pattern
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(pattern_data.patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        pattern = await service.create_health_pattern(pattern_data, db)
        
        return pattern
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pattern: {str(e)}")


@router.put("/{pattern_id}", response_model=HealthPatternResponse)
async def update_pattern(
    request: Request,
    pattern_id: UUID = Path(..., description="Pattern ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    update_data: HealthPatternUpdate = Body(..., description="Update data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing health pattern.
    
    Args:
        pattern_id: Pattern ID
        patient_id: Patient ID
        update_data: Update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        HealthPatternResponse: Updated pattern
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        pattern = await service.update_health_pattern(pattern_id, patient_id, update_data, db)
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return pattern
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update pattern: {str(e)}")


@router.delete("/{pattern_id}")
async def delete_pattern(
    request: Request,
    pattern_id: UUID = Path(..., description="Pattern ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a health pattern.
    
    Args:
        pattern_id: Pattern ID
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        deleted = await service.delete_health_pattern(pattern_id, patient_id, db)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return {
            "success": True,
            "message": "Pattern deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete pattern: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for patterns."""
    return {
        "service": "patterns",
        "status": "healthy",
        "message": "Patterns API is running"
    } 