"""
Nutrition Assistant API — contextual intelligence for the Track/Nutrition screen.

Provides:
- Post-log insights (personalized AI feedback after logging a meal)
- Daily progress (today's meals, totals, remaining budget)
- Meal suggestions (context-aware next-meal recommendations)
- Food swaps (healthier alternatives based on health context)
"""

import asyncio
import json
import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()

NUTRITION_SERVICE_URL = os.environ.get(
    "NUTRITION_SERVICE_URL", "http://localhost:8007"
).rstrip("/")


# ---------------------------------------------------------------------------
# Context Gathering
# ---------------------------------------------------------------------------


async def _fetch_todays_meals(user_id: str, bearer: Optional[str]) -> list:
    """Fetch today's meals — tries nutrition service first, falls back to Supabase."""
    today = date.today().isoformat()

    # Try nutrition service (has full nutrition data)
    url = (
        f"{NUTRITION_SERVICE_URL}/api/v1/nutrition/nutrition-history"
        f"?start_date={today}&end_date={today}"
    )
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = bearer
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    meals = data if isinstance(data, list) else (data.get("data") or [])
                    if meals:
                        return meals
    except Exception as e:
        logger.debug("Nutrition service fetch failed, falling back to Supabase: %s", e)

    # Fallback: query Supabase meal_logs directly
    rows = await _supabase_get(
        "meal_logs",
        f"user_id=eq.{user_id}&order=timestamp.desc&limit=20"
        f"&select=meal_name,food_name,meal_type,calories,timestamp",
    )
    # Filter to today only (timestamp may be full ISO datetime)
    today_rows = [r for r in rows if (r.get("timestamp") or "")[:10] == today]
    return today_rows


async def _fetch_nutrition_targets(user_id: str) -> dict:
    """Fetch user's nutrition targets or return sensible defaults."""
    rows = await _supabase_get(
        "nutrition_goals",
        f"user_id=eq.{user_id}&select=target_calories,target_protein_g,"
        f"target_carbs_g,target_fat_g,target_fiber_g&limit=1",
    )
    if rows:
        r = rows[0]
        return {
            "calories": r.get("target_calories") or 2000,
            "protein_g": r.get("target_protein_g") or 100,
            "carbs_g": r.get("target_carbs_g") or 200,
            "fat_g": r.get("target_fat_g") or 65,
            "fiber_g": r.get("target_fiber_g") or 30,
        }
    # Defaults based on profile
    profile = await _supabase_get(
        "profiles",
        f"id=eq.{user_id}&select=weight_kg,biological_sex",
    )
    weight = (profile[0].get("weight_kg") or 70) if profile else 70
    cals = int(weight * 28)  # rough maintenance
    return {
        "calories": cals,
        "protein_g": int(weight * 1.4),
        "carbs_g": int(cals * 0.45 / 4),
        "fat_g": int(cals * 0.30 / 9),
        "fiber_g": 30,
    }


