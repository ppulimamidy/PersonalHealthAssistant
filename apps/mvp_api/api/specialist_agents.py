"""
Specialist Multi-Agent System
Domain-specific expert agents with orchestrator for holistic health analysis
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel  # pylint: disable=too-few-public-methods

from common.utils.logging import get_logger
from common.database.supabase_client import get_supabase_client
from common.ai.openai_client import get_openai_client
from ..dependencies.auth import get_current_user
from ..dependencies.usage_gate import UsageGate

logger = get_logger(__name__)
router = APIRouter()

# ============================================================================
# Request/Response Models
# ============================================================================


class SpecialistInsight(BaseModel):
    """Insight from a specialist agent"""

    # sleep, nutrition, metabolic, cardiovascular, mental_health, movement, endocrine
    specialist: str
    findings: List[str]
    concerns: List[str]
    recommendations: List[str]
    confidence: float  # 0-1
    data_quality: float  # 0-1
    citations: List[str]  # Research references


class CrossSystemPattern(BaseModel):
    """Pattern detected across multiple systems"""

    pattern_type: str  # causal_chain, feedback_loop, synergistic, antagonistic
    systems_involved: List[str]
    description: str
    confidence: float
    impact_score: float  # 0-1, how significant this pattern is


class EvidenceBasedRecommendation(BaseModel):
    """Recommendation with evidence and predicted outcome"""

    priority: int  # 1 = highest
    intervention: str
    rationale: str
    evidence_citations: List[str]
    predicted_outcome: str
    timeline: str  # e.g., "within 10 days"
    success_probability: float  # 0-1


class MetaAnalysisReport(BaseModel):
    """Comprehensive meta-analysis from all specialist agents"""

    report_id: str
    generated_at: str
    analysis_period_days: int

    # Specialist insights
    specialist_insights: List[SpecialistInsight]

    # Integration agent synthesis
    primary_diagnosis: str
    secondary_diagnoses: List[str]
    cross_system_patterns: List[CrossSystemPattern]
    root_cause_analysis: str

    # Recommendations
    recommended_protocol: List[EvidenceBasedRecommendation]

    # Overall assessment
    overall_health_score: float  # 0-100
    confidence_level: str  # high, medium, low
    data_completeness: float  # 0-1


# ============================================================================
# Specialist Agent Prompts
# ============================================================================

SLEEP_AGENT_PROMPT = """You are a Sleep Specialist Agent analyzing sleep health data.

Analyze the following sleep data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Sleep architecture assessment (deep, REM, light sleep phases)
2. Sleep efficiency and consistency
3. Circadian rhythm alignment
4. Recovery quality
5. Any concerning patterns or deficits

Identify root causes for any issues and provide evidence-based recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [bullet list with citations]
CONFIDENCE: [0-1 score]
"""

NUTRITION_AGENT_PROMPT = """You are a Nutrition Specialist Agent analyzing dietary data.

Analyze the following nutrition data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Macronutrient balance (protein, carbs, fats)
2. Micronutrient adequacy (vitamins, minerals)
3. Meal timing and frequency
4. Food quality and variety
5. Any deficiencies or excesses

Identify nutritional gaps and provide evidence-based recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [bullet list with citations]
CONFIDENCE: [0-1 score]
"""

METABOLIC_AGENT_PROMPT = """You are a Metabolic Specialist Agent analyzing metabolic health.

Analyze the following metabolic data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Glucose regulation patterns
2. Inflammation markers (CRP, temperature deviation)
3. Energy metabolism indicators
4. Metabolic stress signals
5. Insulin sensitivity indicators (if available)

Identify metabolic dysregulation and provide evidence-based recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [bullet list with citations]
CONFIDENCE: [0-1 score]
"""

CARDIOVASCULAR_AGENT_PROMPT = """You are a Cardiovascular Specialist Agent analyzing heart health.

Analyze the following cardiovascular data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Heart rate variability (HRV) trends
2. Resting heart rate patterns
3. Blood pressure trends (if available)
4. Cardiovascular stress indicators
5. Autonomic nervous system balance

Identify cardiovascular concerns and provide evidence-based recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [bullet list with citations]
CONFIDENCE: [0-1 score]
"""

MENTAL_HEALTH_AGENT_PROMPT = """You are a Mental Health Specialist Agent \
analyzing psychological wellbeing.

Analyze the following mental health data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Mood patterns and stability
2. Stress levels and stress response
3. Anxiety indicators
4. Cognitive function markers
5. Emotional resilience

