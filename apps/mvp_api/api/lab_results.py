"""
Lab Results API — Phase 5: Lab Results & Health Twin

Manage lab test results, biomarker tracking, and AI-generated insights from lab data.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,line-too-long

import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_insert,
    _supabase_upsert,
    _supabase_patch,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()

# OpenAI for AI-generated insights
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("LAB_INSIGHTS_AI_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class Biomarker(BaseModel):
    """Individual biomarker measurement."""

    name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    status: str  # normal, borderline, abnormal, critical


class CreateLabResultRequest(BaseModel):
    """Request to create a new lab result."""

    test_date: str  # YYYY-MM-DD
    test_type: str  # cbc, metabolic_panel, lipid_panel, etc.
    lab_name: Optional[str] = None
    ordering_provider: Optional[str] = None
    biomarkers: List[Biomarker]
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class LabResult(BaseModel):
    """Lab result with all biomarkers."""

    id: str
    user_id: str
    test_date: str
    test_type: str
    lab_name: Optional[str] = None
    ordering_provider: Optional[str] = None
    biomarkers: List[Biomarker]
    abnormal_count: int
    critical_count: int
    ai_summary: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str]
    created_at: str
    updated_at: str


class BiomarkerTrend(BaseModel):
    """Trend analysis for a single biomarker."""

    id: str
    biomarker_code: str
    biomarker_name: str
    trend_type: str  # improving, worsening, stable, fluctuating
    direction: str  # increasing, decreasing, stable
    slope: Optional[float] = None
    first_test_date: str
    last_test_date: str
    test_count: int
    current_value: float
    previous_value: Optional[float] = None
    min_value: float
    max_value: float
    avg_value: float
    std_deviation: float
    current_status: str
    trend_significance: str
    interpretation: str
    recommendations: List[str]
    computed_at: str


class LabInsight(BaseModel):
    """AI-generated insight from lab results."""

    id: str
    insight_type: str
    category: str
    title: str
    description: str
    key_findings: Dict[str, Any]
    correlated_health_metrics: Optional[Dict[str, float]] = None
    confidence_score: float
    priority: str
    recommendations: List[Dict[str, str]]
    is_acknowledged: bool
    created_at: str


class LabResultsResponse(BaseModel):
    """Response containing lab results."""

    results: List[LabResult]
    total_count: int


class BiomarkerTrendsResponse(BaseModel):
    """Response containing biomarker trends."""

    trends: List[BiomarkerTrend]
    generated_at: str


class LabInsightsResponse(BaseModel):
    """Response containing lab insights."""

    insights: List[LabInsight]
    total_count: int


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _analyze_biomarker_status(
    value: float,
    biomarker_code: str,
    unit: str,
    user_age: int = 35,
    user_gender: str = "all",
) -> tuple[str, str]:
    """
    Analyze biomarker status based on reference ranges.
    Returns (status, reference_range_str).
    """
    # This is a simplified version. In production, you'd query biomarker_references table
    # For now, using hardcoded common ranges

    ranges = {
        "total_cholesterol": (125, 240, 200, 300, "mg/dL"),
        "ldl": (0, 160, 100, 190, "mg/dL"),
        "hdl": (40, 120, 60, 20, "mg/dL"),  # male ranges
        "triglycerides": (0, 150, 100, 500, "mg/dL"),
        "glucose": (65, 110, 100, 400, "mg/dL"),
        "hba1c": (4.0, 6.4, 5.6, 10.0, "%"),
        "tsh": (0.4, 4.5, 2.5, 20.0, "mIU/L"),
        "vitamin_d": (30, 100, 80, 150, "ng/mL"),
        "crp": (0, 3.0, 1.0, 10.0, "mg/L"),
    }

    code_lower = biomarker_code.lower().replace(" ", "_")

    if code_lower not in ranges:
        return "normal", "N/A"

    normal_min, normal_max, optimal_max, critical_high, ref_unit = ranges[code_lower]

    # Determine status
    if value < normal_min:
        status = "abnormal"
    elif value > critical_high:
        status = "critical"
    elif value > normal_max:
        status = "abnormal"
    elif value > optimal_max:
        status = "borderline"
    else:
        status = "normal"

    ref_range = f"{normal_min}-{normal_max} {ref_unit}"

    return status, ref_range


async def _generate_lab_summary(
    biomarkers: List[Dict[str, Any]], test_type: str
) -> str:
    """Generate AI summary of lab results."""
    if not OPENAI_API_KEY:
        return _generate_simple_summary(biomarkers)

    abnormal_markers = [
        b for b in biomarkers if b.get("status") not in ("normal", "borderline")
    ]

    if not abnormal_markers:
        return "All biomarkers within normal ranges. Overall lab results look good."

    prompt = f"""You are a health data analyst. Summarize these lab test results for a patient.

Test Type: {test_type}
Abnormal Biomarkers:
{json.dumps(abnormal_markers, indent=2)}

