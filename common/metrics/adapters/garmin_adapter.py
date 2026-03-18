"""
Garmin adapter — STUB.

Garmin Connect API client is not yet implemented.

When implementing:
  * Garmin body_battery is 0–100 (native) → maps directly to ``body_battery``.
  * Garmin stress is 0–100 (native) → maps directly to ``stress_score``.
  * Garmin HRV = RMSSD during sleep → ``hrv_ms``.
  * Garmin sleep score 0–100 → ``sleep_score``.

Expected raw_day keys (once implemented):
    {
        "steps":                   9_800,
        "active_calories_kcal":    550.0,
        "active_min":              52.0,
        "vo2_max":                 43.0,
        "body_battery":            72.0,   # 0–100
        "stress_score":            28.0,   # 0–100
        "resting_heart_rate":      57.0,
        "hrv_rmssd_ms":            46.0,
        "sleep_score":             78.0,
        "sleep_duration_hours":    7.2,
        "deep_sleep_hours":        1.5,
        "rem_sleep_hours":         1.6,
        "spo2_pct":                98.0,
        "respiratory_rate":        14.8,
        "body_temperature_c":      36.5,
        "weight_kg":               75.0,
    }
"""

from __future__ import annotations

from typing import List

from common.metrics.adapters.base import (
    AdapterRegistry,
    DeviceAdapter,
    NormalizedMetric,
)


@AdapterRegistry.register
class GarminAdapter(DeviceAdapter):
    source_name = "garmin"

    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        # TODO: implement when Garmin Connect OAuth client is ready.
        raise NotImplementedError(
            "GarminAdapter is not yet implemented.  "
            "Wire up the Garmin Connect API client and complete this adapter "
            "following the pattern in oura_adapter.py."
        )
