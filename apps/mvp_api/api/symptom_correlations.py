"""
Symptom Correlations API
Correlate symptoms with nutrition, Oura vitals, and medications
"""

import math
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel  # pylint: disable=too-few-public-methods

from common.utils.logging import get_logger
from common.database.supabase_client import get_supabase_client
from ..dependencies.auth import get_current_user
from ..dependencies.usage_gate import UsageGate

logger = get_logger(__name__)
router = APIRouter()

# ============================================================================
# Request/Response Models
# ============================================================================


class SymptomCorrelation(BaseModel):
    """Correlation between symptom and another variable"""

    id: str
    symptom_type: str
    symptom_metric: str
    correlation_type: str
    correlated_variable: str
    correlated_variable_label: str
    correlation_coefficient: float
    p_value: float
    sample_size: int
    lag_days: int
    effect_type: str
    effect_magnitude: Optional[str] = None
    effect_description: str
    clinical_significance: Optional[str] = None
    recommendation: Optional[str] = None
    trigger_identified: bool
    trigger_confidence: Optional[float] = None
    data_quality_score: float
    days_analyzed: int
    computed_at: str


class TriggerVariable(BaseModel):
    """Variable that triggers a symptom"""

    variable: str
    label: str
    coefficient: float
    p_value: float


class SymptomTriggerPattern(BaseModel):
    """Detected trigger pattern for symptoms"""

    id: str
    symptom_type: str
    pattern_type: str
    trigger_variables: List[TriggerVariable]
    pattern_strength: float
    confidence_score: float
    pattern_description: str
    trigger_threshold: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    times_observed: int
    times_validated: int
    last_observed_at: Optional[str] = None
    is_active: bool
    user_acknowledged: bool
    created_at: str


class SymptomCorrelationsResponse(BaseModel):
    """Response with symptom correlations"""

    correlations: List[SymptomCorrelation]
    trigger_patterns: List[SymptomTriggerPattern]
    total_significant: int
    data_quality_score: float
    analysis_summary: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


def _pearson_correlation(
    x_vals: List[float], y_vals: List[float]
) -> tuple[float, float]:
    """Calculate Pearson correlation coefficient and p-value"""
    num_points = len(x_vals)
    if num_points < 3:
        return 0.0, 1.0

    mean_x = sum(x_vals) / num_points
    mean_y = sum(y_vals) / num_points

    numerator = sum(
        (x_vals[i] - mean_x) * (y_vals[i] - mean_y) for i in range(num_points)
    )
    sum_sq_x = sum((x_vals[i] - mean_x) ** 2 for i in range(num_points))
    sum_sq_y = sum((y_vals[i] - mean_y) ** 2 for i in range(num_points))

    if sum_sq_x == 0 or sum_sq_y == 0:
        return 0.0, 1.0

    pearson_r = numerator / math.sqrt(sum_sq_x * sum_sq_y)

    # Calculate p-value using t-distribution approximation
    if abs(pearson_r) >= 0.9999:
        p_value = 0.0
    else:
        t_stat = (
            pearson_r * math.sqrt(num_points - 2) / math.sqrt(1 - pearson_r * pearson_r)
        )
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

    return pearson_r, p_value