Identify mental health concerns and provide evidence-based recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [bullet list with citations]
CONFIDENCE: [0-1 score]
"""

MOVEMENT_AGENT_PROMPT = """You are a Movement Specialist Agent analyzing physical activity.

Analyze the following movement/activity data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Activity volume and intensity patterns
2. Recovery adequacy between sessions
3. Overtraining or undertraining indicators
4. Movement quality and consistency
5. Active vs sedentary time balance

Identify activity concerns and provide evidence-based recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [bullet list with citations]
CONFIDENCE: [0-1 score]
"""

INTEGRATION_AGENT_PROMPT = """You are the Integration Agent (Orchestrator) \
synthesizing insights from all specialist agents.

Specialist Reports:
{specialist_reports}

Cross-Domain Correlation Data:
{correlation_data}

Your task is to:
1. Identify PRIMARY diagnosis - the root cause linking multiple systems
2. Identify SECONDARY diagnoses - contributing factors
3. Detect cross-system patterns (causal chains, feedback loops, synergistic effects)
4. Generate evidence-based protocol prioritized by impact
5. Provide predicted outcomes with success probabilities

Use the format:
PRIMARY DIAGNOSIS: [causal chain linking multiple systems]
SECONDARY DIAGNOSES: [bullet list]
CROSS-SYSTEM PATTERNS: [detailed analysis]
RECOMMENDED PROTOCOL: [prioritized interventions with evidence]
CONFIDENCE: [HIGH/MEDIUM/LOW]
"""


# ============================================================================
# Helper Functions
# ============================================================================


async def _gather_sleep_data(user_id: str, days: int, supabase) -> Dict[str, Any]:
    """Gather sleep data for analysis"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    sleep_result = (
        supabase.table("oura_sleep")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", start_date.date().isoformat())
        .order("date")
        .execute()
    )

    sleep_data = sleep_result.data if sleep_result.data else []

    if not sleep_data:
        return {"available": False}

    # Calculate averages and trends
    avg_sleep_score = sum(s.get("sleep_score", 0) for s in sleep_data) / len(sleep_data)
    avg_deep_sleep = (
        sum(s.get("deep_sleep_duration", 0) for s in sleep_data) / len(sleep_data) / 60
    )  # minutes
    avg_rem_sleep = (
        sum(s.get("rem_sleep_duration", 0) for s in sleep_data) / len(sleep_data) / 60
    )
    avg_efficiency = sum(s.get("sleep_efficiency", 0) for s in sleep_data) / len(
        sleep_data
    )

    return {
        "available": True,
        "days_analyzed": len(sleep_data),
        "avg_sleep_score": round(avg_sleep_score, 1),
        "avg_deep_sleep_min": round(avg_deep_sleep, 1),
        "avg_rem_sleep_min": round(avg_rem_sleep, 1),
        "avg_efficiency": round(avg_efficiency, 1),
        "baseline_deep_sleep": 75,  # Could be personalized
        "baseline_rem_sleep": 90,
    }


