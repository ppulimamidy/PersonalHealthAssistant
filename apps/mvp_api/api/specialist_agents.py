"""
Specialist Multi-Agent System
Domain-specific expert agents with orchestrator for holistic health analysis
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,import-outside-toplevel,too-few-public-methods,missing-class-docstring,invalid-name

import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel  # pylint: disable=too-few-public-methods

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import UsageGate, _supabase_get

logger = get_logger(__name__)
router = APIRouter()

# ============================================================================
# Request/Response Models
# ============================================================================


class PrimaryDiagnosis(BaseModel):
    """Structured primary diagnosis from integration agent"""

    diagnosis: str
    systems_involved: List[str]
    confidence: float  # 0-1
    causal_chain: List[str]


class SecondaryDiagnosis(BaseModel):
    """Structured secondary diagnosis"""

    diagnosis: str
    systems_involved: List[str]
    confidence: float  # 0-1


class EvidenceBasedRecommendation(BaseModel):
    """Recommendation with structured evidence fields matching TypeScript interface"""

    action: str
    rationale: str
    priority: str  # 'critical'|'high'|'medium'|'low'
    evidence_level: str  # 'strong'|'moderate'|'limited'|'theoretical'
    citations: List[str]
    expected_benefit: str
    implementation_difficulty: str  # 'easy'|'moderate'|'difficult'
    estimated_impact: float  # 0-1


class CrossSystemPattern(BaseModel):
    """Pattern detected across multiple systems"""

    pattern_type: str  # 'causal_chain'|'feedback_loop'|'synergistic_effect'|'antagonistic_interaction'
    systems_involved: List[str]
    pattern_description: str
    clinical_significance: str
    strength: str  # 'strong'|'moderate'|'weak'


class PredictedOutcome(BaseModel):
    """Predicted health outcome from intervention"""

    metric: str
    current_value: float
    predicted_value: float
    timeframe_days: int
    success_probability: float
    confidence_interval: Dict[str, float]  # {"lower": x, "upper": y}


class SpecialistInsight(BaseModel):
    """Insight from a specialist agent"""

    specialist_name: str  # sleep, nutrition, cardiovascular, movement, mental_health
    findings: List[str]
    concerns: List[str]
    recommendations: List[EvidenceBasedRecommendation]
    confidence_score: float  # 0-1
    data_quality: float  # 0-1


class MetaAnalysisReport(BaseModel):
    """Comprehensive meta-analysis from all specialist agents — matches TypeScript interface"""

    report_id: str
    user_id: str
    generated_at: str
    analysis_period_days: int

    # Specialist insights
    specialist_insights: List[SpecialistInsight]

    # Integration agent synthesis
    primary_diagnosis: PrimaryDiagnosis
    secondary_diagnoses: List[SecondaryDiagnosis]
    cross_system_patterns: List[CrossSystemPattern]

    # Recommendations & outcomes
    recommended_protocol: List[EvidenceBasedRecommendation]
    predicted_outcomes: List[PredictedOutcome]

    # Quality metrics
    overall_confidence: float  # 0-1
    data_completeness: float  # 0-1
    evidence_quality: str  # high, medium, low


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
RECOMMENDATIONS: [one recommendation per line in this exact format]
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
CONFIDENCE: [0-1 score]
"""

NUTRITION_AGENT_PROMPT = """You are a Nutrition Specialist Agent analyzing dietary data.

USER PREFERENCES (personalise your analysis accordingly):
{user_preferences}

Analyze the following nutrition data and provide insights:

Data Summary:
{data_summary}

Your analysis should include:
1. Macronutrient balance vs. the user's goals (protein, carbs, fats)
2. Micronutrient adequacy (vitamins, minerals)
3. Meal timing and frequency relative to their stated meal timing preference
4. Food quality and variety — flag any allergens or restriction violations found in the data
5. Any deficiencies or excesses relative to their personal targets

Identify nutritional gaps and provide evidence-based, personalised recommendations.
Format your response as:
FINDINGS: [bullet list]
CONCERNS: [bullet list]
RECOMMENDATIONS: [one recommendation per line in this exact format]
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
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
RECOMMENDATIONS: [one recommendation per line in this exact format]
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
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
RECOMMENDATIONS: [one recommendation per line in this exact format]
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
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
RECOMMENDATIONS: [one recommendation per line in this exact format]
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
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
RECOMMENDATIONS: [one recommendation per line in this exact format]
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
CONFIDENCE: [0-1 score]
"""

