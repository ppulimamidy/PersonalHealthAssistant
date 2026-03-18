"""
Google Health Connect adapter.

Maps native_health_data rows with ``source = "health_connect"`` to
canonical metric names.

Health Connect and HealthKit expose very similar metric types through our
ingest endpoint, so this adapter mirrors ``AppleHealthAdapter`` almost
exactly.  Differences:

* Health Connect reports ``HeartRateVariabilityRmssd`` (RMSSD), not SDNN.
  We store this as ``hrv_ms`` with ``raw_metric = "hrv_rmssd"``.
* Health Connect natively supports a ``stress`` metric type.
* Temperature reporting is less common but supported.

Raw input dict keys (same conventions as AppleHealthAdapter)::

    {
        "steps":                          9_100,
        "sleep_hours":                    7.3,
        "resting_heart_rate":             60.0,
        "hrv_rmssd_ms":                   38.0,   # RMSSD (Health Connect native)
        "spo2_pct":                       98.0,
        "respiratory_rate":               15.0,
        "active_calories_kcal":           520.0,
        "workout_minutes":                40.0,
        "vo2_max":                        40.1,
        "stress_score":                   34.0,   # 0–100, Health Connect native
        "blood_glucose_mgdl":             102.0,
        "body_temperature_c":             36.6,
        "weight_kg":                      74.0,
        "body_fat_pct":                   21.5,
        "blood_pressure_systolic_mmhg":   120.0,
        "blood_pressure_diastolic_mmhg":  78.0,
    }
"""

from __future__ import annotations

from typing import List, Optional

from common.metrics.adapters.base import (
    AdapterRegistry,
    DeviceAdapter,
    NormalizedMetric,
)
from common.metrics.registry import SourceType


@AdapterRegistry.register
class HealthConnectAdapter(DeviceAdapter):
    source_name = "health_connect"

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

        # Health Connect reports RMSSD (more aligned with Oura than SDNN)
        if (v := self._f(raw_day, "hrv_rmssd_ms")) is not None:
            out.append(self._direct("hrv_ms", v, src, "hrv_rmssd"))

        if (v := self._f(raw_day, "spo2_pct")) is not None:
            out.append(self._direct("spo2_pct", v, src, "spo2"))

        if (v := self._f(raw_day, "respiratory_rate")) is not None:
            out.append(self._direct("respiratory_rate_bpm", v, src, "respiratory_rate"))

        # Health Connect native stress score (0–100)
        if (v := self._f(raw_day, "stress_score")) is not None:
            out.append(self._direct("stress_score", v, src, "stress_score"))

        # ── Body composition ──────────────────────────────────────────────
        if (v := self._f(raw_day, "weight_kg")) is not None:
            out.append(self._direct("weight_kg", v, src, "weight"))

        if (v := self._f(raw_day, "body_fat_pct")) is not None:
            out.append(self._direct("body_fat_pct", v, src, "body_fat"))

        if (v := self._f(raw_day, "body_temperature_c")) is not None:
            out.append(self._direct("body_temperature_c", v, src, "body_temperature"))

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
        if (v := self._f(raw_day, "blood_glucose_mgdl")) is not None:
            out.append(self._direct("avg_glucose_mgdl", v, src, "blood_glucose"))

        return out

    def _derive_temp_deviation(
        self, today_temp: float, user_baseline: dict
    ) -> Optional[float]:
        bline = user_baseline.get("body_temperature_c", {})
        mean = bline.get("mean_30d")
        n = bline.get("n", 0)
        if mean is None or n < self._MIN_TEMP_BASELINE_DAYS:
            return None
        return max(-3.0, min(3.0, round(today_temp - mean, 3)))
