"""
Onboarding API — Closed-Loop-Integrated New User Flow

Powers the redesigned onboarding: intent selection, condition/goal picking,
specialist activation, journey proposal, quick context collection,
smart prompts, and data completeness scoring.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_insert,
    _supabase_upsert,
    _supabase_patch,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class IntentRequest(BaseModel):
    intent: str  # "condition" | "goal" | "exploring"


class SelectRequest(BaseModel):
    type: str  # "condition" | "goal"
    value: str  # e.g. "pcos", "weight_loss"


class ContextRequest(BaseModel):
    answers: Dict[str, Any]
    # e.g. { "medications": "Metformin 500mg", "cycle_tracking": "yes",
    #        "last_period_date": "2026-03-10", "dietary_preferences": ["gluten-free"] }


class StartJourneyRequest(BaseModel):
    journey_template_key: Optional[str] = None  # override proposed_journey_key


class CompleteRequest(BaseModel):
    skipped_journey: bool = False


class SmartPrompt(BaseModel):
    type: str  # device|medications|cycle|labs|meals|symptoms
    title: str
    body: str
    action: str  # screen to navigate to
    priority: int


class DataCompleteness(BaseModel):
    score: int
    level: str  # getting_started|building|almost_there|great
    breakdown: Dict[str, bool]


# ---------------------------------------------------------------------------
# Condition/goal picker options
# ---------------------------------------------------------------------------

CONDITION_CATEGORIES = {
    "Metabolic": [
        "Type 2 Diabetes",
        "PCOS",
        "Hypothyroidism",
        "Prediabetes",
        "Metabolic Syndrome",
        "Hyperthyroidism",
    ],
    "Heart & Blood": [
        "Hypertension",
        "High Cholesterol",
        "Heart Disease",
        "Atrial Fibrillation",
    ],
    "Digestive": [
        "IBS",
        "IBD / Crohn's",
        "GERD",
        "Celiac Disease",
        "SIBO",
        "Food Sensitivities",
    ],
    "Mental Health": ["Anxiety", "Depression", "Insomnia", "ADHD", "PTSD"],
    "Women's Health": ["Perimenopause", "Endometriosis", "PMS / PMDD", "Menopause"],
    "Autoimmune & Pain": [
        "Rheumatoid Arthritis",
        "Fibromyalgia",
        "Lupus",
        "Chronic Pain",
        "Migraine",
    ],
    "Respiratory": ["Asthma", "COPD", "Sleep Apnea"],
    "Other": ["Kidney Disease", "Cancer Support", "Eczema / Psoriasis"],
}

GOAL_OPTIONS = [
    {"value": "sleep_optimization", "label": "Sleep better", "icon": "moon"},
    {"value": "weight_loss", "label": "Lose weight", "icon": "scale"},
    {"value": "muscle_building", "label": "Build muscle", "icon": "dumbbell"},
    {"value": "mental_health", "label": "Reduce stress", "icon": "brain"},
    {"value": "general_wellness", "label": "More energy", "icon": "zap"},
    {"value": "cardiac_rehab", "label": "Heart health", "icon": "heart"},
]

# Map condition display names to specialist-config keys
CONDITION_KEY_MAP: Dict[str, str] = {
    "Type 2 Diabetes": "type_2_diabetes",
    "PCOS": "pcos",
    "Hypothyroidism": "hypothyroidism",
    "Hyperthyroidism": "hyperthyroidism",
    "Prediabetes": "prediabetes",
    "Metabolic Syndrome": "metabolic_syndrome",
    "Hypertension": "hypertension",
    "High Cholesterol": "high_cholesterol",
    "Heart Disease": "coronary_artery_disease",
    "Atrial Fibrillation": "afib",
    "IBS": "ibs",
    "IBD / Crohn's": "ibd",
    "GERD": "gerd",
    "Celiac Disease": "celiac_disease",
    "SIBO": "sibo",
    "Food Sensitivities": "food_intolerances",
    "Anxiety": "anxiety",
    "Depression": "depression",
    "Insomnia": "insomnia",
    "ADHD": "adhd",
    "PTSD": "ptsd",
    "Perimenopause": "perimenopause",
    "Endometriosis": "endometriosis",
    "PMS / PMDD": "pmdd",
    "Menopause": "menopause",
    "Rheumatoid Arthritis": "rheumatoid_arthritis",
    "Fibromyalgia": "fibromyalgia",
    "Lupus": "lupus",
    "Chronic Pain": "chronic_pain",
    "Migraine": "migraine",
    "Asthma": "asthma",
    "COPD": "copd",
    "Sleep Apnea": "sleep_apnea",
    "Kidney Disease": "ckd",
    "Cancer Support": "cancer",
    "Eczema / Psoriasis": "psoriasis",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_hormonal_condition(condition: Optional[str]) -> bool:
    if not condition:
        return False
    return condition.lower() in (
        "pcos",
        "perimenopause",
        "menopause",
        "endometriosis",
        "pms",
        "pmdd",
        "hypothyroidism",
        "hyperthyroidism",
    )


async def _compute_completeness(user_id: str) -> DataCompleteness:
    """Calculate data completeness score for a user."""
    breakdown: Dict[str, bool] = {}

    # Device (20 pts)
    oura = await _supabase_get(
        "oura_connections", f"user_id=eq.{user_id}&is_active=eq.true&limit=1"
    )
    breakdown["device"] = bool(oura)

    # Conditions (15 pts)
    conditions = await _supabase_get(
        "health_conditions", f"user_id=eq.{user_id}&is_active=eq.true&limit=1"
    )
    breakdown["conditions"] = bool(conditions)

    # Medications (15 pts)
    meds = await _supabase_get(
        "medications", f"user_id=eq.{user_id}&is_active=eq.true&limit=1"
    )
    breakdown["medications"] = bool(meds)

    # Dietary preferences (10 pts)
    profile = await _supabase_get(
        "user_health_profile", f"user_id=eq.{user_id}&limit=1"
    )
    prefs = (profile[0].get("dietary_preferences") if profile else None) or []
    if isinstance(prefs, str):
        try:
            prefs = json.loads(prefs)
        except Exception:
            prefs = []
    breakdown["dietary"] = bool(prefs)

    # Labs (10 pts)
    labs = await _supabase_get("lab_results", f"user_id=eq.{user_id}&limit=1")
    breakdown["labs"] = bool(labs)

    # Cycle data (10 pts — only counted if female/hormonal condition)
    cycle = await _supabase_get("cycle_logs", f"user_id=eq.{user_id}&limit=1")
    breakdown["cycle"] = bool(cycle)

    # 7+ days health data (10 pts)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    health_data = await _supabase_get(
        "native_health_data",
        f"user_id=eq.{user_id}&created_at=gte.{cutoff}&limit=1",
    )
    if not health_data:
        # Try oura timeline
        health_data = await _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&limit=1",
        )
    breakdown["health_data_7d"] = bool(health_data)

    # Meals (5 pts)
    meals = await _supabase_get("meal_entries", f"user_id=eq.{user_id}&limit=1")
    if not meals:
        meals = await _supabase_get("nutrition_logs", f"user_id=eq.{user_id}&limit=1")
    breakdown["meals"] = bool(meals)

    # Symptoms (5 pts)
    symptoms = await _supabase_get("symptom_entries", f"user_id=eq.{user_id}&limit=1")
    breakdown["symptoms"] = bool(symptoms)

    # Score
    weights = {
        "device": 20,
        "conditions": 15,
        "medications": 15,
        "dietary": 10,
        "labs": 10,
        "cycle": 10,
        "health_data_7d": 10,
        "meals": 5,
        "symptoms": 5,
    }
    score = sum(weights[k] for k, v in breakdown.items() if v)

    level = (
        "great"
        if score >= 80
        else "almost_there"
        if score >= 60
        else "building"
        if score >= 30
        else "getting_started"
    )

    return DataCompleteness(score=score, level=level, breakdown=breakdown)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


async def _ensure_profile(user_id: str, current_user: dict) -> None:
    """Create profile row if it doesn't exist (bypasses RLS via service role)."""
    existing = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
    if not existing:
        name = (
            (current_user.get("user_metadata") or {}).get("full_name")
            or (current_user.get("user_metadata") or {}).get("name")
            or current_user.get("email", "").split("@")[0]
        )
        await _supabase_upsert(
            "profiles",
            {
                "id": user_id,
                "full_name": name,
                "user_role": "patient",
            },
        )
        logger.info("Created profile for user %s (%s)", user_id, name)


