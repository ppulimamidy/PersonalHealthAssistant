"""
Medication Intelligence API
AI-powered drug-nutrient interactions and medication-vitals correlations
"""

from datetime import datetime, timedelta
from typing import Optional, List
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


class InteractionSource(BaseModel):
    """Citation source for interaction"""

    title: str
    url: Optional[str] = None
    pubmed_id: Optional[str] = None


class MedicationInteraction(BaseModel):
    """Known medication-nutrient interaction"""

    id: str
    medication_name: str
    medication_generic_name: Optional[str] = None
    medication_class: Optional[str] = None
    interaction_type: str
    interacts_with: str
    interacts_with_category: Optional[str] = None
    severity: str
    evidence_level: str
    mechanism: Optional[str] = None
    clinical_significance: Optional[str] = None
    recommendation: str
    timing_recommendation: Optional[str] = None
    sources: List[InteractionSource] = []


class UserMedicationAlert(BaseModel):
    """User-specific interaction alert"""

    id: str
    user_id: str
    interaction_id: Optional[str] = None
    medication_id: Optional[str] = None
    supplement_id: Optional[str] = None
    nutrition_item: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    description: str
    recommendation: str
    is_acknowledged: bool
    is_dismissed: bool
    detected_at: str
    medication_name: Optional[str] = None
    interacts_with: Optional[str] = None


class MedicationVitalsCorrelation(BaseModel):
    """Correlation between medication timing and vitals"""

    id: str
    medication_id: str
    medication_name: str
    vital_metric: str
    vital_label: str
    correlation_coefficient: float
    p_value: float
    sample_size: int
    lag_hours: int
    optimal_timing_window: Optional[str] = None
    effect_type: str
    effect_magnitude: Optional[str] = None
    effect_description: str
    clinical_significance: Optional[str] = None
    recommendation: Optional[str] = None
    data_quality_score: float
    days_analyzed: int
    computed_at: str


class InteractionAlertsResponse(BaseModel):
    """Response with user interaction alerts"""

    alerts: List[UserMedicationAlert]
    total_critical: int
    total_high: int
    total_unacknowledged: int


class MedicationCorrelationsResponse(BaseModel):
    """Response with medication-vitals correlations"""

    correlations: List[MedicationVitalsCorrelation]
    total_significant: int
    data_quality_score: float


# ============================================================================
# Helper Functions
# ============================================================================


