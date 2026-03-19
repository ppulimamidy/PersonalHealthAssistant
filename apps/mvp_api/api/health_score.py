"""
Daily Health Score API
Computes a weighted composite score from wearable sleep, activity, and readiness data.
Sources: any connected device via the canonical pipeline (Oura, Apple Health, Health Connect, etc.).
"""

import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()

USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")

# Weights for composite score
WEIGHT_SLEEP = 0.40
WEIGHT_READINESS = 0.35
WEIGHT_ACTIVITY = 0.25


async def get_user_optional(request: Request) -> dict:
    """Get current user, or return a sandbox user if in sandbox mode."""
    if USE_SANDBOX:
        try:
            return await get_current_user(request)
        except HTTPException:
            return {
                "id": "sandbox-user-123",
                "email": "sandbox@example.com",
                "user_type": "sandbox",
            }
    return await get_current_user(request)


@router.get("")
async def get_health_score(current_user: dict = Depends(get_user_optional)):
    """
    Get today's composite health score.

    Primary: reads canonical scores from health_metric_summaries (device-agnostic).
    Fallback: reads from Oura timeline (legacy).

    Weights: sleep 35%, recovery 30%, activity 25%, cardiac 10%.
    """
    user_id = current_user["id"]

    # Primary: canonical scores from summaries
    try:
        canonical_score, canonical_breakdown = await _compute_score_from_canonical(user_id)
        if canonical_score is not None:
            return {
                "score": round(canonical_score, 1),
                "breakdown": canonical_breakdown,
                "trend": "stable",  # TODO: compare with previous day's canonical scores
                "change_from_yesterday": 0,
                "date": str(__import__("datetime").date.today()),
            }
    except Exception as exc:
        logger.debug("Canonical health score failed, trying timeline: %s", exc)

    # Fallback: Oura timeline
    from .timeline import get_timeline

    try:
        timeline = await get_timeline(days=2, current_user=current_user)
    except (HTTPException, KeyError, TypeError) as exc:
        logger.error(f"Failed to fetch timeline for health score: {exc}")
        return _empty_score()

    if not timeline:
        return _empty_score()

    today = timeline[0]
    yesterday = timeline[1] if len(timeline) > 1 else None

    today_score, today_breakdown = _compute_score(today)
    yesterday_score = _compute_score(yesterday)[0] if yesterday else None

    if today_score is None:
        return _empty_score()

    trend = "stable"
    change = 0.0
    if yesterday_score is not None:
        change = round(today_score - yesterday_score, 1)
        if change > 2:
            trend = "up"
        elif change < -2:
            trend = "down"

    return {
        "score": round(today_score, 1),
        "breakdown": today_breakdown,
        "trend": trend,
        "change_from_yesterday": change,
        "date": getattr(today, "date", None),
    }


async def _compute_score_from_canonical(user_id: str):
    """Compute health score from canonical scores in health_metric_summaries."""
    rows = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&canonical_metric=not.is.null&select=canonical_metric,canonical_score",
    )
    if not rows:
        return None, {}

    scores = {r["canonical_metric"]: r["canonical_score"] for r in rows if r.get("canonical_score") is not None}

    sleep_q = scores.get("sleep_quality")
    recovery = scores.get("recovery")
    activity = scores.get("activity_level")
    cardiac = scores.get("cardiac_stress")

    components = []
    breakdown = {}

    if sleep_q is not None:
        w = 0.35
        components.append(sleep_q * w)
        breakdown["sleep"] = {"score": sleep_q, "weight": w, "weighted": round(sleep_q * w, 1)}

    if recovery is not None:
        w = 0.30
        components.append(recovery * w)
        breakdown["recovery"] = {"score": recovery, "weight": w, "weighted": round(recovery * w, 1)}

    if activity is not None:
        w = 0.25
        components.append(activity * w)
        breakdown["activity"] = {"score": activity, "weight": w, "weighted": round(activity * w, 1)}

    if cardiac is not None:
        w = 0.10
        inverted = 100 - cardiac  # lower stress = higher health
        components.append(inverted * w)
        breakdown["cardiac"] = {"score": round(inverted, 1), "weight": w, "weighted": round(inverted * w, 1)}

    if not components:
        return None, breakdown

    total_weight = sum(b["weight"] for b in breakdown.values())
    score = sum(components) / total_weight if total_weight > 0 else 0
    return score, breakdown


