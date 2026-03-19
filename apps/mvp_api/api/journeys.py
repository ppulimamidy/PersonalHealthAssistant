"""
Goal Journeys API — Multi-phase health improvement programs

A Goal Journey wraps multiple experiments (interventions) into a structured
program with phases, milestones, and specialist agent guidance.

Quick experiments are journeys with one phase and no specialist.
Complex journeys (PCOS, cardiac rehab, etc.) have multiple phases,
cycle-based timing, and lab checkpoints.
"""

import json
import os
import ssl
from datetime import datetime, timedelta, timezone
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
    _supabase_insert,
    _supabase_patch,
)

logger = get_logger(__name__)
router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("JOURNEY_AI_MODEL", "claude-sonnet-4-6")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class PhaseDefinition(BaseModel):
    name: str
    description: str = ""
    phase_type: str = "intervention"  # observation | intervention | checkpoint
    duration_days_estimate: int = 30
    duration_type: str = "fixed"  # fixed | cycle_based | until_lab | manual
    experiment: Optional[
        Dict[str, Any]
    ] = None  # null for observation/checkpoint phases
    tracked_metrics: List[str] = []
    checkpoints: List[Dict[str, Any]] = []
    # Status fields (set during execution)
    status: str = "pending"  # pending | active | completed | skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    outcome_summary: Optional[str] = None


class CreateJourneyRequest(BaseModel):
    title: str
    condition: Optional[str] = None
    goal_type: str = "general_wellness"
    specialist_agent_id: Optional[str] = None
    duration_type: str = "week_based"
    target_metrics: List[str] = []
    phases: List[PhaseDefinition]


class JourneyOverview(BaseModel):
    id: str
    title: str
    condition: Optional[str] = None
    goal_type: str
    specialist_agent_id: Optional[str] = None
    duration_type: str
    target_metrics: List[str]
    phases: List[Dict[str, Any]]
    current_phase: int
    status: str
    baseline_snapshot: Optional[Dict[str, Any]] = None
    outcome_snapshot: Optional[Dict[str, Any]] = None
    started_at: str
    completed_at: Optional[str] = None
    # Computed
    total_phases: int = 0
    progress_pct: float = 0
    current_phase_name: Optional[str] = None
    days_active: int = 0


class AdvancePhaseRequest(BaseModel):
    skip: bool = False  # Skip current phase without completing
    notes: Optional[str] = None


class CheckpointRequest(BaseModel):
    lab_results: Dict[str, Any]
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enrich_journey(row: Dict[str, Any]) -> Dict[str, Any]:
    """Add computed fields to a journey row."""
    row = dict(row)
    phases = row.get("phases") or []
    if isinstance(phases, str):
        phases = json.loads(phases)
    row["phases"] = phases
    row["total_phases"] = len(phases)
    row["target_metrics"] = row.get("target_metrics") or []

    current = row.get("current_phase", 0)
    completed_count = sum(1 for p in phases if p.get("status") == "completed")
    row["progress_pct"] = (
        round((completed_count / len(phases)) * 100, 1) if phases else 0
    )

    if 0 <= current < len(phases):
        row["current_phase_name"] = phases[current].get("name", f"Phase {current + 1}")
    else:
        row["current_phase_name"] = None

    try:
        started = datetime.fromisoformat(row["started_at"].replace("Z", "+00:00"))
        row["days_active"] = max(0, (datetime.now(timezone.utc) - started).days)
    except Exception:
        row["days_active"] = 0

    return row


async def _capture_baseline(current_user: dict) -> Dict[str, Any]:
    """Capture current health metrics as journey baseline."""
    from .timeline import get_timeline
    from .interventions import _extract_metrics

    try:
        timeline = await get_timeline(days=7, current_user=current_user)
        return _extract_metrics(timeline)
    except Exception as exc:
        logger.warning("Could not capture journey baseline: %s", exc)
        return {}


