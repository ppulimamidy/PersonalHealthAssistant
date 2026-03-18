"""
Metabolic Intelligence — Advanced Correlation Engine

Cross-references ALL user-connected data sources (wearables, Apple Health,
Google Health, Whoop, Dexcom, Garmin, etc.) with nutrition, medications,
supplements, and symptoms over 7–30 day windows to surface statistically
significant patterns. The engine is data-source agnostic: it uses whatever
the user has connected and returns a note listing every source used.

Engine considerations:
- Multi-lag analysis: lags 1–14 days (not just same-day + lag-1).
- Non-linear relationships: Spearman rank correlation alongside Pearson.
- Granger causality: causal direction testing up to 14 lags when data allows.
- Confounding: AI summary notes controlled-for (e.g. sleep duration) when available.
- Output shape: causal confidence, effect timing, magnitude, and controlled-for
  are encouraged in descriptions and in downstream insights.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,line-too-long,invalid-name

import math
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.metrics.normalizer import SOURCE_PRIORITY as _SOURCE_PRIORITY
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_upsert,
)

logger = get_logger(__name__)
router = APIRouter()

NUTRITION_SERVICE_URL = os.environ.get(
    "NUTRITION_SERVICE_URL", "http://localhost:8007"
).rstrip("/")
NUTRITION_TIMEOUT_S = float(os.environ.get("NUTRITION_SERVICE_TIMEOUT_S", "8.0"))
USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")

# Anthropic for AI summary generation
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("CORRELATION_AI_MODEL", "claude-sonnet-4-6")

CACHE_TTL_HOURS = 6
MIN_OVERLAPPING_DAYS = 5
# Advanced Correlation Engine: multi-lag analysis (1-14 days), Granger up to 14 lags
MAX_LAG_DAYS = 14
GRANGER_MAX_LAG = 14

# Relaxed thresholds for condition-specific pairs
CONDITION_MIN_R = 0.3
CONDITION_MAX_P = 0.15

# Which metrics belong to each data source — used to classify condition variables
_NUTRITION_VARS: frozenset = frozenset(
    {
        "total_calories",
        "total_protein_g",
        "total_carbs_g",
        "total_fat_g",
        "total_fiber_g",
        "total_sugar_g",
        "total_sodium_mg",
        "glycemic_load_est",
        "last_meal_hour",
        "protein_pct",
        "carb_pct",
        "fat_pct",
    }
)
_HEALTH_VARS: frozenset = frozenset(
    {
        # Sleep
        "sleep_score",
        "sleep_efficiency_pct",
        "deep_sleep_min",
        "sleep_duration_min",
        # Recovery
        "hrv_balance",
        "hrv_ms",
        "resting_hr_bpm",
        "readiness_score",
        "recovery_index",
        "body_temp_deviation_c",
        # Activity
        "steps",
        "activity_score",
        "active_calories_kcal",
        "active_min",
        "vo2_max",
        # Wearable
        "respiratory_rate_bpm",
        "spo2_pct",
        # Tier 2 wearables (Whoop, Garmin, etc.)
        "whoop_strain",
        "whoop_recovery",
        "garmin_stress",
        "garmin_body_battery",
        # Tier 3 / medical devices
        "avg_glucose_mgdl",
        "blood_pressure_systolic_mmhg",
        "blood_pressure_diastolic_mmhg",
        "body_temperature_c",
        "weight_kg",
        "body_fat_pct",
        # Symptom outcomes
        "symptom_severity_avg",
        "symptom_count",
    }
)
# Backward-compat alias for learned_priors stored with old metric names
_OURA_VARS = _HEALTH_VARS

# Map native_health_data metric_type → internal metric key used by correlation engine
_NATIVE_METRIC_MAP: Dict[str, str] = {
    "steps": "steps",
    "sleep": "sleep_duration_min",
    "resting_heart_rate": "resting_hr_bpm",
    "hrv_sdnn": "hrv_ms",
    "spo2": "spo2_pct",
    "respiratory_rate": "respiratory_rate_bpm",
    "active_calories": "active_calories_kcal",
    "workout": "active_min",
    "vo2_max": "vo2_max",
    "blood_glucose": "avg_glucose_mgdl",
    "blood_pressure_systolic": "blood_pressure_systolic_mmhg",
    "blood_pressure_diastolic": "blood_pressure_diastolic_mmhg",
    "body_temperature": "body_temperature_c",
    "weight": "weight_kg",
    "body_fat": "body_fat_pct",
    "strain": "whoop_strain",
    "recovery": "whoop_recovery",
    "readiness": "readiness_score",
    "skin_temperature": "body_temperature_c",
}

# Unit conversions applied when extracting from native_health_data.value_json
_NATIVE_SCALE: Dict[str, float] = {
    "sleep": 60.0,  # hours → minutes (canonical: sleep_duration_min)
}

# primary value key inside native_health_data.value_json, per metric_type
_NATIVE_PRIMARY_KEY: Dict[str, str] = {
    "steps": "steps",
    "sleep": "hours",
    "resting_heart_rate": "bpm",
    "hrv_sdnn": "ms",
    "spo2": "pct",
    "respiratory_rate": "rate",
    "active_calories": "kcal",
    "workout": "minutes",
    "vo2_max": "ml_kg_min",
    "blood_glucose": "mg_dl",
    "blood_pressure_systolic": "mmhg",
    "blood_pressure_diastolic": "mmhg",
    "body_temperature": "celsius",
    "weight": "kg",
    "body_fat": "pct",
    "strain": "score",
    "recovery": "pct",
    "readiness": "score",
    "skin_temperature": "celsius",
}

# Human-readable source names
_SOURCE_DISPLAY_NAMES: Dict[str, str] = {
    "oura": "Oura Ring",
    "healthkit": "Apple Health",
    "health_connect": "Google Health",
    "whoop": "Whoop",
    "garmin": "Garmin",
    "fitbit": "Fitbit",
    "polar": "Polar",
    "samsung": "Samsung Health",
    "dexcom": "Dexcom",
    "blood_pressure": "Blood Pressure Monitor",
    "clinical": "Clinical Data",
    "nutrition": "Nutrition Logs",
    "symptoms": "Symptom Journal",
    "medications": "Medications",
}

# Which native metrics pair naturally against nutrition inputs (as outcomes)
_NATIVE_OUTCOME_METRICS: frozenset = frozenset(
    {
        "sleep_duration_min",
        "hrv_ms",
        "spo2_pct",
        "respiratory_rate_bpm",
        "active_min",
        "vo2_max",
        "avg_glucose_mgdl",
        "blood_pressure_systolic_mmhg",
        "blood_pressure_diastolic_mmhg",
        "body_temperature_c",
        "weight_kg",
        "body_fat_pct",
        "whoop_strain",
        "whoop_recovery",
        "symptom_severity_avg",
        "symptom_count",
    }
)

# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class CorrelationDataPoint(BaseModel):
    """Single data point for a correlation scatter plot."""

    date: str
    a_value: float
    b_value: float


class Correlation(BaseModel):
    """One statistically significant correlation between two metrics."""

    id: str
    metric_a: str
    metric_a_label: str
    metric_b: str
    metric_b_label: str
    correlation_coefficient: float
    p_value: float
    sample_size: int
    lag_days: int
    effect_description: str
    category: str  # nutrition_sleep, nutrition_readiness, nutrition_activity
    strength: str  # strong, moderate, weak
    direction: str  # positive, negative
    data_points: List[CorrelationDataPoint]


class CorrelationResults(BaseModel):
    """Full correlation analysis response."""

    correlations: List[Correlation]
    summary: Optional[str] = None
    data_quality_score: float
    oura_days_available: int
    nutrition_days_available: int
    days_with_data: int = 0  # union of all source days
    data_sources_used: List[str] = []  # human-readable source names
    computed_at: str
    period_days: int


class CausalEdge(BaseModel):
    """Causal relationship between two variables."""

    from_metric: str
    from_label: str
    to_metric: str
    to_label: str
    causality_score: float  # 0-1, higher = stronger causal evidence
    correlation: float
    granger_p_value: Optional[float]
    optimal_lag_days: int
    strength: str  # strong, moderate, weak
    evidence: List[str]  # ["correlation", "granger_causality", "temporal_precedence"]


class CausalGraph(BaseModel):
    """Causal graph showing directional relationships."""

    nodes: List[
        Dict[str, str]
    ]  # [{"id": "total_carbs_g", "label": "Carbs", "type": "nutrition"}]
    edges: List[CausalEdge]
    computed_at: str
    confidence_threshold: float
    data_sources_used: List[str] = []
    days_with_data: int = 0  # actual days analyzed (useful when days=0 / all-history)


# ---------------------------------------------------------------------------
# Human-readable labels
# ---------------------------------------------------------------------------

METRIC_LABELS: Dict[str, str] = {
    # Nutrition
    "total_calories": "Daily Calories",
    "total_protein_g": "Protein (g)",
    "total_carbs_g": "Carbs (g)",
    "total_fat_g": "Fat (g)",
    "total_fiber_g": "Fiber (g)",
    "total_sugar_g": "Sugar (g)",
    "total_sodium_mg": "Sodium (mg)",
    "protein_pct": "Protein %",
    "carb_pct": "Carb %",
    "fat_pct": "Fat %",
    "glycemic_load_est": "Glycemic Load Est.",
    "last_meal_hour": "Last Meal Hour",
    # Oura
    "sleep_score": "Sleep Score",
    "sleep_efficiency": "Sleep Efficiency",
    "deep_sleep_hours": "Deep Sleep (h)",
    "total_sleep_hours": "Total Sleep (h)",
    "hrv_balance": "HRV Balance",
    "resting_heart_rate": "Resting Heart Rate",
    "readiness_score": "Readiness Score",
    "recovery_index": "Recovery Index",
    "temperature_deviation": "Temp Deviation",
    "steps": "Daily Steps",
    "activity_score": "Activity Score",
    "active_calories": "Active Calories",
    # Native wearable metrics (Tier 1/2)
    "respiratory_rate": "Respiratory Rate",
    "spo2": "Blood Oxygen (SpO₂)",
    "workout_minutes": "Workout Duration (min)",
    "vo2_max": "VO₂ Max",
    "hrv_sdnn": "HRV (SDNN)",
    # Tier 2 wearables (Whoop, Garmin)
    "whoop_strain": "Whoop Strain",
    "whoop_recovery": "Whoop Recovery",
    "garmin_stress": "Garmin Stress",
    "garmin_body_battery": "Garmin Body Battery",
    # Tier 3 / medical
    "blood_glucose": "Blood Glucose (mg/dL)",
    "blood_pressure_systolic": "Systolic BP (mmHg)",
    "blood_pressure_diastolic": "Diastolic BP (mmHg)",
    "body_temperature": "Body Temperature (°C)",
    "weight_kg": "Weight (kg)",
    "body_fat_pct": "Body Fat %",
    # Symptoms
    "symptom_severity_avg": "Avg Symptom Severity",
    "symptom_count": "Symptom Count",
    # Medications
    "medication_adherence": "Medication Adherence",
    # Canonical metric names (device-agnostic)
    "sleep_efficiency_pct": "Sleep Efficiency %",
    "sleep_duration_min": "Sleep Duration (min)",
    "deep_sleep_min": "Deep Sleep (min)",
    "resting_hr_bpm": "Resting Heart Rate (bpm)",
    "active_calories_kcal": "Active Calories (kcal)",
    "active_min": "Active Minutes",
    "hrv_ms": "HRV (ms)",
    "spo2_pct": "Blood Oxygen (SpO₂%)",
    "respiratory_rate_bpm": "Respiratory Rate (bpm)",
    "body_temp_deviation_c": "Body Temp Deviation (°C)",
    "body_temperature_c": "Body Temperature (°C)",
    "avg_glucose_mgdl": "Avg Blood Glucose (mg/dL)",
    "peak_glucose_mgdl": "Peak Blood Glucose (mg/dL)",
    "time_in_range_pct": "Time in Range (%)",
    "glucose_variability_cv": "Glucose Variability (CV%)",
    "glucose_spikes_count": "Glucose Spikes",
    "blood_pressure_systolic_mmhg": "Systolic BP (mmHg)",
    "blood_pressure_diastolic_mmhg": "Diastolic BP (mmHg)",
}

# Track 1 — Health-self pairs (wearable vs wearable, no nutrition required).
# Evaluated independently of diet data so users with wearable data but no
# nutrition logs still see meaningful patterns.
# Format: (metric_a, metric_b, category, lag_days)
HEALTH_SELF_PAIRS: List[Tuple[str, str, str, int]] = [
    ("sleep_score", "hrv_balance", "nutrition_readiness", 1),
    ("sleep_score", "readiness_score", "nutrition_readiness", 1),
    ("deep_sleep_min", "hrv_balance", "nutrition_sleep", 1),
    ("steps", "sleep_score", "nutrition_sleep", 1),
    ("steps", "readiness_score", "nutrition_activity", 1),
    ("active_calories_kcal", "hrv_balance", "nutrition_readiness", 1),
    ("resting_hr_bpm", "readiness_score", "nutrition_readiness", 1),
    ("hrv_balance", "readiness_score", "nutrition_readiness", 0),
    ("sleep_efficiency_pct", "resting_hr_bpm", "nutrition_sleep", 1),
]

# Key pairs for multi-lag analysis (1 to MAX_LAG_DAYS): (nutrition_metric, oura_metric, category)
KEY_PAIRS_MULTILAG: List[Tuple[str, str, str]] = [
    ("total_sugar_g", "hrv_balance", "nutrition_readiness"),
    ("total_sugar_g", "sleep_score", "nutrition_sleep"),
    ("total_carbs_g", "sleep_score", "nutrition_sleep"),
    ("total_carbs_g", "hrv_balance", "nutrition_readiness"),
    ("total_calories", "readiness_score", "nutrition_readiness"),
    ("last_meal_hour", "sleep_score", "nutrition_sleep"),
]

# Correlation pairs: (nutrition_metric, oura_metric, category, lag) — fixed lag 0 or 1
CORRELATION_PAIRS: List[Tuple[str, str, str, int]] = [
    # Nutrition → Sleep (next-day effect)
    ("total_carbs_g", "sleep_score", "nutrition_sleep", 1),
    ("total_carbs_g", "sleep_efficiency_pct", "nutrition_sleep", 1),
    ("total_carbs_g", "deep_sleep_min", "nutrition_sleep", 1),
    ("total_sugar_g", "sleep_score", "nutrition_sleep", 1),
    ("total_sugar_g", "sleep_efficiency_pct", "nutrition_sleep", 1),
    ("total_calories", "sleep_score", "nutrition_sleep", 1),
    ("last_meal_hour", "sleep_score", "nutrition_sleep", 0),
    ("last_meal_hour", "sleep_efficiency_pct", "nutrition_sleep", 0),
    ("total_protein_g", "deep_sleep_min", "nutrition_sleep", 1),
    ("total_fat_g", "sleep_score", "nutrition_sleep", 1),
    ("total_fiber_g", "sleep_efficiency_pct", "nutrition_sleep", 1),
    ("glycemic_load_est", "sleep_score", "nutrition_sleep", 1),
    ("glycemic_load_est", "hrv_balance", "nutrition_sleep", 1),
    # Nutrition → Readiness/Recovery
    ("total_protein_g", "readiness_score", "nutrition_readiness", 1),
    ("total_protein_g", "recovery_index", "nutrition_readiness", 1),
    ("total_carbs_g", "hrv_balance", "nutrition_readiness", 1),
    ("total_carbs_g", "resting_hr_bpm", "nutrition_readiness", 1),
    ("total_sugar_g", "hrv_balance", "nutrition_readiness", 1),
    ("total_sodium_mg", "resting_hr_bpm", "nutrition_readiness", 1),
    ("total_calories", "readiness_score", "nutrition_readiness", 1),
    ("total_protein_g", "hrv_balance", "nutrition_readiness", 0),
    # Nutrition → Activity
    ("total_calories", "steps", "nutrition_activity", 0),
    ("total_calories", "active_calories_kcal", "nutrition_activity", 0),
    ("total_protein_g", "activity_score", "nutrition_activity", 0),
    ("total_carbs_g", "active_calories_kcal", "nutrition_activity", 0),
]


# ---------------------------------------------------------------------------
# Pure-Python Pearson correlation
# ---------------------------------------------------------------------------


def _pearson_r(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and approximate p-value.
    Pure Python — no numpy/scipy dependency.
    """
    n = len(x)
    if n < MIN_OVERLAPPING_DAYS:
        return 0.0, 1.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if std_x == 0 or std_y == 0:
        return 0.0, 1.0

    r = cov / (std_x * std_y)
    r = max(-1.0, min(1.0, r))  # clamp floating-point drift

    # t-statistic for significance
    if abs(r) >= 1.0:
        return r, 0.0
    t_stat = r * math.sqrt((n - 2) / (1 - r * r))
    p_value = _approx_two_tail_p(t_stat, n - 2)
    return round(r, 4), round(p_value, 6)


