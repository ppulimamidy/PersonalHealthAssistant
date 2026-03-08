"""
User Goals API

Simple CRUD for user-authored health goals.
Goals are free-text (e.g. "Reduce LDL by March", "Walk 8k steps daily"),
categorised, and surfaced on the Today page and in AI agent context.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
    _supabase_patch,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

GoalCategory = Literal[
    "weight", "medication", "exercise", "diet",
    "lab_result", "sleep", "mental_health", "general",
]

GoalStatus = Literal["active", "achieved", "abandoned"]


class UserGoal(BaseModel):
    id: str
    user_id: str
    goal_text: str
    category: str
    status: str
    due_date: Optional[str] = None
    notes: Optional[str] = None
    source: str = "user"
    is_pinned: bool = False
    created_at: str
    updated_at: str


class CreateGoalRequest(BaseModel):
    goal_text: str
    category: GoalCategory = "general"
    due_date: Optional[str] = None   # ISO date YYYY-MM-DD
    notes: Optional[str] = None
    source: Optional[str] = "user"   # "user" | "doctor"
    is_pinned: Optional[bool] = False


class UpdateGoalRequest(BaseModel):
    status: Optional[GoalStatus] = None
    goal_text: Optional[str] = None
    category: Optional[GoalCategory] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    is_pinned: Optional[bool] = None


class GoalsListResponse(BaseModel):
    goals: List[UserGoal]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=GoalsListResponse)
async def list_goals(
    status: Optional[str] = "active",
    current_user: dict = Depends(get_current_user),
):
    """List the current user's goals (default: active only)."""
    user_id = current_user["id"]
    status_filter = f"&status=eq.{status}" if status else ""
    rows = await _supabase_get(
        "user_goals",
        f"user_id=eq.{user_id}{status_filter}&order=is_pinned.desc,created_at.desc&select=*&limit=50",
    ) or []
    goals = [_row_to_goal(r) for r in rows]
    return GoalsListResponse(goals=goals)


@router.post("", response_model=UserGoal, status_code=201)
async def create_goal(
    body: CreateGoalRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new health goal."""
    user_id = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "user_id": user_id,
        "goal_text": body.goal_text.strip(),
        "category": body.category,
        "status": "active",
        "due_date": body.due_date or None,
        "notes": body.notes or None,
        "source": body.source or "user",
        "is_pinned": body.is_pinned or False,
        "created_at": now,
        "updated_at": now,
    }
    row = await _supabase_upsert("user_goals", data)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create goal")
    logger.info(f"Goal created for user {user_id}: {body.goal_text[:50]}")
    return _row_to_goal(row)


@router.patch("/{goal_id}", response_model=UserGoal)
async def update_goal(
    goal_id: str,
    body: UpdateGoalRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a goal (e.g. mark as achieved)."""
    user_id = current_user["id"]

    existing = await _supabase_get(
        "user_goals",
        f"id=eq.{goal_id}&user_id=eq.{user_id}&select=id&limit=1",
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")

    updates: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ("status", "goal_text", "category", "due_date", "notes"):
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val
    if body.is_pinned is not None:
        updates["is_pinned"] = body.is_pinned

    row = await _supabase_patch(
        "user_goals", f"id=eq.{goal_id}&user_id=eq.{user_id}", updates
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to update goal")
    return _row_to_goal(row)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a goal."""
    user_id = current_user["id"]
    existing = await _supabase_get(
        "user_goals",
        f"id=eq.{goal_id}&user_id=eq.{user_id}&select=id&limit=1",
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")
    await _supabase_delete("user_goals", f"id=eq.{goal_id}&user_id=eq.{user_id}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_goal(row: dict) -> UserGoal:
    return UserGoal(
        id=row["id"],
        user_id=row["user_id"],
        goal_text=row["goal_text"],
        category=row.get("category", "general"),
        status=row.get("status", "active"),
        due_date=row.get("due_date"),
        notes=row.get("notes"),
        source=row.get("source", "user"),
        is_pinned=row.get("is_pinned", False) or False,
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
    )