async def _gather_nutrition_data(  # pylint: disable=too-many-locals
    user_id: str, days: int, supabase
) -> Dict[str, Any]:
    """Gather nutrition data for analysis"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    meals_result = (
        supabase.table("meal_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("timestamp", start_date.isoformat())
        .execute()
    )

    meals = meals_result.data if meals_result.data else []

    if not meals:
        return {"available": False}

    # Aggregate by day
    daily_totals = {}
    for meal in meals:
        meal_date = meal.get("timestamp", "")[:10]
        if meal_date not in daily_totals:
            daily_totals[meal_date] = {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0,
                "fiber": 0,
                "sugar": 0,
            }
        daily_totals[meal_date]["calories"] += meal.get("total_calories", 0)
        daily_totals[meal_date]["protein"] += meal.get("total_protein_g", 0)
        daily_totals[meal_date]["carbs"] += meal.get("total_carbs_g", 0)
        daily_totals[meal_date]["fat"] += meal.get("total_fat_g", 0)
        daily_totals[meal_date]["fiber"] += meal.get("total_fiber_g", 0)
        daily_totals[meal_date]["sugar"] += meal.get("total_sugar_g", 0)

    num_days = len(daily_totals)
    avg_calories = sum(d["calories"] for d in daily_totals.values()) / num_days
    avg_protein = sum(d["protein"] for d in daily_totals.values()) / num_days
    avg_carbs = sum(d["carbs"] for d in daily_totals.values()) / num_days
    avg_fat = sum(d["fat"] for d in daily_totals.values()) / num_days
    avg_fiber = sum(d["fiber"] for d in daily_totals.values()) / num_days

    return {
        "available": True,
        "days_analyzed": num_days,
        "avg_calories": round(avg_calories, 1),
        "avg_protein_g": round(avg_protein, 1),
        "avg_carbs_g": round(avg_carbs, 1),
        "avg_fat_g": round(avg_fat, 1),
        "avg_fiber_g": round(avg_fiber, 1),
        "protein_percent": round(
            (avg_protein * 4 / avg_calories * 100) if avg_calories > 0 else 0, 1
        ),
        "carb_percent": round(
            (avg_carbs * 4 / avg_calories * 100) if avg_calories > 0 else 0, 1
        ),
        "fat_percent": round(
            (avg_fat * 9 / avg_calories * 100) if avg_calories > 0 else 0, 1
        ),
    }


async def _gather_cardiovascular_data(
    user_id: str, days: int, supabase
) -> Dict[str, Any]:
    """Gather cardiovascular data for analysis"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    readiness_result = (
        supabase.table("oura_readiness")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", start_date.date().isoformat())
        .order("date")
        .execute()
    )

    readiness_data = readiness_result.data if readiness_result.data else []

    if not readiness_data:
        return {"available": False}

    avg_hrv = sum(r.get("hrv_balance", 0) for r in readiness_data) / len(readiness_data)
    avg_rhr = sum(r.get("resting_heart_rate", 0) for r in readiness_data) / len(
        readiness_data
    )
    avg_recovery = sum(r.get("recovery_index", 0) for r in readiness_data) / len(
        readiness_data
    )

    return {
        "available": True,
        "days_analyzed": len(readiness_data),
        "avg_hrv_balance": round(avg_hrv, 1),
        "avg_resting_hr": round(avg_rhr, 1),
        "avg_recovery_index": round(avg_recovery, 1),
    }


async def _gather_activity_data(user_id: str, days: int, supabase) -> Dict[str, Any]:
    """Gather activity/movement data for analysis"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    activity_result = (
        supabase.table("oura_activity")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", start_date.date().isoformat())
        .order("date")
        .execute()
    )

    activity_data = activity_result.data if activity_result.data else []

    if not activity_data:
        return {"available": False}

    avg_steps = sum(a.get("steps", 0) for a in activity_data) / len(activity_data)
    avg_activity_score = sum(a.get("activity_score", 0) for a in activity_data) / len(
        activity_data
    )
    avg_high_activity = sum(
        a.get("high_activity_time", 0) for a in activity_data
    ) / len(activity_data)

    return {
        "available": True,
        "days_analyzed": len(activity_data),
        "avg_steps": round(avg_steps, 0),
        "avg_activity_score": round(avg_activity_score, 1),
        "avg_high_activity_min": round(avg_high_activity / 60, 1),
    }


async def _gather_symptom_data(user_id: str, days: int, supabase) -> Dict[str, Any]:
    """Gather symptom/mental health data for analysis"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    symptoms_result = (
        supabase.table("symptom_journal")
        .select("*")
        .eq("user_id", user_id)
        .gte("symptom_date", start_date.date().isoformat())
        .execute()
    )

    symptoms = symptoms_result.data if symptoms_result.data else []

    if not symptoms:
        return {"available": False}

    # Count by type
    symptom_counts: Dict[str, int] = {}
    mood_counts: Dict[str, int] = {}
    stress_levels = []

    for symptom in symptoms:
        stype = symptom.get("symptom_type", "unknown")
        symptom_counts[stype] = symptom_counts.get(stype, 0) + 1

        mood = symptom.get("mood")
        if mood:
            mood_counts[mood] = mood_counts.get(mood, 0) + 1

        stress = symptom.get("stress_level")
        if stress is not None:
            stress_levels.append(stress)

    avg_stress = sum(stress_levels) / len(stress_levels) if stress_levels else 0

    return {
        "available": True,
        "days_analyzed": days,
        "total_symptoms": len(symptoms),
        "symptom_types": symptom_counts,
        "mood_distribution": mood_counts,
        "avg_stress_level": round(avg_stress, 1),
    }


