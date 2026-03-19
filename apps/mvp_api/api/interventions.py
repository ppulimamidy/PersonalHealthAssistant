"""
N-of-1 Interventions API — Personal Learning Loop

Allows users to accept a recommendation as a timed trial intervention,
track daily adherence, and auto-measure health delta at completion.
Outcomes are written to agent_memory for use as correlation priors.

Health-data-source agnostic: baseline/outcome metrics are extracted via
get_timeline() which aggregates Oura today; Apple Health and Google Health
will flow through the same timeline abstraction when integrated.

Provider-in-the-loop: outcomes are accessible via share tokens, so care
teams can review personal experiment results without the system autonomously
adapting treatment.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,line-too-long

import json
import os
import ssl
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import certifi
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_upsert,
    _supabase_insert,
    _supabase_patch,
)

logger = get_logger(__name__)
router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("INTERVENTION_AI_MODEL", "claude-sonnet-4-6")


def _ssl_ctx() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class StartInterventionRequest(BaseModel):
    recommendation_pattern: str  # overtraining|inflammation|poor_recovery|sleep_disruption
    title: str
    description: Optional[str] = None
    duration_days: int = 7


class StartFromRecommendationRequest(BaseModel):
    recommendation_pattern: str
    title: str
    description: Optional[str] = None
    duration_days: int = 7
    evidence: Optional[Dict[str, Any]] = None


class CheckinRequest(BaseModel):
    adhered: bool = True
    notes: Optional[str] = None
    checkin_date: Optional[str] = None  # ISO date string; defaults to today


class InterventionCheckin(BaseModel):
    id: str
    intervention_id: str
    checkin_date: str
    adhered: bool
    notes: Optional[str] = None
    created_at: str


class InterventionOutcome(BaseModel):
    baseline_metrics: Dict[str, Any]
    outcome_metrics: Dict[str, Any]
    outcome_delta: Dict[str, float]  # metric -> % change
    adherence_pct: float
    summary: Optional[str] = None  # AI-generated plain English summary
    completed_at: str


class MetricTrendPoint(BaseModel):
    date: str
    metric: str
    value: Optional[float] = None


class KeyMetricDelta(BaseModel):
    metric: str
    label: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    delta_pct: Optional[float] = None
    direction: str = "stable"  # up|down|stable


class ActiveIntervention(BaseModel):
    id: str
    user_id: str
    recommendation_pattern: str
    title: str
    description: Optional[str] = None
    duration_days: int
    started_at: str
    ends_at: str
    status: str  # active|completed|abandoned
    baseline_metrics: Optional[Dict[str, Any]] = None
    outcome_metrics: Optional[Dict[str, Any]] = None
    outcome_delta: Optional[Dict[str, float]] = None
    adherence_days: int
    data_sources: List[str]
    created_at: str
    updated_at: str
    # Computed fields
    days_remaining: Optional[int] = None
    adherence_pct: Optional[float] = None
    checkins: Optional[List[InterventionCheckin]] = None
    # Metric tracking for active experiments
    metric_trend: Optional[List[MetricTrendPoint]] = None
    key_metric: Optional[KeyMetricDelta] = None
    today_checked_in: Optional[bool] = None


# ---------------------------------------------------------------------------
# Health metrics extraction (source-agnostic)
# ---------------------------------------------------------------------------

# Key metrics to snapshot at baseline/outcome.
# When Apple Health or Google Health are integrated, their data will be
# normalised through the same get_timeline() → _extract_metrics() path.
TRACKED_METRICS = [
    "sleep_score",
    "sleep_efficiency",
    "deep_sleep_hours",
    "hrv_balance",
    "resting_heart_rate",
    "readiness_score",
    "recovery_index",
    "temperature_deviation",
    "steps",
    "activity_score",
    # Native wearable metrics (Apple Health, Health Connect, any Tier 1/2 device)
    "respiratory_rate",
    "spo2",
    "active_calories",
    "workout_minutes",
    "vo2_max",
]


def _extract_metrics(timeline: list) -> Dict[str, Optional[float]]:
    """
    Extract a rolling 3-day average of key health metrics from a timeline.
    Source-agnostic: timeline entries may originate from Oura, Apple Health,
    Google Health, or any other wearable. The field names are normalised by
    the timeline aggregator.
    """
    # Collect up to last 3 days worth of data
    recent = timeline[-3:] if len(timeline) >= 3 else timeline
    if not recent:
        return {m: None for m in TRACKED_METRICS}

    aggregated: Dict[str, List[float]] = {m: [] for m in TRACKED_METRICS}
    for entry in recent:
        oura = entry.get("oura", {}) or {}
        sleep = oura.get("sleep") or {}
        readiness = oura.get("readiness") or {}
        activity = oura.get("activity") or {}

        # Also check native_health_data fields surfaced by the timeline aggregator
        native = entry.get("native", {}) or {}

        metric_map = {
            "sleep_score": sleep.get("score"),
            "sleep_efficiency": sleep.get("efficiency"),
            "deep_sleep_hours": (sleep.get("deep") or 0) / 3600
            if sleep.get("deep")
            else None,
            "hrv_balance": readiness.get("hrv_balance"),
            "resting_heart_rate": readiness.get("resting_heart_rate"),
            "readiness_score": readiness.get("score"),
            "recovery_index": readiness.get("recovery_index"),
            "temperature_deviation": readiness.get("temperature_deviation"),
            "steps": activity.get("steps"),
            "activity_score": activity.get("score"),
            # Native wearable metrics — populated from Apple Health / Health Connect
            "respiratory_rate": native.get("respiratory_rate"),
            "spo2": native.get("spo2"),
            "active_calories": native.get("active_calories")
            or activity.get("active_calories"),
            "workout_minutes": native.get("workout_minutes"),
            "vo2_max": native.get("vo2_max"),
        }
        # Also check top-level normalised fields (future Apple/Google sources)
        for m in TRACKED_METRICS:
            val = metric_map.get(m)
            if val is None:
                val = entry.get(m)
            if val is not None:
                try:
                    aggregated[m].append(float(val))
                except (TypeError, ValueError):
                    pass

    result: Dict[str, Optional[float]] = {}
    for m in TRACKED_METRICS:
        vals = aggregated[m]
        result[m] = round(sum(vals) / len(vals), 2) if vals else None
    return result


def _compute_delta(
    baseline: Dict[str, Any], outcome: Dict[str, Any]
) -> Dict[str, float]:
    """Compute % change between baseline and outcome for available metrics."""
    delta: Dict[str, float] = {}
    for metric, base_val in baseline.items():
        out_val = outcome.get(metric)
        if base_val is not None and out_val is not None:
            try:
                b = float(base_val)
                o = float(out_val)
                if b != 0:
                    delta[metric] = round(((o - b) / abs(b)) * 100, 1)
            except (TypeError, ValueError):
                pass
    return delta


# ---------------------------------------------------------------------------
# Agent memory: write learned patterns
# ---------------------------------------------------------------------------


async def _write_learned_pattern(
    user_id: str,
    intervention: Dict[str, Any],
    outcome_delta: Dict[str, float],
    summary: str,
) -> None:
    """
    Persist the intervention outcome to agent_memory as a learned_pattern.
    The correlation engine reads these priors to personalise threshold relaxation.
    """
    pattern = intervention.get("recommendation_pattern", "unknown")
    memory_key = f"intervention_outcome_{pattern}_{intervention['id'][:8]}"
    memory_value = {
        "pattern": pattern,
        "title": intervention.get("title"),
        "duration_days": intervention.get("duration_days"),
        "adherence_days": intervention.get("adherence_days", 0),
        "outcome_delta": outcome_delta,
        "data_sources": intervention.get("data_sources", ["oura"]),
        "summary": summary,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    # Confidence: adherence percentage mapped to 0–1
    duration = max(intervention.get("duration_days", 7), 1)
    adherence = intervention.get("adherence_days", 0) / duration
    confidence = round(min(1.0, adherence), 2)

    await _supabase_upsert(
        "agent_memory",
        {
            "agent_id": "metabolic_intelligence",
            "user_id": user_id,
            "memory_key": memory_key,
            "memory_value": memory_value,
            "memory_type": "learned_pattern",
            "confidence_score": confidence,
            "is_active": True,
        },
    )
    logger.info(
        "Wrote learned_pattern to agent_memory: %s for user %s", memory_key, user_id
    )


# ---------------------------------------------------------------------------
# AI outcome summary
# ---------------------------------------------------------------------------


async def _generate_outcome_summary(
    intervention: Dict[str, Any],
    outcome_delta: Dict[str, float],
    adherence_pct: float,
) -> str:
    """Generate a plain-English summary of what the intervention achieved."""
    if not ANTHROPIC_API_KEY:
        return _fallback_summary(outcome_delta, adherence_pct)

    pattern = intervention.get("recommendation_pattern", "unknown")
    title = intervention.get("title", "Intervention")
    duration = intervention.get("duration_days", 7)

    delta_lines = []
    for metric, pct in outcome_delta.items():
        direction = "improved" if pct > 0 else "decreased"
        friendly = metric.replace("_", " ").title()
        delta_lines.append(f"  - {friendly}: {direction} by {abs(pct):.1f}%")

    delta_text = (
        "\n".join(delta_lines) if delta_lines else "  - No significant changes detected"
    )

    prompt = f"""A user completed a {duration}-day {pattern.replace('_', ' ')} nutrition intervention titled "{title}".

