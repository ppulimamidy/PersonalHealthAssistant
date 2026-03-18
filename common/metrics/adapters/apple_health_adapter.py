"""
Apple Health (HealthKit) adapter.

Maps native_health_data rows with ``source = "healthkit"`` to canonical
metric names.

Raw input dict format
---------------------
The normalizer pre-extracts the primary scalar from each row's ``value_json``
using the ``_PRIMARY_KEY`` mapping in ``health_data.py``.  The resulting
``raw_day`` dict passed to this adapter is::

    {
        "steps":               8_430,
        "sleep_hours":         6.9,      # from metric_type "sleep", value_json.hours
        "resting_heart_rate":  58.0,     # bpm
        "hrv_sdnn_ms":         44.0,     # ms  (Apple Health reports SDNN)
        "spo2_pct":            97.0,
        "respiratory_rate":    14.5,
        "active_calories_kcal": 480.0,
        "workout_minutes":     35.0,
        "vo2_max":             42.5,
        "blood_glucose_mgdl":  105.0,
        "body_temperature_c":  36.7,
        "weight_kg":           72.4,
        "body_fat_pct":        22.1,
        "blood_pressure_systolic_mmhg": 118.0,
        "blood_pressure_diastolic_mmhg": 76.0,
    }

Note on HRV: Apple Health records ``HKQuantityTypeIdentifierHeartRateVariabilitySDNN``
which is SDNN, not RMSSD.  Both are stored as ``hrv_ms`` with the distinction
preserved in ``raw_metric`` (``"hrv_sdnn"``).

Note on temperature: Apple Health measures wrist/body temperature but does
not compute a deviation from baseline.  ``body_temp_deviation_c`` is
therefore a derived metric computed by the normalizer / composite_scores
after accumulating a 30-day rolling baseline.
"""

from __future__ import annotations

import math
from typing import List, Optional

from common.metrics.adapters.base import (
    AdapterRegistry,
    DeviceAdapter,
    NormalizedMetric,
)
from common.metrics.registry import SourceType


@AdapterRegistry.register
class AppleHealthAdapter(DeviceAdapter):
    source_name = "healthkit"

    # Minimum days of body_temperature_c history required before we trust
    # the derived body_temp_deviation_c value.
    _MIN_TEMP_BASELINE_DAYS = 7

    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        out: List[NormalizedMetric] = []
        src = self.source_name

        # ── Activity ──────────────────────────────────────────────────────
        if (v := self._f(raw_day, "steps")) is not None:
            out.append(self._direct("steps", v, src, "steps"))

        if (v := self._f(raw_day, "active_calories_kcal")) is not None:
            out.append(
                self._direct("active_calories_kcal", v, src, "active_calories_kcal")
            )

        if (v := self._f(raw_day, "workout_minutes")) is not None:
            out.append(self._direct("active_min", v, src, "workout_minutes"))

        if (v := self._f(raw_day, "vo2_max")) is not None:
            out.append(self._direct("vo2_max", v, src, "vo2_max"))

        # ── Sleep ─────────────────────────────────────────────────────────
        if (v := self._f(raw_day, "sleep_hours")) is not None:
            out.append(
                self._direct("sleep_duration_min", round(v * 60, 1), src, "sleep_hours")
            )

        # ── Recovery ──────────────────────────────────────────────────────
        if (v := self._f(raw_day, "resting_heart_rate")) is not None:
            out.append(self._direct("resting_hr_bpm", v, src, "resting_heart_rate"))

        # Apple Health HRV = SDNN — stored as hrv_ms with raw_metric=hrv_sdnn
        if (v := self._f(raw_day, "hrv_sdnn_ms")) is not None:
            out.append(self._direct("hrv_ms", v, src, "hrv_sdnn"))

        if (v := self._f(raw_day, "spo2_pct")) is not None:
            out.append(self._direct("spo2_pct", v, src, "spo2"))

        if (v := self._f(raw_day, "respiratory_rate")) is not None:
            out.append(self._direct("respiratory_rate_bpm", v, src, "respiratory_rate"))

        # ── Body composition ──────────────────────────────────────────────
        if (v := self._f(raw_day, "weight_kg")) is not None:
            out.append(self._direct("weight_kg", v, src, "weight"))

        if (v := self._f(raw_day, "body_fat_pct")) is not None:
            out.append(self._direct("body_fat_pct", v, src, "body_fat"))

        # Absolute body temperature — direct measurement (used to derive deviation)
        if (v := self._f(raw_day, "body_temperature_c")) is not None:
            out.append(self._direct("body_temperature_c", v, src, "body_temperature"))

            # Derive body_temp_deviation_c from the 30-day rolling baseline
            deviation = self._derive_temp_deviation(v, user_baseline)
            if deviation is not None:
                baseline = user_baseline.get("body_temperature_c", {})
                out.append(
                    self._derived(
                        "body_temp_deviation_c",
                        deviation,
                        src,
                        raw_metric="body_temperature",
                        confidence=0.70,
                        baseline_used={
                            "mean_30d": baseline.get("mean_30d"),
                            "n": baseline.get("n"),
                        },
                    )
                )

        # ── Cardiovascular ────────────────────────────────────────────────
        if (v := self._f(raw_day, "blood_pressure_systolic_mmhg")) is not None:
            out.append(
                self._direct(
                    "blood_pressure_systolic_mmhg", v, src, "blood_pressure_systolic"
                )
            )

        if (v := self._f(raw_day, "blood_pressure_diastolic_mmhg")) is not None:
            out.append(
                self._direct(
                    "blood_pressure_diastolic_mmhg", v, src, "blood_pressure_diastolic"
                )
            )

        # ── Glucose ───────────────────────────────────────────────────────
        # Apple Health can record individual blood glucose readings.
        # The normalizer pre-aggregates to daily mean before passing here.
        if (v := self._f(raw_day, "blood_glucose_mgdl")) is not None:
            out.append(self._direct("avg_glucose_mgdl", v, src, "blood_glucose"))

        return out

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _derive_temp_deviation(
        self, today_temp: float, user_baseline: dict
    ) -> Optional[float]:
        """
        Compute temperature deviation = today − 30d mean.

        Returns None when the baseline has fewer than ``_MIN_TEMP_BASELINE_DAYS``
        data points (not enough history to trust the baseline).
        """
        bline = user_baseline.get("body_temperature_c", {})
        mean = bline.get("mean_30d")
        n = bline.get("n", 0)
        if mean is None or n < self._MIN_TEMP_BASELINE_DAYS:
            return None
        deviation = today_temp - mean
        # Clamp to physiologically plausible range
        return max(-3.0, min(3.0, round(deviation, 3)))
