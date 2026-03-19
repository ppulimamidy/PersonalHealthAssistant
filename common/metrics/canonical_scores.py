"""
Canonical Score Computation — Device-Agnostic Health Intelligence

Converts raw device-specific metrics into canonical 0-100 scores.
The intelligence layer (patterns, recommendations, interventions, efficacy)
reads ONLY canonical scores, never raw device metrics.

Canonical scores are relative to the user's personal baseline when available,
falling back to population defaults for new users (< 7 days of data).
"""

from typing import Any, Dict, List, Optional, Tuple

from common.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Population defaults (used when personal baseline not yet established)
# ---------------------------------------------------------------------------

POPULATION_DEFAULTS: Dict[str, Dict[str, float]] = {
    "hrv_sdnn": {"baseline": 50.0, "stddev": 15.0},
    "resting_heart_rate": {"baseline": 65.0, "stddev": 8.0},
    "sleep": {"baseline": 7.5, "stddev": 1.0},  # hours
    "steps": {"baseline": 7000.0, "stddev": 2000.0},
    "active_calories": {"baseline": 350.0, "stddev": 150.0},
    "spo2": {"baseline": 97.0, "stddev": 1.5},
    "respiratory_rate": {"baseline": 15.0, "stddev": 2.0},
    "temperature_deviation": {"baseline": 0.0, "stddev": 0.15},
    "workout": {"baseline": 30.0, "stddev": 15.0},  # minutes
    "vo2_max": {"baseline": 40.0, "stddev": 8.0},
}

# ---------------------------------------------------------------------------
# Canonical metric definitions
# ---------------------------------------------------------------------------

# Maps (source_metric, source) → (canonical_metric, derivation)
# "direct" = value is already 0-100, use as-is
# "derive" = compute from raw value + baseline

CANONICAL_MAPPING: Dict[str, Dict[str, Any]] = {
    # ── Sleep Quality (0-100) ─────────────────────────────────────────────
    "sleep_quality": {
        "sources": {
            "sleep_score": "direct",  # Oura: already 0-100
            "sleep": "derive_sleep",  # Apple Health: hours → score
        },
        "description": "Overall sleep quality score",
    },
    # ── HRV Health (0-100) ────────────────────────────────────────────────
    "hrv_health": {
        "sources": {
            "hrv_balance": "direct",  # Oura: already normalized
            "hrv_sdnn": "derive_hrv",  # Apple Health: ms → score
        },
        "description": "Heart rate variability relative to personal baseline",
    },
    # ── Recovery (0-100) ──────────────────────────────────────────────────
    "recovery": {
        "sources": {
            "readiness_score": "direct",  # Oura: already 0-100
            # For non-Oura: computed from sleep_quality + hrv_health + cardiac_stress
        },
        "description": "Overall recovery and readiness",
    },
    # ── Activity Level (0-100) ────────────────────────────────────────────
    "activity_level": {
        "sources": {
            "activity_score": "direct",  # Oura: already 0-100
            # For non-Oura: computed from steps + active_calories
        },
        "description": "Daily activity relative to goals",
    },
    # ── Cardiac Stress (0-100, higher = MORE stress) ──────────────────────
    "cardiac_stress": {
        "sources": {
            "resting_heart_rate": "derive_cardiac",
        },
        "description": "Cardiac stress indicator (higher = more stressed)",
    },
    # ── Temperature Trend (z-score, normalized) ───────────────────────────
    "temp_trend": {
        "sources": {
            "temperature_deviation": "derive_temp",
        },
        "description": "Body temperature deviation in standard deviations",
    },
    # ── Sleep Efficiency (0-100) ──────────────────────────────────────────
    "sleep_efficiency": {
        "sources": {
            "sleep_efficiency": "direct",  # Already 0-100 from any source
        },
        "description": "Percentage of time in bed actually asleep",
    },
    # ── Deep Sleep Percentage (0-100) ─────────────────────────────────────
    "deep_sleep_pct": {
        "sources": {
            "deep_sleep_hours": "derive_deep_sleep",
        },
        "description": "Deep sleep as percentage of total sleep",
    },
    # ── Glucose Stability (0-100, CGM users) ──────────────────────────────
    "glucose_stability": {
        "sources": {
            "glucose_variability_cv": "derive_glucose_stability",
        },
        "description": "Glucose stability (higher = more stable)",
    },
    # ── Time in Range (0-100, CGM users) ──────────────────────────────────
    "time_in_range": {
        "sources": {
            "time_in_range_pct": "direct",
        },
        "description": "Percentage of time glucose is in target range",
    },
}

