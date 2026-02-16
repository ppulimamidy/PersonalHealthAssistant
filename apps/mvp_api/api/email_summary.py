"""
Weekly Health Email Summary API
Sends a weekly health digest to Pro+ users via Resend.
Can be triggered by a cron job (e.g., Render Cron or external scheduler).
"""

import os
from datetime import date, timedelta
from typing import List, Optional
from typing_extensions import TypedDict

import aiohttp
from fastapi import APIRouter, Depends, Header, HTTPException

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    get_user_tier,
    _supabase_get,
)

logger = get_logger(__name__)
router = APIRouter()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get(
    "EMAIL_FROM", "HealthAssist <health@updates.healthassist.app>"
)
_DATE_FMT = "%b %d"


async def _send_email(to: str, subject: str, html: str) -> bool:
    """Send email via Resend API."""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email")
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": EMAIL_FROM,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            ) as resp:
                if resp.status in (200, 201):
                    logger.info(f"Email sent to {to}")
                    return True
                body = await resp.text()
                logger.error(f"Resend API error {resp.status}: {body}")
                return False
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.error(f"Failed to send email: {exc}")
        return False


def _fmt_date(d_str: str) -> str:
    """Format ISO date string to human-readable 'Monday, Jan 01'."""
    try:
        return date.fromisoformat(d_str).strftime("%A, %b %d")
    except (ValueError, TypeError):
        return d_str


def _compute_sleep_trend(sleep_scores: List[float]) -> str:
    """Determine sleep trend from a list of scores."""
    if len(sleep_scores) < 3:
        return "Not enough data"
    half = len(sleep_scores) // 2
    first = sum(sleep_scores[:half]) / half
    second = sum(sleep_scores[half:]) / (len(sleep_scores) - half)
    if second - first > 3:
        return "Improving"
    if first - second > 3:
        return "Declining"
    return "Stable"


def _day_score(entry: dict) -> float:
    """Average of available scores for a single timeline day."""
    scores: List[float] = []
    if entry.get("sleep"):
        scores.append(entry["sleep"]["sleep_score"])
    if entry.get("readiness"):
        scores.append(entry["readiness"]["readiness_score"])
    if entry.get("activity"):
        scores.append(entry["activity"]["activity_score"])
    return sum(scores) / len(scores) if scores else 0


def _safe_avg(values: List[float]) -> float:
    """Return average of values, or 0 if empty."""
    return sum(values) / len(values) if values else 0


class _SummaryData(TypedDict):
    avg_sleep: float
    avg_readiness: float
    avg_activity: float
    sleep_trend: str
    best_day: str
    worst_day: str


def _compute_summary(timeline: list) -> _SummaryData:
    """Extract averages, trend, best/worst day from timeline data."""
    sleep_scores = [e["sleep"]["sleep_score"] for e in timeline if e.get("sleep")]
    readiness_scores = [
        e["readiness"]["readiness_score"] for e in timeline if e.get("readiness")
    ]
    activity_scores = [
        e["activity"]["activity_score"] for e in timeline if e.get("activity")
    ]

    sorted_days = sorted(timeline, key=_day_score, reverse=True)
    best_day = sorted_days[0]["date"] if sorted_days else "N/A"
    worst_day = sorted_days[-1]["date"] if sorted_days else "N/A"

    return {
        "avg_sleep": _safe_avg(sleep_scores),
        "avg_readiness": _safe_avg(readiness_scores),
        "avg_activity": _safe_avg(activity_scores),
        "sleep_trend": _compute_sleep_trend(sleep_scores),
        "best_day": _fmt_date(best_day),
        "worst_day": _fmt_date(worst_day),
    }


def _weekly_subject() -> str:
    """Build the weekly email subject line."""
    week_start = (date.today() - timedelta(days=7)).strftime(_DATE_FMT)
    week_end = date.today().strftime(_DATE_FMT)
    return f"Your Health Week: {week_start} - {week_end}"


