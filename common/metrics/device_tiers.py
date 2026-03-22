"""
Device Tier Classification
Classifies connected devices into three tiers for tier-aware UX and scoring.

Tier 1 (T1) — Smartphone: basic steps, HR, workouts
Tier 2 (T2) — Wearable: sleep staging, HRV, recovery, temp, SpO2
Tier 3 (T3) — Medical Device: continuous glucose, blood pressure
"""

from enum import Enum
from typing import Dict, List, Optional, Set


class DeviceTier(str, Enum):
    T1_SMARTPHONE = "T1"
    T2_WEARABLE = "T2"
    T3_MEDICAL = "T3"


# Map each known source to its base tier
DEVICE_TIER_MAP: Dict[str, str] = {
    "healthkit": "T1",
    "health_connect": "T1",
    "samsung": "T1",
    "oura": "T2",
    "whoop": "T2",
    "garmin": "T2",
    "fitbit": "T2",
    "polar": "T2",
    "dexcom": "T3",
    "clinical": "T3",
    "blood_pressure": "T3",
}

# Metrics that indicate wearable-grade data (upgrades T1 → T2)
WEARABLE_GRADE_METRICS: Set[str] = {
    "hrv_ms",
    "sleep_efficiency_pct",
    "deep_sleep_min",
    "rem_sleep_min",
    "readiness_score",
    "recovery_score",
    "body_temp_deviation_c",
    "hrv_balance",
    "recovery_index",
    "spo2_pct",
    "strain_score",
    "body_battery",
}

# Metrics that require medical devices (T3)
MEDICAL_GRADE_METRICS: Set[str] = {
    "avg_glucose_mgdl",
    "time_in_range_pct",
    "glucose_variability_cv",
    "peak_glucose_mgdl",
    "glucose_spikes_count",
    "blood_pressure_systolic_mmhg",
    "blood_pressure_diastolic_mmhg",
    "postprandial_peak_mgdl",
    "postprandial_auc",
    "postprandial_excursion_mgdl",
    "time_to_glucose_peak_min",
}

# Core metrics available at each tier (cumulative)
TIER_METRICS: Dict[str, Set[str]] = {
    "T1": {
        "steps",
        "active_calories_kcal",
        "total_calories_kcal",
        "active_min",
        "resting_hr_bpm",
        "weight_kg",
        "body_fat_pct",
        "vo2_max",
        "sleep_duration_min",
        "activity_score",
    },
    "T2": {
        "sleep_score",
        "sleep_efficiency_pct",
        "deep_sleep_min",
        "rem_sleep_min",
        "light_sleep_min",
        "sleep_latency_min",
        "sleep_disturbances",
        "hrv_ms",
        "hrv_balance",
        "readiness_score",
        "recovery_score",
        "recovery_index",
        "body_temp_deviation_c",
        "respiratory_rate_bpm",
        "spo2_pct",
        "strain_score",
        "body_battery",
        "stress_score",
        "body_temperature_c",
    },
    "T3": {
        "avg_glucose_mgdl",
        "time_in_range_pct",
        "glucose_variability_cv",
        "peak_glucose_mgdl",
        "glucose_spikes_count",
        "blood_pressure_systolic_mmhg",
        "blood_pressure_diastolic_mmhg",
        "postprandial_peak_mgdl",
        "postprandial_auc",
        "postprandial_excursion_mgdl",
        "time_to_glucose_peak_min",
    },
}

TIER_LABELS: Dict[str, str] = {
    "T1": "Basic Health Tracking",
    "T2": "Advanced Health Monitoring",
    "T3": "Medical-Grade Monitoring",
}

# What each tier upgrade unlocks — used for user guidance messaging
TIER_UNLOCK_MAP: Dict[str, Dict] = {
    "T1_to_T2": {
        "label": "Wearable Device",
        "examples": "Oura Ring, Apple Watch, WHOOP, Garmin, Fitbit",
        "unlocks": [
            "Sleep quality & staging analysis",
            "HRV trends & recovery scores",
            "Readiness & strain tracking",
            "Body temperature deviation",
            "Overtraining & inflammation detection",
            "Sleep-nutrition correlations",
        ],
    },
    "T2_to_T3": {
        "label": "Medical Device",
        "examples": "Dexcom CGM, Blood Pressure Monitor",
        "unlocks": [
            "Continuous glucose monitoring",
            "Meal-glucose response patterns",
            "Time-in-range tracking",
            "Blood pressure trends",
            "Glucose-nutrition correlations",
        ],
    },
}