def _spearman_r(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation (non-linear / monotonic).
    Pure Python — no numpy/scipy dependency.
    """
    n = len(x)
    if n < MIN_OVERLAPPING_DAYS:
        return 0.0, 1.0

    def rank(vals: List[float]) -> List[float]:
        order = sorted(range(n), key=lambda i: vals[i])
        ranks = [0.0] * n
        for r, i in enumerate(order, 1):
            ranks[i] = float(r)
        # Handle ties: assign average rank
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[order[j]] == vals[order[j + 1]]:
                j += 1
            if j > i:
                avg = (i + 1 + j + 1) / 2.0
                for k in range(i, j + 1):
                    ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx = rank(x)
    ry = rank(y)
    return _pearson_r(rx, ry)


def _approx_two_tail_p(t: float, df: int) -> float:
    """
    Approximate two-tailed p-value for a t-distribution.
    Uses a simple approximation adequate for df=3..20 (our typical range).
    """
    if df <= 0:
        return 1.0
    # Approximation: p ≈ 2 * (1 - Φ(|t| * √(df / (df + t²))))  for large df
    # For small df, use the regularised incomplete beta function shortcut.
    x = df / (df + t * t)
    # Regularised incomplete beta I_x(df/2, 0.5) via a simple series expansion
    a = df / 2.0
    b = 0.5
    p = _reg_incomplete_beta(x, a, b)
    return max(0.0, min(1.0, p))


def _reg_incomplete_beta(x: float, a: float, b: float, max_iter: int = 100) -> float:
    """Regularised incomplete beta function I_x(a, b) via continued fraction."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    # Use the log-beta for the prefactor
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta) / a

    # Lentz continued fraction
    f = 1.0
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1)
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    f = d

    for m in range(1, max_iter + 1):
        # even step
        num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        d = 1.0 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= d * c

        # odd step
        num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        delta = d * c
        f *= delta

        if abs(delta - 1.0) < 1e-8:
            break

    return front * f


def _f_dist_p_value(f_stat: float, df1: int, df2: int) -> float:
    """
    Upper-tail p-value for the F-distribution: P(F > f_stat).
    Uses the regularised incomplete beta identity:
        p = 1 - I_{x}(df1/2, df2/2)  where x = df1*f / (df1*f + df2)
    """
    if f_stat <= 0 or df1 <= 0 or df2 <= 0:
        return 1.0
    x = (df1 * f_stat) / (df1 * f_stat + df2)
    cdf = _reg_incomplete_beta(x, df1 / 2.0, df2 / 2.0)
    return max(0.0, min(1.0, 1.0 - cdf))


def _ols_rss(X_rows: List[List[float]], y: List[float]) -> Optional[float]:
    """
    Fit OLS via the normal equations  (X'X)⁻¹ X'y  using Gaussian elimination
    with partial pivoting.  Returns residual sum of squares, or None if the
    system is (near-)singular or there are too few observations.
    Pure Python — no numpy / scipy dependency.
    """
    n = len(y)
    if not X_rows or n == 0:
        return None
    k = len(X_rows[0])
    if n < k + 2:
        return None

    # Build X'X (k×k) and X'y (k,)
    XtX = [[0.0] * k for _ in range(k)]
    Xty = [0.0] * k
    for i in range(n):
        xi = X_rows[i]
        for a in range(k):
            Xty[a] += xi[a] * y[i]
            for b in range(a, k):
                v = xi[a] * xi[b]
                XtX[a][b] += v
                if b != a:
                    XtX[b][a] += v

    # Solve (X'X) beta = X'y via Gauss-Jordan with partial pivoting
    # Augmented matrix [XtX | Xty]
    aug = [XtX[i][:] + [Xty[i]] for i in range(k)]

    for col in range(k):
        # Partial pivoting
        max_row = max(range(col, k), key=lambda r: abs(aug[r][col]))
        aug[col], aug[max_row] = aug[max_row], aug[col]
        pivot = aug[col][col]
        if abs(pivot) < 1e-12:
            return None  # singular — can't fit model
        # Normalise pivot row
        inv_pivot = 1.0 / pivot
        aug[col] = [v * inv_pivot for v in aug[col]]
        # Eliminate column in all other rows
        for row in range(k):
            if row == col:
                continue
            factor = aug[row][col]
            if abs(factor) < 1e-15:
                continue
            for j in range(col, k + 1):
                aug[row][j] -= factor * aug[col][j]

    beta = [aug[i][k] for i in range(k)]

    # Compute RSS = Σ (y_i - ŷ_i)²
    rss = 0.0
    for i in range(n):
        pred = sum(X_rows[i][j] * beta[j] for j in range(k))
        resid = y[i] - pred
        rss += resid * resid
    return rss


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------