async def _start_phase_experiment(
    user_id: str,
    journey_id: str,
    phase_index: int,
    phase: Dict[str, Any],
    current_user: dict,
) -> Optional[str]:
    """
    If the phase has an experiment definition, create an intervention for it.
    Returns the intervention ID or None.
    """
    experiment = phase.get("experiment")
    if not experiment:
        return None

    from .interventions import _extract_metrics
    from .timeline import get_timeline

    try:
        timeline = await get_timeline(days=7, current_user=current_user)
        baseline = _extract_metrics(timeline)
    except Exception:
        baseline = {}

    now = datetime.now(timezone.utc)
    duration = phase.get("duration_days_estimate", 30)
    ends_at = now + timedelta(days=duration)

    row = {
        "user_id": user_id,
        "recommendation_pattern": experiment.get("recommendation_pattern", "custom"),
        "title": experiment.get("title", phase.get("name", "Journey Phase")),
        "description": experiment.get("description", phase.get("description", "")),
        "duration_days": duration,
        "started_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "status": "active",
        "baseline_metrics": baseline,
        "adherence_days": 0,
        "data_sources": ["oura"],
        "journey_id": journey_id,
        "journey_phase": phase_index,
    }

    result = await _supabase_insert("active_interventions", row)
    if result:
        # Schedule nudges for this experiment
        from .nudges import schedule_intervention_nudges

        await schedule_intervention_nudges(
            user_id=user_id,
            intervention_id=result["id"],
            title=row["title"],
            duration_days=duration,
            started_at=now,
        )
        return result["id"]
    return None


async def _generate_phase_summary(
    journey: Dict[str, Any],
    phase: Dict[str, Any],
    phase_index: int,
) -> str:
    """Generate an AI summary of what happened in a completed phase."""
    if not ANTHROPIC_API_KEY:
        return f"Phase {phase_index + 1} ({phase.get('name', 'unnamed')}) completed."

    prompt = f"""A user completed phase {phase_index + 1} of their health journey "{journey.get('title', '')}".

Phase: {phase.get('name', '')}
Type: {phase.get('phase_type', 'intervention')}
Description: {phase.get('description', '')}

Write 1-2 sentences summarizing this phase completion and what to expect next. Be encouraging."""

    try:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        timeout = aiohttp.ClientTimeout(total=10)
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
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["content"][0]["text"].strip()
    except Exception as exc:
        logger.warning("Journey phase summary failed: %s", exc)

    return f"Phase {phase_index + 1} ({phase.get('name', 'unnamed')}) completed."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=JourneyOverview, status_code=201)
