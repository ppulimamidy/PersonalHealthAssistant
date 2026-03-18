"""
Native Health Data Ingestion API

Receives batched HealthKit (iOS) and Health Connect (Android) data
from the mobile app and stores it in the native_health_data Supabase table.

Endpoint:
  POST /api/v1/health-data/ingest

The upsert key is (user_id, source, metric_type, date) — sending the same
date/metric again updates the existing row, so syncing is idempotent and
safe to retry.

Supabase table DDL (run once in Supabase SQL editor):

    -- Layer 1: Raw daily data (every data point, every day, every source)
    CREATE TABLE public.native_health_data (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        source TEXT NOT NULL,
        metric_type TEXT NOT NULL,
        date DATE NOT NULL,
        value_json JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    ALTER TABLE public.native_health_data
        ADD CONSTRAINT native_health_data_uq
        UNIQUE (user_id, source, metric_type, date);
    CREATE INDEX idx_nhd_user_metric_date
        ON public.native_health_data (user_id, metric_type, date DESC);
    ALTER TABLE public.native_health_data ENABLE ROW LEVEL SECURITY;
    CREATE POLICY "own health data" ON public.native_health_data
        FOR ALL USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);

    -- Layer 2: Pre-computed summaries (updated after each sync)
    -- One row per user per metric. AI agents query this for baselines,
    -- anomaly detection, and trend analysis.
    CREATE TABLE public.health_metric_summaries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        metric_type TEXT NOT NULL,
        -- Rolling averages
        avg_7d FLOAT,
        avg_30d FLOAT,
        avg_90d FLOAT,
        avg_180d FLOAT,
        avg_365d FLOAT,
        -- Min/Max for range context
        min_7d FLOAT,
        max_7d FLOAT,
        min_30d FLOAT,
        max_30d FLOAT,
        -- Latest reading
        latest_value FLOAT,
        latest_date DATE,
        -- Data coverage
        data_points_7d INT DEFAULT 0,
        data_points_30d INT DEFAULT 0,
        data_points_total INT DEFAULT 0,
        first_date DATE,
        -- Trend (comparing current window avg vs previous window avg)
        trend_7d TEXT CHECK (trend_7d IN ('up', 'down', 'stable')),
        trend_30d TEXT CHECK (trend_30d IN ('up', 'down', 'stable')),
        -- Personal baseline (long-term average for anomaly detection)
        personal_baseline FLOAT,
        baseline_stddev FLOAT,
        -- Anomaly flags (current reading vs personal baseline)
        is_anomalous BOOLEAN DEFAULT FALSE,
        anomaly_severity TEXT CHECK (anomaly_severity IN ('low', 'medium', 'high')),
        anomaly_detail TEXT,
        -- Timestamps
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(user_id, metric_type)
    );
    CREATE INDEX idx_hms_user ON public.health_metric_summaries (user_id);
    ALTER TABLE public.health_metric_summaries ENABLE ROW LEVEL SECURITY;
    CREATE POLICY "own summaries" ON public.health_metric_summaries
        FOR ALL USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id);

Supported sources (Tier 1–3):
    Tier 1 (Smartphones):  healthkit, health_connect
    Tier 2 (Wearables):    oura, whoop, garmin, fitbit, polar, samsung
    Tier 3 (Medical):      dexcom, blood_pressure, clinical
"""

import asyncio
import json
import math
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

import aiohttp
from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    _supabase_headers,
    _ssl_context,
)

logger = get_logger(__name__)
router = APIRouter()

_ON_CONFLICT = "user_id,source,metric_type,date"

# All supported data sources across tiers
VALID_SOURCES = {
    # Tier 1: Smartphones
    "healthkit",
    "health_connect",
    # Tier 2: Wearables
    "oura",
    "whoop",
    "garmin",
    "fitbit",
    "polar",
    "samsung",
    # Tier 3: Medical devices
    "dexcom",
    "blood_pressure",
    "clinical",
}