# Mapping from Oura-format metric names → canonical metric names
_OURA_TO_CANONICAL: Dict[str, str] = {
    "sleep_score": "sleep_score",
    "sleep_efficiency": "sleep_efficiency_pct",
    "total_sleep_hours": "sleep_duration_min",
    "deep_sleep_hours": "deep_sleep_min",
    "hrv_balance": "hrv_balance",
    "resting_heart_rate": "resting_hr_bpm",
    "readiness_score": "readiness_score",
    "recovery_index": "recovery_index",
    "temperature_deviation": "body_temp_deviation_c",
    "steps": "steps",
    "activity_score": "activity_score",
    "active_calories": "active_calories_kcal",
    "respiratory_rate": "respiratory_rate_bpm",
    "spo2": "spo2_pct",
    "workout_minutes": "active_min",
    "vo2_max": "vo2_max",
}

# Scale factors for Oura metrics when remapping to canonical (hours → minutes etc.)
_OURA_SCALE: Dict[str, float] = {
    "total_sleep_hours": 60.0,
    "deep_sleep_hours": 60.0,
}


def _oura_to_canonical(oura_metrics: Dict[str, float]) -> Dict[str, float]:
    """Remap Oura-format metric dict to canonical metric names."""
    canonical: Dict[str, float] = {}
    for oura_key, value in oura_metrics.items():
        canon_key = _OURA_TO_CANONICAL.get(oura_key)
        if canon_key is not None:
            scale = _OURA_SCALE.get(oura_key, 1.0)
            canonical[canon_key] = value * scale
    return canonical


async def _build_health_daily(
    user_id: str,
    fetch_days: int,
    timeline: list,
) -> Tuple[Dict[str, Dict[str, float]], List[str]]:
    """
    Build the device-agnostic health_daily dict from all connected sources.

    Data priority per date:
    1. health_metrics_normalized (canonical names, all sources via Session 2+)
    2. Oura timeline data (remapped to canonical via _oura_to_canonical)
    3. native_health_data fallback for dates not yet in health_metrics_normalized

    Returns (health_daily, display_source_names).
    """
    from datetime import date as _date

    health_daily: Dict[str, Dict[str, float]] = {}
    sources_seen: Set[str] = set()

    # 1. Query health_metrics_normalized for canonical data from all devices
    start_d = (_date.today() - timedelta(days=fetch_days)).isoformat()
    norm_rows: list = []
    try:
        norm_rows = await _supabase_get(
            "health_metrics_normalized",
            f"user_id=eq.{user_id}&date=gte.{start_d}"
            f"&select=date,canonical_metric,value,source,confidence"
            f"&order=date.asc,confidence.desc",
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Could not fetch health_metrics_normalized: %s", exc)

    # Track best priority per (date, metric) to handle multi-source deduplication
    _best_priority: Dict[Tuple[str, str], int] = {}

    for row in norm_rows or []:
        date_str = str(row.get("date", ""))[:10]
        metric = row.get("canonical_metric", "")
        value = row.get("value")
        source = row.get("source", "")
        if not date_str or not metric or value is None:
            continue
        try:
            val = float(value)
        except (TypeError, ValueError):
            continue

        src_prio = _SOURCE_PRIORITY.get(source, 0)
        key = (date_str, metric)
        if src_prio > _best_priority.get(key, -1):
            health_daily.setdefault(date_str, {})[metric] = val
            _best_priority[key] = src_prio
            sources_seen.add(source)

    normalized_dates = set(health_daily.keys())

    # 2. Oura timeline fallback for dates not yet in health_metrics_normalized
    oura_raw = _extract_oura_daily(timeline)
    if oura_raw:
        sources_seen.add("oura")
        for date_str, oura_metrics in oura_raw.items():
            canonical = _oura_to_canonical(oura_metrics)
            if not canonical:
                continue
            day = health_daily.setdefault(date_str, {})
            for metric, val in canonical.items():
                # health_metrics_normalized takes priority; Oura fills gaps
                if date_str not in normalized_dates or metric not in day:
                    day[metric] = val

    # 3. native_health_data fallback (for dates not yet normalized)
    native_daily, native_source_names = await _fetch_native_health_data(
        user_id, fetch_days
    )
    for date_str, native_metrics in native_daily.items():
        if date_str in normalized_dates:
            continue  # Already covered by health_metrics_normalized
        day = health_daily.setdefault(date_str, {})
        for metric, val in native_metrics.items():
            if metric not in day:
                day[metric] = val
    # Merge source names (already display-formatted)
    for name in native_source_names:
        # Reverse lookup from display name to source key for sources_seen
        sources_seen.update(k for k, v in _SOURCE_DISPLAY_NAMES.items() if v == name)

    display_names = [
        _SOURCE_DISPLAY_NAMES.get(s, s.capitalize()) for s in sorted(sources_seen)
    ]
    return health_daily, display_names


async def _fetch_nutrition_daily(
    bearer: Optional[str], days: int
) -> Dict[str, Dict[str, float]]:
    """
    Fetch daily-aggregated nutrition data from the nutrition service.
    Returns {date_str: {metric: value, ...}, ...}
    """
    end_d = date.today()
    start_d = end_d - timedelta(days=days)
    url = (
        f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/nutrition-history"
        f"?start_date={start_d.isoformat()}&end_date={end_d.isoformat()}"
    )

    headers: Dict[str, str] = {}
    if bearer:
        headers["Authorization"] = bearer

    timeout = aiohttp.ClientTimeout(total=NUTRITION_TIMEOUT_S)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Nutrition service returned %s for correlation fetch",
                        resp.status,
                    )
                    return {}
                payload = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.warning("Nutrition service unreachable for correlations: %s", exc)
        return {}

    # Unwrap {success: true, data: [...]} format
    items = payload
    if isinstance(payload, dict):
        if payload.get("success") and "data" in payload:
            items = payload["data"]
        elif "items" in payload:
            items = payload["items"]
    if not isinstance(items, list):
        return {}

    # Aggregate by date
    daily: Dict[str, Dict[str, float]] = {}
    for meal in items:
        ts = meal.get("timestamp") or meal.get("date") or ""
        day_str = ts[:10] if ts else ""
        if not day_str:
            continue

        if day_str not in daily:
            daily[day_str] = {
                "total_calories": 0,
                "total_protein_g": 0,
                "total_carbs_g": 0,
                "total_fat_g": 0,
                "total_fiber_g": 0,
                "total_sugar_g": 0,
                "total_sodium_mg": 0,
                "last_meal_hour": 0,
                "_meal_count": 0,
            }

        d = daily[day_str]
        d["total_calories"] += float(meal.get("total_calories") or 0)
        d["total_protein_g"] += float(meal.get("total_protein_g") or 0)
        d["total_carbs_g"] += float(meal.get("total_carbs_g") or 0)
        d["total_fat_g"] += float(meal.get("total_fat_g") or 0)
        d["total_fiber_g"] += float(meal.get("total_fiber_g") or 0)
        d["total_sugar_g"] += float(meal.get("total_sugar_g") or 0)
        d["total_sodium_mg"] += float(meal.get("total_sodium_mg") or 0)
        d["_meal_count"] += 1

        # Track latest meal hour for the day
        if ts and len(ts) >= 13:
            try:
                hour = int(ts[11:13])
                if hour > d["last_meal_hour"]:
                    d["last_meal_hour"] = float(hour)
            except (ValueError, IndexError):
                pass

    # Compute derived metrics
    for d in daily.values():
        cals = d["total_calories"] or 1
        d["protein_pct"] = round(d["total_protein_g"] * 4 / cals * 100, 1)
        d["carb_pct"] = round(d["total_carbs_g"] * 4 / cals * 100, 1)
        d["fat_pct"] = round(d["total_fat_g"] * 9 / cals * 100, 1)
        d["glycemic_load_est"] = max(0, d["total_carbs_g"] - d["total_fiber_g"])
        del d["_meal_count"]

    return daily


def _extract_oura_daily(timeline: list) -> Dict[str, Dict[str, float]]:
    """
    Flatten timeline entries into {date_str: {metric: value, ...}} dict.
    """
    daily: Dict[str, Dict[str, float]] = {}
    for entry in timeline:
        day = entry.date if hasattr(entry, "date") else entry.get("date", "")
        if not day:
            continue

        row: Dict[str, float] = {}
        s = entry.sleep if hasattr(entry, "sleep") else entry.get("sleep")
        if s:
            row["sleep_score"] = float(getattr(s, "sleep_score", 0) or 0)
            row["sleep_efficiency"] = float(getattr(s, "sleep_efficiency", 0) or 0)
            dur = float(getattr(s, "total_sleep_duration", 0) or 0)
            row["total_sleep_hours"] = round(dur / 3600, 2)
            deep = float(getattr(s, "deep_sleep_duration", 0) or 0)
            row["deep_sleep_hours"] = round(deep / 3600, 2)

        a = entry.activity if hasattr(entry, "activity") else entry.get("activity")
        if a:
            row["steps"] = float(getattr(a, "steps", 0) or 0)
            row["active_calories"] = float(getattr(a, "active_calories", 0) or 0)
            row["activity_score"] = float(getattr(a, "activity_score", 0) or 0)

        r = entry.readiness if hasattr(entry, "readiness") else entry.get("readiness")
        if r:
            row["readiness_score"] = float(getattr(r, "readiness_score", 0) or 0)
            row["hrv_balance"] = float(getattr(r, "hrv_balance", 0) or 0)
            row["recovery_index"] = float(getattr(r, "recovery_index", 0) or 0)
            row["resting_heart_rate"] = float(getattr(r, "resting_heart_rate", 0) or 0)
            row["temperature_deviation"] = float(
                getattr(r, "temperature_deviation", 0) or 0
            )

        # Native wearable metrics (Apple Health, Health Connect, any Tier 1/2 device)
        n = entry.native if hasattr(entry, "native") else entry.get("native")
        if n:
            for field, key in [
                ("respiratory_rate", "respiratory_rate"),
                ("spo2", "spo2"),
                ("active_calories", "active_calories"),
                ("workout_minutes", "workout_minutes"),
                ("vo2_max", "vo2_max"),
            ]:
                val = (
                    getattr(n, field, None)
                    if hasattr(n, field)
                    else (n.get(field) if isinstance(n, dict) else None)
                )
                if val is not None and val != 0:
                    row[key] = float(val)
            # If native active_calories is present but activity entry already has it, prefer the larger value
            if "active_calories" in row and a:
                oura_cal = float(getattr(a, "active_calories", 0) or 0)
                if oura_cal > row.get("active_calories", 0):
                    row["active_calories"] = oura_cal

        if row:
            daily[day] = row

    return daily


