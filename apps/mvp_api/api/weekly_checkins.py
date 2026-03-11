"""
Weekly Mood/Energy/Pain Check-In API

Lightweight self-reported well-being snapshots.
Returns the most recent check-in date so the frontend can decide when to prompt.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
)

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CheckinRequest(BaseModel):
    energy: int = Field(..., ge=0, le=10)
    mood: int = Field(..., ge=0, le=10)
    pain: int = Field(..., ge=0, le=10)
    notes: Optional[str] = None


class CheckinResponse(BaseModel):
    id: str
    energy: int
    mood: int
    pain: int
    notes: Optional[str]
    checked_in_at: str


class CheckinStatusResponse(BaseModel):
    last_checkin_at: Optional[str]
    days_since_last: Optional[int]
    should_prompt: bool  # True when ≥7 days since last check-in


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_checkin(row: dict) -> CheckinResponse:
    return CheckinResponse(
        id=row["id"],
        energy=row["energy"],
        mood=row["mood"],
        pain=row["pain"],
        notes=row.get("notes"),
        checked_in_at=row.get("checked_in_at", ""),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/status", response_model=CheckinStatusResponse)
async def get_checkin_status(
    current_user: dict = Depends(get_current_user),
):
    """Return last check-in date and whether the user should be prompted."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "weekly_checkins",
        f"user_id=eq.{user_id}&order=checked_in_at.desc&select=checked_in_at&limit=1",
    )
    if not rows:
        return CheckinStatusResponse(
            last_checkin_at=None, days_since_last=None, should_prompt=True
        )

    last_at = rows[0].get("checked_in_at", "")
    try:
        last_dt = datetime.fromisoformat(last_at.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - last_dt).days
    except Exception:
        days = 99

    return CheckinStatusResponse(
        last_checkin_at=last_at,
        days_since_last=days,
        should_prompt=days >= 7,
    )


@router.post("", response_model=CheckinResponse, status_code=201)
async def create_checkin(
    body: CheckinRequest,
    current_user: dict = Depends(get_current_user),
):
    """Record a weekly check-in."""
    user_id = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "user_id": user_id,
        "energy": body.energy,
        "mood": body.mood,
        "pain": body.pain,
        "notes": body.notes or None,
        "checked_in_at": now,
    }
    row = await _supabase_upsert("weekly_checkins", data)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to save check-in")
    logger.info(f"Weekly check-in saved for user {user_id}")
    return _row_to_checkin(row)


@router.get("/history", response_model=List[CheckinResponse])
async def get_checkin_history(
    limit: int = Query(default=12, ge=1, le=52),
    since_timestamp: Optional[str] = Query(
        default=None,
        description="ISO 8601 timestamp — return only check-ins on or after this date "
        "(use for incremental mobile sync)",
    ),
    current_user: dict = Depends(get_current_user),
):
    """Return the user's recent check-in history."""
    user_id = current_user["id"]
    query = (
        f"user_id=eq.{user_id}&order=checked_in_at.desc&select=*&limit={min(limit, 52)}"
    )

    if since_timestamp:
        try:
            datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))  # validate
            query += f"&checked_in_at=gte.{since_timestamp.replace('Z', '+00:00')}"
        except ValueError:
            pass  # Invalid format — ignore

    rows = await _supabase_get("weekly_checkins", query) or []
    return [_row_to_checkin(r) for r in rows]
