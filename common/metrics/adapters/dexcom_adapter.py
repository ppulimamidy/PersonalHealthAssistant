"""
Dexcom CGM adapter.

Handles two modes:

Track A — Daily aggregates (available now)
    The normalizer pre-computes daily summary statistics from raw CGM
    readings and passes them as a flat dict.  This works immediately
    with the existing correlation engine once adapters are wired in.

Track B — Per-meal postprandial analysis (Session 5)
    When raw 5-minute readings are present alongside meal-log timestamps,
    ``common.metrics.postprandial.PostprandialAnalyzer`` computes
    per-meal glucose metrics.  This adapter does NOT handle Track B;
    Track B is computed by the postprandial module and stored separately
    with a ``meal_id`` reference.

Raw input dict (Track A — daily aggregates)
-------------------------------------------
The normalizer populates this dict from ``native_health_data`` rows where
``source = "dexcom"`` and from any ``blood_glucose`` rows from other sources
that have been pre-aggregated.

    {
        # Required for Track A
        "avg_glucose_mgdl":        105.3,  # daily mean
        "peak_glucose_mgdl":       178.0,  # daily max
        "time_in_range_pct":        89.0,  # % readings 70–180 mg/dL
        "glucose_variability_cv":   18.2,  # stddev / mean × 100
        "glucose_spikes_count":      0.0,  # readings > 180 mg/dL

        # Optional — available when raw readings array is pre-processed
        "min_glucose_mgdl":         82.0,
        "readings_count":          288.0,  # 288 = full day at 5-min intervals
    }

Confidence
----------
All Track A metrics from Dexcom CGM are direct measurements — confidence 1.0.
Blood glucose single-point readings (e.g. from Apple Health manual entry)
are also direct but have lower statistical power; confidence is preserved
as-is since we can't distinguish the method at this layer.
"""

from __future__ import annotations

from typing import List

from common.metrics.adapters.base import (
    AdapterRegistry,
    DeviceAdapter,
    NormalizedMetric,
)


@AdapterRegistry.register
class DexcomAdapter(DeviceAdapter):
    source_name = "dexcom"

    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        out: List[NormalizedMetric] = []
        src = self.source_name

        # ── Track A: Daily glucose aggregates ─────────────────────────────
        if (v := self._f(raw_day, "avg_glucose_mgdl")) is not None:
            out.append(self._direct("avg_glucose_mgdl", v, src, "avg_glucose_mgdl"))

        if (v := self._f(raw_day, "peak_glucose_mgdl")) is not None:
            out.append(self._direct("peak_glucose_mgdl", v, src, "peak_glucose_mgdl"))

        if (v := self._f_allow_zero(raw_day, "time_in_range_pct")) is not None:
            out.append(self._direct("time_in_range_pct", v, src, "time_in_range_pct"))

        if (v := self._f_allow_zero(raw_day, "glucose_variability_cv")) is not None:
            out.append(
                self._direct("glucose_variability_cv", v, src, "glucose_variability_cv")
            )

        if (v := self._f_allow_zero(raw_day, "glucose_spikes_count")) is not None:
            out.append(
                self._direct("glucose_spikes_count", v, src, "glucose_spikes_count")
            )

        # ── Fallback: plain blood_glucose reading ─────────────────────────
        # Used when a single daily reading is ingested (e.g. from a fingerstick
        # device or manual Apple Health entry with source re-mapped to dexcom).
        if not out:
            if (v := self._f(raw_day, "blood_glucose_mgdl")) is not None:
                out.append(self._direct("avg_glucose_mgdl", v, src, "blood_glucose"))

        return out