async def _compute_symptom_nutrition_correlations(
    user_id: str, symptom_type: str, days: int, supabase
) -> List[SymptomCorrelation]:
    """Compute correlations between symptom severity and nutrition variables"""
    correlations = []

    # Get symptom journal entries
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    symptoms_result = (
        supabase.table("symptom_journal")
        .select("*")
        .eq("user_id", user_id)
        .eq("symptom_type", symptom_type)
        .gte("symptom_date", start_date.date().isoformat())
        .lte("symptom_date", end_date.date().isoformat())
        .order("symptom_date")
        .execute()
    )

    symptoms = symptoms_result.data if symptoms_result.data else []

    if len(symptoms) < 5:
        return []

    # Get nutrition data for same period
    nutrition_result = (
        supabase.table("meal_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("timestamp", start_date.isoformat())
        .lte("timestamp", end_date.isoformat())
        .order("timestamp")
        .execute()
    )

    meals = nutrition_result.data if nutrition_result.data else []

    # Aggregate nutrition by date
    nutrition_by_date: Dict[str, Dict[str, float]] = {}
    for meal in meals:
        meal_date = meal.get("timestamp", "")[:10]
        if meal_date not in nutrition_by_date:
            nutrition_by_date[meal_date] = {
                "total_calories": 0,
                "total_protein_g": 0,
                "total_carbs_g": 0,
                "total_fat_g": 0,
                "total_sugar_g": 0,
                "total_fiber_g": 0,
                "total_sodium_mg": 0,
            }

        nutrition_by_date[meal_date]["total_calories"] += meal.get("total_calories", 0)
        nutrition_by_date[meal_date]["total_protein_g"] += meal.get(
            "total_protein_g", 0
        )
        nutrition_by_date[meal_date]["total_carbs_g"] += meal.get("total_carbs_g", 0)
        nutrition_by_date[meal_date]["total_fat_g"] += meal.get("total_fat_g", 0)
        nutrition_by_date[meal_date]["total_sugar_g"] += meal.get("total_sugar_g", 0)
        nutrition_by_date[meal_date]["total_fiber_g"] += meal.get("total_fiber_g", 0)
        nutrition_by_date[meal_date]["total_sodium_mg"] += meal.get(
            "total_sodium_mg", 0
        )

    # Nutrition variables to correlate
    nutrition_vars = [
        ("total_calories", "Daily Calories"),
        ("total_sugar_g", "Sugar Intake"),
        ("total_carbs_g", "Carbohydrate Intake"),
        ("total_fat_g", "Fat Intake"),
        ("total_protein_g", "Protein Intake"),
        ("total_fiber_g", "Fiber Intake"),
        ("total_sodium_mg", "Sodium Intake"),
    ]

    # For each nutrition variable, correlate with symptom severity
    for nutr_var, nutr_label in nutrition_vars:
        # Build aligned data
        severity_values = []
        nutrition_values = []

        for symptom in symptoms:
            symptom_date = symptom.get("symptom_date")
            severity = symptom.get("severity", 0)

            # Same-day nutrition
            if symptom_date in nutrition_by_date:
                severity_values.append(float(severity))
                nutrition_values.append(
                    float(nutrition_by_date[symptom_date].get(nutr_var, 0))
                )

        if len(severity_values) < 5:
            continue

        pearson_r, p_value = _pearson_correlation(nutrition_values, severity_values)

        # Filter for significance
        if abs(pearson_r) >= 0.3 and p_value < 0.1:
            effect_type = "positive" if pearson_r > 0 else "negative"

            if abs(pearson_r) >= 0.7:
                effect_magnitude = "large"
            elif abs(pearson_r) >= 0.5:
                effect_magnitude = "moderate"
            else:
                effect_magnitude = "small"

            # Generate description
            direction = "increases" if pearson_r > 0 else "decreases"
            effect_description = (
                f"Higher {nutr_label.lower()} {direction} {symptom_type} severity "
                f"(r={pearson_r:.2f}, p={p_value:.3f})"
            )

            # Identify as trigger if strong negative or positive correlation
            trigger_identified = abs(pearson_r) >= 0.5 and pearson_r > 0
            trigger_confidence = abs(pearson_r) if trigger_identified else None

            correlation = SymptomCorrelation(
                id="",
                symptom_type=symptom_type,
                symptom_metric="severity",
                correlation_type="symptom_nutrition",
                correlated_variable=nutr_var,
                correlated_variable_label=nutr_label,
                correlation_coefficient=pearson_r,
                p_value=p_value,
                sample_size=len(severity_values),
                lag_days=0,
                effect_type=effect_type,
                effect_magnitude=effect_magnitude,
                effect_description=effect_description,
                trigger_identified=trigger_identified,
                trigger_confidence=trigger_confidence,
                data_quality_score=min(len(severity_values) / 30.0, 1.0),
                days_analyzed=days,
                computed_at=datetime.utcnow().isoformat(),
            )

            correlations.append(correlation)

    return correlations


async def _compute_symptom_oura_correlations(
    user_id: str, symptom_type: str, days: int, supabase
) -> List[SymptomCorrelation]:
    """Compute correlations between symptoms and Oura vitals"""
    correlations = []

    # Get symptom journal entries
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    symptoms_result = (
        supabase.table("symptom_journal")
        .select("*")
        .eq("user_id", user_id)
        .eq("symptom_type", symptom_type)
        .gte("symptom_date", start_date.date().isoformat())
        .lte("symptom_date", end_date.date().isoformat())
        .order("symptom_date")
        .execute()
    )

    symptoms = symptoms_result.data if symptoms_result.data else []

    if len(symptoms) < 5:
        return []

    # Get Oura readiness data
    readiness_result = (
        supabase.table("oura_readiness")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", start_date.date().isoformat())
        .lte("date", end_date.date().isoformat())
        .order("date")
        .execute()
    )

    readiness_data = readiness_result.data if readiness_result.data else []

    # Oura variables to correlate
    oura_vars = [
        ("hrv_balance", "HRV Balance"),
        ("resting_heart_rate", "Resting Heart Rate"),
        ("readiness_score", "Readiness Score"),
        ("recovery_index", "Recovery Index"),
        ("temperature_deviation", "Temperature Deviation"),
    ]

    # For each Oura variable, correlate with symptom severity
    for oura_var, oura_label in oura_vars:
        # Build aligned data (lag-1: previous day's Oura predicts today's symptom)
        severity_values = []
        oura_values = []

        for symptom in symptoms:
            symptom_date = symptom.get("symptom_date")
            severity = symptom.get("severity", 0)

            # Previous day's Oura data
            prev_date = (
                (datetime.strptime(symptom_date, "%Y-%m-%d") - timedelta(days=1))
                .date()
                .isoformat()
            )

            prev_oura = next(
                (r for r in readiness_data if r.get("date") == prev_date), None
            )

            if prev_oura and prev_oura.get(oura_var) is not None:
                severity_values.append(float(severity))
                oura_values.append(float(prev_oura.get(oura_var, 0)))

        if len(severity_values) < 5:
            continue

        pearson_r, p_value = _pearson_correlation(oura_values, severity_values)

        # Filter for significance
        if abs(pearson_r) >= 0.3 and p_value < 0.1:
            # Determine effect type (lower HRV/readiness → worse symptoms is negative)
            if oura_var in ["hrv_balance", "readiness_score", "recovery_index"]:
                effect_type = "negative" if pearson_r < 0 else "positive"
            else:
                effect_type = "positive" if pearson_r > 0 else "negative"

            if abs(pearson_r) >= 0.7:
                effect_magnitude = "large"
            elif abs(pearson_r) >= 0.5:
                effect_magnitude = "moderate"
            else:
                effect_magnitude = "small"

            # Generate description
            direction = "lower" if pearson_r < 0 else "higher"
            effect_description = (
                f"{direction.capitalize()} {oura_label.lower()} on previous day "
                f"predicts {'worse' if pearson_r < 0 else 'better'} {symptom_type} "
                f"(r={pearson_r:.2f}, p={p_value:.3f})"
            )

            correlation = SymptomCorrelation(
                id="",
                symptom_type=symptom_type,
                symptom_metric="severity",
                correlation_type="symptom_oura",
                correlated_variable=oura_var,
                correlated_variable_label=oura_label,
                correlation_coefficient=pearson_r,
                p_value=p_value,
                sample_size=len(severity_values),
                lag_days=1,
                effect_type=effect_type,
                effect_magnitude=effect_magnitude,
                effect_description=effect_description,
                trigger_identified=False,
                data_quality_score=min(len(severity_values) / 30.0, 1.0),
                days_analyzed=days,
                computed_at=datetime.utcnow().isoformat(),
            )

            correlations.append(correlation)

    return correlations


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/symptoms/{symptom_type}/correlations",
    response_model=SymptomCorrelationsResponse,
    dependencies=[Depends(UsageGate("symptom_journal"))],
)
async def get_symptom_correlations(
    symptom_type: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Get correlations for a specific symptom type
    Analyzes nutrition and Oura vitals correlations
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user["sub"]

        # Check for cached correlations
        cached_result = (
            supabase.table("symptom_correlations")
            .select("*")
            .eq("user_id", user_id)
            .eq("symptom_type", symptom_type)
            .gt("expires_at", datetime.utcnow().isoformat())
            .execute()
        )

        if cached_result.data and len(cached_result.data) > 0:
            correlations = [SymptomCorrelation(**c) for c in cached_result.data]
        else:
            # Compute fresh correlations
            nutrition_corrs = await _compute_symptom_nutrition_correlations(
                user_id, symptom_type, days, supabase
            )
            oura_corrs = await _compute_symptom_oura_correlations(
                user_id, symptom_type, days, supabase
            )

            correlations = nutrition_corrs + oura_corrs

            # Save to cache
            for corr in correlations:
                corr_dict = corr.model_dump(exclude={"id"})
                corr_dict["user_id"] = user_id
                corr_dict["analysis_period_days"] = days
                corr_dict["expires_at"] = (
                    datetime.utcnow() + timedelta(days=7)
                ).isoformat()

                supabase.table("symptom_correlations").insert(corr_dict).execute()

        # Get trigger patterns
        patterns_result = (
            supabase.table("symptom_trigger_patterns")
            .select("*")
            .eq("user_id", user_id)
            .eq("symptom_type", symptom_type)
            .eq("is_active", True)
            .execute()
        )

        trigger_patterns = []
        if patterns_result.data:
            for pattern in patterns_result.data:
                trigger_vars = [
                    TriggerVariable(**tv) for tv in pattern.get("trigger_variables", [])
                ]
                trigger_patterns.append(
                    SymptomTriggerPattern(
                        id=pattern["id"],
                        symptom_type=pattern["symptom_type"],
                        pattern_type=pattern["pattern_type"],
                        trigger_variables=trigger_vars,
                        pattern_strength=pattern["pattern_strength"],
                        confidence_score=pattern["confidence_score"],
                        pattern_description=pattern["pattern_description"],
                        trigger_threshold=pattern.get("trigger_threshold"),
                        recommendations=pattern.get("recommendations", []),
                        times_observed=pattern.get("times_observed", 0),
                        times_validated=pattern.get("times_validated", 0),
                        last_observed_at=pattern.get("last_observed_at"),
                        is_active=pattern.get("is_active", True),
                        user_acknowledged=pattern.get("user_acknowledged", False),
                        created_at=pattern["created_at"],
                    )
                )

        # Calculate stats
        total_significant = sum(
            1
            for c in correlations
            if c.p_value < 0.05 and abs(c.correlation_coefficient) >= 0.3
        )
        avg_quality = (
            sum(c.data_quality_score for c in correlations) / len(correlations)
            if correlations
            else 0
        )

        return SymptomCorrelationsResponse(
            correlations=correlations,
            trigger_patterns=trigger_patterns,
            total_significant=total_significant,
            data_quality_score=avg_quality,
        )

    except Exception as err:
        logger.error(f"Error getting symptom correlations: {err}")
        raise HTTPException(status_code=500, detail=str(err)) from err


@router.post("/symptoms/{symptom_type}/triggers/{pattern_id}/validate")
async def validate_trigger_pattern(
    symptom_type: str,
    pattern_id: str,
    validated: bool,
    current_user: dict = Depends(get_current_user),
):
    """Validate or invalidate a detected trigger pattern"""
    try:
        supabase = get_supabase_client()
        user_id = current_user["sub"]

        # Call the validation function
        supabase.rpc(
            "update_trigger_validation",
            {
                "p_pattern_id": pattern_id,
                "p_user_id": user_id,
                "p_validated": validated,
            },
        ).execute()

        return {"success": True, "validated": validated}

    except Exception as err:
        logger.error(f"Error validating trigger pattern: {err}")
        raise HTTPException(status_code=500, detail=str(err)) from err
