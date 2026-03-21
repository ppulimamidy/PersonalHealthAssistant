"""
Timeline Actions API — aggregates user actions (meals, symptoms, meds,
experiments, journey events) grouped by date for timeline overlay.

Designed to be called alongside the health timeline so each DayCard
can show *what the user did* next to *what their body measured*.
"""

import asyncio
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Internal fetchers — each returns raw rows from Supabase
# ---------------------------------------------------------------------------


async def _fetch_symptoms(user_id: str, start_date: str) -> list:
    """Symptom journal entries in date range."""
    return await _supabase_get(
        "symptom_journal",
        f"user_id=eq.{user_id}&symptom_date=gte.{start_date}"
        f"&select=symptom_date,symptom_type,severity,mood,stress_level"
        f"&order=symptom_date.desc,symptom_time.desc",
    )


async def _fetch_adherence(user_id: str, start_dt: str) -> tuple:
    """Active medications + adherence logs in date range."""
    meds_coro = _supabase_get(
        "medications",
        f"user_id=eq.{user_id}&is_active=eq.true" f"&select=id,medication_name",
    )
    logs_coro = _supabase_get(
        "medication_adherence_log",
        f"user_id=eq.{user_id}&scheduled_time=gte.{start_dt}"
        f"&select=medication_id,scheduled_time,was_taken"
        f"&limit=1000",
    )
    meds, logs = await asyncio.gather(meds_coro, logs_coro)
    return meds, logs


async def _fetch_interventions(user_id: str) -> tuple:
    """Active + recently completed interventions with checkins."""
    interventions = await _supabase_get(
        "active_interventions",
        f"user_id=eq.{user_id}&status=in.(active,completed)"
        f"&select=id,title,status,started_at,ends_at,duration_days"
        f"&order=created_at.desc&limit=10",
    )
    if not interventions:
        return [], []

    # Fetch all checkins for these interventions in one query
    intervention_ids = ",".join(f'"{i["id"]}"' for i in interventions)
    checkins = await _supabase_get(
        "intervention_checkins",
        f"intervention_id=in.({intervention_ids})"
        f"&select=intervention_id,checkin_date,adhered"
        f"&order=checkin_date.asc",
    )
    return interventions, checkins


async def _fetch_journeys(user_id: str) -> list:
    """Active journeys with phase data."""
    return await _supabase_get(
        "goal_journeys",
        f"user_id=eq.{user_id}&status=in.(active,completed)"
        f"&select=id,title,phases,current_phase,started_at"
        f"&order=created_at.desc&limit=5",
    )


# ---------------------------------------------------------------------------
# Grouping logic — organize raw data by date
# ---------------------------------------------------------------------------


def _group_symptoms(rows: list) -> Dict[str, list]:
    """Group symptom entries by date."""
    by_date: Dict[str, list] = defaultdict(list)
    for row in rows:
        d = row.get("symptom_date", "")[:10]
        if d:
            by_date[d].append(
                {
                    "type": row.get("symptom_type", "unknown"),
                    "severity": row.get("severity"),
                    "mood": row.get("mood"),
                    "stress_level": row.get("stress_level"),
                }
            )
    return dict(by_date)


def _group_adherence(meds: list, logs: list) -> Dict[str, dict]:
    """Group adherence logs by date, compute taken/total per day."""
    med_names = {m["id"]: m["medication_name"] for m in meds}
    by_date: Dict[str, dict] = defaultdict(
        lambda: {"taken": 0, "total": 0, "medications": []}
    )

    for log in logs:
        ts = log.get("scheduled_time", "")
        d = ts[:10] if ts else ""
        if not d:
            continue
        entry = by_date[d]
        entry["total"] += 1
        if log.get("was_taken"):
            entry["taken"] += 1
        med_name = med_names.get(log.get("medication_id", ""), "")
        if med_name and med_name not in entry["medications"]:
            entry["medications"].append(med_name)

    return dict(by_date)