async def _gather_nutrition_context(
    user_id: str, bearer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gather full health context relevant to nutrition decisions.
    All fetches run in parallel for speed.
    """
    (
        meals_raw,
        targets,
        profile_rows,
        conditions,
        medications,
        supplements,
        labs,
        wearable,
        prefs,
        experiments,
        journeys,
        goals,
        cycle_logs,
        efficacy,
    ) = await asyncio.gather(
        _fetch_todays_meals(user_id, bearer),
        _fetch_nutrition_targets(user_id),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}"
            f"&select=date_of_birth,biological_sex,weight_kg,height_cm,full_name",
        ),
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=condition_name,condition_category",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=medication_name,dosage,frequency",
        ),
        _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=supplement_name,dosage,frequency,purpose",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=3"
            f"&select=test_type,test_date,biomarkers",
        ),
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=eq.{date.today().isoformat()}"
            f"&select=metric_type,score,latest_value",
        ),
        _supabase_get(
            "nutrition_analyst_prefs",
            f"user_id=eq.{user_id}&select=preferences&limit=1",
        ),
        _supabase_get(
            "active_interventions",
            f"user_id=eq.{user_id}&status=eq.active"
            f"&select=title,started_at,duration_days&limit=3",
        ),
        _supabase_get(
            "goal_journeys",
            f"user_id=eq.{user_id}&status=eq.active"
            f"&select=title,phases,current_phase&limit=1",
        ),
        _supabase_get(
            "user_goals",
            f"user_id=eq.{user_id}&status=eq.active&category=eq.diet"
            f"&select=goal_text&limit=3",
        ),
        _supabase_get(
            "cycle_logs",
            f"user_id=eq.{user_id}&order=event_date.desc"
            f"&select=event_type,event_date&limit=1",
        ),
        _supabase_get(
            "efficacy_patterns",
            f"user_id=eq.{user_id}&verdict=eq.proven"
            f"&select=pattern_label,metric_pair,effect_direction&limit=5",
        ),
    )

    # Demographics
    profile = profile_rows[0] if profile_rows else {}
    dob = profile.get("date_of_birth")
    age = None
    if dob:
        try:
            birth = date.fromisoformat(str(dob)[:10])
            age = (date.today() - birth).days // 365
        except (ValueError, TypeError):
            pass
    demographics = {
        "age": age,
        "sex": profile.get("biological_sex"),
        "weight_kg": profile.get("weight_kg"),
        "height_cm": profile.get("height_cm"),
        "first_name": (profile.get("full_name") or "").split(" ")[0] or None,
    }

    # Compute daily totals from meals
    daily_totals = {
        "calories": 0,
        "protein_g": 0,
        "carbs_g": 0,
        "fat_g": 0,
        "fiber_g": 0,
    }
    meals_summary = []
    for m in meals_raw:
        cals = m.get("total_calories") or m.get("calories") or 0
        daily_totals["calories"] += cals
        daily_totals["protein_g"] += m.get("total_protein_g") or m.get("protein_g") or 0
        daily_totals["carbs_g"] += m.get("total_carbs_g") or m.get("carbs_g") or 0
        daily_totals["fat_g"] += m.get("total_fat_g") or m.get("fat_g") or 0
        daily_totals["fiber_g"] += m.get("total_fiber_g") or m.get("fiber_g") or 0
        meals_summary.append(
            {
                "meal_type": m.get("meal_type", "meal"),
                "meal_name": m.get("meal_name") or m.get("food_name") or "Meal",
                "calories": round(cals),
            }
        )

    remaining = {k: max(0, round(targets[k] - daily_totals[k])) for k in targets}

    # Extract abnormal labs
    abnormal_labs = []
    for lab in labs:
        biomarkers = lab.get("biomarkers") or []
        if isinstance(biomarkers, str):
            try:
                biomarkers = json.loads(biomarkers)
            except (json.JSONDecodeError, TypeError):
                biomarkers = []
        for bm in biomarkers:
            if not isinstance(bm, dict):
                continue
            if bm.get("status") in ("abnormal", "critical", "borderline"):
                abnormal_labs.append(
                    {
                        "name": bm.get("name"),
                        "value": bm.get("value"),
                        "unit": bm.get("unit"),
                        "status": bm.get("status"),
                        "date": lab.get("test_date"),
                    }
                )

    # Wearable today summary
    wearable_today = {}
    for w in wearable:
        mt = w.get("metric_type", "")
        if mt == "steps":
            wearable_today["steps"] = w.get("latest_value") or w.get("score")
        elif mt == "sleep":
            wearable_today["sleep_score"] = w.get("score")
        elif mt in ("hrv_sdnn", "hrv"):
            wearable_today["hrv"] = w.get("latest_value") or w.get("score")
        elif mt == "active_calories":
            wearable_today["active_cal"] = w.get("latest_value") or w.get("score")

    # Dietary preferences
    dietary_prefs: Dict[str, Any] = {}
    if prefs:
        dietary_prefs = prefs[0].get("preferences") or {}
        if isinstance(dietary_prefs, str):
            try:
                dietary_prefs = json.loads(dietary_prefs)
            except (json.JSONDecodeError, TypeError):
                dietary_prefs = {}

    # Active experiment
    active_experiment = None
    for exp in experiments:
        title = exp.get("title", "")
        started = exp.get("started_at", "")[:10]
        try:
            day_num = (date.today() - date.fromisoformat(started)).days + 1
        except (ValueError, TypeError):
            day_num = None
        active_experiment = {
            "title": title,
            "day": day_num,
            "duration": exp.get("duration_days"),
        }
        break

    # Journey phase
    journey_phase = None
    if journeys:
        j = journeys[0]
        phases = j.get("phases") or []
        if isinstance(phases, str):
            try:
                phases = json.loads(phases)
            except (json.JSONDecodeError, TypeError):
                phases = []
        cp = j.get("current_phase", 0)
        phase_name = (
            phases[cp].get("name", f"Phase {cp + 1}") if cp < len(phases) else None
        )
        journey_phase = {
            "title": j.get("title"),
            "phase": phase_name,
        }

    # Cycle phase estimation
    cycle_phase = None
    if cycle_logs:
        last_event = cycle_logs[0]
        if last_event.get("event_type") == "period_start":
            try:
                period_start = date.fromisoformat(last_event["event_date"][:10])
                day_in_cycle = (date.today() - period_start).days
                if day_in_cycle <= 5:
                    cycle_phase = {"phase": "menstrual", "day": day_in_cycle}
                elif day_in_cycle <= 13:
                    cycle_phase = {"phase": "follicular", "day": day_in_cycle}
                elif day_in_cycle <= 16:
                    cycle_phase = {"phase": "ovulatory", "day": day_in_cycle}
                elif day_in_cycle <= 28:
                    cycle_phase = {"phase": "luteal", "day": day_in_cycle}
            except (ValueError, TypeError):
                pass

    return {
        "demographics": demographics,
        "today_meals": meals_summary,
        "daily_totals": {k: round(v) for k, v in daily_totals.items()},
        "targets": targets,
        "remaining": remaining,
        "conditions": [c.get("condition_name") for c in conditions],
        "medications": [
            {
                "name": m.get("medication_name"),
                "dosage": m.get("dosage"),
                "frequency": m.get("frequency"),
            }
            for m in medications
        ],
        "supplements": [
            {"name": s.get("supplement_name"), "dosage": s.get("dosage")}
            for s in supplements
        ],
        "abnormal_labs": abnormal_labs[:5],
        "wearable_today": wearable_today,
        "dietary_prefs": dietary_prefs,
        "active_experiment": active_experiment,
        "journey_phase": journey_phase,
        "goals": [g.get("goal_text") for g in goals],
        "cycle_phase": cycle_phase,
        "proven_patterns": [
            {"label": p.get("pattern_label"), "direction": p.get("effect_direction")}
            for p in efficacy
        ],
    }


def _format_context_for_prompt(ctx: dict) -> str:
    """Format nutrition context dict into concise prompt text."""
    parts = []

    # Demographics — critical for age/sex-appropriate nutrition
    demo = ctx.get("demographics", {})
    demo_parts = []
    if demo.get("age"):
        demo_parts.append(f"age {demo['age']}")
    if demo.get("sex"):
        sex_label = {
            "male": "male",
            "female": "female",
            "other": "non-binary",
        }.get(demo["sex"], demo["sex"])
        demo_parts.append(sex_label)
    if demo.get("weight_kg"):
        demo_parts.append(f"{demo['weight_kg']}kg")
    if demo.get("height_cm"):
        demo_parts.append(f"{demo['height_cm']}cm")
    if demo.get("first_name"):
        demo_parts.insert(0, demo["first_name"])
    if demo_parts:
        parts.append(f"Profile: {', '.join(demo_parts)}")

    # Infer life stage for nutrition guidance
    age = demo.get("age")
    sex = demo.get("sex")
    if age and sex:
        if sex == "female" and age >= 45:
            # Check cycle data — if no recent periods, likely peri/post-menopausal
            if not ctx.get("cycle_phase"):
                parts.append(
                    "Life stage: likely peri/post-menopausal — prioritize calcium, "
                    "vitamin D, iron awareness (lower need post-menopause), omega-3, "
                    "and adequate protein for bone/muscle preservation"
                )
            elif age >= 55:
                parts.append(
                    "Life stage: post-menopausal — prioritize calcium (1200mg/d), "
                    "vitamin D (800-1000 IU/d), protein for sarcopenia prevention"
                )
        elif sex == "female" and age < 25:
            parts.append(
                "Life stage: young adult female — ensure adequate iron, folate, "
                "calcium for peak bone mass, and sufficient calories for activity level"
            )
        elif sex == "male" and age < 25:
            parts.append(
                "Life stage: young adult male — higher calorie/protein needs for "
                "growth, ensure zinc, magnesium, and vitamin D adequacy"
            )
        elif age >= 65:
            parts.append(
                "Life stage: older adult — prioritize protein (1.2-1.5g/kg) to "
                "prevent sarcopenia, vitamin B12, vitamin D, calcium, hydration"
            )

    if ctx.get("today_meals"):
        meal_strs = [
            f"{m['meal_type'].title()}: {m['meal_name']} ({m['calories']} cal)"
            for m in ctx["today_meals"]
        ]
        parts.append(f"Today's meals: {'; '.join(meal_strs)}")
        t = ctx["daily_totals"]
        parts.append(
            f"Daily totals so far: {t['calories']} cal, {t['protein_g']}g protein, {t['carbs_g']}g carbs, {t['fat_g']}g fat"
        )
        r = ctx["remaining"]
        parts.append(
            f"Remaining budget: ~{r['calories']} cal, {r['protein_g']}g protein, {r['carbs_g']}g carbs, {r['fat_g']}g fat"
        )
    else:
        parts.append("No meals logged today yet.")
        t = ctx.get("targets", {})
        parts.append(
            f"Daily targets: {t.get('calories', 2000)} cal, {t.get('protein_g', 100)}g protein"
        )

    if ctx.get("conditions"):
        parts.append(f"Health conditions: {', '.join(ctx['conditions'])}")
    if ctx.get("medications"):
        med_strs = [
            f"{m['name']} {m.get('dosage', '')} ({m.get('frequency', '')})"
            for m in ctx["medications"]
        ]
        parts.append(f"Medications: {', '.join(med_strs)}")
    if ctx.get("supplements"):
        sup_strs = [f"{s['name']} {s.get('dosage', '')}" for s in ctx["supplements"]]
        parts.append(f"Supplements: {', '.join(sup_strs)}")
    if ctx.get("abnormal_labs"):
        lab_strs = [
            f"{l['name']}: {l['value']} {l.get('unit', '')} ({l['status']})"
            for l in ctx["abnormal_labs"]
        ]
        parts.append(f"Recent lab flags: {', '.join(lab_strs)}")
    if ctx.get("wearable_today"):
        w = ctx["wearable_today"]
        w_parts = []
        if w.get("steps"):
            w_parts.append(f"{int(w['steps']):,} steps")
        if w.get("active_cal"):
            w_parts.append(f"{int(w['active_cal'])} active cal")
        if w.get("sleep_score"):
            w_parts.append(f"sleep score {int(w['sleep_score'])}")
        if w.get("hrv"):
            w_parts.append(f"HRV {int(w['hrv'])}ms")
        if w_parts:
            parts.append(f"Wearable today: {', '.join(w_parts)}")
    if ctx.get("dietary_prefs"):
        dp = ctx["dietary_prefs"]
        pref_parts = []
        if dp.get("diet_type"):
            pref_parts.append(dp["diet_type"])
        if dp.get("allergies"):
            pref_parts.append(f"allergies: {', '.join(dp['allergies'])}")
        if dp.get("restrictions"):
            pref_parts.append(f"restrictions: {', '.join(dp['restrictions'])}")
        if pref_parts:
            parts.append(f"Dietary preferences: {', '.join(pref_parts)}")
    if ctx.get("active_experiment"):
        e = ctx["active_experiment"]
        parts.append(
            f"Active experiment: {e['title']} (day {e.get('day')}/{e.get('duration')})"
        )
    if ctx.get("journey_phase"):
        j = ctx["journey_phase"]
        parts.append(f"Journey: {j['title']} — {j.get('phase')}")
    if ctx.get("goals"):
        parts.append(f"Nutrition goals: {', '.join(ctx['goals'])}")
    if ctx.get("cycle_phase"):
        c = ctx["cycle_phase"]
        parts.append(f"Cycle: {c['phase']} phase (day {c['day']})")
    if ctx.get("proven_patterns"):
        pat_strs = [p["label"] for p in ctx["proven_patterns"] if p.get("label")]
        if pat_strs:
            parts.append(f"Proven patterns: {', '.join(pat_strs)}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class PostLogInsightRequest(BaseModel):
    meal_type: str = "meal"
    food_items: List[Dict[str, Any]] = []


class PostLogInsightResponse(BaseModel):
    insight: str
    macros: Dict[str, float]
    quick_actions: List[str]


@router.post("/post-log-insight", response_model=PostLogInsightResponse)
async def post_log_insight(
    body: PostLogInsightRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a personalized AI insight after the user logs a meal.

    References health conditions, medications, labs, wearable data,
    active experiments, and dietary preferences.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")

    ctx = await _gather_nutrition_context(user_id, bearer)

    # Compute macros from food items
    macros = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    food_lines = []
    for f in body.food_items:
        macros["calories"] += f.get("calories") or 0
        macros["protein_g"] += f.get("protein_g") or 0
        macros["carbs_g"] += f.get("carbs_g") or 0
        macros["fat_g"] += f.get("fat_g") or 0
        qty = f.get("quantity", "")
        unit = f.get("unit", "")
        name = f.get("name", "food")
        food_lines.append(f"{qty} {unit} {name}".strip())

    macros = {k: round(v, 1) for k, v in macros.items()}
    context_text = _format_context_for_prompt(ctx)
    first_name = ctx.get("demographics", {}).get("first_name") or "there"

    # Build prompt
    prompt = f"""You are a nutrition analyst. The user's name is {first_name}.

MEAL LOGGED:
{body.meal_type.title()}: {', '.join(food_lines) or 'meal logged'}
Total: {macros['calories']} cal, {macros['protein_g']}g protein, {macros['carbs_g']}g carbs, {macros['fat_g']}g fat

HEALTH CONTEXT:
{context_text}

Generate a 1-2 sentence personalized insight about this meal. Rules:
- Address {first_name} by name naturally (e.g. "Nice choice, {first_name}!")
- Reference at least one specific health data point (condition, lab, medication, wearable, or experiment)
- Be encouraging but honest — flag concerns gently
- If a medication should be taken with/around this meal, mention timing
- If this meal conflicts with an active experiment, flag it
- Keep it conversational and warm, not clinical
- Max 100 words
- Return ONLY the insight text, nothing else."""

    # Call Claude
    insight = await _call_claude(prompt)

    # Determine quick actions based on context
    quick_actions = ["Ask nutrition coach"]
    remaining_cal = ctx.get("remaining", {}).get("calories", 0)
    if remaining_cal > 300:
        quick_actions.insert(0, "Suggest next meal")
    if ctx.get("active_experiment"):
        quick_actions.append("Check experiment fit")

    return PostLogInsightResponse(
        insight=insight,
        macros=macros,
        quick_actions=quick_actions,
    )


class DailyProgressResponse(BaseModel):
    meals_today: List[Dict[str, Any]]
    totals: Dict[str, float]
    targets: Dict[str, float]
    remaining: Dict[str, float]
    progress_pct: Dict[str, int]


@router.get("/daily-progress", response_model=DailyProgressResponse)
async def daily_progress(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Today's nutrition progress: meals logged, totals, targets, remaining.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")
    ctx = await _gather_nutrition_context(user_id, bearer)

    totals = ctx["daily_totals"]
    targets = ctx["targets"]
    remaining = ctx["remaining"]

    progress_pct = {}
    for k in ("calories", "protein_g", "carbs_g", "fat_g"):
        tgt = targets.get(k, 1)
        progress_pct[k.replace("_g", "")] = (
            min(100, round((totals.get(k, 0) / tgt) * 100)) if tgt else 0
        )

    return DailyProgressResponse(
        meals_today=ctx["today_meals"],
        totals=totals,
        targets=targets,
        remaining=remaining,
        progress_pct=progress_pct,
    )


class SuggestMealRequest(BaseModel):
    meal_type: Optional[str] = None


class SuggestMealResponse(BaseModel):
    meal_name: str
    ingredients: List[Dict[str, Any]]
    macros: Dict[str, float]
    rationale: str


@router.post("/suggest-meal", response_model=SuggestMealResponse)
async def suggest_meal(
    body: SuggestMealRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a personalized meal suggestion based on full health context.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")
    ctx = await _gather_nutrition_context(user_id, bearer)

    # Infer meal type from time if not provided
    meal_type = body.meal_type
    if not meal_type:
        hour = datetime.now().hour
        if hour < 10:
            meal_type = "breakfast"
        elif hour < 14:
            meal_type = "lunch"
        elif hour < 17:
            meal_type = "snack"
        else:
            meal_type = "dinner"

    context_text = _format_context_for_prompt(ctx)
    first_name = ctx.get("demographics", {}).get("first_name") or "there"
    r = ctx.get("remaining", {})

    prompt = f"""You are a nutrition analyst. The user's name is {first_name}. Suggest a {meal_type}.

TODAY SO FAR:
{context_text}

Remaining budget: ~{r.get('calories', 600)} cal, {r.get('protein_g', 40)}g protein, {r.get('carbs_g', 60)}g carbs, {r.get('fat_g', 20)}g fat

Suggest ONE specific meal. Return ONLY valid JSON (no markdown fences):
{{
  "meal_name": "Descriptive meal name",
  "ingredients": [
    {{"name": "ingredient", "portion": "amount", "unit": "unit"}},
  ],
  "macros": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
  "rationale": "One sentence addressing {first_name} by name explaining why this meal is good for their specific situation"
}}

Rules:
- Must fit within remaining calorie/macro budget
- Must respect dietary restrictions and allergies
- Prioritize nutrients flagged as low in recent labs
- If active experiment, ensure compliance
- If cycle phase known, adjust accordingly (e.g. iron-rich in menstrual)
- Be specific with portions (e.g. "6 oz grilled salmon" not just "salmon")"""

    raw = await _call_claude(prompt, max_tokens=500)

    # Parse JSON response
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        parsed = {
            "meal_name": "Balanced meal",
            "ingredients": [],
            "macros": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
            "rationale": raw[:200],
        }

    return SuggestMealResponse(
        meal_name=parsed.get("meal_name", "Meal suggestion"),
        ingredients=parsed.get("ingredients", []),
        macros=parsed.get("macros", {}),
        rationale=parsed.get("rationale", ""),
    )


class SwapRequest(BaseModel):
    food_name: str
    reason: Optional[str] = None  # "lower_carb", "higher_protein", "iron_rich", etc.


class SwapResponse(BaseModel):
    original: str
    alternatives: List[Dict[str, Any]]


@router.post("/swap", response_model=SwapResponse)
async def swap_food(
    body: SwapRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Suggest 3 alternative foods based on health context.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")
    ctx = await _gather_nutrition_context(user_id, bearer)
    context_text = _format_context_for_prompt(ctx)

    first_name = ctx.get("demographics", {}).get("first_name") or "there"
    reason_text = f" that is {body.reason.replace('_', ' ')}" if body.reason else ""

    prompt = f"""Suggest 3 food alternatives for "{body.food_name}"{reason_text} for {first_name}.

USER CONTEXT:
{context_text}

Return ONLY valid JSON (no markdown fences):
[
  {{"name": "alternative food", "portion": "amount with unit", "macros": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}}, "why": "one sentence why it's better"}}
]

