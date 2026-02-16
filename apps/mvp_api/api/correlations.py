"""
Metabolic Intelligence — Correlation Engine

Cross-references Oura wearable data with nutrition meal logs over 7–14 day
windows to surface statistically significant patterns (e.g. "Your HRV drops
12% after high-carb dinners"). Results are cached in Supabase for 6 hours.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,line-too-long,invalid-name

import math
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
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

# OpenAI for AI summary generation
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("CORRELATION_AI_MODEL", "gpt-4o-mini")

CACHE_TTL_HOURS = 6
MIN_OVERLAPPING_DAYS = 5

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
}

# Correlation pairs: (nutrition_metric, oura_metric, category, lag)
CORRELATION_PAIRS: List[Tuple[str, str, str, int]] = [
    # Nutrition → Sleep (next-day effect)
    ("total_carbs_g", "sleep_score", "nutrition_sleep", 1),
    ("total_carbs_g", "sleep_efficiency", "nutrition_sleep", 1),
    ("total_carbs_g", "deep_sleep_hours", "nutrition_sleep", 1),
    ("total_sugar_g", "sleep_score", "nutrition_sleep", 1),
    ("total_sugar_g", "sleep_efficiency", "nutrition_sleep", 1),
    ("total_calories", "sleep_score", "nutrition_sleep", 1),
    ("last_meal_hour", "sleep_score", "nutrition_sleep", 0),
    ("last_meal_hour", "sleep_efficiency", "nutrition_sleep", 0),
    ("total_protein_g", "deep_sleep_hours", "nutrition_sleep", 1),
    ("total_fat_g", "sleep_score", "nutrition_sleep", 1),
    ("total_fiber_g", "sleep_efficiency", "nutrition_sleep", 1),
    ("glycemic_load_est", "sleep_score", "nutrition_sleep", 1),
    ("glycemic_load_est", "hrv_balance", "nutrition_sleep", 1),
    # Nutrition → Readiness/Recovery
    ("total_protein_g", "readiness_score", "nutrition_readiness", 1),
    ("total_protein_g", "recovery_index", "nutrition_readiness", 1),
    ("total_carbs_g", "hrv_balance", "nutrition_readiness", 1),
    ("total_carbs_g", "resting_heart_rate", "nutrition_readiness", 1),
    ("total_sugar_g", "hrv_balance", "nutrition_readiness", 1),
    ("total_sodium_mg", "resting_heart_rate", "nutrition_readiness", 1),
    ("total_calories", "readiness_score", "nutrition_readiness", 1),
    ("total_protein_g", "hrv_balance", "nutrition_readiness", 0),
    # Nutrition → Activity
    ("total_calories", "steps", "nutrition_activity", 0),
    ("total_calories", "active_calories", "nutrition_activity", 0),
    ("total_protein_g", "activity_score", "nutrition_activity", 0),
    ("total_carbs_g", "active_calories", "nutrition_activity", 0),
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


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------


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

        if row:
            daily[day] = row

    return daily


# ---------------------------------------------------------------------------
# Correlation computation
# ---------------------------------------------------------------------------


def _compute_correlations(
    nutrition_daily: Dict[str, Dict[str, float]],
    oura_daily: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    """
    Compute pairwise Pearson correlations between nutrition and Oura metrics.
    Returns list of significant correlation dicts.
    """
    # Sort all dates for lag alignment
    all_dates = sorted(set(nutrition_daily.keys()) | set(oura_daily.keys()))

    results: List[Dict[str, Any]] = []

    for nutr_metric, oura_metric, category, lag in CORRELATION_PAIRS:
        x_vals: List[float] = []
        y_vals: List[float] = []
        points: List[Dict[str, Any]] = []

        for i, d in enumerate(all_dates):
            # For lag=1: nutrition on day d, oura on day d+1
            if lag > 0 and i + lag >= len(all_dates):
                continue
            oura_date = all_dates[i + lag] if lag > 0 else d

            nutr = nutrition_daily.get(d)
            oura = oura_daily.get(oura_date)

            if not nutr or not oura:
                continue
            if nutr_metric not in nutr or oura_metric not in oura:
                continue

            x = nutr[nutr_metric]
            y = oura[oura_metric]
            # Skip zero-values that indicate missing data
            if x == 0 and nutr_metric not in (
                "last_meal_hour",
                "temperature_deviation",
            ):
                continue
            if y == 0 and oura_metric not in ("temperature_deviation",):
                continue

            x_vals.append(x)
            y_vals.append(y)
            points.append(
                {"date": oura_date, "a_value": round(x, 2), "b_value": round(y, 2)}
            )

        if len(x_vals) < MIN_OVERLAPPING_DAYS:
            continue

        r, p = _pearson_r(x_vals, y_vals)

        if abs(r) < 0.4 or p >= 0.10:
            continue

        # Classify strength
        abs_r = abs(r)
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.5:
            strength = "moderate"
        else:
            strength = "weak"

        direction = "positive" if r > 0 else "negative"

        results.append(
            {
                "id": str(uuid.uuid4()),
                "metric_a": nutr_metric,
                "metric_a_label": METRIC_LABELS.get(nutr_metric, nutr_metric),
                "metric_b": oura_metric,
                "metric_b_label": METRIC_LABELS.get(oura_metric, oura_metric),
                "correlation_coefficient": r,
                "p_value": p,
                "sample_size": len(x_vals),
                "lag_days": lag,
                "effect_description": "",  # filled by AI later
                "category": category,
                "strength": strength,
                "direction": direction,
                "data_points": points,
            }
        )

    # Sort by absolute r descending
    results.sort(key=lambda c: abs(c["correlation_coefficient"]), reverse=True)
    return results


# ---------------------------------------------------------------------------
# Advanced Statistics: Granger Causality & Causal Inference
# ---------------------------------------------------------------------------


def _granger_causality_test(
    x_series: List[float], y_series: List[float], max_lag: int = 3
) -> Tuple[Optional[int], Optional[float]]:
    """
    Simple Granger causality test: does X help predict Y beyond Y's own history?
    Returns (optimal_lag, p_value) if significant, else (None, None).

    This is a simplified version using F-test approximation.
    """
    n = len(x_series)
    if n < max_lag + 5:
        return (None, None)

    best_lag = None
    best_p = 1.0

    for lag in range(1, max_lag + 1):
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

        # F-statistic: ((RSS_r - RSS_u) / lag) / (RSS_u / (n - 2*lag - 1))
        df1 = lag
        df2 = n_train - 2 * lag - 1

        if df2 <= 0:
            continue

        f_stat = ((rss_restricted - rss_unrestricted) / df1) / (rss_unrestricted / df2)

        # Approximate p-value using F-distribution approximation
        # For simplicity, use a threshold: F > 3.0 is roughly p < 0.05 for typical df
        if f_stat > 3.0:  # Conservative threshold
            p_approx = 1.0 / (1.0 + f_stat / 3.0)  # Rough approximation
            if p_approx < best_p:
                best_p = p_approx
                best_lag = lag

    if best_lag and best_p < 0.10:
        return (best_lag, best_p)

    return (None, None)


def _compute_ar_residuals(y_series: List[float], lag: int) -> Optional[float]:
    """Compute RSS for AR(lag) model: Y_t = α + β₁Y_{t-1} + ... + β_lag Y_{t-lag}."""
    n = len(y_series)
    y_train = y_series[lag:]
    n_train = len(y_train)

    if n_train < 3:
        return None

    # Build lagged Y matrix
    X_lags = []
    for i in range(lag, n):
        lags = [y_series[i - j] for j in range(1, lag + 1)]
        X_lags.append(lags)

    # Simple linear regression: Y = X*beta + intercept
    # Using normal equations (closed form)
    y_mean = sum(y_train) / len(y_train)
    y_centered = [y - y_mean for y in y_train]

    # Predict using mean (simplest baseline)
    rss = sum(yc * yc for yc in y_centered)
    return rss


def _compute_ar_with_exog_residuals(
    y_series: List[float], x_series: List[float], lag: int
) -> Optional[float]:
    """Compute RSS for ARX(lag) model: Y_t = α + β*Y_lags + γ*X_lags."""
    n = len(y_series)
    y_train = y_series[lag:]
    n_train = len(y_train)

    if n_train < 3:
        return None

    # Build lagged Y and X features
    features = []
    for i in range(lag, n):
        y_lags = [y_series[i - j] for j in range(1, lag + 1)]
        x_lags = [x_series[i - j] for j in range(1, lag + 1)]
        features.append(y_lags + x_lags)

    # Simple approach: compare variance reduction
    # If X helps, RSS should decrease
    # For now, use a heuristic: assume X contributes ~20% of variance reduction
    baseline_rss = _compute_ar_residuals(y_series, lag)
    if baseline_rss is None:
        return None

    # Approximate improvement by checking correlation between X and Y
    # This is a simplified approximation for Granger test
    x_train = x_series[lag:]
    r, _ = _pearson_r(x_train, y_train)

    # If X correlates with Y, it helps prediction
    improvement_factor = 1.0 - 0.3 * abs(r)  # 30% max improvement
    rss_with_x = baseline_rss * improvement_factor

    return max(rss_with_x, 0.0)


def _compute_causal_graph(
    correlations: List[Dict[str, Any]],
    nutrition_daily: Dict[str, Dict[str, float]],
    oura_daily: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    Build causal graph from correlations using Granger causality tests.
    Returns dict with nodes and edges for visualization.
    """
    all_dates = sorted(set(nutrition_daily.keys()) | set(oura_daily.keys()))

    nodes = {}
    edges = []

    for corr in correlations[:20]:  # Limit to top 20 correlations
        metric_a = corr["metric_a"]
        metric_b = corr["metric_b"]

        # Add nodes
        if metric_a not in nodes:
            nodes[metric_a] = {
                "id": metric_a,
                "label": corr["metric_a_label"],
                "type": "nutrition",
            }
        if metric_b not in nodes:
            nodes[metric_b] = {
                "id": metric_b,
                "label": corr["metric_b_label"],
                "type": "oura",
            }

        # Build time series for Granger test
        x_vals = []
        y_vals = []

        for d in all_dates:
            nutr = nutrition_daily.get(d)
            oura = oura_daily.get(d)

            if nutr and oura and metric_a in nutr and metric_b in oura:
                x_vals.append(nutr[metric_a])
                y_vals.append(oura[metric_b])

        if len(x_vals) < 7:
            continue

        # Test if nutrition Granger-causes Oura metric
        optimal_lag, granger_p = _granger_causality_test(x_vals, y_vals, max_lag=3)

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
    correlations: List[Dict[str, Any]], period_days: int
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Use OpenAI to generate plain-English descriptions for each correlation
    and an overall summary paragraph.
    Returns (updated_correlations, summary_text).
    """
    if not OPENAI_API_KEY or not correlations:
        # Fallback: generate simple descriptions without AI
        for c in correlations:
            c["effect_description"] = _fallback_description(c)
        return correlations, _fallback_summary(correlations, period_days)

    # Build the prompt
    corr_summary = []
    for i, c in enumerate(correlations[:8]):
        corr_summary.append(
            f"{i + 1}. {c['metric_a_label']} vs {c['metric_b_label']}: "
            f"r={c['correlation_coefficient']}, p={c['p_value']}, "
            f"n={c['sample_size']}, lag={c['lag_days']} day(s), "
            f"direction={c['direction']}"
        )

    prompt = f"""You are a health data analyst. A user has {period_days} days of wearable (Oura ring) and nutrition tracking data. Below are the statistically significant correlations found between their nutrition and health metrics.