# Primary numeric key per metric type (for extracting values from JSONB)
_PRIMARY_KEY: Dict[str, str] = {
    "steps": "steps",
    "sleep": "hours",
    "resting_heart_rate": "bpm",
    "hrv_sdnn": "ms",
    "spo2": "pct",
    "respiratory_rate": "rate",
    "active_calories": "kcal",
    "workout": "minutes",
    "vo2_max": "ml_kg_min",
    # Tier 2/3 metrics (future)
    "blood_glucose": "mg_dl",
    "blood_pressure_systolic": "mmhg",
    "blood_pressure_diastolic": "mmhg",
    "body_temperature": "celsius",
    "weight": "kg",
    "body_fat": "pct",
    "strain": "score",
    "recovery": "pct",
    "readiness": "score",
    "skin_temperature": "celsius",
}


# ---------------------------------------------------------------------------
# Session 2: DDL for health_metrics_normalized
# (Run once in Supabase SQL editor — or execute via migration script)
# ---------------------------------------------------------------------------
# CREATE TABLE IF NOT EXISTS public.health_metrics_normalized (
#     id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
#     date             DATE NOT NULL,
#     canonical_metric TEXT NOT NULL,
#     value            FLOAT NOT NULL,
#     source           TEXT NOT NULL,
#     source_type      TEXT NOT NULL
#         CHECK (source_type IN ('direct', 'derived', 'computed_composite')),
#     raw_metric       TEXT,
#     confidence       FLOAT NOT NULL DEFAULT 1.0,
#     computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
#     UNIQUE (user_id, date, canonical_metric, source)
# );
# CREATE INDEX IF NOT EXISTS idx_hmn_user_date
#     ON public.health_metrics_normalized (user_id, date DESC);
# CREATE INDEX IF NOT EXISTS idx_hmn_user_metric
#     ON public.health_metrics_normalized (user_id, canonical_metric, date DESC);
# ALTER TABLE public.health_metrics_normalized ENABLE ROW LEVEL SECURITY;
# CREATE POLICY "own normalized metrics" ON public.health_metrics_normalized
#     FOR ALL USING (auth.uid() = user_id)
#     WITH CHECK  (auth.uid() = user_id);
# ---------------------------------------------------------------------------

# Mapping from (source, metric_type) → (value_json_key, adapter_raw_key)
# Used by _build_raw_day() to reconstruct the flat dict each DeviceAdapter expects.
#   value_json_key  — the key to extract from native_health_data.value_json
#   adapter_raw_key — the key to use in the raw_day dict passed to the adapter
_HEALTHKIT_REMAP: Dict[str, tuple] = {
    "steps": ("steps", "steps"),
    "sleep": ("hours", "sleep_hours"),
    "resting_heart_rate": ("bpm", "resting_heart_rate"),
    "hrv_sdnn": ("ms", "hrv_sdnn_ms"),
    "spo2": ("pct", "spo2_pct"),
    "respiratory_rate": ("rate", "respiratory_rate"),
    "active_calories": ("kcal", "active_calories_kcal"),
    "workout": ("minutes", "workout_minutes"),
    "vo2_max": ("ml_kg_min", "vo2_max"),
    "blood_glucose": ("mg_dl", "blood_glucose_mgdl"),
    "blood_pressure_systolic": ("mmhg", "blood_pressure_systolic_mmhg"),
    "blood_pressure_diastolic": ("mmhg", "blood_pressure_diastolic_mmhg"),
    "body_temperature": ("celsius", "body_temperature_c"),
    "weight": ("kg", "weight_kg"),
    "body_fat": ("pct", "body_fat_pct"),
}

_HEALTH_CONNECT_REMAP: Dict[str, tuple] = {
    **_HEALTHKIT_REMAP,
    "hrv_sdnn": ("ms", "hrv_rmssd_ms"),  # Health Connect uses RMSSD
    "hrv_rmssd": ("ms", "hrv_rmssd_ms"),  # explicit RMSSD key
    "stress_score": ("score", "stress_score"),
}

_DEXCOM_REMAP: Dict[str, tuple] = {
    "blood_glucose": ("mg_dl", "blood_glucose_mgdl"),
    "avg_glucose": ("mg_dl", "avg_glucose_mgdl"),
    "peak_glucose": ("mg_dl", "peak_glucose_mgdl"),
    "time_in_range": ("pct", "time_in_range_pct"),
    "glucose_variability": ("cv", "glucose_variability_cv"),
    "glucose_spikes": ("count", "glucose_spikes_count"),
}

_SOURCE_REMAP: Dict[str, Dict[str, tuple]] = {
    "healthkit": _HEALTHKIT_REMAP,
    "health_connect": _HEALTH_CONNECT_REMAP,
    "dexcom": _DEXCOM_REMAP,
}


