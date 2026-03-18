"""
Async persistence helper for health_metrics_normalized.

This is the only I/O-performing module in common.metrics.  It writes
NormalizedMetric objects to the ``health_metrics_normalized`` Supabase
table and is intentionally decoupled from the normalizer (which is
pure, stateless computation).

Table DDL (run once in Supabase SQL editor) — also mirrored in
``apps/mvp_api/api/health_data.py``::

    CREATE TABLE IF NOT EXISTS public.health_metrics_normalized (
        id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        date             DATE NOT NULL,
        canonical_metric TEXT NOT NULL,
        value            FLOAT NOT NULL,
        source           TEXT NOT NULL,
        source_type      TEXT NOT NULL
            CHECK (source_type IN ('direct', 'derived', 'computed_composite')),
        raw_metric       TEXT,
        confidence       FLOAT NOT NULL DEFAULT 1.0,
        computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, date, canonical_metric, source)
    );
    CREATE INDEX IF NOT EXISTS idx_hmn_user_date
        ON public.health_metrics_normalized (user_id, date DESC);
    CREATE INDEX IF NOT EXISTS idx_hmn_user_metric
        ON public.health_metrics_normalized (user_id, canonical_metric, date DESC);
    ALTER TABLE public.health_metrics_normalized ENABLE ROW LEVEL SECURITY;
    CREATE POLICY "own normalized metrics" ON public.health_metrics_normalized
        FOR ALL USING (auth.uid() = user_id)
        WITH CHECK  (auth.uid() = user_id);

Usage::

    from common.metrics.persistence import persist_normalized_metrics

    n = await persist_normalized_metrics(
        user_id="uuid-...",
        date="2026-03-18",
        metrics=normalized_metric_list,
    )
"""

from __future__ import annotations

import logging
import os
import ssl
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp
import certifi

from common.metrics.adapters.base import NormalizedMetric

logger = logging.getLogger(__name__)

_TABLE = "health_metrics_normalized"
_ON_CONFLICT = "user_id,date,canonical_metric,source"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ssl_ctx() -> ssl.SSLContext:
    """certifi CA bundle — fixes macOS SSL cert verification."""
    return ssl.create_default_context(cafile=certifi.where())


def _headers(service_key: str) -> dict:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


def _to_row(user_id: str, date: str, m: NormalizedMetric, now_iso: str) -> dict:
    """Convert a NormalizedMetric to a Supabase row dict."""
    return {
        "user_id": user_id,
        "date": date,
        "canonical_metric": m.canonical_metric,
        "value": m.value,
        "source": m.source,
        "source_type": m.source_type.value,  # enum → "DIRECT" / "DERIVED" / etc.
        "raw_metric": m.raw_metric,
        "confidence": m.confidence,
        "computed_at": now_iso,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def persist_normalized_metrics(
    user_id: str,
    date: str,
    metrics: List[NormalizedMetric],
    *,
    supabase_url: Optional[str] = None,
    supabase_service_key: Optional[str] = None,
) -> int:
    """
    Upsert *metrics* for *user_id* / *date* into ``health_metrics_normalized``.

    Conflict key is ``(user_id, date, canonical_metric, source)`` — re-calling
    with the same data is safe (idempotent upsert).

    Parameters
    ----------
    user_id:
        Supabase ``auth.users.id`` UUID string.
    date:
        ISO date string ``"YYYY-MM-DD"``.
    metrics:
        List of ``NormalizedMetric`` objects from ``HealthNormalizer.normalize()``.
    supabase_url:
        Override the ``SUPABASE_URL`` env var (useful in tests).
    supabase_service_key:
        Override the ``SUPABASE_SERVICE_KEY`` env var (useful in tests).

    Returns
    -------
    int
        Number of rows accepted by Supabase.  Returns 0 on error or when
        credentials are unavailable.
    """
    url_base = (supabase_url or os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = supabase_service_key or os.environ.get("SUPABASE_SERVICE_KEY") or ""

    if not url_base or not key:
        logger.debug(
            "persist_normalized_metrics: Supabase credentials not set — skipping"
        )
        return 0

    if not metrics:
        return 0

    now_iso = datetime.now(timezone.utc).isoformat()
    rows = [_to_row(user_id, date, m, now_iso) for m in metrics]

    url = f"{url_base}/rest/v1/{_TABLE}?on_conflict={_ON_CONFLICT}"
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=_ssl_ctx()),
        ) as session:
            async with session.post(url, headers=_headers(key), json=rows) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    accepted = len(data) if isinstance(data, list) else len(rows)
                    logger.debug(
                        "persist_normalized: user=%s date=%s accepted=%d",
                        user_id,
                        date,
                        accepted,
                    )
                    return accepted

                err = await resp.text()
                logger.error(
                    "persist_normalized failed: status=%d error=%s",
                    resp.status,
                    err,
                )
                return 0

    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("persist_normalized exception: %s", exc)
        return 0
