"""
Pharmacogenomics API endpoints for Personal Health Assistant.

This module provides endpoints for pharmacogenomics including:
- Drug-gene interaction analysis
- Drug response prediction
- Dosage recommendations
- Drug safety assessment
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from apps.auth.models.user import User
from ..models.genomic_data import (
    PharmacogenomicProfile, PharmacogenomicProfileCreate, PharmacogenomicProfileResponse
)
from ..services.pharmacogenomics_service import PharmacogenomicsService

router = APIRouter()


@router.post("/profiles", response_model=PharmacogenomicProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_pharmacogenomic_profile(
    profile: PharmacogenomicProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new pharmacogenomic profile."""
    try:
        service = PharmacogenomicsService(db)
        return await service.create_profile(profile, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles", response_model=List[PharmacogenomicProfileResponse])
async def list_pharmacogenomic_profiles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List pharmacogenomic profiles for the current user."""
    try:
        service = PharmacogenomicsService(db)
        return await service.list_profiles(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles/{profile_id}", response_model=PharmacogenomicProfileResponse)
async def get_pharmacogenomic_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific pharmacogenomic profile by ID."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_profile(profile_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/profiles/{profile_id}", response_model=PharmacogenomicProfileResponse)
async def update_pharmacogenomic_profile(
    profile_id: str,
    profile: PharmacogenomicProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update pharmacogenomic profile."""
    try:
        service = PharmacogenomicsService(db)
        return await service.update_profile(profile_id, profile, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pharmacogenomic_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete pharmacogenomic profile."""
    try:
        service = PharmacogenomicsService(db)
        await service.delete_profile(profile_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/drug-interactions", response_model=List[dict])
async def get_drug_interactions(
    drug_name: Optional[str] = None,
    gene_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drug-gene interactions for the user."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_drug_interactions(
            user_id=current_user.id,
            drug_name=drug_name,
            gene_name=gene_name,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metabolizer-status", response_model=dict)
async def get_metabolizer_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metabolizer status for the user."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_metabolizer_status(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/drug-response", response_model=dict)
async def predict_drug_response(
    drug_name: str,
    dosage: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict drug response based on pharmacogenomic profile."""
    try:
        service = PharmacogenomicsService(db)
        return await service.predict_drug_response(
            user_id=current_user.id,
            drug_name=drug_name,
            dosage=dosage
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/medication-recommendations", response_model=List[dict])
async def get_medication_recommendations(
    condition: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized medication recommendations."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_medication_recommendations(
            user_id=current_user.id,
            condition=condition
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/drug-risks", response_model=List[dict])
async def get_drug_risks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drug-related risks for the user."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_drug_risks(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze-medication", response_model=dict)
async def analyze_medication(
    medication_list: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze medication list for pharmacogenomic interactions."""
    try:
        service = PharmacogenomicsService(db)
        return await service.analyze_medication(
            user_id=current_user.id,
            medication_list=medication_list
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/genes", response_model=List[dict])
async def get_pharmacogenomic_genes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pharmacogenomic genes for the user."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_pharmacogenomic_genes(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/drugs", response_model=List[dict])
async def get_pharmacogenomic_drugs(
    gene_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get drugs with pharmacogenomic implications."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_pharmacogenomic_drugs(
            user_id=current_user.id,
            gene_name=gene_name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/interpret", response_model=dict)
async def interpret_pharmacogenomic_data(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Interpret pharmacogenomic data and generate recommendations."""
    try:
        service = PharmacogenomicsService(db)
        return await service.interpret_pharmacogenomic_data(
            profile_id=profile_id,
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_pharmacogenomic_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pharmacogenomic statistics for the user."""
    try:
        service = PharmacogenomicsService(db)
        return await service.get_pharmacogenomic_statistics(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export-report", response_model=dict)
async def export_pharmacogenomic_report(
    profile_id: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export pharmacogenomic report."""
    try:
        service = PharmacogenomicsService(db)
        return await service.export_pharmacogenomic_report(
            profile_id=profile_id,
            user_id=current_user.id,
            format=format
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 