def _build_raw_day(
    source: str, data_points: List["HealthDataPoint"]
) -> Dict[str, Dict[str, Any]]:
    """
    Group *data_points* by date and produce a flat adapter-ready raw_day
    dict for each date.

    Returns ``{date_str: {adapter_raw_key: scalar_value, ...}, ...}``.
    """
    remap = _SOURCE_REMAP.get(source, {})
    by_date: Dict[str, Dict[str, Any]] = {}

    for dp in data_points:
        day = by_date.setdefault(dp.date, {})
        vj = dp.value_json if isinstance(dp.value_json, dict) else {}

        mapping = remap.get(dp.metric_type)
        if mapping:
            vj_key, adapter_key = mapping
            if vj_key in vj:
                try:
                    day[adapter_key] = float(vj[vj_key])
                except (TypeError, ValueError):
                    pass
        else:
            # Fallback: extract any numeric value from value_json
            # and key it by metric_type (handles future or unknown metrics)
            for vj_val in vj.values():
                try:
                    day[dp.metric_type] = float(vj_val)
                    break
                except (TypeError, ValueError):
                    pass

    return by_date


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class HealthDataPoint(BaseModel):  # pylint: disable=too-few-public-methods
    """A single health metric sample for one calendar day."""

    metric_type: str = Field(
        ...,
        description=(
            "Data type: steps | sleep | resting_heart_rate | hrv_sdnn | spo2 | workout"
        ),
    )
    date: str = Field(..., description="Calendar date in YYYY-MM-DD format")
    value_json: Dict[str, Any] = Field(
        ..., description="Metric-specific payload, e.g. {steps: 8000}"
    )


class HealthIngestRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Batch health data payload sent from the mobile app after a sync."""

    source: str = Field(
        ...,
        description="Data source: healthkit, health_connect, oura, whoop, garmin, etc.",
    )
    data_points: List[HealthDataPoint] = Field(
        ..., max_length=500, description="Up to 500 data points per request"
    )
    sync_timestamp: str = Field(
        ..., description="ISO 8601 UTC timestamp of when the sync was initiated"
    )


class HealthIngestResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Summary of ingest results."""

    accepted: int
    skipped: int
    sync_timestamp: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=HealthIngestResponse, status_code=201)
async def ingest_health_data(
    body: HealthIngestRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Ingest batched native health data from any supported source.

    Each data_point is upserted by (user_id, source, metric_type, date).
    Re-syncing the same date is safe — it updates the existing row.
    Maximum 500 data points per request.

    After ingest, summaries are recomputed in the background.
    """
    if body.source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source '{body.source}'. Valid: {sorted(VALID_SOURCES)}",
        )
    user_id = current_user["id"]
    now_iso = datetime.now(timezone.utc).isoformat()

    rows = [
        {
            "user_id": user_id,
            "source": body.source,
            "metric_type": dp.metric_type,
            "date": dp.date,
            "value_json": dp.value_json,
            "created_at": now_iso,
        }
        for dp in body.data_points
    ]

    # Single batch upsert — orders of magnitude faster than per-row calls
    accepted = 0
    skipped = len(rows)
    if SUPABASE_URL and SUPABASE_SERVICE_KEY and rows:
        url = f"{SUPABASE_URL}/rest/v1/native_health_data?on_conflict={_ON_CONFLICT}"
        headers = {
            **_supabase_headers(),
            "Prefer": "resolution=merge-duplicates,return=representation",
        }
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(ssl=_ssl_context()),
            ) as session:
                async with session.post(url, headers=headers, json=rows) as resp:
                    if resp.status in (200, 201):
                        data = await resp.json()
                        accepted = len(data) if isinstance(data, list) else len(rows)
                        skipped = len(rows) - accepted
                    else:
                        err = await resp.text()
                        logger.error(
                            "Batch upsert failed status=%d error=%s", resp.status, err
                        )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Batch upsert exception: %s", exc)

    logger.info(
        "Health ingest user=%s source=%s accepted=%d skipped=%d",
        user_id,
        body.source,
        accepted,
        skipped,
    )

    # Recompute summaries in the background (non-blocking)
    if accepted > 0:
        background_tasks.add_task(recompute_summaries, user_id)
        # Session 2: also normalize + persist to health_metrics_normalized
        background_tasks.add_task(
            normalize_and_persist_ingest, user_id, body.source, body.data_points
        )

    return HealthIngestResponse(
        accepted=accepted,
        skipped=skipped,
        sync_timestamp=body.sync_timestamp,
    )


@router.get("/status")
async def get_native_health_status(
    current_user: dict = Depends(get_current_user),
):
    """Return connection status per native health source (healthkit / health_connect)."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "native_health_data",
        f"user_id=eq.{user_id}&select=source,date&order=date.desc&limit=200",
    )
    sources: Dict[str, Any] = {}
    for row in rows:
        src = row.get("source")
        if src and src not in sources:
            sources[src] = {"connected": True, "last_sync": row.get("date")}
    return {
        "healthkit": sources.get("healthkit", {"connected": False, "last_sync": None}),
        "health_connect": sources.get(
            "health_connect", {"connected": False, "last_sync": None}
        ),
    }