def _group_experiments(interventions: list, checkins: list) -> Dict[str, list]:
    """Map experiment checkins to their dates + compute day number."""
    interv_map = {i["id"]: i for i in interventions}
    checkin_by_interv: Dict[str, list] = defaultdict(list)
    for c in checkins:
        checkin_by_interv[c["intervention_id"]].append(c)

    by_date: Dict[str, list] = defaultdict(list)

    for interv in interventions:
        iid = interv["id"]
        started = interv.get("started_at", "")[:10]
        title = interv.get("title", "Experiment")

        for c in checkin_by_interv.get(iid, []):
            d = c.get("checkin_date", "")[:10]
            if not d or not started:
                continue
            try:
                day_num = (date.fromisoformat(d) - date.fromisoformat(started)).days + 1
            except (ValueError, TypeError):
                day_num = None

            by_date[d].append(
                {
                    "title": title,
                    "day_number": day_num,
                    "adhered": c.get("adhered"),
                    "status": interv.get("status", "active"),
                }
            )

    return dict(by_date)


def _group_journey_events(journeys: list) -> Dict[str, list]:
    """Extract journey phase transition events by date."""
    by_date: Dict[str, list] = defaultdict(list)

    for j in journeys:
        title = j.get("title", "Journey")
        phases = j.get("phases") or []
        if isinstance(phases, str):
            import json

            try:
                phases = json.loads(phases)
            except (json.JSONDecodeError, TypeError):
                phases = []

        for i, phase in enumerate(phases):
            started = (phase.get("started_at") or "")[:10]
            if started:
                by_date[started].append(
                    {
                        "title": title,
                        "event": "phase_start",
                        "phase": phase.get("name", f"Phase {i + 1}"),
                        "phase_number": i + 1,
                    }
                )
            completed = (phase.get("completed_at") or "")[:10]
            if completed:
                by_date[completed].append(
                    {
                        "title": title,
                        "event": "phase_complete",
                        "phase": phase.get("name", f"Phase {i + 1}"),
                        "phase_number": i + 1,
                    }
                )

    return dict(by_date)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_timeline_actions(
    days: int = 7,
    current_user: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Aggregate user actions grouped by date.

    Called directly by the batch endpoint (no HTTP hop) and also
    exposed as a standalone GET for debugging / direct use.
    """
    user_id = (current_user or {})["id"]
    start_date = (date.today() - timedelta(days=days)).isoformat()
    start_dt = f"{start_date}T00:00:00"

    # Fetch all data sources in parallel
    (
        symptoms_raw,
        (meds, adherence_logs),
        (interventions, checkins),
        journeys_raw,
        medical_records_raw,
    ) = await asyncio.gather(
        _fetch_symptoms(user_id, start_date),
        _fetch_adherence(user_id, start_dt),
        _fetch_interventions(user_id),
        _fetch_journeys(user_id),
        _supabase_get(
            "medical_records",
            f"user_id=eq.{user_id}&order=created_at.desc&limit=20"
            f"&select=record_type,title,report_date,created_at",
        ),
    )

    # Group by date
    symptoms_by_date = _group_symptoms(symptoms_raw)
    adherence_by_date = _group_adherence(meds, adherence_logs)
    experiments_by_date = _group_experiments(interventions, checkins)
    journey_events_by_date = _group_journey_events(journeys_raw)

    # Group medical records by date
    records_by_date: Dict[str, list] = defaultdict(list)
    for rec in medical_records_raw:
        d = (rec.get("report_date") or rec.get("created_at", ""))[:10]
        if d:
            records_by_date[d].append(
                {
                    "type": rec.get("record_type", ""),
                    "title": rec.get("title", "Medical Record"),
                }
            )

    # Merge all dates
    all_dates: set[str] = set()
    all_dates.update(symptoms_by_date.keys())
    all_dates.update(adherence_by_date.keys())
    all_dates.update(experiments_by_date.keys())
    all_dates.update(journey_events_by_date.keys())
    all_dates.update(records_by_date.keys())

    result: Dict[str, Any] = {}
    for d in sorted(all_dates, reverse=True):
        entry: Dict[str, Any] = {}
        if d in symptoms_by_date:
            entry["symptoms"] = symptoms_by_date[d]
        if d in adherence_by_date:
            entry["adherence"] = adherence_by_date[d]
        if d in experiments_by_date:
            entry["experiments"] = experiments_by_date[d]
        if d in journey_events_by_date:
            entry["journey_events"] = journey_events_by_date[d]
        if d in records_by_date:
            entry["medical_records"] = records_by_date[d]
        if entry:
            result[d] = entry

    return result


@router.get("")
async def timeline_actions_endpoint(
    days: int = Query(default=7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """
    Get user actions (symptoms, meds, experiments, journeys) grouped by date.

    Designed to be overlaid on the health timeline so each day card
    shows both wearable metrics AND user actions.
    """
    return await get_timeline_actions(days=days, current_user=current_user)
