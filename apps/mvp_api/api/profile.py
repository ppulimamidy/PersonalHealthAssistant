"""
Profile endpoints: periodic vitals check-in and user role/persona update.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, timezone

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_patch, _supabase_upsert

logger = get_logger(__name__)
router = APIRouter()


class CheckinRequest(BaseModel):
    weight_kg: Optional[float] = None
    height_cm: Optional[int] = None
    new_conditions: Optional[List[str]] = None   # condition names to add
    new_medications: Optional[List[str]] = None  # medication names to add


class RoleRequest(BaseModel):
    user_role: Literal["patient", "provider", "caregiver"]


@router.patch("/checkin")
async def update_checkin(
    body: CheckinRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Record a periodic vitals check-in.
    Updates weight/height if provided and stamps last_checkin_at = now().
    """
    user_id = current_user["id"]

    now = datetime.now(timezone.utc)
    updates: dict = {"last_checkin_at": now.isoformat()}
    if body.weight_kg is not None:
        updates["weight_kg"] = body.weight_kg
    if body.height_cm is not None:
        updates["height_cm"] = body.height_cm

    await _supabase_patch("profiles", f"id=eq.{user_id}", updates)

    # Insert new conditions
    if body.new_conditions:
        for cname in body.new_conditions:
            cname = cname.strip()
            if not cname:
                continue
            try:
                await _supabase_upsert("health_conditions", {
                    "user_id": user_id,
                    "condition_name": cname,
                    "is_active": True,
                    "severity": "moderate",
                    "diagnosed_date": now.date().isoformat(),
                })
            except Exception as exc:
                logger.warning(f"Failed to insert condition '{cname}': {exc}")

    # Insert new medications
    if body.new_medications:
        for mname in body.new_medications:
            mname = mname.strip()
            if not mname:
                continue
            try:
                await _supabase_upsert("medications", {
                    "user_id": user_id,
                    "medication_name": mname,
                    "dosage": "—",
                    "frequency": "as directed",
                    "is_active": True,
                    "start_date": now.date().isoformat(),
                })
            except Exception as exc:
                logger.warning(f"Failed to insert medication '{mname}': {exc}")

    logger.info(f"Profile checkin for user {user_id}")
    return {"ok": True, "last_checkin_at": updates["last_checkin_at"]}


@router.patch("/role")
async def update_role(
    body: RoleRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Update the user's persona role (patient / provider / caregiver).
    """
    user_id = current_user["id"]
    await _supabase_patch("profiles", f"id=eq.{user_id}", {"user_role": body.user_role})
    logger.info(f"User {user_id} set role to {body.user_role}")
    return {"ok": True, "user_role": body.user_role}