# Pattern → minimum tier required
PATTERN_TIER_REQUIREMENTS: Dict[str, Dict] = {
    "overtraining": {
        "min_tier": "T2",
        "required_metrics": ["hrv_health", "sleep_quality", "activity_level"],
        "description": "Detects when HRV drops + sleep declines + activity stays high",
    },
    "inflammation": {
        "min_tier": "T2",
        "required_metrics": ["hrv_health"],
        "optional_metrics": ["temp_trend"],
        "description": "Detects elevated inflammation from HRV, temperature, and diet signals",
    },
    "poor_recovery": {
        "min_tier": "T2",
        "required_metrics": ["recovery", "hrv_health"],
        "description": "Detects inadequate recovery from readiness and cardiac stress",
    },
    "sleep_disruption": {
        "min_tier": "T2",
        "required_metrics": ["sleep_quality"],
        "optional_metrics": ["sleep_efficiency"],
        "description": "Detects poor sleep quality linked to meal timing",
    },
    "glucose_instability": {
        "min_tier": "T3",
        "required_metrics": ["glucose_stability", "time_in_range"],
        "description": "Detects glucose spikes and time-out-of-range from CGM data",
    },
    "cardiac_strain": {
        "min_tier": "T2",
        "required_metrics": ["cardiac_stress", "recovery", "hrv_health"],
        "description": "Detects elevated cardiac stress with poor recovery",
    },
}


def detect_effective_tier(
    connected_sources: List[str],
    available_metrics: Optional[List[str]] = None,
) -> str:
    """
    Detect user's effective device tier from connected sources and available metrics.
    Returns "T1", "T2", or "T3".
    """
    sources = set(connected_sources) if connected_sources else set()
    metrics = set(available_metrics) if available_metrics else set()

    # T3: Has medical device data
    if sources & {"dexcom", "clinical", "blood_pressure"}:
        return "T3"
    if metrics & MEDICAL_GRADE_METRICS:
        return "T3"

    # T2: Has dedicated wearable OR phone with wearable-grade data
    if sources & {"oura", "whoop", "garmin", "fitbit", "polar"}:
        return "T2"
    # HealthKit/HealthConnect with Apple Watch or wearable-grade metrics
    if metrics & WEARABLE_GRADE_METRICS:
        return "T2"

    return "T1"


def get_missing_pillars(available_metrics: List[str]) -> List[Dict[str, str]]:
    """Return health score pillars that are missing and what tier would provide them."""
    metrics = set(available_metrics) if available_metrics else set()
    missing = []

    pillar_requirements = {
        "Sleep Quality": {"metrics": {"sleep_quality", "sleep_score"}, "tier": "T2"},
        "Heart (HRV)": {
            "metrics": {"hrv_ms", "hrv_balance", "hrv_health"},
            "tier": "T2",
        },
        "Recovery": {
            "metrics": {"recovery", "readiness_score", "recovery_score"},
            "tier": "T2",
        },
        "Activity": {
            "metrics": {"activity_level", "steps", "active_calories_kcal"},
            "tier": "T1",
        },
    }

    for pillar, req in pillar_requirements.items():
        if not (metrics & set(req["metrics"])):
            missing.append(
                {
                    "pillar": pillar,
                    "requires_tier": req["tier"],
                    "upgrade_hint": TIER_UNLOCK_MAP.get(f"T1_to_{req['tier']}", {}).get(
                        "examples", ""
                    ),
                }
            )

    return missing


def get_unlock_hints(
    detected_patterns: List[str],
    available_metrics: List[str],
    current_tier: str,
) -> List[Dict]:
    """
    Return hints about patterns that could be detected with device upgrades.
    Only returns hints for tiers above the user's current tier.
    """
    metrics = set(available_metrics) if available_metrics else set()
    tier_order = {"T1": 1, "T2": 2, "T3": 3}
    current_rank = tier_order.get(current_tier, 1)
    hints = []

    for pattern_name, req in PATTERN_TIER_REQUIREMENTS.items():
        if pattern_name in detected_patterns:
            continue  # Already detected, no hint needed

        req_tier = req["min_tier"]
        req_rank = tier_order.get(req_tier, 1)

        if req_rank > current_rank:
            # This pattern requires a higher tier
            upgrade_key = f"T{current_rank}_to_{req_tier}"
            upgrade_info = TIER_UNLOCK_MAP.get(upgrade_key, {})
            hints.append(
                {
                    "pattern_name": pattern_name,
                    "label": req.get("description", pattern_name),
                    "requires_tier": req_tier,
                    "missing_metrics": req.get("required_metrics", []),
                    "device_examples": upgrade_info.get("examples", ""),
                    "upgrade_label": upgrade_info.get("label", ""),
                }
            )

    return hints
