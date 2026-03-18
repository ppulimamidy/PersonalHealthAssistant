"""
Fitbit adapter — STUB.

Fitbit Web API client is not yet implemented.

When implementing:
  * Fitbit HRV = daily RMSSD → ``hrv_ms``.
  * Fitbit sleep score 0–100 → ``sleep_score``.
  * Fitbit SpO2 = avg % → ``spo2_pct``.
  * Fitbit skin temperature deviation → ``body_temp_deviation_c`` (direct!
    Fitbit Sense/Versa 3+ measures this natively — confidence 0.9 vs
    Oura's 1.0 since sensor placement differs).

Expected raw_day keys (once implemented):
    {
        "steps":                   8_200,
        "active_calories_kcal":    490.0,
        "active_min":              38.0,
        "resting_heart_rate":      62.0,
        "hrv_rmssd_ms":            36.0,
        "sleep_score":             74.0,
        "sleep_duration_hours":    6.8,
        "sleep_efficiency_pct":    88.0,
        "deep_sleep_hours":        1.2,
        "rem_sleep_hours":         1.3,
        "spo2_pct":                97.0,
        "skin_temp_deviation_c":   0.3,  # Fitbit natively computes deviation
        "weight_kg":               71.0,
        "body_fat_pct":            23.0,
        "respiratory_rate":        15.5,
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
class FitbitAdapter(DeviceAdapter):
    source_name = "fitbit"

    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        # TODO: implement when Fitbit Web API OAuth client is ready.
        raise NotImplementedError(
            "FitbitAdapter is not yet implemented.  "
            "Wire up the Fitbit Web API client and complete this adapter "
            "following the pattern in oura_adapter.py."
        )
