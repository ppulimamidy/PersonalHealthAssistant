"""
Genetic variants API endpoints for Personal Health Assistant.

This module provides endpoints for managing genetic variants including:
- Variant discovery and annotation
- Variant filtering and prioritization
- Clinical significance assessment
- Variant database integration
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from apps.auth.models.user import User
from ..models.genomic_data import (
    GeneticVariant, GeneticVariantCreate, GeneticVariantResponse,
    VariantType, VariantClassification
)
from ..services.variant_service import VariantService

router = APIRouter()


@router.post("/", response_model=GeneticVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    variant: GeneticVariantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new genetic variant."""
    try:
        service = VariantService(db)
        return await service.create_variant(variant, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[GeneticVariantResponse])
async def list_variants(
    skip: int = 0,
    limit: int = 100,
    chromosome: Optional[str] = None,
    gene_name: Optional[str] = None,
    variant_type: Optional[VariantType] = None,
    clinical_significance: Optional[VariantClassification] = None,
    genomic_data_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List genetic variants for the current user."""
    try:
        service = VariantService(db)
        return await service.list_variants(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            chromosome=chromosome,
            gene_name=gene_name,
            variant_type=variant_type,
            clinical_significance=clinical_significance,
            genomic_data_id=genomic_data_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{variant_id}", response_model=GeneticVariantResponse)
async def get_variant(
    variant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific variant by ID."""
    try:
        service = VariantService(db)
        return await service.get_variant(variant_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{variant_id}", response_model=GeneticVariantResponse)
async def update_variant(
    variant_id: str,
    variant: GeneticVariantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update variant."""
    try:
        service = VariantService(db)
        return await service.update_variant(variant_id, variant, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete variant."""
    try:
        service = VariantService(db)
        await service.delete_variant(variant_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=List[GeneticVariantResponse])
async def search_variants(
    query: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search variants by various criteria."""
    try:
        service = VariantService(db)
        return await service.search_variants(
            query=query,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chromosome/{chromosome}", response_model=List[GeneticVariantResponse])
async def get_variants_by_chromosome(
    chromosome: str,
    start_position: Optional[int] = None,
    end_position: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get variants by chromosome and position range."""
    try:
        service = VariantService(db)
        return await service.get_variants_by_chromosome(
            chromosome=chromosome,
            start_position=start_position,
            end_position=end_position,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/gene/{gene_name}", response_model=List[GeneticVariantResponse])
async def get_variants_by_gene(
    gene_name: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get variants by gene name."""
    try:
        service = VariantService(db)
        return await service.get_variants_by_gene(
            gene_name=gene_name,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rs/{rs_id}", response_model=List[GeneticVariantResponse])
async def get_variants_by_rs_id(
    rs_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get variants by dbSNP rs ID."""
    try:
        service = VariantService(db)
        return await service.get_variants_by_rs_id(rs_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{variant_id}/annotate", response_model=GeneticVariantResponse)
async def annotate_variant(
    variant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Annotate variant with additional information."""
    try:
        service = VariantService(db)
        return await service.annotate_variant(variant_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{variant_id}/clinical-info", response_model=dict)
async def get_variant_clinical_info(
    variant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get clinical information for variant."""
    try:
        service = VariantService(db)
        return await service.get_variant_clinical_info(variant_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{variant_id}/frequency", response_model=dict)
async def get_variant_frequency(
    variant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get population frequency data for variant."""
    try:
        service = VariantService(db)
        return await service.get_variant_frequency(variant_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/batch", response_model=List[GeneticVariantResponse], status_code=status.HTTP_201_CREATED)
async def create_batch_variants(
    variants: List[GeneticVariantCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple variants in batch."""
    try:
        service = VariantService(db)
        results = []
        for variant in variants:
            result = await service.create_variant(variant, current_user.id)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_variant_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get variant statistics for the user."""
    try:
        service = VariantService(db)
        return await service.get_variant_statistics(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export", response_model=dict)
async def export_variants(
    format: str = "vcf",
    chromosome: Optional[str] = None,
    gene_name: Optional[str] = None,
    clinical_significance: Optional[VariantClassification] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export variants in specified format."""
    try:
        service = VariantService(db)
        return await service.export_variants(
            user_id=current_user.id,
            format=format,
            chromosome=chromosome,
            gene_name=gene_name,
            clinical_significance=clinical_significance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 