# All canonical metric names
CANONICAL_METRICS = list(CANONICAL_MAPPING.keys())


# ---------------------------------------------------------------------------
# Score derivation functions
# ---------------------------------------------------------------------------


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _derive_sleep_quality(sleep_hours: float, baseline: float, stddev: float) -> float:
    """Convert sleep hours to a 0-100 quality score."""
    # 8 hours = 100, scale linearly with personal baseline adjustment
    goal = max(baseline, 7.0)  # at least 7h goal
    raw_score = (sleep_hours / goal) * 85  # 85 at goal
    # Bonus for exceeding goal, penalty for under
    if sleep_hours >= goal:
        raw_score = 85 + min((sleep_hours - goal) / 1.0, 1.0) * 15
    return _clamp(raw_score)


def _derive_hrv_health(hrv_ms: float, baseline: float, stddev: float) -> float:
    """Convert HRV in ms to a 0-100 health score relative to baseline."""
    if baseline <= 0:
        baseline = POPULATION_DEFAULTS["hrv_sdnn"]["baseline"]
    ratio = hrv_ms / baseline
    # At baseline = 75, above baseline = 75-100, below = 0-75
    score = ratio * 75
    return _clamp(score)


def _derive_cardiac_stress(rhr: float, baseline: float, stddev: float) -> float:
    """Convert resting HR to cardiac stress score (higher = MORE stressed)."""
    if baseline <= 0:
        baseline = POPULATION_DEFAULTS["resting_heart_rate"]["baseline"]
    if stddev <= 0:
        stddev = POPULATION_DEFAULTS["resting_heart_rate"]["stddev"]
    # At baseline = 30 (moderate), each stddev above = +15
    deviation = (rhr - baseline) / stddev
    score = 30 + deviation * 15
    return _clamp(score)


def _derive_temp_trend(temp_dev: float, baseline: float, stddev: float) -> float:
    """Convert temperature deviation to z-score (stored as 0-100 for consistency).
    50 = normal, >65 = elevated (>1σ), >80 = high (>2σ)."""
    if stddev <= 0:
        stddev = POPULATION_DEFAULTS["temperature_deviation"]["stddev"]
    z = (temp_dev - baseline) / stddev
    score = 50 + z * 15  # maps z-score to 50-centered scale
    return _clamp(score)


def _derive_deep_sleep_pct(deep_hours: float, sleep_hours: Optional[float]) -> float:
    """Convert deep sleep hours to percentage of total sleep."""
    if not sleep_hours or sleep_hours <= 0:
        sleep_hours = 7.5
    pct = (deep_hours / sleep_hours) * 100
    return _clamp(pct)


def _derive_glucose_stability(cv: float) -> float:
    """Convert glucose coefficient of variation to stability score.
    Lower CV = more stable = higher score."""
    # CV < 20% = excellent (90+), 20-36% = good (60-90), >36% = poor (<60)
    score = 100 - (cv * 2.5)
    return _clamp(score)


def _compute_recovery(
    sleep_quality: Optional[float],
    hrv_health: Optional[float],
    cardiac_stress: Optional[float],
) -> Optional[float]:
    """Derive recovery score from components when no direct readiness score."""
    components = []
    weights = []
    if sleep_quality is not None:
        components.append(sleep_quality)
        weights.append(0.4)
    if hrv_health is not None:
        components.append(hrv_health)
        weights.append(0.4)
    if cardiac_stress is not None:
        components.append(100 - cardiac_stress)  # invert: low stress = high recovery
        weights.append(0.2)
    if not components:
        return None
    total_weight = sum(weights)
    return _clamp(sum(c * w for c, w in zip(components, weights)) / total_weight)


def _compute_activity_level(
    steps: Optional[float],
    active_cal: Optional[float],
) -> Optional[float]:
    """Derive activity level from steps + active calories."""
    score = 0.0
    has_data = False
    if steps is not None:
        score += min(steps / 8000, 1.0) * 60
        has_data = True
    if active_cal is not None:
        score += min(active_cal / 400, 1.0) * 40
        has_data = True
    elif has_data:
        # Only steps available — scale to full range
        score = min(steps / 8000, 1.0) * 100 if steps else 0
    if not has_data:
        return None
    return _clamp(score)