def _pearson_correlation(x: List[float], y: List[float]) -> tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value
    Pure Python implementation
    """
    import math

    n = len(x)
    if n < 3:
        return 0.0, 1.0

    # Calculate means
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate correlation
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    if sum_sq_x == 0 or sum_sq_y == 0:
        return 0.0, 1.0

    r = numerator / math.sqrt(sum_sq_x * sum_sq_y)

    # Calculate p-value using t-distribution approximation
    if abs(r) >= 0.9999:
        p_value = 0.0
    else:
        t = r * math.sqrt(n - 2) / math.sqrt(1 - r * r)
        # Simple p-value approximation
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))

    return r, p_value


async def _detect_user_interactions(
    user_id: str, supabase
) -> List[UserMedicationAlert]:
    """
    Detect potential drug-nutrient interactions for user's current medications/supplements
    """
    alerts = []

    # Get user's active medications
    meds_result = (
        supabase.table("medications")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )

    medications = meds_result.data if meds_result.data else []

    # Get user's active supplements
    supps_result = (
        supabase.table("supplements")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )

    supplements = supps_result.data if supps_result.data else []

    # Get all known interactions
    interactions_result = (
        supabase.table("medication_interactions").select("*").execute()
    )
    interactions = interactions_result.data if interactions_result.data else []

    # Check each medication against known interactions
    for med in medications:
        med_name = med.get("medication_name", "").lower()
        generic_name = (med.get("generic_name") or "").lower()

        for interaction in interactions:
            interaction_med = interaction.get("medication_name", "").lower()
            interaction_generic = (
                interaction.get("medication_generic_name") or ""
            ).lower()

            # Check if this interaction applies to user's medication
            if (
                interaction_med in med_name
                or (generic_name and interaction_generic in generic_name)
                or med_name in interaction_med
            ):
                # Check if user is taking the interacting substance
                interacts_with = interaction.get("interacts_with", "")

                # Check against supplements
                for supp in supplements:
                    supp_name = supp.get("supplement_name", "").lower()
                    if (
                        interacts_with.lower() in supp_name
                        or supp_name in interacts_with.lower()
                    ):
                        alert = UserMedicationAlert(
                            id="",  # Will be generated
                            user_id=user_id,
                            interaction_id=interaction.get("id"),
                            medication_id=med.get("id"),
                            supplement_id=supp.get("id"),
                            alert_type="drug_supplement",
                            severity=interaction.get("severity", "moderate"),
                            title=f"Interaction: {med.get('medication_name')} + {supp.get('supplement_name')}",
                            description=interaction.get(
                                "clinical_significance",
                                interaction.get("mechanism", ""),
                            ),
                            recommendation=interaction.get("recommendation", ""),
                            is_acknowledged=False,
                            is_dismissed=False,
                            detected_at=datetime.utcnow().isoformat(),
                            medication_name=med.get("medication_name"),
                            interacts_with=supp.get("supplement_name"),
                        )
                        alerts.append(alert)

    return alerts


async def _compute_medication_vitals_correlations(
    user_id: str, medication_id: str, days: int, supabase
) -> List[MedicationVitalsCorrelation]:
    """
    Compute correlations between medication adherence timing and Oura vitals
    """
    correlations = []

    # Get medication adherence logs for the period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    adherence_result = (
        supabase.table("medication_adherence_logs")
        .select("*")
        .eq("user_id", user_id)
        .eq("medication_id", medication_id)
        .eq("was_taken", True)
        .gte("scheduled_time", start_date.isoformat())
        .lte("scheduled_time", end_date.isoformat())
        .order("scheduled_time")
        .execute()
    )

    adherence_logs = adherence_result.data if adherence_result.data else []

    if len(adherence_logs) < 5:
        return []  # Not enough data

    # Get medication info
    med_result = (
        supabase.table("medications")
        .select("*")
        .eq("id", medication_id)
        .single()
        .execute()
    )
    medication = med_result.data if med_result.data else {}

    # Get Oura readiness data for the period
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

    if len(readiness_data) < 5:
        return []

    # Vital metrics to correlate
    vital_metrics = [
        ("hrv_balance", "HRV Balance"),
        ("resting_heart_rate", "Resting Heart Rate"),
        ("readiness_score", "Readiness Score"),
        ("recovery_index", "Recovery Index"),
        ("temperature_deviation", "Temperature Deviation"),
    ]

    # For each vital metric, correlate with medication timing
    for vital_key, vital_label in vital_metrics:
        # Build aligned data: medication dose times vs next-day vital
        med_dates = []
        vital_values = []

        for adherence in adherence_logs:
            dose_date = datetime.fromisoformat(
                adherence.get("scheduled_time", "").replace("Z", "+00:00")
            ).date()
            next_day = dose_date + timedelta(days=1)

            # Find next-day vital
            next_day_vital = next(
                (r for r in readiness_data if r.get("date") == next_day.isoformat()),
                None,
            )

            if next_day_vital and next_day_vital.get(vital_key) is not None:
                med_dates.append(dose_date.isoformat())
                vital_values.append(float(next_day_vital.get(vital_key, 0)))

        if len(vital_values) < 5:
            continue

        # Get baseline (days without medication) for comparison
        # For now, just compute trend in vital values
        pearson_r, p_value = _pearson_correlation(
            list(range(len(vital_values))), vital_values
        )

        # Determine effect type and magnitude
        effect_type = "neutral"
        effect_magnitude = "small"

        if abs(pearson_r) >= 0.3 and p_value < 0.1:
            if pearson_r > 0:
                effect_type = (
                    "positive" if vital_key != "resting_heart_rate" else "negative"
                )
            else:
                effect_type = (
                    "negative" if vital_key != "resting_heart_rate" else "positive"
                )

            if abs(pearson_r) >= 0.7:
                effect_magnitude = "large"
            elif abs(pearson_r) >= 0.5:
                effect_magnitude = "moderate"
            else:
                effect_magnitude = "small"

            # Generate effect description
            avg_change = (
                (vital_values[-1] - vital_values[0]) / vital_values[0] * 100
                if vital_values[0] != 0
                else 0
            )
            med_name = medication.get("medication_name", "this medication")
            direction = "increase" if avg_change > 0 else "decrease"
            effect_description = (
                f"Your {vital_label} shows a {abs(avg_change):.1f}% {direction} "
                f"over {days} days of taking {med_name}"
            )

            correlation = MedicationVitalsCorrelation(
                id="",
                medication_id=medication_id,
                medication_name=medication.get("medication_name", ""),
                vital_metric=vital_key,
                vital_label=vital_label,
                correlation_coefficient=pearson_r,
                p_value=p_value,
                sample_size=len(vital_values),
                lag_hours=24,  # Next-day effect
                effect_type=effect_type,
                effect_magnitude=effect_magnitude,
                effect_description=effect_description,
                data_quality_score=min(len(vital_values) / 30.0, 1.0),
                days_analyzed=days,
                computed_at=datetime.utcnow().isoformat(),
            )

            correlations.append(correlation)

    return correlations


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/medication-interactions/alerts", response_model=InteractionAlertsResponse)
async def get_medication_interaction_alerts(
    current_user: dict = Depends(get_current_user),
):
    """
    Get medication-nutrient interaction alerts for current user
    Analyzes active medications and supplements against known interactions
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user["sub"]

        # Check for existing alerts
        existing_result = (
            supabase.table("user_medication_alerts")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_dismissed", False)
            .execute()
        )

        existing_alerts = existing_result.data if existing_result.data else []

        # If no existing alerts, run detection
        if not existing_alerts:
            detected_alerts = await _detect_user_interactions(user_id, supabase)

            # Save detected alerts
            for alert in detected_alerts:
                alert_dict = alert.model_dump(exclude={"id"})
                supabase.table("user_medication_alerts").insert(alert_dict).execute()

            existing_alerts = detected_alerts
        else:
            # Convert to Pydantic models
            existing_alerts = [
                UserMedicationAlert(**alert) for alert in existing_alerts
            ]

        # Calculate summary stats
        total_critical = sum(1 for a in existing_alerts if a.severity == "critical")
        total_high = sum(1 for a in existing_alerts if a.severity == "high")
        total_unacknowledged = sum(1 for a in existing_alerts if not a.is_acknowledged)

        return InteractionAlertsResponse(
            alerts=existing_alerts,
            total_critical=total_critical,
            total_high=total_high,
            total_unacknowledged=total_unacknowledged,
        )

    except Exception as e:
        logger.error(f"Error getting medication interaction alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medication-interactions/alerts/{alert_id}/acknowledge")