Adherence: {adherence_pct:.0f}% of days followed.

Observed metric changes:
{delta_text}

Write a 2–3 sentence plain-English summary of what this personal experiment revealed. Be specific about which metrics changed and by how much. End with one practical insight the user can apply going forward. Keep it encouraging and factual. Do not diagnose or prescribe."""

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }
    timeout = aiohttp.ClientTimeout(total=15)
    connector = aiohttp.TCPConnector(ssl=_ssl_ctx())
    try:
        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector
        ) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["content"][0]["text"].strip()
    except Exception as exc:
        logger.warning("AI outcome summary failed: %s", exc)

    return _fallback_summary(outcome_delta, adherence_pct)


def _fallback_summary(outcome_delta: Dict[str, float], adherence_pct: float) -> str:
    if not outcome_delta:
        return f"Intervention completed with {adherence_pct:.0f}% adherence. Insufficient data to measure impact."
    positives = [m for m, v in outcome_delta.items() if v > 3]
    negatives = [m for m, v in outcome_delta.items() if v < -3]
    parts = []
    if positives:
        friendly = [m.replace("_", " ") for m in positives[:2]]
        parts.append(f"Improvements in {', '.join(friendly)}")
    if negatives:
        friendly = [m.replace("_", " ") for m in negatives[:2]]
        parts.append(f"Decreases in {', '.join(friendly)}")
    if not parts:
        parts.append("Metrics remained largely stable")
    return f"{'. '.join(parts)} over the trial period ({adherence_pct:.0f}% adherence)."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enrich_intervention(row: Dict[str, Any]) -> Dict[str, Any]:
    """Add computed fields to a raw DB row."""
    row = dict(row)
    try:
        ends_at = datetime.fromisoformat(row["ends_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        row["days_remaining"] = max(0, (ends_at - now).days)
    except Exception:
        row["days_remaining"] = None

    duration = max(row.get("duration_days", 7), 1)
    adhered = row.get("adherence_days", 0)
    row["adherence_pct"] = round((adhered / duration) * 100, 1)
    row["data_sources"] = row.get("data_sources") or ["oura"]
    return row


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ActiveIntervention, status_code=201)
async def start_intervention(
    body: StartInterventionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a recommendation as a timed trial intervention.
    Captures baseline health metrics from the current timeline snapshot.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # Capture baseline from current timeline (source-agnostic)
    try:
        timeline = await get_timeline(days=7, current_user=current_user)
        baseline = _extract_metrics(timeline)
    except Exception as exc:
        logger.warning("Could not capture baseline metrics: %s", exc)
        baseline = {}

    now = datetime.now(timezone.utc)
    ends_at = now + timedelta(days=body.duration_days)

    row = {
        "user_id": user_id,
        "recommendation_pattern": body.recommendation_pattern,
        "title": body.title,
        "description": body.description,
        "duration_days": body.duration_days,
        "started_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "status": "active",
        "baseline_metrics": baseline,
        "adherence_days": 0,
        "data_sources": [
            "oura"
        ],  # will expand when Apple/Google Health integrations land
    }

    result = await _supabase_insert("active_interventions", row)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create intervention")

    return ActiveIntervention(**_enrich_intervention(result))


@router.get("", response_model=List[ActiveIntervention])
async def list_interventions(
    request: Request,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List user's interventions (optionally filtered by status)."""
    user_id = current_user["id"]
    params = f"user_id=eq.{user_id}&order=created_at.desc"
    if status:
        params += f"&status=eq.{status}"

    rows = await _supabase_get("active_interventions", params)
    return [ActiveIntervention(**_enrich_intervention(r)) for r in (rows or [])]


