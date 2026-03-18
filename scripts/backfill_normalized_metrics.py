#!/usr/bin/env python3
"""
One-time backfill script: populate health_metrics_normalized from existing data.

Reads from:
  1. native_health_data  (HealthKit, Health Connect, Dexcom, etc.)
  2. Oura legacy tables  (daily_sleep, daily_activity, daily_readiness)

Runs each row through HealthNormalizer → persist_normalized_metrics().

Usage:
    # From project root with PYTHONPATH set:
    export PYTHONPATH=/Users/pulimap/PersonalHealthAssistant
    python scripts/backfill_normalized_metrics.py [--user USER_ID] [--dry-run]

    # Backfill only Sarah Chen demo data:
    python scripts/backfill_normalized_metrics.py --user 22144dc2-f352-48aa-b34b-aebfa9f7e638
"""

import argparse
import asyncio
import json
import logging
import os
import ssl
import sys
from collections import defaultdict
from datetime import datetime, timezone

import aiohttp
import certifi
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.metrics.normalizer import HealthNormalizer
from common.metrics.persistence import persist_normalized_metrics

load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps", "mvp_api", ".env")
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BATCH_SIZE = 500


def _ssl_ctx():
    return ssl.create_default_context(cafile=certifi.where())


def _headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


async def _supabase_get(session: aiohttp.ClientSession, table: str, query: str) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    async with session.get(url, headers=_headers()) as resp:
        if resp.status == 200:
            return await resp.json()
        logger.error("GET %s failed: %s %s", table, resp.status, await resp.text())
        return []


# ── Native Health Data backfill ──────────────────────────────────────────────

# Map native metric_type → raw field name for HealthKit/Health Connect adapter
_HEALTHKIT_FIELD_MAP = {
    "sleep": "sleep_hours",
    "steps": "steps",
    "heart_rate": "resting_heart_rate",
    "hrv_sdnn": "hrv_sdnn_ms",
    "resting_heart_rate": "resting_heart_rate",
    "respiratory_rate": "respiratory_rate",
    "active_energy": "active_energy_kcal",
    "resting_energy": "resting_energy_kcal",
    "blood_oxygen": "blood_oxygen_pct",
    "vo2_max": "vo2_max",
    "body_temperature": "body_temperature_c",
    "workout": "workout_minutes",
    "spo2": "spo2_pct",
}

# Oura metric_types stored in native_health_data map directly to OuraAdapter field names
_OURA_FIELD_MAP = {
    "sleep_score": "sleep_score",
    "sleep_efficiency": "sleep_efficiency",
    "total_sleep_hours": "total_sleep_hours",
    "deep_sleep_hours": "deep_sleep_hours",
    "readiness_score": "readiness_score",
    "hrv_balance": "hrv_balance",
    "recovery_index": "recovery_index",
    "resting_heart_rate": "resting_heart_rate",
    "steps": "steps",
    "active_calories": "active_calories",
    "activity_score": "activity_score",
    "temperature_deviation": "temperature_deviation",
    "respiratory_rate": "respiratory_rate",
    "hrv_sdnn": "hrv_sdnn",
    "spo2": "spo2",
    "workout_minutes": "workout_minutes",
    "vo2_max": "vo2_max",
}


def _get_field_map(source: str) -> dict:
    if source == "oura":
        return _OURA_FIELD_MAP
    return _HEALTHKIT_FIELD_MAP


async def backfill_native(
    session: aiohttp.ClientSession,
    normalizer: HealthNormalizer,
    user_filter: str | None,
    dry_run: bool,
) -> int:
    """Backfill from native_health_data table."""
    # Paginate to fetch all rows (Supabase REST caps at 1000 per request)
    all_rows: list = []
    page_size = 1000
    offset = 0
    while True:
        query = (
            f"select=user_id,source,metric_type,date,value_json"
            f"&order=date.asc&limit={page_size}&offset={offset}"
        )
        if user_filter:
            query += f"&user_id=eq.{user_filter}"
        page = await _supabase_get(session, "native_health_data", query)
        if not page:
            break
        all_rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size

    rows = all_rows
    logger.info("native_health_data: fetched %d rows", len(rows))

    # Group by (user_id, source, date)
    grouped: dict[tuple, dict] = defaultdict(dict)
    for row in rows:
        source = row.get("source", "healthkit")
        key = (row["user_id"], source, row["date"])
        metric_type = row.get("metric_type", "")

        try:
            vj = row.get("value_json")
            if isinstance(vj, str):
                val_json = json.loads(vj)
            elif isinstance(vj, dict):
                val_json = vj
            else:
                continue
            # Try common value_json key patterns:
            # {"value": 82}, {"steps": 2610}, {"kcal": 319}, {"hours": 4.3},
            # {"rate": 16.2}, {"ml_kg_min": 29}, {"bpm": 58}, {"ms": 35},
            # {"pct": 97}, {"avg": 65}
            value = None
            for k in (
                "value",
                "steps",
                "kcal",
                "hours",
                "rate",
                "ml_kg_min",
                "bpm",
                "ms",
                "pct",
                "avg",
                "total",
                "count",
                "min",
            ):
                if k in val_json:
                    value = val_json[k]
                    break
            if value is None and len(val_json) == 1:
                # Single-key dict — use the only value
                value = next(iter(val_json.values()))
        except (json.JSONDecodeError, TypeError):
            continue

        if value is None:
            continue

        field_map = _get_field_map(source)
        field = field_map.get(metric_type, metric_type)
        grouped[key][field] = float(value)

    total_persisted = 0
    for (user_id, source, date_str), raw_day in grouped.items():
        if not raw_day:
            continue
        metrics = normalizer.normalize(
            source=source,
            raw_day=raw_day,
            date=date_str,
            user_baseline={},
        )
        if not metrics:
            continue

        if dry_run:
            logger.info(
                "[DRY RUN] Would persist %d metrics for user=%s source=%s date=%s",
                len(metrics),
                user_id,
                source,
                date_str,
            )
            total_persisted += len(metrics)
        else:
            n = await persist_normalized_metrics(user_id, date_str, metrics)
            total_persisted += n

    logger.info("native_health_data backfill: %d metrics persisted", total_persisted)
    return total_persisted