# ---------------------------------------------------------------------------
# Main computation function
# ---------------------------------------------------------------------------


def compute_canonical_scores(
    summaries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute canonical 0-100 scores from health_metric_summaries rows.

    Args:
        summaries: List of health_metric_summaries rows (dicts with
                   metric_type, latest_value, personal_baseline, baseline_stddev, etc.)

    Returns:
        List of updates: [{metric_type, canonical_metric, canonical_score}, ...]
        to be upserted back into health_metric_summaries.
    """
    # Index summaries by metric_type for lookup
    by_type: Dict[str, Dict[str, Any]] = {}
    for s in summaries:
        by_type[s["metric_type"]] = s

    updates: List[Dict[str, Any]] = []
    computed_canonical: Dict[str, float] = {}  # for composite derivation

    # Pass 1: Direct mappings and simple derivations
    for canonical_name, config in CANONICAL_MAPPING.items():
        for source_metric, derivation in config["sources"].items():
            if source_metric not in by_type:
                continue

            row = by_type[source_metric]
            value = row.get("latest_value")
            if value is None:
                continue

            baseline = row.get("personal_baseline") or POPULATION_DEFAULTS.get(
                source_metric, {}
            ).get("baseline", 50.0)
            stddev = row.get("baseline_stddev") or POPULATION_DEFAULTS.get(
                source_metric, {}
            ).get("stddev", 10.0)

            score: Optional[float] = None

            if derivation == "direct":
                score = _clamp(float(value))
            elif derivation == "derive_sleep":
                score = _derive_sleep_quality(float(value), baseline, stddev)
            elif derivation == "derive_hrv":
                score = _derive_hrv_health(float(value), baseline, stddev)
            elif derivation == "derive_cardiac":
                score = _derive_cardiac_stress(float(value), baseline, stddev)
            elif derivation == "derive_temp":
                score = _derive_temp_trend(float(value), baseline, stddev)
            elif derivation == "derive_deep_sleep":
                sleep_row = by_type.get("sleep")
                sleep_hours = sleep_row.get("latest_value") if sleep_row else None
                score = _derive_deep_sleep_pct(float(value), sleep_hours)
            elif derivation == "derive_glucose_stability":
                score = _derive_glucose_stability(float(value))

            if score is not None:
                score = round(score, 1)
                computed_canonical[canonical_name] = score
                updates.append(
                    {
                        "metric_type": source_metric,
                        "canonical_metric": canonical_name,
                        "canonical_score": score,
                    }
                )
                break  # first matching source wins

    # Pass 2: Composite derivations (recovery, activity_level)
    if "recovery" not in computed_canonical:
        recovery = _compute_recovery(
            computed_canonical.get("sleep_quality"),
            computed_canonical.get("hrv_health"),
            computed_canonical.get("cardiac_stress"),
        )
        if recovery is not None:
            computed_canonical["recovery"] = round(recovery, 1)
            # Attach to the best available source metric
            for source in ["resting_heart_rate", "hrv_sdnn", "sleep"]:
                if source in by_type:
                    updates.append(
                        {
                            "metric_type": source,
                            "canonical_metric": "recovery",
                            "canonical_score": round(recovery, 1),
                        }
                    )
                    break

    if "activity_level" not in computed_canonical:
        activity = _compute_activity_level(
            by_type.get("steps", {}).get("latest_value"),
            by_type.get("active_calories", {}).get("latest_value"),
        )
        if activity is not None:
            computed_canonical["activity_level"] = round(activity, 1)
            for source in ["steps", "active_calories"]:
                if source in by_type:
                    updates.append(
                        {
                            "metric_type": source,
                            "canonical_metric": "activity_level",
                            "canonical_score": round(activity, 1),
                        }
                    )
                    break

    return updates


def get_canonical_summary(
    summaries: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Convenience: compute canonical scores and return as {canonical_metric: score} dict.
    """
    updates = compute_canonical_scores(summaries)
    result: Dict[str, float] = {}
    for u in updates:
        cm = u["canonical_metric"]
        if cm not in result:  # first source wins
            result[cm] = u["canonical_score"]
    return result
