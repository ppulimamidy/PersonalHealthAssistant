"""
Genomic analysis API endpoints for Personal Health Assistant.

This module provides endpoints for genomic analysis including:
- Variant calling and annotation
- Quality control analysis
- Statistical analysis
- Report generation
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from apps.auth.models.user import User
from ..models.analysis import (
    GenomicAnalysis, GenomicAnalysisCreate, GenomicAnalysisUpdate, GenomicAnalysisResponse,
    DiseaseRiskAssessment, DiseaseRiskAssessmentCreate, DiseaseRiskAssessmentResponse,
    AncestryAnalysis, AncestryAnalysisCreate, AncestryAnalysisResponse,
    AnalysisType, AnalysisStatus, RiskLevel, ConfidenceLevel
)
from ..services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/", response_model=GenomicAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis: GenomicAnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and start a new genomic analysis."""
    try:
        service = AnalysisService(db)
        analysis_result = await service.create_analysis(analysis, current_user.id)
        
        # Start analysis in background
        background_tasks.add_task(
            service.run_analysis_background,
            analysis_result.id,
            current_user.id
        )
        
        return analysis_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[GenomicAnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 100,
    analysis_type: Optional[AnalysisType] = None,
    status: Optional[AnalysisStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List genomic analyses for the current user."""
    try:
        service = AnalysisService(db)
        return await service.list_analyses(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            analysis_type=analysis_type,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{analysis_id}", response_model=GenomicAnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific analysis by ID."""
    try:
        service = AnalysisService(db)
        return await service.get_analysis(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{analysis_id}", response_model=GenomicAnalysisResponse)
async def update_analysis(
    analysis_id: str,
    analysis: GenomicAnalysisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update analysis."""
    try:
        service = AnalysisService(db)
        return await service.update_analysis(analysis_id, analysis, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete analysis."""
    try:
        service = AnalysisService(db)
        await service.delete_analysis(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{analysis_id}/status", response_model=dict)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis status and progress."""
    try:
        service = AnalysisService(db)
        return await service.get_analysis_status(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{analysis_id}/results", response_model=dict)
async def get_analysis_results(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis results."""
    try:
        service = AnalysisService(db)
        return await service.get_analysis_results(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{analysis_id}/cancel", response_model=GenomicAnalysisResponse)
async def cancel_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel running analysis."""
    try:
        service = AnalysisService(db)
        return await service.cancel_analysis(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Disease Risk Assessment endpoints
@router.post("/disease-risk", response_model=DiseaseRiskAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_disease_risk_assessment(
    assessment: DiseaseRiskAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create disease risk assessment."""
    try:
        service = AnalysisService(db)
        return await service.create_disease_risk_assessment(assessment, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/disease-risk/{assessment_id}", response_model=DiseaseRiskAssessmentResponse)
async def get_disease_risk_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get disease risk assessment."""
    try:
        service = AnalysisService(db)
        return await service.get_disease_risk_assessment(assessment_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/disease-risk", response_model=List[DiseaseRiskAssessmentResponse])
async def list_disease_risk_assessments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List disease risk assessments."""
    try:
        service = AnalysisService(db)
        return await service.list_disease_risk_assessments(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Ancestry Analysis endpoints
@router.post("/ancestry", response_model=AncestryAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_ancestry_analysis(
    analysis: AncestryAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create ancestry analysis."""
    try:
        service = AnalysisService(db)
        return await service.create_ancestry_analysis(analysis, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ancestry/{analysis_id}", response_model=AncestryAnalysisResponse)
async def get_ancestry_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ancestry analysis."""
    try:
        service = AnalysisService(db)
        return await service.get_ancestry_analysis(analysis_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ancestry", response_model=List[AncestryAnalysisResponse])
async def list_ancestry_analyses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List ancestry analyses."""
    try:
        service = AnalysisService(db)
        return await service.list_ancestry_analyses(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Batch analysis endpoints
@router.post("/batch", response_model=List[GenomicAnalysisResponse], status_code=status.HTTP_201_CREATED)
async def create_batch_analysis(
    analyses: List[GenomicAnalysisCreate],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple analyses in batch."""
    try:
        service = AnalysisService(db)
        results = []
        for analysis in analyses:
            result = await service.create_analysis(analysis, current_user.id)
            results.append(result)
            
            # Start analysis in background
            background_tasks.add_task(
                service.run_analysis_background,
                result.id,
                current_user.id
            )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/batch/{batch_id}/status", response_model=dict)
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get batch analysis status."""
    try:
        service = AnalysisService(db)
        return await service.get_batch_status(batch_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) 