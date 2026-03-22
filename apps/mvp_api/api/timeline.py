"""
Health Timeline API
Endpoints for viewing combined health data over time.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from apps.device_data.services.oura_client import OuraAPIClient
from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get, SUPABASE_URL, SUPABASE_SERVICE_KEY

# Pydantic models are intentionally simple containers.
# pylint: disable=too-few-public-methods,too-many-locals,broad-except,no-member

logger = get_logger(__name__)

router = APIRouter()

# Sandbox mode - uses mock data, no real API calls
USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")


# Helper function for optional auth in sandbox mode
async def get_user_optional(request: Request) -> dict:
    """Get current user, or return a sandbox user if not authenticated and in sandbox mode"""
    if USE_SANDBOX:
        try:
            return await get_current_user(request)
        except HTTPException:
            # In sandbox mode, if auth fails, return a mock user
            return {
                "id": "sandbox-user-123",
                "email": "sandbox@example.com",
                "user_type": "sandbox",
            }
    else:
        # In production, require authentication
        return await get_current_user(request)


class SleepData(BaseModel):
    """Sleep metrics for a given day (durations in seconds)."""

    id: str
    date: str
    # Durations are in SECONDS (matches Oura API + frontend formatDuration())
    total_sleep_duration: int
    deep_sleep_duration: int
    rem_sleep_duration: int
    light_sleep_duration: int
    sleep_efficiency: int
    sleep_score: int
    bedtime_start: Optional[str] = None
    bedtime_end: Optional[str] = None


class ActivityData(BaseModel):
    """Activity metrics for a given day."""

    id: str
    date: str
    steps: int
    active_calories: int
    total_calories: int
    activity_score: int
    high_activity_time: int
    medium_activity_time: int
    low_activity_time: int
    sedentary_time: int


class ReadinessData(BaseModel):
    """Readiness metrics for a given day."""

    id: str
    date: str
    readiness_score: int
    temperature_deviation: float
    hrv_balance: int
    recovery_index: int
    resting_heart_rate: int


class AltMetrics(BaseModel):
    """Values from the non-primary source for the same day — shown alongside
    the primary so the user can compare sources or validate accuracy."""

    source: str  # e.g. "healthkit", "oura"
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None  # total sleep in hours
    resting_heart_rate: Optional[int] = None  # bpm
    hrv_ms: Optional[float] = None  # SDNN in ms


class NativeMetrics(BaseModel):
    """Extended metrics from Apple Health, Health Connect, or any Tier 1/2 wearable."""

    respiratory_rate: Optional[float] = None  # breaths/min
    spo2: Optional[float] = None  # %
    active_calories: Optional[int] = None  # kcal
    workout_minutes: Optional[int] = None  # total workout duration minutes
    workout_sessions: Optional[int] = None  # number of workout sessions
    workout_types: Optional[List[str]] = None  # e.g. ["yoga", "running"]
    vo2_max: Optional[float] = None  # mL/kg/min


class TimelineEntry(BaseModel):
    """Combined daily metrics across sleep/activity/readiness."""

    date: str
    sleep: Optional[SleepData] = None
    activity: Optional[ActivityData] = None
    readiness: Optional[ReadinessData] = None
    sources: List[str] = []  # all sources that contributed data this day
    alt_metrics: Optional[AltMetrics] = None  # secondary-source values for comparison
    native: Optional[NativeMetrics] = None  # extended native wearable metrics


@router.get("/timeline", response_model=List[TimelineEntry])
async def get_timeline(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to include"),
    since_timestamp: Optional[str] = Query(
        default=None,
        description="ISO 8601 timestamp — return only entries on or after this date "
        "(narrows the fetch window; more recent than days-based start wins)",
    ),
    source_priority: str = Query(
        default="oura",
        description=(
            "Which source to use as primary when both have data for the same metric. "
            "'oura' = prefer Oura (default). "
            "'healthkit'/'health_connect' = prefer Apple/Google Health. "
            "'auto' = per-metric heuristic: Apple Health for steps, Oura for sleep/HRV/readiness."
        ),
    ),
    current_user: dict = Depends(get_user_optional),
):
    """
    Get combined health timeline data.
    Returns sleep, activity, and readiness data for each day.
    """
    access_token = os.environ.get("OURA_ACCESS_TOKEN", "")
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Gate: return empty for users with no real device data (avoid sandbox mock data)
    _uid = current_user.get("id", "")
    if USE_SANDBOX and _uid and _uid != "sandbox-user-123":
        from ..dependencies.usage_gate import _supabase_get

        _has_data = await _supabase_get(
            "oura_connections",
            f"user_id=eq.{_uid}&is_active=eq.true&limit=1&select=id",
        )
        if not _has_data:
            _has_data = await _supabase_get(
                "native_health_data",
                f"user_id=eq.{_uid}&limit=1&select=id",
            )
        if not _has_data:
            _has_data = await _supabase_get(
                "health_metrics_normalized",
                f"user_id=eq.{_uid}&limit=1&select=id",
            )
        if not _has_data:
            return []

    # Narrow the fetch window when since_timestamp is provided
    # Guard against FastAPI Query objects being passed when called programmatically
    if since_timestamp and isinstance(since_timestamp, str):
        try:
            parsed = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))
            parsed_naive = parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
            if parsed_naive > start_date:
                start_date = parsed_naive
        except ValueError:
            pass  # Invalid format — fall back to days-based range

    try:
        async with OuraAPIClient(
            access_token=access_token if not USE_SANDBOX else None,
            use_sandbox=USE_SANDBOX or not access_token,
            user_id=current_user["id"],
        ) as client:
            # Fetch all data types
            all_data = await client.get_all_data(start_date, end_date)

            # Process and combine data by date
            timeline = {}

            # Process sleep data
            for sleep_entry in all_data.get("daily_sleep", {}).get("data", []):
                date = sleep_entry.get("day", "")[:10]
                if date not in timeline:
                    timeline[date] = {"date": date}

                # Extract nested sleep data
                sleep = sleep_entry.get(
                    "sleep", sleep_entry
                )  # Support both nested and flat structures

                timeline[date]["sleep"] = SleepData(
                    id=sleep_entry.get("id", f"sleep_{date}"),
                    date=date,
                    # Oura provides sleep durations in seconds; keep seconds throughout.
                    total_sleep_duration=int(sleep.get("total_sleep_duration", 0)),
                    deep_sleep_duration=int(sleep.get("deep_sleep_duration", 0)),
                    rem_sleep_duration=int(sleep.get("rem_sleep_duration", 0)),
                    light_sleep_duration=int(sleep.get("light_sleep_duration", 0)),
                    sleep_efficiency=int(sleep.get("sleep_efficiency", 0)),
                    sleep_score=int(sleep.get("sleep_score", 0)),
                    bedtime_start=sleep.get("bedtime_start"),
                    bedtime_end=sleep.get("bedtime_end"),
                )

            # Process activity data
            for activity_entry in all_data.get("daily_activity", {}).get("data", []):
                date = activity_entry.get("day", "")[:10]
                if date not in timeline:
                    timeline[date] = {"date": date}

                # Extract nested activity data
                activity = activity_entry.get(
                    "activity", activity_entry
                )  # Support both nested and flat structures

                timeline[date]["activity"] = ActivityData(
                    id=activity_entry.get("id", f"activity_{date}"),
                    date=date,
                    steps=int(activity.get("steps", 0)),
                    active_calories=int(
                        activity.get(
                            "active_calories", activity.get("calories_active", 0)
                        )
                    ),
                    total_calories=int(
                        activity.get(
                            "total_calories", activity.get("calories_total", 0)
                        )
                    ),
                    activity_score=int(activity.get("score", 0)),
                    high_activity_time=int(
                        activity.get(
                            "high_activity_time", activity.get("met_min_high", 0)
                        )
                    ),
                    medium_activity_time=int(
                        activity.get(
                            "medium_activity_time", activity.get("met_min_medium", 0)
                        )
                    ),
                    low_activity_time=int(
                        activity.get(
                            "low_activity_time", activity.get("met_min_low", 0)
                        )
                    ),
                    sedentary_time=int(
                        activity.get(
                            "sedentary_time", activity.get("met_min_inactive", 0)
                        )
                    ),
                )

            # Process readiness data
            for readiness_entry in all_data.get("daily_readiness", {}).get("data", []):
                date = readiness_entry.get("day", "")[:10]
                if date not in timeline:
                    timeline[date] = {"date": date}

                # Extract nested readiness data
                readiness = readiness_entry.get(
                    "readiness", readiness_entry
                )  # Support both nested and flat structures

                timeline[date]["readiness"] = ReadinessData(
                    id=readiness_entry.get("id", f"readiness_{date}"),
                    date=date,
                    readiness_score=int(readiness.get("score", 0)),
                    temperature_deviation=float(
                        readiness.get("temperature_deviation", 0.0)
                    ),
                    hrv_balance=int(readiness.get("hrv_balance", 0)),
                    recovery_index=int(readiness.get("score_recovery_index", 0)),
                    resting_heart_rate=int(readiness.get("resting_hr", 0)),
                )

            # Tag Oura entries with their source
            for entry in timeline.values():
                entry.setdefault("sources", ["oura"])

            # ── Fetch native_health_data (Apple Health / Health Connect) ──────
            # Collect BOTH sources, then apply source_priority to decide which
            # is "primary" and which is stored in alt_metrics for comparison.
            nhd_by_date: dict = {}
            if SUPABASE_URL and SUPABASE_SERVICE_KEY:
                user_id = current_user.get("id", "")
                start_str = start_date.date().isoformat()
                end_str = end_date.date().isoformat()
                try:
                    nhd_rows = await _supabase_get(
                        "native_health_data",
                        f"user_id=eq.{user_id}"
                        f"&date=gte.{start_str}&date=lte.{end_str}"
                        f"&order=date.desc",
                    )
                    for row in nhd_rows:
                        d = row.get("date", "")[:10]
                        nhd_by_date.setdefault(d, {})
                        nhd_by_date[d][row["metric_type"]] = {
                            "value_json": row.get("value_json", {}),
                            "source": row.get("source", "healthkit"),
                        }
                except Exception as nhd_exc:  # pylint: disable=broad-except
                    logger.warning("native_health_data fetch failed: %s", nhd_exc)

            # ── "auto" heuristic: Apple Health wins for steps (step counting
            # from a wrist-worn device is generally more accurate than a ring),
            # Oura wins for sleep staging and readiness (richer sensor suite).
            def _native_preferred(metric: str) -> bool:
                if source_priority in ("healthkit", "health_connect"):
                    return True
                if source_priority == "auto" and metric == "steps":
                    return True
                return False  # "oura" default

            for date, metrics in nhd_by_date.items():
                if date not in timeline:
                    timeline[date] = {"date": date, "sources": []}

                entry = timeline[date]
                nhd_source = next((v["source"] for v in metrics.values()), "healthkit")
                if nhd_source not in entry["sources"]:
                    entry["sources"].append(nhd_source)

                # ── Steps ────────────────────────────────────────────────────
                nhd_steps = (
                    int(metrics["steps"]["value_json"].get("steps", 0))
                    if "steps" in metrics
                    else None
                )
                oura_steps = entry.get("activity", {})
                if hasattr(oura_steps, "steps"):
                    oura_steps_val: Optional[int] = oura_steps.steps
                else:
                    oura_steps_val = None

                if nhd_steps is not None:
                    if "activity" not in entry:
                        # No Oura data — use native
                        entry["activity"] = ActivityData(
                            id=f"nhd_activity_{date}",
                            date=date,
                            steps=nhd_steps,
                            active_calories=0,
                            total_calories=0,
                            activity_score=0,
                            high_activity_time=0,
                            medium_activity_time=0,
                            low_activity_time=0,
                            sedentary_time=0,
                        )
                    elif _native_preferred("steps") and oura_steps_val is not None:
                        # Override Oura steps with native; keep alt for comparison
                        entry["activity"] = ActivityData(
                            id=entry["activity"].id,
                            date=date,
                            steps=nhd_steps,
                            active_calories=entry["activity"].active_calories,
                            total_calories=entry["activity"].total_calories,
                            activity_score=entry["activity"].activity_score,
                            high_activity_time=entry["activity"].high_activity_time,
                            medium_activity_time=entry["activity"].medium_activity_time,
                            low_activity_time=entry["activity"].low_activity_time,
                            sedentary_time=entry["activity"].sedentary_time,
                        )
                        alt = entry.setdefault("alt_metrics", {})
                        alt["source"] = "oura"
                        alt["steps"] = oura_steps_val
                    elif oura_steps_val is not None:
                        # Oura is primary; store native as alt
                        alt = entry.setdefault("alt_metrics", {})
                        alt["source"] = nhd_source
                        alt["steps"] = nhd_steps

                # ── Sleep ────────────────────────────────────────────────────
                if "sleep" in metrics:
                    vj = metrics["sleep"]["value_json"]
                    nhd_sleep_hrs = float(vj.get("hours", 0))
                    if "sleep" not in entry:
                        entry["sleep"] = SleepData(
                            id=f"nhd_sleep_{date}",
                            date=date,
                            total_sleep_duration=int(nhd_sleep_hrs * 3600),
                            deep_sleep_duration=0,
                            rem_sleep_duration=0,
                            light_sleep_duration=0,
                            sleep_efficiency=0,
                            sleep_score=0,
                        )
                    elif _native_preferred("sleep"):
                        # Swap — native becomes primary, Oura goes to alt
                        oura_hrs = entry["sleep"].total_sleep_duration / 3600
                        entry["sleep"] = SleepData(
                            id=entry["sleep"].id,
                            date=date,
                            total_sleep_duration=int(nhd_sleep_hrs * 3600),
                            deep_sleep_duration=0,
                            rem_sleep_duration=0,
                            light_sleep_duration=0,
                            sleep_efficiency=0,
                            sleep_score=0,
                        )
                        alt = entry.setdefault("alt_metrics", {})
                        alt["source"] = "oura"
                        alt["sleep_hours"] = round(oura_hrs, 1)
                    else:
                        # Oura primary; store native duration as alt
                        alt = entry.setdefault("alt_metrics", {})
                        alt["source"] = nhd_source
                        alt["sleep_hours"] = round(nhd_sleep_hrs, 1)

                # ── Resting HR + HRV ─────────────────────────────────────────
                hr_vj = metrics.get("resting_heart_rate", {}).get("value_json", {})
                hrv_vj = metrics.get("hrv_sdnn", {}).get("value_json", {})
                nhd_hr = int(hr_vj.get("bpm", 0)) if hr_vj else None
                nhd_hrv = float(hrv_vj.get("ms", 0)) if hrv_vj else None

                if nhd_hr or nhd_hrv:
                    if "readiness" not in entry:
                        entry["readiness"] = ReadinessData(
                            id=f"nhd_readiness_{date}",
                            date=date,
                            readiness_score=0,
                            temperature_deviation=0.0,
                            hrv_balance=int(nhd_hrv or 0),
                            recovery_index=0,
                            resting_heart_rate=int(nhd_hr or 0),
                        )
                    elif _native_preferred("hrv"):
                        # Swap HR/HRV to native; keep Oura values as alt
                        alt = entry.setdefault("alt_metrics", {})
                        alt["source"] = "oura"
                        alt["resting_heart_rate"] = entry[
                            "readiness"
                        ].resting_heart_rate
                        alt["hrv_ms"] = float(entry["readiness"].hrv_balance)
                        entry["readiness"] = ReadinessData(
                            id=entry["readiness"].id,
                            date=date,
                            readiness_score=entry["readiness"].readiness_score,
                            temperature_deviation=entry[
                                "readiness"
                            ].temperature_deviation,
                            hrv_balance=int(nhd_hrv or 0),
                            recovery_index=entry["readiness"].recovery_index,
                            resting_heart_rate=int(nhd_hr or 0),
                        )
                    else:
                        alt = entry.setdefault("alt_metrics", {})
                        alt["source"] = nhd_source
                        if nhd_hr:
                            alt["resting_heart_rate"] = nhd_hr
                        if nhd_hrv:
                            alt["hrv_ms"] = nhd_hrv

                # ── Extended native metrics (respiratory, SpO2, calories, workout, VO2) ──
                native = entry.setdefault("native", {})

                if "respiratory_rate" in metrics:
                    vj = metrics["respiratory_rate"]["value_json"]
                    rate = vj.get("rate")
                    if rate is not None:
                        native["respiratory_rate"] = float(rate)

                if "spo2" in metrics:
                    vj = metrics["spo2"]["value_json"]
                    pct = vj.get("pct")
                    if pct is not None:
                        native["spo2"] = float(pct)

                if "active_calories" in metrics:
                    vj = metrics["active_calories"]["value_json"]
                    kcal = vj.get("kcal")
                    if kcal is not None:
                        native["active_calories"] = int(kcal)
                        # Also surface to ActivityData if no Oura active_calories
                        if (
                            "activity" in entry
                            and entry["activity"].active_calories == 0
                        ):
                            act = entry["activity"]
                            entry["activity"] = ActivityData(
                                id=act.id,
                                date=act.date,
                                steps=act.steps,
                                active_calories=int(kcal),
                                total_calories=act.total_calories,
                                activity_score=act.activity_score,
                                high_activity_time=act.high_activity_time,
                                medium_activity_time=act.medium_activity_time,
                                low_activity_time=act.low_activity_time,
                                sedentary_time=act.sedentary_time,
                            )

                if "workout" in metrics:
                    vj = metrics["workout"]["value_json"]
                    mins = vj.get("minutes")
                    if mins is not None:
                        native["workout_minutes"] = int(mins)
                        native["workout_sessions"] = int(vj.get("sessions", 1))
                        native["workout_types"] = vj.get("types", [])

                if "vo2_max" in metrics:
                    vj = metrics["vo2_max"]["value_json"]
                    ml = vj.get("ml_kg_min")
                    if ml is not None:
                        native["vo2_max"] = float(ml)

            # Promote alt_metrics and native dicts to model objects
            for entry in timeline.values():
                if "alt_metrics" in entry and isinstance(entry["alt_metrics"], dict):
                    entry["alt_metrics"] = AltMetrics(**entry["alt_metrics"])
                if (
                    "native" in entry
                    and isinstance(entry["native"], dict)
                    and entry["native"]
                ):
                    entry["native"] = NativeMetrics(**entry["native"])

            # Sort by date descending
            sorted_entries = sorted(
                [TimelineEntry(**entry) for entry in timeline.values()],
                key=lambda x: x.date,
                reverse=True,
            )

            return sorted_entries

    except Exception as exc:
        logger.error(f"Failed to fetch timeline: {exc}")
        # Return empty timeline on error
        return []


@router.get("/summary")
async def get_health_summary(
    days: int = Query(default=7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a summary of health metrics over a period.
    """
    timeline = await get_timeline(days=days, current_user=current_user)

    if not timeline:
        return {
            "period_days": days,
            "data_available": False,
        }

    # Calculate averages
    sleep_scores = [e.sleep.sleep_score for e in timeline if e.sleep]
    activity_scores = [e.activity.activity_score for e in timeline if e.activity]
    readiness_scores = [e.readiness.readiness_score for e in timeline if e.readiness]
    steps = [e.activity.steps for e in timeline if e.activity]

    return {
        "period_days": days,
        "data_available": True,
        "entries_count": len(timeline),
        "averages": {
            "sleep_score": sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0,
            "activity_score": sum(activity_scores) / len(activity_scores)
            if activity_scores
            else 0,
            "readiness_score": sum(readiness_scores) / len(readiness_scores)
            if readiness_scores
            else 0,
            "daily_steps": sum(steps) / len(steps) if steps else 0,
        },
        "best_day": {
            "sleep": max(
                timeline, key=lambda x: x.sleep.sleep_score if x.sleep else 0
            ).date
            if sleep_scores
            else None,
            "activity": max(
                timeline, key=lambda x: x.activity.activity_score if x.activity else 0
            ).date
            if activity_scores
            else None,
            "readiness": max(
                timeline,
                key=lambda x: x.readiness.readiness_score if x.readiness else 0,
            ).date
            if readiness_scores
            else None,
        },
    }
