"""
Usage gating dependency for subscription tier enforcement.

Checks whether a user has remaining quota for a given feature
based on their subscription tier. Returns 403 when limit is exceeded.
"""

import os
from datetime import date, timedelta
from typing import Any, Dict, Optional

import aiohttp
from fastapi import HTTPException, Request

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

logger = get_logger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Tier feature limits (-1 = unlimited, 0 = not available)
TIER_LIMITS: Dict[str, Dict[str, int]] = {
    "free": {"ai_insights": 3, "nutrition_scans": 5, "doctor_prep": 0, "pdf_export": 0},
    "pro": {
        "ai_insights": -1,
        "nutrition_scans": -1,
        "doctor_prep": 0,
        "pdf_export": 0,
    },
    "pro_plus": {
        "ai_insights": -1,
        "nutrition_scans": -1,
        "doctor_prep": -1,
        "pdf_export": -1,
    },
}

# Sandbox mode — skip gating entirely
USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")


def _supabase_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _current_week_start() -> str:
    """Monday of the current week as YYYY-MM-DD."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


async def _supabase_get(table: str, params: str) -> list:
    """GET from Supabase PostgREST."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return []
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=_supabase_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.warning(f"Supabase GET {table} failed: {exc}")
        return []


async def _supabase_upsert(table: str, body: dict) -> Optional[dict]:
    """POST (upsert) to Supabase PostgREST."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        **_supabase_headers(),
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=body) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return data[0] if isinstance(data, list) and data else data
                return None
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.warning(f"Supabase upsert {table} failed: {exc}")
        return None


async def get_user_tier(user_id: str) -> str:
    """Look up the user's subscription tier. Defaults to 'free'."""
    rows = await _supabase_get(
        "subscriptions",
        f"user_id=eq.{user_id}&status=in.(active,trialing)&select=tier&limit=1",
    )
    if rows and isinstance(rows, list) and rows[0].get("tier"):
        return rows[0]["tier"]
    return "free"


async def get_usage_count(user_id: str, feature: str, week_start: str) -> int:
    """Get the current week's usage count for a feature."""
    rows = await _supabase_get(
        "usage_tracking",
        f"user_id=eq.{user_id}&feature=eq.{feature}"
        f"&week_start=eq.{week_start}&select=usage_count&limit=1",
    )
    if rows and isinstance(rows, list):
        return rows[0].get("usage_count", 0)
    return 0


async def increment_usage(user_id: str, feature: str, week_start: str) -> None:
    """Increment usage count (upsert). If row exists, increment; otherwise create."""
    # First try to get existing count
    current = await get_usage_count(user_id, feature, week_start)
    await _supabase_upsert(
        "usage_tracking",
        {
            "user_id": user_id,
            "feature": feature,
            "week_start": week_start,
            "usage_count": current + 1,
            "updated_at": "now()",
        },
    )


async def get_usage_summary(user_id: str) -> Dict[str, Dict[str, Any]]:
    """Get usage summary for all features for the current week."""
    tier = await get_user_tier(user_id)
    week_start = _current_week_start()
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    summary = {}
    for feature, limit in limits.items():
        used = await get_usage_count(user_id, feature, week_start) if limit != -1 else 0
        summary[feature] = {
            "used": used,
            "limit": limit,
            "period": "week",
        }
    return summary


class UsageGate:  # pylint: disable=too-few-public-methods
    """
    FastAPI dependency that checks whether the user has remaining
    quota for a given feature based on their subscription tier.

    Usage:
        @router.get("/endpoint")
        async def my_endpoint(current_user: dict = Depends(UsageGate("ai_insights"))):
            ...
    """

    def __init__(self, feature: str):
        self.feature = feature

    async def __call__(self, request: Request) -> dict:
        # In sandbox mode, skip gating entirely
        if USE_SANDBOX:
            try:
                return await get_current_user(request)
            except HTTPException:
                return {
                    "id": "sandbox-user-123",
                    "email": "sandbox@example.com",
                    "user_type": "sandbox",
                }

        current_user = await get_current_user(request)
        user_id = current_user["id"]

        tier = await get_user_tier(user_id)
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        limit = limits.get(self.feature, 0)

        # Unlimited
        if limit == -1:
            return current_user

        # Feature not available for this tier
        if limit == 0:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "usage_limit_reached",
                    "message": f"Upgrade to access {self.feature.replace('_', ' ')}",
                    "feature": self.feature,
                    "limit": 0,
                    "used": 0,
                    "tier": tier,
                    "upgrade_url": "/pricing",
                },
            )

        week_start = _current_week_start()
        used = await get_usage_count(user_id, self.feature, week_start)

        if used >= limit:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "usage_limit_reached",
                    "message": (
                        f"You've used all {limit} "
                        f"{self.feature.replace('_', ' ')} this week"
                    ),
                    "feature": self.feature,
                    "limit": limit,
                    "used": used,
                    "tier": tier,
                    "upgrade_url": "/pricing",
                },
            )

        # Increment usage
        await increment_usage(user_id, self.feature, week_start)
        return current_user