@router.post(
    "/{intervention_id}/checkin", response_model=InterventionCheckin, status_code=201
)
async def daily_checkin(
    intervention_id: str,
    body: CheckinRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Log daily adherence for an intervention.
    Increments adherence_days on the intervention when adhered=True.
    """
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "active_interventions",
        f"id=eq.{intervention_id}&user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Active intervention not found")

    checkin_date = body.checkin_date or date.today().isoformat()

    checkin = await _supabase_upsert(
        "intervention_checkins",
        {
            "intervention_id": intervention_id,
            "user_id": user_id,
            "checkin_date": checkin_date,
            "adhered": body.adhered,
            "notes": body.notes,
        },
    )
    if not checkin:
        raise HTTPException(status_code=500, detail="Failed to record check-in")

    # Increment adherence_days if adhered
    if body.adhered:
        current_adherence = rows[0].get("adherence_days", 0) or 0
        await _supabase_patch(
            "active_interventions",
            f"id=eq.{intervention_id}",
            {"adherence_days": current_adherence + 1, "updated_at": "now()"},
        )

    return InterventionCheckin(
        id=checkin["id"],
        intervention_id=checkin["intervention_id"],
        checkin_date=checkin["checkin_date"],
        adhered=checkin["adhered"],
        notes=checkin.get("notes"),
        created_at=checkin["created_at"],
    )


@router.post("/{intervention_id}/complete", response_model=InterventionOutcome)
async def complete_intervention(
    intervention_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Complete a trial intervention.
    1. Captures outcome metrics from the health timeline.
    2. Computes % delta vs baseline.
    3. Generates AI outcome summary.
    4. Writes learned_pattern to agent_memory for use as correlation prior.
    5. Provider-accessible via existing share tokens.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    rows = await _supabase_get(
        "active_interventions",
        f"id=eq.{intervention_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Intervention not found")

    intervention = rows[0]
    if intervention["status"] not in ("active", "completed"):
        raise HTTPException(status_code=400, detail="Intervention is not active")

    # Capture outcome metrics from timeline (source-agnostic)
    try:
        timeline = await get_timeline(days=7, current_user=current_user)
        outcome_metrics = _extract_metrics(timeline)
    except Exception as exc:
        logger.warning("Could not capture outcome metrics: %s", exc)
        outcome_metrics = {}

    baseline = intervention.get("baseline_metrics") or {}
    outcome_delta = _compute_delta(baseline, outcome_metrics)

    duration = max(intervention.get("duration_days", 7), 1)
    adherence_days = intervention.get("adherence_days", 0) or 0
    adherence_pct = round((adherence_days / duration) * 100, 1)

    # Generate AI plain-English summary
    summary = await _generate_outcome_summary(
        intervention, outcome_delta, adherence_pct
    )

    completed_at = datetime.now(timezone.utc).isoformat()

    # Update intervention record (including summary for later retrieval)
    await _supabase_patch(
        "active_interventions",
        f"id=eq.{intervention_id}",
        {
            "status": "completed",
            "outcome_metrics": outcome_metrics,
            "outcome_delta": outcome_delta,
            "outcome_summary": summary,
            "updated_at": "now()",
        },
    )

    # Write to agent_memory as learned_pattern (feeds correlation prior)
    await _write_learned_pattern(user_id, intervention, outcome_delta, summary)

    # Update personal efficacy model
    from .efficacy import update_efficacy

    await update_efficacy(user_id, intervention, outcome_delta)

    return InterventionOutcome(
        baseline_metrics=baseline,
        outcome_metrics=outcome_metrics,
        outcome_delta=outcome_delta,
        adherence_pct=adherence_pct,
        summary=summary,
        completed_at=completed_at,
    )


# Friendly labels for metric names
_METRIC_LABELS: Dict[str, str] = {
    "sleep_score": "Sleep Score",
    "sleep_efficiency": "Sleep Efficiency",
    "deep_sleep_hours": "Deep Sleep",
    "hrv_balance": "HRV Balance",
    "resting_heart_rate": "Resting HR",
    "readiness_score": "Readiness",
    "recovery_index": "Recovery",
    "temperature_deviation": "Temp Deviation",
    "steps": "Steps",
    "activity_score": "Activity",
    "respiratory_rate": "Respiratory Rate",
    "spo2": "SpO2",
    "active_calories": "Active Calories",
    "workout_minutes": "Workout Minutes",
    "vo2_max": "VO2 Max",
}

# Which metrics are "higher is better" vs "lower is better"
_LOWER_IS_BETTER = {"resting_heart_rate", "temperature_deviation"}


@router.get("/active", response_model=Optional[ActiveIntervention])
async def get_active_intervention(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current active intervention with live metric trends.
    Includes daily metric values since baseline, key metric with biggest
    positive change, and whether user has checked in today.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]
    rows = await _supabase_get(
        "active_interventions",
        f"user_id=eq.{user_id}&status=eq.active&order=created_at.desc&limit=1",
    )
    if not rows:
        return None

    # Lazy auto-complete: if experiment duration has expired, complete it now
    row = rows[0]
    try:
        ends_at = datetime.fromisoformat(row["ends_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) >= ends_at:
            logger.info("Auto-completing expired intervention %s", row["id"])
            await _auto_complete_intervention(row, current_user)
            return None  # No longer active — frontend will pick up the result via /latest-result
    except Exception as exc:
        logger.warning("Auto-complete check failed: %s", exc)

    intervention = _enrich_intervention(row)

    # Fetch check-ins
    checkin_rows = await _supabase_get(
        "intervention_checkins",
        f"intervention_id=eq.{intervention['id']}&order=checkin_date.asc",
    )
    checkins = checkin_rows or []
    intervention["checkins"] = [
        InterventionCheckin(
            id=c["id"],
            intervention_id=c["intervention_id"],
            checkin_date=c["checkin_date"],
            adhered=c["adhered"],
            notes=c.get("notes"),
            created_at=c["created_at"],
        )
        for c in checkins
    ]

    # Check if user checked in today
    today_str = date.today().isoformat()
    intervention["today_checked_in"] = any(
        c["checkin_date"] == today_str for c in checkins
    )

    # Compute metric trend: daily values from timeline since experiment started
    baseline = intervention.get("baseline_metrics") or {}
    try:
        started = datetime.fromisoformat(
            intervention["started_at"].replace("Z", "+00:00")
        )
        days_elapsed = max(1, (datetime.now(timezone.utc) - started).days + 1)
        timeline = await get_timeline(
            days=min(days_elapsed, 30), current_user=current_user
        )
    except Exception as exc:
        logger.warning("Could not fetch timeline for metric trend: %s", exc)
        timeline = []

    # Build trend for key metrics that have baseline values
    trend_points: List[Dict[str, Any]] = []
    # Focus on metrics relevant to the pattern
    pattern = intervention.get("recommendation_pattern", "")
    focus_metrics = _pattern_focus_metrics(pattern)

    for entry in timeline:
        entry_date = entry.get("date", "")
        snapshot = _extract_metrics([entry])
        for m in focus_metrics:
            val = snapshot.get(m)
            if val is not None:
                trend_points.append({"date": entry_date, "metric": m, "value": val})

    intervention["metric_trend"] = trend_points

    # Find key metric: biggest positive improvement vs baseline
    if baseline and timeline:
        current_snapshot = _extract_metrics(
            timeline[-3:] if len(timeline) >= 3 else timeline
        )
        best_metric = None
        best_delta = 0.0
        for m in focus_metrics:
            bv = baseline.get(m)
            cv = current_snapshot.get(m)
            if bv is not None and cv is not None and bv != 0:
                delta_pct = ((cv - bv) / abs(bv)) * 100
                # For "lower is better" metrics, flip the sign for ranking
                rank_delta = -delta_pct if m in _LOWER_IS_BETTER else delta_pct
                if rank_delta > best_delta:
                    best_delta = rank_delta
                    # Keep actual delta_pct for display
                    actual_delta = delta_pct
                    direction = (
                        "down"
                        if actual_delta < -1
                        else ("up" if actual_delta > 1 else "stable")
                    )
                    best_metric = KeyMetricDelta(
                        metric=m,
                        label=_METRIC_LABELS.get(m, m.replace("_", " ").title()),
                        baseline_value=round(bv, 1),
                        current_value=round(cv, 1),
                        delta_pct=round(actual_delta, 1),
                        direction=direction,
                    )
        intervention["key_metric"] = best_metric

    return ActiveIntervention(**intervention)


def _pattern_focus_metrics(pattern: str) -> List[str]:
    """Return the metrics most relevant to a given pattern."""
    mapping = {
        "overtraining": [
            "hrv_balance",
            "sleep_score",
            "readiness_score",
            "resting_heart_rate",
        ],
        "inflammation": [
            "hrv_balance",
            "temperature_deviation",
            "sleep_score",
            "readiness_score",
        ],
        "poor_recovery": [
            "readiness_score",
            "resting_heart_rate",
            "hrv_balance",
            "sleep_score",
        ],
        "sleep_disruption": [
            "sleep_score",
            "sleep_efficiency",
            "deep_sleep_hours",
            "hrv_balance",
        ],
    }
    return mapping.get(
        pattern, ["sleep_score", "hrv_balance", "readiness_score", "steps"]
    )


@router.post("/from-recommendation", response_model=ActiveIntervention, status_code=201)
async def start_from_recommendation(
    body: StartFromRecommendationRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    One-tap start: create an intervention directly from a recommendation card.
    Also records the 'started' event for recommendation tracking.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # Check no active intervention already
    active = await _supabase_get(
        "active_interventions",
        f"user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if active:
        raise HTTPException(
            status_code=409, detail="An active intervention already exists"
        )

    # Capture baseline
    try:
        timeline = await get_timeline(days=7, current_user=current_user)
        baseline = _extract_metrics(timeline)
    except Exception as exc:
        logger.warning("Could not capture baseline metrics: %s", exc)
        baseline = {}

    now = datetime.now(timezone.utc)
    ends_at = now + timedelta(days=body.duration_days)

    row = {
        "user_id": user_id,
        "recommendation_pattern": body.recommendation_pattern,
        "title": body.title,
        "description": body.description,
        "duration_days": body.duration_days,
        "started_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "status": "active",
        "baseline_metrics": baseline,
        "adherence_days": 0,
        "data_sources": ["oura"],
        "recommendation_evidence": body.evidence,
    }

    result = await _supabase_insert("active_interventions", row)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create intervention")

    # Record the 'started' event
    await _supabase_insert(
        "recommendation_events",
        {
            "user_id": user_id,
            "recommendation_pattern": body.recommendation_pattern,
            "event_type": "started",
        },
    )

    # Schedule nudges for the experiment
    from .nudges import schedule_intervention_nudges

    await schedule_intervention_nudges(
        user_id=user_id,
        intervention_id=result["id"],
        title=body.title,
        duration_days=body.duration_days,
        started_at=now,
    )

    return ActiveIntervention(**_enrich_intervention(result))


@router.patch("/{intervention_id}/abandon", status_code=200)
async def abandon_intervention(
    intervention_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Mark an intervention as abandoned."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "active_interventions",
        f"id=eq.{intervention_id}&user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Active intervention not found")

    await _supabase_patch(
        "active_interventions",
        f"id=eq.{intervention_id}",
        {"status": "abandoned", "updated_at": "now()"},
    )

    # Cancel pending nudges
    from .nudges import cancel_intervention_nudges

    await cancel_intervention_nudges(intervention_id)

    return {"status": "abandoned"}


# ---------------------------------------------------------------------------
# Auto-complete helper (shared by lazy check + cron endpoint)
# ---------------------------------------------------------------------------


async def _auto_complete_intervention(
    intervention: Dict[str, Any],
    current_user: dict,
) -> None:
    """
    Complete an expired intervention: capture outcome, compute delta,
    generate summary, write learned pattern, update DB.
    """
    from .timeline import get_timeline

    user_id = intervention["user_id"]

    try:
        timeline = await get_timeline(days=7, current_user=current_user)
        outcome_metrics = _extract_metrics(timeline)
    except Exception as exc:
        logger.warning("Auto-complete: could not capture outcome: %s", exc)
        outcome_metrics = {}

    baseline = intervention.get("baseline_metrics") or {}
    outcome_delta = _compute_delta(baseline, outcome_metrics)

    duration = max(intervention.get("duration_days", 7), 1)
    adherence_days = intervention.get("adherence_days", 0) or 0
    adherence_pct = round((adherence_days / duration) * 100, 1)

    summary = await _generate_outcome_summary(
        intervention, outcome_delta, adherence_pct
    )

    await _supabase_patch(
        "active_interventions",
        f"id=eq.{intervention['id']}",
        {
            "status": "completed",
            "outcome_metrics": outcome_metrics,
            "outcome_delta": outcome_delta,
            "outcome_summary": summary,
            "updated_at": "now()",
        },
    )

    await _write_learned_pattern(user_id, intervention, outcome_delta, summary)

    # Update personal efficacy model
    from .efficacy import update_efficacy

    await update_efficacy(user_id, intervention, outcome_delta)

    # If linked to a journey phase, check if phase should auto-advance
    journey_id = intervention.get("journey_id")
    if journey_id:
        await _check_journey_phase_complete(journey_id, intervention, current_user)

    logger.info(
        "Auto-completed intervention %s for user %s", intervention["id"], user_id
    )


async def _check_journey_phase_complete(
    journey_id: str,
    intervention: Dict[str, Any],
    current_user: dict,
) -> None:
    """When a journey-linked intervention completes, auto-advance the journey phase."""
    try:
        from .journeys import advance_phase, AdvancePhaseRequest

        # Verify the journey is active and the intervention matches current phase
        rows = await _supabase_get(
            "goal_journeys",
            f"id=eq.{journey_id}&status=eq.active&limit=1",
        )
        if not rows:
            return

        journey = rows[0]
        current_phase_idx = journey.get("current_phase", 0)
        intervention_phase = intervention.get("journey_phase")

        if intervention_phase is not None and intervention_phase == current_phase_idx:
            logger.info(
                "Journey %s phase %d intervention completed — auto-advancing",
                journey_id,
                current_phase_idx,
            )
            # Create a mock request for the advance endpoint
            from starlette.requests import Request as StarletteRequest
            from starlette.datastructures import Headers
            import io

            scope = {
                "type": "http",
                "method": "POST",
                "path": f"/api/v1/journeys/{journey_id}/advance",
                "headers": [],
            }
            mock_request = StarletteRequest(scope, receive=lambda: None)
            await advance_phase(
                journey_id=journey_id,
                body=AdvancePhaseRequest(
                    skip=False, notes="Phase experiment completed"
                ),
                request=mock_request,
                current_user=current_user,
            )
    except Exception as exc:
        logger.warning("Journey phase auto-advance failed: %s", exc)


# ---------------------------------------------------------------------------
# Latest result + keep-as-habit
# ---------------------------------------------------------------------------


class LatestResult(BaseModel):
    id: str
    title: str
    recommendation_pattern: str
    duration_days: int
    adherence_days: int
    adherence_pct: float
    baseline_metrics: Dict[str, Any]
    outcome_metrics: Dict[str, Any]
    outcome_delta: Dict[str, float]
    summary: Optional[str] = None
    completed_at: Optional[str] = None
    status: str


@router.get("/latest-result", response_model=Optional[LatestResult])
async def get_latest_result(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the most recently completed intervention (within last 14 days).
    Used to show the Results card on Home after an experiment ends.
    Returns null if no recent completions or if already dismissed/adopted.
    """
    user_id = current_user["id"]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    rows = await _supabase_get(
        "active_interventions",
        f"user_id=eq.{user_id}&status=eq.completed&updated_at=gte.{cutoff}"
        f"&order=updated_at.desc&limit=1",
    )
    if not rows:
        return None

    r = rows[0]
    duration = max(r.get("duration_days", 7), 1)
    adherence_days = r.get("adherence_days", 0) or 0

    return LatestResult(
        id=r["id"],
        title=r.get("title", ""),
        recommendation_pattern=r.get("recommendation_pattern", ""),
        duration_days=duration,
        adherence_days=adherence_days,
        adherence_pct=round((adherence_days / duration) * 100, 1),
        baseline_metrics=r.get("baseline_metrics") or {},
        outcome_metrics=r.get("outcome_metrics") or {},
        outcome_delta=r.get("outcome_delta") or {},
        summary=r.get("outcome_summary"),
        completed_at=r.get("updated_at"),
        status=r.get("status", "completed"),
    )


@router.post("/{intervention_id}/keep-as-habit", status_code=200)
async def keep_as_habit(
    intervention_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a completed intervention as a habit the user wants to maintain.
    Boosts the learned pattern confidence in agent_memory.
    """
    user_id = current_user["id"]
    rows = await _supabase_get(
        "active_interventions",
        f"id=eq.{intervention_id}&user_id=eq.{user_id}&status=eq.completed&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Completed intervention not found")

    # Update status
    await _supabase_patch(
        "active_interventions",
        f"id=eq.{intervention_id}",
        {"status": "habit_adopted", "updated_at": "now()"},
    )

    # Boost confidence of the learned pattern in agent_memory
    pattern = rows[0].get("recommendation_pattern", "unknown")
    memory_key = f"intervention_outcome_{pattern}_{intervention_id[:8]}"
    await _supabase_patch(
        "agent_memory",
        f"memory_key=eq.{memory_key}&user_id=eq.{user_id}",
        {"confidence_score": 1.0, "is_active": True},
    )

    # Record adoption event
    await _supabase_insert(
        "recommendation_events",
        {
            "user_id": user_id,
            "recommendation_pattern": pattern,
            "event_type": "started",  # reuse 'started' as positive signal
            "reason": "habit_adopted",
        },
    )

    return {"status": "habit_adopted", "pattern": pattern}


@router.post("/{intervention_id}/dismiss-result", status_code=200)
async def dismiss_result(
    intervention_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Dismiss the results card without adopting. Keeps status as 'completed'
    but the /latest-result endpoint won't show it again (no status change needed —
    the frontend simply hides it locally).
    """
    return {"status": "dismissed"}


# ---------------------------------------------------------------------------
# Parameterized route LAST — so /active, /latest-result, /from-recommendation match first
# ---------------------------------------------------------------------------


@router.get("/{intervention_id}", response_model=ActiveIntervention)
async def get_intervention(
    intervention_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get a single intervention with its check-ins."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "active_interventions",
        f"id=eq.{intervention_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Intervention not found")

    intervention = _enrich_intervention(rows[0])

    # Fetch check-ins
    checkin_rows = await _supabase_get(
        "intervention_checkins",
        f"intervention_id=eq.{intervention_id}&order=checkin_date.asc",
    )
    intervention["checkins"] = [
        InterventionCheckin(
            id=c["id"],
            intervention_id=c["intervention_id"],
            checkin_date=c["checkin_date"],
            adhered=c["adhered"],
            notes=c.get("notes"),
            created_at=c["created_at"],
        )
        for c in (checkin_rows or [])
    ]

    return ActiveIntervention(**intervention)