def _native_sleep_score(sleep_entry) -> float | None:
    """Estimate a 0–100 sleep quality score from raw sleep duration when native score unavailable."""
    duration_sec = getattr(sleep_entry, "total_sleep_duration", 0) or 0
    if duration_sec <= 0:
        return None
    hours = duration_sec / 3600
    score: float
    if hours < 4:
        score = 20.0
    elif hours < 6:
        score = 40 + (hours - 4) * 20
    elif hours <= 8:
        score = 70 + (hours - 6) * 7.5
    elif hours <= 9:
        score = 85 - (hours - 8) * 5
    else:
        score = 80.0
    return min(100, max(0, round(score)))


def _native_activity_score(activity_entry) -> float | None:
    """Estimate a 0–100 activity score from step count when native score unavailable."""
    steps = getattr(activity_entry, "steps", 0) or 0
    if steps <= 0:
        return None
    if steps < 2000:
        score = steps / 2000 * 20
    elif steps < 7500:
        score = 20 + (steps - 2000) / 5500 * 50
    elif steps < 12000:
        score = 70 + (steps - 7500) / 4500 * 30
    else:
        score = 100
    return min(100, max(0, round(score)))


def _compute_score(entry) -> tuple:
    """Compute weighted health score from a timeline entry. Returns (score, breakdown)."""
    if entry is None:
        return None, {}

    sleep_entry = getattr(entry, "sleep", None)
    readiness_entry = getattr(entry, "readiness", None)
    activity_entry = getattr(entry, "activity", None)

    sleep_score = getattr(sleep_entry, "sleep_score", None) if sleep_entry else None
    readiness_score = (
        getattr(readiness_entry, "readiness_score", None) if readiness_entry else None
    )
    activity_score = (
        getattr(activity_entry, "activity_score", None) if activity_entry else None
    )

    # Fall back to native-derived scores when device scores are absent or zero
    if (sleep_score is None or sleep_score == 0) and sleep_entry:
        sleep_score = _native_sleep_score(sleep_entry)

    if (activity_score is None or activity_score == 0) and activity_entry:
        activity_score = _native_activity_score(activity_entry)

    components = []
    breakdown = {}

    if sleep_score is not None:
        weighted = sleep_score * WEIGHT_SLEEP
        components.append(weighted)
        breakdown["sleep"] = {
            "score": sleep_score,
            "weight": WEIGHT_SLEEP,
            "weighted": round(weighted, 1),
        }

    if readiness_score is not None:
        weighted = readiness_score * WEIGHT_READINESS
        components.append(weighted)
        breakdown["readiness"] = {
            "score": readiness_score,
            "weight": WEIGHT_READINESS,
            "weighted": round(weighted, 1),
        }

    if activity_score is not None:
        weighted = activity_score * WEIGHT_ACTIVITY
        components.append(weighted)
        breakdown["activity"] = {
            "score": activity_score,
            "weight": WEIGHT_ACTIVITY,
            "weighted": round(weighted, 1),
        }

    if not components:
        return None, breakdown

    # Normalize: if only some components are available, scale proportionally
    total_weight = sum(b["weight"] for b in breakdown.values())
    score = sum(components) / total_weight if total_weight > 0 else 0

    return score, breakdown


def _empty_score():
    return {
        "score": None,
        "breakdown": {},
        "trend": "stable",
        "change_from_yesterday": 0,
        "date": None,
    }


# ── Trajectory score ───────────────────────────────────────────────────────────


class TrajectoryComponent(BaseModel):
    name: str
    label: str
    score: float  # 0–100
    weight: float  # 0–1
    available: bool  # False when insufficient data


class TrajectoryResponse(BaseModel):
    score: Optional[float]  # weighted composite 0–100
    delta_30d: Optional[float]  # change vs 30 days ago
    direction: str  # "up" | "down" | "stable" | "insufficient"
    components: List[TrajectoryComponent]
    data_quality: str  # "good" | "partial" | "insufficient"


def _avg(vals: list) -> Optional[float]:
    clean = [v for v in vals if v is not None]
    return sum(clean) / len(clean) if clean else None