def _build_summary_html(
    user_name: str,
    avg_sleep: float,
    avg_readiness: float,
    avg_activity: float,
    sleep_trend: str,
    best_day: str,
    worst_day: str,
) -> str:
    """Build a simple HTML email for the weekly summary."""
    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
      <div style="text-align: center; margin-bottom: 24px;">
        <h1 style="color: #1e293b; font-size: 24px; margin: 0;">Your Weekly Health Summary</h1>
        <p style="color: #64748b; margin-top: 4px;">Hi {user_name}, here's how your week went.</p>
      </div>

      <div style="background: #f8fafc; border-radius: 12px; padding: 24px; margin-bottom: 20px;">
        <h2 style="color: #334155; font-size: 16px; margin: 0 0 16px 0;">Average Scores</h2>
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #64748b;">Sleep</td>
            <td style="padding: 8px 0; text-align: right; font-weight: 600; color: #6366f1;">{avg_sleep:.0f}/100</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #64748b;">Readiness</td>
            <td style="padding: 8px 0; text-align: right; font-weight: 600; color: #22c55e;">{avg_readiness:.0f}/100</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #64748b;">Activity</td>
            <td style="padding: 8px 0; text-align: right; font-weight: 600; color: #f59e0b;">{avg_activity:.0f}/100</td>
          </tr>
        </table>
      </div>

      <div style="background: #f8fafc; border-radius: 12px; padding: 24px; margin-bottom: 20px;">
        <h2 style="color: #334155; font-size: 16px; margin: 0 0 12px 0;">Highlights</h2>
        <p style="color: #475569; margin: 4px 0;">Sleep trend: <strong>{sleep_trend}</strong></p>
        <p style="color: #475569; margin: 4px 0;">Best day: <strong>{best_day}</strong></p>
        <p style="color: #475569; margin: 4px 0;">Needs attention: <strong>{worst_day}</strong></p>
      </div>

      <div style="text-align: center; margin-top: 24px;">
        <a href="https://healthassist.app/trends" style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View Full Trends</a>
      </div>

      <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 32px;">
        You're receiving this because you're a Pro+ subscriber.
        <a href="https://healthassist.app/settings" style="color: #94a3b8;">Manage preferences</a>
      </p>
    </div>
    """


@router.post("/send-weekly-summary")
async def send_weekly_summary(
    current_user: dict = Depends(get_current_user),
):
    """
    Send a weekly health summary email to the authenticated user.
    Only available for Pro+ subscribers.
    """
    user_id = current_user["id"]
    email = current_user.get("email", "")
    name = current_user.get("name", email.split("@")[0])

    tier = await get_user_tier(user_id)
    if tier != "pro_plus":
        raise HTTPException(
            status_code=403,
            detail="Weekly email summaries are a Pro+ feature",
        )

    from .timeline import get_timeline

    try:
        timeline = await get_timeline(days=7, current_user=current_user)
    except (HTTPException, KeyError, TypeError) as exc:
        logger.error(f"Failed to fetch timeline for email summary: {exc}")
        raise HTTPException(
            status_code=500, detail="Failed to generate summary"
        ) from exc

    if not timeline:
        return {"sent": False, "reason": "No data available for the past week"}

    summary = _compute_summary(timeline)
    html = _build_summary_html(user_name=name, **summary)
    sent = await _send_email(email, _weekly_subject(), html)
    return {"sent": sent}


@router.post("/send-bulk-weekly")
async def send_bulk_weekly(
    x_cron_secret: str = Header(..., alias="X-Cron-Secret"),
):
    """
    Cron-triggered endpoint to send weekly summaries to all Pro+ users.
    Requires X-Cron-Secret header matching the CRON_SECRET env var.
    """
    cron_secret = os.environ.get("CRON_SECRET", "")
    if not cron_secret:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")
    if x_cron_secret != cron_secret:
        raise HTTPException(status_code=401, detail="Invalid cron secret")

    rows = await _supabase_get(
        "subscriptions",
        "tier=eq.pro_plus&status=eq.active&select=user_id",
    )
    if not rows or not isinstance(rows, list):
        return {"sent": 0, "total": 0}

    sent_count = 0
    errors = 0
    subject = _weekly_subject()

    for row in rows:
        user_id = row.get("user_id")
        if not user_id:
            continue

        try:
            email, name = await _lookup_user_email(user_id)
            if not email:
                continue

            timeline = await _fetch_user_timeline(user_id, email)
            if not timeline:
                continue

            summary = _compute_summary(timeline)
            html = _build_summary_html(user_name=name or email.split("@")[0], **summary)
            if await _send_email(email, subject, html):
                sent_count += 1

        except (HTTPException, KeyError, TypeError) as exc:
            logger.warning(f"Failed to generate summary for user {user_id}: {exc}")
            errors += 1

    logger.info(
        f"Bulk weekly summary: sent={sent_count}, "
        f"errors={errors}, total={len(rows)}"
    )
    return {"sent": sent_count, "errors": errors, "total": len(rows)}


async def _lookup_user_email(
    user_id: str,
) -> tuple:
    """Look up user email and name from the profiles table."""
    profile_rows = await _supabase_get("profiles", f"id=eq.{user_id}&select=email,name")
    if not profile_rows or not isinstance(profile_rows, list):
        logger.warning(f"No email for user {user_id}, skipping")
        return "", ""
    row = profile_rows[0]
    email = row.get("email", "")
    name = row.get("name", email.split("@")[0] if email else "")
    return email, name


async def _fetch_user_timeline(user_id: str, email: str) -> Optional[list]:
    """Fetch 7-day timeline for a user (system context)."""
    from .timeline import get_timeline

    mock_user = {"id": user_id, "email": email, "user_type": "system"}
    return await get_timeline(days=7, current_user=mock_user)
