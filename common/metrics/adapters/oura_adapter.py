"""
Oura Ring adapter.

Maps the flat dict produced by ``_extract_wearable_daily()`` in
``correlations.py`` to canonical metric names.

Raw input keys (produced by _extract_wearable_daily)
-------------------------------------------------
Sleep:
  sleep_score           0–100
  sleep_efficiency      %
  total_sleep_hours     hours (float)
  deep_sleep_hours      hours (float)

Activity:
  steps                 count
  active_calories       kcal
  activity_score        0–100

Readiness:
  readiness_score       0–100
  hrv_balance           Oura z-score vs personal baseline (direct)
  recovery_index        0–100
  resting_heart_rate    bpm
  temperature_deviation °C from baseline (direct, sleep-period skin temp)

Native wearable (may also come from timeline.native):
  respiratory_rate      breaths/min
  spo2                  %
  workout_minutes       min
  vo2_max               ml/kg/min
  hrv_sdnn              ms  (sometimes present from native passthrough)
"""

from __future__ import annotations

from typing import List

from common.metrics.adapters.base import (
    AdapterRegistry,
    DeviceAdapter,
    NormalizedMetric,
)
from common.metrics.registry import SourceType


@AdapterRegistry.register
class OuraAdapter(DeviceAdapter):
    source_name = "oura"

    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        out: List[NormalizedMetric] = []
        src = self.source_name

        # ── Sleep ─────────────────────────────────────────────────────────
        if (v := self._f(raw_day, "sleep_score")) is not None:
            out.append(self._direct("sleep_score", v, src, "sleep_score"))

        if (v := self._f(raw_day, "sleep_efficiency")) is not None:
            out.append(self._direct("sleep_efficiency_pct", v, src, "sleep_efficiency"))

        if (v := self._f(raw_day, "total_sleep_hours")) is not None:
            out.append(
                self._direct(
                    "sleep_duration_min", round(v * 60, 1), src, "total_sleep_hours"
                )
            )

        if (v := self._f(raw_day, "deep_sleep_hours")) is not None:
            out.append(
                self._direct(
                    "deep_sleep_min", round(v * 60, 1), src, "deep_sleep_hours"
                )
            )

        # ── Activity ──────────────────────────────────────────────────────
        if (v := self._f(raw_day, "steps")) is not None:
            out.append(self._direct("steps", v, src, "steps"))

        if (v := self._f(raw_day, "active_calories")) is not None:
            out.append(self._direct("active_calories_kcal", v, src, "active_calories"))

        if (v := self._f(raw_day, "activity_score")) is not None:
            out.append(self._direct("activity_score", v, src, "activity_score"))

        if (v := self._f(raw_day, "workout_minutes")) is not None:
            out.append(self._direct("active_min", v, src, "workout_minutes"))

        if (v := self._f(raw_day, "vo2_max")) is not None:
            out.append(self._direct("vo2_max", v, src, "vo2_max"))

        # ── Recovery ──────────────────────────────────────────────────────
        if (v := self._f(raw_day, "readiness_score")) is not None:
            out.append(self._direct("readiness_score", v, src, "readiness_score"))

        if (v := self._f(raw_day, "recovery_index")) is not None:
            out.append(self._direct("recovery_index", v, src, "recovery_index"))

        if (v := self._f(raw_day, "resting_heart_rate")) is not None:
            out.append(self._direct("resting_hr_bpm", v, src, "resting_heart_rate"))

        # hrv_balance — Oura computes this natively vs personal baseline
        if (v := self._f_allow_zero(raw_day, "hrv_balance")) is not None:
            out.append(self._direct("hrv_balance", v, src, "hrv_balance"))

        # hrv_sdnn (sometimes present as a pass-through from native data)
        if (v := self._f(raw_day, "hrv_sdnn")) is not None:
            out.append(self._direct("hrv_ms", v, src, "hrv_sdnn"))

        # temperature_deviation — Oura measures skin temp during sleep;
        # this is the most accurate source of body_temp_deviation_c
        if (v := self._f_allow_zero(raw_day, "temperature_deviation")) is not None:
            out.append(
                self._direct("body_temp_deviation_c", v, src, "temperature_deviation")
            )

        # ── Other vitals ──────────────────────────────────────────────────
        if (v := self._f(raw_day, "respiratory_rate")) is not None:
            out.append(self._direct("respiratory_rate_bpm", v, src, "respiratory_rate"))

        if (v := self._f(raw_day, "spo2")) is not None:
            out.append(self._direct("spo2_pct", v, src, "spo2"))

        return out
