"""
Health Insights API Router
Handles endpoints for health insights management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.models.base import BaseModel, PaginatedResponse, create_paginated_response
from ..models.health_insights import (
    HealthInsightCreate, HealthInsightUpdate, HealthInsightResponse, 
    HealthInsightFilter, InsightType
)
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/insights", tags=["health-insights"])

@router.post("/", response_model=HealthInsightResponse, status_code=status.HTTP_201_CREATED)
async def create_insight(
    insight: HealthInsightCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new health insight.
    
    - **insight**: Health insight data to create
    - **current_user**: Authenticated user (from JWT)
    - **db**: Database session
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.create_insight(
            user_id=current_user["id"],
            insight_data=insight.dict()
        )
        return HealthInsightResponse(**result)
    except ValueError as e:
        import logging
        logging.error(f"Validation error creating insight for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to create insight for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create insight")

@router.get("/", response_model=PaginatedResponse)
async def get_insights(
    insight_type: Optional[InsightType] = Query(None, description="Filter by insight type"),
    insight_status: Optional[str] = Query(None, description="Filter by insight status"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    actionable: Optional[bool] = Query(None, description="Filter by actionable insights"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get health insights with optional filtering.
    
    - **insight_type**: Filter by specific insight type
    - **insight_status**: Filter by insight status (new, read, acted_upon, etc.)
    - **severity**: Filter by severity level (low, medium, high, critical)
    - **actionable**: Filter by actionable insights only
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip for pagination
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        filter_params = HealthInsightFilter(
            insight_type=insight_type,
            status=insight_status,
            severity=severity,
            actionable=actionable,
            limit=limit,
            offset=offset
        )
        result = await analytics_service.get_insights(
            user_id=current_user["id"],
            filter_params=filter_params
        )
        # result should be a dict with keys: data, total
        return create_paginated_response(
            data=[HealthInsightResponse(**insight) for insight in result["data"]],
            total=result["total"],
            page=(offset // limit) + 1,
            size=limit,
            message="Insights retrieved successfully"
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve insights for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve insights")

@router.get("/{insight_id}", response_model=HealthInsightResponse)
async def get_insight(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific health insight by ID.
    
    - **insight_id**: Unique identifier of the insight
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        insight = await analytics_service.get_insight(
            user_id=current_user["id"],
            insight_id=insight_id
        )
        if not insight:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
        return HealthInsightResponse(**insight)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve insight {insight_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve insight")

@router.put("/{insight_id}", response_model=HealthInsightResponse)
async def update_insight(
    insight_id: str,
    insight_update: HealthInsightUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a health insight.
    
    - **insight_id**: Unique identifier of the insight to update
    - **insight_update**: Updated insight data
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.update_insight(
            user_id=current_user["id"],
            insight_id=insight_id,
            update_data=insight_update.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
        return HealthInsightResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        import logging
        logging.error(f"Validation error updating insight {insight_id} for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to update insight {insight_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update insight")

@router.delete("/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a health insight.
    
    - **insight_id**: Unique identifier of the insight to delete
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        success = await analytics_service.delete_insight(
            user_id=current_user["id"],
            insight_id=insight_id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to delete insight {insight_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete insight")

@router.get("/types/list", response_model=Dict[str, List[str]])
async def get_insight_types():
    """
    Get list of available insight types.
    """
    return {"insight_types": [insight_type.value for insight_type in InsightType]}

@router.post("/{insight_id}/mark-read", response_model=HealthInsightResponse)
async def mark_insight_read(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark an insight as read.
    
    - **insight_id**: Unique identifier of the insight
    """
    import logging, traceback
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.mark_insight_read(
            user_id=current_user["id"],
            insight_id=insight_id
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
        return HealthInsightResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Exception in mark_insight_read: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark insight as read")

@router.post("/{insight_id}/act-upon", response_model=HealthInsightResponse)
async def act_upon_insight(
    insight_id: str,
    action_taken: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark an insight as acted upon.
    
    - **insight_id**: Unique identifier of the insight
    - **action_taken**: Description of the action taken
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.act_upon_insight(
            user_id=current_user["id"],
            insight_id=insight_id,
            action_taken=action_taken
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
        return HealthInsightResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to mark insight {insight_id} as acted upon for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to mark insight as acted upon")

@router.get("/summary/dashboard", response_model=Dict[str, Any])
async def get_insights_dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get insights dashboard summary.
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        dashboard = await analytics_service.get_insights_dashboard(
            user_id=current_user["id"]
        )
        return dashboard
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve insights dashboard for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve insights dashboard") 