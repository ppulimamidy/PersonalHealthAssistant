"""
Beta Signup API
Public endpoints for collecting beta interest and displaying social proof.
"""

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get, _supabase_upsert

logger = get_logger(__name__)
router = APIRouter()

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class BetaSignupRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for beta signup."""

    email: str
    source: str = "landing_page"


@router.post("/signup")
async def beta_signup(body: BetaSignupRequest):
    """Sign up for the beta waitlist. No auth required."""
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    await _supabase_upsert(
        "beta_signups",
        {
            "email": email,
            "source": body.source,
            "status": "pending",
        },
    )

    logger.info(f"Beta signup: {email}")
    return {"success": True, "message": "You're on the list! We'll be in touch soon."}


@router.get("/count")
async def beta_count():
    """Get total beta signup count for social proof."""
    rows = await _supabase_get("beta_signups", "select=id&limit=10000")
    count = len(rows) if isinstance(rows, list) else 0
    return {"count": count}
