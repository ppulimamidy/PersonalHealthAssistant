"""
Ancestry analysis API endpoints for Personal Health Assistant.

This module provides endpoints for ancestry analysis including:
- Ancestry composition analysis
- Geographic origins mapping
- Haplogroup analysis
- Population matching
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from apps.auth.models.user import User
from ..models.analysis import (
    AncestryAnalysis, AncestryAnalysisCreate, AncestryAnalysisResponse
)
from ..services.ancestry_service import AncestryService

router = APIRouter()


@router.post("/", response_model=AncestryAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_ancestry_analysis(
    analysis: AncestryAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new ancestry analysis."""
    try:
        service = AncestryService(db)
        return await service.create_ancestry_analysis(analysis, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[AncestryAnalysisResponse])
async def list_ancestry_analyses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List ancestry analyses for the current user."""
    try:
        service = AncestryService(db)
        return await service.list_ancestry_analyses(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{analysis_id}", response_model=AncestryAnalysisResponse)
async def get_ancestry_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific ancestry analysis by ID."""
    try:
        service = AncestryService(db)
        return await service.get_ancestry_analysis(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{analysis_id}", response_model=AncestryAnalysisResponse)
async def update_ancestry_analysis(
    analysis_id: str,
    analysis: AncestryAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ancestry analysis."""
    try:
        service = AncestryService(db)
        return await service.update_ancestry_analysis(analysis_id, analysis, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ancestry_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete ancestry analysis."""
    try:
        service = AncestryService(db)
        await service.delete_ancestry_analysis(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/composition", response_model=dict)
async def get_ancestry_composition(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ancestry composition for the user."""
    try:
        service = AncestryService(db)
        return await service.get_ancestry_composition(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/geographic-origins", response_model=List[dict])
async def get_geographic_origins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get geographic origins for the user."""
    try:
        service = AncestryService(db)
        return await service.get_geographic_origins(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/haplogroups", response_model=dict)
async def get_haplogroups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get haplogroups for the user."""
    try:
        service = AncestryService(db)
        return await service.get_haplogroups(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/population-matches", response_model=List[dict])
async def get_population_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get population matches for the user."""
    try:
        service = AncestryService(db)
        return await service.get_population_matches(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/migration-patterns", response_model=List[dict])
async def get_migration_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get migration patterns for the user."""
    try:
        service = AncestryService(db)
        return await service.get_migration_patterns(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/neanderthal-ancestry", response_model=dict)
async def get_neanderthal_ancestry(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Neanderthal ancestry percentage for the user."""
    try:
        service = AncestryService(db)
        return await service.get_neanderthal_ancestry(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/denisovan-ancestry", response_model=dict)
async def get_denisovan_ancestry(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Denisovan ancestry percentage for the user."""
    try:
        service = AncestryService(db)
        return await service.get_denisovan_ancestry(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reference-populations", response_model=List[dict])
async def get_reference_populations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reference populations for the user."""
    try:
        service = AncestryService(db)
        return await service.get_reference_populations(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare", response_model=dict)
async def compare_ancestry(
    other_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare ancestry with another user."""
    try:
        service = AncestryService(db)
        return await service.compare_ancestry(current_user.id, other_user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/regions", response_model=List[dict])
async def get_ancestry_regions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ancestry regions for the user."""
    try:
        service = AncestryService(db)
        return await service.get_ancestry_regions(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/confidence-scores", response_model=dict)
async def get_confidence_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get confidence scores for ancestry analysis."""
    try:
        service = AncestryService(db)
        return await service.get_confidence_scores(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export", response_model=dict)
async def export_ancestry_report(
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export ancestry analysis report."""
    try:
        service = AncestryService(db)
        return await service.export_ancestry_report(
            user_id=current_user.id,
            format=format
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_ancestry_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ancestry statistics for the user."""
    try:
        service = AncestryService(db)
        return await service.get_ancestry_statistics(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 