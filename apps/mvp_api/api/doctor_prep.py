"""
Doctor Visit Prep API
Endpoints for generating health summary reports for doctor visits.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import io
import os

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger

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
                "user_type": "sandbox"
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


class DoctorPrepReport(BaseModel):
    id: str
    user_id: str
    generated_at: datetime
    date_range: dict
    summary: ReportSummary
    detailed_data: DetailedData


class GenerateReportRequest(BaseModel):
    days: int = 30


@router.post("/generate", response_model=DoctorPrepReport)
async def generate_report(
    request: GenerateReportRequest,
    current_user: dict = Depends(get_user_optional)
):
    """
    Generate a comprehensive health summary report for doctor visits.
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
        raise HTTPException(status_code=400, detail="Insufficient data to generate report")

    # Calculate sleep metrics
    sleep_entries = [e for e in timeline if e.sleep]
    if sleep_entries:
        sleep_scores = [e.sleep.sleep_score for e in sleep_entries]
        sleep_durations = [e.sleep.total_sleep_duration / 3600 for e in sleep_entries]  # hours
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
            highest_readiness_day=max(readiness_entries, key=lambda x: x.readiness.readiness_score).date,
            lowest_readiness_day=min(readiness_entries, key=lambda x: x.readiness.readiness_score).date,
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
        key_metrics.append(KeyMetric(
            name="Sleep Score",
            value=round(sleep_summary.average_score, 1),
            unit="",
            status=get_status(sleep_summary.average_score),
            comparison_to_average=0
        ))
        key_metrics.append(KeyMetric(
            name="Sleep Duration",
            value=round(sleep_summary.average_duration, 1),
            unit="hours",
            status="good" if sleep_summary.average_duration >= 7 else "moderate",
            comparison_to_average=0
        ))

    if activity_entries:
        key_metrics.append(KeyMetric(
            name="Daily Steps",
            value=round(activity_summary.average_steps),
            unit="steps",
            status="good" if activity_summary.average_steps >= 7500 else "moderate",
            comparison_to_average=0
        ))
        key_metrics.append(KeyMetric(
            name="Activity Score",
            value=round(activity_summary.average_score, 1),
            unit="",
            status=get_status(activity_summary.average_score),
            comparison_to_average=0
        ))

    if readiness_entries:
        key_metrics.append(KeyMetric(
            name="Resting Heart Rate",
            value=round(readiness_summary.average_resting_hr),
            unit="bpm",
            status="good" if readiness_summary.average_resting_hr < 70 else "moderate",
            comparison_to_average=0
        ))

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
            [e.sleep.sleep_score for e in sleep_entries[half:]]
        )
        trends.append(TrendSummary(
            metric="Sleep Quality",
            direction=direction,
            percentage_change=change,
            period=f"Last {days} days"
        ))

    if len(activity_entries) >= 7:
        half = len(activity_entries) // 2
        direction, change = calculate_trend(
            [e.activity.steps for e in activity_entries[:half]],
            [e.activity.steps for e in activity_entries[half:]]
        )
        trends.append(TrendSummary(
            metric="Activity Level",
            direction=direction,
            percentage_change=change,
            period=f"Last {days} days"
        ))

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
        concerns.append("Resting heart rate is elevated - consider discussing with doctor")
    elif readiness_summary.average_resting_hr < 60:
        improvements.append("Excellent cardiovascular fitness indicated by low resting HR")

    # Build report
    report = DoctorPrepReport(
        id=str(uuid.uuid4()),
        user_id=current_user['id'],
        generated_at=datetime.utcnow(),
        date_range={
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        },
        summary=ReportSummary(
            overall_health_score=round(overall_score, 1),
            key_metrics=key_metrics,
            trends=trends,
            concerns=concerns,
            improvements=improvements
        ),
        detailed_data=DetailedData(
            sleep=sleep_summary,
            activity=activity_summary,
            readiness=readiness_summary
        )
    )

    logger.info(f"Generated doctor prep report for user {current_user['id']}")
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
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_user_optional)
):
    """
    Get a specific report by ID.
    """
    # In production, fetch from database
    raise HTTPException(status_code=404, detail="Report not found")


@router.get("/reports/{report_id}/pdf")
async def export_pdf(
    report_id: str,
    current_user: dict = Depends(get_user_optional)
):
    """
    Export a report as PDF.
    """
    # Generate fresh report for MVP
    report = await generate_report(
        GenerateReportRequest(days=30),
        current_user=current_user
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
    c.drawString(1 * inch, height - 1.5 * inch,
                 f"Period: {report.date_range['start']} to {report.date_range['end']}")

    # Overall Score
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 2.2 * inch,
                 f"Overall Health Score: {report.summary.overall_health_score}")

    # Key Metrics
    y = height - 3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Key Metrics:")
    y -= 0.3 * inch

    c.setFont("Helvetica", 11)
    for metric in report.summary.key_metrics:
        c.drawString(1.2 * inch, y, f"• {metric.name}: {metric.value} {metric.unit} ({metric.status})")
        y -= 0.25 * inch

    # Trends
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Trends:")
    y -= 0.3 * inch

    c.setFont("Helvetica", 11)
    for trend in report.summary.trends:
        c.drawString(1.2 * inch, y, f"• {trend.metric}: {trend.direction} ({trend.percentage_change}%)")
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
    c.drawString(1 * inch, 0.5 * inch, f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    c.drawString(1 * inch, 0.35 * inch, "This report is for informational purposes only.")

    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=health-report-{report.date_range['end']}.pdf"
        }
    )
