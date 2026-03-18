"""
Canonical health metric registry.

Every health metric used by the analytics engine is represented by a
canonical name (e.g. ``hrv_ms``, ``sleep_score``).  Device adapters map
raw, device-specific field names to these canonical names.  The
correlation engine only ever operates on canonical names, making it
completely device-agnostic.

Adding a new device:
    1. Write an adapter in ``common/metrics/adapters/``.
    2. Register it with ``AdapterRegistry.register(MyAdapter)``.
    3. No changes to the correlation engine required.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class MetricCategory(str, Enum):
    SLEEP = "sleep"
    RECOVERY = "recovery"
    ACTIVITY = "activity"
    GLUCOSE = "glucose"
    CARDIOVASCULAR = "cardiovascular"
    BODY_COMPOSITION = "body_composition"
    SYMPTOM = "symptom"


class SourceType(str, Enum):
    """How a normalised metric value was obtained."""

    DIRECT = "direct"
    # Measured directly by the device (highest confidence).

    DERIVED = "derived"
    # Computed from direct measurements of the same device
    # (e.g. temperature deviation = today_temp − rolling_baseline).
    # Confidence is typically 0.7.

    COMPUTED_COMPOSITE = "computed_composite"
    # Computed from multiple canonical metrics sourced from the same or
    # different devices (e.g. readiness_score = weighted(hrv_balance,
    # resting_hr_bpm, sleep_score)).
    # Confidence is typically 0.5–0.6.


# ---------------------------------------------------------------------------
# Canonical metric definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CanonicalMetric:
    """Immutable description of one canonical health metric."""

    name: str
    category: MetricCategory
    unit: str
    description: str
    value_range: Optional[Tuple[float, float]] = None
    # (min, max) when the metric has a natural bounded range; None otherwise.
    higher_is_better: Optional[bool] = None
    # True / False when direction is clear; None when context-dependent.


# ---------------------------------------------------------------------------
# Full canonical metric catalogue
# ---------------------------------------------------------------------------

CANONICAL_METRICS: Dict[str, CanonicalMetric] = {
    # ── Sleep ────────────────────────────────────────────────────────────────
    "sleep_score": CanonicalMetric(
        "sleep_score",
        MetricCategory.SLEEP,
        "0–100",
        "Composite sleep quality score; native for Oura/Fitbit, computed composite for others",
        (0, 100),
        True,
    ),
    "sleep_duration_min": CanonicalMetric(
        "sleep_duration_min",
        MetricCategory.SLEEP,
        "min",
        "Total sleep duration in minutes",
        (0, 960),
        True,
    ),
    "deep_sleep_min": CanonicalMetric(
        "deep_sleep_min",
        MetricCategory.SLEEP,
        "min",
        "Deep (slow-wave) sleep duration in minutes",
        (0, 240),
        True,
    ),
    "rem_sleep_min": CanonicalMetric(
        "rem_sleep_min",
        MetricCategory.SLEEP,
        "min",
        "REM sleep duration in minutes",
        (0, 240),
        True,
    ),
    "light_sleep_min": CanonicalMetric(
        "light_sleep_min",
        MetricCategory.SLEEP,
        "min",
        "Light sleep duration in minutes",
        (0, 480),
        None,
    ),
    "sleep_efficiency_pct": CanonicalMetric(
        "sleep_efficiency_pct",
        MetricCategory.SLEEP,
        "%",
        "Percentage of time in bed actually spent asleep",
        (0, 100),
        True,
    ),
    "sleep_latency_min": CanonicalMetric(
        "sleep_latency_min",
        MetricCategory.SLEEP,
        "min",
        "Time from lights-out to sleep onset",
        (0, 120),
        False,
    ),
    "sleep_disturbances": CanonicalMetric(
        "sleep_disturbances",
        MetricCategory.SLEEP,
        "count",
        "Number of awakenings during the night",
        (0, 50),
        False,
    ),
    # ── Recovery ─────────────────────────────────────────────────────────────
    "readiness_score": CanonicalMetric(
        "readiness_score",
        MetricCategory.RECOVERY,
        "0–100",
        "Overall daily readiness / recovery score; native for Oura, computed composite for others",
        (0, 100),
        True,
    ),
    "hrv_ms": CanonicalMetric(
        "hrv_ms",
        MetricCategory.RECOVERY,
        "ms",
        (
            "Heart rate variability in milliseconds.  "
            "Oura/Whoop/Garmin report RMSSD; Apple Health reports SDNN.  "
            "Both are stored as hrv_ms with the measurement method noted in raw_metric."
        ),
        (0, 200),
        True,
    ),
    "hrv_balance": CanonicalMetric(
        "hrv_balance",
        MetricCategory.RECOVERY,
        "z-score",
        (
            "HRV relative to the user's personal 30-day baseline "
            "(positive = above average).  "
            "Native for Oura; derived from hrv_ms rolling baseline for other devices "
            "(confidence = min(days_available / 30, 1.0), requires ≥14 days)."
        ),
        (-3.0, 3.0),
        True,
    ),
    "resting_hr_bpm": CanonicalMetric(
        "resting_hr_bpm",
        MetricCategory.RECOVERY,
        "bpm",
        "Resting heart rate in beats per minute",
        (30, 120),
        False,
    ),
    "body_temp_deviation_c": CanonicalMetric(
        "body_temp_deviation_c",
        MetricCategory.RECOVERY,
        "°C",
        (
            "Body temperature deviation from personal baseline in °C.  "
            "Oura = direct sleep-period skin temperature (confidence 1.0).  "
            "Apple Health / others = derived from 30-day body_temperature_c baseline "
            "(confidence 0.7, flagged as source_type=derived)."
        ),
        (-2.0, 2.0),
        None,
    ),
    "respiratory_rate_bpm": CanonicalMetric(
        "respiratory_rate_bpm",
        MetricCategory.RECOVERY,
        "breaths/min",
        "Resting respiratory rate in breaths per minute",
        (8, 30),
        None,
    ),
    "spo2_pct": CanonicalMetric(
        "spo2_pct",
        MetricCategory.RECOVERY,
        "%",
        "Blood oxygen saturation percentage",
        (85, 100),
        True,
    ),
    "recovery_score": CanonicalMetric(
        "recovery_score",
        MetricCategory.RECOVERY,
        "0–100",
        "Recovery score; Whoop-native (0–100); composite for other devices",
        (0, 100),
        True,
    ),
    "recovery_index": CanonicalMetric(
        "recovery_index",
        MetricCategory.RECOVERY,
        "0–100",
        "Oura recovery index: how quickly HRV peaked during sleep",
        (0, 100),
        True,
    ),
    # ── Activity ─────────────────────────────────────────────────────────────
    "activity_score": CanonicalMetric(
        "activity_score",
        MetricCategory.ACTIVITY,
        "0–100",
        "Daily activity / movement score; native for Oura/Garmin, composite for others",
        (0, 100),
        True,
    ),
    "steps": CanonicalMetric(
        "steps",
        MetricCategory.ACTIVITY,
        "count",
        "Total step count for the day",
        (0, 100_000),
        True,
    ),
    "active_calories_kcal": CanonicalMetric(
        "active_calories_kcal",
        MetricCategory.ACTIVITY,
        "kcal",
        "Active energy expenditure (does not include BMR)",
        (0, 5_000),
        True,
    ),
    "total_calories_kcal": CanonicalMetric(
        "total_calories_kcal",
        MetricCategory.ACTIVITY,
        "kcal",
        "Total energy expenditure (active + resting/BMR)",
        (0, 8_000),
        None,
    ),
    "active_min": CanonicalMetric(
        "active_min",
        MetricCategory.ACTIVITY,
        "min",
        "Minutes of moderate-to-vigorous physical activity",
        (0, 480),
        True,
    ),
    "vo2_max": CanonicalMetric(
        "vo2_max",
        MetricCategory.ACTIVITY,
        "ml/kg/min",
        "Estimated maximal aerobic capacity",
        (10, 90),
        True,
    ),
    "strain_score": CanonicalMetric(
        "strain_score",
        MetricCategory.ACTIVITY,
        "0–100",
        (
            "Exertion / strain score normalised to 0–100.  "
            "Whoop-native is 0–21 and is linearly scaled here.  "
            "Other devices use activity_score as a proxy."
        ),
        (0, 100),
        None,
    ),
    "body_battery": CanonicalMetric(
        "body_battery",
        MetricCategory.ACTIVITY,
        "0–100",
        "Energy reserve score; Garmin-native; readiness_score proxy for other devices",
        (0, 100),
        True,
    ),
    "stress_score": CanonicalMetric(
        "stress_score",
        MetricCategory.ACTIVITY,
        "0–100",
        "Daily stress level; Google Health Connect / Garmin native; HRV-derived otherwise",
        (0, 100),
        False,
    ),
    # ── Body composition ─────────────────────────────────────────────────────
    "weight_kg": CanonicalMetric(
        "weight_kg",
        MetricCategory.BODY_COMPOSITION,
        "kg",
        "Body weight in kilograms",
        (20, 300),
        None,
    ),
    "body_fat_pct": CanonicalMetric(
        "body_fat_pct",
        MetricCategory.BODY_COMPOSITION,
        "%",
        "Body fat percentage",
        (3, 60),
        False,
    ),
    "body_temperature_c": CanonicalMetric(
        "body_temperature_c",
        MetricCategory.BODY_COMPOSITION,
        "°C",
        "Absolute body temperature reading in Celsius (used to derive body_temp_deviation_c)",
        (35.0, 42.0),
        None,
    ),
    # ── Cardiovascular ───────────────────────────────────────────────────────
    "blood_pressure_systolic_mmhg": CanonicalMetric(
        "blood_pressure_systolic_mmhg",
        MetricCategory.CARDIOVASCULAR,
        "mmHg",
        "Systolic blood pressure",
        (60, 200),
        False,
    ),
    "blood_pressure_diastolic_mmhg": CanonicalMetric(
        "blood_pressure_diastolic_mmhg",
        MetricCategory.CARDIOVASCULAR,
        "mmHg",
        "Diastolic blood pressure",
        (40, 130),
        False,
    ),
    # ── Glucose ──────────────────────────────────────────────────────────────
    "avg_glucose_mgdl": CanonicalMetric(
        "avg_glucose_mgdl",
        MetricCategory.GLUCOSE,
        "mg/dL",
        "Daily mean blood / interstitial glucose",
        (40, 400),
        None,
    ),
    "time_in_range_pct": CanonicalMetric(
        "time_in_range_pct",
        MetricCategory.GLUCOSE,
        "%",
        "Percentage of the day with glucose in target range 70–180 mg/dL (ADA standard)",
        (0, 100),
        True,
    ),
    "glucose_variability_cv": CanonicalMetric(
        "glucose_variability_cv",
        MetricCategory.GLUCOSE,
        "%",
        "Glucose coefficient of variation (CV = σ/μ × 100); <36 % = stable",
        (0, 100),
        False,
    ),
    "peak_glucose_mgdl": CanonicalMetric(
        "peak_glucose_mgdl",
        MetricCategory.GLUCOSE,
        "mg/dL",
        "Daily maximum glucose reading",
        (40, 400),
        None,
    ),
    "glucose_spikes_count": CanonicalMetric(
        "glucose_spikes_count",
        MetricCategory.GLUCOSE,
        "count",
        "Number of glucose readings above 180 mg/dL during the day",
        (0, 100),
        False,
    ),
    # Track B — postprandial metrics (per-meal, computed by postprandial.py)
    "postprandial_peak_mgdl": CanonicalMetric(
        "postprandial_peak_mgdl",
        MetricCategory.GLUCOSE,
        "mg/dL",
        "Maximum glucose in the 0–120 min window following a meal",
        (40, 400),
        None,
    ),
    "postprandial_auc": CanonicalMetric(
        "postprandial_auc",
        MetricCategory.GLUCOSE,
        "mg·min/dL",
        "Area under the glucose curve for 0–120 min after a meal (trapezoidal)",
        (0, 50_000),
        None,
    ),
    "postprandial_excursion_mgdl": CanonicalMetric(
        "postprandial_excursion_mgdl",
        MetricCategory.GLUCOSE,
        "mg/dL",
        "Glucose peak minus the 30-min pre-meal baseline",
        (-50, 200),
        None,
    ),
    "time_to_glucose_peak_min": CanonicalMetric(
        "time_to_glucose_peak_min",
        MetricCategory.GLUCOSE,
        "min",
        "Minutes from meal start to glucose peak",
        (0, 180),
        None,
    ),
    # ── Symptom outcomes ─────────────────────────────────────────────────────
    "symptom_severity_avg": CanonicalMetric(
        "symptom_severity_avg",
        MetricCategory.SYMPTOM,
        "0–10",
        "Average symptom severity for the day (from symptom journal)",
        (0, 10),
        False,
    ),
    "symptom_count": CanonicalMetric(
        "symptom_count",
        MetricCategory.SYMPTOM,
        "count",
        "Number of distinct symptoms logged for the day",
        (0, 20),
        False,
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_metric(name: str) -> Optional[CanonicalMetric]:
    """Return the CanonicalMetric for *name*, or None if unknown."""
    return CANONICAL_METRICS.get(name)


def metrics_by_category(category: MetricCategory) -> Dict[str, CanonicalMetric]:
    """Return all canonical metrics belonging to *category*."""
    return {k: v for k, v in CANONICAL_METRICS.items() if v.category == category}


def is_known(name: str) -> bool:
    """True if *name* is a registered canonical metric name."""
    return name in CANONICAL_METRICS