async def create_journey(
    body: CreateJourneyRequest,
    request: Request,
    current_user: dict = Depends(UsageGate("interventions")),
):
    """Create a new goal journey with defined phases."""
    user_id = current_user["id"]

    # Only one active journey at a time
    active = await _supabase_get(
        "goal_journeys",
        f"user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if active:
        raise HTTPException(status_code=409, detail="An active journey already exists")

    # Capture baseline
    baseline = await _capture_baseline(current_user)

    # Prepare phases with initial status
    phases = []
    for i, p in enumerate(body.phases):
        phase_dict = p.model_dump()
        phase_dict["status"] = "active" if i == 0 else "pending"
        if i == 0:
            phase_dict["started_at"] = datetime.now(timezone.utc).isoformat()
        phases.append(phase_dict)

    row = {
        "user_id": user_id,
        "title": body.title,
        "condition": body.condition,
        "goal_type": body.goal_type,
        "specialist_agent_id": body.specialist_agent_id,
        "duration_type": body.duration_type,
        "target_metrics": body.target_metrics,
        "phases": phases,
        "current_phase": 0,
        "status": "active",
        "baseline_snapshot": baseline,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_insert("goal_journeys", row)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create journey")

    # Start first phase's experiment if it has one
    if phases and phases[0].get("experiment"):
        await _start_phase_experiment(
            user_id=user_id,
            journey_id=result["id"],
            phase_index=0,
            phase=phases[0],
            current_user=current_user,
        )

    return JourneyOverview(**_enrich_journey(result))


@router.get("", response_model=List[JourneyOverview])
async def list_journeys(
    request: Request,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List user's journeys, optionally filtered by status."""
    user_id = current_user["id"]
    params = f"user_id=eq.{user_id}&order=created_at.desc"
    if status:
        params += f"&status=eq.{status}"

    rows = await _supabase_get("goal_journeys", params)
    return [JourneyOverview(**_enrich_journey(r)) for r in (rows or [])]


@router.get("/active", response_model=Optional[JourneyOverview])
async def get_active_journey(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get the current active journey (or null)."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"user_id=eq.{user_id}&status=eq.active&order=created_at.desc&limit=1",
    )
    if not rows:
        return None
    return JourneyOverview(**_enrich_journey(rows[0]))


@router.get("/{journey_id}", response_model=JourneyOverview)
async def get_journey(
    journey_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get journey details with phase status."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Journey not found")
    return JourneyOverview(**_enrich_journey(rows[0]))


@router.post("/{journey_id}/advance", response_model=JourneyOverview)
async def advance_phase(
    journey_id: str,
    body: AdvancePhaseRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Complete the current phase and advance to the next one.
    If skip=True, marks current phase as skipped instead of completed.
    If this was the last phase, marks the journey as completed.
    """
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Active journey not found")

    journey = rows[0]
    phases = journey.get("phases") or []
    if isinstance(phases, str):
        phases = json.loads(phases)
    current_idx = journey.get("current_phase", 0)

    if current_idx >= len(phases):
        raise HTTPException(status_code=400, detail="No more phases to advance")

    # Complete current phase
    now = datetime.now(timezone.utc).isoformat()
    phases[current_idx]["status"] = "skipped" if body.skip else "completed"
    phases[current_idx]["completed_at"] = now

    if not body.skip:
        phases[current_idx]["outcome_summary"] = await _generate_phase_summary(
            journey, phases[current_idx], current_idx
        )

    next_idx = current_idx + 1

    if next_idx >= len(phases):
        # Journey complete
        outcome = await _capture_baseline(current_user)
        await _supabase_patch(
            "goal_journeys",
            f"id=eq.{journey_id}",
            {
                "phases": phases,
                "current_phase": next_idx,
                "status": "completed",
                "outcome_snapshot": outcome,
                "completed_at": now,
                "updated_at": now,
            },
        )
    else:
        # Start next phase
        phases[next_idx]["status"] = "active"
        phases[next_idx]["started_at"] = now

        await _supabase_patch(
            "goal_journeys",
            f"id=eq.{journey_id}",
            {
                "phases": phases,
                "current_phase": next_idx,
                "updated_at": now,
            },
        )

        # Start next phase's experiment if it has one
        if phases[next_idx].get("experiment"):
            await _start_phase_experiment(
                user_id=user_id,
                journey_id=journey_id,
                phase_index=next_idx,
                phase=phases[next_idx],
                current_user=current_user,
            )

    # Re-fetch and return
    updated = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&limit=1",
    )
    return JourneyOverview(**_enrich_journey(updated[0]))


@router.post("/{journey_id}/checkpoint", response_model=JourneyOverview)
async def record_checkpoint(
    journey_id: str,
    body: CheckpointRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Record lab results at a checkpoint.
    If the current phase is a checkpoint phase, this can trigger advancement.
    """
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Active journey not found")

    journey = rows[0]
    phases = journey.get("phases") or []
    if isinstance(phases, str):
        phases = json.loads(phases)
    current_idx = journey.get("current_phase", 0)

    if current_idx >= len(phases):
        raise HTTPException(status_code=400, detail="No active phase")

    current_phase = phases[current_idx]

    # Store lab results in the phase checkpoints
    checkpoints = current_phase.get("checkpoints") or []
    checkpoints.append(
        {
            "type": "lab_results",
            "data": body.lab_results,
            "notes": body.notes,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    phases[current_idx]["checkpoints"] = checkpoints

    await _supabase_patch(
        "goal_journeys",
        f"id=eq.{journey_id}",
        {
            "phases": phases,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    # If this is a checkpoint phase with duration_type "until_lab", auto-advance
    if current_phase.get("duration_type") == "until_lab":
        return await advance_phase(
            journey_id=journey_id,
            body=AdvancePhaseRequest(skip=False, notes="Lab checkpoint received"),
            request=request,
            current_user=current_user,
        )

    updated = await _supabase_get("goal_journeys", f"id=eq.{journey_id}&limit=1")
    return JourneyOverview(**_enrich_journey(updated[0]))


@router.patch("/{journey_id}/pause", status_code=200)
async def pause_journey(
    journey_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Pause an active journey."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Active journey not found")

    await _supabase_patch(
        "goal_journeys",
        f"id=eq.{journey_id}",
        {"status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()},
    )
    return {"status": "paused"}


@router.patch("/{journey_id}/resume", status_code=200)
async def resume_journey(
    journey_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Resume a paused journey."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&user_id=eq.{user_id}&status=eq.paused&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Paused journey not found")

    await _supabase_patch(
        "goal_journeys",
        f"id=eq.{journey_id}",
        {"status": "active", "updated_at": datetime.now(timezone.utc).isoformat()},
    )
    return {"status": "active"}


@router.post("/auto-checkpoint")
async def auto_checkpoint_from_lab(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Called after lab results are saved. Checks if the user has an active journey
    with a checkpoint phase waiting for labs, and auto-records the checkpoint.
    Returns the journey if updated, null otherwise.
    """
    user_id = current_user["id"]

    # Find active journey
    rows = await _supabase_get(
        "goal_journeys",
        f"user_id=eq.{user_id}&status=eq.active&limit=1",
    )
    if not rows:
        return {"updated": False}

    journey = rows[0]
    phases = journey.get("phases") or []
    if isinstance(phases, str):
        phases = json.loads(phases)
    current_idx = journey.get("current_phase", 0)

    if current_idx >= len(phases):
        return {"updated": False}

    current_phase = phases[current_idx]

    # Check if current phase is a checkpoint waiting for labs
    if current_phase.get("phase_type") != "checkpoint":
        return {"updated": False}

    if current_phase.get("duration_type") != "until_lab":
        return {"updated": False}

    # Fetch recent lab results (last 7 days)
    from datetime import timedelta

    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    lab_rows = await _supabase_get(
        "lab_results",
        f"user_id=eq.{user_id}&created_at=gte.{cutoff}&order=created_at.desc&limit=10",
    )

    if not lab_rows:
        return {"updated": False}

    # Record checkpoint and auto-advance
    lab_data = {r.get("test_name", "unknown"): r.get("value") for r in lab_rows}
    checkpoints = current_phase.get("checkpoints") or []
    checkpoints.append(
        {
            "type": "lab_results",
            "data": lab_data,
            "notes": f"Auto-detected from {len(lab_rows)} recent lab results",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    phases[current_idx]["checkpoints"] = checkpoints

    await _supabase_patch(
        "goal_journeys",
        f"id=eq.{journey['id']}",
        {"phases": phases, "updated_at": datetime.now(timezone.utc).isoformat()},
    )

    # Auto-advance since we received the labs
    body = AdvancePhaseRequest(
        skip=False, notes="Lab checkpoint auto-recorded from new lab results"
    )
    result = await advance_phase(
        journey_id=journey["id"],
        body=body,
        request=request,
        current_user=current_user,
    )
    return {"updated": True, "journey": result}


@router.patch("/{journey_id}/abandon", status_code=200)
async def abandon_journey(
    journey_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Abandon a journey. Also abandons any active linked intervention."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "goal_journeys",
        f"id=eq.{journey_id}&user_id=eq.{user_id}&status=in.(active,paused)&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Journey not found")

    # Abandon any active linked interventions
    linked = await _supabase_get(
        "active_interventions",
        f"journey_id=eq.{journey_id}&status=eq.active",
    )
    for intervention in linked or []:
        await _supabase_patch(
            "active_interventions",
            f"id=eq.{intervention['id']}",
            {"status": "abandoned", "updated_at": "now()"},
        )
        from .nudges import cancel_intervention_nudges

        await cancel_intervention_nudges(intervention["id"])

    await _supabase_patch(
        "goal_journeys",
        f"id=eq.{journey_id}",
        {"status": "abandoned", "updated_at": datetime.now(timezone.utc).isoformat()},
    )
    return {"status": "abandoned"}
