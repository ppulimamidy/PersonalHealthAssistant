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
    current_user: dict = Depends(UsageGate("interventions")),
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

    # Update intervention record
    await _supabase_patch(
        "active_interventions",
        f"id=eq.{intervention_id}",
        {
            "status": "completed",
            "outcome_metrics": outcome_metrics,
            "outcome_delta": outcome_delta,
            "updated_at": "now()",
        },
    )

    # Write to agent_memory as learned_pattern (feeds correlation prior)
    await _write_learned_pattern(user_id, intervention, outcome_delta, summary)

    return InterventionOutcome(
        baseline_metrics=baseline,
        outcome_metrics=outcome_metrics,
        outcome_delta=outcome_delta,
        adherence_pct=adherence_pct,
        summary=summary,
        completed_at=completed_at,
    )


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
    return {"status": "abandoned"}
