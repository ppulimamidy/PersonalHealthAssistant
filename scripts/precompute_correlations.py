#!/usr/bin/env python3
"""
Pre-compute correlations for all users so the frontend loads instantly.

Run as a cron job (e.g., every 6 hours):
    export PYTHONPATH=/Users/pulimap/PersonalHealthAssistant
    python scripts/precompute_correlations.py

Or for a single user:
    python scripts/precompute_correlations.py --user 22144dc2-...
"""

import argparse
import asyncio
import logging
import os
import ssl
import sys

import aiohttp
import certifi
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps", "mvp_api", ".env")
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

PERIODS = [14, 30, 0]  # 0 = All (capped at 365d in engine)


async def get_active_users() -> list[str]:
    """Get all user IDs that have health data."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    url = f"{SUPABASE_URL}/rest/v1/native_health_data?select=user_id&limit=1000"
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx)) as s:
        async with s.get(url, headers=headers) as r:
            if r.status == 200:
                rows = await r.json()
                return list({row["user_id"] for row in rows if row.get("user_id")})
    return []


async def precompute_for_user(user_id: str) -> None:
    """Pre-compute all correlation periods for a user."""
    from apps.mvp_api.api.correlations import _compute_and_cache

    user = {"id": user_id, "email": ""}

    for days in PERIODS:
        label = "All (365d)" if days == 0 else f"{days}d"
        try:
            result = await _compute_and_cache(user, days, None)
            n = len(result.correlations)
            logger.info(
                "user=%s period=%s correlations=%d days_with_data=%d",
                user_id[:8],
                label,
                n,
                result.days_with_data,
            )
        except Exception as exc:
            logger.error("user=%s period=%s failed: %s", user_id[:8], label, exc)


async def main(user_filter: str | None) -> None:
    if user_filter:
        users = [user_filter]
    else:
        users = await get_active_users()

    logger.info(
        "Pre-computing correlations for %d users, periods=%s", len(users), PERIODS
    )

    for uid in users:
        logger.info("Processing user %s...", uid[:8])
        await precompute_for_user(uid)

    logger.info("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-compute correlations")
    parser.add_argument("--user", help="Single user ID to process")
    args = parser.parse_args()
    asyncio.run(main(args.user))