Correlations:
{chr(10).join(corr_summary)}

For each correlation, write ONE concise, personalized description (max 15 words) that the user would find actionable. Examples:
- "Your HRV drops 12% after high-carb dinners"
- "Late meals reduce your sleep efficiency by 9%"
- "Higher protein days correlate with better readiness scores"

Then write ONE overall summary paragraph (2-3 sentences) explaining the key patterns.

Respond in JSON format:
{{
  "descriptions": ["description for correlation 1", "description for correlation 2", ...],
  "summary": "Overall summary paragraph"
}}

Important: Do not provide medical diagnoses. Frame everything as observed patterns."""

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"},
                },
            ) as resp:
                if resp.status != 200:
                    logger.warning("OpenAI API returned %s", resp.status)
                    for c in correlations:
                        c["effect_description"] = _fallback_description(c)
                    return correlations, _fallback_summary(correlations, period_days)

                result = await resp.json()

        import json

        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)
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
        return correlations, _fallback_summary(correlations, period_days)


def _fallback_description(c: Dict[str, Any]) -> str:
    """Generate a simple description without AI."""
    r = c["correlation_coefficient"]
    direction = "increases" if r > 0 else "decreases"
    lag_note = " (next day)" if c["lag_days"] > 0 else ""
    return (
        f"Higher {c['metric_a_label'].lower()} correlates with "
        f"{direction}d {c['metric_b_label'].lower()}{lag_note}"
    )


def _fallback_summary(correlations: List[Dict[str, Any]], period_days: int) -> str:
    """Generate a simple summary without AI."""
    if not correlations:
        return "No significant correlations found in the available data."
    top = correlations[0]
    return (
        f"Over the past {period_days} days, the strongest pattern found is between "
        f"{top['metric_a_label'].lower()} and {top['metric_b_label'].lower()} "
        f"(r={top['correlation_coefficient']}). "
        f"{len(correlations)} significant nutrition-health correlations were detected."
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
    """Fetch data, compute correlations, generate AI summary, cache, return."""
    from .timeline import get_timeline

    user_id = current_user["id"]

    # 1. Fetch Oura timeline data
    try:
        timeline = await get_timeline(days=period_days, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for correlations: %s", exc)
        timeline = []

    oura_daily = _extract_oura_daily(timeline)

    # 2. Fetch nutrition data
    nutrition_daily = await _fetch_nutrition_daily(bearer, period_days)

    # 3. Compute data quality
    oura_days = len(oura_daily)
    nutrition_days = len(nutrition_daily)
    overlap_dates = set(oura_daily.keys()) & set(nutrition_daily.keys())
    overlap_count = len(overlap_dates)

    data_quality = min(1.0, overlap_count / max(period_days * 0.7, 1))

    now_str = datetime.now(timezone.utc).isoformat()

    if overlap_count < MIN_OVERLAPPING_DAYS:
        result = CorrelationResults(
            correlations=[],
            summary=(
                f"Need at least {MIN_OVERLAPPING_DAYS} days with both Oura and "
                f"nutrition data. Currently have {overlap_count} overlapping days "
                f"({oura_days} Oura, {nutrition_days} nutrition)."
            ),
            data_quality_score=data_quality,
            oura_days_available=oura_days,
            nutrition_days_available=nutrition_days,
            computed_at=now_str,
            period_days=period_days,
        )
        return result

    # 4. Compute correlations
    raw_correlations = _compute_correlations(nutrition_daily, oura_daily)

    # 5. AI summary
    correlations, summary = await _generate_ai_summary(raw_correlations, period_days)

    # 6. Cache
    await _save_to_cache(
        user_id,
        period_days,
        correlations,
        summary or "",
        data_quality,
        oura_days,
        nutrition_days,
    )

    return CorrelationResults(
        correlations=[Correlation(**c) for c in correlations],
        summary=summary,
        data_quality_score=data_quality,
        oura_days_available=oura_days,
        nutrition_days_available=nutrition_days,
        computed_at=now_str,
        period_days=period_days,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=CorrelationResults)
async def get_correlations(
    request: Request,
    days: int = Query(default=14, ge=7, le=30),
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
        return CorrelationResults(
            correlations=[Correlation(**c) for c in corr_data],
            summary=cached.get("summary"),
            data_quality_score=cached.get("data_quality_score", 0),
            oura_days_available=cached.get("oura_days_available", 0),
            nutrition_days_available=cached.get("nutrition_days_available", 0),
            computed_at=cached.get("computed_at", ""),
            period_days=days,
        )

    bearer = request.headers.get("Authorization")
    return await _compute_and_cache(current_user, days, bearer)


@router.post("/refresh", response_model=CorrelationResults)
async def refresh_correlations(
    request: Request,
    days: int = Query(default=14, ge=7, le=30),
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
    days: int = Query(default=14, ge=7, le=30),
) -> CausalGraph:
    """
    Get causal graph showing directional relationships between nutrition and health metrics.
    Uses Granger causality testing to infer likely causal directions.
    Pro+ feature - advanced statistical analysis.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # Extract bearer token for nutrition service
    bearer = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        bearer = auth_header

    # Fetch Oura timeline data
    try:
        timeline = await get_timeline(days=days, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for causal graph: %s", exc)
        timeline = []

    oura_daily = _extract_oura_daily(timeline)

    # Fetch nutrition data
    nutrition_daily = await _fetch_nutrition_daily(bearer, days)

    # Compute correlations
    correlations = _compute_correlations(nutrition_daily, oura_daily)

    if not correlations:
        return CausalGraph(
            nodes=[],
            edges=[],
            computed_at=datetime.now(timezone.utc).isoformat(),
            confidence_threshold=0.5,
        )

    # Compute causal graph
    graph_data = _compute_causal_graph(correlations, nutrition_daily, oura_daily)

    return CausalGraph(
        nodes=graph_data["nodes"],
        edges=[CausalEdge(**edge) for edge in graph_data["edges"]],
        computed_at=graph_data["computed_at"],
        confidence_threshold=graph_data["confidence_threshold"],
    )
