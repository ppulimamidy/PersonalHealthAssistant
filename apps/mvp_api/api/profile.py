"""
Profile endpoints: periodic vitals check-in, user role update, and account deletion.

Account deletion (GDPR Article 17 / CCPA / HIPAA Right of Access):
    DELETE /api/v1/profile/account
    Permanently removes all user data across all tables.
"""

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, timezone

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_patch,
    _supabase_upsert,
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    _supabase_headers,
    _ssl_context,
)

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


# ---------------------------------------------------------------------------
# Account Deletion — GDPR Right to Erasure / CCPA / HIPAA
# ---------------------------------------------------------------------------

# All user-scoped tables to purge. Order matters: children before parents.
_USER_TABLES = [
    "saved_insights",
    "agent_actions",
    "agent_conversations",
    "medication_adherence_log",
    "weekly_checkins",
    "symptom_journal",
    "health_conditions",
    "medications",
    "supplements",
    "care_plans",
    "user_goals",
    "native_health_data",
    "health_metric_summaries",
    "oura_connections",
    "daily_sleep",
    "daily_activity",
    "daily_readiness",
    "push_subscriptions",
    "nutrition_goals",
    "user_preferences",
    "sharing_links",
    "profiles",
]


@router.delete("/account", status_code=200)
async def delete_account(
    current_user: dict = Depends(get_current_user),
):
    """
    Permanently delete all user data and the auth account.

    This is irreversible. Complies with:
    - GDPR Article 17 (Right to Erasure)
    - CCPA (Right to Delete)
    - HIPAA (individual right to request amendment/deletion)

    Deletes data from all user-scoped tables, then removes the
    Supabase Auth account itself.
    """
    user_id = current_user["id"]
    deleted_tables = []
    errors = []

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Phase 1: Delete all user data from every table
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=60),
        connector=aiohttp.TCPConnector(ssl=_ssl_context()),
    ) as session:
        for table in _USER_TABLES:
            url = f"{SUPABASE_URL}/rest/v1/{table}?user_id=eq.{user_id}"
            try:
                async with session.delete(url, headers=_supabase_headers()) as resp:
                    if resp.status in (200, 204):
                        deleted_tables.append(table)
                    elif resp.status == 404:
                        pass  # table doesn't exist — skip
                    else:
                        err = await resp.text()
                        errors.append(f"{table}: {resp.status} {err[:100]}")
            except Exception as exc:
                errors.append(f"{table}: {exc}")

        # Also delete from nutrition service tables (meal_logs, food_recognition_results)
        for table in ["meal_logs", "food_recognition_results", "user_corrections"]:
            url = f"{SUPABASE_URL}/rest/v1/{table}?user_id=eq.{user_id}"
            try:
                async with session.delete(url, headers=_supabase_headers()) as resp:
                    if resp.status in (200, 204):
                        deleted_tables.append(table)
            except Exception:
                pass

        # Also try lab_results (nested under /lab-results router but table is lab_results)
        url = f"{SUPABASE_URL}/rest/v1/lab_results?user_id=eq.{user_id}"
        try:
            async with session.delete(url, headers=_supabase_headers()) as resp:
                if resp.status in (200, 204):
                    deleted_tables.append("lab_results")
        except Exception:
            pass

    # Phase 2: Delete the Supabase Auth user account
    auth_deleted = False
    try:
        auth_url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        }
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=_ssl_context()),
        ) as session:
            async with session.delete(auth_url, headers=headers) as resp:
                auth_deleted = resp.status in (200, 204)
                if not auth_deleted:
                    errors.append(f"auth_user: {resp.status}")
    except Exception as exc:
        errors.append(f"auth_user: {exc}")

    logger.info(
        "Account deleted user=%s tables=%d auth=%s errors=%d",
        user_id,
        len(deleted_tables),
        auth_deleted,
        len(errors),
    )

    return {
        "deleted": True,
        "user_id": user_id,
        "tables_purged": len(deleted_tables),
        "auth_account_deleted": auth_deleted,
        "errors": errors if errors else None,
    }
