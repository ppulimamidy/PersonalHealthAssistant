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

import json
import math
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
