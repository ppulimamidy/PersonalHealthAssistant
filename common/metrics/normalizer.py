"""
HealthNormalizer — the single entry point for canonicalising health data.

Usage::

    from common.metrics.normalizer import HealthNormalizer

    normalizer = HealthNormalizer()

    # Normalise one day of Oura data
    metrics = normalizer.normalize(
        source="oura",
        raw_day={"sleep_score": 82, "hrv_balance": 1.2, "resting_heart_rate": 56, ...},
        date="2026-03-18",
        user_baseline={"hrv_ms": {"mean_30d": 42.1, "std_30d": 8.3, "n": 28}},
    )
    # → list[NormalizedMetric]

    # Normalise Apple Health data (composite scores computed automatically)
    metrics = normalizer.normalize(
        source="healthkit",
        raw_day={"steps": 8430, "sleep_hours": 6.9, "resting_heart_rate": 58, ...},
        date="2026-03-18",
        user_baseline={...},
    )

The normalizer:
  1. Looks up the right ``DeviceAdapter`` from ``AdapterRegistry``.
  2. Calls ``adapter.to_canonical(raw_day, date, user_baseline)``.
  3. Calls ``compute_all_composites`` to fill in any aggregate scores that
     the device does not provide natively (readiness_score, activity_score,
     sleep_score, hrv_balance), skipping those already populated.
  4. Returns the combined list of ``NormalizedMetric`` objects.

The normalizer is intentionally stateless — it holds no user data and
performs no I/O.  Persistence (``Session 2``) is handled separately.

Source priority when the same canonical metric is returned by multiple
sources for the same day::

    oura > healthkit / health_connect > dexcom > other

The caller (correlation engine) can apply this priority when building the
``health_daily`` dict.  The normalizer returns ALL metrics from the
specified source for one call; cross-source deduplication happens upstream.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

# Import adapters package to trigger all @AdapterRegistry.register decorators
import common.metrics.adapters  # noqa: F401

from common.metrics.adapters.base import AdapterRegistry, NormalizedMetric
from common.metrics.composite_scores import compute_all_composites
from common.metrics.registry import CANONICAL_METRICS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Source priority for cross-source deduplication
# Higher = more trusted when multiple sources report the same metric
# ---------------------------------------------------------------------------

SOURCE_PRIORITY: Dict[str, int] = {
    "oura": 100,
    "whoop": 80,
    "garmin": 80,
    "fitbit": 70,
    "healthkit": 60,
    "health_connect": 60,
    "dexcom": 90,  # highest for glucose metrics specifically
    "blood_pressure": 85,
    "clinical": 90,
    "polar": 70,
    "samsung": 50,
}


class HealthNormalizer:
    """
    Converts raw device data to canonical NormalizedMetric objects.

    Thread-safe: holds no mutable state — safe to use as a singleton.
    """

    def normalize(
        self,
        source: str,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        """
        Normalise one day of raw device data from *source*.

        Parameters
        ----------
        source:
            Source name matching ``native_health_data.source``
            (e.g. ``"oura"``, ``"healthkit"``).
        raw_day:
            Flat ``{field_name: scalar_value}`` dict.  Keys are
            device-specific; see individual adapter docstrings for details.
        date:
            ISO date string ``"YYYY-MM-DD"``.
        user_baseline:
            Rolling per-user statistics keyed by canonical metric name::

                {
                  "hrv_ms": {"mean_30d": 42.1, "std_30d": 8.3, "n": 28},
                  "body_temperature_c": {"mean_30d": 36.6, "std_30d": 0.2, "n": 30},
                  "resting_hr_bpm": {"mean_30d": 58.0, "std_30d": 4.1, "n": 30},
                  "steps": {"mean_30d": 8200.0},
                }

        Returns
        -------
        list[NormalizedMetric]
            Direct, derived, and composite metrics.  Unknown canonical names
            (from future adapter versions) are filtered out with a warning.
        """
        adapter = AdapterRegistry.get(source)
        if adapter is None:
            logger.warning(
                "HealthNormalizer: no adapter registered for source %r — skipping",
                source,
            )
            return []

        # Step 1: device adapter → direct + derived metrics
        try:
            direct_metrics = adapter.to_canonical(raw_day, date, user_baseline)
        except NotImplementedError:
            logger.debug(
                "HealthNormalizer: adapter for %r is a stub — no metrics produced",
                source,
            )
            return []
        except Exception:
            logger.exception(
                "HealthNormalizer: adapter %r raised an unexpected error for date %s",
                source,
                date,
            )
            return []

        # Step 2: filter out any unrecognised canonical metric names
        valid_metrics: List[NormalizedMetric] = []
        for m in direct_metrics:
            if m.canonical_metric not in CANONICAL_METRICS:
                logger.warning(
                    "HealthNormalizer: adapter %r produced unknown canonical metric %r "
                    "— skipped.  Add it to registry.py if intentional.",
                    source,
                    m.canonical_metric,
                )
            else:
                valid_metrics.append(m)

        # Step 3: composite scores — only for metrics not already populated
        already_have = {m.canonical_metric for m in valid_metrics}
        canonical_day = {m.canonical_metric: m.value for m in valid_metrics}

        composite_metrics = compute_all_composites(
            canonical_day=canonical_day,
            user_baseline=user_baseline,
            source=source,
            already_have=already_have,
        )

        all_metrics = valid_metrics + composite_metrics

        logger.debug(
            "HealthNormalizer: %s / %s → %d metrics (%d direct/derived, %d composite)",
            source,
            date,
            len(all_metrics),
            len(valid_metrics),
            len(composite_metrics),
        )
        return all_metrics

    def normalize_multi_source(
        self,
        days_data: Dict[str, Dict[str, dict]],
        user_baseline: dict,
    ) -> Dict[str, Dict[str, NormalizedMetric]]:
        """
        Normalise multiple days and sources, applying source priority to
        deduplicate metrics where multiple sources report the same canonical
        metric for the same day.

        Parameters
        ----------
        days_data:
            Nested dict::

                {
                  "2026-03-17": {
                    "oura":      {"sleep_score": 82, ...},
                    "healthkit": {"steps": 8430, ...},
                  },
                  "2026-03-18": { ... },
                }

        user_baseline:
            Same format as ``normalize()``.

        Returns
        -------
        Dict[date_str, Dict[canonical_metric, NormalizedMetric]]
            One ``NormalizedMetric`` per canonical metric per day, chosen
            by source priority.
        """
        result: Dict[str, Dict[str, NormalizedMetric]] = {}

        for date_str, sources in days_data.items():
            day_candidates: Dict[str, List[NormalizedMetric]] = {}

            for source, raw_day in sources.items():
                for metric in self.normalize(source, raw_day, date_str, user_baseline):
                    day_candidates.setdefault(metric.canonical_metric, []).append(
                        metric
                    )

            # Pick highest-priority source for each metric
            best: Dict[str, NormalizedMetric] = {}
            for canonical_name, candidates in day_candidates.items():
                candidates.sort(
                    key=lambda m: SOURCE_PRIORITY.get(m.source, 0), reverse=True
                )
                best[canonical_name] = candidates[0]

            if best:
                result[date_str] = best

        return result

    @staticmethod
    def to_flat_dict(
        normalized: Dict[str, NormalizedMetric],
    ) -> Dict[str, float]:
        """
        Convert a ``{canonical_metric: NormalizedMetric}`` day dict to a
        simple ``{canonical_metric: float}`` dict suitable for passing to
        the correlation engine.
        """
        return {k: v.value for k, v in normalized.items()}
