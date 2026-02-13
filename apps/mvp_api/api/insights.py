"""
AI Insights API
Endpoints for AI-generated health insights with explainability.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import os

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Sandbox mode
USE_SANDBOX = os.getenv("USE_SANDBOX", "true").lower() in ("true", "1", "yes")


# Helper function for optional auth in sandbox mode
async def get_user_optional(request: Request) -> dict:
    """Get current user, or return a sandbox user if not authenticated and in sandbox mode"""
    if USE_SANDBOX:
        try:
            return await get_current_user(request)
        except HTTPException:
            # In sandbox mode, if auth fails, return a mock user
            return {
                "id": "sandbox-user-123",
                "email": "sandbox@example.com",
                "user_type": "sandbox"
            }
    else:
        # In production, require authentication
        return await get_current_user(request)


class InsightType(str, Enum):
    TREND = "trend"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"


class InsightCategory(str, Enum):
    SLEEP = "sleep"
    ACTIVITY = "activity"
    READINESS = "readiness"
    GENERAL = "general"


class DataPoint(BaseModel):
    metric: str
    value: float
    date: str
    trend: str  # "up", "down", "stable"


class AIInsight(BaseModel):
    id: str
    type: InsightType
    category: InsightCategory
    title: str
    summary: str
    explanation: str
    confidence: float
    data_points: List[DataPoint]
    created_at: datetime


class InsightsResponse(BaseModel):
    insights: List[AIInsight]
    generated_at: datetime


@router.get("", response_model=List[AIInsight])
async def get_insights(
    limit: int = Query(default=5, ge=1, le=10),
    current_user: dict = Depends(get_user_optional)
):
    """
    Get AI-generated insights based on user's health data.
    Returns up to 5 personalized insights with explanations.
    """
    from .timeline import get_timeline

    # Fetch recent health data
    try:
        timeline = await get_timeline(days=14, current_user=current_user)
    except Exception as e:
        logger.error(f"Failed to fetch timeline for insights: {e}")
        timeline = []

    insights = []

    if not timeline:
        # Return default insights if no data
        insights.append(AIInsight(
            id=str(uuid.uuid4()),
            type=InsightType.RECOMMENDATION,
            category=InsightCategory.GENERAL,
            title="Connect Your Device",
            summary="Connect your Oura Ring to start receiving personalized insights.",
            explanation="We analyze your sleep, activity, and readiness data to provide actionable recommendations. Once you connect your device and sync a few days of data, we'll generate insights tailored to your health patterns.",
            confidence=1.0,
            data_points=[],
            created_at=datetime.utcnow()
        ))
        return insights[:limit]

    # Analyze sleep patterns
    sleep_data = [e for e in timeline if e.sleep]
    if len(sleep_data) >= 3:
        scores = [e.sleep.sleep_score for e in sleep_data]
        avg_score = sum(scores) / len(scores)
        recent_avg = sum(scores[:3]) / 3
        older_avg = sum(scores[3:7]) / max(len(scores[3:7]), 1) if len(scores) > 3 else avg_score

        if recent_avg > older_avg + 5:
            insights.append(AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.TREND,
                category=InsightCategory.SLEEP,
                title="Sleep Quality Improving",
                summary=f"Your sleep score has improved by {int(recent_avg - older_avg)} points over the past week.",
                explanation=f"Looking at your last 14 days of sleep data, your average sleep score in the past 3 days ({int(recent_avg)}) is higher than the previous week ({int(older_avg)}). This improvement suggests your sleep habits or environment may be optimizing. Keep up whatever changes you've made!",
                confidence=0.85,
                data_points=[
                    DataPoint(metric="Sleep Score (Recent)", value=recent_avg, date=sleep_data[0].date, trend="up"),
                    DataPoint(metric="Sleep Score (Previous)", value=older_avg, date=sleep_data[-1].date, trend="stable"),
                ],
                created_at=datetime.utcnow()
            ))
        elif recent_avg < older_avg - 5:
            insights.append(AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.ALERT,
                category=InsightCategory.SLEEP,
                title="Sleep Quality Declining",
                summary=f"Your sleep score has dropped by {int(older_avg - recent_avg)} points recently.",
                explanation=f"Your recent sleep scores (avg {int(recent_avg)}) are lower than your previous week (avg {int(older_avg)}). This could be due to changes in bedtime routine, stress, or environmental factors. Consider reviewing your sleep habits.",
                confidence=0.82,
                data_points=[
                    DataPoint(metric="Sleep Score (Recent)", value=recent_avg, date=sleep_data[0].date, trend="down"),
                    DataPoint(metric="Sleep Score (Previous)", value=older_avg, date=sleep_data[-1].date, trend="stable"),
                ],
                created_at=datetime.utcnow()
            ))

        # Check deep sleep
        deep_sleep = [e.sleep.deep_sleep_duration for e in sleep_data]
        avg_deep = sum(deep_sleep) / len(deep_sleep)
        if avg_deep < 3600:  # Less than 1 hour
            insights.append(AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.RECOMMENDATION,
                category=InsightCategory.SLEEP,
                title="Boost Deep Sleep",
                summary="Your deep sleep averages under 1 hour per night.",
                explanation=f"Your average deep sleep is {int(avg_deep/60)} minutes, which is below the recommended 1-2 hours for adults. Deep sleep is crucial for physical recovery and immune function. Try avoiding alcohol and heavy meals before bed, keeping your room cool (65-68°F), and maintaining a consistent sleep schedule.",
                confidence=0.78,
                data_points=[
                    DataPoint(metric="Avg Deep Sleep (min)", value=avg_deep/60, date=sleep_data[0].date, trend="stable"),
                ],
                created_at=datetime.utcnow()
            ))

    # Analyze activity patterns
    activity_data = [e for e in timeline if e.activity]
    if len(activity_data) >= 3:
        steps = [e.activity.steps for e in activity_data]
        avg_steps = sum(steps) / len(steps)

        if avg_steps < 5000:
            insights.append(AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.RECOMMENDATION,
                category=InsightCategory.ACTIVITY,
                title="Increase Daily Movement",
                summary=f"Your daily steps average {int(avg_steps):,}, below the 7,500 target.",
                explanation=f"Research shows 7,500-10,000 daily steps are associated with lower mortality risk. Your current average of {int(avg_steps):,} steps suggests opportunities for more movement. Try taking short walks after meals, using stairs instead of elevators, or setting hourly movement reminders.",
                confidence=0.88,
                data_points=[
                    DataPoint(metric="Avg Daily Steps", value=avg_steps, date=activity_data[0].date, trend="stable"),
                ],
                created_at=datetime.utcnow()
            ))
        elif avg_steps > 10000:
            insights.append(AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.TREND,
                category=InsightCategory.ACTIVITY,
                title="Great Activity Level",
                summary=f"You're averaging {int(avg_steps):,} steps daily - excellent!",
                explanation=f"Your consistent activity of over 10,000 daily steps is associated with improved cardiovascular health, better mood, and reduced disease risk. Keep maintaining this healthy habit!",
                confidence=0.92,
                data_points=[
                    DataPoint(metric="Avg Daily Steps", value=avg_steps, date=activity_data[0].date, trend="up"),
                ],
                created_at=datetime.utcnow()
            ))

    # Analyze readiness patterns
    readiness_data = [e for e in timeline if e.readiness]
    if len(readiness_data) >= 3:
        scores = [e.readiness.readiness_score for e in readiness_data]
        hrv = [e.readiness.hrv_balance for e in readiness_data]
        avg_hrv = sum(hrv) / len(hrv)

        if avg_hrv < 50:
            insights.append(AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.ALERT,
                category=InsightCategory.READINESS,
                title="Recovery May Be Low",
                summary="Your HRV balance suggests your body may need more recovery time.",
                explanation=f"Your HRV balance score of {int(avg_hrv)} indicates your autonomic nervous system may be under stress. This could be from physical training, mental stress, or insufficient sleep. Consider lighter workouts, stress reduction activities like meditation, and ensuring adequate sleep this week.",
                confidence=0.75,
                data_points=[
                    DataPoint(metric="HRV Balance", value=avg_hrv, date=readiness_data[0].date, trend="down"),
                ],
                created_at=datetime.utcnow()
            ))

    # Add a general wellness insight if we have good data
    if len(insights) < limit and len(timeline) >= 7:
        insights.append(AIInsight(
            id=str(uuid.uuid4()),
            type=InsightType.RECOMMENDATION,
            category=InsightCategory.GENERAL,
            title="Track Consistently for Better Insights",
            summary="Wearing your ring consistently helps us provide more accurate insights.",
            explanation="The more complete your data, the better we can identify patterns and trends in your health. Try to wear your Oura Ring during sleep and throughout the day for the most comprehensive analysis.",
            confidence=0.95,
            data_points=[],
            created_at=datetime.utcnow()
        ))

    return insights[:limit]


@router.get("/{insight_id}", response_model=AIInsight)
async def get_insight_detail(
    insight_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific insight.
    """
    # In production, fetch from database
    # For MVP, regenerate and find matching ID
    insights = await get_insights(limit=10, current_user=current_user)

    for insight in insights:
        if insight.id == insight_id:
            return insight

    raise HTTPException(status_code=404, detail="Insight not found")


@router.post("/{insight_id}/dismiss")
async def dismiss_insight(
    insight_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Dismiss an insight so it won't appear again.
    """
    # In production, store dismissal in database
    logger.info(f"User {current_user['id']} dismissed insight {insight_id}")
    return {"status": "dismissed"}


@router.post("/refresh", response_model=List[AIInsight])
async def refresh_insights(current_user: dict = Depends(get_current_user)):
    """
    Force refresh of AI insights.
    Regenerates insights based on latest data.
    """
    return await get_insights(limit=5, current_user=current_user)
