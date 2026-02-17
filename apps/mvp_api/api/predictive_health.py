"""
Predictive Health API — Phase 4: Health Predictions & Forecasting

AI-powered predictions for health metrics, risk assessments, trend analysis,
and personalized health scores using statistical and machine learning models.
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
    _supabase_insert,
)

logger = get_logger(__name__)
router = APIRouter()

NUTRITION_SERVICE_URL = os.environ.get(
    "NUTRITION_SERVICE_URL", "http://localhost:8007"
).rstrip("/")
NUTRITION_TIMEOUT_S = float(os.environ.get("NUTRITION_SERVICE_TIMEOUT_S", "8.0"))

# OpenAI for AI-enhanced predictions
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("PREDICTION_AI_MODEL", "gpt-4o-mini")

MIN_HISTORICAL_DAYS = 14  # Minimum days needed for predictions
PREDICTION_CACHE_HOURS = 12  # Cache predictions for 12 hours

# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class PredictionRange(BaseModel):
    """Confidence interval for prediction."""

    lower: float
    upper: float


class HealthPrediction(BaseModel):
    """Single health metric prediction."""

    id: str
    prediction_type: str  # sleep_score, readiness_score, hrv_forecast, etc.
    metric_name: str
    prediction_date: str
    prediction_horizon_days: int
    predicted_value: float
    confidence_score: float
    prediction_range: Optional[PredictionRange] = None
    actual_value: Optional[float] = None
    prediction_error: Optional[float] = None
    model_type: str  # statistical, ml, hybrid
    model_version: str
    features_used: List[str]
    contributing_factors: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    status: str  # pending, confirmed, inaccurate
    created_at: str


class RiskFactor(BaseModel):
    """Individual risk factor."""

    factor: str
    impact_score: float  # 0-1
    description: str


class HealthRiskAssessment(BaseModel):
    """Risk assessment for health conditions."""

    id: str
    risk_type: str  # symptom_flare, sleep_decline, recovery_decline, burnout
    risk_category: str  # cardiovascular, metabolic, mental_health, sleep, recovery
    risk_score: float  # 0-1
    risk_level: str  # low, moderate, high, critical
    risk_window_start: str
    risk_window_end: str
    contributing_factors: List[RiskFactor]
    protective_factors: List[RiskFactor]
    recommendations: List[Dict[str, Any]]
    early_warning_signs: List[str]
    historical_patterns: List[Dict[str, Any]]
    confidence_score: float
    user_acknowledged: bool
    is_active: bool
    created_at: str


class HealthTrend(BaseModel):
    """Trend analysis for a health metric."""

    id: str
    metric_name: str
    trend_type: str  # improving, declining, stable, fluctuating
    analysis_start_date: str
    analysis_end_date: str
    window_days: int
    slope: float  # rate of change
    r_squared: float  # trend strength
    average_value: float
    std_deviation: float
    percent_change: float
    absolute_change: float
    detected_patterns: List[str]
    anomalies: List[Dict[str, Any]]
    forecast_7d: Optional[float] = None
    forecast_14d: Optional[float] = None
    forecast_30d: Optional[float] = None
    interpretation: str
    significance: str  # clinically_significant, notable, minor, noise
    created_at: str


class PersonalizedHealthScore(BaseModel):
    """Personalized health score/index."""

    id: str
    score_date: str
    score_type: str  # overall_health, recovery_capacity, resilience, metabolic_health
    score_value: float  # 0-100
    percentile: Optional[float] = None
    component_scores: Dict[str, float]
    positive_factors: List[str]
    negative_factors: List[str]
    trend_7d: str  # up, down, stable
    change_7d: float
    improvement_recommendations: List[Dict[str, Any]]
    created_at: str


class PredictionsResponse(BaseModel):
    """Response containing multiple predictions."""

    predictions: List[HealthPrediction]
    generated_at: str
    days_of_data: int
    data_quality_score: float


class RisksResponse(BaseModel):
    """Response containing risk assessments."""

    risks: List[HealthRiskAssessment]
    overall_risk_level: str
    generated_at: str


class TrendsResponse(BaseModel):
    """Response containing trend analyses."""

    trends: List[HealthTrend]
    generated_at: str


# ---------------------------------------------------------------------------
# Statistical Forecasting Functions
# ---------------------------------------------------------------------------


def _moving_average(values: List[float], window: int = 3) -> List[float]:
    """Compute simple moving average."""
    if len(values) < window:
        return values

    result = []
    for i in range(len(values)):
        if i < window - 1:
            result.append(values[i])
        else:
            avg = sum(values[i - window + 1 : i + 1]) / window
            result.append(avg)

    return result


def _exponential_smoothing(
    values: List[float], alpha: float = 0.3
) -> Tuple[List[float], float]:
    """
    Exponential smoothing for time series.
    Returns (smoothed_values, next_forecast).
    """
    if not values:
        return [], 0.0

    smoothed = [values[0]]
    for i in range(1, len(values)):
        s = alpha * values[i] + (1 - alpha) * smoothed[-1]
        smoothed.append(s)

    # Forecast next value
    forecast = smoothed[-1]
    return smoothed, forecast


def _linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """
    Simple linear regression: y = mx + b
    Returns (slope, intercept, r_squared).
    """
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate slope and intercept
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0, mean_y, 0.0

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x

    # Calculate R²
    y_pred = [slope * x[i] + intercept for i in range(n)]
    ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))

    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    r_squared = max(0.0, min(1.0, r_squared))

    return slope, intercept, r_squared


def _forecast_linear(
    values: List[float], days_ahead: int
) -> Tuple[float, float, float]:
    """
    Linear forecast for future values.
    Returns (forecast, lower_bound, upper_bound).
    """
    if len(values) < 3:
        return values[-1] if values else 0.0, 0.0, 0.0

    x = [float(i) for i in range(len(values))]
    slope, intercept, r_squared = _linear_regression(x, values)

    # Forecast
    forecast_x = len(values) + days_ahead - 1
    forecast = slope * forecast_x + intercept

    # Confidence interval (simple approach using std dev)
    std_dev = math.sqrt(
        sum((values[i] - (slope * i + intercept)) ** 2 for i in range(len(values)))
        / len(values)
    )
    margin = 1.96 * std_dev  # 95% confidence interval

    lower = forecast - margin
    upper = forecast + margin

    return forecast, lower, upper


def _detect_trend_type(slope: float, r_squared: float, threshold: float = 0.01) -> str:
    """
    Classify trend as improving, declining, stable, or fluctuating.
    """
    if r_squared < 0.3:
        return "fluctuating"

    if abs(slope) < threshold:
        return "stable"

    return "improving" if slope > 0 else "declining"


def _calculate_anomalies(values: List[float], threshold_std: float = 2.0) -> List[int]:
    """
    Detect anomalies using standard deviation threshold.
    Returns list of indices of anomalous values.
    """
    if len(values) < 3:
        return []

    mean = sum(values) / len(values)
    std_dev = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

    if std_dev == 0:
        return []

    anomalies = []
    for i, v in enumerate(values):
        z_score = abs((v - mean) / std_dev)
        if z_score > threshold_std:
            anomalies.append(i)

    return anomalies


# ---------------------------------------------------------------------------
# Risk Assessment Functions
# ---------------------------------------------------------------------------


def _assess_sleep_decline_risk(
    sleep_scores: List[float], dates: List[str]
) -> Optional[Dict[str, Any]]:
    """Assess risk of sleep decline."""
    if len(sleep_scores) < 7:
        return None

    # Calculate trend
    x = [float(i) for i in range(len(sleep_scores))]
    slope, _, r_squared = _linear_regression(x, sleep_scores)

    recent_avg = sum(sleep_scores[-7:]) / 7
    overall_avg = sum(sleep_scores) / len(sleep_scores)

    # Risk scoring
    risk_score = 0.0
    factors = []

    # Declining trend
    if slope < -0.5 and r_squared > 0.3:
        risk_score += 0.3
        factors.append(
            {
                "factor": "Declining sleep trend",
                "impact_score": 0.3,
                "description": f"Sleep scores decreasing by {abs(slope):.1f} points per day",
            }
        )

    # Below baseline
    if recent_avg < overall_avg - 5:
        risk_score += 0.3
        factors.append(
            {
                "factor": "Below personal baseline",
                "impact_score": 0.3,
                "description": f"Recent average {recent_avg:.0f} vs baseline {overall_avg:.0f}",
            }
        )

    # Low absolute score
    if recent_avg < 70:
        risk_score += 0.2
        factors.append(
            {
                "factor": "Low sleep score",
                "impact_score": 0.2,
                "description": f"Average sleep score of {recent_avg:.0f} is below optimal range",
            }
        )

    # High variability
    std_dev = math.sqrt(sum((v - recent_avg) ** 2 for v in sleep_scores[-7:]) / 7)
    if std_dev > 10:
        risk_score += 0.2
        factors.append(
            {
                "factor": "High variability",
                "impact_score": 0.2,
                "description": f"Sleep quality varying significantly (±{std_dev:.0f} points)",
            }
        )

    if risk_score < 0.3:
        return None

    risk_level = (
        "critical" if risk_score >= 0.7 else "high" if risk_score >= 0.5 else "moderate"
    )

    return {
        "risk_type": "sleep_decline",
        "risk_category": "sleep",
        "risk_score": min(risk_score, 1.0),
        "risk_level": risk_level,
        "contributing_factors": factors,
        "recommendations": [
            {
                "priority": "high",
                "action": "Establish consistent sleep schedule",
                "rationale": "Improves sleep quality and reduces variability",
            },
            {
                "priority": "high",
                "action": "Review evening routine and screen time",
                "rationale": "Late light exposure can disrupt sleep",
            },
            {
                "priority": "medium",
                "action": "Consider sleep environment optimization",
                "rationale": "Temperature, noise, and light affect sleep quality",
            },
        ],
        "early_warning_signs": [
            "Difficulty falling asleep",
            "Waking frequently during night",
            "Feeling unrefreshed in morning",
            "Increased caffeine consumption",
        ],
    }


def _assess_recovery_decline_risk(
    readiness_scores: List[float], hrv_values: List[float]
) -> Optional[Dict[str, Any]]:
    """Assess risk of recovery decline."""
    if len(readiness_scores) < 7:
        return None

    recent_readiness = sum(readiness_scores[-7:]) / 7
    overall_readiness = sum(readiness_scores) / len(readiness_scores)

    risk_score = 0.0
    factors = []

    # Low readiness
    if recent_readiness < 70:
        risk_score += 0.3
        factors.append(
            {
                "factor": "Low readiness score",
                "impact_score": 0.3,
                "description": f"Average readiness {recent_readiness:.0f} indicates poor recovery",
            }
        )

    # Declining HRV
    if len(hrv_values) >= 7:
        hrv_recent = sum(hrv_values[-7:]) / 7
        hrv_overall = sum(hrv_values) / len(hrv_values)

        if hrv_recent < hrv_overall - 5:
            risk_score += 0.3
            factors.append(
                {
                    "factor": "Declining HRV",
                    "impact_score": 0.3,
                    "description": "Heart rate variability below baseline suggests accumulated stress",
                }
            )

    # Consistent low scores
    low_days = sum(1 for s in readiness_scores[-7:] if s < 70)
    if low_days >= 5:
        risk_score += 0.2
        factors.append(
            {
                "factor": "Persistent low recovery",
                "impact_score": 0.2,
                "description": f"{low_days} out of 7 days with poor readiness",
            }
        )

    if risk_score < 0.3:
        return None

    risk_level = (
        "critical" if risk_score >= 0.7 else "high" if risk_score >= 0.5 else "moderate"
    )

    return {
        "risk_type": "recovery_decline",
        "risk_category": "recovery",
        "risk_score": min(risk_score, 1.0),
        "risk_level": risk_level,
        "contributing_factors": factors,
        "recommendations": [
            {
                "priority": "high",
                "action": "Reduce training intensity",
                "rationale": "Allow body to recover and prevent overtraining",
            },
            {
                "priority": "high",
                "action": "Prioritize sleep quality and duration",
                "rationale": "Sleep is primary recovery mechanism",
            },
            {
                "priority": "medium",
                "action": "Review nutrition and hydration",
                "rationale": "Proper fueling supports recovery",
            },
        ],
        "early_warning_signs": [
            "Persistent fatigue",
            "Decreased performance",
            "Elevated resting heart rate",
            "Mood changes or irritability",
        ],
    }


def _assess_burnout_risk(
    sleep_scores: List[float],
    readiness_scores: List[float],
    activity_scores: List[float],
) -> Optional[Dict[str, Any]]:
    """Assess risk of burnout based on multiple metrics."""
    if len(sleep_scores) < 14 or len(readiness_scores) < 14:
        return None

    recent_sleep = sum(sleep_scores[-14:]) / 14
    recent_readiness = sum(readiness_scores[-14:]) / 14

    risk_score = 0.0
    factors = []

    # Poor sleep + poor recovery = burnout risk
    if recent_sleep < 70 and recent_readiness < 70:
        risk_score += 0.4
        factors.append(
            {
                "factor": "Combined sleep and recovery decline",
                "impact_score": 0.4,
                "description": "Both sleep and readiness below optimal levels",
            }
        )

    # High activity with low recovery
    if len(activity_scores) >= 7:
        recent_activity = sum(activity_scores[-7:]) / 7
        if recent_activity > 80 and recent_readiness < 70:
            risk_score += 0.3
            factors.append(
                {
                    "factor": "Overtraining pattern",
                    "impact_score": 0.3,
                    "description": "High activity without adequate recovery",
                }
            )

    # Sustained poor metrics
    low_sleep_days = sum(1 for s in sleep_scores[-14:] if s < 70)
    low_readiness_days = sum(1 for s in readiness_scores[-14:] if s < 70)

    if low_sleep_days >= 10 or low_readiness_days >= 10:
        risk_score += 0.3
        factors.append(
            {
                "factor": "Chronic poor recovery",
                "impact_score": 0.3,
                "description": "Extended period of suboptimal metrics",
            }
        )

    if risk_score < 0.4:
        return None

    risk_level = "critical" if risk_score >= 0.7 else "high"

    return {
        "risk_type": "burnout",
        "risk_category": "mental_health",
        "risk_score": min(risk_score, 1.0),
        "risk_level": risk_level,
        "contributing_factors": factors,
        "recommendations": [
            {
                "priority": "critical",
                "action": "Schedule rest and recovery days",
                "rationale": "Prevent burnout and maintain long-term health",
            },
            {
                "priority": "high",
                "action": "Reduce overall training load",
                "rationale": "Body needs time to adapt and recover",
            },
            {
                "priority": "high",
                "action": "Practice stress management techniques",
                "rationale": "Mental recovery is as important as physical",
            },
            {
                "priority": "medium",
                "action": "Consider professional support",
                "rationale": "Burnout may require expert guidance",
            },
        ],
        "early_warning_signs": [
            "Loss of motivation",
            "Persistent fatigue despite rest",
            "Mood disturbances",
            "Decreased performance",
            "Sleep disturbances",
            "Increased susceptibility to illness",
        ],
    }


# ---------------------------------------------------------------------------
# Data Fetching Helpers
# ---------------------------------------------------------------------------


async def _fetch_nutrition_daily(
    bearer: Optional[str], days: int
) -> Dict[str, Dict[str, float]]:
    """Fetch nutrition data from nutrition service."""
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
                    return {}
                payload = await resp.json()
    except Exception:
        return {}

    items = payload
    if isinstance(payload, dict):
        if payload.get("success") and "data" in payload:
            items = payload["data"]
        elif "items" in payload:
            items = payload["items"]

    if not isinstance(items, list):
        return {}

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
            }

        d = daily[day_str]
        d["total_calories"] += float(meal.get("total_calories") or 0)
        d["total_protein_g"] += float(meal.get("total_protein_g") or 0)
        d["total_carbs_g"] += float(meal.get("total_carbs_g") or 0)

    return daily


def _extract_time_series(
    timeline: list, metric_path: str
) -> Tuple[List[str], List[float]]:
    """
    Extract time series data from timeline.
    metric_path examples: 'sleep.sleep_score', 'readiness.readiness_score', 'activity.steps'
    """
    dates = []
    values = []

    for entry in timeline:
        day = entry.date if hasattr(entry, "date") else entry.get("date", "")
        if not day:
            continue

        # Parse nested path
        parts = metric_path.split(".")
        obj = entry

        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict):
                obj = obj.get(part)
            else:
                obj = None
                break

        if obj is not None:
            value = float(obj)
            if value > 0:  # Skip zero values (missing data)
                dates.append(day)
                values.append(value)

    return dates, values


# ---------------------------------------------------------------------------
# Prediction Generation
# ---------------------------------------------------------------------------


async def _generate_predictions(
    user_id: str, timeline: list, nutrition_data: Dict[str, Dict[str, float]]
) -> List[Dict[str, Any]]:
    """Generate predictions for multiple health metrics."""
    predictions = []

    # Sleep score prediction
    dates, sleep_scores = _extract_time_series(timeline, "sleep.sleep_score")
    if len(sleep_scores) >= MIN_HISTORICAL_DAYS:
        for horizon in [1, 3, 7]:
            forecast, lower, upper = _forecast_linear(sleep_scores, horizon)

            # Confidence based on recent stability
            recent_std = math.sqrt(
                sum((v - sum(sleep_scores[-7:]) / 7) ** 2 for v in sleep_scores[-7:])
                / 7
            )
            confidence = max(0.5, 1.0 - (recent_std / 20))

            pred_date = (date.today() + timedelta(days=horizon)).isoformat()

            predictions.append(
                {
                    "user_id": user_id,
                    "prediction_type": "sleep_score",
                    "metric_name": "sleep",
                    "prediction_date": pred_date,
                    "prediction_horizon_days": horizon,
                    "predicted_value": round(forecast, 1),
                    "confidence_score": round(confidence, 2),
                    "prediction_range": {
                        "lower": round(lower, 1),
                        "upper": round(upper, 1),
                    },
                    "model_type": "statistical",
                    "model_version": "linear_v1",
                    "features_used": ["historical_sleep_scores", "trend"],
                    "contributing_factors": [
                        {
                            "factor": "Recent trend",
                            "value": "stable"
                            if abs(
                                _linear_regression(
                                    list(range(len(sleep_scores[-7:]))),
                                    sleep_scores[-7:],
                                )[0]
                            )
                            < 0.5
                            else "changing",
                        }
                    ],
                    "recommendations": [],
                    "status": "pending",
                }
            )

    # Readiness score prediction
    dates, readiness_scores = _extract_time_series(
        timeline, "readiness.readiness_score"
    )
    if len(readiness_scores) >= MIN_HISTORICAL_DAYS:
        for horizon in [1, 3, 7]:
            forecast, lower, upper = _forecast_linear(readiness_scores, horizon)

            recent_std = math.sqrt(
                sum(
                    (v - sum(readiness_scores[-7:]) / 7) ** 2
                    for v in readiness_scores[-7:]
                )
                / 7
            )
            confidence = max(0.5, 1.0 - (recent_std / 20))

            pred_date = (date.today() + timedelta(days=horizon)).isoformat()

            predictions.append(
                {
                    "user_id": user_id,
                    "prediction_type": "readiness_score",
                    "metric_name": "readiness",
                    "prediction_date": pred_date,
                    "prediction_horizon_days": horizon,
                    "predicted_value": round(forecast, 1),
                    "confidence_score": round(confidence, 2),
                    "prediction_range": {
                        "lower": round(lower, 1),
                        "upper": round(upper, 1),
                    },
                    "model_type": "statistical",
                    "model_version": "linear_v1",
                    "features_used": ["historical_readiness_scores", "hrv", "sleep"],
                    "contributing_factors": [],
                    "recommendations": [],
                    "status": "pending",
                }
            )

    # HRV forecast
    dates, hrv_values = _extract_time_series(timeline, "readiness.hrv_balance")
    if len(hrv_values) >= MIN_HISTORICAL_DAYS:
        forecast, lower, upper = _forecast_linear(hrv_values, 1)

        predictions.append(
            {
                "user_id": user_id,
                "prediction_type": "hrv_forecast",
                "metric_name": "hrv",
                "prediction_date": (date.today() + timedelta(days=1)).isoformat(),
                "prediction_horizon_days": 1,
                "predicted_value": round(forecast, 1),
                "confidence_score": 0.7,
                "prediction_range": {
                    "lower": round(lower, 1),
                    "upper": round(upper, 1),
                },
                "model_type": "statistical",
                "model_version": "linear_v1",
                "features_used": ["historical_hrv", "recovery_index"],
                "contributing_factors": [],
                "recommendations": [],
                "status": "pending",
            }
        )

    return predictions


async def _generate_risk_assessments(
    user_id: str, timeline: list
) -> List[Dict[str, Any]]:
    """Generate risk assessments."""
    risks = []

    # Extract time series
    _, sleep_scores = _extract_time_series(timeline, "sleep.sleep_score")
    _, readiness_scores = _extract_time_series(timeline, "readiness.readiness_score")
    _, hrv_values = _extract_time_series(timeline, "readiness.hrv_balance")
    _, activity_scores = _extract_time_series(timeline, "activity.activity_score")

    # Sleep decline risk
    sleep_risk = _assess_sleep_decline_risk(sleep_scores, [])
    if sleep_risk:
        risks.append(
            {
                "user_id": user_id,
                "risk_window_start": (date.today() - timedelta(days=7)).isoformat(),
                "risk_window_end": (date.today() + timedelta(days=7)).isoformat(),
                "confidence_score": 0.8,
                "historical_patterns": [],
                "user_acknowledged": False,
                "is_active": True,
                **sleep_risk,
            }
        )

    # Recovery decline risk
    recovery_risk = _assess_recovery_decline_risk(readiness_scores, hrv_values)
    if recovery_risk:
        risks.append(
            {
                "user_id": user_id,
                "risk_window_start": (date.today() - timedelta(days=7)).isoformat(),
                "risk_window_end": (date.today() + timedelta(days=7)).isoformat(),
                "confidence_score": 0.8,
                "historical_patterns": [],
                "user_acknowledged": False,
                "is_active": True,
                **recovery_risk,
            }
        )

    # Burnout risk
    burnout_risk = _assess_burnout_risk(sleep_scores, readiness_scores, activity_scores)
    if burnout_risk:
        risks.append(
            {
                "user_id": user_id,
                "risk_window_start": (date.today() - timedelta(days=14)).isoformat(),
                "risk_window_end": (date.today() + timedelta(days=14)).isoformat(),
                "confidence_score": 0.85,
                "historical_patterns": [],
                "user_acknowledged": False,
                "is_active": True,
                **burnout_risk,
            }
        )

    return risks


async def _generate_trends(user_id: str, timeline: list) -> List[Dict[str, Any]]:
    """Generate trend analyses for key metrics."""
    trends = []

    metrics = [
        ("sleep.sleep_score", "Sleep Score"),
        ("readiness.readiness_score", "Readiness Score"),
        ("readiness.hrv_balance", "HRV Balance"),
        ("readiness.resting_heart_rate", "Resting Heart Rate"),
        ("activity.steps", "Daily Steps"),
    ]

    for metric_path, metric_label in metrics:
        dates, values = _extract_time_series(timeline, metric_path)

        if len(values) < 7:
            continue

        # Calculate statistics
        x = [float(i) for i in range(len(values))]
        slope, intercept, r_squared = _linear_regression(x, values)

        avg = sum(values) / len(values)
        std_dev = math.sqrt(sum((v - avg) ** 2 for v in values) / len(values))

        # Recent vs overall change
        recent_avg = sum(values[-7:]) / min(7, len(values[-7:]))
        overall_avg = avg
        percent_change = (
            ((recent_avg - overall_avg) / overall_avg * 100) if overall_avg != 0 else 0
        )
        absolute_change = recent_avg - overall_avg

        # Trend type
        trend_type = _detect_trend_type(slope, r_squared)

        # Forecasts
        forecast_7d, _, _ = _forecast_linear(values, 7)
        forecast_14d, _, _ = _forecast_linear(values, 14)
        forecast_30d, _, _ = _forecast_linear(values, 30)

        # Anomalies
        anomaly_indices = _calculate_anomalies(values)
        anomalies = [
            {
                "date": dates[i],
                "value": values[i],
                "z_score": abs((values[i] - avg) / std_dev) if std_dev > 0 else 0,
            }
            for i in anomaly_indices
        ]

        # Significance
        if abs(percent_change) > 10 and r_squared > 0.5:
            significance = "clinically_significant"
        elif abs(percent_change) > 5 and r_squared > 0.3:
            significance = "notable"
        elif abs(percent_change) > 2:
            significance = "minor"
        else:
            significance = "noise"

        # Interpretation
        if trend_type == "improving":
            interpretation = (
                f"{metric_label} is improving by {abs(slope):.2f} points per day"
            )
        elif trend_type == "declining":
            interpretation = (
                f"{metric_label} is declining by {abs(slope):.2f} points per day"
            )
        elif trend_type == "stable":
            interpretation = f"{metric_label} is stable around {avg:.1f}"
        else:
            interpretation = f"{metric_label} shows high variability"

        trends.append(
            {
                "user_id": user_id,
                "metric_name": metric_path.split(".")[-1],
                "trend_type": trend_type,
                "analysis_start_date": dates[0],
                "analysis_end_date": dates[-1],
                "window_days": len(values),
                "slope": round(slope, 4),
                "r_squared": round(r_squared, 3),
                "average_value": round(avg, 2),
                "std_deviation": round(std_dev, 2),
                "percent_change": round(percent_change, 2),
                "absolute_change": round(absolute_change, 2),
                "detected_patterns": [],
                "anomalies": anomalies[:5],  # Top 5 anomalies
                "forecast_7d": round(forecast_7d, 1),
                "forecast_14d": round(forecast_14d, 1),
                "forecast_30d": round(forecast_30d, 1),
                "interpretation": interpretation,
                "significance": significance,
            }
        )

    return trends


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/predictions", response_model=PredictionsResponse)
async def get_predictions(
    request: Request,
    days: int = Query(default=30, ge=14, le=90),
    current_user: dict = Depends(UsageGate("predictions")),
):
    """
    Get health predictions for the authenticated user.
    Generates forecasts for sleep, readiness, HRV, and other metrics.
    Requires Pro+ subscription.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")

    # Fetch historical data
    try:
        timeline = await get_timeline(days=days, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for predictions: %s", exc)
        timeline = []

    nutrition_data = await _fetch_nutrition_daily(bearer, days)

    # Calculate data quality
    data_quality = min(1.0, len(timeline) / (days * 0.7))

    if len(timeline) < MIN_HISTORICAL_DAYS:
        return PredictionsResponse(
            predictions=[],
            generated_at=datetime.now(timezone.utc).isoformat(),
            days_of_data=len(timeline),
            data_quality_score=data_quality,
        )

    # Generate predictions
    predictions = await _generate_predictions(user_id, timeline, nutrition_data)

    # Save to database
    for pred in predictions:
        pred["id"] = str(uuid.uuid4())
        pred["created_at"] = datetime.now(timezone.utc).isoformat()
        try:
            await _supabase_insert("health_predictions", pred)
        except Exception as exc:
            logger.warning("Failed to save prediction: %s", exc)

    return PredictionsResponse(
        predictions=[HealthPrediction(**p) for p in predictions],
        generated_at=datetime.now(timezone.utc).isoformat(),
        days_of_data=len(timeline),
        data_quality_score=data_quality,
    )


@router.get("/risks", response_model=RisksResponse)
async def get_risk_assessments(
    request: Request,
    current_user: dict = Depends(UsageGate("predictions")),
):
    """
    Get active risk assessments for the authenticated user.
    Identifies potential health risks based on recent patterns.
    Requires Pro+ subscription.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # Fetch recent data (30 days for risk assessment)
    try:
        timeline = await get_timeline(days=30, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for risks: %s", exc)
        timeline = []

    if len(timeline) < MIN_HISTORICAL_DAYS:
        return RisksResponse(
            risks=[],
            overall_risk_level="unknown",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # Generate risk assessments
    risks = await _generate_risk_assessments(user_id, timeline)

    # Save to database
    for risk in risks:
        risk["id"] = str(uuid.uuid4())
        risk["created_at"] = datetime.now(timezone.utc).isoformat()
        try:
            await _supabase_insert("health_risk_assessments", risk)
        except Exception as exc:
            logger.warning("Failed to save risk assessment: %s", exc)

    # Determine overall risk level
    if not risks:
        overall_risk = "low"
    elif any(r["risk_level"] == "critical" for r in risks):
        overall_risk = "critical"
    elif any(r["risk_level"] == "high" for r in risks):
        overall_risk = "high"
    elif any(r["risk_level"] == "moderate" for r in risks):
        overall_risk = "moderate"
    else:
        overall_risk = "low"

    return RisksResponse(
        risks=[HealthRiskAssessment(**r) for r in risks],
        overall_risk_level=overall_risk,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    request: Request,
    days: int = Query(default=30, ge=14, le=90),
    current_user: dict = Depends(UsageGate("predictions")),
):
    """
    Get trend analyses for health metrics.
    Shows patterns, forecasts, and anomalies in health data.
    Requires Pro+ subscription.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # Fetch historical data
    try:
        timeline = await get_timeline(days=days, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for trends: %s", exc)
        timeline = []

    if len(timeline) < 7:
        return TrendsResponse(
            trends=[],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # Generate trends
    trends = await _generate_trends(user_id, timeline)

    # Save to database
    for trend in trends:
        trend["id"] = str(uuid.uuid4())
        trend["created_at"] = datetime.now(timezone.utc).isoformat()
        trend["expires_at"] = (
            datetime.now(timezone.utc) + timedelta(days=7)
        ).isoformat()
        try:
            await _supabase_insert("health_trends", trend)
        except Exception as exc:
            logger.warning("Failed to save trend: %s", exc)

    return TrendsResponse(
        trends=[HealthTrend(**t) for t in trends],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health-scores/{score_type}", response_model=PersonalizedHealthScore)
async def get_health_score(
    score_type: str,
    request: Request,
    current_user: dict = Depends(UsageGate("predictions")),
):
    """
    Get personalized health score.
    score_type: overall_health, recovery_capacity, resilience, metabolic_health
    Requires Pro+ subscription.
    """
    from .timeline import get_timeline

    user_id = current_user["id"]

    # Fetch recent data
    try:
        timeline = await get_timeline(days=30, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for health score: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch health data")

    if len(timeline) < 7:
        raise HTTPException(
            status_code=400, detail="Insufficient data for health score"
        )

    # Calculate overall health score
    _, sleep_scores = _extract_time_series(timeline, "sleep.sleep_score")
    _, readiness_scores = _extract_time_series(timeline, "readiness.readiness_score")
    _, activity_scores = _extract_time_series(timeline, "activity.activity_score")

    if score_type == "overall_health":
        recent_sleep = (
            sum(sleep_scores[-7:]) / min(7, len(sleep_scores[-7:]))
            if sleep_scores
            else 75
        )
        recent_readiness = (
            sum(readiness_scores[-7:]) / min(7, len(readiness_scores[-7:]))
            if readiness_scores
            else 75
        )
        recent_activity = (
            sum(activity_scores[-7:]) / min(7, len(activity_scores[-7:]))
            if activity_scores
            else 75
        )

        score_value = (
            recent_sleep * 0.4 + recent_readiness * 0.4 + recent_activity * 0.2
        )

        component_scores = {
            "sleep": round(recent_sleep, 1),
            "readiness": round(recent_readiness, 1),
            "activity": round(recent_activity, 1),
        }

        positive_factors = []
        negative_factors = []

        if recent_sleep > 80:
            positive_factors.append("Excellent sleep quality")
        elif recent_sleep < 70:
            negative_factors.append("Sleep needs improvement")

        if recent_readiness > 80:
            positive_factors.append("Good recovery")
        elif recent_readiness < 70:
            negative_factors.append("Recovery needs attention")

        # Compare to 7 days ago
        if len(sleep_scores) >= 14:
            prev_sleep = sum(sleep_scores[-14:-7]) / 7
            sleep_change = recent_sleep - prev_sleep
            trend_7d = (
                "up" if sleep_change > 2 else "down" if sleep_change < -2 else "stable"
            )
            change_7d = sleep_change
        else:
            trend_7d = "stable"
            change_7d = 0.0

        score_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "score_date": date.today().isoformat(),
            "score_type": score_type,
            "score_value": round(score_value, 1),
            "percentile": None,
            "component_scores": component_scores,
            "positive_factors": positive_factors,
            "negative_factors": negative_factors,
            "trend_7d": trend_7d,
            "change_7d": round(change_7d, 1),
            "improvement_recommendations": [
                {"priority": "high", "action": "Maintain consistent sleep schedule"},
                {"priority": "medium", "action": "Balance activity with recovery"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save to database
        try:
            await _supabase_upsert("personalized_health_scores", score_data)
        except Exception as exc:
            logger.warning("Failed to save health score: %s", exc)

        return PersonalizedHealthScore(**score_data)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown score type: {score_type}")