async def _fetch_native_health_data(
    user_id: str, days: int
) -> Tuple[Dict[str, Dict[str, float]], List[str]]:
    """
    Query native_health_data for ALL connected device sources.
    Returns (daily_dict, display_source_names).
    daily_dict: {date_str: {internal_metric_key: value, ...}}

    Merges data from Apple Health, Google Health, Whoop, Dexcom, Garmin, etc.
    Oura data already comes from the timeline endpoint; native data supplements it.
    """
    from datetime import date as _date

    start_d = (_date.today() - timedelta(days=days)).isoformat()

    try:
        rows = await _supabase_get(
            "native_health_data",
            f"user_id=eq.{user_id}&date=gte.{start_d}"
            f"&select=date,source,metric_type,value_json&order=date.asc",
        )
    except Exception as exc:
        logger.warning("Could not fetch native_health_data: %s", exc)
        return {}, []

    daily: Dict[str, Dict[str, float]] = {}
    sources_seen: set = set()

    for row in rows or []:
        date_str = str(row.get("date", ""))[:10]
        source = row.get("source", "")
        metric_type = row.get("metric_type", "")
        value_json = row.get("value_json") or {}

        # Map to internal metric key
        internal_key = _NATIVE_METRIC_MAP.get(metric_type)
        primary_key = _NATIVE_PRIMARY_KEY.get(metric_type)
        if not internal_key or not primary_key or not isinstance(value_json, dict):
            continue

        val = value_json.get(primary_key)
        if val is None:
            continue
        try:
            val = float(val) * _NATIVE_SCALE.get(metric_type, 1.0)
        except (TypeError, ValueError):
            continue
        if val == 0 and internal_key not in (
            "body_temperature_c",
            "blood_pressure_diastolic_mmhg",
        ):
            continue

        if date_str not in daily:
            daily[date_str] = {}

        # Keep the higher non-zero value if multiple sources report the same metric
        existing = daily[date_str].get(internal_key, 0.0)
        if val > existing or existing == 0:
            daily[date_str][internal_key] = val

        sources_seen.add(source)

    display_names = [
        _SOURCE_DISPLAY_NAMES.get(s, s.capitalize()) for s in sorted(sources_seen)
    ]
    return daily, display_names


async def _fetch_symptoms_daily(user_id: str, days: int) -> Dict[str, Dict[str, float]]:
    """
    Fetch daily symptom averages from symptom_journal.
    Returns {date_str: {"symptom_severity_avg": float, "symptom_count": float}}.
    These are used as health *outcome* variables in correlation analysis.
    """
    from datetime import date as _date

    start_d = (_date.today() - timedelta(days=days)).isoformat()

    try:
        rows = await _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{start_d}"
            f"&select=symptom_date,severity&order=symptom_date.asc",
        )
    except Exception as exc:
        logger.warning("Could not fetch symptom_journal for correlations: %s", exc)
        return {}

    # Aggregate by date: average severity + count
    by_date: Dict[str, List[float]] = {}
    for row in rows or []:
        d = str(row.get("symptom_date", ""))[:10]
        sev = row.get("severity")
        if d and sev is not None:
            by_date.setdefault(d, []).append(float(sev))

    daily: Dict[str, Dict[str, float]] = {}
    for d, sevs in by_date.items():
        daily[d] = {
            "symptom_severity_avg": round(sum(sevs) / len(sevs), 2),
            "symptom_count": float(len(sevs)),
        }
    return daily


async def _fetch_medications_supplements_context(
    user_id: str, days: int
) -> Tuple[Dict[str, Dict[str, float]], str, List[str]]:
    """
    Fetch active medications and supplements, and daily adherence rates.
    Returns (adherence_daily, context_str, sources_used).
    - adherence_daily: {date: {medication_adherence_rate: 0.0–1.0}} from adherence log
    - context_str: human-readable list for the AI summary prompt
    - sources_used: ["Medications"] and/or ["Supplements"] if any exist
    """
    from datetime import date as _date

    start_d = (_date.today() - timedelta(days=days)).isoformat()
    sources_used: List[str] = []
    context_parts: List[str] = []

    # Active medications
    try:
        med_rows = await _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=medication_name,dosage,frequency,indication",
        )
        if med_rows:
            sources_used.append("Medications")
            descs = []
            for r in med_rows:
                d = f"{r.get('medication_name', '')} {r.get('dosage', '')} {r.get('frequency', '')}".strip()
                if r.get("indication"):
                    d += f" (for {r['indication']})"
                descs.append(d)
            context_parts.append("Active medications: " + "; ".join(descs))
    except Exception as exc:
        logger.warning("Could not fetch medications for context: %s", exc)

    # Active supplements
    try:
        supp_rows = await _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=supplement_name,dosage,frequency,purpose",
        )
        if supp_rows:
            sources_used.append("Supplements")
            descs = []
            for r in supp_rows:
                d = f"{r.get('supplement_name', '')} {r.get('dosage', '')}".strip()
                if r.get("purpose"):
                    d += f" ({r['purpose']})"
                descs.append(d)
            context_parts.append("Active supplements: " + "; ".join(descs))
    except Exception as exc:
        logger.warning("Could not fetch supplements for context: %s", exc)

    # Medication adherence log → daily adherence rate (continuous variable for correlations)
    adherence_daily: Dict[str, Dict[str, float]] = {}
    try:
        adh_rows = await _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&scheduled_time=gte.{start_d}"
            f"&select=scheduled_time,was_taken&order=scheduled_time.asc",
        )
        if adh_rows:
            by_date: Dict[str, List[bool]] = {}
            for row in adh_rows:
                d = str(row.get("scheduled_time", ""))[:10]
                taken = bool(row.get("was_taken", False))
                if d:
                    by_date.setdefault(d, []).append(taken)
            for d, bools in by_date.items():
                adherence_daily[d] = {
                    "medication_adherence_rate": round(sum(bools) / len(bools), 3)
                }
    except Exception as exc:
        logger.warning("Could not fetch medication_adherence_log: %s", exc)

    context_str = " | ".join(context_parts) if context_parts else ""
    return adherence_daily, context_str, sources_used


async def _fetch_lab_biomarkers_daily(
    user_id: str, days: int
) -> Tuple[Dict[str, Dict[str, float]], str]:
    """
    Fetch lab results within the date window.
    Returns (daily_dict, context_str).
    - daily_dict: {test_date: {lab_glucose: 125.0, lab_hba1c: 6.8, ...}}
      Only populated if >= 2 draws exist in the window (need variance for statistics).
    - context_str: most-recent lab values formatted for the AI prompt.
    """
    import re as _re
    from datetime import date as _date

    start_d = (_date.today() - timedelta(days=days)).isoformat()

    try:
        rows = await _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&test_date=gte.{start_d}"
            f"&select=test_date,biomarkers&order=test_date.asc",
        )
    except Exception as exc:
        logger.warning("Could not fetch lab_results: %s", exc)
        return {}, ""

    if not rows:
        return {}, ""

    def _slug(name: str) -> str:
        return "lab_" + _re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

    daily: Dict[str, Dict[str, float]] = {}
    most_recent_date = ""
    most_recent_markers: List[str] = []

    for row in rows:
        date_str = str(row.get("test_date", ""))[:10]
        biomarkers = row.get("biomarkers") or []
        if not date_str or not isinstance(biomarkers, list):
            continue
        day_vals: Dict[str, float] = {}
        for bm in biomarkers:
            name = str(bm.get("name", "")).strip()
            val = bm.get("value")
            if not name or val is None:
                continue
            try:
                day_vals[_slug(name)] = float(val)
            except (TypeError, ValueError):
                continue
        if day_vals:
            daily[date_str] = day_vals
            if date_str >= most_recent_date:
                most_recent_date = date_str
                most_recent_markers = [
                    f"{bm.get('name', '')} {bm.get('value', '')} {bm.get('unit', '')}".strip()
                    + (
                        " ⚠"
                        if str(bm.get("status", "")).lower()
                        in ("high", "low", "abnormal", "critical")
                        else ""
                    )
                    for bm in biomarkers
                    if bm.get("name") and bm.get("value") is not None
                ]

    # Only expose daily dict for statistical use if we have >= 2 draws
    stats_daily = daily if len(daily) >= 2 else {}

    context_str = (
        f"Recent labs ({most_recent_date}): {', '.join(most_recent_markers[:8])}"
        if most_recent_markers and most_recent_date
        else ""
    )
    return stats_daily, context_str


async def _fetch_conditions_context(user_id: str) -> str:
    """Return the user's active health conditions as a short string for the AI prompt."""
    try:
        rows = await _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=condition_name,severity&order=created_at.asc",
        )
        if rows:
            parts = []
            for r in rows:
                name = r.get("condition_name", "")
                if name:
                    sev = r.get("severity", "")
                    parts.append(f"{name} ({sev})" if sev else name)
            if parts:
                return "Active conditions: " + ", ".join(parts)
    except Exception as exc:
        logger.warning("Could not fetch conditions for context: %s", exc)
    return ""


# ---------------------------------------------------------------------------
# Correlation computation
# ---------------------------------------------------------------------------


def _infer_category(nutr_metric: str, health_metric: str) -> str:
    """Derive a correlation category string from the metric names."""
    sleep_metrics = {
        "sleep_score",
        "sleep_efficiency_pct",
        "deep_sleep_min",
        "sleep_duration_min",
    }
    activity_metrics = {"steps", "activity_score", "active_calories_kcal", "active_min"}
    if health_metric in sleep_metrics:
        return "nutrition_sleep"
    if health_metric in activity_metrics:
        return "nutrition_activity"
    return "nutrition_readiness"


def _build_dynamic_native_pairs(
    available_health_metrics: set,
) -> List[Tuple[str, str, str, int]]:
    """
    Build correlation pairs for native device metrics not covered by the
    hardcoded CORRELATION_PAIRS list. Pairs every nutrition input metric
    against any available native outcome metric.
    """
    extra_pairs: List[Tuple[str, str, str, int]] = []
    already_paired = {(a, b) for a, b, _cat, _lag in CORRELATION_PAIRS}

    for outcome in _NATIVE_OUTCOME_METRICS & available_health_metrics:
        if outcome in _HEALTH_VARS - _NATIVE_OUTCOME_METRICS:
            # Already covered by standard CORRELATION_PAIRS
            continue
        for nutr in _NUTRITION_VARS:
            if (nutr, outcome) in already_paired:
                continue
            # Choose lag based on metric type
            lag = (
                1
                if outcome
                in {
                    "hrv_ms",
                    "avg_glucose_mgdl",
                    "blood_pressure_systolic_mmhg",
                    "blood_pressure_diastolic_mmhg",
                    "symptom_severity_avg",
                }
                else 0
            )
            cat = (
                "nutrition_glucose"
                if outcome == "avg_glucose_mgdl"
                else "nutrition_bp"
                if "blood_pressure" in outcome
                else "nutrition_symptom"
                if "symptom" in outcome
                else "nutrition_body"
                if outcome in {"weight_kg", "body_fat_pct"}
                else "nutrition_recovery"
            )
            extra_pairs.append((nutr, outcome, cat, lag))

    return extra_pairs


