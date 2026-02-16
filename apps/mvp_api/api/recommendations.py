"""
Recommendation Engine — AI Recovery Nutrition

Detects metabolic patterns from Oura + nutrition data and generates
personalized nutrition recommendations. Patterns detected:
- Overtraining: HRV↓ + sleep↓ + activity↑
- Inflammation: temp_deviation↑ + HRV↓ + high sugar
- Poor Recovery: readiness↓ + RHR↑
- Sleep Disruption: sleep_efficiency↓ + late meals
"""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements,broad-except,line-too-long

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from common.utils.logging import get_logger
from ..dependencies.usage_gate import UsageGate, _supabase_get

logger = get_logger(__name__)
router = APIRouter()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("RECOMMENDATION_AI_MODEL", "gpt-4o-mini")
USE_SANDBOX = os.environ.get("USE_SANDBOX", "true").lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class FoodSuggestion(BaseModel):
    name: str
    reason: str
    category: str  # protein, anti_inflammatory, recovery, sleep, energy


class PatternDetection(BaseModel):
    pattern: str  # overtraining, inflammation, poor_recovery, sleep_disruption
    label: str
    severity: str  # mild, moderate, high
    signals: List[str]
    food_suggestions: List[FoodSuggestion]


class Recommendation(BaseModel):
    id: str
    title: str
    description: str
    priority: str  # high, medium, low
    category: str  # nutrition, timing, supplement, lifestyle
    foods: List[FoodSuggestion]
    rationale: str


class RecommendationsResponse(BaseModel):
    patterns_detected: List[PatternDetection]
    recommendations: List[Recommendation]
    ai_summary: Optional[str] = None
    data_quality: str  # good, limited, insufficient
    generated_at: str


class RecoveryPlan(BaseModel):
    title: str
    overview: str
    daily_plan: List[Dict[str, Any]]
    key_focus_areas: List[str]
    foods_to_emphasize: List[FoodSuggestion]
    foods_to_limit: List[str]
    generated_at: str


# ---------------------------------------------------------------------------
# Pattern detection rules
# ---------------------------------------------------------------------------

# Hardcoded food lists per pattern (fast, no AI needed)
PATTERN_FOODS: Dict[str, List[Dict[str, str]]] = {
    "overtraining": [
        {
            "name": "Salmon",
            "reason": "Omega-3 reduces exercise-induced inflammation",
            "category": "anti_inflammatory",
        },
        {
            "name": "Tart cherry juice",
            "reason": "Anthocyanins accelerate muscle recovery",
            "category": "recovery",
        },
        {
            "name": "Sweet potatoes",
            "reason": "Complex carbs replenish glycogen stores",
            "category": "recovery",
        },
        {
            "name": "Eggs",
            "reason": "Complete protein + choline for muscle repair",
            "category": "protein",
        },
        {
            "name": "Turmeric/ginger tea",
            "reason": "Natural anti-inflammatory compounds",
            "category": "anti_inflammatory",
        },
        {
            "name": "Greek yogurt",
            "reason": "Casein protein supports overnight recovery",
            "category": "protein",
        },
    ],
    "inflammation": [
        {
            "name": "Blueberries",
            "reason": "High antioxidants reduce oxidative stress",
            "category": "anti_inflammatory",
        },
        {
            "name": "Leafy greens (spinach, kale)",
            "reason": "Magnesium + folate reduce inflammation markers",
            "category": "anti_inflammatory",
        },
        {
            "name": "Walnuts",
            "reason": "ALA omega-3 + polyphenols",
            "category": "anti_inflammatory",
        },
        {
            "name": "Olive oil (extra virgin)",
            "reason": "Oleocanthal has ibuprofen-like effects",
            "category": "anti_inflammatory",
        },
        {
            "name": "Fatty fish (mackerel, sardines)",
            "reason": "EPA/DHA directly lower CRP",
            "category": "anti_inflammatory",
        },
    ],
    "poor_recovery": [
        {
            "name": "Bone broth",
            "reason": "Glycine + collagen support tissue repair",
            "category": "recovery",
        },
        {
            "name": "Magnesium-rich foods (pumpkin seeds, dark chocolate)",
            "reason": "Magnesium supports HRV and muscle relaxation",
            "category": "recovery",
        },
        {
            "name": "Bananas",
            "reason": "Potassium + B6 for nervous system recovery",
            "category": "recovery",
        },
        {
            "name": "Chicken breast",
            "reason": "Lean protein for muscle repair without excess fat",
            "category": "protein",
        },
        {
            "name": "Avocado",
            "reason": "Healthy fats + potassium for electrolyte balance",
            "category": "recovery",
        },
    ],
    "sleep_disruption": [
        {
            "name": "Kiwi",
            "reason": "Serotonin precursors improve sleep onset",
            "category": "sleep",
        },
        {
            "name": "Almonds",
            "reason": "Magnesium + melatonin support sleep quality",
            "category": "sleep",
        },
        {
            "name": "Turkey",
            "reason": "Tryptophan aids melatonin production",
            "category": "sleep",
        },
        {
            "name": "Chamomile tea",
            "reason": "Apigenin binds GABA receptors, promoting calm",
            "category": "sleep",
        },
        {
            "name": "Tart cherries",
            "reason": "Natural melatonin source",
            "category": "sleep",
        },
    ],
}


