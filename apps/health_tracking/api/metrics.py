"""
Health Metrics API Router
Handles health metrics tracking and management endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.models.base import BaseModel, PaginatedResponse, create_paginated_response
from ..models.health_metrics import (
    HealthMetricCreate, HealthMetricUpdate, HealthMetricResponse, 
    HealthMetricFilter, MetricType
)
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/metrics", tags=["health-metrics"])

@router.post("/", response_model=HealthMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
    metric: HealthMetricCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new health metric entry.
    
    - **metric**: Health metric data to create
    - **current_user**: Authenticated user (from JWT)
    - **db**: Database session
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.create_metric(
            user_id=current_user["id"],
            metric_data=metric.dict()
        )
        return HealthMetricResponse(**result)
    except ValueError as e:
        import logging
        logging.error(f"Validation error creating metric for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to create metric for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create metric")

@router.get("/", response_model=PaginatedResponse)
async def get_metrics(
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get health metrics with optional filtering.
    
    - **metric_type**: Filter by specific metric type
    - **start_date**: Filter metrics from this date
    - **end_date**: Filter metrics until this date
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip for pagination
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        filter_params = HealthMetricFilter(
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        result = await analytics_service.get_metrics(
            user_id=current_user["id"],
            filter_params=filter_params,
            db=db
        )
        # result should be a dict with keys: data, total
        return create_paginated_response(
            data=[HealthMetricResponse(**metric) for metric in result["data"]],
            total=result["total"],
            page=(offset // limit) + 1,
            size=limit,
            message="Metrics retrieved successfully"
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve metrics for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metrics")

@router.get("/{metric_id}", response_model=HealthMetricResponse)
async def get_metric(
    metric_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific health metric by ID.
    
    - **metric_id**: Unique identifier of the metric
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        metric = await analytics_service.get_metric(
            user_id=current_user["id"],
            metric_id=metric_id
        )
        if not metric:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
        return HealthMetricResponse(**metric)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve metric {metric_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metric")

@router.put("/{metric_id}", response_model=HealthMetricResponse)
async def update_metric(
    metric_id: str,
    metric_update: HealthMetricUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a health metric entry.
    
    - **metric_id**: Unique identifier of the metric to update
    - **metric_update**: Updated metric data
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.update_metric(
            user_id=current_user["id"],
            metric_id=metric_id,
            update_data=metric_update.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
        return HealthMetricResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        import logging
        logging.error(f"Validation error updating metric {metric_id} for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to update metric {metric_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update metric")

@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a health metric entry.
    
    - **metric_id**: Unique identifier of the metric to delete
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        success = await analytics_service.delete_metric(
            user_id=current_user["id"],
            metric_id=metric_id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to delete metric {metric_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete metric")

@router.get("/types/list", response_model=Dict[str, List[str]])
async def get_metric_types():
    """
    Get list of available metric types.
    """
    return {"metric_types": [metric_type.value for metric_type in MetricType]}

@router.get("/summary/stats", response_model=Dict[str, Any])
async def get_metrics_summary(
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get summary statistics for metrics.
    
    - **metric_type**: Optional filter by metric type
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        summary = await analytics_service.get_metrics_summary(
            user_id=current_user["id"],
            metric_type=metric_type
        )
        return summary
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve metrics summary for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve metrics summary") 