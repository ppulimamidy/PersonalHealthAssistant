"""
Composite score computation for devices that lack native aggregate scores.

Functions here are called by ``HealthNormalizer`` after the adapter has
produced its direct/derived metrics.  They fill in scores that a device
does not provide natively (e.g. Oura provides ``readiness_score`` natively;
Apple Health does not, so we compute one from the canonical metrics we do
have).

Each function:
  * Accepts a ``canonical_day`` dict: ``{canonical_metric_name: float}``
    reflecting the already-normalised values for one day.
  * Accepts ``user_baseline``: rolling per-user statistics.
  * Returns a list of ``NormalizedMetric`` with
    ``source_type = COMPUTED_COMPOSITE``.
  * Returns an empty list if insufficient input metrics are available.

Confidence levels
-----------------
* ``hrv_balance`` derived from ``hrv_ms``:  ``min(n / 30, 1.0)``
* ``readiness_score`` composite:            0.55 (three inputs) / 0.45 (two)
* ``activity_score`` composite:             0.60 (three inputs) / 0.50 (two)
* ``sleep_score`` composite:                0.55 (two inputs)   / 0.45 (one)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from common.metrics.adapters.base import NormalizedMetric
from common.metrics.registry import SourceType


# ---------------------------------------------------------------------------
# HRV balance
# ---------------------------------------------------------------------------


def compute_hrv_balance(
    canonical_day: Dict[str, float],
    user_baseline: dict,
    source: str,
) -> List[NormalizedMetric]:
    """
    Derive ``hrv_balance`` (z-score vs 30-day personal baseline) from
    ``hrv_ms`` when the device does not provide it natively (i.e. any
    non-Oura device).

    Requires at least 14 days of ``hrv_ms`` history in ``user_baseline``.
    """
    hrv_today = canonical_day.get("hrv_ms")
    if hrv_today is None:
        return []

    bline = user_baseline.get("hrv_ms", {})
    mean = bline.get("mean_30d")
    std = bline.get("std_30d")
    n = bline.get("n", 0)

    if mean is None or std is None or n < 14:
        return []

    if std < 0.5:
        # Essentially no variability in baseline — z-score not meaningful
        return []

    z = (hrv_today - mean) / std
    z = max(-3.0, min(3.0, round(z, 3)))
    confidence = min(n / 30, 1.0)

    return [
        NormalizedMetric(
            canonical_metric="hrv_balance",
            value=z,
            source=source,
            source_type=SourceType.DERIVED,
            raw_metric="hrv_ms",
            confidence=round(confidence, 3),
            baseline_used={"mean_30d": mean, "std_30d": std, "n": n},
        )
    ]


# ---------------------------------------------------------------------------
# Readiness score
# ---------------------------------------------------------------------------

# Weights used when all three primary inputs are available.
_READINESS_WEIGHTS_FULL = {
    "hrv_balance": 0.35,
    "resting_hr_trend": 0.30,  # derived internally from resting_hr_bpm
    "sleep_score": 0.20,
    "body_temp_deviation_c": 0.15,
}

_READINESS_WEIGHTS_NO_TEMP = {
    "hrv_balance": 0.40,
    "resting_hr_trend": 0.35,
    "sleep_score": 0.25,
}

_READINESS_WEIGHTS_NO_HRV = {
    "sleep_score": 0.50,
    "resting_hr_trend": 0.30,
    "spo2_pct": 0.20,
}


def compute_readiness_score(
    canonical_day: Dict[str, float],
    user_baseline: dict,
    source: str,
) -> List[NormalizedMetric]:
    """
    Compute a composite readiness score (0–100) when the device does not
    provide one natively.

    Logic:
    1. Normalise each available input to 0–1 using its known range / baseline.
    2. Apply weights based on which inputs are available.
    3. Scale result to 0–100.

    Returns empty if fewer than two input metrics are available.
    """
    hrv_bal = canonical_day.get("hrv_balance")
    sleep_sc = canonical_day.get("sleep_score")
    rhr = canonical_day.get("resting_hr_bpm")
    temp_dev = canonical_day.get("body_temp_deviation_c")
    spo2 = canonical_day.get("spo2_pct")

    # Derive resting HR trend score: lower HR vs baseline = higher readiness
    rhr_trend = _rhr_trend_score(rhr, user_baseline)

    # ── Select weighting scheme based on available inputs ─────────────────
    if hrv_bal is not None and rhr_trend is not None and sleep_sc is not None:
        score, n_inputs = _readiness_from_full(hrv_bal, rhr_trend, sleep_sc, temp_dev)
        confidence = 0.55 if temp_dev is not None else 0.50
    elif hrv_bal is not None and rhr_trend is not None:
        score = _weighted([(_normalise_hrv_balance(hrv_bal), 0.55), (rhr_trend, 0.45)])
        n_inputs, confidence = 2, 0.45
    elif sleep_sc is not None and rhr_trend is not None:
        score = _weighted(
            [
                (_normalise_sleep(sleep_sc), 0.55),
                (rhr_trend, 0.30),
                (_normalise_spo2(spo2) if spo2 else 0.5, 0.15),
            ]
        )
        n_inputs, confidence = 2, 0.40
    else:
        return []

    score_100 = max(0.0, min(100.0, round(score * 100, 1)))
    return [
        NormalizedMetric(
            canonical_metric="readiness_score",
            value=score_100,
            source=source,
            source_type=SourceType.COMPUTED_COMPOSITE,
            raw_metric=None,
            confidence=confidence,
            baseline_used={"rhr_baseline": user_baseline.get("resting_hr_bpm")},
        )
    ]


# ---------------------------------------------------------------------------
# Activity score
# ---------------------------------------------------------------------------

# Personal targets used for normalisation (sensible defaults; will improve
# once we have per-user activity goal data).
_DEFAULT_STEP_TARGET = 8_000
_DEFAULT_ACTIVE_MIN_TARGET = 30
_DEFAULT_ACTIVE_CAL_TARGET = 400


def compute_activity_score(
    canonical_day: Dict[str, float],
    user_baseline: dict,
    source: str,
) -> List[NormalizedMetric]:
    """
    Compute a composite activity score (0–100) for devices that do not
    provide one natively (Apple Health, Health Connect, Dexcom, etc.).

    Formula::

        0.40 × (steps / step_target)
      + 0.30 × (active_min / 30)
      + 0.20 × (active_calories / cal_target)
      + 0.10 × vo2_max_normalised   (if available)

    All components are clamped to [0, 1] before weighting.
    Returns empty if no activity metrics are available.
    """
    steps = canonical_day.get("steps")
    active_min = canonical_day.get("active_min")
    active_cal = canonical_day.get("active_calories_kcal")
    vo2 = canonical_day.get("vo2_max")

    parts: list[tuple[float, float]] = []

    if steps is not None:
        step_target = (
            user_baseline.get("steps", {}).get("mean_30d") or _DEFAULT_STEP_TARGET
        )
        parts.append((_clamp(steps / max(step_target, 1)), 0.40))

    if active_min is not None:
        parts.append((_clamp(active_min / _DEFAULT_ACTIVE_MIN_TARGET), 0.30))

    if active_cal is not None:
        cal_target = (
            user_baseline.get("active_calories_kcal", {}).get("mean_30d")
            or _DEFAULT_ACTIVE_CAL_TARGET
        )
        parts.append((_clamp(active_cal / max(cal_target, 1)), 0.20))

    if vo2 is not None:
        # VO2max of 50 = elite-ish; normalise to 0–1 across 10–70 range
        parts.append((_clamp((vo2 - 10) / 60), 0.10))

    if not parts:
        return []

    # Re-normalise weights to sum to 1.0 given available components
    total_weight = sum(w for _, w in parts)
    score = sum(v * w / total_weight for v, w in parts)
    score_100 = max(0.0, min(100.0, round(score * 100, 1)))
    n_inputs = len(parts)
    confidence = 0.60 if n_inputs >= 3 else 0.50

    return [
        NormalizedMetric(
            canonical_metric="activity_score",
            value=score_100,
            source=source,
            source_type=SourceType.COMPUTED_COMPOSITE,
            raw_metric=None,
            confidence=confidence,
            baseline_used=None,
        )
    ]


# ---------------------------------------------------------------------------
# Sleep score
# ---------------------------------------------------------------------------


def compute_sleep_score(
    canonical_day: Dict[str, float],
    user_baseline: dict,
    source: str,
) -> List[NormalizedMetric]:
    """
    Compute a composite sleep score (0–100) for devices that do not provide
    one natively.

    Uses ``sleep_duration_min`` and ``sleep_efficiency_pct``.  If deep sleep
    or REM is available, they contribute a small bonus.

    Returns empty if neither duration nor efficiency is available.
    """
    duration_min = canonical_day.get("sleep_duration_min")
    efficiency = canonical_day.get("sleep_efficiency_pct")
    deep_min = canonical_day.get("deep_sleep_min")
    rem_min = canonical_day.get("rem_sleep_min")

    parts: list[tuple[float, float]] = []

    if duration_min is not None:
        # 7–8 h = optimal; normalise: 480 min = 1.0; penalise < 6 h or > 9 h
        optimal_min = 450.0  # 7.5 h
        penalty = abs(duration_min - optimal_min) / optimal_min
        dur_score = max(0.0, 1.0 - penalty)
        parts.append((dur_score, 0.50))

    if efficiency is not None:
        parts.append((_clamp(efficiency / 100.0), 0.35))

    if deep_min is not None and duration_min and duration_min > 0:
        # Deep sleep should be ~15-20% of total; 20% = 1.0
        deep_pct = deep_min / duration_min
        parts.append((_clamp(deep_pct / 0.20), 0.10))

    if rem_min is not None and duration_min and duration_min > 0:
        # REM should be ~20-25% of total
        rem_pct = rem_min / duration_min
        parts.append((_clamp(rem_pct / 0.22), 0.05))

    if not parts:
        return []

    total_weight = sum(w for _, w in parts)
    score = sum(v * w / total_weight for v, w in parts)
    score_100 = max(0.0, min(100.0, round(score * 100, 1)))
    confidence = 0.55 if len(parts) >= 2 else 0.45

    return [
        NormalizedMetric(
            canonical_metric="sleep_score",
            value=score_100,
            source=source,
            source_type=SourceType.COMPUTED_COMPOSITE,
            raw_metric=None,
            confidence=confidence,
            baseline_used=None,
        )
    ]


# ---------------------------------------------------------------------------
# Orchestrator — run all composites for one day
# ---------------------------------------------------------------------------


def compute_all_composites(
    canonical_day: Dict[str, float],
    user_baseline: dict,
    source: str,
    already_have: set[str],
) -> List[NormalizedMetric]:
    """
    Compute all applicable composite metrics for one day, skipping any
    that are already present in *already_have* (direct or derived values
    from the adapter take priority over computed composites).

    Parameters
    ----------
    canonical_day:
        Dict of canonical_metric → value for metrics already normalised
        by the adapter for this day.
    user_baseline:
        Per-user rolling stats (see ``DeviceAdapter.to_canonical`` docstring).
    source:
        Source name to tag the composite metrics with.
    already_have:
        Set of canonical metric names already present for this source/day.
        Composites are skipped for any metric in this set.
    """
    out: List[NormalizedMetric] = []

    if "hrv_balance" not in already_have:
        out.extend(compute_hrv_balance(canonical_day, user_baseline, source))

    if "readiness_score" not in already_have:
        out.extend(compute_readiness_score(canonical_day, user_baseline, source))

    if "activity_score" not in already_have:
        out.extend(compute_activity_score(canonical_day, user_baseline, source))

    if "sleep_score" not in already_have:
        out.extend(compute_sleep_score(canonical_day, user_baseline, source))

    return out


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _weighted(pairs: list[tuple[float, float]]) -> float:
    """Weighted average; weights need not sum to 1 (normalised internally)."""
    total_w = sum(w for _, w in pairs)
    if total_w == 0:
        return 0.5
    return sum(v * w for v, w in pairs) / total_w


def _normalise_hrv_balance(z: float) -> float:
    """Map z-score −3…+3 to 0–1 linearly."""
    return _clamp((z + 3.0) / 6.0)


def _normalise_sleep(score: float) -> float:
    return _clamp(score / 100.0)


def _normalise_spo2(spo2: float) -> float:
    """95–100% is normal; below 90% is critical."""
    return _clamp((spo2 - 85.0) / 15.0)


def _rhr_trend_score(rhr: Optional[float], user_baseline: dict) -> Optional[float]:
    """
    Convert resting HR to a 0–1 readiness component.

    Lower HR vs personal baseline = higher readiness.
    Returns None when no resting HR or no baseline available.
    """
    if rhr is None:
        return None
    bline = user_baseline.get("resting_hr_bpm", {})
    mean = bline.get("mean_30d")
    std = bline.get("std_30d")
    if mean is None:
        # No baseline — use absolute scale: 45 bpm = 1.0, 90 bpm = 0.0
        return _clamp(1.0 - (rhr - 45.0) / 45.0)
    # z-score: lower HR (negative z) = better
    if std and std > 0:
        z = (mean - rhr) / std  # positive when HR is below baseline
    else:
        z = 0.0
    return _clamp((z + 2.0) / 4.0)  # map −2…+2 z → 0–1


def _readiness_from_full(
    hrv_bal: float,
    rhr_trend: float,
    sleep_sc: float,
    temp_dev: Optional[float],
) -> tuple[float, int]:
    parts: list[tuple[float, float]] = [
        (_normalise_hrv_balance(hrv_bal), 0.35),
        (rhr_trend, 0.30),
        (_normalise_sleep(sleep_sc), 0.20),
    ]
    if temp_dev is not None:
        # Smaller absolute deviation = better readiness
        temp_norm = _clamp(1.0 - abs(temp_dev) / 2.0)
        parts.append((temp_norm, 0.15))
    return _weighted(parts), len(parts)
