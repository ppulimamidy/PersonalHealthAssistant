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
from pydantic import BaseModel, Field

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

    subs = (
        await _supabase_get(
            "push_subscriptions",
            f"user_id=eq.{user_id}&select=endpoint,p256dh,auth",
        )
        or []
    )

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


# ── Expo Push Token Models ─────────────────────────────────────────────────────


class ExpoPushTokenRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Expo push token registration payload from the mobile app."""

    token: str = Field(
        ..., description="Expo push token, e.g. ExponentPushToken[xxxxxx]"
    )
    platform: str = Field(..., description="ios or android")


# ── Expo Push Token Endpoints ─────────────────────────────────────────────────


@router.post("/register", status_code=201)
async def register_push_token(
    body: ExpoPushTokenRequest,
    current_user: dict = Depends(get_current_user),
):
    """Register an Expo push token for the current user.

    Upserts on (user_id, token) so re-registering the same token is safe.
    Call this after login and after the OS grants notification permission.

    Supabase table DDL (run once):

        CREATE TABLE public.push_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            token TEXT NOT NULL,
            platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        ALTER TABLE public.push_tokens
            ADD CONSTRAINT push_tokens_uq UNIQUE (user_id, token);
        CREATE INDEX idx_push_tokens_uid ON public.push_tokens (user_id);
        ALTER TABLE public.push_tokens ENABLE ROW LEVEL SECURITY;
        CREATE POLICY "own push tokens" ON public.push_tokens
            FOR ALL USING (auth.uid() = user_id)
            WITH CHECK (auth.uid() = user_id);
    """
    from datetime import datetime, timezone  # pylint: disable=import-outside-toplevel

    user_id = current_user["id"]
    row = await _supabase_upsert(
        "push_tokens",
        {
            "user_id": user_id,
            "token": body.token,
            "platform": body.platform,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="user_id,token",
    )
    if not row:
        from fastapi import HTTPException  # pylint: disable=import-outside-toplevel

        raise HTTPException(status_code=500, detail="Failed to register push token")
    logger.info(
        "Expo push token registered user=%s platform=%s", user_id, body.platform
    )
    return {"status": "registered"}


@router.delete("/unregister", status_code=204)
async def unregister_push_token(
    body: ExpoPushTokenRequest,
    current_user: dict = Depends(get_current_user),
):
    """Remove a specific Expo push token on logout or permission revocation."""
    user_id = current_user["id"]
    await _supabase_delete(
        "push_tokens",
        f"user_id=eq.{user_id}&token=eq.{body.token}",
    )
    logger.info("Expo push token removed user=%s platform=%s", user_id, body.platform)
