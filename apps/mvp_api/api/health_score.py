"""
Daily Health Score API
Computes a weighted composite score from Oura sleep, activity, and readiness data.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")

# Weights for composite score
WEIGHT_SLEEP = 0.40
WEIGHT_READINESS = 0.35
WEIGHT_ACTIVITY = 0.25


async def get_user_optional(request: Request) -> dict:
    """Get current user, or return a sandbox user if in sandbox mode."""
    if USE_SANDBOX:
        try:
            return await get_current_user(request)
        except HTTPException:
            return {
                "id": "sandbox-user-123",
                "email": "sandbox@example.com",
                "user_type": "sandbox",
            }
    return await get_current_user(request)


@router.get("")
async def get_health_score(current_user: dict = Depends(get_user_optional)):
    """
    Get today's composite health score.

    Weights: sleep 40%, readiness 35%, activity 25%.
    Returns breakdown per component, trend vs yesterday, and the composite score.
    """
    from .timeline import get_timeline

    try:
        timeline = await get_timeline(days=2, current_user=current_user)
    except (HTTPException, KeyError, TypeError) as exc:
        logger.error(f"Failed to fetch timeline for health score: {exc}")
        return _empty_score()

    if not timeline:
        return _empty_score()

    today = timeline[0]
    yesterday = timeline[1] if len(timeline) > 1 else None

    today_score, today_breakdown = _compute_score(today)
    yesterday_score = _compute_score(yesterday)[0] if yesterday else None

    if today_score is None:
        return _empty_score()

    trend = "stable"
    change = 0.0
    if yesterday_score is not None:
        change = round(today_score - yesterday_score, 1)
        if change > 2:
            trend = "up"
        elif change < -2:
            trend = "down"

    return {
        "score": round(today_score, 1),
        "breakdown": today_breakdown,
        "trend": trend,
        "change_from_yesterday": change,
        "date": getattr(today, "date", None),
    }


def _compute_score(entry) -> tuple:
    """Compute weighted health score from a timeline entry. Returns (score, breakdown)."""
    if entry is None:
        return None, {}

    sleep_score = (
        getattr(entry.sleep, "sleep_score", None)
        if getattr(entry, "sleep", None)
        else None
    )
    readiness_score = (
        getattr(entry.readiness, "readiness_score", None)
        if getattr(entry, "readiness", None)
        else None
    )
    activity_score = (
        getattr(entry.activity, "activity_score", None)
        if getattr(entry, "activity", None)
        else None
    )

    components = []
    breakdown = {}

    if sleep_score is not None:
        weighted = sleep_score * WEIGHT_SLEEP
        components.append(weighted)
        breakdown["sleep"] = {
            "score": sleep_score,
            "weight": WEIGHT_SLEEP,
            "weighted": round(weighted, 1),
        }

    if readiness_score is not None:
        weighted = readiness_score * WEIGHT_READINESS
        components.append(weighted)
        breakdown["readiness"] = {
            "score": readiness_score,
            "weight": WEIGHT_READINESS,
            "weighted": round(weighted, 1),
        }

    if activity_score is not None:
        weighted = activity_score * WEIGHT_ACTIVITY
        components.append(weighted)
        breakdown["activity"] = {
            "score": activity_score,
            "weight": WEIGHT_ACTIVITY,
            "weighted": round(weighted, 1),
        }

    if not components:
        return None, breakdown

    # Normalize: if only some components are available, scale proportionally
    total_weight = sum(b["weight"] for b in breakdown.values())
    score = sum(components) / total_weight if total_weight > 0 else 0

    return score, breakdown


def _empty_score():
    return {
        "score": None,
        "breakdown": {},
        "trend": "stable",
        "change_from_yesterday": 0,
        "date": None,
    }
