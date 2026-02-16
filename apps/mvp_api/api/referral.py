"""
Referral System API
"Invite a friend, get 1 month free" — generates referral codes,
tracks signups, and applies credit via Stripe coupons.
"""

import os
import secrets
import string

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get, _supabase_upsert

logger = get_logger(__name__)
router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


# --- Models ---


class RedeemRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for redeeming a referral code."""

    code: str


# --- Helpers ---


def _generate_code(length: int = 8) -> str:
    """Generate a short, URL-safe referral code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def _get_referral_row(user_id: str) -> dict:
    """Get the referral row for a user, or empty dict."""
    rows = await _supabase_get(
        "referrals",
        f"referrer_id=eq.{user_id}&select=*&limit=1",
    )
    if rows and isinstance(rows, list):
        return rows[0]
    return {}


async def _get_referral_by_code(code: str) -> dict:
    """Look up a referral row by code."""
    rows = await _supabase_get(
        "referrals",
        f"code=eq.{code}&select=*&limit=1",
    )
    if rows and isinstance(rows, list):
        return rows[0]
    return {}


async def _apply_stripe_credit(user_id: str) -> bool:
    """
    Apply 1-month free credit to the referrer's Stripe subscription
    by adding a coupon. Returns True if successful.
    """
    if not stripe.api_key:
        logger.warning("Stripe not configured, skipping credit")
        return False

    # Find the user's Stripe customer ID
    rows = await _supabase_get(
        "subscriptions",
        f"user_id=eq.{user_id}"
        f"&status=in.(active,trialing)"
        f"&select=stripe_subscription_id"
        f"&limit=1",
    )
    if not rows or not rows[0].get("stripe_subscription_id"):
        logger.info(f"User {user_id} has no active subscription for credit")
        return False

    sub_id = rows[0]["stripe_subscription_id"]

    try:
        # Create a one-time 100% off coupon for 1 month
        coupon = stripe.Coupon.create(
            percent_off=100,
            duration="once",
            name="Referral reward — 1 month free",
            metadata={"referrer_user_id": user_id},
        )
        # Apply to the subscription
        stripe.Subscription.modify(
            sub_id,
            coupon=coupon.id,
        )
        logger.info(
            f"Applied referral credit to subscription {sub_id} " f"for user {user_id}"
        )
        return True
    except stripe.error.StripeError as exc:
        logger.error(f"Failed to apply Stripe credit: {exc}")
        return False


# --- Endpoints ---


@router.get("/code")
async def get_referral_code(
    current_user: dict = Depends(get_current_user),
):
    """Get or create a referral code for the authenticated user."""
    user_id = current_user["id"]
    existing = await _get_referral_row(user_id)

    if existing and existing.get("code"):
        return {
            "code": existing["code"],
            "referral_count": existing.get("referral_count", 0),
            "credits_earned": existing.get("credits_earned", 0),
            "share_url": f"{FRONTEND_URL}/signup?ref={existing['code']}",
        }

    # Create a new code
    code = _generate_code()
    await _supabase_upsert(
        "referrals",
        {
            "referrer_id": user_id,
            "code": code,
            "referral_count": 0,
            "credits_earned": 0,
        },
    )

    return {
        "code": code,
        "referral_count": 0,
        "credits_earned": 0,
        "share_url": f"{FRONTEND_URL}/signup?ref={code}",
    }


@router.post("/redeem")
async def redeem_referral(
    body: RedeemRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Redeem a referral code. Called when a new user signs up with a code.
    Increments referrer's count and applies credit when threshold is met.
    """
    user_id = current_user["id"]
    code = body.code.strip().upper()

    if not code:
        raise HTTPException(status_code=400, detail="Code is required")

    referral = await _get_referral_by_code(code)
    if not referral:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    referrer_id = referral.get("referrer_id", "")
    if referrer_id == user_id:
        raise HTTPException(
            status_code=400, detail="You cannot use your own referral code"
        )

    # Check if this user already redeemed a code
    already = await _supabase_get(
        "referral_redemptions",
        f"redeemed_by=eq.{user_id}&select=id&limit=1",
    )
    if already and isinstance(already, list) and already:
        raise HTTPException(
            status_code=400, detail="You have already used a referral code"
        )

    # Record the redemption
    await _supabase_upsert(
        "referral_redemptions",
        {
            "referral_code": code,
            "referrer_id": referrer_id,
            "redeemed_by": user_id,
        },
    )

    # Increment referrer's count
    new_count = referral.get("referral_count", 0) + 1
    new_credits = referral.get("credits_earned", 0)

    # Apply credit for every referral (1 referral = 1 month free)
    credit_applied = await _apply_stripe_credit(referrer_id)
    if credit_applied:
        new_credits += 1

    await _supabase_upsert(
        "referrals",
        {
            "referrer_id": referrer_id,
            "code": code,
            "referral_count": new_count,
            "credits_earned": new_credits,
        },
    )

    logger.info(
        f"Referral redeemed: code={code}, referrer={referrer_id}, "
        f"redeemed_by={user_id}, total_referrals={new_count}"
    )

    return {
        "success": True,
        "message": "Referral code applied successfully",
    }


@router.get("/stats")
async def get_referral_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get referral statistics for the authenticated user."""
    user_id = current_user["id"]
    referral = await _get_referral_row(user_id)

    if not referral:
        return {
            "code": None,
            "referral_count": 0,
            "credits_earned": 0,
            "share_url": None,
        }

    # Get list of people who used the code
    redemptions = await _supabase_get(
        "referral_redemptions",
        f"referrer_id=eq.{user_id}"
        f"&select=redeemed_by,created_at"
        f"&order=created_at.desc&limit=10",
    )

    return {
        "code": referral.get("code"),
        "referral_count": referral.get("referral_count", 0),
        "credits_earned": referral.get("credits_earned", 0),
        "share_url": f"{FRONTEND_URL}/signup?ref={referral.get('code', '')}",
        "recent_referrals": redemptions if isinstance(redemptions, list) else [],
    }