async def acknowledge_interaction_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Acknowledge a medication interaction alert"""
    try:
        supabase = get_supabase_client()
        user_id = current_user["sub"]

        supabase.table("user_medication_alerts").update(
            {
                "is_acknowledged": True,
                "acknowledged_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", alert_id).eq("user_id", user_id).execute()

        return {"success": True}

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medication-interactions/alerts/{alert_id}/dismiss")
async def dismiss_interaction_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Dismiss a medication interaction alert"""
    try:
        supabase = get_supabase_client()
        user_id = current_user["sub"]

        supabase.table("user_medication_alerts").update(
            {
                "is_dismissed": True,
                "dismissed_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", alert_id).eq("user_id", user_id).execute()

        return {"success": True}

    except Exception as e:
        logger.error(f"Error dismissing alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/medications/{medication_id}/vitals-correlations",
    response_model=MedicationCorrelationsResponse,
    dependencies=[Depends(UsageGate("medication_vitals_correlations"))],
)
async def get_medication_vitals_correlations(
    medication_id: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Get correlations between medication timing and vital signs
    Pro+ feature
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user["sub"]

        # Check for cached correlations
        cached_result = (
            supabase.table("medication_vitals_correlations")
            .select("*")
            .eq("user_id", user_id)
            .eq("medication_id", medication_id)
            .eq("analysis_period_days", days)
            .gt("expires_at", datetime.utcnow().isoformat())
            .execute()
        )

        if cached_result.data:
            correlations = [
                MedicationVitalsCorrelation(**c) for c in cached_result.data
            ]
        else:
            # Compute fresh correlations
            correlations = await _compute_medication_vitals_correlations(
                user_id, medication_id, days, supabase
            )

            # Save to cache
            for corr in correlations:
                corr_dict = corr.model_dump(exclude={"id"})
                corr_dict["user_id"] = user_id
                corr_dict["analysis_period_days"] = days
                corr_dict["expires_at"] = (
                    datetime.utcnow() + timedelta(days=7)
                ).isoformat()

                supabase.table("medication_vitals_correlations").insert(
                    corr_dict
                ).execute()

        # Calculate stats
        total_significant = sum(
            1
            for c in correlations
            if c.p_value < 0.1 and abs(c.correlation_coefficient) >= 0.3
        )
        avg_quality = (
            sum(c.data_quality_score for c in correlations) / len(correlations)
            if correlations
            else 0
        )

        return MedicationCorrelationsResponse(
            correlations=correlations,
            total_significant=total_significant,
            data_quality_score=avg_quality,
        )

    except Exception as e:
        logger.error(f"Error getting medication-vitals correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/medication-interactions/search")
async def search_medication_interactions(
    query: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Search known medication-nutrient interactions
    Useful for looking up interactions before starting new medication
    """
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("medication_interactions")
            .select("*")
            .or_(
                f"medication_name.ilike.%{query}%,medication_generic_name.ilike.%{query}%,interacts_with.ilike.%{query}%"
            )
            .execute()
        )

        interactions = (
            [MedicationInteraction(**i) for i in result.data] if result.data else []
        )

        return {"interactions": interactions, "total": len(interactions)}

    except Exception as e:
        logger.error(f"Error searching interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