Provide a brief 2-3 sentence summary highlighting:
1. Which biomarkers are abnormal and their significance
2. Any patterns or concerns
3. General recommendation (if any)

Keep it concise and patient-friendly. Do not provide medical diagnoses."""

    try:
        timeout = aiohttp.ClientTimeout(total=10)
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
                    "max_tokens": 150,
                },
            ) as resp:
                if resp.status != 200:
                    return _generate_simple_summary(biomarkers)

                result = await resp.json()
                summary = result["choices"][0]["message"]["content"].strip()
                return summary
    except Exception as exc:
        logger.warning("AI summary generation failed: %s", exc)
        return _generate_simple_summary(biomarkers)


def _generate_simple_summary(biomarkers: List[Dict[str, Any]]) -> str:
    """Generate simple text summary without AI."""
    abnormal = sum(1 for b in biomarkers if b.get("status") == "abnormal")
    critical = sum(1 for b in biomarkers if b.get("status") == "critical")

    if critical > 0:
        return f"{critical} critical value(s) detected. Please consult with your healthcare provider."
    elif abnormal > 0:
        return f"{abnormal} biomarker(s) outside normal range. Consider discussing with your doctor."
    else:
        return "All biomarkers within normal ranges."


def _calculate_biomarker_trend(
    values: List[float], dates: List[str]
) -> tuple[str, str, float]:
    """
    Calculate trend for biomarker values over time.
    Returns (trend_type, direction, slope).
    """
    if len(values) < 2:
        return "stable", "stable", 0.0

    # Simple linear regression
    n = len(values)
    x = [float(i) for i in range(n)]
    y = values

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0.0

    # Determine direction
    if abs(slope) < 0.01:
        direction = "stable"
        trend_type = "stable"
    elif slope > 0:
        direction = "increasing"
        trend_type = "worsening" if slope > 0.1 else "fluctuating"
    else:
        direction = "decreasing"
        trend_type = "improving" if slope < -0.1 else "fluctuating"

    return trend_type, direction, slope


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/lab-results", response_model=LabResult)
async def create_lab_result(
    request: CreateLabResultRequest,
    current_user: dict = Depends(UsageGate("lab_results")),
):
    """
    Create a new lab result entry.
    Requires Pro+ subscription.
    """
    user_id = current_user["id"]

    # Convert biomarkers to JSON format
    biomarkers_data = []
    abnormal_count = 0
    critical_count = 0

    for biomarker in request.biomarkers:
        # Analyze status if not provided
        status = biomarker.status
        ref_range = biomarker.reference_range

        if not ref_range:
            status, ref_range = _analyze_biomarker_status(
                biomarker.value, biomarker.name, biomarker.unit
            )

        biomarker_dict = {
            "name": biomarker.name,
            "value": biomarker.value,
            "unit": biomarker.unit,
            "reference_range": ref_range,
            "status": status,
        }
        biomarkers_data.append(biomarker_dict)

        if status == "abnormal":
            abnormal_count += 1
        elif status == "critical":
            critical_count += 1

    # Generate AI summary
    ai_summary = await _generate_lab_summary(biomarkers_data, request.test_type)

    # Create lab result
    lab_result = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "test_date": request.test_date,
        "test_type": request.test_type,
        "lab_name": request.lab_name,
        "ordering_provider": request.ordering_provider,
        "biomarkers": json.dumps(biomarkers_data),
        "abnormal_count": abnormal_count,
        "critical_count": critical_count,
        "ai_summary": ai_summary,
        "notes": request.notes,
        "tags": request.tags or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_insert("lab_results", lab_result)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create lab result")

    # Parse biomarkers back for response
    result["biomarkers"] = json.loads(result["biomarkers"])

    return LabResult(**result)


@router.get("/lab-results", response_model=LabResultsResponse)
async def get_lab_results(
    test_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Get user's lab results with optional filtering."""
    user_id = current_user["id"]

    # Build query
    query = f"user_id=eq.{user_id}"

    if test_type:
        query += f"&test_type=eq.{test_type}"
    if start_date:
        query += f"&test_date=gte.{start_date}"
    if end_date:
        query += f"&test_date=lte.{end_date}"

    query += f"&order=test_date.desc&limit={limit}"

    results = await _supabase_get("lab_results", query)

    if not results:
        return LabResultsResponse(results=[], total_count=0)

    # Parse biomarkers JSON
    for result in results:
        if isinstance(result.get("biomarkers"), str):
            result["biomarkers"] = json.loads(result["biomarkers"])

    return LabResultsResponse(
        results=[LabResult(**r) for r in results], total_count=len(results)
    )


