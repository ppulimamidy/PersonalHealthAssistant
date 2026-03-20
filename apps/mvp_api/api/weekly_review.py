"""
Weekly Review API — week-over-week health summary.

Computes deltas for health score, sleep, adherence, symptoms, and experiments
comparing current week to previous week.
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()


def _week_bounds(ref: date):
    """Return (monday, sunday) for the week containing `ref`."""
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


async def _avg_health_score(user_id: str, start: str, end: str) -> Optional[float]:
    """Average health score from health_metric_summaries in date range."""
    rows = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&date=gte.{start}&date=lte.{end}"
        f"&select=metric_type,score",
    )
    scores = [r["score"] for r in rows if r.get("score") is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


async def _avg_sleep_score(user_id: str, start: str, end: str) -> Optional[float]:
    """Average sleep score from timeline data."""
    rows = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&date=gte.{start}&date=lte.{end}"
        f"&metric_type=eq.sleep&select=score",
    )
    scores = [r["score"] for r in rows if r.get("score") is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


async def _adherence_pct(user_id: str, start_dt: str, end_dt: str) -> Optional[float]:
    """Adherence percentage in date range."""
    logs = await _supabase_get(
        "medication_adherence_log",
        f"user_id=eq.{user_id}&scheduled_time=gte.{start_dt}&scheduled_time=lte.{end_dt}"
        f"&select=was_taken",
    )
    if not logs:
        return None
    taken = sum(1 for l in logs if l.get("was_taken"))
    return round((taken / len(logs)) * 100, 1)


async def _symptom_count(user_id: str, start: str, end: str) -> int:
    """Count symptom journal entries in date range."""
    rows = await _supabase_get(
        "symptom_journal",
        f"user_id=eq.{user_id}&symptom_date=gte.{start}&symptom_date=lte.{end}"
        f"&select=id",
    )
    return len(rows)


async def _experiments_completed(user_id: str, start: str, end: str) -> int:
    """Count experiments completed in date range."""
    rows = await _supabase_get(
        "active_interventions",
        f"user_id=eq.{user_id}&status=eq.completed" f"&select=id,updated_at",
    )
    # Filter by completion date falling in range
    count = 0
    for r in rows:
        updated = (r.get("updated_at") or "")[:10]
        if start <= updated <= end:
            count += 1
    return count


def _build_summary(metrics: dict, experiments: int) -> str:
    """Generate a human-readable summary sentence."""
    parts = []

    sleep = metrics.get("sleep_avg")
    if sleep and sleep.get("delta"):
        d = sleep["delta"]
        direction = "improved" if d > 0 else "dipped"
        parts.append(f"Sleep {direction} {abs(round(d))}%")

    adherence = metrics.get("adherence_pct")
    if adherence and adherence.get("current") is not None:
        parts.append(f"Med adherence at {round(adherence['current'])}%")

    symptoms = metrics.get("symptom_count")
    if symptoms and symptoms.get("delta") and symptoms["delta"] < 0:
        parts.append(f"{abs(symptoms['delta'])} fewer symptoms")
    elif symptoms and symptoms.get("delta") and symptoms["delta"] > 0:
        parts.append(f"{symptoms['delta']} more symptoms")

    if experiments > 0:
        parts.append(
            f"Completed {experiments} experiment{'s' if experiments > 1 else ''}"
        )

    return (
        ". ".join(parts) + "."
        if parts
        else "Keep logging to build your weekly picture."
    )


@router.get("/weekly-review")
async def get_weekly_review(
    current_user: dict = Depends(get_current_user),
):
    """
    Week-over-week health summary.

    Compares current week (Mon–today) with previous full week.
    Returns summary text, metric deltas, top achievement, and watch area.
    """
    user_id = current_user["id"]
    today = date.today()

    # Current week: Monday → today
    curr_start, _ = _week_bounds(today)
    curr_end = today

    # Previous week: full Mon–Sun
    prev_end = curr_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6)

    cs, ce = curr_start.isoformat(), curr_end.isoformat()
    ps, pe = prev_start.isoformat(), prev_end.isoformat()
    cs_dt, ce_dt = f"{cs}T00:00:00", f"{ce}T23:59:59"
    ps_dt, pe_dt = f"{ps}T00:00:00", f"{pe}T23:59:59"

    # Fetch all metrics in parallel (import asyncio at top would be cleaner but
    # keeping it simple)
    import asyncio

    (
        curr_sleep,
        prev_sleep,
        curr_adherence,
        prev_adherence,
        curr_symptoms,
        prev_symptoms,
        experiments,
    ) = await asyncio.gather(
        _avg_sleep_score(user_id, cs, ce),
        _avg_sleep_score(user_id, ps, pe),
        _adherence_pct(user_id, cs_dt, ce_dt),
        _adherence_pct(user_id, ps_dt, pe_dt),
        _symptom_count(user_id, cs, ce),
        _symptom_count(user_id, ps, pe),
        _experiments_completed(user_id, cs, ce),
    )

    metrics: Dict[str, Any] = {}

    if curr_sleep is not None:
        metrics["sleep_avg"] = {
            "current": curr_sleep,
            "previous": prev_sleep or 0,
            "delta": round(curr_sleep - (prev_sleep or curr_sleep), 1),
        }

    if curr_adherence is not None:
        metrics["adherence_pct"] = {
            "current": curr_adherence,
            "previous": prev_adherence or 0,
            "delta": round(curr_adherence - (prev_adherence or curr_adherence), 1),
        }

    _curr_sym = int(curr_symptoms or 0)
    _prev_sym = int(prev_symptoms or 0)
    metrics["symptom_count"] = {
        "current": _curr_sym,
        "previous": _prev_sym,
        "delta": _curr_sym - _prev_sym,
    }

    summary = _build_summary(metrics, int(experiments or 0))

    # Determine top achievement and watch area
    top_achievement = None
    watch_area = None

    best_delta = 0
    worst_delta = 0
    for key, m in metrics.items():
        d = m.get("delta", 0)
        label = key.replace("_", " ").title()
        # For symptoms, negative delta is good
        effective = -d if key == "symptom_count" else d
        if effective > best_delta:
            best_delta = effective
            if key == "symptom_count":
                top_achievement = f"{abs(d)} fewer symptoms than last week"
            else:
                top_achievement = f"{label} up {abs(round(d))} points"
        if effective < worst_delta:
            worst_delta = effective
            if key == "symptom_count":
                watch_area = f"{d} more symptoms than last week"
            else:
                watch_area = f"{label} down {abs(round(d))} points"

    return {
        "week_start": cs,
        "summary": summary,
        "metrics": metrics,
        "experiments_completed": experiments,
        "top_achievement": top_achievement,
        "watch_area": watch_area,
    }
