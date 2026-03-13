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

    CREATE TABLE public.native_health_data (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        source TEXT NOT NULL CHECK (source IN ('healthkit', 'health_connect')),
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
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

import aiohttp
from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    _supabase_headers,
    _ssl_context,
)

logger = get_logger(__name__)
router = APIRouter()

_ON_CONFLICT = "user_id,source,metric_type,date"


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

    source: Literal["healthkit", "health_connect"]
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
    current_user: dict = Depends(get_current_user),
):
    """Ingest batched native health data from HealthKit or Health Connect.

    Each data_point is upserted by (user_id, source, metric_type, date).
    Re-syncing the same date is safe — it updates the existing row.
    Maximum 500 data points per request.
    """
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
    return HealthIngestResponse(
        accepted=accepted,
        skipped=skipped,
        sync_timestamp=body.sync_timestamp,
    )


@router.get("/recent")
async def get_recent_health_data(
    current_user: dict = Depends(get_current_user),
):
    """Return the most recent value for each metric type for the current user."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "native_health_data",
        f"user_id=eq.{user_id}&order=date.desc&limit=50&select=metric_type,value_json",
    )
    # Pick the most recent row per metric_type
    seen: set = set()
    result: Dict[str, Any] = {}
    for row in rows:
        metric_type = row.get("metric_type")
        if metric_type and metric_type not in seen:
            seen.add(metric_type)
            value_json = row.get("value_json", {})
            # Extract the primary numeric value from value_json
            if isinstance(value_json, dict) and value_json:
                result[metric_type] = next(iter(value_json.values()))
    return result