async def _call_specialist_agent(  # pylint: disable=too-many-locals
    specialist_name: str,
    prompt_template: str,
    data_summary: Dict[str, Any],
    openai_client,
) -> SpecialistInsight:
    """Call a specialist agent and parse response"""

    prompt = prompt_template.format(data_summary=str(data_summary))

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical specialist providing evidence-based analysis.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content

        # Parse the structured response
        findings = []
        concerns = []
        recommendations = []
        confidence = 0.8
        citations = []

        if "FINDINGS:" in content:
            findings_section = (
                content.split("FINDINGS:")[1].split("CONCERNS:")[0].strip()
            )
            findings = [
                f.strip("- ").strip() for f in findings_section.split("\n") if f.strip()
            ]

        if "CONCERNS:" in content:
            concerns_section = (
                content.split("CONCERNS:")[1].split("RECOMMENDATIONS:")[0].strip()
            )
            concerns = [
                c.strip("- ").strip() for c in concerns_section.split("\n") if c.strip()
            ]

        if "RECOMMENDATIONS:" in content:
            recs_section = (
                content.split("RECOMMENDATIONS:")[1].split("CONFIDENCE:")[0].strip()
            )
            recommendations = [
                r.strip("- ").strip() for r in recs_section.split("\n") if r.strip()
            ]

            # Extract citations from recommendations
            for rec in recommendations:
                if "[" in rec and "]" in rec:
                    citation = rec[rec.find("[") : rec.find("]") + 1]
                    citations.append(citation)

        if "CONFIDENCE:" in content:
            try:
                confidence_str = content.split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(confidence_str)
            except (ValueError, IndexError):
                confidence = 0.7

        return SpecialistInsight(
            specialist=specialist_name,
            findings=findings,
            concerns=concerns,
            recommendations=recommendations,
            confidence=confidence,
            data_quality=0.8 if data_summary.get("available") else 0.0,
            citations=citations,
        )

    except Exception as err:  # pylint: disable=broad-except
        logger.error(f"Error calling {specialist_name} agent: {err}")
        return SpecialistInsight(
            specialist=specialist_name,
            findings=[],
            concerns=[f"Error analyzing {specialist_name} data"],
            recommendations=[],
            confidence=0.0,
            data_quality=0.0,
            citations=[],
        )


