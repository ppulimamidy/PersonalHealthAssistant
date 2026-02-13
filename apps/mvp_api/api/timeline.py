"""
Health Timeline API
Endpoints for viewing combined health data over time.
"""

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import os

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Sandbox mode - uses mock data, no real API calls
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


class SleepData(BaseModel):
    id: str
    date: str
    total_sleep_duration: int
    deep_sleep_duration: int
    rem_sleep_duration: int
    light_sleep_duration: int
    sleep_efficiency: int
    sleep_score: int
    bedtime_start: Optional[str] = None
    bedtime_end: Optional[str] = None


class ActivityData(BaseModel):
    id: str
    date: str
    steps: int
    active_calories: int
    total_calories: int
    activity_score: int
    high_activity_time: int
    medium_activity_time: int
    low_activity_time: int
    sedentary_time: int


class ReadinessData(BaseModel):
    id: str
    date: str
    readiness_score: int
    temperature_deviation: float
    hrv_balance: int
    recovery_index: int
    resting_heart_rate: int


class TimelineEntry(BaseModel):
    date: str
    sleep: Optional[SleepData] = None
    activity: Optional[ActivityData] = None
    readiness: Optional[ReadinessData] = None


@router.get("/timeline", response_model=List[TimelineEntry])
async def get_timeline(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to include"),
    current_user: dict = Depends(get_user_optional)
):
    """
    Get combined health timeline data.
    Returns sleep, activity, and readiness data for each day.
    """
    from apps.device_data.services.oura_client import OuraAPIClient

    access_token = os.getenv("OURA_ACCESS_TOKEN", "")
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    try:
        async with OuraAPIClient(
            access_token=access_token if not USE_SANDBOX else None,
            use_sandbox=USE_SANDBOX or not access_token,
            user_id=current_user['id']
        ) as client:
            # Fetch all data types
            all_data = await client.get_all_data(start_date, end_date)

            # Process and combine data by date
            timeline = {}

            # Process sleep data
            for sleep_entry in all_data.get("daily_sleep", {}).get("data", []):
                date = sleep_entry.get("day", "")[:10]
                if date not in timeline:
                    timeline[date] = {"date": date}

                # Extract nested sleep data
                sleep = sleep_entry.get("sleep", sleep_entry)  # Support both nested and flat structures

                timeline[date]["sleep"] = SleepData(
                    id=sleep_entry.get("id", f"sleep_{date}"),
                    date=date,
                    total_sleep_duration=int(sleep.get("total_sleep_duration", 0) / 60),  # Convert seconds to minutes
                    deep_sleep_duration=int(sleep.get("deep_sleep_duration", 0) / 60),
                    rem_sleep_duration=int(sleep.get("rem_sleep_duration", 0) / 60),
                    light_sleep_duration=int(sleep.get("light_sleep_duration", 0) / 60),
                    sleep_efficiency=int(sleep.get("sleep_efficiency", 0)),
                    sleep_score=int(sleep.get("sleep_score", 0)),
                    bedtime_start=sleep.get("bedtime_start"),
                    bedtime_end=sleep.get("bedtime_end"),
                )

            # Process activity data
            for activity_entry in all_data.get("daily_activity", {}).get("data", []):
                date = activity_entry.get("day", "")[:10]
                if date not in timeline:
                    timeline[date] = {"date": date}

                # Extract nested activity data
                activity = activity_entry.get("activity", activity_entry)  # Support both nested and flat structures

                timeline[date]["activity"] = ActivityData(
                    id=activity_entry.get("id", f"activity_{date}"),
                    date=date,
                    steps=int(activity.get("steps", 0)),
                    active_calories=int(activity.get("active_calories", activity.get("calories_active", 0))),
                    total_calories=int(activity.get("total_calories", activity.get("calories_total", 0))),
                    activity_score=int(activity.get("score", 0)),
                    high_activity_time=int(activity.get("high_activity_time", activity.get("met_min_high", 0))),
                    medium_activity_time=int(activity.get("medium_activity_time", activity.get("met_min_medium", 0))),
                    low_activity_time=int(activity.get("low_activity_time", activity.get("met_min_low", 0))),
                    sedentary_time=int(activity.get("sedentary_time", activity.get("met_min_inactive", 0))),
                )

            # Process readiness data
            for readiness_entry in all_data.get("daily_readiness", {}).get("data", []):
                date = readiness_entry.get("day", "")[:10]
                if date not in timeline:
                    timeline[date] = {"date": date}

                # Extract nested readiness data
                readiness = readiness_entry.get("readiness", readiness_entry)  # Support both nested and flat structures

                timeline[date]["readiness"] = ReadinessData(
                    id=readiness_entry.get("id", f"readiness_{date}"),
                    date=date,
                    readiness_score=int(readiness.get("score", 0)),
                    temperature_deviation=float(readiness.get("temperature_deviation", 0.0)),
                    hrv_balance=int(readiness.get("hrv_balance", 0)),
                    recovery_index=int(readiness.get("score_recovery_index", 0)),
                    resting_heart_rate=int(readiness.get("resting_hr", 0)),
                )

            # Sort by date descending
            sorted_entries = sorted(
                [TimelineEntry(**entry) for entry in timeline.values()],
                key=lambda x: x.date,
                reverse=True
            )

            return sorted_entries

    except Exception as e:
        logger.error(f"Failed to fetch timeline: {e}")
        # Return empty timeline on error
        return []


@router.get("/summary")
async def get_health_summary(
    days: int = Query(default=7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of health metrics over a period.
    """
    timeline = await get_timeline(days=days, current_user=current_user)

    if not timeline:
        return {
            "period_days": days,
            "data_available": False,
        }

    # Calculate averages
    sleep_scores = [e.sleep.sleep_score for e in timeline if e.sleep]
    activity_scores = [e.activity.activity_score for e in timeline if e.activity]
    readiness_scores = [e.readiness.readiness_score for e in timeline if e.readiness]
    steps = [e.activity.steps for e in timeline if e.activity]

    return {
        "period_days": days,
        "data_available": True,
        "entries_count": len(timeline),
        "averages": {
            "sleep_score": sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0,
            "activity_score": sum(activity_scores) / len(activity_scores) if activity_scores else 0,
            "readiness_score": sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0,
            "daily_steps": sum(steps) / len(steps) if steps else 0,
        },
        "best_day": {
            "sleep": max(timeline, key=lambda x: x.sleep.sleep_score if x.sleep else 0).date if sleep_scores else None,
            "activity": max(timeline, key=lambda x: x.activity.activity_score if x.activity else 0).date if activity_scores else None,
            "readiness": max(timeline, key=lambda x: x.readiness.readiness_score if x.readiness else 0).date if readiness_scores else None,
        }
    }