def _safe_avg(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _detect_patterns(
    oura_daily: Dict[str, Dict[str, float]],
    nutrition_daily: Dict[str, Dict[str, float]],
) -> List[PatternDetection]:
    """Detect metabolic patterns from recent data."""
    if not oura_daily:
        return []

    dates = sorted(oura_daily.keys())
    recent_dates = dates[-7:] if len(dates) >= 7 else dates
    recent_oura = [oura_daily[d] for d in recent_dates]
    recent_nutrition = [nutrition_daily.get(d, {}) for d in recent_dates]

    patterns: List[PatternDetection] = []

    # 1. Overtraining: HRV↓ + sleep↓ + activity↑
    hrv_vals = [d.get("hrv_balance", 0) for d in recent_oura if d.get("hrv_balance")]
    sleep_scores = [
        d.get("sleep_score", 0) for d in recent_oura if d.get("sleep_score")
    ]
    activity_scores = [
        d.get("activity_score", 0) for d in recent_oura if d.get("activity_score")
    ]

    if len(hrv_vals) >= 3 and len(sleep_scores) >= 3 and len(activity_scores) >= 3:
        hrv_avg = _safe_avg(hrv_vals)
        sleep_avg = _safe_avg(sleep_scores)
        activity_avg = _safe_avg(activity_scores)

        signals = []
        score = 0
        if hrv_avg < 55:
            signals.append(f"HRV balance low ({hrv_avg:.0f})")
            score += 1
        if sleep_avg < 70:
            signals.append(f"Sleep score below average ({sleep_avg:.0f})")
            score += 1
        if activity_avg > 75:
            signals.append(f"High activity level ({activity_avg:.0f})")
            score += 1

        if score >= 2:
            severity = "high" if score >= 3 else "moderate"
            patterns.append(
                PatternDetection(
                    pattern="overtraining",
                    label="Overtraining Risk",
                    severity=severity,
                    signals=signals,
                    food_suggestions=[
                        FoodSuggestion(**f) for f in PATTERN_FOODS["overtraining"]
                    ],
                )
            )

    # 2. Inflammation: temp_deviation↑ + HRV↓ + high sugar
    temp_vals = [
        d.get("temperature_deviation", 0)
        for d in recent_oura
        if "temperature_deviation" in d
    ]
    sugar_vals = [
        d.get("total_sugar_g", 0) for d in recent_nutrition if d.get("total_sugar_g")
    ]

    if temp_vals and hrv_vals:
        signals = []
        score = 0
        temp_avg = _safe_avg(temp_vals)
        if temp_avg > 0.3:
            signals.append(f"Elevated body temperature (+{temp_avg:.2f}°C)")
            score += 1
        if hrv_vals and _safe_avg(hrv_vals) < 50:
            signals.append(f"Low HRV balance ({_safe_avg(hrv_vals):.0f})")
            score += 1
        if sugar_vals and _safe_avg(sugar_vals) > 60:
            signals.append(f"High sugar intake ({_safe_avg(sugar_vals):.0f}g/day)")
            score += 1

        if score >= 2:
            severity = "high" if score >= 3 else "moderate"
            patterns.append(
                PatternDetection(
                    pattern="inflammation",
                    label="Inflammation Indicators",
                    severity=severity,
                    signals=signals,
                    food_suggestions=[
                        FoodSuggestion(**f) for f in PATTERN_FOODS["inflammation"]
                    ],
                )
            )

    # 3. Poor Recovery: readiness↓ + RHR↑
    readiness_vals = [
        d.get("readiness_score", 0) for d in recent_oura if d.get("readiness_score")
    ]
    rhr_vals = [
        d.get("resting_heart_rate", 0)
        for d in recent_oura
        if d.get("resting_heart_rate")
    ]

    if readiness_vals and rhr_vals:
        signals = []
        score = 0
        readiness_avg = _safe_avg(readiness_vals)
        rhr_avg = _safe_avg(rhr_vals)

        if readiness_avg < 65:
            signals.append(f"Low readiness score ({readiness_avg:.0f})")
            score += 1
        if rhr_avg > 68:
            signals.append(f"Elevated resting heart rate ({rhr_avg:.0f} bpm)")
            score += 1
        if hrv_vals and _safe_avg(hrv_vals) < 55:
            signals.append(f"Below-average HRV ({_safe_avg(hrv_vals):.0f})")
            score += 1

        if score >= 2:
            severity = "high" if score >= 3 else "moderate"
            patterns.append(
                PatternDetection(
                    pattern="poor_recovery",
                    label="Poor Recovery",
                    severity=severity,
                    signals=signals,
                    food_suggestions=[
                        FoodSuggestion(**f) for f in PATTERN_FOODS["poor_recovery"]
                    ],
                )
            )

    # 4. Sleep Disruption: sleep_efficiency↓ + late meals
    eff_vals = [
        d.get("sleep_efficiency", 0) for d in recent_oura if d.get("sleep_efficiency")
    ]
    meal_hour_vals = [
        d.get("last_meal_hour", 0) for d in recent_nutrition if d.get("last_meal_hour")
    ]

    if eff_vals:
        signals = []
        score = 0
        eff_avg = _safe_avg(eff_vals)

        if eff_avg < 85:
            signals.append(f"Low sleep efficiency ({eff_avg:.0f}%)")
            score += 1
        if meal_hour_vals and _safe_avg(meal_hour_vals) >= 20:
            signals.append(
                f"Late meals (avg last meal at {_safe_avg(meal_hour_vals):.0f}:00)"
            )
            score += 1
        if sleep_scores and _safe_avg(sleep_scores) < 70:
            signals.append(f"Below-average sleep score ({_safe_avg(sleep_scores):.0f})")
            score += 1

        if score >= 2:
            severity = "high" if score >= 3 else "moderate"
            patterns.append(
                PatternDetection(
                    pattern="sleep_disruption",
                    label="Sleep Disruption",
                    severity=severity,
                    signals=signals,
                    food_suggestions=[
                        FoodSuggestion(**f) for f in PATTERN_FOODS["sleep_disruption"]
                    ],
                )
            )

    return patterns


# ---------------------------------------------------------------------------
# AI-enhanced recommendations
# ---------------------------------------------------------------------------


async def _get_user_health_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user health profile from Supabase."""
    rows = await _supabase_get(
        "user_health_profile",
        f"user_id=eq.{user_id}&select=*&limit=1",
    )
    if rows and isinstance(rows, list):
        return rows[0]
    return None


async def _get_user_conditions(user_id: str) -> List[Dict[str, Any]]:
    """Fetch user's active health conditions from Supabase."""
    rows = await _supabase_get(
        "health_conditions",
        f"user_id=eq.{user_id}&is_active=eq.true&select=*",
    )
    if rows and isinstance(rows, list):
        return rows
    return []


async def _generate_ai_recommendations(
    patterns: List[PatternDetection],
    profile: Optional[Dict[str, Any]],
    conditions: List[Dict[str, Any]],
) -> Tuple[List[Recommendation], str]:
    """Use AI to personalize recommendations based on patterns + profile."""
    if not OPENAI_API_KEY or not patterns:
        return _fallback_recommendations(patterns), _fallback_summary(patterns)

    # Build context
    pattern_lines = []
    for p in patterns:
        pattern_lines.append(f"- {p.label} ({p.severity}): {', '.join(p.signals)}")

    profile_context = ""
    if profile:
        goals = profile.get("health_goals") or []
        if isinstance(goals, str):
            try:
                goals = json.loads(goals)
            except (json.JSONDecodeError, TypeError):
                goals = []
        prefs = profile.get("dietary_preferences") or []
        if isinstance(prefs, str):
            try:
                prefs = json.loads(prefs)
            except (json.JSONDecodeError, TypeError):
                prefs = []
        supplements = profile.get("supplements") or []
        if isinstance(supplements, str):
            try:
                supplements = json.loads(supplements)
            except (json.JSONDecodeError, TypeError):
                supplements = []

        profile_context = f"""
User Profile:
- Health goals: {', '.join(goals) if goals else 'Not specified'}
- Dietary preferences: {', '.join(prefs) if prefs else 'No restrictions'}
- Current supplements: {', '.join(s.get('name', '') for s in supplements if isinstance(s, dict)) if supplements else 'None'}"""

    condition_context = ""
    if conditions:
        cond_names = [
            c.get("condition_name", "") for c in conditions if c.get("condition_name")
        ]
        if cond_names:
            condition_context = f"\nHealth conditions: {', '.join(cond_names)}"

    prompt = f"""You are a nutrition advisor for a health app. Based on the detected metabolic patterns and user profile, generate personalized nutrition recommendations.

Detected Patterns:
{chr(10).join(pattern_lines)}
{profile_context}
{condition_context}

Generate 3-5 actionable nutrition recommendations. For each, provide:
1. A concise title (5-8 words)
2. A description (1-2 sentences)
3. Priority (high/medium/low)
4. Category (nutrition/timing/supplement/lifestyle)
5. 2-3 specific food suggestions with reasons
6. Brief rationale

Respond in JSON:
{{
  "recommendations": [
    {{
      "title": "...",
      "description": "...",
      "priority": "high|medium|low",
      "category": "nutrition|timing|supplement|lifestyle",
      "foods": [{{"name": "...", "reason": "...", "category": "..."}}],
      "rationale": "..."
    }}
  ],
  "summary": "2-3 sentence overview of the key nutritional focus areas"
}}

Important: Do not provide medical diagnoses. Frame as observed patterns and suggestions."""

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
                    logger.warning(
                        "OpenAI API returned %s for recommendations", resp.status
                    )
                    return _fallback_recommendations(patterns), _fallback_summary(
                        patterns
                    )

                result = await resp.json()

        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        recs = []
        for i, r in enumerate(parsed.get("recommendations", [])):
            foods = [
                FoodSuggestion(
                    name=f.get("name", ""),
                    reason=f.get("reason", ""),
                    category=f.get("category", "nutrition"),
                )
                for f in r.get("foods", [])
            ]
            recs.append(
                Recommendation(
                    id=f"rec-{i+1}",
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    priority=r.get("priority", "medium"),
                    category=r.get("category", "nutrition"),
                    foods=foods,
                    rationale=r.get("rationale", ""),
                )
            )

        summary = parsed.get("summary", "")
        return recs, summary

    except Exception as exc:
        logger.warning("AI recommendation generation failed: %s", exc)
        return _fallback_recommendations(patterns), _fallback_summary(patterns)


def _fallback_recommendations(patterns: List[PatternDetection]) -> List[Recommendation]:
    """Generate simple recommendations without AI."""
    recs = []
    for i, p in enumerate(patterns):
        foods = p.food_suggestions[:3]
        recs.append(
            Recommendation(
                id=f"rec-{i+1}",
                title=f"Address {p.label}",
                description=f"Based on detected {p.label.lower()} pattern ({p.severity} severity). "
                f"Signals: {', '.join(p.signals[:2])}.",
                priority="high" if p.severity == "high" else "medium",
                category="nutrition",
                foods=foods,
                rationale=f"Your recent data shows signs of {p.label.lower()}. "
                f"Adjusting nutrition can help improve recovery.",
            )
        )
    return recs


def _fallback_summary(patterns: List[PatternDetection]) -> str:
    if not patterns:
        return "No significant metabolic patterns detected. Your nutrition and recovery appear balanced."
    labels = [p.label.lower() for p in patterns]
    return (
        f"Your recent data shows signs of {', '.join(labels)}. "
        f"Focus on anti-inflammatory foods, adequate protein, and meal timing "
        f"to support recovery."
    )


# ---------------------------------------------------------------------------
# Data fetching (reuse from correlations)
# ---------------------------------------------------------------------------


async def _get_recent_data(
    current_user: dict, bearer: Optional[str]
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """Fetch recent Oura + nutrition data for pattern detection."""
    from .correlations import _extract_oura_daily, _fetch_nutrition_daily
    from .timeline import get_timeline

    try:
        timeline = await get_timeline(days=14, current_user=current_user)
    except Exception as exc:
        logger.error("Failed to fetch timeline for recommendations: %s", exc)
        timeline = []

    oura_daily = _extract_oura_daily(timeline)
    nutrition_daily = await _fetch_nutrition_daily(bearer, 14)

    return oura_daily, nutrition_daily


# ---------------------------------------------------------------------------
# Recovery plan generation
# ---------------------------------------------------------------------------


async def _generate_recovery_plan(
    patterns: List[PatternDetection],
    profile: Optional[Dict[str, Any]],
    conditions: List[Dict[str, Any]],
) -> RecoveryPlan:
    """Generate AI recovery nutrition plan."""
    # Collect all food suggestions from patterns
    all_foods: List[FoodSuggestion] = []
    focus_areas: List[str] = []
    foods_to_limit: List[str] = []

    for p in patterns:
        all_foods.extend(p.food_suggestions[:3])
        focus_areas.append(p.label)

        if p.pattern == "inflammation":
            foods_to_limit.extend(["Refined sugar", "Processed foods", "Seed oils"])
        elif p.pattern == "sleep_disruption":
            foods_to_limit.extend(
                ["Caffeine after 2pm", "Heavy meals after 8pm", "Alcohol"]
            )
        elif p.pattern == "overtraining":
            foods_to_limit.extend(
                ["Fasting/calorie restriction", "High-intensity exercise"]
            )

    # Deduplicate
    seen_foods = set()
    unique_foods = []
    for f in all_foods:
        if f.name not in seen_foods:
            seen_foods.add(f.name)
            unique_foods.append(f)

    foods_to_limit = list(dict.fromkeys(foods_to_limit))

    if not OPENAI_API_KEY or not patterns:
        return RecoveryPlan(
            title="Recovery Nutrition Plan",
            overview=_fallback_summary(patterns),
            daily_plan=[
                {
                    "day": "Day 1-2",
                    "focus": "Reduce inflammation",
                    "meals": "Anti-inflammatory foods, reduced sugar",
                },
                {
                    "day": "Day 3-4",
                    "focus": "Rebuild recovery",
                    "meals": "High protein, magnesium-rich foods",
                },
                {
                    "day": "Day 5-7",
                    "focus": "Optimize sleep",
                    "meals": "Early dinners, sleep-supporting foods",
                },
            ],
            key_focus_areas=focus_areas or ["General recovery"],
            foods_to_emphasize=unique_foods[:8],
            foods_to_limit=foods_to_limit[:5],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # AI-enhanced plan
    pattern_lines = [f"- {p.label}: {', '.join(p.signals)}" for p in patterns]

    profile_str = ""
    if profile:
        prefs = profile.get("dietary_preferences") or []
        if isinstance(prefs, str):
            try:
                prefs = json.loads(prefs)
            except (json.JSONDecodeError, TypeError):
                prefs = []
        if prefs:
            profile_str = f"\nDietary preferences: {', '.join(prefs)}"

    prompt = f"""Create a 7-day recovery nutrition plan based on these detected health patterns:

{chr(10).join(pattern_lines)}
{profile_str}

Respond in JSON:
{{
  "title": "Personalized Recovery Plan title",
  "overview": "2-3 sentence overview",
  "daily_plan": [
    {{"day": "Day 1-2", "focus": "...", "meals": "Brief meal suggestions"}},
    {{"day": "Day 3-4", "focus": "...", "meals": "..."}},
    {{"day": "Day 5-7", "focus": "...", "meals": "..."}}
  ],
  "key_focus_areas": ["area1", "area2"],
  "foods_to_limit": ["food1", "food2"]
}}

Keep it practical and actionable. No medical diagnoses."""

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
                    raise ValueError(f"OpenAI returned {resp.status}")
                result = await resp.json()

        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return RecoveryPlan(
            title=parsed.get("title", "Recovery Nutrition Plan"),
            overview=parsed.get("overview", _fallback_summary(patterns)),
            daily_plan=parsed.get("daily_plan", []),
            key_focus_areas=parsed.get("key_focus_areas", focus_areas),
            foods_to_emphasize=unique_foods[:8],
            foods_to_limit=parsed.get("foods_to_limit", foods_to_limit[:5]),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as exc:
        logger.warning("AI recovery plan generation failed: %s", exc)
        return RecoveryPlan(
            title="Recovery Nutrition Plan",
            overview=_fallback_summary(patterns),
            daily_plan=[
                {
                    "day": "Day 1-2",
                    "focus": "Reduce inflammation",
                    "meals": "Anti-inflammatory foods, reduced sugar",
                },
                {
                    "day": "Day 3-4",
                    "focus": "Rebuild recovery",
                    "meals": "High protein, magnesium-rich foods",
                },
                {
                    "day": "Day 5-7",
                    "focus": "Optimize sleep",
                    "meals": "Early dinners, sleep-supporting foods",
                },
            ],
            key_focus_areas=focus_areas or ["General recovery"],
            foods_to_emphasize=unique_foods[:8],
            foods_to_limit=foods_to_limit[:5],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=RecommendationsResponse)
async def get_recommendations(
    request: Request,
    current_user: dict = Depends(UsageGate("correlations")),
):
    """
    Get personalized nutrition recommendations based on detected patterns.
    Analyzes recent Oura + nutrition data for metabolic patterns.
    """
    bearer = request.headers.get("Authorization")
    oura_daily, nutrition_daily = await _get_recent_data(current_user, bearer)

    if not oura_daily:
        return RecommendationsResponse(
            patterns_detected=[],
            recommendations=[],
            ai_summary="Connect your Oura ring and log meals to receive personalized recommendations.",
            data_quality="insufficient",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    data_quality = (
        "good" if len(oura_daily) >= 7 and len(nutrition_daily) >= 5 else "limited"
    )

    # Detect patterns
    patterns = _detect_patterns(oura_daily, nutrition_daily)

    # Get user profile + conditions for personalization
    user_id = current_user["id"]
    profile = await _get_user_health_profile(user_id)
    conditions = await _get_user_conditions(user_id)

    # Generate AI-enhanced recommendations
    recommendations, ai_summary = await _generate_ai_recommendations(
        patterns, profile, conditions
    )

    return RecommendationsResponse(
        patterns_detected=patterns,
        recommendations=recommendations,
        ai_summary=ai_summary,
        data_quality=data_quality,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/recovery-plan", response_model=RecoveryPlan)
async def get_recovery_plan(
    request: Request,
    current_user: dict = Depends(UsageGate("correlations")),
):
    """
    Generate an AI recovery nutrition plan based on detected patterns.
    """
    bearer = request.headers.get("Authorization")
    oura_daily, nutrition_daily = await _get_recent_data(current_user, bearer)

    patterns = _detect_patterns(oura_daily, nutrition_daily)

    user_id = current_user["id"]
    profile = await _get_user_health_profile(user_id)
    conditions = await _get_user_conditions(user_id)

    plan = await _generate_recovery_plan(patterns, profile, conditions)
    return plan