def _one_correlation(
    nutr_metric: str,
    oura_metric: str,
    category: str,
    lag: int,
    all_dates: List[str],
    nutrition_daily: Dict[str, Dict[str, float]],
    health_daily: Dict[str, Dict[str, float]],
    use_spearman: bool = False,
    min_r: float = 0.4,
    max_p: float = 0.10,
) -> Optional[Dict[str, Any]]:
    """Build aligned series and compute one correlation (Pearson or Spearman)."""
    x_vals: List[float] = []
    y_vals: List[float] = []
    points: List[Dict[str, Any]] = []

    for i, d in enumerate(all_dates):
        if lag > 0 and i + lag >= len(all_dates):
            continue
        oura_date = all_dates[i + lag] if lag > 0 else d
        nutr = nutrition_daily.get(d)
        health = health_daily.get(oura_date)
        if (
            not nutr
            or not health
            or nutr_metric not in nutr
            or oura_metric not in health
        ):
            continue
        x, y = nutr[nutr_metric], health[oura_metric]
        if x == 0 and nutr_metric not in ("last_meal_hour", "temperature_deviation"):
            continue
        if y == 0 and oura_metric not in ("temperature_deviation",):
            continue
        x_vals.append(x)
        y_vals.append(y)
        points.append(
            {"date": oura_date, "a_value": round(x, 2), "b_value": round(y, 2)}
        )

    if len(x_vals) < MIN_OVERLAPPING_DAYS:
        return None

    if use_spearman:
        r, p = _spearman_r(x_vals, y_vals)
        correlation_type = "spearman"
    else:
        r, p = _pearson_r(x_vals, y_vals)
        correlation_type = "pearson"

    if abs(r) < min_r or p >= max_p:
        return None

    abs_r = abs(r)
    strength = "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.5 else "weak"
    direction = "positive" if r > 0 else "negative"

    return {
        "id": str(uuid.uuid4()),
        "metric_a": nutr_metric,
        "metric_a_label": METRIC_LABELS.get(nutr_metric, nutr_metric),
        "metric_b": oura_metric,
        "metric_b_label": METRIC_LABELS.get(oura_metric, oura_metric),
        "correlation_coefficient": r,
        "p_value": p,
        "sample_size": len(x_vals),
        "lag_days": lag,
        "effect_description": "",
        "category": category,
        "strength": strength,
        "direction": direction,
        "data_points": points,
        "correlation_type": correlation_type,
    }


def _one_health_correlation(
    metric_a: str,
    metric_b: str,
    category: str,
    lag: int,
    all_dates: List[str],
    health_daily: Dict[str, Dict[str, float]],
    use_spearman: bool = False,
    min_r: float = 0.4,
    max_p: float = 0.10,
) -> Optional[Dict[str, Any]]:
    """
    Correlation between two health/wearable metrics (Track 1 — no nutrition needed).
    Both metric_a and metric_b are looked up from health_daily.
    """
    x_vals: List[float] = []
    y_vals: List[float] = []
    points: List[Dict[str, Any]] = []

    for i, d in enumerate(all_dates):
        if lag > 0 and i + lag >= len(all_dates):
            continue
        target_date = all_dates[i + lag] if lag > 0 else d
        src = health_daily.get(d)
        tgt = health_daily.get(target_date)
        if not src or not tgt or metric_a not in src or metric_b not in tgt:
            continue
        x, y = src[metric_a], tgt[metric_b]
        if x == 0 or y == 0:
            continue
        x_vals.append(x)
        y_vals.append(y)
        points.append(
            {"date": target_date, "a_value": round(x, 2), "b_value": round(y, 2)}
        )

    if len(x_vals) < MIN_OVERLAPPING_DAYS:
        return None

    if use_spearman:
        r, p = _spearman_r(x_vals, y_vals)
        correlation_type = "spearman"
    else:
        r, p = _pearson_r(x_vals, y_vals)
        correlation_type = "pearson"

    if abs(r) < min_r or p >= max_p:
        return None

    abs_r = abs(r)
    strength = "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.5 else "weak"
    direction = "positive" if r > 0 else "negative"

    return {
        "id": str(uuid.uuid4()),
        "metric_a": metric_a,
        "metric_a_label": METRIC_LABELS.get(metric_a, metric_a),
        "metric_b": metric_b,
        "metric_b_label": METRIC_LABELS.get(metric_b, metric_b),
        "correlation_coefficient": r,
        "p_value": p,
        "sample_size": len(x_vals),
        "lag_days": lag,
        "effect_description": "",
        "category": category,
        "strength": strength,
        "direction": direction,
        "data_points": points,
        "correlation_type": correlation_type,
    }


def _compute_correlations(
    nutrition_daily: Dict[str, Dict[str, float]],
    health_daily: Dict[str, Dict[str, float]],
    condition_vars: Optional[List[str]] = None,
    learned_priors: Optional[List[Dict[str, Any]]] = None,
    dynamic_native_pairs: Optional[List[Tuple[str, str, str, int]]] = None,
) -> List[Dict[str, Any]]:
    """
    Compute pairwise correlations (Pearson + Spearman for non-linear).

    Six passes:
      0) Health-self pairs (Track 1): wearable vs wearable — no nutrition needed
      1) Fixed-lag pairs from CORRELATION_PAIRS  (standard thresholds)
      2) Multi-lag analysis (1 to MAX_LAG_DAYS) for KEY_PAIRS_MULTILAG
      3) Condition-specific pairs — relaxed thresholds for clinical relevance
      4) Learned-prior pairs from N-of-1 intervention outcomes
      5) Dynamic native device pairs (Dexcom, Whoop, symptom outcomes, etc.)

    Returns list of significant correlation dicts sorted by |r| descending.
    """
    all_dates = sorted(set(nutrition_daily.keys()) | set(health_daily.keys()))
    health_dates = sorted(health_daily.keys())  # Track 1 only needs health data
    best_by_pair: Dict[Tuple[str, str], Dict[str, Any]] = {}

    # 0) Track 1: Health-self pairs — wearable vs wearable, no nutrition needed.
    #    Per-pair overlap check: each pair independently needs ≥MIN_OVERLAPPING_DAYS
    #    of days where both metrics are present. Users with 0 nutrition logs still
    #    get patterns from their wearable data here.
    for metric_a, metric_b, category, lag in HEALTH_SELF_PAIRS:
        best_c = None
        for use_spearman in (False, True):
            c = _one_health_correlation(
                metric_a,
                metric_b,
                category,
                lag,
                health_dates,
                health_daily,
                use_spearman=use_spearman,
            )
            if c and (
                best_c is None
                or abs(c["correlation_coefficient"])
                > abs(best_c["correlation_coefficient"])
            ):
                best_c = c
        if best_c:
            key = (metric_a, metric_b)
            if key not in best_by_pair or abs(best_c["correlation_coefficient"]) > abs(
                best_by_pair[key]["correlation_coefficient"]
            ):
                best_by_pair[key] = best_c

    # 1) Fixed-lag pairs (Pearson + Spearman: keep stronger)
    for nutr_metric, oura_metric, category, lag in CORRELATION_PAIRS:
        best_c = None
        for use_spearman in (False, True):
            c = _one_correlation(
                nutr_metric,
                oura_metric,
                category,
                lag,
                all_dates,
                nutrition_daily,
                health_daily,
                use_spearman=use_spearman,
            )
            if c and (
                best_c is None
                or abs(c["correlation_coefficient"])
                > abs(best_c["correlation_coefficient"])
            ):
                best_c = c
        if best_c:
            key = (nutr_metric, oura_metric)
            if key not in best_by_pair or abs(best_c["correlation_coefficient"]) > abs(
                best_by_pair[key]["correlation_coefficient"]
            ):
                best_by_pair[key] = best_c

    # 2) Multi-lag analysis (1 to MAX_LAG_DAYS) for key pairs
    max_lag = min(MAX_LAG_DAYS, len(all_dates) - 2)
    if max_lag >= 1:
        for nutr_metric, oura_metric, category in KEY_PAIRS_MULTILAG:
            key = (nutr_metric, oura_metric)
            best_r = 0.0
            best_c = None
            for lag in range(1, max_lag + 1):
                for use_spearman in (False, True):
                    c = _one_correlation(
                        nutr_metric,
                        oura_metric,
                        category,
                        lag,
                        all_dates,
                        nutrition_daily,
                        health_daily,
                        use_spearman=use_spearman,
                    )
                    if c and abs(c["correlation_coefficient"]) > best_r:
                        best_r = abs(c["correlation_coefficient"])
                        best_c = c
            if best_c and (
                key not in best_by_pair
                or best_r > abs(best_by_pair[key]["correlation_coefficient"])
            ):
                best_by_pair[key] = best_c

    # 3) Condition-specific pairs — relaxed thresholds so condition-relevant weak
    #    signals surface even when they wouldn't pass the standard |r|>=0.4 gate.
    if condition_vars:
        cond_nutr = [v for v in condition_vars if v in _NUTRITION_VARS]
        cond_oura = [v for v in condition_vars if v in _OURA_VARS]
        for nutr_metric in cond_nutr:
            for oura_metric in cond_oura:
                key = (nutr_metric, oura_metric)
                category = _infer_category(nutr_metric, oura_metric)
                best_r = (
                    abs(best_by_pair[key]["correlation_coefficient"])
                    if key in best_by_pair
                    else 0.0
                )
                best_c = best_by_pair.get(key)
                # Test lags 0, 1, 2 with both Pearson and Spearman
                for lag in (0, 1, 2):
                    for use_spearman in (False, True):
                        c = _one_correlation(
                            nutr_metric,
                            oura_metric,
                            category,
                            lag,
                            all_dates,
                            nutrition_daily,
                            health_daily,
                            use_spearman=use_spearman,
                            min_r=CONDITION_MIN_R,
                            max_p=CONDITION_MAX_P,
                        )
                        if c and abs(c["correlation_coefficient"]) > best_r:
                            best_r = abs(c["correlation_coefficient"])
                            best_c = c
                if best_c:
                    best_by_pair[key] = best_c

    # 4) Learned-prior pairs from N-of-1 intervention outcomes.
    # Use even-more-relaxed thresholds (|r|>=0.25, p<0.20) since these are
    # metric pairs the user has personally validated as relevant.
    if learned_priors:
        PRIOR_MIN_R = 0.25
        PRIOR_MAX_P = 0.20
        for prior in learned_priors:
            nutr_metric = prior.get("nutrition_metric", "")
            oura_metric = prior.get("oura_metric", "")
            if not nutr_metric or not oura_metric:
                continue
            key = (nutr_metric, oura_metric)
            category = _infer_category(nutr_metric, oura_metric)
            best_r = (
                abs(best_by_pair[key]["correlation_coefficient"])
                if key in best_by_pair
                else 0.0
            )
            best_c = best_by_pair.get(key)
            for lag in (0, 1, 2):
                for use_spearman in (False, True):
                    c = _one_correlation(
                        nutr_metric,
                        oura_metric,
                        category,
                        lag,
                        all_dates,
                        nutrition_daily,
                        health_daily,
                        use_spearman=use_spearman,
                        min_r=PRIOR_MIN_R,
                        max_p=PRIOR_MAX_P,
                    )
                    if c and abs(c["correlation_coefficient"]) > best_r:
                        best_r = abs(c["correlation_coefficient"])
                        best_c = c
            if best_c:
                best_by_pair[key] = best_c

    # 5) Dynamic native device / symptom pairs (Dexcom, Whoop, BP, symptom outcomes)
    if dynamic_native_pairs:
        for nutr_metric, health_metric, category, lag in dynamic_native_pairs:
            key = (nutr_metric, health_metric)
            best_r = (
                abs(best_by_pair[key]["correlation_coefficient"])
                if key in best_by_pair
                else 0.0
            )
            best_c = best_by_pair.get(key)
            for use_spearman in (False, True):
                c = _one_correlation(
                    nutr_metric,
                    health_metric,
                    category,
                    lag,
                    all_dates,
                    nutrition_daily,
                    health_daily,
                    use_spearman=use_spearman,
                )
                if c and abs(c["correlation_coefficient"]) > best_r:
                    best_r = abs(c["correlation_coefficient"])
                    best_c = c
            if best_c:
                best_by_pair[key] = best_c

    results = list(best_by_pair.values())
    results.sort(key=lambda c: abs(c["correlation_coefficient"]), reverse=True)
    return results


