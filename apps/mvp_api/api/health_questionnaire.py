"""
Health Questionnaire — AI-Generated Health Questions

Generates personalized health questions based on the user's conditions,
data patterns, and existing profile. Stores responses in user_health_profile.
"""

# pylint: disable=broad-except,line-too-long

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get, _supabase_upsert

logger = get_logger(__name__)
router = APIRouter()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("QUESTIONNAIRE_AI_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class QuestionOption(BaseModel):
    value: str
    label: str


class HealthQuestion(BaseModel):
    id: str
    question: str
    type: str  # single_choice, multi_choice, text, scale
    category: str  # goals, diet, supplements, medications, lifestyle, condition_specific
    options: Optional[List[QuestionOption]] = None
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    required: bool = True


class QuestionnaireResponse(BaseModel):
    questions: List[HealthQuestion]
    profile_completed: bool
    sections: List[str]


class SubmitAnswersRequest(BaseModel):
    answers: Dict[str, Any]


class SubmitAnswersResponse(BaseModel):
    saved: bool
    profile_updated: bool
    message: str


class UserProfileResponse(BaseModel):
    health_goals: List[str]
    dietary_preferences: List[str]
    supplements: List[Dict[str, str]]
    medications: List[Dict[str, str]]
    questionnaire_completed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Default questions (fallback when AI not available)
# ---------------------------------------------------------------------------

DEFAULT_QUESTIONS: List[HealthQuestion] = [
    HealthQuestion(
        id="health_goals",
        question="What are your primary health goals?",
        type="multi_choice",
        category="goals",
        options=[
            QuestionOption(value="weight_loss", label="Lose weight"),
            QuestionOption(value="muscle_gain", label="Build muscle"),
            QuestionOption(value="better_sleep", label="Improve sleep quality"),
            QuestionOption(value="more_energy", label="Increase energy levels"),
            QuestionOption(value="reduce_stress", label="Reduce stress"),
            QuestionOption(value="improve_recovery", label="Improve workout recovery"),
            QuestionOption(value="manage_condition", label="Manage a health condition"),
            QuestionOption(value="general_wellness", label="General wellness"),
        ],
    ),
    HealthQuestion(
        id="dietary_preferences",
        question="Do you follow any dietary preferences or restrictions?",
        type="multi_choice",
        category="diet",
        options=[
            QuestionOption(value="none", label="No restrictions"),
            QuestionOption(value="vegetarian", label="Vegetarian"),
            QuestionOption(value="vegan", label="Vegan"),
            QuestionOption(value="gluten_free", label="Gluten-free"),
            QuestionOption(value="dairy_free", label="Dairy-free"),
            QuestionOption(value="keto", label="Keto / Low-carb"),
            QuestionOption(value="paleo", label="Paleo"),
            QuestionOption(value="mediterranean", label="Mediterranean"),
            QuestionOption(value="halal", label="Halal"),
            QuestionOption(value="kosher", label="Kosher"),
        ],
    ),
    HealthQuestion(
        id="supplements",
        question="Do you currently take any supplements? (List name and dose, or 'none')",
        type="text",
        category="supplements",
    ),
    HealthQuestion(
        id="medications",
        question="Are you currently taking any medications? (List name and dose, or 'none')",
        type="text",
        category="medications",
    ),
    HealthQuestion(
        id="sleep_habits",
        question="How would you rate your typical sleep quality?",
        type="single_choice",
        category="lifestyle",
        options=[
            QuestionOption(value="excellent", label="Excellent — I wake up refreshed"),
            QuestionOption(value="good", label="Good — Usually sleep well"),
            QuestionOption(value="fair", label="Fair — Some trouble sleeping"),
            QuestionOption(value="poor", label="Poor — Frequent sleep issues"),
        ],
    ),
    HealthQuestion(
        id="stress_level",
        question="How would you rate your current stress level?",
        type="scale",
        category="lifestyle",
        scale_min=1,
        scale_max=10,
    ),
    HealthQuestion(
        id="exercise_frequency",
        question="How often do you exercise?",
        type="single_choice",
        category="lifestyle",
        options=[
            QuestionOption(value="daily", label="Daily"),
            QuestionOption(value="4_6_week", label="4-6 times per week"),
            QuestionOption(value="2_3_week", label="2-3 times per week"),
            QuestionOption(value="1_week", label="Once a week"),
            QuestionOption(value="rarely", label="Rarely"),
        ],
    ),
    HealthQuestion(
        id="meal_timing",
        question="What time do you typically eat your last meal?",
        type="single_choice",
        category="lifestyle",
        options=[
            QuestionOption(value="before_6pm", label="Before 6 PM"),
            QuestionOption(value="6_7pm", label="6-7 PM"),
            QuestionOption(value="7_8pm", label="7-8 PM"),
            QuestionOption(value="8_9pm", label="8-9 PM"),
            QuestionOption(value="after_9pm", label="After 9 PM"),
        ],
    ),
]


# ---------------------------------------------------------------------------
# AI question generation
# ---------------------------------------------------------------------------


async def _generate_ai_questions(
    conditions: List[Dict[str, Any]],
    existing_profile: Optional[Dict[str, Any]],
) -> List[HealthQuestion]:
    """Generate personalized questions based on conditions and profile."""
    if not OPENAI_API_KEY:
        return _add_condition_questions(DEFAULT_QUESTIONS, conditions)

    condition_names = [
        c.get("condition_name", "") for c in conditions if c.get("condition_name")
    ]

    profile_context = ""
    if existing_profile:
        goals = existing_profile.get("health_goals") or []
        if isinstance(goals, str):
            try:
                goals = json.loads(goals)
            except (json.JSONDecodeError, TypeError):
                goals = []
        if goals:
            profile_context = f"\nExisting goals: {', '.join(goals)}"

    prompt = f"""Generate 3-4 personalized health questions for a user with these conditions: {', '.join(condition_names) if condition_names else 'None specified'}.
{profile_context}

Generate questions that help understand their condition management, triggers, and lifestyle factors relevant to their conditions. Questions should be specific to their conditions.

Respond in JSON:
{{
  "questions": [
    {{
      "id": "unique_id",
      "question": "The question text",
      "type": "single_choice|multi_choice|text|scale",
      "category": "condition_specific",
      "options": [{{"value": "opt1", "label": "Option 1"}}]
    }}
  ]
}}

For scale type, use scale_min: 1, scale_max: 10.
For text type, omit options.
Keep questions practical and non-diagnostic."""

    try:
        timeout = aiohttp.ClientTimeout(total=12)
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
                    logger.warning("OpenAI returned %s for questionnaire", resp.status)
                    return _add_condition_questions(DEFAULT_QUESTIONS, conditions)
                result = await resp.json()

        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        ai_questions: List[HealthQuestion] = []
        for q in parsed.get("questions", []):
            options = None
            if q.get("options"):
                options = [
                    QuestionOption(value=o.get("value", ""), label=o.get("label", ""))
                    for o in q["options"]
                ]
            ai_questions.append(
                HealthQuestion(
                    id=q.get("id", f"ai_{len(ai_questions)}"),
                    question=q.get("question", ""),
                    type=q.get("type", "text"),
                    category=q.get("category", "condition_specific"),
                    options=options,
                    scale_min=q.get("scale_min"),
                    scale_max=q.get("scale_max"),
                )
            )

        # Combine default + AI questions
        return DEFAULT_QUESTIONS + ai_questions

    except Exception as exc:
        logger.warning("AI questionnaire generation failed: %s", exc)
        return _add_condition_questions(DEFAULT_QUESTIONS, conditions)


def _add_condition_questions(
    base: List[HealthQuestion],
    conditions: List[Dict[str, Any]],
) -> List[HealthQuestion]:
    """Add condition-specific questions without AI."""
    extra = list(base)
    for cond in conditions:
        name = cond.get("condition_name", "")
        if not name:
            continue
        extra.append(
            HealthQuestion(
                id=f"condition_trigger_{name.lower().replace(' ', '_')}",
                question=f"What triggers or worsens your {name}?",
                type="text",
                category="condition_specific",
            )
        )
    return extra


# ---------------------------------------------------------------------------
# Profile helpers
# ---------------------------------------------------------------------------


async def _get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    rows = await _supabase_get(
        "user_health_profile",
        f"user_id=eq.{user_id}&select=*&limit=1",
    )
    if rows and isinstance(rows, list):
        return rows[0]
    return None


async def _save_profile(user_id: str, data: Dict[str, Any]) -> bool:
    result = await _supabase_upsert(
        "user_health_profile",
        {
            "user_id": user_id,
            **data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return result is not None


def _parse_json_field(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=QuestionnaireResponse)
async def get_questionnaire(
    current_user: dict = Depends(get_current_user),
):
    """
    Get personalized health questionnaire.
    Questions are tailored to user's conditions and existing profile.
    """
    user_id = current_user["id"]

    # Fetch conditions and existing profile
    conditions_rows = await _supabase_get(
        "health_conditions",
        f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name,condition_category",
    )
    conditions = conditions_rows if isinstance(conditions_rows, list) else []

    profile = await _get_profile(user_id)
    completed = bool(profile and profile.get("questionnaire_completed_at"))

    questions = await _generate_ai_questions(conditions, profile)

    sections = list(dict.fromkeys(q.category for q in questions))

    return QuestionnaireResponse(
        questions=questions,
        profile_completed=completed,
        sections=sections,
    )


@router.post("", response_model=SubmitAnswersResponse)
async def submit_questionnaire(
    body: SubmitAnswersRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit questionnaire answers. Updates user_health_profile.
    """
    user_id = current_user["id"]
    answers = body.answers

    # Map answers to profile fields
    profile_data: Dict[str, Any] = {}

    if "health_goals" in answers:
        goals = answers["health_goals"]
        if isinstance(goals, str):
            goals = [goals]
        profile_data["health_goals"] = json.dumps(goals)

    if "dietary_preferences" in answers:
        prefs = answers["dietary_preferences"]
        if isinstance(prefs, str):
            prefs = [prefs]
        profile_data["dietary_preferences"] = json.dumps(prefs)

    if "supplements" in answers:
        supp_raw = answers["supplements"]
        if isinstance(supp_raw, str):
            # Parse "Vitamin D 2000IU, Magnesium 400mg" format
            supplements = []
            if supp_raw.lower().strip() not in ("none", "n/a", ""):
                for item in supp_raw.split(","):
                    item = item.strip()
                    if item:
                        supplements.append(
                            {"name": item, "dose": "", "frequency": "daily"}
                        )
            profile_data["supplements"] = json.dumps(supplements)
        elif isinstance(supp_raw, list):
            profile_data["supplements"] = json.dumps(supp_raw)

    if "medications" in answers:
        med_raw = answers["medications"]
        if isinstance(med_raw, str):
            medications = []
            if med_raw.lower().strip() not in ("none", "n/a", ""):
                for item in med_raw.split(","):
                    item = item.strip()
                    if item:
                        medications.append(
                            {"name": item, "dose": "", "frequency": "daily"}
                        )
            profile_data["medications"] = json.dumps(medications)
        elif isinstance(med_raw, list):
            profile_data["medications"] = json.dumps(med_raw)

    # Store all answers as questionnaire_responses
    profile_data["questionnaire_responses"] = json.dumps(answers)
    profile_data["questionnaire_completed_at"] = datetime.now(timezone.utc).isoformat()

    saved = await _save_profile(user_id, profile_data)

    return SubmitAnswersResponse(
        saved=saved,
        profile_updated=saved,
        message="Health profile updated successfully"
        if saved
        else "Failed to save profile",
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_health_profile(
    current_user: dict = Depends(get_current_user),
):
    """Get the user's health profile summary."""
    user_id = current_user["id"]
    profile = await _get_profile(user_id)

    if not profile:
        return UserProfileResponse(
            health_goals=[],
            dietary_preferences=[],
            supplements=[],
            medications=[],
        )

    return UserProfileResponse(
        health_goals=_parse_json_field(profile.get("health_goals")) or [],
        dietary_preferences=_parse_json_field(profile.get("dietary_preferences")) or [],
        supplements=_parse_json_field(profile.get("supplements")) or [],
        medications=_parse_json_field(profile.get("medications")) or [],
        questionnaire_completed_at=profile.get("questionnaire_completed_at"),
    )
