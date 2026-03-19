"""
Personal Efficacy Model — What Works For Me

Tracks per-user intervention outcomes to build a personal response profile.
Used by the recommendation ranker to surface high-confidence suggestions first.
"""

import json
import os
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import certifi
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get, _supabase_upsert

logger = get_logger(__name__)
router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("EFFICACY_AI_MODEL", "claude-sonnet-4-6")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class EfficacyEntry(BaseModel):
    id: str
    pattern: str
    category: str
    interventions_tried: int
    avg_effect_size: float
    confidence: float
    best_duration: Optional[int] = None
    adherence_avg: float
    conditions_context: List[str]
    last_tested: Optional[str] = None
    status: str
    notes: Optional[str] = None


class EfficacySummary(BaseModel):
    entries: List[EfficacyEntry]
    proven: List[EfficacyEntry]
    disproven: List[EfficacyEntry]
    inconclusive: List[EfficacyEntry]
    untested: List[str]  # pattern names not yet tried
    ai_summary: Optional[str] = None


# ---------------------------------------------------------------------------
# Core: update efficacy after intervention completion
# ---------------------------------------------------------------------------

# All known patterns
ALL_PATTERNS = ["overtraining", "inflammation", "poor_recovery", "sleep_disruption"]

# Metrics that matter per pattern (for computing effect size)
_PATTERN_KEY_METRICS: Dict[str, List[str]] = {
    "overtraining": ["hrv_balance", "sleep_score", "readiness_score"],
    "inflammation": ["hrv_balance", "temperature_deviation", "sleep_score"],
    "poor_recovery": ["readiness_score", "resting_heart_rate", "hrv_balance"],
    "sleep_disruption": ["sleep_score", "sleep_efficiency", "deep_sleep_hours"],
}

_LOWER_IS_BETTER = {"resting_heart_rate", "temperature_deviation"}


