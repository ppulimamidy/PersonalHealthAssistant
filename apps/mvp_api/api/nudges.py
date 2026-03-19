"""
Nudge Engine — Contextual Push Notifications for the Closed Loop

Generates and sends push notifications during active experiments:
- Morning metric update
- Evening check-in reminder
- Halfway milestone
- Completion notification
- Weekly recommendation (when no active experiment)

Uses Expo Push API for mobile delivery.
"""

import os
import ssl
from datetime import datetime, date, timedelta, timezone, time
from typing import Any, Dict, List, Optional

import aiohttp
import certifi
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_insert,
    _supabase_patch,
)

logger = get_logger(__name__)
router = APIRouter()

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class NudgeItem(BaseModel):
    id: str
    nudge_type: str
    title: str
    body: str
    data: Dict[str, Any]
    scheduled_for: str
    status: str


class ScheduleNudgesResponse(BaseModel):
    scheduled: int
    cancelled: int


# ---------------------------------------------------------------------------
# Expo Push sending
# ---------------------------------------------------------------------------


async def _send_expo_push(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Send push notification via Expo Push API.
    Returns count of successfully queued messages.
    """
    if not tokens:
        return 0

    messages = [
        {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {},
        }
        for token in tokens
    ]

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            async with session.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ok_count = sum(
                        1 for r in result.get("data", []) if r.get("status") == "ok"
                    )
                    logger.info("Expo push sent: %d/%d OK", ok_count, len(tokens))
                    return ok_count
                else:
                    body_text = await resp.text()
                    logger.warning(
                        "Expo push failed: %s %s", resp.status, body_text[:200]
                    )
                    return 0
    except Exception as exc:
        logger.warning("Expo push send error: %s", exc)
        return 0


async def _get_user_tokens(user_id: str) -> List[str]:
    """Fetch all Expo push tokens for a user."""
    rows = await _supabase_get(
        "push_tokens",
        f"user_id=eq.{user_id}&select=token",
    )
    return [r["token"] for r in (rows or []) if r.get("token")]


# ---------------------------------------------------------------------------
# Nudge scheduling for interventions
# ---------------------------------------------------------------------------


async def schedule_intervention_nudges(
    user_id: str,
    intervention_id: str,
    title: str,
    duration_days: int,
    started_at: datetime,
) -> int:
    """
    Schedule all nudges for a new intervention.
    Called when user starts an experiment via "Try This".
    """
    nudges = []
    now = datetime.now(timezone.utc)

    for day in range(1, duration_days + 1):
        nudge_date = started_at + timedelta(days=day)

        # Morning metric update (8am user local — approximate with UTC for now)
        morning = datetime.combine(
            nudge_date.date(), time(13, 0), tzinfo=timezone.utc
        )  # ~8am EST
        if morning > now:
            nudges.append(
                {
                    "user_id": user_id,
                    "nudge_type": "experiment_morning",
                    "title": f"Day {day}: {title}",
                    "body": "Check your Home screen for updated metrics.",
                    "data": {
                        "intervention_id": intervention_id,
                        "day": day,
                        "screen": "home",
                    },
                    "scheduled_for": morning.isoformat(),
                    "intervention_id": intervention_id,
                    "status": "pending",
                }
            )

        # Evening check-in reminder (8pm — only if not checked in)
        evening = datetime.combine(
            nudge_date.date(), time(1, 0), tzinfo=timezone.utc
        )  # ~8pm EST next day
        evening += timedelta(days=1)
        if evening > now:
            nudges.append(
                {
                    "user_id": user_id,
                    "nudge_type": "experiment_checkin",
                    "title": "Quick check-in",
                    "body": f"Did you follow through on your experiment today?",
                    "data": {
                        "intervention_id": intervention_id,
                        "day": day,
                        "screen": "home",
                    },
                    "scheduled_for": evening.isoformat(),
                    "intervention_id": intervention_id,
                    "status": "pending",
                }
            )

    # Halfway milestone
    halfway_day = duration_days // 2
    if halfway_day >= 2:
        halfway_date = started_at + timedelta(days=halfway_day)
        halfway_time = datetime.combine(
            halfway_date.date(), time(14, 0), tzinfo=timezone.utc
        )
        if halfway_time > now:
            nudges.append(
                {
                    "user_id": user_id,
                    "nudge_type": "experiment_halfway",
                    "title": f"Halfway through!",
                    "body": f"You're {halfway_day} days into your {title} experiment. See how your metrics are trending.",
                    "data": {
                        "intervention_id": intervention_id,
                        "day": halfway_day,
                        "screen": "home",
                    },
                    "scheduled_for": halfway_time.isoformat(),
                    "intervention_id": intervention_id,
                    "status": "pending",
                }
            )

    # Completion nudge
    complete_date = started_at + timedelta(days=duration_days)
    complete_time = datetime.combine(
        complete_date.date(), time(14, 0), tzinfo=timezone.utc
    )
    nudges.append(
        {
            "user_id": user_id,
            "nudge_type": "experiment_complete",
            "title": "Experiment complete!",
            "body": f"Your {title} experiment just ended. Tap to see your results.",
            "data": {"intervention_id": intervention_id, "screen": "home"},
            "scheduled_for": complete_time.isoformat(),
            "intervention_id": intervention_id,
            "status": "pending",
        }
    )

    # Insert all nudges
    count = 0
    for nudge in nudges:
        result = await _supabase_insert("nudge_queue", nudge)
        if result:
            count += 1

    logger.info("Scheduled %d nudges for intervention %s", count, intervention_id)
    return count


async def cancel_intervention_nudges(intervention_id: str) -> int:
    """Cancel all pending nudges for an intervention (on abandon)."""
    rows = await _supabase_get(
        "nudge_queue",
        f"intervention_id=eq.{intervention_id}&status=eq.pending&select=id",
    )
    count = 0
    for row in rows or []:
        await _supabase_patch(
            "nudge_queue",
            f"id=eq.{row['id']}",
            {"status": "cancelled"},
        )
        count += 1

    logger.info("Cancelled %d nudges for intervention %s", count, intervention_id)
    return count


# ---------------------------------------------------------------------------
# Send pending nudges
# ---------------------------------------------------------------------------


async def _should_skip_checkin_nudge(nudge: Dict[str, Any]) -> bool:
    """Skip evening check-in nudge if user already checked in today."""
    if nudge.get("nudge_type") != "experiment_checkin":
        return False
    intervention_id = nudge.get("data", {}).get("intervention_id") or nudge.get(
        "intervention_id"
    )
    if not intervention_id:
        return False
    today_str = date.today().isoformat()
    checkins = await _supabase_get(
        "intervention_checkins",
        f"intervention_id=eq.{intervention_id}&checkin_date=eq.{today_str}&limit=1",
    )
    return bool(checkins)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/send-pending")
async def send_pending_nudges(
    request: Request,
):
    """
    Send all pending nudges where scheduled_for <= now.
    Called by a cron job or manually. Protected by CRON_SECRET header.
    """
    cron_secret = os.environ.get("CRON_SECRET", "")
    auth_header = request.headers.get("x-cron-secret", "")
    if cron_secret and auth_header != cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    now = datetime.now(timezone.utc).isoformat()
    pending = await _supabase_get(
        "nudge_queue",
        f"status=eq.pending&scheduled_for=lte.{now}&order=scheduled_for.asc&limit=50",
    )
    if not pending:
        return {"sent": 0, "skipped": 0}

    sent = 0
    skipped = 0
    for nudge in pending:
        # Skip check-in nudges if already checked in
        if await _should_skip_checkin_nudge(nudge):
            await _supabase_patch(
                "nudge_queue",
                f"id=eq.{nudge['id']}",
                {"status": "cancelled"},
            )
            skipped += 1
            continue

        tokens = await _get_user_tokens(nudge["user_id"])
        if not tokens:
            # No tokens — mark as sent to avoid retrying
            await _supabase_patch(
                "nudge_queue",
                f"id=eq.{nudge['id']}",
                {"status": "sent", "sent_at": now},
            )
            skipped += 1
            continue

        ok = await _send_expo_push(
            tokens=tokens,
            title=nudge["title"],
            body=nudge["body"],
            data=nudge.get("data") or {},
        )
        await _supabase_patch(
            "nudge_queue",
            f"id=eq.{nudge['id']}",
            {"status": "sent", "sent_at": now},
        )
        if ok > 0:
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}


@router.post("/{nudge_id}/opened", status_code=200)
async def mark_nudge_opened(
    nudge_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a nudge as opened (called from mobile deep link handler)."""
    now = datetime.now(timezone.utc).isoformat()
    await _supabase_patch(
        "nudge_queue",
        f"id=eq.{nudge_id}&user_id=eq.{current_user['id']}",
        {"status": "opened", "opened_at": now},
    )
    return {"status": "opened"}


@router.get("/pending", response_model=List[NudgeItem])
async def get_pending_nudges(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Preview pending nudges for the current user (debug/admin)."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "nudge_queue",
        f"user_id=eq.{user_id}&status=eq.pending&order=scheduled_for.asc&limit=20",
    )
    return [
        NudgeItem(
            id=r["id"],
            nudge_type=r["nudge_type"],
            title=r["title"],
            body=r["body"],
            data=r.get("data") or {},
            scheduled_for=r["scheduled_for"],
            status=r["status"],
        )
        for r in (rows or [])
    ]