Rules:
- Respect dietary restrictions and allergies
- Consider health conditions and lab flags
- Keep portions realistic and specific"""

    raw = await _call_claude(prompt, max_tokens=500)

    try:
        if "```" in raw:
            raw = raw[raw.find("[") : raw.rfind("]") + 1]
        alternatives = json.loads(raw)
        if not isinstance(alternatives, list):
            alternatives = []
    except (json.JSONDecodeError, ValueError):
        alternatives = []

    return SwapResponse(
        original=body.food_name,
        alternatives=alternatives[:3],
    )


class MealPlanRequest(BaseModel):
    days: int = 7


class MealPlanResponse(BaseModel):
    days: List[Dict[str, Any]]


@router.post("/meal-plan", response_model=MealPlanResponse)
async def generate_meal_plan(
    body: MealPlanRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a personalized multi-day meal plan based on full health context.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")
    ctx = await _gather_nutrition_context(user_id, bearer)
    context_text = _format_context_for_prompt(ctx)
    first_name = ctx.get("demographics", {}).get("first_name") or "there"
    targets = ctx.get("targets", {})

    prompt = f"""Generate a {body.days}-day meal plan for {first_name}.

USER CONTEXT:
{context_text}

Daily targets: {targets.get('calories', 2000)} cal, {targets.get('protein_g', 100)}g protein, {targets.get('carbs_g', 200)}g carbs, {targets.get('fat_g', 65)}g fat

