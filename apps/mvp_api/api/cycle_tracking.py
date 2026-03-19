"""
Cycle Tracking API — Menstrual Cycle Logging & Phase Intelligence

Provides cycle logging, phase estimation, and cycle-aware normalization
for the experiment engine. Ensures experiment results compare same-phase
data (follicular vs follicular, luteal vs luteal) rather than mixing phases.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CycleLogRequest(BaseModel):
    event_type: str  # period_start|period_end|ovulation|symptom
    event_date: str  # ISO date
    flow_intensity: Optional[str] = None  # light|medium|heavy|spotting
    symptoms: List[str] = []
    notes: Optional[str] = None


class CycleLogEntry(BaseModel):
    id: str
    event_type: str
    event_date: str
    flow_intensity: Optional[str] = None
    symptoms: List[str] = []
    notes: Optional[str] = None
    created_at: str


class CyclePhase(BaseModel):
    phase: str  # menstrual|follicular|ovulation|luteal|unknown
    cycle_day: Optional[int] = None
    days_until_next_period: Optional[int] = None
    confidence: str = "low"  # low|medium|high


class CycleInfo(BaseModel):
    current_phase: CyclePhase
    avg_cycle_length: Optional[int] = None
    last_period_start: Optional[str] = None
    cycles_tracked: int = 0
    is_regular: Optional[bool] = None  # cycles within ±3 days of average


class CycleHistoryEntry(BaseModel):
    cycle_number: int
    start_date: str
    end_date: Optional[str] = None
    length_days: Optional[int] = None
    ovulation_date: Optional[str] = None


class CycleHistory(BaseModel):
    cycles: List[CycleHistoryEntry]
    avg_length: Optional[int] = None
    shortest: Optional[int] = None
    longest: Optional[int] = None
    is_regular: Optional[bool] = None


# ---------------------------------------------------------------------------
# Phase estimation logic
# ---------------------------------------------------------------------------


def _estimate_phase(
    cycle_day: int,
    avg_cycle_length: int,
    ovulation_day: Optional[int] = None,
) -> str:
    """
    Estimate menstrual cycle phase from cycle day.
    Uses population averages when personal ovulation data unavailable.
    """
    if cycle_day <= 0:
        return "unknown"

    # Menstrual phase: days 1-5 (typically)
    if cycle_day <= 5:
        return "menstrual"

    # Estimate ovulation day
    ov_day = ovulation_day or max(avg_cycle_length - 14, 10)

    # Follicular: day 6 to ovulation-1
    if cycle_day < ov_day:
        return "follicular"

    # Ovulation: ~2 day window
    if cycle_day <= ov_day + 1:
        return "ovulation"

    # Luteal: ovulation+2 to end
    return "luteal"


def _phase_confidence(cycles_tracked: int, has_ovulation_data: bool) -> str:
    """Determine confidence in phase estimation."""
    if cycles_tracked >= 3 and has_ovulation_data:
        return "high"
    if cycles_tracked >= 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Cycle-aware metric normalization (used by interventions)
# ---------------------------------------------------------------------------


async def get_cycle_phase_for_date(
    user_id: str, target_date: date
) -> Optional[CyclePhase]:
    """
    Determine the cycle phase for a specific date.
    Used by the intervention engine to normalize metrics by phase.
    """
    # Get recent period starts
    rows = await _supabase_get(
        "cycle_logs",
        f"user_id=eq.{user_id}&event_type=eq.period_start"
        f"&event_date=lte.{target_date.isoformat()}"
        f"&order=event_date.desc&limit=6",
    )
    if not rows:
        return None

    period_starts = [date.fromisoformat(r["event_date"]) for r in rows]
    last_start = period_starts[0]
    cycle_day = (target_date - last_start).days + 1

    # Calculate average cycle length
    if len(period_starts) >= 2:
        lengths = [
            (period_starts[i] - period_starts[i + 1]).days
            for i in range(len(period_starts) - 1)
        ]
        avg_length = round(sum(lengths) / len(lengths))
    else:
        avg_length = 28

    # Check for ovulation data
    ov_rows = await _supabase_get(
        "cycle_logs",
        f"user_id=eq.{user_id}&event_type=eq.ovulation"
        f"&event_date=gte.{last_start.isoformat()}"
        f"&event_date=lte.{target_date.isoformat()}"
        f"&limit=1",
    )
    ov_day = None
    if ov_rows:
        ov_date = date.fromisoformat(ov_rows[0]["event_date"])
        ov_day = (ov_date - last_start).days + 1

    phase = _estimate_phase(cycle_day, avg_length, ov_day)
    confidence = _phase_confidence(len(period_starts) - 1, ov_day is not None)
    days_until = max(0, avg_length - cycle_day) if avg_length else None

    return CyclePhase(
        phase=phase,
        cycle_day=cycle_day,
        days_until_next_period=days_until,
        confidence=confidence,
    )


def normalize_metric_by_phase(
    baseline_phase: str,
    current_phase: str,
    metric: str,
    delta_pct: float,
) -> Dict[str, Any]:
    """
    Adjust metric delta based on expected cycle-phase differences.
    Returns adjusted delta and a flag indicating if normalization was applied.
    """
    # Known phase-dependent metric adjustments (population averages)
    # HRV: typically 5-10% lower in luteal vs follicular
    # RHR: typically 1-3 bpm higher in luteal
    # Sleep: typically 3-5% lower efficiency in luteal
    # Weight: 1-3 lbs water retention in luteal
    PHASE_ADJUSTMENTS = {
        ("follicular", "luteal"): {
            "hrv_balance": -7,  # HRV drops ~7% follicular→luteal
            "resting_heart_rate": 3,  # RHR rises ~3% follicular→luteal
            "sleep_efficiency": -4,  # sleep efficiency drops ~4%
            "sleep_score": -5,
            "weight": 1.5,  # ~1.5% water retention
        },
        ("luteal", "follicular"): {
            "hrv_balance": 7,
            "resting_heart_rate": -3,
            "sleep_efficiency": 4,
            "sleep_score": 5,
            "weight": -1.5,
        },
    }

    key = (baseline_phase, current_phase)
    adjustments = PHASE_ADJUSTMENTS.get(key, {})
    adjustment = adjustments.get(metric, 0)

    if adjustment != 0:
        adjusted_delta = delta_pct - adjustment
        return {
            "original_delta": delta_pct,
            "adjusted_delta": round(adjusted_delta, 1),
            "phase_adjustment": adjustment,
            "normalized": True,
            "note": f"Adjusted {adjustment:+.0f}% for {baseline_phase}→{current_phase} phase difference",
        }

    return {
        "original_delta": delta_pct,
        "adjusted_delta": delta_pct,
        "phase_adjustment": 0,
        "normalized": False,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/log", response_model=CycleLogEntry, status_code=201)
async def log_cycle_event(
    body: CycleLogRequest,
    current_user: dict = Depends(get_current_user),
):
    """Log a cycle event (period start/end, ovulation, symptom)."""
    user_id = current_user["id"]

    if body.event_type not in ("period_start", "period_end", "ovulation", "symptom"):
        raise HTTPException(status_code=400, detail="Invalid event_type")

    row = await _supabase_upsert(
        "cycle_logs",
        {
            "user_id": user_id,
            "event_type": body.event_type,
            "event_date": body.event_date,
            "flow_intensity": body.flow_intensity,
            "symptoms": body.symptoms,
            "notes": body.notes,
        },
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to log cycle event")

    return CycleLogEntry(
        id=row["id"],
        event_type=row["event_type"],
        event_date=row["event_date"],
        flow_intensity=row.get("flow_intensity"),
        symptoms=row.get("symptoms") or [],
        notes=row.get("notes"),
        created_at=row["created_at"],
    )


@router.delete("/log/{event_date}/{event_type}", status_code=204)
async def delete_cycle_event(
    event_date: str,
    event_type: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a specific cycle event."""
    user_id = current_user["id"]
    await _supabase_delete(
        "cycle_logs",
        f"user_id=eq.{user_id}&event_date=eq.{event_date}&event_type=eq.{event_type}",
    )


