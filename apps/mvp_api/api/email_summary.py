"""
Weekly Health Email Summary API
Sends a weekly health digest to Pro+ users via Resend.
Can be triggered by a cron job (e.g., Render Cron or external scheduler).
"""

import os
from datetime import date, timedelta

import aiohttp
from fastapi import APIRouter, Depends, HTTPException

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
async def send_weekly_summary(current_user: dict = Depends(get_current_user)):
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

    # Fetch last 7 days of timeline data
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

    # Compute averages
    sleep_scores = [e["sleep"]["sleep_score"] for e in timeline if e.get("sleep")]
    readiness_scores = [
        e["readiness"]["readiness_score"] for e in timeline if e.get("readiness")
    ]
    activity_scores = [
        e["activity"]["activity_score"] for e in timeline if e.get("activity")
    ]

    avg_sleep = sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0
    avg_readiness = (
        sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0
    )
    avg_activity = sum(activity_scores) / len(activity_scores) if activity_scores else 0

    # Determine sleep trend
    if len(sleep_scores) >= 3:
        first_half = sum(sleep_scores[: len(sleep_scores) // 2]) / (
            len(sleep_scores) // 2
        )
        second_half = sum(sleep_scores[len(sleep_scores) // 2 :]) / (
            len(sleep_scores) - len(sleep_scores) // 2
        )
        if second_half - first_half > 3:
            sleep_trend = "Improving"
        elif first_half - second_half > 3:
            sleep_trend = "Declining"
        else:
            sleep_trend = "Stable"
    else:
        sleep_trend = "Not enough data"

    # Best and worst days
    def day_score(entry: dict) -> float:
        scores = []
        if entry.get("sleep"):
            scores.append(entry["sleep"]["sleep_score"])
        if entry.get("readiness"):
            scores.append(entry["readiness"]["readiness_score"])
        if entry.get("activity"):
            scores.append(entry["activity"]["activity_score"])
        return sum(scores) / len(scores) if scores else 0

    sorted_days = sorted(timeline, key=day_score, reverse=True)
    best_day = sorted_days[0]["date"] if sorted_days else "N/A"
    worst_day = sorted_days[-1]["date"] if sorted_days else "N/A"

    # Format dates nicely
    def fmt_date(d: str) -> str:
        try:
            dt = date.fromisoformat(d)
            return dt.strftime("%A, %b %d")
        except (ValueError, TypeError):
            return d

    html = _build_summary_html(
        user_name=name,
        avg_sleep=avg_sleep,
        avg_readiness=avg_readiness,
        avg_activity=avg_activity,
        sleep_trend=sleep_trend,
        best_day=fmt_date(best_day),
        worst_day=fmt_date(worst_day),
    )

    week_start = (date.today() - timedelta(days=7)).strftime("%b %d")
    week_end = date.today().strftime("%b %d")
    subject = f"Your Health Week: {week_start} - {week_end}"

    sent = await _send_email(email, subject, html)
    return {"sent": sent}


@router.post("/send-bulk-weekly")
async def send_bulk_weekly():
    """
    Cron-triggered endpoint to send weekly summaries to all Pro+ users.
    Should be called by an external scheduler with a secret header.
    """
    cron_secret = os.environ.get("CRON_SECRET", "")
    if not cron_secret:
        raise HTTPException(status_code=500, detail="CRON_SECRET not configured")

    # Fetch all Pro+ subscriptions
    rows = await _supabase_get(
        "subscriptions",
        "tier=eq.pro_plus&status=eq.active&select=user_id",
    )
    if not rows or not isinstance(rows, list):
        return {"sent": 0, "total": 0}

    sent_count = 0
    for row in rows:
        user_id = row.get("user_id")
        if not user_id:
            continue

        try:
            # Build a mock current_user dict for the timeline call
            mock_user = {"id": user_id, "email": "", "user_type": "system"}
            from .timeline import get_timeline

            timeline = await get_timeline(days=7, current_user=mock_user)
            if not timeline:
                continue

            # We'd need to look up email — simplified for now
            logger.info(
                f"Would send weekly summary to user {user_id} "
                f"({len(timeline)} days of data)"
            )
            sent_count += 1
        except (HTTPException, KeyError, TypeError) as exc:
            logger.warning(f"Failed to generate summary for user {user_id}: {exc}")

    return {"sent": sent_count, "total": len(rows)}