@router.delete("/source/{source}", status_code=204)
async def disconnect_source(
    source: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete all synced data for the given source, effectively disconnecting it.

    Source must be 'healthkit' or 'health_connect'.
    """
    if source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source '{source}'. Valid: {sorted(VALID_SOURCES)}",
        )

    user_id = current_user["id"]

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        url = (
            f"{SUPABASE_URL}/rest/v1/native_health_data"
            f"?user_id=eq.{user_id}&source=eq.{source}"
        )
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(ssl=_ssl_context()),
            ) as session:
                async with session.delete(url, headers=_supabase_headers()) as resp:
                    if resp.status not in (200, 204):
                        err = await resp.text()
                        logger.error(
                            "Source delete failed status=%d error=%s", resp.status, err
                        )
                        raise HTTPException(
                            status_code=500, detail="Failed to disconnect source"
                        )
        except HTTPException:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Source delete exception: %s", exc)
            raise HTTPException(
                status_code=500, detail="Failed to disconnect source"
            ) from exc

    logger.info("Health source disconnected user=%s source=%s", user_id, source)


@router.get("/recent")
async def get_recent_health_data(
    current_user: dict = Depends(get_current_user),
    source: Optional[str] = None,
):
    """Return the most recent value for each metric type for the current user."""
    user_id = current_user["id"]
    source_filter = f"&source=eq.{source}" if source in VALID_SOURCES else ""
    rows = await _supabase_get(
        "native_health_data",
        f"user_id=eq.{user_id}{source_filter}&order=date.desc&limit=50&select=metric_type,value_json",
    )
    seen: set = set()
    result: Dict[str, Any] = {}
    for row in rows:
        metric_type = row.get("metric_type")
        if metric_type and metric_type not in seen:
            seen.add(metric_type)
            vj = row.get("value_json") or {}
            key = _PRIMARY_KEY.get(metric_type)
            result[metric_type] = vj.get(key) if key and isinstance(vj, dict) else None
    return {k: v for k, v in result.items() if v is not None}


# ---------------------------------------------------------------------------
# Summaries: pre-computed rolling averages + anomaly detection
# ---------------------------------------------------------------------------


def _extract_value(metric_type: str, value_json: Any) -> Optional[float]:
    """Extract the primary numeric value from a JSONB value_json field."""
    if not isinstance(value_json, dict):
        return None
    key = _PRIMARY_KEY.get(metric_type)
    if not key:
        return None
    val = value_json.get(key)
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _trend(current_avg: Optional[float], prev_avg: Optional[float]) -> str:
    """Compare two averages to determine trend direction."""
    if current_avg is None or prev_avg is None or prev_avg == 0:
        return "stable"
    pct_change = (current_avg - prev_avg) / abs(prev_avg)
    if pct_change > 0.05:
        return "up"
    if pct_change < -0.05:
        return "down"
    return "stable"


def _safe_avg(values: List[Any]) -> Optional[float]:
    nums = [v for v in values if isinstance(v, (int, float))]
    return sum(nums) / len(nums) if nums else None


def _safe_stddev(values: List[Any], mean: Optional[float]) -> Optional[float]:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums or mean is None or len(nums) < 3:
        return None
    variance = sum((v - mean) ** 2 for v in nums) / len(nums)
    return math.sqrt(variance)


async def recompute_summaries(user_id: str) -> None:
    """Recompute health_metric_summaries for a user from raw data.

    Called as a background task after each ingest. Queries all raw data,
    computes rolling averages and anomaly flags, then upserts one row
    per metric into health_metric_summaries.
    """
    try:
        # Fetch all raw data for this user (ordered by date desc)
        rows = await _supabase_get(
            "native_health_data",
            f"user_id=eq.{user_id}"
            f"&select=metric_type,date,value_json"
            f"&order=date.desc"
            f"&limit=10000",
        )
        if not rows:
            return

        today = date.today()

        # Group values by metric_type with date
        by_metric: Dict[str, List[tuple]] = {}
        for row in rows:
            mt = row.get("metric_type")
            d = row.get("date")
            vj = row.get("value_json")
            if not mt or not d:
                continue
            val = _extract_value(mt, vj)
            if val is None:
                continue
            by_metric.setdefault(mt, []).append((d, val))

        summaries = []
        for metric_type, date_vals in by_metric.items():
            # Parse dates and sort
            parsed = []
            for d_str, val in date_vals:
                try:
                    d = (
                        datetime.fromisoformat(d_str).date()
                        if isinstance(d_str, str)
                        else d_str
                    )
                    parsed.append((d, val))
                except (ValueError, TypeError):
                    continue

            if not parsed:
                continue

            parsed.sort(key=lambda x: x[0], reverse=True)

            # Window calculations
            def vals_in_window(days: int) -> List[Any]:
                cutoff = today - timedelta(days=days)
                return [v for d, v in parsed if d >= cutoff]

            def vals_in_window_range(start_days: int, end_days: int) -> List[Any]:
                start = today - timedelta(days=start_days)
                end = today - timedelta(days=end_days)
                return [v for d, v in parsed if end <= d < start]

            v7: List[Any] = vals_in_window(7)
            v30: List[Any] = vals_in_window(30)
            v90: List[Any] = vals_in_window(90)
            v180: List[Any] = vals_in_window(180)
            v365: List[Any] = vals_in_window(365)
            all_vals: List[Any] = [v for _, v in parsed]

            avg_7d = _safe_avg(v7)
            avg_30d = _safe_avg(v30)
            avg_90d = _safe_avg(v90)
            avg_180d = _safe_avg(v180)
            avg_365d = _safe_avg(v365)

            # Previous windows for trend
            prev_7d = vals_in_window_range(14, 7)
            prev_30d = vals_in_window_range(60, 30)

            # Personal baseline = 90-day average (or all-time if <90 days)
            baseline = avg_90d if avg_90d is not None else _safe_avg(all_vals)
            stddev = _safe_stddev(v90 if len(v90) >= 3 else all_vals, baseline)

            # Anomaly detection: is current 7d avg >2σ from baseline?
            is_anomalous = False
            anomaly_severity = None
            anomaly_detail = None
            if avg_7d is not None and baseline is not None and stddev and stddev > 0:
                deviation = abs(avg_7d - baseline) / stddev
                if deviation > 3:
                    is_anomalous = True
                    anomaly_severity = "high"
                    direction = "above" if avg_7d > baseline else "below"
                    anomaly_detail = (
                        f"7-day avg ({avg_7d:.1f}) is {deviation:.1f}σ "
                        f"{direction} your baseline ({baseline:.1f})"
                    )
                elif deviation > 2:
                    is_anomalous = True
                    anomaly_severity = "medium"
                    direction = "above" if avg_7d > baseline else "below"
                    anomaly_detail = (
                        f"7-day avg ({avg_7d:.1f}) is {deviation:.1f}σ "
                        f"{direction} your baseline ({baseline:.1f})"
                    )

            latest_date_obj = parsed[0][0]
            latest_value: float = float(parsed[0][1] or 0)
            first_date_obj = parsed[-1][0]

            summaries.append(
                {
                    "user_id": user_id,
                    "metric_type": metric_type,
                    "avg_7d": round(avg_7d, 2) if avg_7d else None,
                    "avg_30d": round(avg_30d, 2) if avg_30d else None,
                    "avg_90d": round(avg_90d, 2) if avg_90d else None,
                    "avg_180d": round(avg_180d, 2) if avg_180d else None,
                    "avg_365d": round(avg_365d, 2) if avg_365d else None,
                    "min_7d": round(min(v7), 2) if v7 else None,
                    "max_7d": round(max(v7), 2) if v7 else None,
                    "min_30d": round(min(v30), 2) if v30 else None,
                    "max_30d": round(max(v30), 2) if v30 else None,
                    "latest_value": round(latest_value, 2),
                    "latest_date": str(latest_date_obj),
                    "data_points_7d": len(v7),
                    "data_points_30d": len(v30),
                    "data_points_total": len(parsed),
                    "first_date": str(first_date_obj),
                    "trend_7d": _trend(avg_7d, _safe_avg(prev_7d)),
                    "trend_30d": _trend(avg_30d, _safe_avg(prev_30d)),
                    "personal_baseline": round(baseline, 2) if baseline else None,
                    "baseline_stddev": round(stddev, 2) if stddev else None,
                    "is_anomalous": is_anomalous,
                    "anomaly_severity": anomaly_severity,
                    "anomaly_detail": anomaly_detail,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        # Upsert all summaries
        for summary in summaries:
            try:
                await _supabase_upsert(
                    "health_metric_summaries", summary, "user_id,metric_type"
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(
                    "Summary upsert failed metric=%s: %s",
                    summary.get("metric_type"),
                    exc,
                )

        logger.info("Summaries recomputed user=%s metrics=%d", user_id, len(summaries))
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("recompute_summaries failed user=%s: %s", user_id, exc)


# ---------------------------------------------------------------------------
# Session 2: normalize ingest data → health_metrics_normalized
# ---------------------------------------------------------------------------


async def normalize_and_persist_ingest(
    user_id: str,
    source: str,
    data_points: List[HealthDataPoint],
) -> None:
    """
    Background task: convert raw ingest data_points into canonical
    NormalizedMetric objects and persist to ``health_metrics_normalized``.

    Only runs for sources with a registered DeviceAdapter
    (healthkit, health_connect, dexcom).  Unrecognised sources are
    silently skipped — existing Oura data flows through the Oura
    polling endpoint (Session 3 will unify the two paths).
    """
    from common.metrics.normalizer import HealthNormalizer  # late import avoids cycles
    from common.metrics.persistence import persist_normalized_metrics

    try:
        by_date = _build_raw_day(source, data_points)
        if not by_date:
            return

        normalizer = HealthNormalizer()
        total_rows = 0

        for date_str, raw_day in by_date.items():
            if not raw_day:
                continue

            # Phase 2: pass empty baseline — composite scores that need
            # rolling history (hrv_balance, readiness) will be computed
            # once health_metrics_normalized has 14+ days (Session 3+).
            metrics = normalizer.normalize(
                source=source,
                raw_day=raw_day,
                date=date_str,
                user_baseline={},
            )
            if metrics:
                n = await persist_normalized_metrics(user_id, date_str, metrics)
                total_rows += n

        logger.info(
            "normalize_and_persist: user=%s source=%s dates=%d rows=%d",
            user_id,
            source,
            len(by_date),
            total_rows,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(
            "normalize_and_persist failed user=%s source=%s: %s", user_id, source, exc
        )


@router.get("/summaries")
async def get_health_summaries(
    current_user: dict = Depends(get_current_user),
):
    """Return pre-computed health metric summaries with rolling averages,
    trends, personal baselines, and anomaly flags.

    This is the primary endpoint for AI agents, insights, and the mobile app
    to understand a user's health trajectory.
    """
    user_id = current_user["id"]
    rows = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&order=metric_type",
    )
    result: Dict[str, Any] = {}
    for row in rows:
        mt = row.get("metric_type")
        if not mt:
            continue
        result[mt] = {
            "latest_value": row.get("latest_value"),
            "latest_date": row.get("latest_date"),
            "avg_7d": row.get("avg_7d"),
            "avg_30d": row.get("avg_30d"),
            "avg_90d": row.get("avg_90d"),
            "avg_180d": row.get("avg_180d"),
            "avg_365d": row.get("avg_365d"),
            "min_7d": row.get("min_7d"),
            "max_7d": row.get("max_7d"),
            "min_30d": row.get("min_30d"),
            "max_30d": row.get("max_30d"),
            "trend_7d": row.get("trend_7d"),
            "trend_30d": row.get("trend_30d"),
            "data_points_7d": row.get("data_points_7d"),
            "data_points_30d": row.get("data_points_30d"),
            "data_points_total": row.get("data_points_total"),
            "first_date": row.get("first_date"),
            "personal_baseline": row.get("personal_baseline"),
            "is_anomalous": row.get("is_anomalous"),
            "anomaly_severity": row.get("anomaly_severity"),
            "anomaly_detail": row.get("anomaly_detail"),
        }
    return result


# ---------------------------------------------------------------------------
# Session 6: Push on First Connect — initial-sync + sync-status endpoints
# ---------------------------------------------------------------------------

# In-process task registry (survives process restart only for fast tasks;
# long historical pulls finish within a few minutes so this is sufficient).
_sync_tasks: Dict[str, Dict[str, Any]] = {}

# Watermark table DDL (run once in Supabase SQL editor):
#
#   CREATE TABLE IF NOT EXISTS public.health_sync_watermarks (
#       user_id   UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
#       source    TEXT NOT NULL,
#       last_sync_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
#       PRIMARY KEY (user_id, source)
#   );
#   ALTER TABLE public.health_sync_watermarks ENABLE ROW LEVEL SECURITY;
#   CREATE POLICY "own watermarks" ON public.health_sync_watermarks
#       FOR ALL USING (auth.uid() = user_id)
#       WITH CHECK (auth.uid() = user_id);

INITIAL_SYNC_DAYS = int(__import__("os").environ.get("INITIAL_SYNC_DAYS", "90"))


class InitialSyncRequest(BaseModel):
    source: Literal[
        "healthkit",
        "health_connect",
        "oura",
        "whoop",
        "garmin",
        "fitbit",
        "polar",
        "samsung",
        "dexcom",
        "blood_pressure",
        "clinical",
    ]
    data_points: List[HealthDataPoint] = Field(
        default=[],
        description="Pre-fetched 90d data_points from the mobile client. "
        "If empty the server will note that it expects the client to push data.",
    )


class InitialSyncResponse(BaseModel):
    task_id: str
    status: str  # 'accepted' | 'skipped' (already synced)
    message: str
    accepted: int = 0


class SyncStatusResponse(BaseModel):
    task_id: str
    status: str  # 'pending' | 'running' | 'done' | 'error'
    accepted: int = 0
    message: str = ""
    completed_at: Optional[str] = None


async def _get_last_sync(user_id: str, source: str) -> Optional[datetime]:
    """Return the last_sync_at watermark for (user_id, source), or None."""
    try:
        rows = await _supabase_get(
            "health_sync_watermarks",
            f"user_id=eq.{user_id}&source=eq.{source}&select=last_sync_at&limit=1",
        )
        if rows:
            ts = rows[0].get("last_sync_at")
            if ts:
                return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Could not read watermark for %s/%s: %s", user_id, source, exc)
    return None


async def _set_watermark(user_id: str, source: str) -> None:
    """Upsert the last_sync_at watermark to now."""
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        await _supabase_upsert(
            "health_sync_watermarks",
            [{"user_id": user_id, "source": source, "last_sync_at": now_iso}],
            on_conflict="user_id,source",
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Could not write watermark for %s/%s: %s", user_id, source, exc)


async def _run_initial_sync(
    task_id: str,
    user_id: str,
    source: str,
    data_points: List[HealthDataPoint],
) -> None:
    """
    Background task: ingest pre-fetched data_points, update watermark, mark done.
    The mobile client is responsible for fetching and sending the 90-day history;
    this function handles persistence + normalization.
    """
    _sync_tasks[task_id]["status"] = "running"

    total_accepted = 0
    try:
        if data_points:
            now_iso = datetime.now(timezone.utc).isoformat()
            rows = [
                {
                    "user_id": user_id,
                    "source": source,
                    "metric_type": dp.metric_type,
                    "date": dp.date,
                    "value_json": dp.value_json,
                    "created_at": now_iso,
                }
                for dp in data_points
            ]

            if SUPABASE_URL and SUPABASE_SERVICE_KEY and rows:
                url = f"{SUPABASE_URL}/rest/v1/native_health_data?on_conflict={_ON_CONFLICT}"
                headers = {
                    **_supabase_headers(),
                    "Prefer": "resolution=merge-duplicates,return=representation",
                }
                # Chunk into batches of 500 to avoid payload limits
                for i in range(0, len(rows), 500):
                    chunk = rows[i : i + 500]
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=60),
                        connector=aiohttp.TCPConnector(ssl=_ssl_context()),
                    ) as session:
                        async with session.post(
                            url, headers=headers, json=chunk
                        ) as resp:
                            if resp.status in (200, 201):
                                data = await resp.json()
                                total_accepted += (
                                    len(data) if isinstance(data, list) else len(chunk)
                                )
                            else:
                                err = await resp.text()
                                logger.error(
                                    "initial-sync chunk failed status=%d err=%s",
                                    resp.status,
                                    err,
                                )

            # Trigger normalization in background (fire-and-forget)
            if total_accepted > 0:
                asyncio.create_task(
                    normalize_and_persist_ingest(user_id, source, data_points)
                )
                asyncio.create_task(recompute_summaries(user_id))

        await _set_watermark(user_id, source)

        _sync_tasks[task_id].update(
            {
                "status": "done",
                "accepted": total_accepted,
                "message": f"Ingested {total_accepted} data points",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(
            "initial-sync done user=%s source=%s accepted=%d",
            user_id,
            source,
            total_accepted,
        )

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("initial-sync task %s failed: %s", task_id, exc)
        _sync_tasks[task_id].update(
            {
                "status": "error",
                "message": str(exc),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )


@router.post("/initial-sync", response_model=InitialSyncResponse, status_code=202)
async def initial_sync(
    body: InitialSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger a one-time 90-day historical sync after a device is first connected.

    The mobile client should:
    1. Request health permissions.
    2. Fetch the past 90 days of data locally (HealthKit / Health Connect).
    3. POST this endpoint with data_points (batched; call multiple times if >500).

    If the source already has a watermark (has been synced before), returns
    status='skipped' to prevent redundant re-ingestion.

    Returns a task_id to poll via GET /api/v1/health-data/sync-status/{task_id}.
    """
    user_id = current_user["id"]

    if body.source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source '{body.source}'. Valid: {sorted(VALID_SOURCES)}",
        )

    # Idempotency guard: skip if watermark exists (already synced)
    last_sync = await _get_last_sync(user_id, body.source)
    if last_sync is not None:
        task_id = str(uuid.uuid4())
        _sync_tasks[task_id] = {
            "status": "done",
            "accepted": 0,
            "message": f"Already synced at {last_sync.isoformat()}",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        return InitialSyncResponse(
            task_id=task_id,
            status="skipped",
            message=f"Already synced at {last_sync.isoformat()}",
        )

    task_id = str(uuid.uuid4())
    _sync_tasks[task_id] = {
        "status": "pending",
        "accepted": 0,
        "message": "Queued",
        "completed_at": None,
    }

    background_tasks.add_task(
        _run_initial_sync, task_id, user_id, body.source, body.data_points
    )

    logger.info(
        "initial-sync queued task=%s user=%s source=%s points=%d",
        task_id,
        user_id,
        body.source,
        len(body.data_points),
    )

    return InitialSyncResponse(
        task_id=task_id,
        status="accepted",
        message=f"Syncing {len(body.data_points)} data points in background",
        accepted=len(body.data_points),
    )


@router.get("/sync-status/{task_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),  # auth required
):
    """
    Poll the status of a background initial-sync task.

    Returns one of: pending | running | done | error.
    Poll every 2–3 seconds until status is 'done' or 'error'.
    """
    task = _sync_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return SyncStatusResponse(
        task_id=task_id,
        status=task["status"],
        accepted=task.get("accepted", 0),
        message=task.get("message", ""),
        completed_at=task.get("completed_at"),
    )


@router.get("/sync-watermark")
async def get_sync_watermark(
    source: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Return the last_sync_at watermark for the user's connected sources.
    Mobile uses this to determine if an initial sync is needed and what
    date range to fetch (from watermark to now for incremental syncs).
    """
    user_id = current_user["id"]
    query = f"user_id=eq.{user_id}&select=source,last_sync_at"
    if source:
        query += f"&source=eq.{source}"

    try:
        rows = await _supabase_get("health_sync_watermarks", query)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Could not read watermarks: %s", exc)
        rows = []

    return {
        row.get("source"): row.get("last_sync_at")
        for row in (rows or [])
        if row.get("source")
    }
