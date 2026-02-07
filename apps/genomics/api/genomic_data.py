"""
Genomic data API endpoints for Personal Health Assistant.

This module provides endpoints for managing genomic data including:
- Upload and storage of genomic files
- Data validation and processing
- File format conversion
- Data access and retrieval
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from apps.auth.models.user import User
from ..models.genomic_data import (
    GenomicData, GenomicDataCreate, GenomicDataUpdate, GenomicDataResponse,
    GeneticVariant, GeneticVariantCreate, GeneticVariantResponse,
    PharmacogenomicProfile, PharmacogenomicProfileCreate, PharmacogenomicProfileResponse,
    DataSource, DataFormat, QualityStatus, VariantType, VariantClassification
)
from ..services.genomic_data_service import GenomicDataService

router = APIRouter()


@router.post("/", response_model=GenomicDataResponse, status_code=status.HTTP_201_CREATED)
async def create_genomic_data(
    data: GenomicDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new genomic data record."""
    try:
        service = GenomicDataService(db)
        return await service.create_genomic_data(data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[GenomicDataResponse])
async def list_genomic_data(
    skip: int = 0,
    limit: int = 100,
    data_source: Optional[DataSource] = None,
    data_format: Optional[DataFormat] = None,
    quality_status: Optional[QualityStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List genomic data for the current user."""
    try:
        service = GenomicDataService(db)
        return await service.list_genomic_data(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            data_source=data_source,
            data_format=data_format,
            quality_status=quality_status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{data_id}", response_model=GenomicDataResponse)
async def get_genomic_data(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific genomic data by ID."""
    try:
        service = GenomicDataService(db)
        return await service.get_genomic_data(data_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{data_id}", response_model=GenomicDataResponse)
async def update_genomic_data(
    data_id: str,
    data: GenomicDataUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update genomic data."""
    try:
        service = GenomicDataService(db)
        return await service.update_genomic_data(data_id, data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genomic_data(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete genomic data."""
    try:
        service = GenomicDataService(db)
        await service.delete_genomic_data(data_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload", response_model=GenomicDataResponse, status_code=status.HTTP_201_CREATED)
async def upload_genomic_file(
    file: UploadFile = File(...),
    data_source: DataSource = DataSource.DIRECT_TO_CONSUMER,
    sample_id: Optional[str] = None,
    collection_date: Optional[str] = None,
    lab_name: Optional[str] = None,
    test_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload genomic data file."""
    try:
        service = GenomicDataService(db)
        return await service.upload_genomic_file(
            file=file,
            user_id=current_user.id,
            data_source=data_source,
            sample_id=sample_id,
            collection_date=collection_date,
            lab_name=lab_name,
            test_name=test_name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{data_id}/download")
async def download_genomic_file(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download genomic data file."""
    try:
        service = GenomicDataService(db)
        file_path = await service.get_file_path(data_id, current_user.id)
        return FileResponse(
            path=file_path,
            filename=f"genomic_data_{data_id}.txt",
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{data_id}/process", response_model=GenomicDataResponse)
async def process_genomic_data(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process genomic data for analysis."""
    try:
        service = GenomicDataService(db)
        return await service.process_genomic_data(data_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{data_id}/quality", response_model=dict)
async def get_quality_metrics(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quality metrics for genomic data."""
    try:
        service = GenomicDataService(db)
        return await service.get_quality_metrics(data_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{data_id}/validate", response_model=dict)
async def validate_genomic_data(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate genomic data format and quality."""
    try:
        service = GenomicDataService(db)
        return await service.validate_genomic_data(data_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{data_id}/status", response_model=dict)
async def get_processing_status(
    data_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing status of genomic data."""
    try:
        service = GenomicDataService(db)
        return await service.get_processing_status(data_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) 