@router.get("/current", response_model=CycleInfo)
async def get_current_cycle(
    current_user: dict = Depends(get_current_user),
):
    """Get current cycle day, phase, and average cycle length."""
    user_id = current_user["id"]
    today = date.today()

    phase = await get_cycle_phase_for_date(user_id, today)

    # Count tracked cycles
    all_starts = await _supabase_get(
        "cycle_logs",
        f"user_id=eq.{user_id}&event_type=eq.period_start&order=event_date.desc&limit=12",
    )
    starts = [date.fromisoformat(r["event_date"]) for r in (all_starts or [])]
    cycles_tracked = max(0, len(starts) - 1)

    avg_length = None
    is_regular = None
    if len(starts) >= 2:
        lengths = [(starts[i] - starts[i + 1]).days for i in range(len(starts) - 1)]
        avg_length = round(sum(lengths) / len(lengths))
        if len(lengths) >= 3:
            is_regular = (max(lengths) - min(lengths)) <= 7

    return CycleInfo(
        current_phase=phase or CyclePhase(phase="unknown"),
        avg_cycle_length=avg_length,
        last_period_start=starts[0].isoformat() if starts else None,
        cycles_tracked=cycles_tracked,
        is_regular=is_regular,
    )


@router.get("/history", response_model=CycleHistory)
async def get_cycle_history(
    current_user: dict = Depends(get_current_user),
):
    """Get last 6 cycles with lengths and phase estimates."""
    user_id = current_user["id"]

    starts_rows = await _supabase_get(
        "cycle_logs",
        f"user_id=eq.{user_id}&event_type=eq.period_start&order=event_date.desc&limit=7",
    )
    starts = [date.fromisoformat(r["event_date"]) for r in (starts_rows or [])]

    if len(starts) < 2:
        return CycleHistory(
            cycles=[], avg_length=None, shortest=None, longest=None, is_regular=None
        )

    # Get ovulation dates
    ov_rows = await _supabase_get(
        "cycle_logs",
        f"user_id=eq.{user_id}&event_type=eq.ovulation&order=event_date.desc&limit=12",
    )
    ov_dates = {date.fromisoformat(r["event_date"]) for r in (ov_rows or [])}

    cycles = []
    lengths = []
    for i in range(len(starts) - 1):
        start = starts[i]
        prev_start = starts[i + 1] if i + 1 < len(starts) else None
        length = (start - starts[i + 1]).days if i + 1 < len(starts) else None

        # Find ovulation in this cycle
        ov_in_cycle = None
        if prev_start:
            for ov in ov_dates:
                if prev_start <= ov < start:
                    ov_in_cycle = ov.isoformat()
                    break

        if length and length > 0:
            lengths.append(length)

        cycles.append(
            CycleHistoryEntry(
                cycle_number=i + 1,
                start_date=starts[i + 1].isoformat(),
                end_date=(start - timedelta(days=1)).isoformat(),
                length_days=length,
                ovulation_date=ov_in_cycle,
            )
        )

    avg = round(sum(lengths) / len(lengths)) if lengths else None
    is_regular = (max(lengths) - min(lengths)) <= 7 if len(lengths) >= 3 else None

    return CycleHistory(
        cycles=cycles,
        avg_length=avg,
        shortest=min(lengths) if lengths else None,
        longest=max(lengths) if lengths else None,
        is_regular=is_regular,
    )


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_cycle_recommendations(
    current_user: dict = Depends(get_current_user),
):
    """
    Get cycle-phase-aware recommendations for experiments.
    Returns guidance on what types of experiments are appropriate for the current phase.
    """
    user_id = current_user["id"]
    today = date.today()
    phase_info = await get_cycle_phase_for_date(user_id, today)

    if not phase_info or phase_info.phase == "unknown":
        return {
            "phase": "unknown",
            "recommendation": "Start logging your cycle to get phase-aware experiment recommendations.",
            "experiment_guidance": None,
        }

    PHASE_GUIDANCE = {
        "menstrual": {
            "best_for": ["rest", "gentle_movement", "anti_inflammatory_foods"],
            "avoid": ["starting_new_experiments", "high_intensity_exercise"],
            "note": "Energy is typically lower. Focus on recovery, not new experiments. If you have heavy flow, watch iron levels.",
        },
        "follicular": {
            "best_for": ["diet_experiments", "exercise_experiments", "new_habits"],
            "avoid": [],
            "note": "Peak insulin sensitivity and energy. Best time to start diet or exercise experiments — your body is most responsive.",
        },
        "ovulation": {
            "best_for": ["peak_performance_testing", "social_experiments"],
            "avoid": ["using_as_baseline_day"],
            "note": "Peak energy and performance. Good for testing limits, but not representative for baseline measurements.",
        },
        "luteal": {
            "best_for": ["stress_management", "sleep_experiments", "comfort_foods"],
            "avoid": ["starting_weight_experiments", "comparing_to_follicular"],
            "note": "HRV and sleep quality typically dip. Water retention affects weight. Don't start weight-tracking experiments now — results will be confounded.",
        },
    }

    guidance: Dict[str, Any] = PHASE_GUIDANCE.get(phase_info.phase, {})  # type: ignore[assignment]

    return {
        "phase": phase_info.phase,
        "cycle_day": phase_info.cycle_day,
        "confidence": phase_info.confidence,
        "recommendation": guidance.get("note", ""),
        "experiment_guidance": {
            "best_for": guidance.get("best_for", []),
            "avoid": guidance.get("avoid", []),
        },
    }
