"""
AI Insights API
Endpoints for AI-generated health insights with explainability.
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,import-outside-toplevel,too-few-public-methods,missing-class-docstring,invalid-name,line-too-long

import os
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import UsageGate, _supabase_get

logger = get_logger(__name__)

# OpenAI for correlated insights synthesis
OPENAI_API_KEY_INSIGHTS = os.environ.get("OPENAI_API_KEY", "")

router = APIRouter()

# Sandbox mode
USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")

# Advanced insights wiring (AI Insights + Knowledge Graph)
ADVANCED_INSIGHTS_ENABLED = os.environ.get(
    "ADVANCED_INSIGHTS_ENABLED", "false"
).lower() in (
    "true",
    "1",
    "yes",
)
AI_INSIGHTS_URL = os.environ.get("AI_INSIGHTS_URL", "http://localhost:8200").rstrip("/")
KNOWLEDGE_GRAPH_URL = os.environ.get(
    "KNOWLEDGE_GRAPH_URL", "http://localhost:8010"
).rstrip("/")
ADVANCED_INSIGHTS_TIMEOUT_S = float(
    os.environ.get("ADVANCED_INSIGHTS_TIMEOUT_S", "6.0")
)


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


class InsightType(str, Enum):
    TREND = "trend"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"


class InsightCategory(str, Enum):
    SLEEP = "sleep"
    ACTIVITY = "activity"
    READINESS = "readiness"
    GENERAL = "general"


class DataPoint(BaseModel):
    metric: str
    value: float
    date: str
    trend: str  # "up", "down", "stable"


class AIInsight(BaseModel):
    id: str
    type: InsightType
    category: InsightCategory
    title: str
    summary: str
    explanation: str
    confidence: float
    data_points: List[DataPoint]
    created_at: datetime


class InsightsResponse(BaseModel):
    insights: List[AIInsight]
    generated_at: datetime


# Correlated insights: recommendation + evidence, multi-source (age, gender, meds, symptoms, etc.)
class CorrelatedInsight(BaseModel):
    id: str
    insight_type: str  # correlation | causation | medication_alert | pattern | supplement | general
    title: str
    recommendation: str
    evidence: str
    factors_considered: List[str] = []
    confidence: float = 0.0


def _safe_uuid_from_user_id(user_id: str) -> UUID:
    """
    Return a UUID for downstream services.

    - If user_id is already a UUID string, use it.
    - Otherwise derive a stable UUID from the string (so sandbox IDs work).
    """
    try:
        return UUID(str(user_id))
    except Exception:
        return uuid.uuid5(uuid.NAMESPACE_URL, str(user_id))


def _map_metric_to_category(metric: str) -> "InsightCategory":
    m = (metric or "").lower()
    if "sleep" in m:
        return InsightCategory.SLEEP
    if "step" in m or "activity" in m or "calorie" in m:
        return InsightCategory.ACTIVITY
    if (
        "readiness" in m
        or "hrv" in m
        or "resting_heart_rate" in m
        or "resting heart rate" in m
    ):
        return InsightCategory.READINESS
    return InsightCategory.GENERAL


def _severity_to_type(severity: Optional[str]) -> "InsightType":
    s = (severity or "").lower()
    if s in ("critical", "high", "medium"):
        return InsightType.ALERT
    return InsightType.TREND


def _build_clinical_questions(metric: str, direction: str) -> List[str]:
    """
    Generate clinician-friendly question prompts.
    Keep these as questions (not diagnoses or instructions).
    """
    m = (metric or "").lower()
    d = (direction or "").lower()

    if "sleep_score" in m or "sleep score" in m:
        first = (
            "What are the most common clinical reasons for a sustained drop in sleep quality, and which apply to me?"
            if "decreas" in d
            else "What are the most important factors that could be driving this sleep trend for me?"
        )
        return [
            first,
            "Could recent stress, travel, alcohol, caffeine timing, or a schedule change explain this trend?",
            "Are there symptoms of sleep disruption (snoring, choking/gasping, morning headaches) worth evaluating?",
            "If this persists, what additional monitoring or labs would you consider based on my history?",
        ]
    if "total_sleep" in m or "sleep_duration" in m:
        return [
            "Is my sleep duration sufficient for my age and activity level?",
            "Could circadian rhythm issues or insomnia be contributing to this pattern?",
            "Would you recommend a sleep diary or further evaluation if this continues?",
        ]
    if "deep_sleep" in m:
        return [
            "Could medications, alcohol, or late meals be affecting deep sleep?",
            "Is there anything in my health history that would make low deep sleep more concerning?",
            "If symptoms match, when is a sleep study appropriate?",
        ]
    if "resting_heart_rate" in m or "resting heart rate" in m:
        return [
            "Could dehydration, illness, stress, or overtraining explain this resting heart rate pattern?",
            "Is this change clinically meaningful for me given my baseline and symptoms?",
            "Would you recommend any follow-up measurements (BP, ECG, labs) if the trend persists?",
        ]
    if "readiness" in m or "hrv" in m:
        return [
            "Could training load, illness, or mental stress explain this recovery pattern?",
            "Are there lifestyle or medical factors that could lower HRV over time?",
            "What signs would indicate I should seek evaluation sooner?",
        ]

    # Generic fallback
    return [
        "Is this trend clinically meaningful for me given my personal risk factors and symptoms?",
        "What additional context or measurements would help interpret this change?",
        "At what point would you recommend follow-up testing or evaluation?",
    ]


def _direction_to_trend(direction: str) -> str:
    d = (direction or "").lower()
    if "increas" in d:
        return "up"
    if "decreas" in d:
        return "down"
    return "stable"


async def _kg_quick_search(query: str, limit: int = 2) -> List[dict]:
    """Fetch a few knowledge graph snippets to add medical context."""
    if not query:
        return []
    url = f"{KNOWLEDGE_GRAPH_URL}/api/v1/knowledge-graph/search/quick"
    params = {"q": query, "limit": limit}
    timeout = aiohttp.ClientTimeout(total=ADVANCED_INSIGHTS_TIMEOUT_S)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                payload = await resp.json()
                return payload.get("results", []) or []
    except Exception:
        return []


async def _get_advanced_insights(
    timeline: list,
    current_user: dict,
    limit: int,
) -> List[AIInsight]:
    """
    Generate insights by calling the AI Insights service, then enrich explanations
    with Knowledge Graph context and clinician-style question prompts.

    Falls back to an empty list on any failure (caller should then use rule-based insights).
    """
    patient_uuid = _safe_uuid_from_user_id(current_user.get("id", "sandbox-user-123"))
    token_payload = current_user.get("token_payload") or {}
    user_md = token_payload.get("user_metadata") or {}
    if not isinstance(user_md, dict):
        user_md = {}

    # Build a minimal vital_signs time series from the MVP timeline.
    vital_signs: List[dict] = []
    for entry in timeline:
        date = getattr(entry, "date", None)
        ts = str(date) if date else ""
        if getattr(entry, "sleep", None):
            s = entry.sleep
            vital_signs.extend(
                [
                    {
                        "metric": "sleep_score",
                        "value": float(s.sleep_score or 0),
                        "timestamp": ts,
                    },
                    {
                        "metric": "sleep_efficiency",
                        "value": float(s.sleep_efficiency or 0),
                        "timestamp": ts,
                    },
                    {
                        "metric": "total_sleep_duration_hours",
                        "value": float((s.total_sleep_duration or 0) / 3600),
                        "timestamp": ts,
                    },
                    {
                        "metric": "deep_sleep_duration_hours",
                        "value": float((s.deep_sleep_duration or 0) / 3600),
                        "timestamp": ts,
                    },
                ]
            )
        if getattr(entry, "readiness", None):
            r = entry.readiness
            vital_signs.extend(
                [
                    {
                        "metric": "readiness_score",
                        "value": float(r.readiness_score or 0),
                        "timestamp": ts,
                    },
                    {
                        "metric": "resting_heart_rate",
                        "value": float(r.resting_heart_rate or 0),
                        "timestamp": ts,
                    },
                    {
                        "metric": "hrv_balance",
                        "value": float(r.hrv_balance or 0),
                        "timestamp": ts,
                    },
                ]
            )
        if getattr(entry, "activity", None):
            a = entry.activity
            vital_signs.append(
                {"metric": "steps", "value": float(a.steps or 0), "timestamp": ts}
            )

    # AI Insights Agent endpoint (doesn't require patient_id/auth)
    url = f"{AI_INSIGHTS_URL}/api/v1/ai-insights/agents/generate-insight"
    payload = {
        "patient_id": str(patient_uuid),
        "health_metrics": [],  # required by agent interface; keep empty for MVP
        "vital_signs": vital_signs,
        "lab_results": [],
        "medication_data": [],
        "lifestyle_data": [],
        "medical_history": {
            # Best-effort: if the JWT is a Supabase token, these may be present in `user_metadata`
            "age": user_md.get("age"),
            "gender": user_md.get("gender"),
            "weight_kg": user_md.get("weight_kg"),
        },
    }

    timeout = aiohttp.ClientTimeout(total=ADVANCED_INSIGHTS_TIMEOUT_S)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                return []
            agent_result = await resp.json()

    if not agent_result.get("success"):
        return []

    raw_insights = agent_result.get("insights") or []
    if not isinstance(raw_insights, list) or not raw_insights:
        return []

    mapped: List[AIInsight] = []
    for item in raw_insights[: max(limit, 1) * 3]:
        if not isinstance(item, dict):
            continue

        metric = (item.get("metadata") or {}).get("metric") or (item.get("title") or "")
        direction = (item.get("metadata") or {}).get("trend_direction") or ""
        confidence = float(item.get("confidence_score") or 0.6)
        severity = item.get("severity")

        category = _map_metric_to_category(str(metric))
        insight_type = _severity_to_type(severity)

        # Pull a tiny bit of KG context (best-effort).
        kg_query = f"{str(metric).replace('_', ' ')} {direction}".strip()
        kg_hits = await _kg_quick_search(kg_query, limit=2)
        kg_context_lines = []
        for hit in kg_hits:
            name = hit.get("name")
            desc = hit.get("description")
            if name and desc:
                kg_context_lines.append(f"- {name}: {desc}")

        questions = _build_clinical_questions(str(metric), str(direction))
        questions_block = "\n".join([f"- {q}" for q in questions])

        explanation_parts = [
            (item.get("description") or "").strip(),
            "",
            "Suggested questions for your clinician:",
            questions_block,
        ]
        if kg_context_lines:
            explanation_parts.extend(
                ["", "Medical context (knowledge graph):", *kg_context_lines]
            )

        explanation = "\n".join([p for p in explanation_parts if p is not None]).strip()

        # Try to surface the actual metric value(s) from the AI agent evidence.
        trend_data = (item.get("supporting_evidence") or {}).get("trend_data") or {}
        values = trend_data.get("values") or []
        timestamps = trend_data.get("timestamps") or []
        latest_value = None
        latest_ts = ""
        if isinstance(values, list) and values:
            try:
                latest_value = float(values[-1])
            except Exception:
                latest_value = None
        if isinstance(timestamps, list) and timestamps:
            latest_ts = str(timestamps[-1] or "")

        points: List[DataPoint] = []
        if latest_value is not None:
            points.append(
                DataPoint(
                    metric=str(metric).replace("_", " ").title(),
                    value=latest_value,
                    date=latest_ts,
                    trend=_direction_to_trend(str(direction)),
                )
            )
        # Always include a confidence datapoint so the UI has an at-a-glance number even if values are missing.
        points.append(
            DataPoint(
                metric="Model confidence",
                value=max(0.0, min(confidence, 1.0)),
                date=latest_ts
                or (str(getattr(timeline[0], "date", "")) if timeline else ""),
                trend="stable",
            )
        )

        mapped.append(
            AIInsight(
                id=str(uuid.uuid4()),
                type=insight_type,
                category=category,
                title=(item.get("title") or "Health Trend").strip(),
                summary=(item.get("description") or "").strip()[:240],
                explanation=explanation,
                confidence=max(0.0, min(confidence, 1.0)),
                data_points=points,
                created_at=datetime.utcnow(),
            )
        )

    # Prefer sleep-related insights first (so the top-3 UI tends to include them)
    mapped.sort(
        key=lambda i: (
            0 if i.category == InsightCategory.SLEEP else 1,
            0 if i.type == InsightType.ALERT else 1,
            -(i.confidence or 0.0),
        )
    )

    return mapped[:limit]


@router.get("", response_model=List[AIInsight])
async def get_insights(
    limit: int = Query(default=5, ge=1, le=10),
    current_user: dict = Depends(UsageGate("ai_insights")),
):
    """
    Get AI-generated insights based on user's health data.
    Returns up to 5 personalized insights with explanations.
    """
    from .timeline import get_timeline

    # Fetch recent health data
    try:
        timeline = await get_timeline(days=14, current_user=current_user)
    except Exception as e:
        logger.error(f"Failed to fetch timeline for insights: {e}")
        timeline = []

    # Advanced insights path (AI Insights + Knowledge Graph). Best-effort with safe fallback.
    if ADVANCED_INSIGHTS_ENABLED and timeline:
        try:
            advanced = await _get_advanced_insights(
                timeline=timeline, current_user=current_user, limit=limit
            )
            if advanced:
                return advanced[:limit]
        except Exception as e:
            logger.warning(
                f"Advanced insights generation failed; falling back to rule-based insights: {e}"
            )

    insights = []

    if not timeline:
        # Return default insights if no data
        insights.append(
            AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.RECOMMENDATION,
                category=InsightCategory.GENERAL,
                title="Connect Your Device",
                summary="Connect your Oura Ring to start receiving personalized insights.",
                explanation="We analyze your sleep, activity, and readiness data to provide actionable recommendations. Once you connect your device and sync a few days of data, we'll generate insights tailored to your health patterns.",
                confidence=1.0,
                data_points=[],
                created_at=datetime.utcnow(),
            )
        )
        return insights[:limit]

    # Analyze sleep patterns
    sleep_data = [e for e in timeline if e.sleep]
    if len(sleep_data) >= 3:
        scores = [e.sleep.sleep_score for e in sleep_data]
        avg_score = sum(scores) / len(scores)
        recent_avg = sum(scores[:3]) / 3
        older_avg = (
            sum(scores[3:7]) / max(len(scores[3:7]), 1)
            if len(scores) > 3
            else avg_score
        )

        sleep_insight_added = False
        if recent_avg > older_avg + 5:
            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.TREND,
                    category=InsightCategory.SLEEP,
                    title="Sleep Quality Improving",
                    summary=f"Your sleep score has improved by {int(recent_avg - older_avg)} points over the past week.",
                    explanation=f"Looking at your last 14 days of sleep data, your average sleep score in the past 3 days ({int(recent_avg)}) is higher than the previous week ({int(older_avg)}). This improvement suggests your sleep habits or environment may be optimizing. Keep up whatever changes you've made!",
                    confidence=0.85,
                    data_points=[
                        DataPoint(
                            metric="Sleep Score (Recent)",
                            value=recent_avg,
                            date=sleep_data[0].date,
                            trend="up",
                        ),
                        DataPoint(
                            metric="Sleep Score (Previous)",
                            value=older_avg,
                            date=sleep_data[-1].date,
                            trend="stable",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )
            sleep_insight_added = True
        elif recent_avg < older_avg - 5:
            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.ALERT,
                    category=InsightCategory.SLEEP,
                    title="Sleep Quality Declining",
                    summary=f"Your sleep score has dropped by {int(older_avg - recent_avg)} points recently.",
                    explanation=f"Your recent sleep scores (avg {int(recent_avg)}) are lower than your previous week (avg {int(older_avg)}). This could be due to changes in bedtime routine, stress, or environmental factors. Consider reviewing your sleep habits.",
                    confidence=0.82,
                    data_points=[
                        DataPoint(
                            metric="Sleep Score (Recent)",
                            value=recent_avg,
                            date=sleep_data[0].date,
                            trend="down",
                        ),
                        DataPoint(
                            metric="Sleep Score (Previous)",
                            value=older_avg,
                            date=sleep_data[-1].date,
                            trend="stable",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )
            sleep_insight_added = True

        # Check deep sleep
        deep_sleep = [e.sleep.deep_sleep_duration for e in sleep_data]
        avg_deep = sum(deep_sleep) / len(deep_sleep)
        if avg_deep < 3600:  # Less than 1 hour
            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.RECOMMENDATION,
                    category=InsightCategory.SLEEP,
                    title="Boost Deep Sleep",
                    summary="Your deep sleep averages under 1 hour per night.",
                    explanation=f"Your average deep sleep is {int(avg_deep/60)} minutes, which is below the recommended 1-2 hours for adults. Deep sleep is crucial for physical recovery and immune function. Try avoiding alcohol and heavy meals before bed, keeping your room cool (65-68°F), and maintaining a consistent sleep schedule.",
                    confidence=0.78,
                    data_points=[
                        DataPoint(
                            metric="Avg Deep Sleep (min)",
                            value=avg_deep / 60,
                            date=sleep_data[0].date,
                            trend="stable",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )
            sleep_insight_added = True

        # Fallback: always emit at least one sleep insight when we have data
        if not sleep_insight_added:
            # Sleep duration (seconds) → hours
            durations = [e.sleep.total_sleep_duration for e in sleep_data]
            avg_hours = (sum(durations) / len(durations)) / 3600
            eff = [e.sleep.sleep_efficiency for e in sleep_data]
            avg_eff = sum(eff) / len(eff)

            # Create a simple, clinician-friendly trend summary even if stable.
            title = "Sleep Trend Snapshot"
            summary = (
                f"Your recent sleep looks stable. Avg sleep score ~{int(avg_score)}, "
                f"avg duration ~{avg_hours:.1f}h, efficiency ~{int(avg_eff)}%."
            )
            explanation = (
                "This insight is derived directly from your Oura sleep metrics (sleep score, duration, and efficiency) "
                "over the last 14 days. We compare the last 3 days to the prior week to detect changes, and otherwise "
                "summarize your baseline. If you're feeling off despite stable scores, consider tracking stress, travel, "
                "illness symptoms, caffeine/alcohol timing, and bedtime consistency."
            )

            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.TREND,
                    category=InsightCategory.SLEEP,
                    title=title,
                    summary=summary,
                    explanation=explanation,
                    confidence=0.7,
                    data_points=[
                        DataPoint(
                            metric="Avg Sleep Score (14d)",
                            value=avg_score,
                            date=sleep_data[0].date,
                            trend="stable",
                        ),
                        DataPoint(
                            metric="Avg Sleep Duration (h, 14d)",
                            value=avg_hours,
                            date=sleep_data[0].date,
                            trend="stable",
                        ),
                        DataPoint(
                            metric="Avg Sleep Efficiency (% , 14d)",
                            value=avg_eff,
                            date=sleep_data[0].date,
                            trend="stable",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )

    # Analyze activity patterns
    activity_data = [e for e in timeline if e.activity]
    if len(activity_data) >= 3:
        steps = [e.activity.steps for e in activity_data]
        avg_steps = sum(steps) / len(steps)

        if avg_steps < 5000:
            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.RECOMMENDATION,
                    category=InsightCategory.ACTIVITY,
                    title="Increase Daily Movement",
                    summary=f"Your daily steps average {int(avg_steps):,}, below the 7,500 target.",
                    explanation=f"Research shows 7,500-10,000 daily steps are associated with lower mortality risk. Your current average of {int(avg_steps):,} steps suggests opportunities for more movement. Try taking short walks after meals, using stairs instead of elevators, or setting hourly movement reminders.",
                    confidence=0.88,
                    data_points=[
                        DataPoint(
                            metric="Avg Daily Steps",
                            value=avg_steps,
                            date=activity_data[0].date,
                            trend="stable",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )
        elif avg_steps > 10000:
            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.TREND,
                    category=InsightCategory.ACTIVITY,
                    title="Great Activity Level",
                    summary=f"You're averaging {int(avg_steps):,} steps daily - excellent!",
                    explanation="Your consistent activity of over 10,000 daily steps is associated with improved cardiovascular health, better mood, and reduced disease risk. Keep maintaining this healthy habit!",
                    confidence=0.92,
                    data_points=[
                        DataPoint(
                            metric="Avg Daily Steps",
                            value=avg_steps,
                            date=activity_data[0].date,
                            trend="up",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )

    # Analyze readiness patterns
    readiness_data = [e for e in timeline if e.readiness]
    if len(readiness_data) >= 3:
        scores = [e.readiness.readiness_score for e in readiness_data]
        hrv = [e.readiness.hrv_balance for e in readiness_data]
        avg_hrv = sum(hrv) / len(hrv)

        if avg_hrv < 50:
            insights.append(
                AIInsight(
                    id=str(uuid.uuid4()),
                    type=InsightType.ALERT,
                    category=InsightCategory.READINESS,
                    title="Recovery May Be Low",
                    summary="Your HRV balance suggests your body may need more recovery time.",
                    explanation=f"Your HRV balance score of {int(avg_hrv)} indicates your autonomic nervous system may be under stress. This could be from physical training, mental stress, or insufficient sleep. Consider lighter workouts, stress reduction activities like meditation, and ensuring adequate sleep this week.",
                    confidence=0.75,
                    data_points=[
                        DataPoint(
                            metric="HRV Balance",
                            value=avg_hrv,
                            date=readiness_data[0].date,
                            trend="down",
                        ),
                    ],
                    created_at=datetime.utcnow(),
                )
            )

    # Add a general wellness insight if we have good data
    if len(insights) < limit and len(timeline) >= 7:
        insights.append(
            AIInsight(
                id=str(uuid.uuid4()),
                type=InsightType.RECOMMENDATION,
                category=InsightCategory.GENERAL,
                title="Track Consistently for Better Insights",
                summary="Wearing your ring consistently helps us provide more accurate insights.",
                explanation="The more complete your data, the better we can identify patterns and trends in your health. Try to wear your Oura Ring during sleep and throughout the day for the most comprehensive analysis.",
                confidence=0.95,
                data_points=[],
                created_at=datetime.utcnow(),
            )
        )

    return insights[:limit]


# ---------------------------------------------------------------------------
# Correlated insights: aggregate symptoms, meds, supplements, trends, research
# ---------------------------------------------------------------------------


async def _gather_correlated_context(current_user: dict) -> dict:
    """Gather timeline, correlations, medications, supplements, symptoms, profile for unified insights."""
    user_id = str(current_user.get("id", ""))
    token_payload = current_user.get("token_payload") or {}
    user_metadata = token_payload.get("user_metadata") or {}
    if not isinstance(user_metadata, dict):
        user_metadata = {}

    context = {
        "profile": {},
        "timeline_summary": "",
        "wearable_summary": "",
        "correlation_summary": "",
        "causal_edges": [],
        "medications": [],
        "supplements": [],
        "medication_alerts": [],
        "symptom_summary": "",
        "health_conditions": [],
        "lab_summary": "",
        "goals_summary": "",
        "doctor_relevant_notes": "",
        "saved_research_summary": "",
        "on_demand_research_summary": "",
        "symptom_correlations_summary": "",
        "medication_vitals_summary": "",
    }

    # Profile: age, gender
    context["profile"] = {
        "age": user_metadata.get("age"),
        "gender": user_metadata.get("gender"),
        "weight_kg": user_metadata.get("weight_kg"),
    }

    # Timeline + wearable (Oura: HRV, resting heart rate, physical activity, sleep)
    try:
        from .timeline import get_timeline

        timeline = await get_timeline(days=14, current_user=current_user)
        if timeline:
            sleep_entries = [e for e in timeline if getattr(e, "sleep", None)]
            activity_entries = [e for e in timeline if getattr(e, "activity", None)]
            readiness_entries = [e for e in timeline if getattr(e, "readiness", None)]
            context["timeline_summary"] = (
                f"Last 14 days: {len(sleep_entries)} sleep days, {len(activity_entries)} activity days, "
                f"{len(readiness_entries)} readiness days."
            )

            # Wearable (Oura) metrics for correlation/causation insights
            wearable_parts = []
            if readiness_entries:
                hrv = [
                    e.readiness.hrv_balance
                    for e in readiness_entries
                    if getattr(e.readiness, "hrv_balance", None) is not None
                ]
                rhr = [
                    e.readiness.resting_heart_rate
                    for e in readiness_entries
                    if getattr(e.readiness, "resting_heart_rate", None) is not None
                ]
                if hrv:
                    wearable_parts.append(
                        "HRV balance (avg): %.1f (n=%d days)"
                        % (sum(hrv) / len(hrv), len(hrv))
                    )
                if rhr:
                    wearable_parts.append(
                        "Resting heart rate (avg): %d bpm (n=%d days)"
                        % (round(sum(rhr) / len(rhr)), len(rhr))
                    )
                scores = [
                    e.readiness.readiness_score
                    for e in readiness_entries
                    if getattr(e.readiness, "readiness_score", None) is not None
                ]
                if scores:
                    wearable_parts.append(
                        "Readiness score (avg): %.1f" % (sum(scores) / len(scores))
                    )
            if activity_entries:
                steps = [
                    e.activity.steps
                    for e in activity_entries
                    if getattr(e.activity, "steps", None) is not None
                ]
                if steps:
                    avg_steps = sum(steps) / len(steps)
                    wearable_parts.append(
                        "Daily steps (avg): %d (n=%d days)"
                        % (round(avg_steps), len(steps))
                    )
                active_cal = [
                    e.activity.active_calories
                    for e in activity_entries
                    if getattr(e.activity, "active_calories", None) is not None
                ]
                if active_cal:
                    wearable_parts.append(
                        "Active calories (avg): %d kcal"
                        % round(sum(active_cal) / len(active_cal))
                    )
                scores = [
                    e.activity.activity_score
                    for e in activity_entries
                    if getattr(e.activity, "activity_score", None) is not None
                ]
                if scores:
                    wearable_parts.append(
                        "Activity score (avg): %.1f" % (sum(scores) / len(scores))
                    )
            if sleep_entries:
                sleep_scores = [
                    e.sleep.sleep_score
                    for e in sleep_entries
                    if getattr(e.sleep, "sleep_score", None) is not None
                ]
                if sleep_scores:
                    wearable_parts.append(
                        "Sleep score (avg): %.1f (n=%d nights)"
                        % (sum(sleep_scores) / len(sleep_scores), len(sleep_scores))
                    )
                deep = [
                    e.sleep.deep_sleep_duration
                    for e in sleep_entries
                    if getattr(e.sleep, "deep_sleep_duration", None) is not None
                ]
                if deep:
                    avg_deep_min = (sum(deep) / len(deep)) / 60
                    wearable_parts.append("Deep sleep (avg): %.0f min" % avg_deep_min)
                total = [
                    e.sleep.total_sleep_duration
                    for e in sleep_entries
                    if getattr(e.sleep, "total_sleep_duration", None) is not None
                ]
                if total:
                    avg_hrs = (sum(total) / len(total)) / 3600
                    wearable_parts.append("Total sleep (avg): %.1f h" % avg_hrs)
            if wearable_parts:
                context["wearable_summary"] = "Wearable (Oura) data: " + "; ".join(
                    wearable_parts
                )
    except Exception as e:
        logger.warning("Timeline fetch for correlated insights: %s", e)

    # Correlation cache (nutrition + vitals); engine uses multi-lag 1-14, Spearman, Granger causality
    try:
        from .correlations import _get_cached_results

        cached = await _get_cached_results(user_id, 14) or await _get_cached_results(
            user_id, 7
        )
        if cached:
            context["correlation_summary"] = (cached.get("summary") or "")[:800]
            # Pass causal/lag detail so insights can cite effect timing, magnitude, controlled-for
            corr_data = cached.get("correlations", "[]")
            if isinstance(corr_data, str):
                try:
                    corr_data = json.loads(corr_data)
                except Exception:
                    corr_data = []
            if isinstance(corr_data, list) and corr_data:
                edges = []
                for c in corr_data[:10]:
                    a = c.get("metric_a_label") or c.get("metric_a") or "X"
                    b = c.get("metric_b_label") or c.get("metric_b") or "Y"
                    r = c.get("correlation_coefficient")
                    lag = c.get("lag_days", 0)
                    edges.append(
                        "%s→%s lag %d r=%s"
                        % (a, b, lag, round(r, 2) if r is not None else "?")
                    )
                context["causal_edges"] = edges
    except Exception as e:
        logger.warning("Correlation cache fetch for correlated insights: %s", e)

    # Medications and supplements
    try:
        meds = await _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&select=medication_name,dosage,frequency&limit=20",
        )
        sups = await _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&select=supplement_name,dosage,frequency,brand&limit=20",
        )
        context["medications"] = [
            "%s (%s, %s)"
            % (
                m.get("medication_name") or "",
                m.get("dosage") or "",
                m.get("frequency") or "",
            )
            for m in (meds or [])
            if m.get("medication_name")
        ]
        context["supplements"] = [
            "%s (%s, %s)"
            % (
                s.get("supplement_name") or "",
                s.get("dosage") or "",
                s.get("frequency") or "",
            )
            for s in (sups or [])
            if s.get("supplement_name")
        ]
    except Exception as e:
        logger.warning("Meds/supplements fetch for correlated insights: %s", e)

    # Medication interaction alerts
    try:
        alerts = await _supabase_get(
            "user_medication_alerts",
            f"user_id=eq.{user_id}&is_dismissed=eq.false&select=title,description,severity&limit=10",
        )
        context["medication_alerts"] = [
            {
                "title": a.get("title"),
                "description": a.get("description"),
                "severity": a.get("severity"),
            }
            for a in (alerts or [])
        ]
    except Exception as e:
        logger.warning("Medication alerts fetch for correlated insights: %s", e)

    # Symptom journal summary (count by type)
    try:
        from datetime import date, timedelta

        start = (date.today() - timedelta(days=14)).isoformat()
        rows = await _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{start}&select=symptom_type,severity&limit=100",
        )
        if rows:
            from collections import Counter

            types = Counter(
                r.get("symptom_type") for r in rows if r.get("symptom_type")
            )
            context["symptom_summary"] = "; ".join(
                f"{t}: {c} entries" for t, c in types.most_common(5)
            )
    except Exception as e:
        logger.warning("Symptom fetch for correlated insights: %s", e)

    # Health conditions (for specificity and causation)
    try:
        cond_rows = await _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name,severity,condition_category&limit=20",
        )
        if cond_rows:
            context["health_conditions"] = [
                "%s (%s)" % (c.get("condition_name", ""), c.get("severity", ""))
                for c in cond_rows
                if c.get("condition_name")
            ]
            context["doctor_relevant_notes"] = "Conditions on file: " + "; ".join(
                context["health_conditions"]
            )
    except Exception as e:
        logger.warning("Health conditions fetch for correlated insights: %s", e)

    # Lab results summary (recent tests and key biomarkers)
    try:
        lab_rows = await _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&select=test_type,test_date,biomarkers&limit=10",
        )
        if lab_rows:
            parts = []
            for row in lab_rows[:5]:
                t = row.get("test_type") or "Lab"
                d = row.get("test_date") or ""
                b = row.get("biomarkers")
                if isinstance(b, str):
                    try:
                        b = json.loads(b) if b else {}
                    except Exception:
                        b = {}
                if isinstance(b, dict) and b:
                    parts.append("%s (%s): %s" % (t, d[:10] if d else "", str(b)[:200]))
                else:
                    parts.append("%s (%s)" % (t, d[:10] if d else ""))
            context["lab_summary"] = "Recent labs: " + "; ".join(parts)
    except Exception as e:
        logger.warning("Lab results fetch for correlated insights: %s", e)

    # Goals (health twin goals and/or nutrition goals)
    try:
        twin_goals = await _supabase_get(
            "health_twin_goals",
            f"user_id=eq.{user_id}&is_active=eq.true&select=goal_name,goal_type&limit=10",
        )
        if twin_goals:
            context["goals_summary"] = "Goals: " + ", ".join(
                g.get("goal_name") or g.get("goal_type") or "" for g in twin_goals
            )
    except Exception as e:
        logger.warning("Goals fetch for correlated insights: %s", e)

    # Saved research (user's bookmarked articles) — use for evidence when relevant
    try:
        bookmarks = await _supabase_get(
            "article_bookmarks",
            f"user_id=eq.{user_id}&order=bookmarked_at.desc&select=article_id&limit=10",
        )
        if bookmarks:
            aids = [str(b["article_id"]) for b in bookmarks if b.get("article_id")]
            if aids:
                ids_param = ",".join(aids[:5])
                articles = await _supabase_get(
                    "research_articles",
                    f"id=in.({ids_param})&select=title,abstract",
                )
                if articles:
                    saved_parts = []
                    for a in articles[:3]:
                        title = (a.get("title") or "")[:120]
                        abstract = (a.get("abstract") or "")[:200]
                        saved_parts.append("[%s] %s" % (title, abstract))
                    context[
                        "saved_research_summary"
                    ] = "User saved/bookmarked research: " + " | ".join(saved_parts)
    except Exception as e:
        logger.warning("Saved research fetch for correlated insights: %s", e)

    # On-demand research: narrow PubMed query from meds + conditions + symptoms
    try:
        from .medical_literature import (
            _pubmed_search,
            _pubmed_fetch_articles,
            _cache_article,
        )

        query_parts = []
        if context.get("medications"):
            query_parts.append(" ".join(context["medications"][:2]))
        if context.get("health_conditions"):
            query_parts.append(context["health_conditions"][0].split("(")[0].strip())
        if context.get("symptom_summary"):
            query_parts.append(context["symptom_summary"].split(";")[0].strip()[:50])
        if query_parts:
            on_demand_query = " ".join(query_parts)[:100]
            pmids = await _pubmed_search(on_demand_query, max_results=2)
            if pmids:
                articles = await _pubmed_fetch_articles(pmids)
                for art in articles[:2]:
                    await _cache_article(art)
                on_demand_parts = [
                    "[%s] %s"
                    % (
                        (art.get("title") or "")[:100],
                        (art.get("abstract") or "")[:300],
                    )
                    for art in articles[:2]
                ]
                if on_demand_parts:
                    context["on_demand_research_summary"] = (
                        "On-demand research (PubMed) for '%s': " % on_demand_query
                        + " | ".join(on_demand_parts)
                    )
    except Exception as e:
        logger.warning("On-demand research for correlated insights: %s", e)

    # Symptom–nutrition and symptom–Oura correlations (e.g. headaches vs deep sleep, digestive vs high-fat)
    try:
        from datetime import datetime as _dt, timezone as _tz

        now_iso = _dt.now(_tz.utc).isoformat()
        sym_rows = await _supabase_get(
            "symptom_correlations",
            f"user_id=eq.{user_id}&expires_at=gt.{now_iso}&order=computed_at.desc&select=symptom_type,correlation_type,correlated_variable_label,correlation_coefficient,p_value,effect_description&limit=15",
        )
        if sym_rows:
            parts = []
            for r in sym_rows[:10]:
                st = r.get("symptom_type") or "symptom"
                var = (
                    r.get("correlated_variable_label")
                    or r.get("correlated_variable")
                    or "metric"
                )
                coef = r.get("correlation_coefficient")
                p = r.get("p_value")
                desc = (r.get("effect_description") or "")[:80]
                parts.append(
                    "%s↔%s (r=%s, p=%s): %s"
                    % (
                        st,
                        var,
                        round(coef, 2) if coef is not None else "?",
                        round(p, 3) if p is not None else "?",
                        desc,
                    )
                )
            if parts:
                context[
                    "symptom_correlations_summary"
                ] = "Symptom correlations: " + "; ".join(parts)
    except Exception as e:
        logger.warning("Symptom correlations fetch for correlated insights: %s", e)

    # Medication–vitals correlations (e.g. HRV drops within 2h of medication)
    try:
        from datetime import datetime as _dt2, timezone as _tz2

        now_iso2 = _dt2.now(_tz2.utc).isoformat()
        med_rows = await _supabase_get(
            "medication_vitals_correlations",
            f"user_id=eq.{user_id}&expires_at=gt.{now_iso2}&order=computed_at.desc&select=medication_name,vital_label,lag_hours,optimal_timing_window,effect_description,effect_type&limit=10",
        )
        if med_rows:
            parts = []
            for r in med_rows[:6]:
                med = r.get("medication_name") or "Medication"
                vital = r.get("vital_label") or r.get("vital_metric") or "vital"
                lag = r.get("lag_hours")
                win = r.get("optimal_timing_window") or ""
                desc = (r.get("effect_description") or "")[:80]
                timing = win or (("%d h after dose" % lag) if lag is not None else "")
                parts.append("%s→%s (%s): %s" % (med, vital, timing, desc))
            if parts:
                context[
                    "medication_vitals_summary"
                ] = "Medication–vitals: " + "; ".join(parts)
    except Exception as e:
        logger.warning("Medication vitals fetch for correlated insights: %s", e)

    return context


async def _generate_correlated_insights_ai(context: dict) -> List[dict]:
    """Call OpenAI to synthesize 3-5 correlated insights (recommendation + evidence)."""
    if not OPENAI_API_KEY_INSIGHTS or not OPENAI_API_KEY_INSIGHTS.strip():
        logger.info(
            "Correlated insights skipped: OPENAI_API_KEY is not set. "
            "Set OPENAI_API_KEY in your environment (e.g. on Render) to enable AI-generated insights."
        )
        return []

    profile = context.get("profile") or {}
    parts = [
        "Profile (use for context): age=%s, gender=%s, weight_kg=%s"
        % (profile.get("age"), profile.get("gender"), profile.get("weight_kg")),
        "Timeline: %s" % (context.get("timeline_summary") or "No timeline data"),
        "Wearable (Oura) metrics — use these for physical activity, HRV, resting heart rate, sleep when relevant: %s"
        % (context.get("wearable_summary") or "No wearable data"),
        "Correlation summary: %s" % (context.get("correlation_summary") or "None"),
        "Causal/lag detail (from correlation engine): %s"
        % ("; ".join(context.get("causal_edges") or []) or "None"),
        "Medications: %s" % ", ".join(context.get("medications") or []),
        "Supplements: %s" % ", ".join(context.get("supplements") or []),
        "Recent symptoms: %s" % (context.get("symptom_summary") or "None"),
        "Health conditions: %s"
        % (", ".join(context.get("health_conditions") or []) or "None"),
        "Labs (recent): %s" % (context.get("lab_summary") or "None"),
        "Goals: %s" % (context.get("goals_summary") or "None"),
        "Doctor-relevant / condition notes: %s"
        % (context.get("doctor_relevant_notes") or "None"),
        "User saved research (bookmarks): %s"
        % (context.get("saved_research_summary") or "None"),
        "On-demand research (PubMed): %s"
        % (context.get("on_demand_research_summary") or "None"),
        "Symptom correlations (e.g. headache vs deep sleep, digestive vs nutrition): %s"
        % (context.get("symptom_correlations_summary") or "None"),
        "Medication–vitals (e.g. HRV drops within 2h of medication): %s"
        % (context.get("medication_vitals_summary") or "None"),
    ]
    for a in context.get("medication_alerts") or []:
        parts.append("Alert: %s - %s" % (a.get("title"), a.get("description")))

    prompt = (
        "Using ONLY the following aggregated health data, produce 3-5 short insights. "
        "Use EVERY available signal: profile, wearable (Oura), medications (dosage, timing, frequency), supplements, symptoms (severity, duration, triggers), health conditions, labs, goals, doctor/condition notes, saved research, on-demand research, symptom correlations (e.g. headache↔deep sleep), medication–vitals (e.g. HRV drops within 2h of medication). "
        "When mentioning medications and side effects: users can track side effects as symptoms in the symptom journal; correlate with medication timing when data exists. For drug–nutrient insights (e.g. Metformin and B12) cite a study when possible. "
        "When you HAVE relevant personal data for an insight: start the recommendation with 'Given your [specific data, e.g. labs/conditions/meds]...' and be specific. "
        "When you do NOT have relevant personal data for that topic: start with 'We don't have enough personal data in this area; here is general guidance:' then give generic, evidence-based advice and be explicit it is general. "
        "Each insight must have: title (short), recommendation (actionable; first line personalized or explicitly generic as above), "
        "evidence (one sentence: causation, correlation, or study/pattern; cite saved or on-demand research when relevant). "
        "For correlation/causation insights when data supports it: state causal confidence (e.g. 78%%), effect timing (e.g. 8-12 hours or next day from lag), magnitude when possible (e.g. 10g sugar ≈ -3 HRV points), and 'Controlled for: sleep duration, alcohol, stress' when relevant. "
        "insight_type (one of: correlation, causation, medication_alert, pattern, supplement, general), "
        "factors_considered (list of strings, e.g. age, medication, sleep, labs, conditions, goals, symptoms, hrv, activity). "
        "End every recommendation with exactly: 'This is not medical advice. If you have questions, follow up with your doctor.' "
        "Output valid JSON only, array of objects with keys: title, recommendation, evidence, insight_type, factors_considered.\n\n"
        "Data:\n" + "\n".join(parts)
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": "Bearer %s" % OPENAI_API_KEY_INSIGHTS,
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a health insights synthesizer. Output only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 1024,
                },
                timeout=aiohttp.ClientTimeout(total=45),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        "Correlated insights OpenAI returned status %s: %s",
                        resp.status,
                        body[:500] if body else "",
                    )
                    return []
                data = await resp.json()
                content = (data.get("choices") or [{}])[0].get("message", {}).get(
                    "content"
                ) or ""
    except Exception as e:
        logger.warning("Correlated insights OpenAI call failed: %s", e)
        return []

    import json

    try:
        # Strip markdown code block if present
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        insights = json.loads(content.strip())
        if not isinstance(insights, list):
            return []
        return insights[:5]
    except json.JSONDecodeError as e:
        logger.warning("Correlated insights OpenAI response was not valid JSON: %s", e)
        return []


@router.get("/correlated", response_model=List[CorrelatedInsight])
async def get_correlated_insights(
    current_user: dict = Depends(UsageGate("ai_insights")),
):
    """
    Unified correlated insights: supplements, symptoms, trends, nutrition, health profile,
    medications, research-style evidence. Uses correlation, causation, and patterns.
    Returns recommendation + evidence per insight with factors_considered (age, gender, etc.).
    """
    context = await _gather_correlated_context(current_user)
    raw = await _generate_correlated_insights_ai(context)

    disclaimer = " This is not medical advice. If you have questions, follow up with your doctor."
    out = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "Insight").strip()[:200]
        rec = (item.get("recommendation") or "").strip()[:500]
        if rec and disclaimer.strip() not in rec:
            rec = (rec + disclaimer)[:600]
        ev = (item.get("evidence") or "").strip()[:600]
        itype = (item.get("insight_type") or "general").strip()[:50]
        factors = item.get("factors_considered")
        if not isinstance(factors, list):
            factors = []
        factors = [str(f)[:50] for f in factors][:8]
        out.append(
            CorrelatedInsight(
                id=str(uuid.uuid4()),
                insight_type=itype,
                title=title,
                recommendation=rec,
                evidence=ev,
                factors_considered=factors,
                confidence=0.8,
            )
        )

    # Fallback: if no AI insights, return 1–2 from raw context
    if not out and context.get("medication_alerts"):
        for a in context["medication_alerts"][:2]:
            out.append(
                CorrelatedInsight(
                    id=str(uuid.uuid4()),
                    insight_type="medication_alert",
                    title=(a.get("title") or "Medication alert")[:200],
                    recommendation="Discuss with your doctor or pharmacist.",
                    evidence=(a.get("description") or "")[:600],
                    factors_considered=["medication"],
                    confidence=0.9,
                )
            )
    if not out and context.get("correlation_summary"):
        out.append(
            CorrelatedInsight(
                id=str(uuid.uuid4()),
                insight_type="correlation",
                title="Pattern from your data",
                recommendation="Review your correlation trends in the Metabolic Intelligence section.",
                evidence=context["correlation_summary"][:600],
                factors_considered=["nutrition", "vitals"],
                confidence=0.7,
            )
        )

    # When still empty (e.g. no OpenAI key, or OpenAI failed, and no fallbacks), return one placeholder
    # so the UI can show a message instead of a blank list
    if not out:
        out.append(
            CorrelatedInsight(
                id=str(uuid.uuid4()),
                insight_type="general",
                title="Insights will appear here",
                recommendation=(
                    "Add medications, log symptoms, connect your wearable, or ensure the server has "
                    "OPENAI_API_KEY set to generate personalized insights. This is not medical advice."
                ),
                evidence="When enough data is available and AI is configured, correlated insights will appear here.",
                factors_considered=[],
                confidence=0.0,
            )
        )

    return out[:5]


@router.get("/{insight_id}", response_model=AIInsight)
async def get_insight_detail(
    insight_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific insight.
    """
    # In production, fetch from database
    # For MVP, regenerate and find matching ID
    insights = await get_insights(limit=10, current_user=current_user)

    for insight in insights:
        if insight.id == insight_id:
            return insight

    raise HTTPException(status_code=404, detail="Insight not found")


@router.post("/{insight_id}/dismiss")
async def dismiss_insight(
    insight_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Dismiss an insight so it won't appear again.
    """
    # In production, store dismissal in database
    logger.info(f"User {current_user['id']} dismissed insight {insight_id}")
    return {"status": "dismissed"}


@router.post("/refresh", response_model=List[AIInsight])
async def refresh_insights(current_user: dict = Depends(get_current_user)):
    """
    Force refresh of AI insights.
    Regenerates insights based on latest data.
    """
    return await get_insights(limit=5, current_user=current_user)