@router.get("/trajectory", response_model=TrajectoryResponse)
async def get_trajectory(current_user: dict = Depends(get_current_user)):
    """
    Composite health trajectory score (0–100) from four pillars:
      1. Medication adherence (30d)     weight 25%
      2. Symptom severity (30d, inverted) weight 25%
      3. Goal/plan engagement            weight 25%
      4. Well-being check-ins (energy + mood) weight 25%

    Also returns a delta vs the previous 30-day period where data allows.
    """
    user_id = current_user["id"]
    today = date.today()

    components: List[TrajectoryComponent] = []
    period_scores: Dict[str, Optional[float]] = {}  # current period
    prev_scores: Dict[str, Optional[float]] = {}  # 30–60d ago

    # ── 1. Medication adherence ──────────────────────────────────────────────
    try:
        start_curr = (today - timedelta(days=30)).isoformat()
        start_prev = (today - timedelta(days=60)).isoformat()
        end_prev = (today - timedelta(days=30)).isoformat()

        rows_curr = (
            await _supabase_get(
                "medication_adherence_log",
                f"user_id=eq.{user_id}&date=gte.{start_curr}&select=was_taken&limit=500",
            )
            or []
        )
        rows_prev = (
            await _supabase_get(
                "medication_adherence_log",
                f"user_id=eq.{user_id}&date=gte.{start_prev}&date=lte.{end_prev}&select=was_taken&limit=500",
            )
            or []
        )

        if rows_curr:
            taken = sum(1 for r in rows_curr if r.get("was_taken"))
            period_scores["adherence"] = round(taken / len(rows_curr) * 100)
        if rows_prev:
            taken_p = sum(1 for r in rows_prev if r.get("was_taken"))
            prev_scores["adherence"] = round(taken_p / len(rows_prev) * 100)

        components.append(
            TrajectoryComponent(
                name="adherence",
                label="Med. Adherence",
                score=period_scores.get("adherence") or 0.0,
                weight=0.25,
                available="adherence" in period_scores,
            )
        )
    except Exception as exc:
        logger.warning("Trajectory adherence: %s", exc)
        components.append(
            TrajectoryComponent(
                name="adherence",
                label="Med. Adherence",
                score=0,
                weight=0.25,
                available=False,
            )
        )

    # ── 2. Symptom severity (inverted: lower = better score) ─────────────────
    try:
        start_curr = (today - timedelta(days=30)).isoformat()
        start_prev = (today - timedelta(days=60)).isoformat()
        end_prev = (today - timedelta(days=30)).isoformat()

        symp_curr = (
            await _supabase_get(
                "symptom_journal",
                f"user_id=eq.{user_id}&symptom_date=gte.{start_curr}&select=severity&limit=200",
            )
            or []
        )
        symp_prev = (
            await _supabase_get(
                "symptom_journal",
                f"user_id=eq.{user_id}&symptom_date=gte.{start_prev}&symptom_date=lte.{end_prev}&select=severity&limit=200",
            )
            or []
        )

        def _sev_to_score(rows: list) -> Optional[float]:
            sevs = [r["severity"] for r in rows if r.get("severity") is not None]
            if not sevs:
                return None
            avg_sev = sum(sevs) / len(sevs)
            return round(max(0, 100 - avg_sev * 10))

        s = _sev_to_score(symp_curr)
        if s is not None:
            period_scores["symptoms"] = s
        sp = _sev_to_score(symp_prev)
        if sp is not None:
            prev_scores["symptoms"] = sp

        components.append(
            TrajectoryComponent(
                name="symptoms",
                label="Symptom Control",
                score=period_scores.get("symptoms") or 0.0,
                weight=0.25,
                available="symptoms" in period_scores,
            )
        )
    except Exception as exc:
        logger.warning("Trajectory symptoms: %s", exc)
        components.append(
            TrajectoryComponent(
                name="symptoms",
                label="Symptom Control",
                score=0,
                weight=0.25,
                available=False,
            )
        )

    # ── 3. Goal / care-plan engagement ───────────────────────────────────────
    try:
        goals_all = (
            await _supabase_get(
                "user_goals",
                f"user_id=eq.{user_id}&select=status&limit=100",
            )
            or []
        )
        plans_all = (
            await _supabase_get(
                "care_plans",
                f"user_id=eq.{user_id}&select=status&limit=100",
            )
            or []
        )

        all_items = goals_all + plans_all
        if all_items:
            completed = sum(
                1 for i in all_items if i.get("status") in ("achieved", "completed")
            )
            total = len(all_items)
            # Score: proportion completed + partial credit for having active items
            active = sum(1 for i in all_items if i.get("status") == "active")
            # Engagement: 50 pts for having active items, 50 pts for completion rate
            engagement = 50 if active > 0 else 0
            completion_rate = (completed / total * 50) if total > 0 else 0
            period_scores["engagement"] = round(engagement + completion_rate)
        else:
            period_scores["engagement"] = None

        components.append(
            TrajectoryComponent(
                name="engagement",
                label="Goal Engagement",
                score=period_scores.get("engagement") or 0.0,
                weight=0.25,
                available=period_scores.get("engagement") is not None,
            )
        )
    except Exception as exc:
        logger.warning("Trajectory engagement: %s", exc)
        components.append(
            TrajectoryComponent(
                name="engagement",
                label="Goal Engagement",
                score=0,
                weight=0.25,
                available=False,
            )
        )

    # ── 4. Well-being check-ins (energy + mood) ───────────────────────────────
    try:
        checkins_curr = (
            await _supabase_get(
                "weekly_checkins",
                f"user_id=eq.{user_id}&order=checked_in_at.desc&select=energy,mood&limit=4",
            )
            or []
        )
        checkins_prev = (
            await _supabase_get(
                "weekly_checkins",
                f"user_id=eq.{user_id}&order=checked_in_at.desc&select=energy,mood&limit=4&offset=4",
            )
            or []
        )

        def _checkin_score(rows: list) -> Optional[float]:
            if not rows:
                return None
            avg_energy = _avg([r.get("energy") for r in rows])
            avg_mood = _avg([r.get("mood") for r in rows])
            if avg_energy is None or avg_mood is None:
                return None
            return round((avg_energy + avg_mood) / 2 * 10)  # 0–10 → 0–100

        wb = _checkin_score(checkins_curr)
        if wb is not None:
            period_scores["wellbeing"] = wb
        wbp = _checkin_score(checkins_prev)
        if wbp is not None:
            prev_scores["wellbeing"] = wbp

        components.append(
            TrajectoryComponent(
                name="wellbeing",
                label="Well-being",
                score=period_scores.get("wellbeing") or 0.0,
                weight=0.25,
                available="wellbeing" in period_scores,
            )
        )
    except Exception as exc:
        logger.warning("Trajectory wellbeing: %s", exc)
        components.append(
            TrajectoryComponent(
                name="wellbeing",
                label="Well-being",
                score=0,
                weight=0.25,
                available=False,
            )
        )

    # ── Composite score ───────────────────────────────────────────────────────
    available = [c for c in components if c.available]
    if len(available) == 0:
        return TrajectoryResponse(
            score=None,
            delta_30d=None,
            direction="insufficient",
            components=components,
            data_quality="insufficient",
        )

    total_weight = sum(c.weight for c in available)
    composite = sum(c.score * c.weight for c in available) / total_weight

    # Previous period composite
    prev_available_keys = set(prev_scores.keys())
    if prev_available_keys:
        prev_comps = [c for c in components if c.name in prev_available_keys]
        prev_total_w = sum(c.weight for c in prev_comps)
        prev_composite: Optional[float] = (
            sum(((prev_scores[c.name] or 0.0) * c.weight for c in prev_comps), 0.0)
            / prev_total_w
            if prev_total_w > 0
            else None
        )
    else:
        prev_composite = None

    delta = round(composite - prev_composite, 1) if prev_composite is not None else None
    direction = (
        "up"
        if delta is not None and delta > 3
        else "down"
        if delta is not None and delta < -3
        else "stable"
        if delta is not None
        else "insufficient"
    )

    data_quality = (
        "good"
        if len(available) == 4
        else "partial"
        if len(available) >= 2
        else "insufficient"
    )

    return TrajectoryResponse(
        score=round(composite, 1),
        delta_30d=delta,
        direction=direction,
        components=components,
        data_quality=data_quality,
    )