INTEGRATION_AGENT_PROMPT = """You are the Integration Agent (Orchestrator) \
synthesizing insights from all specialist agents.

Specialist Reports:
{specialist_reports}

Cross-Domain Correlation Data:
{correlation_data}

Your task is to:
1. Identify PRIMARY diagnosis — the root cause linking multiple systems
2. Identify SECONDARY diagnoses — contributing factors
3. Detect cross-system patterns (causal chains, feedback loops, synergistic effects)
4. Generate evidence-based protocol prioritized by impact
5. Provide predicted outcomes with success probabilities

Use EXACTLY this format (all sections required):

PRIMARY DIAGNOSIS: [root cause in plain English]
PRIMARY SYSTEMS: [comma-separated systems involved, e.g. sleep,cardiovascular,metabolic]
PRIMARY CAUSAL CHAIN: [step1 | step2 | step3]
PRIMARY CONFIDENCE: [0.0-1.0]
SECONDARY DIAGNOSES:
- [diagnosis text] | systems: [sys1,sys2] | confidence: [0.0-1.0]
CROSS-SYSTEM PATTERNS:
- TYPE:[causal_chain|feedback_loop|synergistic_effect|antagonistic_interaction] SYSTEMS:[s1,s2] DESC:[description] STRENGTH:[strong|moderate|weak] CLINICAL:[clinical significance]
PREDICTED OUTCOMES:
- METRIC:[metric name] CURRENT:[numeric value] PREDICTED:[numeric value] DAYS:[integer] PROB:[0.0-1.0]
RECOMMENDED PROTOCOL:
- ACTION: [concise action] | PRIORITY: critical/high/medium/low | EVIDENCE: strong/moderate/limited/theoretical | BENEFIT: [expected benefit] | DIFFICULTY: easy/moderate/difficult | IMPACT: [0.0-1.0]
CONFIDENCE: [HIGH/MEDIUM/LOW]
"""


# ============================================================================
# Helper Functions
# ============================================================================


# ── In-memory report cache (keyed by user_id) ──────────────────────────────

_report_cache: Dict[str, Any] = {}


# ── Recommendation parser ───────────────────────────────────────────────────


def _parse_recommendation(line: str) -> EvidenceBasedRecommendation:
    """Parse a structured recommendation line into EvidenceBasedRecommendation.

    Expected format:
        - ACTION: x | PRIORITY: high | EVIDENCE: moderate | BENEFIT: y | DIFFICULTY: easy | IMPACT: 0.7
    Falls back to sensible defaults if format is not matched.
    """
    line = line.strip().lstrip("- ").strip()

    action = line
    rationale = "Based on specialist analysis"
    priority = "medium"
    evidence_level = "moderate"
    citations: List[str] = []
    expected_benefit = ""
    implementation_difficulty = "moderate"
    estimated_impact = 0.5

    if "ACTION:" in line and "|" in line:
        parts: Dict[str, str] = {}
        for segment in line.split("|"):
            if ":" in segment:
                key, _, value = segment.partition(":")
                parts[key.strip().upper()] = value.strip()
        action = parts.get("ACTION", action)
        priority = parts.get("PRIORITY", priority).lower()
        evidence_level = parts.get("EVIDENCE", evidence_level).lower()
        expected_benefit = parts.get("BENEFIT", expected_benefit)
        implementation_difficulty = parts.get("DIFFICULTY", implementation_difficulty).lower()
        try:
            estimated_impact = float(parts.get("IMPACT", "0.5"))
        except ValueError:
            estimated_impact = 0.5

    # Extract bracket citations from action text
    bracket_citations = re.findall(r"\[([^\]]+)\]", action)
    if bracket_citations:
        citations = bracket_citations
        action = re.sub(r"\s*\[[^\]]+\]", "", action).strip()

    # Validate enum values, coerce to nearest valid option
    _valid_priorities = {"critical", "high", "medium", "low"}
    _valid_evidence = {"strong", "moderate", "limited", "theoretical"}
    _valid_difficulties = {"easy", "moderate", "difficult"}

    if priority not in _valid_priorities:
        priority = "medium"
    if evidence_level not in _valid_evidence:
        evidence_level = "moderate"
    if implementation_difficulty not in _valid_difficulties:
        implementation_difficulty = "moderate"

    return EvidenceBasedRecommendation(
        action=action or line,
        rationale=rationale,
        priority=priority,
        evidence_level=evidence_level,
        citations=citations,
        expected_benefit=expected_benefit,
        implementation_difficulty=implementation_difficulty,
        estimated_impact=max(0.0, min(1.0, estimated_impact)),
    )