@router.get("/lab-results/{result_id}", response_model=LabResult)
async def get_lab_result(
    result_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific lab result by ID."""
    user_id = current_user["id"]

    results = await _supabase_get(
        "lab_results", f"id=eq.{result_id}&user_id=eq.{user_id}"
    )

    if not results:
        raise HTTPException(status_code=404, detail="Lab result not found")

    result = results[0]

    # Parse biomarkers JSON
    if isinstance(result.get("biomarkers"), str):
        result["biomarkers"] = json.loads(result["biomarkers"])

    return LabResult(**result)


@router.delete("/lab-results/{result_id}")
async def delete_lab_result(
    result_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a lab result."""
    user_id = current_user["id"]

    success = await _supabase_delete(
        "lab_results", f"id=eq.{result_id}&user_id=eq.{user_id}"
    )

    if not success:
        raise HTTPException(status_code=404, detail="Lab result not found")

    return {"success": True, "message": "Lab result deleted"}


@router.get("/biomarker-trends", response_model=BiomarkerTrendsResponse)
async def get_biomarker_trends(
    biomarker_code: Optional[str] = None,
    current_user: dict = Depends(UsageGate("lab_results")),
):
    """
    Get trend analysis for biomarkers.
    Analyzes all lab results to identify trends.
    Requires Pro+ subscription.
    """
    user_id = current_user["id"]

    # Fetch all lab results for the user
    results = await _supabase_get(
        "lab_results", f"user_id=eq.{user_id}&order=test_date.asc&limit=100"
    )

    if not results:
        return BiomarkerTrendsResponse(
            trends=[], generated_at=datetime.now(timezone.utc).isoformat()
        )

    # Parse biomarkers and group by biomarker name
    biomarker_data: Dict[str, List[Dict[str, Any]]] = {}

    for result in results:
        test_date = result["test_date"]
        biomarkers = (
            json.loads(result["biomarkers"])
            if isinstance(result["biomarkers"], str)
            else result["biomarkers"]
        )

        for bm in biomarkers:
            name = bm["name"]
            if biomarker_code and name.lower() != biomarker_code.lower():
                continue

            if name not in biomarker_data:
                biomarker_data[name] = []

            biomarker_data[name].append(
                {
                    "date": test_date,
                    "value": bm["value"],
                    "unit": bm["unit"],
                    "status": bm.get("status", "normal"),
                }
            )

    # Calculate trends
    trends = []

    for name, measurements in biomarker_data.items():
        if len(measurements) < 2:
            continue

        # Sort by date
        measurements.sort(key=lambda x: x["date"])

        values = [m["value"] for m in measurements]
        dates = [m["date"] for m in measurements]

        trend_type, direction, slope = _calculate_biomarker_trend(values, dates)

        current_value = values[-1]
        previous_value = values[-2] if len(values) >= 2 else None

        trend = {
            "id": str(uuid.uuid4()),
            "biomarker_code": name.lower().replace(" ", "_"),
            "biomarker_name": name,
            "trend_type": trend_type,
            "direction": direction,
            "slope": slope,
            "first_test_date": dates[0],
            "last_test_date": dates[-1],
            "test_count": len(values),
            "current_value": current_value,
            "previous_value": previous_value,
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "std_deviation": (
                sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)
            )
            ** 0.5,
            "current_status": measurements[-1]["status"],
            "trend_significance": "notable" if abs(slope) > 0.1 else "minor",
            "interpretation": f"{name} is {trend_type} ({direction})",
            "recommendations": [],
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

        trends.append(BiomarkerTrend(**trend))

    return BiomarkerTrendsResponse(
        trends=trends, generated_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/lab-insights", response_model=LabInsightsResponse)
async def get_lab_insights(
    priority: Optional[str] = None,
    current_user: dict = Depends(UsageGate("lab_results")),
):
    """
    Get AI-generated insights from lab results.
    Requires Pro+ subscription.
    """
    user_id = current_user["id"]

    query = f"user_id=eq.{user_id}"
    if priority:
        query += f"&priority=eq.{priority}"

    query += "&order=created_at.desc&limit=20"

    insights = await _supabase_get("lab_insights", query)

    if not insights:
        return LabInsightsResponse(insights=[], total_count=0)

    # Parse JSON fields
    for insight in insights:
        if isinstance(insight.get("key_findings"), str):
            insight["key_findings"] = json.loads(insight["key_findings"])
        if isinstance(insight.get("correlated_health_metrics"), str):
            insight["correlated_health_metrics"] = json.loads(
                insight["correlated_health_metrics"]
            )
        if isinstance(insight.get("recommendations"), str):
            insight["recommendations"] = json.loads(insight["recommendations"])

    return LabInsightsResponse(
        insights=[LabInsight(**i) for i in insights], total_count=len(insights)
    )


@router.patch("/lab-insights/{insight_id}/acknowledge")
async def acknowledge_insight(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a lab insight as acknowledged."""
    user_id = current_user["id"]

    result = await _supabase_patch(
        "lab_insights",
        f"id=eq.{insight_id}&user_id=eq.{user_id}",
        {
            "is_acknowledged": True,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    if not result:
        raise HTTPException(status_code=404, detail="Insight not found")

    return {"success": True, "message": "Insight acknowledged"}