# ── Oura legacy tables backfill ──────────────────────────────────────────────


async def backfill_oura_legacy(
    session: aiohttp.ClientSession,
    normalizer: HealthNormalizer,
    user_filter: str | None,
    dry_run: bool,
) -> int:
    """Backfill from Oura legacy tables (daily_sleep, daily_activity, daily_readiness)."""

    sleep_q = "select=*&order=day.asc&limit=2000"
    activity_q = "select=*&order=day.asc&limit=2000"
    readiness_q = "select=*&order=day.asc&limit=2000"

    if user_filter:
        sleep_q += f"&user_id=eq.{user_filter}"
        activity_q += f"&user_id=eq.{user_filter}"
        readiness_q += f"&user_id=eq.{user_filter}"

    sleep_rows = await _supabase_get(session, "daily_sleep", sleep_q)
    activity_rows = await _supabase_get(session, "daily_activity", activity_q)
    readiness_rows = await _supabase_get(session, "daily_readiness", readiness_q)

    logger.info(
        "Oura legacy: %d sleep, %d activity, %d readiness rows",
        len(sleep_rows),
        len(activity_rows),
        len(readiness_rows),
    )

    # Group by (user_id, date)
    grouped: dict[tuple, dict] = defaultdict(dict)

    for row in sleep_rows:
        uid = row.get("user_id", "")
        day = row.get("day", "")
        if not uid or not day:
            continue
        raw = grouped[(uid, day)]
        if (v := row.get("sleep_score")) is not None:
            raw["sleep_score"] = float(v)
        if (v := row.get("sleep_efficiency")) is not None:
            raw["sleep_efficiency"] = float(v)
        if (v := row.get("total_sleep_duration")) is not None:
            raw["total_sleep_hours"] = round(float(v) / 3600, 2)
        if (v := row.get("deep_sleep_duration")) is not None:
            raw["deep_sleep_hours"] = round(float(v) / 3600, 2)
        if (v := row.get("temperature_deviation")) is not None:
            raw["temperature_deviation"] = float(v)
        if (v := row.get("respiratory_rate")) is not None:
            raw["respiratory_rate"] = float(v)
        if (v := row.get("rmssd") or row.get("hrv_sdnn")) is not None:
            raw["hrv_sdnn"] = float(v)
        if (v := row.get("hr_lowest") or row.get("resting_heart_rate")) is not None:
            raw["resting_heart_rate"] = float(v)

    for row in activity_rows:
        uid = row.get("user_id", "")
        day = row.get("day", "")
        if not uid or not day:
            continue
        raw = grouped[(uid, day)]
        if (v := row.get("steps")) is not None:
            raw["steps"] = float(v)
        if (v := row.get("active_calories")) is not None:
            raw["active_calories"] = float(v)
        if (v := row.get("activity_score") or row.get("score")) is not None:
            raw["activity_score"] = float(v)

    for row in readiness_rows:
        uid = row.get("user_id", "")
        day = row.get("day", "")
        if not uid or not day:
            continue
        raw = grouped[(uid, day)]
        if (v := row.get("readiness_score") or row.get("score")) is not None:
            raw["readiness_score"] = float(v)
        if (v := row.get("hrv_balance")) is not None:
            raw["hrv_balance"] = float(v)
        if (v := row.get("recovery_index")) is not None:
            raw["recovery_index"] = float(v)
        if (v := row.get("resting_hr") or row.get("resting_heart_rate")) is not None:
            raw.setdefault("resting_heart_rate", float(v))

    total_persisted = 0
    for (user_id, date_str), raw_day in grouped.items():
        if not raw_day:
            continue
        metrics = normalizer.normalize(
            source="oura",
            raw_day=raw_day,
            date=date_str,
            user_baseline={},
        )
        if not metrics:
            continue

        if dry_run:
            logger.info(
                "[DRY RUN] Would persist %d Oura metrics for user=%s date=%s",
                len(metrics),
                user_id,
                date_str,
            )
            total_persisted += len(metrics)
        else:
            n = await persist_normalized_metrics(user_id, date_str, metrics)
            total_persisted += n

    logger.info("Oura legacy backfill: %d metrics persisted", total_persisted)
    return total_persisted


# ── Main ─────────────────────────────────────────────────────────────────────


async def main(user_filter: str | None, dry_run: bool):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        sys.exit(1)

    normalizer = HealthNormalizer()

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=_ssl_ctx()),
        timeout=aiohttp.ClientTimeout(total=120),
    ) as session:
        logger.info("Starting backfill%s...", " (DRY RUN)" if dry_run else "")

        native_count = await backfill_native(session, normalizer, user_filter, dry_run)
        oura_count = await backfill_oura_legacy(
            session, normalizer, user_filter, dry_run
        )

        logger.info(
            "Backfill complete: native=%d oura_legacy=%d total=%d%s",
            native_count,
            oura_count,
            native_count + oura_count,
            " (DRY RUN)" if dry_run else "",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill health_metrics_normalized")
    parser.add_argument("--user", help="Backfill only this user_id")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )
    args = parser.parse_args()

    asyncio.run(main(args.user, args.dry_run))
