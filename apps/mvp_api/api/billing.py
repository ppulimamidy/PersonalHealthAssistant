"""
Billing API
Stripe subscriptions, checkout sessions, customer portal, and webhooks.
"""

import os
from datetime import datetime
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    get_user_tier,
    get_usage_summary,
    _supabase_get,
    _supabase_upsert,
)

logger = get_logger(__name__)
router = APIRouter()

# Stripe configuration
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Price IDs from Stripe Dashboard
STRIPE_PRICE_MAP = {
    "pro": os.environ.get("STRIPE_PRICE_PRO", ""),
    "pro_plus": os.environ.get("STRIPE_PRICE_PRO_PLUS", ""),
}

TIER_FROM_PRICE = {v: k for k, v in STRIPE_PRICE_MAP.items() if v}


# --- Request/Response models ---


class CreateCheckoutRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for creating a Stripe checkout session."""

    tier: str  # "pro" or "pro_plus"


class CheckoutResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Response containing a Stripe checkout URL."""

    checkout_url: str


class PortalResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Response containing a Stripe customer portal URL."""

    portal_url: str


class ConfirmCheckoutRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for confirming a checkout session (success page fallback)."""

    session_id: str


# --- Helpers ---


async def _get_or_create_stripe_customer(user_id: str, email: str) -> str:
    """Get existing Stripe customer ID or create one."""
    rows = await _supabase_get(
        "subscriptions",
        f"user_id=eq.{user_id}&select=stripe_customer_id&limit=1",
    )
    if rows and rows[0].get("stripe_customer_id"):
        return rows[0]["stripe_customer_id"]

    # Create new Stripe customer
    customer = stripe.Customer.create(
        email=email,
        metadata={"user_id": user_id},
    )
    return customer.id


async def _upsert_subscription(  # pylint: disable=too-many-arguments
    user_id: str,
    stripe_customer_id: Optional[str],
    stripe_subscription_id: Optional[str],
    tier: str,
    status: str,
    current_period_start: Optional[str] = None,
    current_period_end: Optional[str] = None,
    cancel_at_period_end: bool = False,
) -> None:
    """Create or update a subscription record in Supabase."""
    body = {
        "user_id": user_id,
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "tier": tier,
        "status": status,
        "cancel_at_period_end": cancel_at_period_end,
        "updated_at": "now()",
    }
    if current_period_start:
        body["current_period_start"] = current_period_start
    if current_period_end:
        body["current_period_end"] = current_period_end

    await _supabase_upsert("subscriptions", body)


# --- Endpoints ---


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CreateCheckoutRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a Stripe Checkout session for subscription purchase."""
    if body.tier not in STRIPE_PRICE_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {body.tier}")

    price_id = STRIPE_PRICE_MAP[body.tier]
    if not price_id:
        raise HTTPException(
            status_code=400, detail=f"Price not configured for tier: {body.tier}"
        )

    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    user_id = current_user["id"]
    email = current_user.get("email", "")

    customer_id = await _get_or_create_stripe_customer(user_id, email)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/pricing",
        metadata={"user_id": user_id, "tier": body.tier},
    )

    # Store customer ID so we can look it up later
    await _upsert_subscription(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=None,
        tier="free",
        status="incomplete",
    )

    return CheckoutResponse(checkout_url=session.url)


@router.post("/create-portal-session", response_model=PortalResponse)
async def create_portal_session(
    current_user: dict = Depends(get_current_user),
):
    """Create a Stripe Customer Portal session for managing subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    user_id = current_user["id"]
    rows = await _supabase_get(
        "subscriptions",
        f"user_id=eq.{user_id}&select=stripe_customer_id&limit=1",
    )
    if not rows or not rows[0].get("stripe_customer_id"):
        raise HTTPException(status_code=404, detail="No subscription found")

    session = stripe.billing_portal.Session.create(
        customer=rows[0]["stripe_customer_id"],
        return_url=f"{FRONTEND_URL}/settings",
    )

    return PortalResponse(portal_url=session.url)