# ---------------------------------------------------------------------------
# Advanced Statistics: Granger Causality & Causal Inference
# ---------------------------------------------------------------------------


def _granger_causality_test(
    x_series: List[float], y_series: List[float], max_lag: Optional[int] = None
) -> Tuple[Optional[int], Optional[float]]:
    """
    Granger causality test: does X help predict Y beyond Y's own history?
    Uses up to GRANGER_MAX_LAG (14) when enough data; otherwise min(14, n//3).
    Returns (optimal_lag, p_value) if significant, else (None, None).
    """
    n = len(x_series)
    lag_limit = max_lag if max_lag is not None else min(GRANGER_MAX_LAG, max(1, n // 3))
    if n < lag_limit + 5:
        return (None, None)

    best_lag = None
    best_p = 1.0

    for lag in range(1, lag_limit + 1):
        # Build lagged features
        # Unrestricted model: Y_t = α + β₁Y_{t-1} + ... + β_lag Y_{t-lag} + γ₁X_{t-1} + ... + γ_lag X_{t-lag}
        # Restricted model: Y_t = α + β₁Y_{t-1} + ... + β_lag Y_{t-lag}

        y_train = y_series[lag:]
        n_train = len(y_train)

        if n_train < lag + 3:
            continue

        # Compute RSS for unrestricted model (with X lags)
        # For simplicity, use a partial correlation approach
        # If adding X_lags significantly reduces RSS, X Granger-causes Y

        # Restricted model: Y regressed on its own lags only
        rss_restricted = _compute_ar_residuals(y_series, lag)

        # Unrestricted model: Y regressed on its lags + X lags
        rss_unrestricted = _compute_ar_with_exog_residuals(y_series, x_series, lag)

        if rss_unrestricted is None or rss_restricted is None:
            continue

        if rss_restricted <= 0 or rss_unrestricted < 0:
            continue

        # F-statistic: ((RSS_r - RSS_u) / lag) / (RSS_u / (n_train - 2*lag - 1))
        # df1 = lag (number of X-lag restrictions being tested)
        # df2 = n_train - 2*lag - 1 (residual df of unrestricted model)
        df1 = lag
        df2 = n_train - 2 * lag - 1

        if df2 <= 0:
            continue

        rss_diff = rss_restricted - rss_unrestricted
        if rss_diff <= 0:
            # X lags did not reduce RSS — no causal evidence at this lag
            continue

        f_stat = (rss_diff / df1) / (rss_unrestricted / df2)

        # Exact upper-tail p-value via F-distribution / regularised incomplete beta
        p_exact = _f_dist_p_value(f_stat, df1, df2)

        if p_exact < best_p:
            best_p = p_exact
            best_lag = lag

    if best_lag and best_p < 0.10:
        return (best_lag, best_p)

    return (None, None)


def _compute_ar_residuals(y_series: List[float], lag: int) -> Optional[float]:
    """
    RSS for the restricted AR(lag) model fitted via OLS:
        Y_t = α + β₁ Y_{t-1} + … + β_lag Y_{t-lag}
    Design matrix has an intercept column plus `lag` lagged-Y columns.
    """
    n = len(y_series)
    y_train = y_series[lag:]
    if len(y_train) < lag + 3:
        return None

    X_rows = [
        [1.0] + [y_series[i - j] for j in range(1, lag + 1)] for i in range(lag, n)
    ]
    return _ols_rss(X_rows, y_train)


def _compute_ar_with_exog_residuals(
    y_series: List[float], x_series: List[float], lag: int
) -> Optional[float]:
    """
    RSS for the unrestricted ARX(lag) model fitted via OLS:
        Y_t = α + β₁ Y_{t-1} + … + β_lag Y_{t-lag}
                + γ₁ X_{t-1} + … + γ_lag X_{t-lag}
    Design matrix: intercept + lag Y-lags + lag X-lags  (2*lag + 1 columns).
    """
    n = len(y_series)
    y_train = y_series[lag:]
    if len(y_train) < 2 * lag + 3:
        return None

    X_rows = [
        [1.0]
        + [y_series[i - j] for j in range(1, lag + 1)]
        + [x_series[i - j] for j in range(1, lag + 1)]
        for i in range(lag, n)
    ]
    return _ols_rss(X_rows, y_train)


def _compute_causal_graph(
    correlations: List[Dict[str, Any]],
    nutrition_daily: Dict[str, Dict[str, float]],
    health_daily: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Build causal graph from correlations using Granger causality tests.
    Returns dict with nodes and edges for visualization.
    """
    all_dates = sorted(set(nutrition_daily.keys()) | set(health_daily.keys()))

    nodes = {}
    edges = []

    for corr in correlations[:20]:  # Limit to top 20 correlations
        metric_a = corr["metric_a"]
        metric_b = corr["metric_b"]

        def _node_type(metric: str) -> str:
            if metric in _NUTRITION_VARS:
                return "nutrition"
            if "symptom" in metric:
                return "symptom"
            if "adherence" in metric:
                return "medication"
            if metric.startswith("lab_"):
                return "lab"
            if metric in {
                "blood_glucose",
                "blood_pressure_systolic",
                "blood_pressure_diastolic",
                "body_temperature",
            }:
                return "medical"
            if metric in {
                "whoop_strain",
                "whoop_recovery",
                "garmin_stress",
                "garmin_body_battery",
            }:
                return "wearable"
            return "health"

        # Add nodes
        if metric_a not in nodes:
            nodes[metric_a] = {
                "id": metric_a,
                "label": corr["metric_a_label"],
                "type": _node_type(metric_a),
            }
        if metric_b not in nodes:
            nodes[metric_b] = {
                "id": metric_b,
                "label": corr["metric_b_label"],
                "type": _node_type(metric_b),
            }

        # Build time series for Granger test
        x_vals = []
        y_vals = []

        for d in all_dates:
            nutr = nutrition_daily.get(d)
            health = health_daily.get(d)

            if nutr and health and metric_a in nutr and metric_b in health:
                x_vals.append(nutr[metric_a])
                y_vals.append(health[metric_b])

        if len(x_vals) < 7:
            continue

        # Test if nutrition Granger-causes Oura metric (multi-lag up to 14 when enough data)
        optimal_lag, granger_p = _granger_causality_test(x_vals, y_vals)

        evidence = ["correlation"]
        if corr["lag_days"] > 0:
            evidence.append("temporal_precedence")
        if optimal_lag is not None:
            evidence.append("granger_causality")

        # Compute causality score (0-1)
        causality_score = abs(corr["correlation_coefficient"])  # Base score
        if optimal_lag:
            causality_score += 0.2  # Boost for Granger causality
        if corr["lag_days"] > 0:
            causality_score += 0.1  # Boost for temporal precedence

        causality_score = min(causality_score, 1.0)

        # Only include edges with causality_score > 0.5
        if causality_score > 0.5:
            edges.append(
                {
                    "from_metric": metric_a,
                    "from_label": corr["metric_a_label"],
                    "to_metric": metric_b,
                    "to_label": corr["metric_b_label"],
                    "causality_score": round(causality_score, 3),
                    "correlation": round(corr["correlation_coefficient"], 3),
                    "granger_p_value": round(granger_p, 3) if granger_p else None,
                    "optimal_lag_days": optimal_lag or corr["lag_days"],
                    "strength": corr["strength"],
                    "evidence": evidence,
                }
            )

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "confidence_threshold": 0.5,
    }


# ---------------------------------------------------------------------------
# AI summary generation
# ---------------------------------------------------------------------------


async def _generate_ai_summary(
    correlations: List[Dict[str, Any]],
    period_days: int,
    data_sources: Optional[List[str]] = None,
    user_context: Optional[Dict[str, str]] = None,
    oura_days: int = 0,
    nutrition_days: int = 0,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Use Anthropic Claude to generate plain-English descriptions for each correlation
    and an overall summary paragraph.
    Returns (updated_correlations, summary_text).
    """
    if not ANTHROPIC_API_KEY or not correlations:
        # Fallback: generate simple descriptions without AI
        for c in correlations:
            c["effect_description"] = _fallback_description(c)
        return correlations, _fallback_summary(
            correlations,
            period_days,
            data_sources,
            user_context,
            oura_days=oura_days,
            nutrition_days=nutrition_days,
        )

    # Build the prompt
    corr_summary = []
    for i, c in enumerate(correlations[:8]):
        corr_summary.append(
            f"{i + 1}. {c['metric_a_label']} vs {c['metric_b_label']}: "
            f"r={c['correlation_coefficient']}, p={c['p_value']}, "
            f"n={c['sample_size']}, lag={c['lag_days']} day(s), "
            f"direction={c['direction']}"
        )

    sources_str = (
        ", ".join(data_sources) if data_sources else "wearable and nutrition data"
    )
    ctx_lines = [v for v in (user_context or {}).values() if v]
    ctx_block = (
        ("\n\nUser health profile:\n" + "\n".join(ctx_lines)) if ctx_lines else ""
    )
    # Note partial data availability so Claude can mention what to add
    data_note = f"Health/wearable data: {oura_days} days. Nutrition logs: {nutrition_days} days."
    if nutrition_days < MIN_OVERLAPPING_DAYS:
        data_note += (
            f" Diet-trigger patterns (nutrition → health) are not shown yet — "
            f"need {MIN_OVERLAPPING_DAYS} overlapping days; currently {nutrition_days}."
        )
    prompt = f"""You are a health data analyst. A user has {period_days} days of data from: {sources_str}.
{data_note}{ctx_block}

The correlation engine uses multi-lag analysis (1-14 days), Pearson and Spearman (for non-linear relationships), and Granger causality for causal direction. Below are the statistically significant correlations.

Correlations:
{chr(10).join(corr_summary)}

For each correlation, write ONE concise, personalized description (max 20 words) that the user would find actionable. When the data supports it, include:
- Effect timing (e.g. "effect appears next day" or "8-12 hours later" when lag suggests it)
- Magnitude when inferable (e.g. "roughly 10g sugar ≈ -2 HRV points" only if clearly suggested by strength)
Examples:
- "Your HRV drops after high sugar; effect next day (lag 1)"
- "Late meals reduce your sleep efficiency"
- "Higher protein days correlate with better readiness"

Then write ONE overall summary paragraph (2-4 sentences). When relevant, mention: causal confidence (e.g. "moderate causal confidence from lag and direction"), effect timing, and note: "Controlled for: same-day sleep duration from wearable when available; limited control for alcohol or stress unless in data."

Respond in JSON format only (no markdown, no code fences):
{{
  "descriptions": ["description for correlation 1", "description for correlation 2", ...],
  "summary": "Overall summary paragraph"
}}

Important: Do not provide medical diagnoses. Frame everything as observed patterns."""

    try:
        import json
        import ssl
        import certifi

        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        "Anthropic API returned %s: %s", resp.status, body[:200]
                    )
                    for c in correlations:
                        c["effect_description"] = _fallback_description(c)
                    return correlations, _fallback_summary(
                        correlations,
                        period_days,
                        data_sources,
                        user_context,
                        oura_days=oura_days,
                        nutrition_days=nutrition_days,
                    )

                result = await resp.json()

        raw_text = result["content"][0]["text"]
        # Strip markdown fences if present
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("```", 2)[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.rsplit("```", 1)[0].strip()

        parsed = json.loads(clean)
        descriptions = parsed.get("descriptions", [])
        summary = parsed.get("summary", "")

        for i, c in enumerate(correlations[:8]):
            if i < len(descriptions):
                c["effect_description"] = descriptions[i]
            else:
                c["effect_description"] = _fallback_description(c)

        # Handle any remaining correlations beyond the top 8
        for c in correlations[8:]:
            c["effect_description"] = _fallback_description(c)

        return correlations, summary

    except Exception as exc:
        logger.warning("AI summary generation failed: %s", exc)
        for c in correlations:
            c["effect_description"] = _fallback_description(c)
        return correlations, _fallback_summary(
            correlations,
            period_days,
            data_sources,
            user_context,
            oura_days=oura_days,
            nutrition_days=nutrition_days,
        )


def _fallback_description(c: Dict[str, Any]) -> str:
    """Generate a simple description without AI."""
    r = c["correlation_coefficient"]
    direction = "increases" if r > 0 else "decreases"
    lag_note = " (next day)" if c["lag_days"] > 0 else ""
    return (
        f"Higher {c['metric_a_label'].lower()} correlates with "
        f"{direction}d {c['metric_b_label'].lower()}{lag_note}"
    )


def _fallback_summary(
    correlations: List[Dict[str, Any]],
    period_days: int,
    data_sources: Optional[List[str]] = None,
    user_context: Optional[Dict[str, str]] = None,
    oura_days: int = 0,
    nutrition_days: int = 0,
) -> str:
    """Generate a simple summary without AI."""
    if not correlations:
        if oura_days >= MIN_OVERLAPPING_DAYS and nutrition_days < MIN_OVERLAPPING_DAYS:
            return (
                f"Found {oura_days} days of health data — no significant wearable patterns "
                f"detected yet. Log meals for {MIN_OVERLAPPING_DAYS}+ days to unlock "
                f"diet-trigger analysis (currently {nutrition_days} nutrition day(s))."
            )
        return "No significant correlations found in the available data."
    top = correlations[0]
    sources_note = f" Data sources: {', '.join(data_sources)}." if data_sources else ""
    ctx_lines = [v for v in (user_context or {}).values() if v]
    ctx_note = f" Context: {'; '.join(ctx_lines)}." if ctx_lines else ""
    diet_note = ""
    if oura_days >= MIN_OVERLAPPING_DAYS and nutrition_days < MIN_OVERLAPPING_DAYS:
        diet_note = (
            f" Log meals for {MIN_OVERLAPPING_DAYS - nutrition_days} more day(s) "
            f"to also see how your diet affects these patterns."
        )
    return (
        f"Over the past {period_days} days, the strongest pattern found is between "
        f"{top['metric_a_label'].lower()} and {top['metric_b_label'].lower()} "
        f"(r={top['correlation_coefficient']}). "
        f"{len(correlations)} significant correlations were detected.{diet_note}{sources_note}{ctx_note}"
    )


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


async def _get_cached_results(
    user_id: str, period_days: int
) -> Optional[Dict[str, Any]]:
    """Check Supabase cache for fresh correlation results."""
    now = datetime.now(timezone.utc).isoformat()
    rows = await _supabase_get(
        "correlation_results",
        f"user_id=eq.{user_id}&period_days=eq.{period_days}"
        f"&expires_at=gt.{now}&select=*&limit=1",
    )
    if rows and isinstance(rows, list):
        return rows[0]
    return None


async def _save_to_cache(
    user_id: str,
    period_days: int,
    correlations: List[Dict[str, Any]],
    summary: str,
    data_quality: float,
    oura_days: int,
    nutrition_days: int,
    data_sources_used: Optional[List[str]] = None,
    days_with_data: int = 0,
) -> None:
    """Save correlation results to Supabase cache."""
    import json

    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=CACHE_TTL_HOURS)

    await _supabase_upsert(
        "correlation_results",
        {
            "user_id": user_id,
            "period_days": period_days,
            "correlations": json.dumps(correlations),
            "summary": summary,
            "data_quality_score": data_quality,
            "oura_days_available": oura_days,
            "nutrition_days_available": nutrition_days,
            "data_sources_used": json.dumps(data_sources_used or []),
            "days_with_data": days_with_data,
            "computed_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Main computation orchestrator
# ---------------------------------------------------------------------------


async def _compute_and_cache(
    current_user: dict,
    period_days: int,
    bearer: Optional[str],
) -> CorrelationResults:
    """Fetch ALL available user data, compute correlations, generate AI summary, cache, return."""
    from .timeline import get_timeline

    user_id = current_user["id"]

    # days=0 means "all history" — fetch without a practical window cap.
    ALL_HISTORY = period_days == 0
    fetch_days = 99999 if ALL_HISTORY else period_days

    # 1. Fetch Oura timeline data
    try:
        timeline = await get_timeline(days=fetch_days, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for correlations: %s", exc)
        timeline = []

    # 2. Build canonical health_daily from all connected devices
    health_daily, device_sources = await _build_health_daily(
        user_id, fetch_days, timeline
    )
    data_sources_used: List[str] = list(
        dict.fromkeys(device_sources)
    )  # preserve order, dedupe

    # 3. Fetch nutrition data
    nutrition_daily = await _fetch_nutrition_daily(bearer, fetch_days)
    if nutrition_daily:
        data_sources_used.append("Nutrition Logs")

    # 4. Fetch symptom data and merge as health outcome metrics
    symptoms_daily = await _fetch_symptoms_daily(user_id, fetch_days)
    if symptoms_daily:
        data_sources_used.append("Symptom Journal")
        for date_str, symp_metrics in symptoms_daily.items():
            if date_str not in health_daily:
                health_daily[date_str] = {}
            health_daily[date_str].update(symp_metrics)

    # 4b. Fetch medications + supplements: adherence as daily variable + context for AI
    (
        adherence_daily,
        meds_context,
        med_sources,
    ) = await _fetch_medications_supplements_context(user_id, fetch_days)
    data_sources_used.extend(s for s in med_sources if s not in data_sources_used)
    for date_str, adh_metrics in adherence_daily.items():
        health_daily.setdefault(date_str, {}).update(adh_metrics)

    # 4c. Fetch lab biomarkers: time-series for stats + context for AI
    lab_daily, lab_context = await _fetch_lab_biomarkers_daily(user_id, fetch_days)
    if lab_daily:
        data_sources_used.append("Lab Results")
        for date_str, lab_metrics in lab_daily.items():
            health_daily.setdefault(date_str, {}).update(lab_metrics)

    # 4d. Active conditions context for AI (variable prioritisation already handled in step 6)
    conditions_context = await _fetch_conditions_context(user_id)

    # 5. Compute data quality
    health_days = len(health_daily)
    nutrition_days = len(nutrition_daily)
    all_dates_union = set(health_daily.keys()) | set(nutrition_daily.keys())
    overlap_dates = set(health_daily.keys()) & set(nutrition_daily.keys())
    overlap_count = len(overlap_dates)
    days_with_data = len(all_dates_union)

    # For "all history" (period_days==0) use actual days found as the reference window.
    actual_period_days = days_with_data if ALL_HISTORY else period_days

    # Data quality is based on health data availability (Track 1 minimum),
    # boosted when nutrition overlap is also sufficient (Track 2).
    ref = max(actual_period_days * 0.7, 1)
    if health_days >= MIN_OVERLAPPING_DAYS:
        data_quality = min(1.0, (health_days * 0.5 + overlap_count * 0.5) / ref)
    else:
        data_quality = min(1.0, health_days / ref)

    now_str = datetime.now(timezone.utc).isoformat()

    # Hard gate: need at least MIN_OVERLAPPING_DAYS of health data to find any pattern.
    if health_days < MIN_OVERLAPPING_DAYS:
        src_note = (
            f" Connected sources: {', '.join(data_sources_used)}."
            if data_sources_used
            else ""
        )
        result = CorrelationResults(
            correlations=[],
            summary=(
                f"Need at least {MIN_OVERLAPPING_DAYS} days of health data. "
                f"Currently have {health_days} day(s) of wearable data.{src_note}"
            ),
            data_quality_score=data_quality,
            oura_days_available=health_days,
            nutrition_days_available=nutrition_days,
            days_with_data=days_with_data,
            data_sources_used=data_sources_used,
            computed_at=now_str,
            period_days=actual_period_days,
        )
        return result

    # 6. Fetch user's active health-condition variables (non-blocking; empty list on failure)
    try:
        from .health_conditions import get_condition_variables

        condition_vars = await get_condition_variables(user_id)
    except Exception:
        condition_vars = []

    if condition_vars:
        logger.info(
            "Correlation engine: %d condition variable(s) will lower thresholds for %s",
            len(condition_vars),
            user_id,
        )

    # 6b. Read agent_memory learned_patterns as personalised priors.
    learned_priors: List[Dict[str, Any]] = []
    try:
        prior_rows = await _supabase_get(
            "agent_memory",
            f"user_id=eq.{user_id}&memory_type=eq.learned_pattern&is_active=eq.true"
            f"&order=confidence_score.desc&limit=20",
        )
        for row in prior_rows or []:
            mv = row.get("memory_value") or {}
            if isinstance(mv, str):
                try:
                    mv = __import__("json").loads(mv)
                except Exception:
                    continue
            delta = mv.get("outcome_delta") or {}
            pattern = mv.get("pattern", "")
            pattern_nutrition_map: Dict[str, List[str]] = {
                "overtraining": ["total_calories", "total_protein_g", "total_carbs_g"],
                "inflammation": [
                    "total_sugar_g",
                    "total_carbs_g",
                    "glycemic_load_estimate",
                ],
                "poor_recovery": ["total_protein_g", "total_calories", "total_fat_g"],
                "sleep_disruption": [
                    "last_meal_hour",
                    "total_sugar_g",
                    "total_calories",
                ],
            }
            for oura_metric, pct_change in delta.items():
                if oura_metric in _OURA_VARS and abs(pct_change) > 3:
                    for nut_metric in pattern_nutrition_map.get(pattern, []):
                        learned_priors.append(
                            {
                                "nutrition_metric": nut_metric,
                                "oura_metric": oura_metric,
                                "expected_direction": "positive"
                                if pct_change > 0
                                else "negative",
                                "confidence": row.get("confidence_score", 0.5),
                            }
                        )
        if learned_priors:
            logger.info(
                "Correlation engine: %d learned prior(s) from N-of-1 outcomes for %s",
                len(learned_priors),
                user_id,
            )
    except Exception as exc:
        logger.warning("Could not load learned priors from agent_memory: %s", exc)
        learned_priors = []

    # 7. Build dynamic pairs for native device / symptom metrics
    available_health_metrics: Set[str] = set()
    for day_metrics in health_daily.values():
        available_health_metrics.update(day_metrics.keys())
    dynamic_native_pairs = _build_dynamic_native_pairs(available_health_metrics)
    if dynamic_native_pairs:
        logger.info(
            "Correlation engine: %d dynamic native pairs added for %s",
            len(dynamic_native_pairs),
            user_id,
        )

    # 8. Compute correlations
    raw_correlations = _compute_correlations(
        nutrition_daily,
        health_daily,
        condition_vars,
        learned_priors,
        dynamic_native_pairs,
    )

    # 9. AI summary (pass all data sources + user health profile so Claude can personalise)
    user_context = {
        k: v
        for k, v in {
            "conditions": conditions_context,
            "medications_supplements": meds_context,
            "labs": lab_context,
        }.items()
        if v
    }
    correlations, summary = await _generate_ai_summary(
        raw_correlations,
        period_days,
        data_sources_used,
        user_context,
        oura_days=health_days,
        nutrition_days=nutrition_days,
    )

    # 10. Cache
    await _save_to_cache(
        user_id,
        period_days,
        correlations,
        summary or "",
        data_quality,
        health_days,
        nutrition_days,
        data_sources_used,
        days_with_data,
    )

    return CorrelationResults(
        correlations=[Correlation(**c) for c in correlations],
        summary=summary,
        data_quality_score=data_quality,
        oura_days_available=health_days,
        nutrition_days_available=nutrition_days,
        days_with_data=days_with_data,
        data_sources_used=data_sources_used,
        computed_at=now_str,
        period_days=actual_period_days,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=CorrelationResults)
async def get_correlations(
    request: Request,
    days: int = Query(default=0, ge=0, le=99999),
    current_user: dict = Depends(UsageGate("correlations")),
):
    """
    Get nutrition ↔ health correlations for the authenticated user.
    Returns cached results if fresh, otherwise computes new correlations.
    """
    user_id = current_user["id"]

    # Check cache
    cached = await _get_cached_results(user_id, days)
    if cached:
        import json

        corr_data = cached.get("correlations", "[]")
        if isinstance(corr_data, str):
            corr_data = json.loads(corr_data)
        raw_sources = cached.get("data_sources_used", "[]")
        if isinstance(raw_sources, str):
            try:
                raw_sources = __import__("json").loads(raw_sources)
            except Exception:
                raw_sources = []
        cached_period = cached.get("days_with_data", 0) if days == 0 else days
        return CorrelationResults(
            correlations=[Correlation(**c) for c in corr_data],
            summary=cached.get("summary"),
            data_quality_score=cached.get("data_quality_score", 0),
            oura_days_available=cached.get("oura_days_available", 0),
            nutrition_days_available=cached.get("nutrition_days_available", 0),
            days_with_data=cached.get("days_with_data", 0),
            data_sources_used=raw_sources or [],
            computed_at=cached.get("computed_at", ""),
            period_days=cached_period,
        )

    bearer = request.headers.get("Authorization")
    return await _compute_and_cache(current_user, days, bearer)


@router.post("/refresh", response_model=CorrelationResults)
async def refresh_correlations(
    request: Request,
    days: int = Query(default=0, ge=0, le=99999),
    current_user: dict = Depends(UsageGate("correlations")),
):
    """Force recompute correlations (ignores cache)."""
    bearer = request.headers.get("Authorization")
    return await _compute_and_cache(current_user, days, bearer)


@router.get("/detail/{correlation_id}")
async def get_correlation_detail(
    correlation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get detail for a single correlation by ID."""
    import json

    user_id = current_user["id"]

    # Search in cached results
    for period in (14, 7):
        cached = await _get_cached_results(user_id, period)
        if not cached:
            continue
        corr_data = cached.get("correlations", "[]")
        if isinstance(corr_data, str):
            corr_data = json.loads(corr_data)
        for c in corr_data:
            if c.get("id") == correlation_id:
                return Correlation(**c)

    raise HTTPException(status_code=404, detail="Correlation not found")


@router.get("/summary")
async def get_correlation_summary(
    current_user: dict = Depends(get_current_user),
):
    """
    Quick summary for dashboard widget.
    Returns the AI summary and top 3 correlations (if cached).
    """
    import json

    user_id = current_user["id"]
    cached = await _get_cached_results(user_id, 14)
    if not cached:
        cached = await _get_cached_results(user_id, 7)

    if not cached:
        return {
            "summary": None,
            "top_correlations": [],
            "data_quality_score": 0,
            "has_data": False,
        }

    corr_data = cached.get("correlations", "[]")
    if isinstance(corr_data, str):
        corr_data = json.loads(corr_data)

    top_3 = [Correlation(**c) for c in corr_data[:3]]

    return {
        "summary": cached.get("summary"),
        "top_correlations": top_3,
        "data_quality_score": cached.get("data_quality_score", 0),
        "has_data": True,
    }


@router.get("/causal-graph", response_model=CausalGraph)
async def get_causal_graph(
    request: Request,
    current_user: dict = Depends(UsageGate("correlations")),
    days: int = Query(default=0, ge=0, le=99999),
) -> CausalGraph:
    """
    Get causal graph showing directional relationships between nutrition and health metrics.
    Uses Granger causality testing to infer likely causal directions.
    Pro+ feature - advanced statistical analysis.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # days=0 means "all history" — fetch without a practical window cap.
    fetch_days = 99999 if days == 0 else days

    # Extract bearer token for nutrition service
    bearer = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        bearer = auth_header

    # Fetch Oura timeline data
    try:
        timeline = await get_timeline(days=fetch_days, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for causal graph: %s", exc)
        timeline = []

    # Build canonical health_daily from all connected devices
    health_daily, device_sources = await _build_health_daily(
        user_id, fetch_days, timeline
    )
    causal_sources: List[str] = list(
        dict.fromkeys(device_sources)
    )  # preserve order, dedupe

    # Merge symptom data as outcome variables
    symptoms_daily = await _fetch_symptoms_daily(user_id, fetch_days)
    if symptoms_daily:
        causal_sources.append("Symptom Journal")
    for date_str, symp_metrics in symptoms_daily.items():
        health_daily.setdefault(date_str, {}).update(symp_metrics)

    # Merge medication adherence as outcome variable + track source
    adherence_daily, _, med_src = await _fetch_medications_supplements_context(
        user_id, fetch_days
    )
    causal_sources.extend(s for s in med_src if s not in causal_sources)
    for date_str, adh_metrics in adherence_daily.items():
        health_daily.setdefault(date_str, {}).update(adh_metrics)

    # Merge lab biomarker draws (>= 2 draws required for statistical use)
    lab_daily, _ = await _fetch_lab_biomarkers_daily(user_id, fetch_days)
    if lab_daily:
        causal_sources.append("Lab Results")
    for date_str, lab_metrics in lab_daily.items():
        health_daily.setdefault(date_str, {}).update(lab_metrics)

    # Fetch nutrition data
    nutrition_daily = await _fetch_nutrition_daily(bearer, fetch_days)
    if nutrition_daily:
        causal_sources.append("Nutrition Logs")

    # Actual days found (used in response so UI can show "All · Xd")
    causal_days_with_data = len(set(health_daily.keys()) | set(nutrition_daily.keys()))

    # Fetch condition variables so condition-specific pairs are included in the graph
    try:
        from .health_conditions import get_condition_variables

        condition_vars = await get_condition_variables(user_id)
    except Exception:
        condition_vars = []

    # Build dynamic native pairs
    available_health_metrics: Set[str] = set()
    for day_metrics in health_daily.values():
        available_health_metrics.update(day_metrics.keys())
    dynamic_native_pairs = _build_dynamic_native_pairs(available_health_metrics)

    # Compute correlations (with condition-aware + native device pairs)
    correlations = _compute_correlations(
        nutrition_daily,
        health_daily,
        condition_vars,
        dynamic_native_pairs=dynamic_native_pairs,
    )

    if not correlations:
        return CausalGraph(
            nodes=[],
            edges=[],
            computed_at=datetime.now(timezone.utc).isoformat(),
            confidence_threshold=0.5,
            data_sources_used=causal_sources,
            days_with_data=causal_days_with_data,
        )

    # Compute causal graph
    graph_data = _compute_causal_graph(correlations, nutrition_daily, health_daily)

    return CausalGraph(
        nodes=graph_data["nodes"],
        edges=[CausalEdge(**edge) for edge in graph_data["edges"]],
        computed_at=graph_data["computed_at"],
        confidence_threshold=graph_data["confidence_threshold"],
        data_sources_used=causal_sources,
        days_with_data=causal_days_with_data,
    )