@router.post("/intent")
async def set_intent(
    body: IntentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Step 2: User selects their intent (condition/goal/exploring)."""
    user_id = current_user["id"]

    # Ensure profile exists (signup may not have created it due to RLS)
    await _ensure_profile(user_id, current_user)

    await _supabase_patch(
        "profiles",
        f"id=eq.{user_id}",
        {
            "onboarding_intent": body.intent,
            "user_role": "patient",  # condition/goal → patient role
        },
    )

    if body.intent == "condition":
        return {"intent": "condition", "categories": CONDITION_CATEGORIES}
    elif body.intent == "goal":
        return {"intent": "goal", "options": GOAL_OPTIONS}
    else:
        # Exploring — activate health coach, skip to device step
        await _supabase_patch(
            "profiles",
            f"id=eq.{user_id}",
            {"specialist_agent_type": "health_coach"},
        )
        return {
            "intent": "exploring",
            "specialist": {
                "agent_type": "health_coach",
                "agent_name": "Health Coach",
                "specialty": "General Wellness",
                "description": "Your personal health and wellness guide.",
            },
            "quick_questions": [],
        }


@router.post("/select")
async def select_condition_or_goal(
    body: SelectRequest,
    current_user: dict = Depends(get_current_user),
):
    """Step 3: User picks a condition or goal. Activates specialist + returns journey proposal."""
    from ..agents.specialist_configs import (
        get_specialist_for_condition,
        get_specialist_for_goal,
    )
    from ..agents.journey_templates import get_template
    from ..agents.onboarding_questions import (
        get_questions_for_condition,
        get_questions_for_goal,
    )

    user_id = current_user["id"]
    await _ensure_profile(user_id, current_user)
    value = body.value.strip()

    if body.type == "condition":
        # Normalize condition name to key
        condition_key = CONDITION_KEY_MAP.get(
            value, value.lower().replace(" ", "_").replace("-", "_")
        )

        # Store in profile
        await _supabase_patch(
            "profiles",
            f"id=eq.{user_id}",
            {"primary_condition": condition_key},
        )

        # Insert into health_conditions
        await _supabase_upsert(
            "health_conditions",
            {
                "user_id": user_id,
                "condition_name": value,
                "condition_category": _guess_category(value),
                "is_active": True,
            },
        )

        # Find specialist
        agent = get_specialist_for_condition(condition_key)
        specialist_type = agent["agent_type"] if agent else "health_coach"

        # Find template
        template = get_template(condition_key)
        journey_key = condition_key if template else None

        # Get quick questions
        questions = get_questions_for_condition(condition_key)

    else:  # goal
        goal_key = value.lower().replace(" ", "_").replace("-", "_")

        await _supabase_patch(
            "profiles",
            f"id=eq.{user_id}",
            {"primary_goal": goal_key},
        )

        agent = get_specialist_for_goal(goal_key)
        specialist_type = agent["agent_type"] if agent else "health_coach"

        template = get_template(goal_key)
        journey_key = goal_key if template else None

        questions = get_questions_for_goal(goal_key)

    # Store specialist + journey key
    await _supabase_patch(
        "profiles",
        f"id=eq.{user_id}",
        {
            "specialist_agent_type": specialist_type,
            "proposed_journey_key": journey_key,
        },
    )

    # Build response
    specialist_info = None
    if agent:
        specialist_info = {
            "agent_type": agent["agent_type"],
            "agent_name": agent["agent_name"],
            "specialty": agent["specialty"],
            "description": agent["description"],
        }

    journey_proposal = None
    if template:
        journey_proposal = {
            "key": journey_key,
            "title": template["title"],
            "goal_type": template["goal_type"],
            "duration_type": template["duration_type"],
            "target_metrics": template["target_metrics"],
            "phases": [
                {
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "phase_type": p.get("phase_type", "intervention"),
                }
                for p in template["phases"]
            ],
            "total_phases": len(template["phases"]),
        }

    return {
        "specialist": specialist_info,
        "journey_proposal": journey_proposal,
        "quick_questions": questions,
    }


@router.post("/context")
async def save_context(
    body: ContextRequest,
    current_user: dict = Depends(get_current_user),
):
    """Step 4: Save quick context answers."""
    user_id = current_user["id"]
    answers = body.answers

    # Build profile update
    profile_update: Dict[str, Any] = {}

    if "medications" in answers and answers["medications"]:
        # Parse simple medication text into structured format
        med_text = answers["medications"]
        if isinstance(med_text, str) and med_text.lower() not in (
            "no",
            "none",
            "skip",
            "",
        ):
            meds = [{"name": m.strip(), "is_active": True} for m in med_text.split(",")]
            profile_update["medications"] = meds

    if "dietary_preferences" in answers:
        prefs = answers["dietary_preferences"]
        if isinstance(prefs, list):
            prefs = [p for p in prefs if p.lower() not in ("none", "other")]
        profile_update["dietary_preferences"] = prefs

    if "supplements" in answers and answers["supplements"]:
        supp_text = answers["supplements"]
        if isinstance(supp_text, str) and supp_text.lower() not in (
            "no",
            "none",
            "skip",
            "",
        ):
            supps = [{"name": s.strip()} for s in supp_text.split(",")]
            profile_update["supplements"] = supps

    # Store answers in questionnaire_responses for anything else
    profile_update["questionnaire_responses"] = answers

    if profile_update:
        await _supabase_upsert(
            "user_health_profile",
            {"user_id": user_id, **profile_update},
        )

    # Handle cycle tracking
    if answers.get("cycle_tracking") in ("Yes, regularly", "Sometimes"):
        last_period = answers.get("last_period_date")
        if last_period:
            await _supabase_upsert(
                "cycle_logs",
                {
                    "user_id": user_id,
                    "event_type": "period_start",
                    "event_date": last_period,
                },
            )

    # Handle weight goals
    if "weight_goals" in answers:
        wg = answers["weight_goals"]
        if isinstance(wg, dict):
            current_w = wg.get("current")
            goal_w = wg.get("goal")
            if current_w:
                # Convert lbs to kg if needed (assume lbs input)
                weight_kg = (
                    float(current_w) * 0.453592
                    if float(current_w) > 100
                    else float(current_w)
                )
                await _supabase_patch(
                    "profiles",
                    f"id=eq.{user_id}",
                    {"weight_kg": round(weight_kg, 1)},
                )

    return {"stored": True}


@router.post("/start-journey")
async def start_journey(
    body: StartJourneyRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Step 6 'Start My Journey': Create journey from template and complete onboarding."""
    from ..agents.journey_templates import get_template
    from .journeys import create_journey, CreateJourneyRequest, PhaseDefinition

    user_id = current_user["id"]

    # Get journey key
    journey_key = body.journey_template_key
    if not journey_key:
        profile = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
        journey_key = profile[0].get("proposed_journey_key") if profile else None

    if not journey_key:
        raise HTTPException(status_code=400, detail="No journey template specified")

    template = get_template(journey_key)
    if not template:
        raise HTTPException(
            status_code=404, detail=f"Journey template '{journey_key}' not found"
        )

    # Get specialist
    profile = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
    specialist_type = profile[0].get("specialist_agent_type") if profile else None

    # Build journey request from template
    phases = [
        PhaseDefinition(
            name=p["name"],
            description=p.get("description", ""),
            phase_type=p.get("phase_type", "intervention"),
            duration_days_estimate=p.get("duration_days_estimate", 30),
            duration_type=p.get("duration_type", "fixed"),
            experiment=p.get("experiment"),
            tracked_metrics=p.get("tracked_metrics", []),
            checkpoints=p.get("checkpoints", []),
        )
        for p in template["phases"]
    ]

    journey_body = CreateJourneyRequest(
        title=template["title"],
        condition=journey_key,
        goal_type=template["goal_type"],
        specialist_agent_id=specialist_type,
        duration_type=template["duration_type"],
        target_metrics=template.get("target_metrics", []),
        phases=phases,
    )

    result = await create_journey(journey_body, request, current_user)

    # Mark onboarding complete
    await _supabase_patch(
        "profiles",
        f"id=eq.{user_id}",
        {"onboarding_completed_at": datetime.now(timezone.utc).isoformat()},
    )

    # Schedule specialist onboarding conversation nudges (days 1-7)
    await _schedule_onboarding_conversation(user_id, specialist_type)

    # Schedule welcome nudge
    from .nudges import _get_user_tokens, _send_expo_push

    tokens = await _get_user_tokens(user_id)
    if tokens:
        await _send_expo_push(
            tokens=tokens,
            title="Welcome to your health journey!",
            body=f"Your {template['title']} plan is ready. Open Vitalix to get started.",
            data={"screen": "home"},
        )

    return {"journey": result, "onboarding_completed": True}


@router.post("/complete")
async def complete_onboarding(
    body: CompleteRequest,
    current_user: dict = Depends(get_current_user),
):
    """Complete onboarding without starting a journey ('Maybe Later')."""
    user_id = current_user["id"]

    await _supabase_patch(
        "profiles",
        f"id=eq.{user_id}",
        {"onboarding_completed_at": datetime.now(timezone.utc).isoformat()},
    )

    # Still schedule specialist conversation even without journey
    profile = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
    specialist_type = profile[0].get("specialist_agent_type") if profile else None
    if specialist_type:
        await _schedule_onboarding_conversation(user_id, specialist_type)

    return {"completed": True, "skipped_journey": body.skipped_journey}


# ---------------------------------------------------------------------------
# Smart Prompts
# ---------------------------------------------------------------------------


@router.get("/smart-prompt")
async def get_smart_prompt(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns the single highest-priority missing data action for this user.
    Used by the contextual action card on Home.
    """
    user_id = current_user["id"]

    # Ensure profile exists
    await _ensure_profile(user_id, current_user)

    # Get user profile for context
    profile_rows = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
    profile = profile_rows[0] if profile_rows else {}
    specialist = profile.get("specialist_agent_type", "Health Coach")
    condition = profile.get("primary_condition", "")

    # Get recent dismissals
    dismissals = await _supabase_get(
        "smart_prompt_dismissals",
        f"user_id=eq.{user_id}&select=prompt_type,dismissed_at",
    )
    dismissed_recently = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    for d in dismissals or []:
        try:
            dt = datetime.fromisoformat(d["dismissed_at"].replace("Z", "+00:00"))
            if dt > cutoff:
                dismissed_recently.add(d["prompt_type"])
        except Exception:
            pass

    # Check what exists
    prompts: List[SmartPrompt] = []

    specialist_name = (
        specialist.replace("_", " ").title() if specialist else "Health Coach"
    )

    # Device — check both oura_connections AND native health data
    oura = await _supabase_get(
        "oura_connections", f"user_id=eq.{user_id}&is_active=eq.true&limit=1"
    )
    health_data = await _supabase_get(
        "native_health_data", f"user_id=eq.{user_id}&limit=1"
    )
    has_device = bool(oura) or bool(health_data)
    if not has_device and "device" not in dismissed_recently:
        prompts.append(
            SmartPrompt(
                type="device",
                title="Connect your wearable",
                body=f"Your {specialist_name} needs sleep and HRV data to start analyzing patterns.",
                action="devices",
                priority=100,
            )
        )

    # Medications (for condition users)
    if condition:
        meds = await _supabase_get(
            "medications", f"user_id=eq.{user_id}&is_active=eq.true&limit=1"
        )
        if not meds and "medications" not in dismissed_recently:
            prompts.append(
                SmartPrompt(
                    type="medications",
                    title="Add your medications",
                    body="Helps check interactions and track adherence.",
                    action="medications",
                    priority=90,
                )
            )

    # Cycle (for hormonal conditions)
    if _is_hormonal_condition(condition):
        cycle = await _supabase_get("cycle_logs", f"user_id=eq.{user_id}&limit=1")
        if not cycle and "cycle" not in dismissed_recently:
            prompts.append(
                SmartPrompt(
                    type="cycle",
                    title="Track your cycle",
                    body="Enables cycle-aware experiment results and phase-specific recommendations.",
                    action="cycle",
                    priority=85,
                )
            )

    # Labs (for condition users)
    if condition:
        labs = await _supabase_get("lab_results", f"user_id=eq.{user_id}&limit=1")
        if not labs and "labs" not in dismissed_recently:
            prompts.append(
                SmartPrompt(
                    type="labs",
                    title="Add recent lab results",
                    body="Sets your health baseline for tracking progress.",
                    action="lab-results",
                    priority=80,
                )
            )

    # Meals — always relevant (not just after 2 days)
    if "meals" not in dismissed_recently:
        meals = await _supabase_get("meal_entries", f"user_id=eq.{user_id}&limit=1")
        if not meals:
            meals = await _supabase_get(
                "nutrition_logs", f"user_id=eq.{user_id}&limit=1"
            )
        if not meals:
            prompts.append(
                SmartPrompt(
                    type="meals",
                    title="Log your first meal",
                    body=f"Your {specialist_name} can find food-health connections once you start logging.",
                    action="nutrition",
                    priority=70 if has_device else 55,
                )
            )

    # Symptoms (for condition users, or after 3 days for everyone)
    days_since = 0
    try:
        created = profile.get("created_at", "")
        if created:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            days_since = (datetime.now(timezone.utc) - dt).days
    except Exception:
        pass

    show_symptoms = condition or days_since >= 3
    if show_symptoms and "symptoms" not in dismissed_recently:
        symptoms = await _supabase_get(
            "symptom_entries", f"user_id=eq.{user_id}&limit=1"
        )
        if not symptoms:
            prompts.append(
                SmartPrompt(
                    type="symptoms",
                    title="Track a symptom",
                    body="Helps identify triggers and patterns.",
                    action="symptoms",
                    priority=50,
                )
            )

    # Chat with specialist — show if user has device data but no meals/symptoms yet
    if has_device and not prompts and "chat" not in dismissed_recently:
        prompts.append(
            SmartPrompt(
                type="chat",
                title=f"Talk to your {specialist_name}",
                body="Ask about your health data, get personalized recommendations, or discuss your goals.",
                action="chat",
                priority=65,
            )
        )

    # Return highest priority
    prompts.sort(key=lambda p: p.priority, reverse=True)
    if prompts:
        return prompts[0]
    return None


@router.post("/smart-prompt/{prompt_type}/dismiss")
async def dismiss_prompt(
    prompt_type: str,
    current_user: dict = Depends(get_current_user),
):
    """Dismiss a smart prompt for 3 days."""
    user_id = current_user["id"]
    await _supabase_upsert(
        "smart_prompt_dismissals",
        {
            "user_id": user_id,
            "prompt_type": prompt_type,
            "dismissed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {"dismissed": prompt_type}


@router.get("/journey-proposal")
async def get_journey_proposal(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns the pending journey proposal for users who tapped 'Maybe Later'
    or whose journey creation failed. Returns null if no proposal or journey already active.
    """
    from ..agents.specialist_configs import SPECIALIST_AGENTS
    from ..agents.journey_templates import get_template

    user_id = current_user["id"]

    # Check if active journey exists — if so, no proposal needed
    active = await _supabase_get(
        "goal_journeys", f"user_id=eq.{user_id}&status=eq.active&limit=1"
    )
    if active:
        return None

    profile = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
    if not profile:
        return None

    p = profile[0]
    journey_key = p.get("proposed_journey_key")
    specialist_type = p.get("specialist_agent_type")

    if not journey_key or not specialist_type or specialist_type == "health_coach":
        return None

    template = get_template(journey_key)
    agent = SPECIALIST_AGENTS.get(specialist_type)

    if not template or not agent:
        return None

    return {
        "journey_key": journey_key,
        "specialist": {
            "agent_type": agent["agent_type"],
            "agent_name": agent["agent_name"],
            "specialty": agent["specialty"],
        },
        "journey": {
            "title": template["title"],
            "phases": [{"name": ph["name"]} for ph in template["phases"]],
            "total_phases": len(template["phases"]),
        },
    }


@router.get("/data-completeness", response_model=DataCompleteness)
async def get_data_completeness(
    current_user: dict = Depends(get_current_user),
):
    """Get the user's data completeness score and breakdown."""
    return await _compute_completeness(current_user["id"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _guess_category(condition_name: str) -> str:
    """Guess the condition category from the condition name."""
    for cat, conditions in CONDITION_CATEGORIES.items():
        if condition_name in conditions:
            return cat.lower().replace(" & ", "_").replace(" ", "_")
    return "other"


async def _schedule_onboarding_conversation(
    user_id: str,
    specialist_type: Optional[str],
) -> int:
    """
    Schedule specialist onboarding questions as nudges over days 1-7.
    Questions that correspond to already-existing data are skipped.
    """
    from ..agents.onboarding_conversation import get_onboarding_schedule
    from datetime import time as dt_time

    if not specialist_type:
        return 0

    schedule = get_onboarding_schedule(specialist_type)
    now = datetime.now(timezone.utc)
    count = 0

    for q in schedule:
        day = q.get("day", 1)
        nudge_date = now + timedelta(days=day)
        scheduled_for = datetime.combine(
            nudge_date.date(), dt_time(14, 0), tzinfo=timezone.utc
        )  # ~9am EST

        # Check if data already exists (skip if so)
        check_table = q.get("check_table")
        if check_table:
            check_query = q.get("check_query", "").replace("{user_id}", user_id)
            existing = await _supabase_get(check_table, check_query)
            if existing:
                continue

        result = await _supabase_insert(
            "nudge_queue",
            {
                "user_id": user_id,
                "nudge_type": q.get("nudge_type", "experiment_morning"),
                "title": q["title"],
                "body": q["body"],
                "data": {
                    "screen": "home",
                    "data_field": q.get("data_field", ""),
                    "specialist": specialist_type,
                },
                "scheduled_for": scheduled_for.isoformat(),
                "status": "pending",
            },
        )
        if result:
            count += 1

    logger.info(
        "Scheduled %d onboarding conversation nudges for user=%s specialist=%s",
        count,
        user_id,
        specialist_type,
    )
    return count
