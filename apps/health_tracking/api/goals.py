"""
Health Goals API Router
Handles health goals management endpoints.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.models.base import BaseModel, PaginatedResponse, create_paginated_response
from ..models.health_goals import (
    HealthGoalCreate, HealthGoalUpdate, HealthGoalResponse, 
    HealthGoalFilter, GoalType
)
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/goals", tags=["health-goals"])

@router.post("/", response_model=HealthGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: HealthGoalCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new health goal.
    
    - **goal**: Health goal data to create
    - **current_user**: Authenticated user (from JWT)
    - **db**: Database session
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.create_goal(
            user_id=current_user["id"],
            goal_data=goal.dict()
        )
        return HealthGoalResponse(**result)
    except ValueError as e:
        import logging
        logging.error(f"Validation error creating goal for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to create goal for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create goal")

@router.get("/", response_model=PaginatedResponse)
async def get_goals(
    goal_type: Optional[GoalType] = Query(None, description="Filter by goal type"),
    goal_status: Optional[str] = Query(None, description="Filter by goal status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get health goals with optional filtering.
    
    - **goal_type**: Filter by specific goal type
    - **goal_status**: Filter by goal status (active, completed, paused, etc.)
    - **limit**: Maximum number of records to return
    - **offset**: Number of records to skip for pagination
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        filter_params = HealthGoalFilter(
            goal_type=goal_type,
            status=goal_status,
            limit=limit,
            offset=offset
        )
        result = await analytics_service.get_goals(
            user_id=current_user["id"],
            filter_params=filter_params
        )
        # result should be a dict with keys: data, total
        return create_paginated_response(
            data=[HealthGoalResponse(**goal) for goal in result["data"]],
            total=result["total"],
            page=(offset // limit) + 1,
            size=limit,
            message="Goals retrieved successfully"
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve goals: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve goals")

@router.get("/{goal_id}", response_model=HealthGoalResponse)
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific health goal by ID.
    
    - **goal_id**: Unique identifier of the goal
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        goal = await analytics_service.get_goal(
            user_id=current_user["id"],
            goal_id=goal_id
        )
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return HealthGoalResponse(**goal)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve goal {goal_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve goal")

@router.put("/{goal_id}", response_model=HealthGoalResponse)
async def update_goal(
    goal_id: str,
    goal_update: HealthGoalUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a health goal.
    
    - **goal_id**: Unique identifier of the goal to update
    - **goal_update**: Updated goal data
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.update_goal(
            user_id=current_user["id"],
            goal_id=goal_id,
            update_data=goal_update.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return HealthGoalResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        import logging
        logging.error(f"Validation error updating goal {goal_id} for user {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Failed to update goal {goal_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update goal")

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a health goal.
    
    - **goal_id**: Unique identifier of the goal to delete
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        success = await analytics_service.delete_goal(
            user_id=current_user["id"],
            goal_id=goal_id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to delete goal {goal_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete goal")

@router.get("/types/list", response_model=Dict[str, List[str]])
async def get_goal_types():
    """
    Get list of available goal types.
    """
    return {"goal_types": [goal_type.value for goal_type in GoalType]}

@router.get("/progress/{goal_id}", response_model=Dict[str, Any])
async def get_goal_progress(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get progress information for a specific goal.
    
    - **goal_id**: Unique identifier of the goal
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        progress = await analytics_service.get_goal_progress(
            user_id=current_user["id"],
            goal_id=goal_id
        )
        if not progress:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to retrieve goal progress for goal {goal_id} and user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve goal progress")

@router.post("/{goal_id}/complete", response_model=HealthGoalResponse)
async def complete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark a goal as completed.
    
    - **goal_id**: Unique identifier of the goal to complete
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        result = await analytics_service.complete_goal(
            user_id=current_user["id"],
            goal_id=goal_id
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return HealthGoalResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Failed to complete goal {goal_id} for user {current_user['id']}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete goal") 