"""
Whoop adapter — STUB.

Whoop API client is not yet implemented.  This stub registers the source
name so the ``AdapterRegistry`` knows about it and raises a clear error
rather than silently ignoring data.

When implementing:
  * Whoop strain is 0–21; normalise to 0–100 via ``strain / 21 * 100``.
  * Whoop recovery is already 0–100 (percentage).
  * Whoop HRV = RMSSD (same as Oura) → maps directly to ``hrv_ms``.
  * Whoop sleep performance % → ``sleep_score``.

Expected raw_day keys (once implemented):
    {
        "strain":              14.2,   # 0–21 → normalised to 67.6 / 100
        "recovery_pct":        72.0,   # 0–100
        "hrv_rmssd_ms":        48.0,
        "resting_heart_rate":  54.0,
        "skin_temp_celsius":   36.4,
        "sleep_performance_pct": 85.0,
        "sleep_duration_hours": 7.5,
        "deep_sleep_hours":    1.8,
        "rem_sleep_hours":     1.4,
        "sleep_efficiency_pct": 90.0,
        "respiratory_rate":    15.2,
        "spo2_pct":            97.0,
        "active_calories_kcal": 620.0,
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
class WhoopAdapter(DeviceAdapter):
    source_name = "whoop"

    # Whoop strain scale maximum
    _WHOOP_STRAIN_MAX = 21.0

    def to_canonical(
        self,
        raw_day: dict,
        date: str,
        user_baseline: dict,
    ) -> List[NormalizedMetric]:
        # TODO (Session ~6): implement when Whoop OAuth client is ready.
        # Keeping the method signature correct so any accidental call fails
        # loudly rather than silently returning empty results.
        raise NotImplementedError(
            "WhoopAdapter is not yet implemented.  "
            "Wire up the Whoop OAuth client and complete this adapter "
            "following the pattern in oura_adapter.py."
        )