Return ONLY valid JSON (no markdown fences):
{{
  "days": [
    {{
      "date": "Day 1",
      "meals": [
        {{
          "meal_type": "breakfast",
          "name": "Descriptive meal name",
          "ingredients": [{{"name": "ingredient", "portion": "amount", "unit": "unit"}}],
          "macros": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
          "prep_time_min": 15,
          "notes": "optional tip"
        }}
      ]
    }}
  ]
}}

Rules:
- Each day must have breakfast, lunch, dinner, and optionally a snack
- Daily totals must approximate the calorie/macro targets
- Must respect all dietary restrictions and allergies
- Prioritize nutrients flagged as low in labs
- If health conditions present, follow condition-specific nutrition guidelines
- If active experiment, ensure every day complies
- Vary meals across days — don't repeat the same meal
- Include specific portions (e.g. "6 oz salmon", "1 cup rice")
- Keep prep times realistic (most under 30 min)"""

    raw = await _call_claude(prompt, max_tokens=3000)

    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        parsed = json.loads(raw)
        days_list = parsed.get("days", [])
    except (json.JSONDecodeError, ValueError):
        days_list = []

    return MealPlanResponse(days=days_list)


# ---------------------------------------------------------------------------
# Session 7: Grocery list
# ---------------------------------------------------------------------------


class GroceryCategory(BaseModel):
    name: str
    items: List[Dict[str, Any]]


class GroceryListResponse(BaseModel):
    categories: List[GroceryCategory]


@router.post("/meal-plan/grocery-list", response_model=GroceryListResponse)
async def grocery_list(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a grocery list from the user's active meal plan.
    Aggregates ingredients, groups by category, combines quantities.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")
    ctx = await _gather_nutrition_context(user_id, bearer)

    # First generate or re-use the meal plan
    # For efficiency, caller should pass plan data — but as fallback, generate a 7-day plan
    plan_resp = await generate_meal_plan(MealPlanRequest(days=7), request, current_user)
    days_list = plan_resp.days

    if not days_list:
        return GroceryListResponse(categories=[])

    # Collect all ingredients
    all_ingredients: List[str] = []
    for day in days_list:
        for meal in day.get("meals", []):
            for ing in meal.get("ingredients", []):
                name = ing.get("name", "")
                portion = ing.get("portion", "")
                unit = ing.get("unit", "")
                if name:
                    all_ingredients.append(f"{portion} {unit} {name}".strip())

    if not all_ingredients:
        return GroceryListResponse(categories=[])

    dietary_text = ""
    prefs = ctx.get("dietary_prefs", {})
    if prefs.get("allergies"):
        dietary_text = (
            f"\nAllergies: {', '.join(prefs['allergies'])}. Exclude allergens."
        )

    prompt = f"""Given this ingredient list from a weekly meal plan, create an organized grocery list.