async def update_efficacy(
    user_id: str,
    intervention: Dict[str, Any],
    outcome_delta: Dict[str, float],
) -> None:
    """
    Update the user's efficacy profile after an intervention completes.
    Called from interventions.py completion flow.
    """
    pattern = intervention.get("recommendation_pattern", "")
    if not pattern:
        return

    # Compute effect size: average improvement across key metrics for this pattern
    key_metrics = _PATTERN_KEY_METRICS.get(pattern, ["sleep_score", "hrv_balance"])
    effects = []
    for m in key_metrics:
        delta = outcome_delta.get(m)
        if delta is not None:
            # Normalize: for lower-is-better metrics, flip sign
            normalized = -delta if m in _LOWER_IS_BETTER else delta
            effects.append(normalized)

    effect_size = sum(effects) / len(effects) if effects else 0.0
    duration = intervention.get("duration_days", 7)
    adherence_days = intervention.get("adherence_days", 0) or 0
    adherence_pct = (adherence_days / max(duration, 1)) * 100

    # Fetch existing entry
    rows = await _supabase_get(
        "user_efficacy_profile",
        f"user_id=eq.{user_id}&pattern=eq.{pattern}&limit=1",
    )

    if rows:
        existing = rows[0]
        tried = existing.get("interventions_tried", 0) + 1
        prev_avg = existing.get("avg_effect_size", 0) or 0
        prev_adherence = existing.get("adherence_avg", 0) or 0

        # Running averages
        new_avg_effect = ((prev_avg * (tried - 1)) + effect_size) / tried
        new_adherence_avg = ((prev_adherence * (tried - 1)) + adherence_pct) / tried

        # Determine status
        if tried >= 2:
            if new_avg_effect > 3:
                status = "proven"
            elif new_avg_effect < 1 and tried >= 2:
                status = "disproven"
            else:
                status = "inconclusive"
        else:
            status = "inconclusive"

        # Confidence: combines consistency + adherence + sample size
        # Higher if effect is consistent and adherence is good
        consistency = (
            max(0, 1 - abs(effect_size - prev_avg) / max(abs(prev_avg), 1))
            if prev_avg != 0
            else 0.5
        )
        adherence_factor = min(new_adherence_avg / 100, 1)
        sample_factor = min(tried / 5, 1)  # caps at 5 tries
        confidence = round(
            (consistency * 0.4 + adherence_factor * 0.3 + sample_factor * 0.3), 2
        )

        # Best duration: keep the one with highest effect
        prev_best = existing.get("best_duration")
        best_duration = duration if effect_size > prev_avg else (prev_best or duration)

        await _supabase_upsert(
            "user_efficacy_profile",
            {
                "user_id": user_id,
                "pattern": pattern,
                "category": intervention.get("category", "nutrition"),
                "interventions_tried": tried,
                "avg_effect_size": round(new_avg_effect, 2),
                "confidence": confidence,
                "best_duration": best_duration,
                "adherence_avg": round(new_adherence_avg, 1),
                "last_tested": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    else:
        # First time trying this pattern
        status = "inconclusive"
        confidence = round(
            min(adherence_pct / 100, 1) * 0.5, 2
        )  # low confidence on first try

        await _supabase_upsert(
            "user_efficacy_profile",
            {
                "user_id": user_id,
                "pattern": pattern,
                "category": "nutrition",
                "interventions_tried": 1,
                "avg_effect_size": round(effect_size, 2),
                "confidence": confidence,
                "best_duration": duration,
                "adherence_avg": round(adherence_pct, 1),
                "last_tested": datetime.now(timezone.utc).isoformat(),
                "status": status,
            },
        )

    logger.info(
        "Updated efficacy for user=%s pattern=%s status=%s effect=%.1f",
        user_id,
        pattern,
        status,
        effect_size,
    )


# ---------------------------------------------------------------------------
# AI summary
# ---------------------------------------------------------------------------


async def _generate_efficacy_summary(entries: List[Dict[str, Any]]) -> str:
    """Generate a plain-English 'What works for me' summary."""
    if not entries or not ANTHROPIC_API_KEY:
        return _fallback_summary(entries)

    proven = [e for e in entries if e.get("status") == "proven"]
    disproven = [e for e in entries if e.get("status") == "disproven"]
    inconclusive = [e for e in entries if e.get("status") == "inconclusive"]

    lines = []
    for e in proven:
        lines.append(
            f"- {e['pattern'].replace('_', ' ').title()}: PROVEN effective (avg +{e['avg_effect_size']:.1f}% improvement, tried {e['interventions_tried']}x)"
        )
    for e in disproven:
        lines.append(
            f"- {e['pattern'].replace('_', ' ').title()}: NOT effective for you (avg {e['avg_effect_size']:.1f}%, tried {e['interventions_tried']}x)"
        )
    for e in inconclusive:
        lines.append(
            f"- {e['pattern'].replace('_', ' ').title()}: Inconclusive (avg {e['avg_effect_size']:.1f}%, tried {e['interventions_tried']}x)"
        )

    prompt = f"""Based on this user's personal health experiment results, write a 3-4 sentence summary of what works for their body and what doesn't. Be encouraging and specific.

Results:
{chr(10).join(lines)}

Write in second person ("Your body responds well to..."). Focus on actionable takeaways."""

    try:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["content"][0]["text"].strip()
    except Exception as exc:
        logger.warning("Efficacy AI summary failed: %s", exc)

    return _fallback_summary(entries)


def _fallback_summary(entries: List[Dict[str, Any]]) -> str:
    proven = [e for e in entries if e.get("status") == "proven"]
    if not entries:
        return "Start your first experiment to discover what works for your body."
    if proven:
        names = [e["pattern"].replace("_", " ") for e in proven]
        return f"Your body responds well to interventions targeting {', '.join(names)}. Keep building on these proven patterns."
    return f"You've tried {sum(e.get('interventions_tried', 0) for e in entries)} experiments so far. More data will help identify what works best for you."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=EfficacySummary)
async def get_efficacy(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get the user's personal efficacy profile."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "user_efficacy_profile",
        f"user_id=eq.{user_id}&order=confidence.desc",
    )
    entries_raw = rows or []

    entries = [
        EfficacyEntry(
            id=r["id"],
            pattern=r["pattern"],
            category=r.get("category", "nutrition"),
            interventions_tried=r.get("interventions_tried", 0),
            avg_effect_size=r.get("avg_effect_size", 0),
            confidence=r.get("confidence", 0),
            best_duration=r.get("best_duration"),
            adherence_avg=r.get("adherence_avg", 0),
            conditions_context=r.get("conditions_context") or [],
            last_tested=r.get("last_tested"),
            status=r.get("status", "untested"),
            notes=r.get("notes"),
        )
        for r in entries_raw
    ]

    tested_patterns = {e.pattern for e in entries}
    untested = [p for p in ALL_PATTERNS if p not in tested_patterns]

    proven = [e for e in entries if e.status == "proven"]
    disproven = [e for e in entries if e.status == "disproven"]
    inconclusive = [e for e in entries if e.status == "inconclusive"]

    ai_summary = await _generate_efficacy_summary(entries_raw)

    return EfficacySummary(
        entries=entries,
        proven=proven,
        disproven=disproven,
        inconclusive=inconclusive,
        untested=untested,
        ai_summary=ai_summary,
    )


@router.get("/summary")
async def get_efficacy_summary_only(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get a brief AI-generated summary of what works for this user."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "user_efficacy_profile",
        f"user_id=eq.{user_id}&order=confidence.desc",
    )
    summary = await _generate_efficacy_summary(rows or [])
    return {"summary": summary}
