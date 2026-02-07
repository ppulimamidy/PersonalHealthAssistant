"""
Recommendations API
RESTful API endpoints for health recommendations.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ai_insights.models.recommendation_models import (
    RecommendationDB,
    RecommendationActionDB,
    HealthGoalDB,
)
from common.database.connection import get_async_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/health")
async def health_check():
    """Health check endpoint for recommendations."""
    return {
        "service": "recommendations",
        "status": "healthy",
        "message": "Recommendations API is running",
    }


@router.get("/", response_model=list)
async def list_recommendations(
    patient_id: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_async_db),
):
    """List recommendations for a user."""
    query = select(RecommendationDB)
    if patient_id:
        query = query.where(RecommendationDB.patient_id == patient_id)
    if recommendation_type:
        query = query.where(RecommendationDB.recommendation_type == recommendation_type)
    query = query.offset(skip).limit(limit).order_by(RecommendationDB.created_at.desc())
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        {k: v for k, v in row.__dict__.items() if not k.startswith("_")} for row in rows
    ]


@router.get("/{recommendation_id}")
async def get_recommendation(
    recommendation_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific recommendation."""
    query = select(RecommendationDB).where(RecommendationDB.id == recommendation_id)
    result = await db.execute(query)
    recommendation = result.scalars().first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {k: v for k, v in recommendation.__dict__.items() if not k.startswith("_")}


@router.post("/")
async def create_recommendation(
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new recommendation."""
    recommendation = RecommendationDB(
        id=uuid4(),
        patient_id=data.get("patient_id"),
        insight_id=data.get("insight_id"),
        recommendation_type=data.get("recommendation_type", "lifestyle"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        summary=data.get("summary"),
        priority=data.get("priority", "medium"),
        status=data.get("status", "pending"),
        confidence_score=data.get("confidence_score", 0.0),
        effectiveness_score=data.get("effectiveness_score", 0.0),
        adherence_score=data.get("adherence_score", 0.0),
        actions=data.get("actions"),
        steps=data.get("steps"),
        resources=data.get("resources"),
        due_date=data.get("due_date"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        frequency=data.get("frequency"),
        duration=data.get("duration"),
        data_sources=data.get("data_sources"),
        reasoning=data.get("reasoning"),
        alternatives=data.get("alternatives"),
        contraindications=data.get("contraindications"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(recommendation)
    await db.commit()
    await db.refresh(recommendation)
    return {k: v for k, v in recommendation.__dict__.items() if not k.startswith("_")}


@router.put("/{recommendation_id}")
async def update_recommendation(
    recommendation_id: str,
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Update a recommendation."""
    query = select(RecommendationDB).where(RecommendationDB.id == recommendation_id)
    result = await db.execute(query)
    recommendation = result.scalars().first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    for key, value in data.items():
        if hasattr(recommendation, key) and key not in ("id", "created_at"):
            setattr(recommendation, key, value)
    recommendation.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(recommendation)
    return {k: v for k, v in recommendation.__dict__.items() if not k.startswith("_")}


@router.delete("/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a recommendation."""
    query = select(RecommendationDB).where(RecommendationDB.id == recommendation_id)
    result = await db.execute(query)
    recommendation = result.scalars().first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    await db.delete(recommendation)
    await db.commit()
    return {"status": "deleted", "recommendation_id": recommendation_id}


@router.post("/{recommendation_id}/actions")
async def track_action(
    recommendation_id: str,
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Track an action taken on a recommendation."""
    # Verify the recommendation exists
    rec_query = select(RecommendationDB).where(RecommendationDB.id == recommendation_id)
    rec_result = await db.execute(rec_query)
    recommendation = rec_result.scalars().first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    action = RecommendationActionDB(
        id=uuid4(),
        recommendation_id=recommendation_id,
        patient_id=data.get("patient_id", recommendation.patient_id),
        action_type=data.get("action_type", "monitoring"),
        action_name=data.get("action_name", ""),
        description=data.get("description"),
        status=data.get("status", "pending"),
        scheduled_at=data.get("scheduled_at"),
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at"),
        completion_notes=data.get("completion_notes"),
        completion_evidence=data.get("completion_evidence"),
        effectiveness_rating=data.get("effectiveness_rating"),
        difficulty_rating=data.get("difficulty_rating"),
        adherence_rating=data.get("adherence_rating"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return {k: v for k, v in action.__dict__.items() if not k.startswith("_")}


@router.get("/patient/{patient_id}/summary")
async def get_patient_recommendations_summary(
    patient_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Get recommendation summary for a patient."""
    # Total recommendations
    total_query = (
        select(func.count())
        .select_from(RecommendationDB)
        .where(RecommendationDB.patient_id == patient_id)
    )
    total_result = await db.execute(total_query)
    total_count = total_result.scalar() or 0

    # Count by status
    status_query = (
        select(RecommendationDB.status, func.count())
        .where(RecommendationDB.patient_id == patient_id)
        .group_by(RecommendationDB.status)
    )
    status_result = await db.execute(status_query)
    status_counts = {row[0]: row[1] for row in status_result.all()}

    # Count by type
    type_query = (
        select(RecommendationDB.recommendation_type, func.count())
        .where(RecommendationDB.patient_id == patient_id)
        .group_by(RecommendationDB.recommendation_type)
    )
    type_result = await db.execute(type_query)
    type_counts = {row[0]: row[1] for row in type_result.all()}

    # Count by priority
    priority_query = (
        select(RecommendationDB.priority, func.count())
        .where(RecommendationDB.patient_id == patient_id)
        .group_by(RecommendationDB.priority)
    )
    priority_result = await db.execute(priority_query)
    priority_counts = {row[0]: row[1] for row in priority_result.all()}

    # Total actions taken
    actions_query = (
        select(func.count())
        .select_from(RecommendationActionDB)
        .where(RecommendationActionDB.patient_id == patient_id)
    )
    actions_result = await db.execute(actions_query)
    total_actions = actions_result.scalar() or 0

    return {
        "patient_id": patient_id,
        "total_recommendations": total_count,
        "by_status": status_counts,
        "by_type": type_counts,
        "by_priority": priority_counts,
        "total_actions_taken": total_actions,
    }
