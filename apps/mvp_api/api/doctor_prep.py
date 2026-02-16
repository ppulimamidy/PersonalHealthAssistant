"""
Doctor Visit Prep API
Endpoints for generating health summary reports for doctor visits.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
import uuid
import io
import os

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import UsageGate, _supabase_get

logger = get_logger(__name__)

router = APIRouter()

# Sandbox mode
USE_SANDBOX = os.getenv("USE_SANDBOX", "true").lower() in ("true", "1", "yes")


# Helper function for optional auth in sandbox mode
async def get_user_optional(request: Request) -> dict:
    """Get current user, or return a sandbox user if not authenticated and in sandbox mode"""
    if USE_SANDBOX:
        try:
            return await get_current_user(request)
        except HTTPException:
            # In sandbox mode, if auth fails, return a mock user
            return {
                "id": "sandbox-user-123",
                "email": "sandbox@example.com",
                "user_type": "sandbox",
            }
    else:
        # In production, require authentication
        return await get_current_user(request)


class KeyMetric(BaseModel):
    name: str
    value: float
    unit: str
    status: str  # "excellent", "good", "moderate", "poor"
    comparison_to_average: float


class TrendSummary(BaseModel):
    metric: str
    direction: str  # "improving", "declining", "stable"
    percentage_change: float
    period: str


class SleepSummary(BaseModel):
    average_duration: float
    average_score: float
    average_efficiency: float
    best_night: Optional[str] = None
    worst_night: Optional[str] = None


class ActivitySummary(BaseModel):
    average_steps: float
    average_active_calories: float
    average_score: float
    most_active_day: Optional[str] = None
    least_active_day: Optional[str] = None


class ReadinessSummary(BaseModel):
    average_score: float
    average_hrv: float
    average_resting_hr: float
    highest_readiness_day: Optional[str] = None
    lowest_readiness_day: Optional[str] = None


class ReportSummary(BaseModel):
    overall_health_score: float
    key_metrics: List[KeyMetric]
    trends: List[TrendSummary]
    concerns: List[str]
    improvements: List[str]


class DetailedData(BaseModel):
    sleep: SleepSummary
    activity: ActivitySummary
    readiness: ReadinessSummary


class HealthIntelligenceIndicators(BaseModel):
    sleep_score_trend: str  # improving, declining, stable
    hrv_trend: str
    nutrition_quality_score: float  # 0-100
    inflammation_risk: str  # low, moderate, elevated, high
    stress_index: float  # 0-100
    personalized_actions: List[str]


class CorrelationHighlight(BaseModel):
    metric_a_label: str
    metric_b_label: str
    correlation_coefficient: float
    effect_description: str
    strength: str


class DoctorPrepReport(BaseModel):
    id: str
    user_id: str
    generated_at: datetime
    date_range: dict
    summary: ReportSummary
    detailed_data: DetailedData
    health_intelligence: Optional[HealthIntelligenceIndicators] = None
    nutrition_correlations: Optional[List[CorrelationHighlight]] = None
    condition_specific_notes: Optional[List[str]] = None


class GenerateReportRequest(BaseModel):
    days: int = 30


# ---------------------------------------------------------------------------
# Intelligence indicator helpers
# ---------------------------------------------------------------------------


def _safe_avg(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _compute_trend(recent: List[float], older: List[float]) -> str:
    if not recent or not older:
        return "stable"
    r_avg = _safe_avg(recent)
    o_avg = _safe_avg(older)
    if o_avg == 0:
        return "stable"
    pct = ((r_avg - o_avg) / o_avg) * 100
    if pct > 5:
        return "improving"
    if pct < -5:
        return "declining"
    return "stable"


def _compute_nutrition_quality(nutrition_daily: Dict[str, Dict[str, float]]) -> float:
    """
    Score 0-100 based on macro balance and variety.
    Ideal: 25-35% protein, 40-55% carbs, 20-35% fat, sufficient fiber.
    """
    if not nutrition_daily:
        return 0.0

    scores: List[float] = []
    for _day, d in nutrition_daily.items():
        cals = d.get("total_calories", 0) or 1
        protein_pct = (d.get("total_protein_g", 0) * 4 / cals) * 100
        carb_pct = (d.get("total_carbs_g", 0) * 4 / cals) * 100
        fat_pct = (d.get("total_fat_g", 0) * 9 / cals) * 100
        fiber = d.get("total_fiber_g", 0)

        day_score = 0.0
        # Protein: ideal 25-35%
        if 25 <= protein_pct <= 35:
            day_score += 30
        elif 15 <= protein_pct <= 45:
            day_score += 20
        else:
            day_score += 5

        # Carbs: ideal 40-55%
        if 40 <= carb_pct <= 55:
            day_score += 25
        elif 30 <= carb_pct <= 65:
            day_score += 15
        else:
            day_score += 5

        # Fat: ideal 20-35%
        if 20 <= fat_pct <= 35:
            day_score += 25
        elif 15 <= fat_pct <= 45:
            day_score += 15
        else:
            day_score += 5

        # Fiber: ideal >= 25g
        if fiber >= 25:
            day_score += 20
        elif fiber >= 15:
            day_score += 12
        elif fiber >= 5:
            day_score += 5

        scores.append(min(100, day_score))

    return round(_safe_avg(scores), 1)


def _compute_inflammation_risk(
    temp_vals: List[float],
    hrv_vals: List[float],
    sugar_vals: List[float],
    rhr_vals: List[float],
) -> str:
    """
    Inflammation risk: low / moderate / elevated / high.
    Based on temp deviation, HRV, sugar intake, resting HR.
    """
    score = 0

    if temp_vals:
        avg_temp = _safe_avg(temp_vals)
        if avg_temp > 0.5:
            score += 3
        elif avg_temp > 0.3:
            score += 2
        elif avg_temp > 0.1:
            score += 1

    if hrv_vals:
        avg_hrv = _safe_avg(hrv_vals)
        if avg_hrv < 40:
            score += 3
        elif avg_hrv < 55:
            score += 2
        elif avg_hrv < 65:
            score += 1

    if sugar_vals:
        avg_sugar = _safe_avg(sugar_vals)
        if avg_sugar > 80:
            score += 2
        elif avg_sugar > 50:
            score += 1

    if rhr_vals:
        avg_rhr = _safe_avg(rhr_vals)
        if avg_rhr > 75:
            score += 2
        elif avg_rhr > 65:
            score += 1

    if score >= 7:
        return "high"
    if score >= 5:
        return "elevated"
    if score >= 3:
        return "moderate"
    return "low"


def _compute_stress_index(
    hrv_vals: List[float],
    sleep_eff_vals: List[float],
    rhr_vals: List[float],
) -> float:
    """
    Stress index 0-100 (higher = more stress).
    Weighted: inverse HRV 40% + inverse sleep efficiency 30% + elevated RHR 30%.
    """
    hrv_component = 0.0
    if hrv_vals:
        avg_hrv = _safe_avg(hrv_vals)
        # HRV typically 0-100; invert so low HRV = high stress
        hrv_component = max(0, 100 - avg_hrv)

    sleep_component = 0.0
    if sleep_eff_vals:
        avg_eff = _safe_avg(sleep_eff_vals)
        sleep_component = max(0, 100 - avg_eff)

    rhr_component = 0.0
    if rhr_vals:
        avg_rhr = _safe_avg(rhr_vals)
        # RHR 50-100 range; normalize
        rhr_component = max(0, min(100, (avg_rhr - 50) * 2))

    index = (hrv_component * 0.4) + (sleep_component * 0.3) + (rhr_component * 0.3)
    return round(max(0, min(100, index)), 1)


async def _build_intelligence_indicators(
    timeline: list,
    user_id: str,
    bearer: Optional[str],
    days: int,
) -> Optional[HealthIntelligenceIndicators]:
    """Build health intelligence indicators from timeline + nutrition data."""
    try:
        from .correlations import _extract_oura_daily, _fetch_nutrition_daily

        oura_daily = _extract_oura_daily(timeline)
        nutrition_daily = await _fetch_nutrition_daily(bearer, days)

        if not oura_daily:
            return None

        dates = sorted(oura_daily.keys())
        half = len(dates) // 2
        recent_dates = dates[half:]
        older_dates = dates[:half]

        # Trends
        sleep_recent = [
            oura_daily[d].get("sleep_score", 0)
            for d in recent_dates
            if oura_daily[d].get("sleep_score")
        ]
        sleep_older = [
            oura_daily[d].get("sleep_score", 0)
            for d in older_dates
            if oura_daily[d].get("sleep_score")
        ]
        sleep_trend = _compute_trend(sleep_recent, sleep_older)

        hrv_recent = [
            oura_daily[d].get("hrv_balance", 0)
            for d in recent_dates
            if oura_daily[d].get("hrv_balance")
        ]
        hrv_older = [
            oura_daily[d].get("hrv_balance", 0)
            for d in older_dates
            if oura_daily[d].get("hrv_balance")
        ]
        hrv_trend = _compute_trend(hrv_recent, hrv_older)

        # Nutrition quality
        nutrition_quality = _compute_nutrition_quality(nutrition_daily)

        # Inflammation risk
        temp_vals = [
            oura_daily[d].get("temperature_deviation", 0)
            for d in dates
            if "temperature_deviation" in oura_daily[d]
        ]
        hrv_vals = [
            oura_daily[d].get("hrv_balance", 0)
            for d in dates
            if oura_daily[d].get("hrv_balance")
        ]
        sugar_vals = [
            nutrition_daily[d].get("total_sugar_g", 0)
            for d in dates
            if d in nutrition_daily and nutrition_daily[d].get("total_sugar_g")
        ]
        rhr_vals = [
            oura_daily[d].get("resting_heart_rate", 0)
            for d in dates
            if oura_daily[d].get("resting_heart_rate")
        ]
        inflammation = _compute_inflammation_risk(
            temp_vals, hrv_vals, sugar_vals, rhr_vals
        )

        # Stress index
        sleep_eff_vals = [
            oura_daily[d].get("sleep_efficiency", 0)
            for d in dates
            if oura_daily[d].get("sleep_efficiency")
        ]
        stress = _compute_stress_index(hrv_vals, sleep_eff_vals, rhr_vals)

        # Personalized actions from recommendations
        actions: List[str] = []
        try:
            from .recommendations import _detect_patterns

            patterns = _detect_patterns(oura_daily, nutrition_daily)
            for p in patterns[:3]:
                actions.append(
                    f"Address {p.label.lower()}: {p.signals[0] if p.signals else ''}"
                )
        except Exception:
            pass

        if inflammation in ("elevated", "high"):
            actions.append(
                "Consider anti-inflammatory foods: salmon, blueberries, leafy greens"
            )
        if stress > 60:
            actions.append(
                "Focus on stress reduction: earlier meals, meditation, light exercise"
            )
        if nutrition_quality < 50:
            actions.append(
                "Improve macro balance: aim for 25-35% protein, 40-55% carbs, 20-35% fat"
            )

        return HealthIntelligenceIndicators(
            sleep_score_trend=sleep_trend,
            hrv_trend=hrv_trend,
            nutrition_quality_score=nutrition_quality,
            inflammation_risk=inflammation,
            stress_index=stress,
            personalized_actions=actions[:5],
        )
    except Exception as exc:
        logger.warning("Failed to build intelligence indicators: %s", exc)
        return None


async def _get_top_correlations(user_id: str) -> Optional[List[CorrelationHighlight]]:
    """Fetch top 3 cached correlations for the report."""
    try:
        from datetime import timezone

        now = datetime.now(timezone.utc).isoformat()
        rows = await _supabase_get(
            "correlation_results",
            f"user_id=eq.{user_id}&expires_at=gt.{now}&select=correlations&limit=1&order=period_days.desc",
        )
        if not rows or not isinstance(rows, list):
            return None

        corr_data = rows[0].get("correlations", "[]")
        if isinstance(corr_data, str):
            corr_data = json.loads(corr_data)

        highlights = []
        for c in corr_data[:3]:
            highlights.append(
                CorrelationHighlight(
                    metric_a_label=c.get("metric_a_label", ""),
                    metric_b_label=c.get("metric_b_label", ""),
                    correlation_coefficient=c.get("correlation_coefficient", 0),
                    effect_description=c.get("effect_description", ""),
                    strength=c.get("strength", "weak"),
                )
            )
        return highlights if highlights else None
    except Exception:
        return None


async def _get_condition_notes(user_id: str) -> Optional[List[str]]:
    """Generate condition-specific notes for the doctor report."""
    try:
        from .health_conditions import CONDITION_VARIABLE_MAP

        rows = await _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name,condition_category,severity",
        )
        if not rows or not isinstance(rows, list):
            return None

        notes: List[str] = []
        for row in rows:
            name = row.get("condition_name", "")
            severity = row.get("severity", "")
            key = name.lower().replace(" ", "_").replace("-", "_")
            info = CONDITION_VARIABLE_MAP.get(key)
            if info:
                watch = info.get("watch_metrics", [])
                note = f"{name} ({severity})"
                if watch:
                    note += f" — {watch[0]}"
                notes.append(note)
            else:
                notes.append(f"{name} ({severity})")
        return notes if notes else None
    except Exception:
        return None


@router.post("/generate", response_model=DoctorPrepReport)
async def generate_report(
    request: GenerateReportRequest,
    http_request: Request = None,
    current_user: dict = Depends(UsageGate("doctor_prep")),
):
    """
    Generate a comprehensive health summary report for doctor visits.
    Now includes health intelligence indicators, correlations, and condition notes.
    """
    from .timeline import get_timeline

    days = request.days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Fetch timeline data
    try:
        timeline = await get_timeline(days=days, current_user=current_user)
    except Exception as e:
        logger.error(f"Failed to fetch timeline for report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

    if not timeline:
        raise HTTPException(
            status_code=400, detail="Insufficient data to generate report"
        )

    # Calculate sleep metrics
    sleep_entries = [e for e in timeline if e.sleep]
    if sleep_entries:
        sleep_scores = [e.sleep.sleep_score for e in sleep_entries]
        sleep_durations = [
            e.sleep.total_sleep_duration / 3600 for e in sleep_entries
        ]  # hours
        sleep_efficiencies = [e.sleep.sleep_efficiency for e in sleep_entries]

        sleep_summary = SleepSummary(
            average_duration=sum(sleep_durations) / len(sleep_durations),
            average_score=sum(sleep_scores) / len(sleep_scores),
            average_efficiency=sum(sleep_efficiencies) / len(sleep_efficiencies),
            best_night=max(sleep_entries, key=lambda x: x.sleep.sleep_score).date,
            worst_night=min(sleep_entries, key=lambda x: x.sleep.sleep_score).date,
        )
    else:
        sleep_summary = SleepSummary(
            average_duration=0, average_score=0, average_efficiency=0
        )

    # Calculate activity metrics
    activity_entries = [e for e in timeline if e.activity]
    if activity_entries:
        steps = [e.activity.steps for e in activity_entries]
        calories = [e.activity.active_calories for e in activity_entries]
        activity_scores = [e.activity.activity_score for e in activity_entries]

        activity_summary = ActivitySummary(
            average_steps=sum(steps) / len(steps),
            average_active_calories=sum(calories) / len(calories),
            average_score=sum(activity_scores) / len(activity_scores),
            most_active_day=max(activity_entries, key=lambda x: x.activity.steps).date,
            least_active_day=min(activity_entries, key=lambda x: x.activity.steps).date,
        )
    else:
        activity_summary = ActivitySummary(
            average_steps=0, average_active_calories=0, average_score=0
        )

    # Calculate readiness metrics
    readiness_entries = [e for e in timeline if e.readiness]
    if readiness_entries:
        readiness_scores = [e.readiness.readiness_score for e in readiness_entries]
        hrvs = [e.readiness.hrv_balance for e in readiness_entries]
        resting_hrs = [e.readiness.resting_heart_rate for e in readiness_entries]

        readiness_summary = ReadinessSummary(
            average_score=sum(readiness_scores) / len(readiness_scores),
            average_hrv=sum(hrvs) / len(hrvs),
            average_resting_hr=sum(resting_hrs) / len(resting_hrs),
            highest_readiness_day=max(
                readiness_entries, key=lambda x: x.readiness.readiness_score
            ).date,
            lowest_readiness_day=min(
                readiness_entries, key=lambda x: x.readiness.readiness_score
            ).date,
        )
    else:
        readiness_summary = ReadinessSummary(
            average_score=0, average_hrv=0, average_resting_hr=0
        )

    # Calculate overall health score
    scores = []
    if sleep_entries:
        scores.append(sleep_summary.average_score)
    if activity_entries:
        scores.append(activity_summary.average_score)
    if readiness_entries:
        scores.append(readiness_summary.average_score)

    overall_score = sum(scores) / len(scores) if scores else 0

    # Build key metrics
    key_metrics = []

    def get_status(score):
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "moderate"
        return "poor"

    if sleep_entries:
        key_metrics.append(
            KeyMetric(
                name="Sleep Score",
                value=round(sleep_summary.average_score, 1),
                unit="",
                status=get_status(sleep_summary.average_score),
                comparison_to_average=0,
            )
        )
        key_metrics.append(
            KeyMetric(
                name="Sleep Duration",
                value=round(sleep_summary.average_duration, 1),
                unit="hours",
                status="good" if sleep_summary.average_duration >= 7 else "moderate",
                comparison_to_average=0,
            )
        )

    if activity_entries:
        key_metrics.append(
            KeyMetric(
                name="Daily Steps",
                value=round(activity_summary.average_steps),
                unit="steps",
                status="good" if activity_summary.average_steps >= 7500 else "moderate",
                comparison_to_average=0,
            )
        )
        key_metrics.append(
            KeyMetric(
                name="Activity Score",
                value=round(activity_summary.average_score, 1),
                unit="",
                status=get_status(activity_summary.average_score),
                comparison_to_average=0,
            )
        )

    if readiness_entries:
        key_metrics.append(
            KeyMetric(
                name="Resting Heart Rate",
                value=round(readiness_summary.average_resting_hr),
                unit="bpm",
                status=(
                    "good" if readiness_summary.average_resting_hr < 70 else "moderate"
                ),
                comparison_to_average=0,
            )
        )

    # Calculate trends
    trends = []

    def calculate_trend(recent: List[float], older: List[float]):
        if not recent or not older:
            return "stable", 0
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        if older_avg == 0:
            return "stable", 0
        change = ((recent_avg - older_avg) / older_avg) * 100
        if change > 5:
            return "improving", round(change, 1)
        elif change < -5:
            return "declining", round(change, 1)
        return "stable", round(change, 1)

    if len(sleep_entries) >= 7:
        half = len(sleep_entries) // 2
        direction, change = calculate_trend(
            [e.sleep.sleep_score for e in sleep_entries[:half]],
            [e.sleep.sleep_score for e in sleep_entries[half:]],
        )
        trends.append(
            TrendSummary(
                metric="Sleep Quality",
                direction=direction,
                percentage_change=change,
                period=f"Last {days} days",
            )
        )

    if len(activity_entries) >= 7:
        half = len(activity_entries) // 2
        direction, change = calculate_trend(
            [e.activity.steps for e in activity_entries[:half]],
            [e.activity.steps for e in activity_entries[half:]],
        )
        trends.append(
            TrendSummary(
                metric="Activity Level",
                direction=direction,
                percentage_change=change,
                period=f"Last {days} days",
            )
        )

    # Identify concerns and improvements
    concerns = []
    improvements = []

    if sleep_summary.average_duration < 7:
        concerns.append("Average sleep duration is below recommended 7 hours")
    elif sleep_summary.average_duration >= 7.5:
        improvements.append("Maintaining healthy sleep duration")

    if sleep_summary.average_score < 70:
        concerns.append("Sleep quality score indicates room for improvement")
    elif sleep_summary.average_score >= 80:
        improvements.append("Sleep quality is consistently good")

    if activity_summary.average_steps < 5000:
        concerns.append("Daily step count is significantly below recommendations")
    elif activity_summary.average_steps >= 10000:
        improvements.append("Excellent daily activity levels")

    if readiness_summary.average_resting_hr > 75:
        concerns.append(
            "Resting heart rate is elevated - consider discussing with doctor"
        )
    elif readiness_summary.average_resting_hr < 60:
        improvements.append(
            "Excellent cardiovascular fitness indicated by low resting HR"
        )

    # Build intelligence indicators (best-effort, non-blocking)
    bearer = http_request.headers.get("Authorization") if http_request else None
    user_id = current_user["id"]

    health_intelligence = await _build_intelligence_indicators(
        timeline, user_id, bearer, days
    )
    nutrition_correlations = await _get_top_correlations(user_id)
    condition_notes = await _get_condition_notes(user_id)

    # Enrich concerns/improvements with intelligence data
    if health_intelligence:
        if health_intelligence.inflammation_risk in ("elevated", "high"):
            concerns.append(
                f"Inflammation risk is {health_intelligence.inflammation_risk} — "
                f"consider discussing anti-inflammatory diet strategies"
            )
        if health_intelligence.stress_index > 60:
            concerns.append(
                f"Stress index is elevated ({health_intelligence.stress_index}/100) — "
                f"review stress management and sleep hygiene"
            )
        if health_intelligence.nutrition_quality_score >= 70:
            improvements.append(
                f"Nutrition quality score is good ({health_intelligence.nutrition_quality_score}/100)"
            )
        elif (
            health_intelligence.nutrition_quality_score > 0
            and health_intelligence.nutrition_quality_score < 40
        ):
            concerns.append(
                f"Nutrition quality score is low ({health_intelligence.nutrition_quality_score}/100) — "
                f"macro balance could be improved"
            )

    # Build report
    report = DoctorPrepReport(
        id=str(uuid.uuid4()),
        user_id=user_id,
        generated_at=datetime.utcnow(),
        date_range={
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
        summary=ReportSummary(
            overall_health_score=round(overall_score, 1),
            key_metrics=key_metrics,
            trends=trends,
            concerns=concerns,
            improvements=improvements,
        ),
        detailed_data=DetailedData(
            sleep=sleep_summary, activity=activity_summary, readiness=readiness_summary
        ),
        health_intelligence=health_intelligence,
        nutrition_correlations=nutrition_correlations,
        condition_specific_notes=condition_notes,
    )

    logger.info(f"Generated doctor prep report for user {user_id}")
    return report


@router.get("/reports", response_model=List[DoctorPrepReport])
async def get_reports(current_user: dict = Depends(get_user_optional)):
    """
    Get previously generated reports.
    """
    # In production, fetch from database
    # For MVP, return empty list
    return []


@router.get("/reports/{report_id}", response_model=DoctorPrepReport)
async def get_report(report_id: str, current_user: dict = Depends(get_user_optional)):
    """
    Get a specific report by ID.
    """
    # In production, fetch from database
    raise HTTPException(status_code=404, detail="Report not found")


@router.get("/reports/{report_id}/pdf")
async def export_pdf(
    report_id: str, current_user: dict = Depends(UsageGate("pdf_export"))
):
    """
    Export a report as PDF.
    """
    # Generate fresh report for MVP
    report = await generate_report(
        GenerateReportRequest(days=30), current_user=current_user
    )

    # Create simple PDF content
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1 * inch, height - 1 * inch, "Health Summary Report")

    c.setFont("Helvetica", 12)
    c.drawString(
        1 * inch,
        height - 1.5 * inch,
        f"Period: {report.date_range['start']} to {report.date_range['end']}",
    )

    # Overall Score
    c.setFont("Helvetica-Bold", 14)
    c.drawString(
        1 * inch,
        height - 2.2 * inch,
        f"Overall Health Score: {report.summary.overall_health_score}",
    )

    # Key Metrics
    y = height - 3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Key Metrics:")
    y -= 0.3 * inch

    c.setFont("Helvetica", 11)
    for metric in report.summary.key_metrics:
        c.drawString(
            1.2 * inch,
            y,
            f"• {metric.name}: {metric.value} {metric.unit} ({metric.status})",
        )
        y -= 0.25 * inch

    # Trends
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Trends:")
    y -= 0.3 * inch

    c.setFont("Helvetica", 11)
    for trend in report.summary.trends:
        c.drawString(
            1.2 * inch,
            y,
            f"• {trend.metric}: {trend.direction} ({trend.percentage_change}%)",
        )
        y -= 0.25 * inch

    # Concerns
    if report.summary.concerns:
        y -= 0.3 * inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, y, "Areas to Discuss:")
        y -= 0.3 * inch

        c.setFont("Helvetica", 11)
        for concern in report.summary.concerns:
            c.drawString(1.2 * inch, y, f"• {concern}")
            y -= 0.25 * inch

    # Improvements
    if report.summary.improvements:
        y -= 0.3 * inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, y, "Positive Progress:")
        y -= 0.3 * inch

        c.setFont("Helvetica", 11)
        for improvement in report.summary.improvements:
            c.drawString(1.2 * inch, y, f"• {improvement}")
            y -= 0.25 * inch

    # Footer
    c.setFont("Helvetica", 9)
    c.drawString(
        1 * inch,
        0.5 * inch,
        f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
    )
    c.drawString(
        1 * inch, 0.35 * inch, "This report is for informational purposes only."
    )

    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=health-report-{report.date_range['end']}.pdf"
        },
    )