async def _gather_sleep_data(user_id: str, days: int) -> Dict[str, Any]:
    """Gather sleep data for analysis"""
    start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    sleep_data = (
        await _supabase_get(
            "oura_sleep",
            f"user_id=eq.{user_id}&date=gte.{start_date}&select=sleep_score,deep_sleep_duration,rem_sleep_duration,sleep_efficiency&order=date.asc",
        )
        or []
    )

    if not sleep_data:
        return {"available": False}

    avg_sleep_score = sum(s.get("sleep_score", 0) for s in sleep_data) / len(sleep_data)
    avg_deep_sleep = (
        sum(s.get("deep_sleep_duration", 0) for s in sleep_data) / len(sleep_data) / 60
    )
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
        "baseline_deep_sleep": 75,
        "baseline_rem_sleep": 90,
    }


def _fmt_pref(value) -> str:
    """Format a preference value for display in a prompt."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "none"
    return str(value) if value else "not specified"


def _build_preferences_summary(prefs: Dict[str, Any]) -> str:
    """Build a human-readable preferences summary for the nutrition agent prompt."""
    if not prefs:
        return "No user preferences on file."
    lines = [
        f"- Goals: {_fmt_pref(prefs.get('goals'))}",
        f"- Allergies (strict): {_fmt_pref(prefs.get('allergies'))}",
        f"- Dietary restrictions: {_fmt_pref(prefs.get('dietary_restrictions'))}",
        f"- Dislikes: {_fmt_pref(prefs.get('dislikes'))}",
        f"- Favourite foods/cuisines: {_fmt_pref(prefs.get('food_preferences'))} / "
        f"{_fmt_pref(prefs.get('cuisine_preferences'))}",
        f"- Health conditions: {_fmt_pref(prefs.get('health_conditions'))}",
        f"- Meal timing: {_fmt_pref(prefs.get('meal_timing'))}",
        f"- Cooking skill: {_fmt_pref(prefs.get('cooking_skill'))}",
        f"- Budget: {_fmt_pref(prefs.get('budget'))}",
    ]
    if prefs.get("notes"):
        lines.append(f"- Notes: {prefs['notes']}")
    return "\n".join(lines)


async def _gather_nutrition_data(  # pylint: disable=too-many-locals
    user_id: str, days: int
) -> Dict[str, Any]:
    """Gather nutrition data and user preferences for analysis."""
    start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

    meals = (
        await _supabase_get(
            "meal_logs",
            f"user_id=eq.{user_id}&timestamp=gte.{start_date}&select=timestamp,total_calories,total_protein_g,total_carbs_g,total_fat_g,total_fiber_g",
        )
        or []
    )

    # Fetch user preferences from the nutrition analyst prefs table
    user_prefs: Dict[str, Any] = {}
    try:
        prefs_rows = await _supabase_get(
            "nutrition_analyst_prefs",
            f"user_id=eq.{user_id}&select=preferences&limit=1",
        )
        if prefs_rows:
            user_prefs = prefs_rows[0].get("preferences") or {}
    except Exception:  # pylint: disable=broad-except
        pass

    if not meals:
        return {"available": False, "user_preferences": user_prefs}

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
        "user_preferences": user_prefs,
    }


async def _gather_cardiovascular_data(user_id: str, days: int) -> Dict[str, Any]:
    """Gather cardiovascular data for analysis"""
    start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    readiness_data = (
        await _supabase_get(
            "oura_readiness",
            f"user_id=eq.{user_id}&date=gte.{start_date}&select=hrv_balance,resting_heart_rate,recovery_index&order=date.asc",
        )
        or []
    )

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


async def _gather_activity_data(user_id: str, days: int) -> Dict[str, Any]:
    """Gather activity/movement data for analysis"""
    start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    activity_data = (
        await _supabase_get(
            "oura_activity",
            f"user_id=eq.{user_id}&date=gte.{start_date}&select=steps,activity_score,high_activity_time&order=date.asc",
        )
        or []
    )

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


async def _gather_symptom_data(user_id: str, days: int) -> Dict[str, Any]:
    """Gather symptom/mental health data for analysis"""
    start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    symptoms = (
        await _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{start_date}&select=symptom_type,mood,stress_level",
        )
        or []
    )

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
    anthropic_client,
) -> SpecialistInsight:
    """Call a specialist agent and parse response"""

    prompt = prompt_template.format(data_summary=str(data_summary))

    try:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            system="You are a medical specialist providing evidence-based analysis.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

        content = response.content[0].text

        # Parse the structured response
        findings = []
        concerns = []
        recommendations: List[EvidenceBasedRecommendation] = []
        confidence = 0.8

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
            raw_recs = [r.strip() for r in recs_section.split("\n") if r.strip()]
            recommendations = [_parse_recommendation(r) for r in raw_recs]

        if "CONFIDENCE:" in content:
            try:
                confidence_str = content.split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(confidence_str)
            except (ValueError, IndexError):
                confidence = 0.7

        return SpecialistInsight(
            specialist_name=specialist_name,
            findings=findings,
            concerns=concerns,
            recommendations=recommendations,
            confidence_score=confidence,
            data_quality=0.8 if data_summary.get("available") else 0.0,
        )

    except Exception as err:  # pylint: disable=broad-except
        logger.error(f"Error calling {specialist_name} agent: {err}")
        return SpecialistInsight(
            specialist_name=specialist_name,
            findings=[],
            concerns=[f"Error analyzing {specialist_name} data"],
            recommendations=[],
            confidence_score=0.0,
            data_quality=0.0,
        )


def _parse_section(content: str, start_marker: str, end_markers: List[str]) -> str:
    """Extract a section from agent output between markers."""
    if start_marker not in content:
        return ""
    section = content.split(start_marker)[1]
    for end in end_markers:
        if end in section:
            section = section.split(end)[0]
    return section.strip()


def _parse_secondary_diagnoses(section: str) -> List[Dict[str, Any]]:
    """Parse secondary diagnoses section into list of dicts."""
    results = []
    for line in section.split("\n"):
        line = line.strip("- ").strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        diagnosis_text = parts[0] if parts else line
        systems_involved: List[str] = []
        confidence = 0.6
        for part in parts[1:]:
            part_lower = part.lower()
            if part_lower.startswith("systems:"):
                systems_involved = [s.strip() for s in part.split(":", 1)[1].split(",") if s.strip()]
            elif part_lower.startswith("confidence:"):
                try:
                    confidence = float(part.split(":", 1)[1].strip())
                except ValueError:
                    confidence = 0.6
        if diagnosis_text:
            results.append({
                "diagnosis": diagnosis_text,
                "systems_involved": systems_involved,
                "confidence": confidence,
            })
    return results


def _parse_cross_system_patterns(section: str) -> List[Dict[str, Any]]:
    """Parse cross-system patterns section into list of dicts."""
    results = []
    valid_types = {"causal_chain", "feedback_loop", "synergistic_effect", "antagonistic_interaction"}
    valid_strengths = {"strong", "moderate", "weak"}
    for line in section.split("\n"):
        line = line.strip("- ").strip()
        if not line or "TYPE:" not in line:
            continue
        fields: Dict[str, str] = {}
        for key in ["TYPE", "SYSTEMS", "DESC", "STRENGTH", "CLINICAL"]:
            marker = f"{key}:"
            if marker in line:
                after = line.split(marker, 1)[1]
                # Value ends at next marker or end of line
                for other_key in ["TYPE", "SYSTEMS", "DESC", "STRENGTH", "CLINICAL"]:
                    if other_key != key and f" {other_key}:" in after:
                        after = after.split(f" {other_key}:")[0]
                fields[key] = after.strip()
        pattern_type = fields.get("TYPE", "causal_chain").lower().replace(" ", "_")
        if pattern_type not in valid_types:
            pattern_type = "causal_chain"
        systems_str = fields.get("SYSTEMS", "")
        systems_involved = [s.strip() for s in systems_str.split(",") if s.strip()]
        strength = fields.get("STRENGTH", "moderate").lower()
        if strength not in valid_strengths:
            strength = "moderate"
        desc = fields.get("DESC", line)
        clinical = fields.get("CLINICAL", "")
        if desc:
            results.append({
                "pattern_type": pattern_type,
                "systems_involved": systems_involved,
                "pattern_description": desc,
                "clinical_significance": clinical,
                "strength": strength,
            })
    return results


def _parse_predicted_outcomes(section: str) -> List[Dict[str, Any]]:
    """Parse predicted outcomes section into list of dicts."""
    results = []
    for line in section.split("\n"):
        line = line.strip("- ").strip()
        if not line or "METRIC:" not in line:
            continue
        fields: Dict[str, str] = {}
        for key in ["METRIC", "CURRENT", "PREDICTED", "DAYS", "PROB"]:
            marker = f"{key}:"
            if marker in line:
                after = line.split(marker, 1)[1]
                for other_key in ["METRIC", "CURRENT", "PREDICTED", "DAYS", "PROB"]:
                    if other_key != key and f" {other_key}:" in after:
                        after = after.split(f" {other_key}:")[0]
                fields[key] = after.strip()
        try:
            current_val = float(fields.get("CURRENT", "0"))
            predicted_val = float(fields.get("PREDICTED", "0"))
            days = int(float(fields.get("DAYS", "30")))
            prob = float(fields.get("PROB", "0.7"))
        except ValueError:
            continue
        metric = fields.get("METRIC", "")
        if metric:
            margin = abs(predicted_val - current_val) * 0.15
            results.append({
                "metric": metric,
                "current_value": current_val,
                "predicted_value": predicted_val,
                "timeframe_days": days,
                "success_probability": max(0.0, min(1.0, prob)),
                "confidence_interval": {
                    "lower": round(predicted_val - margin, 2),
                    "upper": round(predicted_val + margin, 2),
                },
            })
    return results


async def _call_integration_agent(
    specialist_insights: List[SpecialistInsight],
    correlation_data: str,
    anthropic_client,
) -> Dict[str, Any]:
    """Call the integration agent to synthesize all specialist insights"""

    def _fmt_recs(recs: List[EvidenceBasedRecommendation]) -> str:
        return ", ".join(r.action for r in recs[:3]) if recs else "none"

    specialist_reports = "\n\n".join(
        [
            f"{insight.specialist_name.upper()} AGENT:\n"
            f"Findings: {', '.join(insight.findings)}\n"
            f"Concerns: {', '.join(insight.concerns)}\n"
            f"Recommendations: {_fmt_recs(insight.recommendations)}\n"
            f"Confidence: {insight.confidence_score}"
            for insight in specialist_insights
        ]
    )

    prompt = INTEGRATION_AGENT_PROMPT.format(
        specialist_reports=specialist_reports, correlation_data=correlation_data
    )

    try:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            system=(
                "You are an Integration Agent synthesizing specialist "
                "insights into holistic diagnosis. Follow the output format exactly."
            ),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2500,
        )

        content = response.content[0].text

        # ── Parse primary diagnosis ─────────────────────────────────────────
        all_section_markers = [
            "PRIMARY SYSTEMS:", "PRIMARY CAUSAL CHAIN:", "PRIMARY CONFIDENCE:",
            "SECONDARY DIAGNOSES:", "CROSS-SYSTEM PATTERNS:", "PREDICTED OUTCOMES:",
            "RECOMMENDED PROTOCOL:", "CONFIDENCE:",
        ]

        primary_diagnosis_text = _parse_section(content, "PRIMARY DIAGNOSIS:", all_section_markers)
        primary_systems_str = _parse_section(content, "PRIMARY SYSTEMS:", all_section_markers)
        primary_causal_str = _parse_section(content, "PRIMARY CAUSAL CHAIN:", all_section_markers)
        primary_confidence_str = _parse_section(content, "PRIMARY CONFIDENCE:", all_section_markers)

        primary_systems = [s.strip() for s in primary_systems_str.split(",") if s.strip()]
        primary_causal_chain = [s.strip() for s in primary_causal_str.split("|") if s.strip()]
        try:
            primary_confidence = float(primary_confidence_str.split()[0]) if primary_confidence_str else 0.6
        except (ValueError, IndexError):
            primary_confidence = 0.6

        primary_diagnosis: Dict[str, Any] = {
            "diagnosis": primary_diagnosis_text or "Multiple system dysregulation detected",
            "systems_involved": primary_systems,
            "confidence": primary_confidence,
            "causal_chain": primary_causal_chain,
        }

        # ── Parse secondary diagnoses ───────────────────────────────────────
        secondary_section = _parse_section(
            content, "SECONDARY DIAGNOSES:",
            ["CROSS-SYSTEM PATTERNS:", "PREDICTED OUTCOMES:", "RECOMMENDED PROTOCOL:", "CONFIDENCE:"]
        )
        secondary_diagnoses = _parse_secondary_diagnoses(secondary_section)

        # ── Parse cross-system patterns ─────────────────────────────────────
        patterns_section = _parse_section(
            content, "CROSS-SYSTEM PATTERNS:",
            ["PREDICTED OUTCOMES:", "RECOMMENDED PROTOCOL:", "CONFIDENCE:"]
        )
        cross_system_patterns = _parse_cross_system_patterns(patterns_section)

        # ── Parse predicted outcomes ────────────────────────────────────────
        outcomes_section = _parse_section(
            content, "PREDICTED OUTCOMES:",
            ["RECOMMENDED PROTOCOL:", "CONFIDENCE:"]
        )
        predicted_outcomes = _parse_predicted_outcomes(outcomes_section)

        # ── Parse recommended protocol ──────────────────────────────────────
        protocol_section = _parse_section(
            content, "RECOMMENDED PROTOCOL:", ["CONFIDENCE:"]
        )
        recommended_protocol = [
            _parse_recommendation(line)
            for line in protocol_section.split("\n")
            if line.strip()
        ]

        # ── Parse confidence level ──────────────────────────────────────────
        confidence_level = "medium"
        if "CONFIDENCE:" in content:
            conf_text = content.split("CONFIDENCE:")[-1].strip().split()[0].lower()
            if conf_text in {"high", "medium", "low"}:
                confidence_level = conf_text

        return {
            "primary_diagnosis": primary_diagnosis,
            "secondary_diagnoses": secondary_diagnoses,
            "cross_system_patterns": cross_system_patterns,
            "predicted_outcomes": predicted_outcomes,
            "recommended_protocol": recommended_protocol,
            "confidence_level": confidence_level,
        }

    except Exception as err:  # pylint: disable=broad-except
        logger.error(f"Error calling integration agent: {err}")
        return {
            "primary_diagnosis": {
                "diagnosis": "Unable to generate synthesis",
                "systems_involved": [],
                "confidence": 0.0,
                "causal_chain": [],
            },
            "secondary_diagnoses": [],
            "cross_system_patterns": [],
            "predicted_outcomes": [],
            "recommended_protocol": [],
            "confidence_level": "low",
        }


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/meta-analysis/latest",
    response_model=MetaAnalysisReport,
)
async def get_latest_meta_analysis(
    current_user: dict = Depends(get_current_user),
):
    """Return the most recently generated meta-analysis report for the user (cached in memory)."""
    user_id = current_user["id"]
    if user_id not in _report_cache:
        raise HTTPException(status_code=404, detail="No cached report found. Generate a report first.")
    return _report_cache[user_id]


@router.post(
    "/meta-analysis",
    response_model=MetaAnalysisReport,
    dependencies=[Depends(UsageGate("ai_agents"))],
)
async def generate_meta_analysis(  # pylint: disable=too-many-locals
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate comprehensive meta-analysis report from all specialist agents.
    Pro+ feature. Results are cached in memory per user for instant retrieval.
    """
    try:
        anthropic_client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )
        user_id = current_user["id"]

        # Gather data for all specialists
        sleep_data = await _gather_sleep_data(user_id, days)
        nutrition_data = await _gather_nutrition_data(user_id, days)
        cardiovascular_data = await _gather_cardiovascular_data(user_id, days)
        activity_data = await _gather_activity_data(user_id, days)
        symptom_data = await _gather_symptom_data(user_id, days)

        # Call specialist agents in parallel where data is available
        specialist_insights: List[SpecialistInsight] = []

        if sleep_data.get("available"):
            sleep_insight = await _call_specialist_agent(
                "sleep", SLEEP_AGENT_PROMPT, sleep_data, anthropic_client
            )
            specialist_insights.append(sleep_insight)

        if nutrition_data.get("available"):
            prefs_summary = _build_preferences_summary(
                nutrition_data.get("user_preferences") or {}
            )
            nutrition_prompt = NUTRITION_AGENT_PROMPT.format(
                user_preferences=prefs_summary,
                data_summary="{data_summary}",  # placeholder for _call_specialist_agent
            )
            nutrition_insight = await _call_specialist_agent(
                "nutrition", nutrition_prompt, nutrition_data, anthropic_client
            )
            specialist_insights.append(nutrition_insight)

        if cardiovascular_data.get("available"):
            cardio_insight = await _call_specialist_agent(
                "cardiovascular",
                CARDIOVASCULAR_AGENT_PROMPT,
                cardiovascular_data,
                anthropic_client,
            )
            specialist_insights.append(cardio_insight)

        if activity_data.get("available"):
            movement_insight = await _call_specialist_agent(
                "movement", MOVEMENT_AGENT_PROMPT, activity_data, anthropic_client
            )
            specialist_insights.append(movement_insight)

        if symptom_data.get("available"):
            mental_health_insight = await _call_specialist_agent(
                "mental_health",
                MENTAL_HEALTH_AGENT_PROMPT,
                symptom_data,
                anthropic_client,
            )
            specialist_insights.append(mental_health_insight)

        # Build correlation summary for integration agent context
        correlation_summary = (
            f"Sleep avg score: {sleep_data.get('avg_sleep_score', 'N/A')}, "
            f"Nutrition avg calories: {nutrition_data.get('avg_calories', 'N/A')}, "
            f"HRV balance: {cardiovascular_data.get('avg_hrv_balance', 'N/A')}, "
            f"Avg steps: {activity_data.get('avg_steps', 'N/A')}, "
            f"Symptoms logged: {symptom_data.get('total_symptoms', 'N/A')}"
        )

        # Call integration agent
        integration_result = await _call_integration_agent(
            specialist_insights, correlation_summary, anthropic_client
        )

        # Build primary diagnosis object
        primary_diag_data = integration_result.get("primary_diagnosis", {})
        if isinstance(primary_diag_data, dict):
            primary_diagnosis = PrimaryDiagnosis(**primary_diag_data)
        else:
            primary_diagnosis = PrimaryDiagnosis(
                diagnosis=str(primary_diag_data) or "Analysis incomplete",
                systems_involved=[],
                confidence=0.5,
                causal_chain=[],
            )

        # Build secondary diagnoses
        secondary_diagnoses = []
        for d in integration_result.get("secondary_diagnoses", []):
            if isinstance(d, dict):
                secondary_diagnoses.append(SecondaryDiagnosis(**d))
            else:
                secondary_diagnoses.append(SecondaryDiagnosis(
                    diagnosis=str(d), systems_involved=[], confidence=0.5
                ))

        # Build cross-system patterns
        cross_system_patterns = []
        for p in integration_result.get("cross_system_patterns", []):
            if isinstance(p, dict):
                cross_system_patterns.append(CrossSystemPattern(**p))

        # Build predicted outcomes
        predicted_outcomes = []
        for o in integration_result.get("predicted_outcomes", []):
            if isinstance(o, dict):
                predicted_outcomes.append(PredictedOutcome(**o))

        # Recommended protocol comes already parsed from integration agent
        recommended_protocol: List[EvidenceBasedRecommendation] = integration_result.get(
            "recommended_protocol", []
        )

        # Calculate overall confidence (0-1)
        avg_confidence = (
            sum(s.confidence_score for s in specialist_insights) / len(specialist_insights)
            if specialist_insights
            else 0.5
        )

        report = MetaAnalysisReport(
            report_id=f"meta-{user_id}-{datetime.utcnow().timestamp():.0f}",
            user_id=user_id,
            generated_at=datetime.utcnow().isoformat(),
            analysis_period_days=days,
            specialist_insights=specialist_insights,
            primary_diagnosis=primary_diagnosis,
            secondary_diagnoses=secondary_diagnoses,
            cross_system_patterns=cross_system_patterns,
            recommended_protocol=recommended_protocol,
            predicted_outcomes=predicted_outcomes,
            overall_confidence=round(avg_confidence, 3),
            evidence_quality=integration_result.get("confidence_level", "medium"),
            data_completeness=round(len(specialist_insights) / 7.0, 2),
        )

        # Cache for instant retrieval
        _report_cache[user_id] = report
        return report

    except Exception as err:
        logger.error(f"Error generating meta-analysis: {err}")
        raise HTTPException(status_code=500, detail=str(err)) from err