INGREDIENTS:
{chr(10).join(f'- {i}' for i in all_ingredients)}
{dietary_text}

Combine duplicate ingredients (e.g., multiple "chicken breast" entries → one combined quantity).
Group into categories.

Return ONLY valid JSON (no markdown fences):
{{
  "categories": [
    {{
      "name": "Produce",
      "items": [
        {{"name": "Broccoli", "quantity": "3 cups", "for_meals": ["Day 1 dinner", "Day 3 lunch"]}}
      ]
    }}
  ]
}}

Use these categories: Produce, Protein, Dairy & Eggs, Grains & Bread, Pantry Staples, Spices & Seasonings, Beverages, Other.
Only include categories that have items. Combine quantities smartly."""

    raw = await _call_claude(prompt, max_tokens=2000)

    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        parsed = json.loads(raw)
        categories = parsed.get("categories", [])
    except (json.JSONDecodeError, ValueError):
        categories = []

    return GroceryListResponse(
        categories=[
            GroceryCategory(name=c.get("name", "Other"), items=c.get("items", []))
            for c in categories
        ]
    )


# ---------------------------------------------------------------------------
# Session 8: Insight caching + nutrition summary for home screen
# ---------------------------------------------------------------------------


@router.get("/nutrition-summary")
async def nutrition_home_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Lightweight nutrition summary for the home screen card.
    Returns today's totals and targets without generating AI content.
    """
    user_id = current_user["id"]
    bearer = request.headers.get("Authorization")

    meals, targets = await asyncio.gather(
        _fetch_todays_meals(user_id, bearer),
        _fetch_nutrition_targets(user_id),
    )

    totals = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    meal_count = 0
    for m in meals:
        totals["calories"] += m.get("total_calories") or m.get("calories") or 0
        totals["protein_g"] += m.get("total_protein_g") or m.get("protein_g") or 0
        totals["carbs_g"] += m.get("total_carbs_g") or m.get("carbs_g") or 0
        totals["fat_g"] += m.get("total_fat_g") or m.get("fat_g") or 0
        meal_count += 1

    return {
        "meals_logged": meal_count,
        "totals": {k: round(v) for k, v in totals.items()},
        "targets": targets,
        "has_data": meal_count > 0,
    }


# ---------------------------------------------------------------------------
# Claude helper
# ---------------------------------------------------------------------------


async def _call_claude(prompt: str, max_tokens: int = 250) -> str:
    """Call Claude for a short generation."""
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Unable to generate insight — AI service not configured."

        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude call failed: %s", e)
        return "Great meal choice! Keep logging to get personalized insights."
