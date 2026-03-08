"""
Web Push / PWA Notifications API.

Endpoints:
  POST /api/v1/notifications/subscribe     — save a push subscription
  DELETE /api/v1/notifications/subscribe   — remove push subscription
  POST /api/v1/notifications/test-push     — send a test push to the current user
"""

import json
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────────────────

class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys


class TestPushRequest(BaseModel):
    title: Optional[str] = "Health Reminder"
    body: Optional[str] = "This is a test notification from your Health Assistant."


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/subscribe", status_code=201)
async def subscribe(
    body: PushSubscriptionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Save or update a push subscription for the current user."""
    user_id = current_user["id"]
    ua = request.headers.get("user-agent", "")[:200]

    row = await _supabase_upsert(
        "push_subscriptions",
        {
            "user_id": user_id,
            "endpoint": body.endpoint,
            "p256dh": body.keys.p256dh,
            "auth": body.keys.auth,
            "user_agent": ua,
        },
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to save subscription")
    return {"status": "subscribed"}


@router.delete("/subscribe", status_code=204)
async def unsubscribe(
    current_user: dict = Depends(get_current_user),
):
    """Remove all push subscriptions for the current user."""
    user_id = current_user["id"]
    await _supabase_delete("push_subscriptions", f"user_id=eq.{user_id}")


@router.post("/test-push")
async def test_push(
    body: TestPushRequest,
    current_user: dict = Depends(get_current_user),
):
    """Send a test push notification to all active subscriptions of the current user."""
    user_id = current_user["id"]

    subs = await _supabase_get(
        "push_subscriptions",
        f"user_id=eq.{user_id}&select=endpoint,p256dh,auth",
    ) or []

    if not subs:
        raise HTTPException(status_code=404, detail="No push subscriptions found")

    # Try to send via pywebpush if available
    try:
        from pywebpush import webpush, WebPushException  # type: ignore

        vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY", "")
        vapid_claims = {
            "sub": f"mailto:{os.environ.get('VAPID_CONTACT_EMAIL', 'admin@healthassistant.app')}"
        }

        if not vapid_private_key:
            return {
                "status": "skipped",
                "reason": "VAPID_PRIVATE_KEY not configured",
                "subscriptions": len(subs),
            }

        payload = json.dumps({"title": body.title, "body": body.body})
        sent = 0
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub["endpoint"],
                        "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                    },
                    data=payload,
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                )
                sent += 1
            except WebPushException as e:
                logger.warning(f"Push failed for sub: {e}")

        return {"status": "sent", "sent": sent, "total": len(subs)}

    except ImportError:
        logger.warning("pywebpush not installed — push delivery skipped")
        return {
            "status": "skipped",
            "reason": "pywebpush not installed. Run: pip install pywebpush",
            "subscriptions": len(subs),
        }