async def _call_integration_agent(
    specialist_insights: List[SpecialistInsight],
    correlation_data: str,
    openai_client,
) -> Dict[str, Any]:
    """Call the integration agent to synthesize all specialist insights"""

    specialist_reports = "\n\n".join(
        [
            f"{insight.specialist.upper()} AGENT:\n"
            f"Findings: {', '.join(insight.findings)}\n"
            f"Concerns: {', '.join(insight.concerns)}\n"
            f"Recommendations: {', '.join(insight.recommendations)}\n"
            f"Confidence: {insight.confidence}"
            for insight in specialist_insights
        ]
    )

    prompt = INTEGRATION_AGENT_PROMPT.format(
        specialist_reports=specialist_reports, correlation_data=correlation_data
    )

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Integration Agent synthesizing specialist "
                        "insights into holistic diagnosis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content

        # Parse response
        primary_diagnosis = ""
        secondary_diagnoses = []
        recommended_protocol = []
        confidence_level = "medium"

        if "PRIMARY DIAGNOSIS:" in content:
            primary_diagnosis = (
                content.split("PRIMARY DIAGNOSIS:")[1].split("SECONDARY")[0].strip()
            )

        if "SECONDARY DIAGNOSES:" in content:
            secondary_section = (
                content.split("SECONDARY DIAGNOSES:")[1]
                .split("CROSS-SYSTEM")[0]
                .strip()
            )
            secondary_diagnoses = [
                s.strip("- ").strip()
                for s in secondary_section.split("\n")
                if s.strip()
            ]

        if "RECOMMENDED PROTOCOL:" in content:
            protocol_section = (
                content.split("RECOMMENDED PROTOCOL:")[1]
                .split("CONFIDENCE:")[0]
                .strip()
            )
            recommended_protocol = [
                p.strip("- ").strip() for p in protocol_section.split("\n") if p.strip()
            ]

        if "CONFIDENCE:" in content:
            confidence_section = content.split("CONFIDENCE:")[1].strip().split()[0]
            confidence_level = confidence_section.lower()

        return {
            "primary_diagnosis": primary_diagnosis,
            "secondary_diagnoses": secondary_diagnoses,
            "recommended_protocol": recommended_protocol,
            "confidence_level": confidence_level,
            "raw_synthesis": content,
        }

    except Exception as err:  # pylint: disable=broad-except
        logger.error(f"Error calling integration agent: {err}")
        return {
            "primary_diagnosis": "Unable to generate synthesis",
            "secondary_diagnoses": [],
            "recommended_protocol": [],
            "confidence_level": "low",
            "raw_synthesis": "",
        }


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/specialist-agents/meta-analysis",
    response_model=MetaAnalysisReport,
    dependencies=[Depends(UsageGate("ai_agents"))],
)
async def generate_meta_analysis(  # pylint: disable=too-many-locals
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate comprehensive meta-analysis report from all specialist agents
    Pro+ feature
    """
    try:
        supabase = get_supabase_client()
        openai_client = get_openai_client()
        user_id = current_user["sub"]

        # Gather data for all specialists
        sleep_data = await _gather_sleep_data(user_id, days, supabase)
        nutrition_data = await _gather_nutrition_data(user_id, days, supabase)
        cardiovascular_data = await _gather_cardiovascular_data(user_id, days, supabase)
        activity_data = await _gather_activity_data(user_id, days, supabase)
        symptom_data = await _gather_symptom_data(user_id, days, supabase)

        # Call specialist agents
        specialist_insights = []

        if sleep_data.get("available"):
            sleep_insight = await _call_specialist_agent(
                "sleep", SLEEP_AGENT_PROMPT, sleep_data, openai_client
            )
            specialist_insights.append(sleep_insight)

        if nutrition_data.get("available"):
            nutrition_insight = await _call_specialist_agent(
                "nutrition", NUTRITION_AGENT_PROMPT, nutrition_data, openai_client
            )
            specialist_insights.append(nutrition_insight)

        if cardiovascular_data.get("available"):
            cardio_insight = await _call_specialist_agent(
                "cardiovascular",
                CARDIOVASCULAR_AGENT_PROMPT,
                cardiovascular_data,
                openai_client,
            )
            specialist_insights.append(cardio_insight)

        if activity_data.get("available"):
            movement_insight = await _call_specialist_agent(
                "movement", MOVEMENT_AGENT_PROMPT, activity_data, openai_client
            )
            specialist_insights.append(movement_insight)

        if symptom_data.get("available"):
            mental_health_insight = await _call_specialist_agent(
                "mental_health",
                MENTAL_HEALTH_AGENT_PROMPT,
                symptom_data,
                openai_client,
            )
            specialist_insights.append(mental_health_insight)

        # Get correlation data summary
        correlation_summary = (
            f"Sleep avg: {sleep_data.get('avg_sleep_score', 'N/A')}, "
            f"Nutrition avg calories: {nutrition_data.get('avg_calories', 'N/A')}, "
            f"HRV: {cardiovascular_data.get('avg_hrv_balance', 'N/A')}"
        )

        # Call integration agent
        integration_result = await _call_integration_agent(
            specialist_insights, correlation_summary, openai_client
        )

        # Build recommendations
        recommended_protocol = []
        for idx, rec_text in enumerate(
            integration_result.get("recommended_protocol", [])[:5]
        ):
            recommended_protocol.append(
                EvidenceBasedRecommendation(
                    priority=idx + 1,
                    intervention=rec_text.split("[")[0].strip(),
                    rationale="Based on specialist analysis",
                    evidence_citations=[
                        rec_text[rec_text.find("[") : rec_text.find("]") + 1]
                    ]
                    if "[" in rec_text
                    else [],
                    predicted_outcome="Improvement expected",
                    timeline="within 10-14 days",
                    success_probability=0.7,
                )
            )

        # Calculate overall health score
        avg_confidence = (
            sum(s.confidence for s in specialist_insights) / len(specialist_insights)
            if specialist_insights
            else 0.5
        )
        overall_score = avg_confidence * 100

        report = MetaAnalysisReport(
            report_id=f"meta-{user_id}-{datetime.utcnow().timestamp()}",
            generated_at=datetime.utcnow().isoformat(),
            analysis_period_days=days,
            specialist_insights=specialist_insights,
            primary_diagnosis=integration_result.get("primary_diagnosis", ""),
            secondary_diagnoses=integration_result.get("secondary_diagnoses", []),
            cross_system_patterns=[],
            root_cause_analysis=integration_result.get("raw_synthesis", ""),
            recommended_protocol=recommended_protocol,
            overall_health_score=overall_score,
            confidence_level=integration_result.get("confidence_level", "medium"),
            data_completeness=len(specialist_insights) / 7.0,
        )

        return report

    except Exception as err:
        logger.error(f"Error generating meta-analysis: {err}")
        raise HTTPException(status_code=500, detail=str(err)) from err