@router.post("/confirm-checkout-session")
async def confirm_checkout_session(
    body: ConfirmCheckoutRequest,
    current_user: dict = Depends(get_current_user),
):
    """Confirm a checkout session and activate subscription (called from success page).
    Use when webhook may not have run yet (e.g. production without webhook)."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    try:
        session = stripe.checkout.Session.retrieve(
            body.session_id,
            expand=["subscription"],
        )
    except stripe.error.InvalidRequestError as exc:
        raise HTTPException(status_code=400, detail="Invalid session") from exc

    if getattr(session, "payment_status", None) != "paid":
        raise HTTPException(status_code=400, detail="Session not paid")

    metadata = getattr(session, "metadata", None) or {}
    if not isinstance(metadata, dict):
        metadata = {
            "user_id": getattr(metadata, "user_id", None),
            "tier": getattr(metadata, "tier", "pro"),
        }
    user_id = metadata.get("user_id")
    if user_id != current_user["id"]:
        raise HTTPException(
            status_code=403, detail="Session does not belong to this user"
        )

    sub = getattr(session, "subscription", None)
    subscription_id = getattr(sub, "id", sub) if sub else None
    session_dict = {
        "metadata": metadata,
        "customer": getattr(session, "customer", None),
        "subscription": subscription_id,
    }
    await _handle_checkout_completed(session_dict)
    return {"ok": True}


@router.get("/subscription")
async def get_subscription(
    current_user: dict = Depends(get_current_user),
):
    """Get current user's subscription details and usage."""
    user_id = current_user["id"]
    tier = await get_user_tier(user_id)
    usage = await get_usage_summary(user_id)

    # Get subscription details
    rows = await _supabase_get(
        "subscriptions",
        f"user_id=eq.{user_id}&select=*&limit=1",
    )

    sub = rows[0] if rows else {}

    return {
        "tier": tier,
        "status": sub.get("status", "active" if tier == "free" else "unknown"),
        "current_period_end": sub.get("current_period_end"),
        "cancel_at_period_end": sub.get("cancel_at_period_end", False),
        "usage": usage,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc
    except Exception as exc:
        logger.error(f"Webhook error: {exc}")
        raise HTTPException(status_code=400, detail="Invalid payload") from exc

    event_type = event["type"]
    event_id = event.get("id", "unknown")
    data = event["data"]["object"]

    logger.info(f"Stripe webhook received: {event_type} (event={event_id})")

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(data)
    else:
        logger.info(f"Unhandled webhook event: {event_type}")

    return {"status": "ok"}


# --- Webhook handlers ---


async def _handle_checkout_completed(session: dict) -> None:
    """Handle successful checkout — activate subscription."""
    user_id = (session.get("metadata") or {}).get("user_id")
    tier = (session.get("metadata") or {}).get("tier", "pro")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not user_id or not customer_id:
        logger.warning(
            "Checkout completed but missing user_id or customer_id in metadata"
        )
        return

    # Fetch subscription details from Stripe
    period_start = None
    period_end = None
    if subscription_id:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            period_start = datetime.fromtimestamp(sub.current_period_start).isoformat()
            period_end = datetime.fromtimestamp(sub.current_period_end).isoformat()
        except (stripe.error.StripeError, KeyError, TypeError) as exc:
            logger.warning(f"Failed to fetch subscription details: {exc}")

    await _upsert_subscription(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        tier=tier,
        status="active",
        current_period_start=period_start,
        current_period_end=period_end,
    )
    logger.info(f"Subscription activated for user {user_id}: tier={tier}")


async def _handle_subscription_updated(subscription: dict) -> None:
    """Handle subscription changes (upgrade, downgrade, renewal)."""
    subscription_id = subscription.get("id")
    customer_id = subscription.get("customer")
    status = subscription.get("status", "active")
    cancel_at_period_end = subscription.get("cancel_at_period_end", False)

    # Determine tier from price
    items = subscription.get("items", {}).get("data", [])
    price_id = items[0]["price"]["id"] if items else ""
    tier = TIER_FROM_PRICE.get(price_id, "pro")

    period_start = datetime.fromtimestamp(
        subscription["current_period_start"]
    ).isoformat()
    period_end = datetime.fromtimestamp(subscription["current_period_end"]).isoformat()

    # Find user by stripe_customer_id
    rows = await _supabase_get(
        "subscriptions",
        f"stripe_customer_id=eq.{customer_id}&select=user_id&limit=1",
    )
    if not rows:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return

    user_id = rows[0]["user_id"]

    await _upsert_subscription(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        tier=tier,
        status=status,
        current_period_start=period_start,
        current_period_end=period_end,
        cancel_at_period_end=cancel_at_period_end,
    )
    logger.info(
        f"Subscription updated for user {user_id}: tier={tier}, status={status}"
    )


async def _handle_subscription_deleted(subscription: dict) -> None:
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")

    rows = await _supabase_get(
        "subscriptions",
        f"stripe_customer_id=eq.{customer_id}&select=user_id&limit=1",
    )
    if not rows:
        return

    user_id = rows[0]["user_id"]

    await _upsert_subscription(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription.get("id"),
        tier="free",
        status="canceled",
    )
    logger.info(f"Subscription canceled for user {user_id}")


async def _handle_payment_failed(invoice: dict) -> None:
    """Handle failed payment — set status to past_due."""
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    rows = await _supabase_get(
        "subscriptions",
        f"stripe_customer_id=eq.{customer_id}&select=user_id,tier,stripe_subscription_id&limit=1",
    )
    if not rows:
        return

    user_id = rows[0]["user_id"]
    tier = rows[0].get("tier", "free")

    await _upsert_subscription(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id or rows[0].get("stripe_subscription_id"),
        tier=tier,
        status="past_due",
    )
    logger.info(f"Payment failed for user {user_id}, status set to past_due")
