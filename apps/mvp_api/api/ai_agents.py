"""
AI Agents Multi-Agent System API

Pro+ feature for conversational AI health assistants with specialized agents
that work together to provide personalized health insights.

Phase 3 of Health Intelligence Features
"""

import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_upsert,
    _supabase_patch,
)

logger = get_logger(__name__)
router = APIRouter()

# Anthropic configuration (set ANTHROPIC_API_KEY in your deployment environment, e.g. Render dashboard)
_DEFAULT_MODEL = "claude-sonnet-4-6"


def _get_anthropic_key() -> str:
    """Read the API key at call time so .env loaded after import is picked up."""
    return (os.environ.get("ANTHROPIC_API_KEY") or "").strip()


# Keep module-level alias for backward compat — re-evaluated each reference via the function
ANTHROPIC_API_KEY = _get_anthropic_key()

# ============================================================================
# DEFAULT AGENTS — used as fallback when Supabase is unavailable or empty
# ============================================================================
_DEFAULT_AGENTS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "agent_type": "health_coach",
        "agent_name": "Health Coach",
        "agent_description": "Your personal health and wellness guide",
        "capabilities": ["general_health_advice", "goal_setting", "motivation", "lifestyle_recommendations"],
        "system_prompt": "You are a compassionate and knowledgeable health coach. Help users set realistic health goals, provide evidence-based wellness advice, and offer motivation and support. Always encourage users to consult healthcare professionals for medical decisions.",
        "model": _DEFAULT_MODEL,
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "agent_type": "nutrition_analyst",
        "agent_name": "Nutrition Analyst",
        "agent_description": "Expert in nutrition patterns and meal planning",
        "capabilities": ["nutrition_analysis", "meal_planning", "dietary_recommendations", "nutrient_tracking"],
        "system_prompt": "You are a nutrition expert specializing in analyzing eating patterns and providing personalized meal recommendations. Use data from the user's meal logs and health metrics to identify patterns and suggest improvements. Be specific and actionable in your advice.",
        "model": _DEFAULT_MODEL,
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "agent_type": "symptom_investigator",
        "agent_name": "Symptom Investigator",
        "agent_description": "Analyzes symptoms and identifies patterns",
        "capabilities": ["symptom_analysis", "pattern_recognition", "correlation_detection", "medical_information"],
        "system_prompt": "You are a medical data analyst specializing in symptom pattern recognition. Help users understand their symptoms by analyzing trends, correlations with lifestyle factors, and potential triggers. Always recommend consulting healthcare professionals for diagnosis and treatment.",
        "model": _DEFAULT_MODEL,
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "agent_type": "research_assistant",
        "agent_name": "Research Assistant",
        "agent_description": "Finds and synthesizes medical research",
        "capabilities": ["literature_search", "research_synthesis", "evidence_summary", "study_interpretation"],
        "system_prompt": "You are a medical research assistant. Help users understand relevant medical research by searching PubMed, synthesizing findings from multiple studies, and explaining complex medical information in accessible language. Always cite sources and explain limitations of research.",
        "model": _DEFAULT_MODEL,
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True,
    },
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "agent_type": "medication_advisor",
        "agent_name": "Medication Advisor",
        "agent_description": "Provides medication and supplement insights",
        "capabilities": ["medication_tracking", "interaction_checking", "adherence_support", "side_effect_monitoring"],
        "system_prompt": "You are a medication information specialist. Help users track medications and supplements, understand potential interactions, monitor for side effects, and improve adherence. Always emphasize the importance of consulting pharmacists and doctors for medical advice.",
        "model": _DEFAULT_MODEL,
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True,
    },
]

import uuid as _uuid

# In-memory conversation store — used as fallback when Supabase is unavailable
_local_conversations: Dict[str, dict] = {}

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class AgentInfo(BaseModel):
    id: str
    agent_type: str
    agent_name: str
    agent_description: str
    capabilities: List[str]
    is_active: bool


class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    agent_id: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    agent_type: Optional[str] = None  # Specify which agent to use
    conversation_type: str = "general"


class Conversation(BaseModel):
    id: str
    title: Optional[str]
    conversation_type: str
    primary_agent_id: str
    primary_agent_name: str
    participating_agents: List[str]
    status: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    last_message_at: str


class AgentAction(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    action_type: str
    action_description: str
    action_data: Dict[str, Any]
    priority: str
    category: Optional[str]
    status: str
    created_at: str


class UpdateActionRequest(BaseModel):
    status: str  # approved, rejected, completed, dismissed
    user_feedback: Optional[str] = None


# ============================================================================
# AGENT BASE CLASS & ORCHESTRATOR
# ============================================================================


class Agent:
    """Base class for AI agents."""

    def __init__(self, agent_data: Dict[str, Any]):
        self.id = agent_data["id"]
        self.agent_type = agent_data["agent_type"]
        self.agent_name = agent_data["agent_name"]
        self.agent_description = agent_data["agent_description"]
        self.capabilities = agent_data.get("capabilities", [])
        self.system_prompt = agent_data["system_prompt"]
        self.model = agent_data.get("model", _DEFAULT_MODEL)
        self.temperature = agent_data.get("temperature", 0.7)
        self.max_tokens = agent_data.get("max_tokens", 1000)

    async def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        conversation_history: List[Dict],
    ) -> str:
        """Generate AI response using Anthropic Claude."""
        api_key = _get_anthropic_key()
        if not api_key:
            logger.info(
                "AI agent response skipped: ANTHROPIC_API_KEY not set (set it in server environment, e.g. Render)"
            )
            return (
                f"I'm {self.agent_name}, your {self.agent_description}. "
                "I'm here to help! (Anthropic API key not configured on the server. Set ANTHROPIC_API_KEY in your deployment environment, e.g. Render → Environment.)"
            )

        # Build system prompt — Anthropic takes system as a top-level string, not a message role
        system_prompt = self.system_prompt
        first_name = context.get("first_name", "the user") if context else "the user"
        if context:
            context_summary = self._build_context_summary(context)
            if context_summary:
                personalization = (
                    f"\n\nPERSONALIZATION RULES (mandatory — follow in every response):\n"
                    f"1. Always address the user as '{first_name}' — use their name naturally throughout.\n"
                    f"2. Your response MUST reference the specific health data listed above "
                    f"(conditions, medications, symptoms, labs, meals, care plans) — never give generic advice when personal data is available.\n"
                    f"3. Open your response by briefly stating which of their data you are drawing from "
                    f"(e.g. 'Based on your recent symptoms and lab results, {first_name}...').\n"
                    f"4. Make every recommendation directly relevant to their personal health profile.\n"
                    f"5. If they have active treatment plans, check in on progress proactively — "
                    f"especially if adherence is below 80% or a target metric is moving in the wrong direction. "
                    f"Example: 'You\\'re 72% adherent on Metformin this month — your LDL data suggests the gap may be impacting results.'\n"
                    f"6. If prior AI findings are listed, reference any that are directly relevant to the current question. "
                    f"This closes the loop and makes advice feel continuous, not episodic."
                )
                system_prompt = (
                    f"{system_prompt}\n\nUser Health Profile:\n{context_summary}"
                    f"{personalization}"
                )

        # Build messages array — only user/assistant roles (no system role)
        messages = []
        for msg in conversation_history[-10:]:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        # Call Anthropic Messages API
        try:
            client = anthropic.AsyncAnthropic(api_key=api_key)
            result = await client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return result.content[0].text

        except Exception as exc:
            logger.error(f"Error calling Anthropic: {exc}")
            return "I apologize, but I'm experiencing technical difficulties."

    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a rich context summary for the agent, covering all available health data."""
        parts = []

        first_name = context.get("first_name") or context.get("user_name") or "the user"
        parts.append(f"User's name: {context.get('user_name', first_name)} (address them as {first_name})")

        if context.get("health_conditions"):
            parts.append(f"Diagnosed health conditions: {', '.join(context['health_conditions'])}")

        if context.get("medications"):
            med_strs = []
            for m in context["medications"]:
                dose = f" {m['dose']}" if m.get("dose") else ""
                freq = f" {m['frequency']}" if m.get("frequency") else ""
                med_strs.append(f"{m['name']}{dose}{freq}")
            parts.append(f"Current medications: {', '.join(med_strs)}")

        if context.get("recent_symptoms"):
            symp_strs = []
            for s in context["recent_symptoms"][:6]:
                sname = s.get("name", "Unknown")
                severity = s.get("severity")
                date = s.get("date", "")
                sev_str = f", severity {severity}/10" if severity else ""
                symp_strs.append(f"{sname} ({date}{sev_str})")
            parts.append(f"Recent symptoms: {'; '.join(symp_strs)}")

        if context.get("lab_results"):
            lab_strs = []
            for l in context["lab_results"][:6]:
                test = l.get("test", "")
                val = f"{l.get('value', '')} {l.get('unit', '')}".strip()
                date = l.get("date", "")
                status = l.get("status", "")
                status_str = f" [{status}]" if status and status.lower() != "normal" else ""
                lab_strs.append(f"{test}: {val}{status_str} ({date})")
            parts.append(f"Recent lab results: {'; '.join(lab_strs)}")

        if context.get("recent_meals"):
            meal_strs = []
            for m in context["recent_meals"][:5]:
                meal_name = m.get("meal") or "Unknown"
                cals = f", {m['calories']} cal" if m.get("calories") else ""
                mtype = f" [{m['meal_type']}]" if m.get("meal_type") else ""
                date = m.get("date", "")
                meal_strs.append(f"{meal_name}{mtype}{cals} ({date})")
            parts.append(f"Recent meals: {', '.join(meal_strs)}")

        if context.get("user_goals"):
            parts.append(f"Health goals: {', '.join(context['user_goals'])}")

        # --- Care plans / treatment targets ---
        if context.get("care_plans"):
            plan_strs = []
            for p in context["care_plans"]:
                title = p.get("title", "Unnamed plan")
                source_tag = " [Doctor-prescribed]" if p.get("source") == "doctor" else ""
                target = ""
                if p.get("target_value") is not None:
                    target = f" — target: {p['target_value']} {p.get('target_unit') or ''}"
                    if p.get("current_value") is not None:
                        target += f" (current: {p['current_value']} {p.get('target_unit') or ''})"
                if p.get("target_date"):
                    target += f" by {p['target_date']}"
                plan_strs.append(f"{title}{source_tag}{target}")
            parts.append(f"Active treatment plans: {'; '.join(plan_strs)}")

        # --- Medication adherence ---
        if context.get("adherence_pct") is not None:
            pct = context["adherence_pct"]
            if pct < 60:
                adherence_note = f"{pct}% (critically low — patient missing more than 4 in 10 doses)"
            elif pct < 80:
                adherence_note = f"{pct}% (below target — patient missing roughly 1 in 5 doses)"
            else:
                adherence_note = f"{pct}% (good)"
            parts.append(f"Medication adherence (last 30 days): {adherence_note}")

        # --- Wellbeing trend ---
        wellbeing_parts = []
        if context.get("avg_energy") is not None:
            wellbeing_parts.append(f"energy {context['avg_energy']}/10")
        if context.get("avg_mood") is not None:
            wellbeing_parts.append(f"mood {context['avg_mood']}/10")
        if context.get("avg_pain") is not None:
            wellbeing_parts.append(f"pain {context['avg_pain']}/10")
        if wellbeing_parts:
            parts.append(f"Avg weekly wellbeing (last 4 check-ins): {', '.join(wellbeing_parts)}")

        # --- Prior AI insights ---
        if context.get("recent_insights"):
            insight_strs = []
            for ins in context["recent_insights"][:3]:
                title = ins.get("title", "")
                week = ins.get("week", "")
                summary = ins.get("summary", "")
                snippet = f"{title}"
                if week:
                    snippet += f" ({week})"
                if summary:
                    snippet += f": {summary[:120]}"
                insight_strs.append(snippet)
            parts.append(f"Prior AI findings: {' | '.join(insight_strs)}")

        return "\n".join(parts) if parts else ""


# ============================================================================
# NUTRITION ANALYST — Preference-Aware Specialist
# ============================================================================

_NUTRITION_PREFERENCE_KEYS = (
    "goals",
    "allergies",
    "dietary_restrictions",
    "dislikes",
    "food_preferences",
    "health_conditions",
    "cuisine_preferences",
    "meal_timing",
    "cooking_skill",
    "budget",
    "notes",
)

# System prompt injected when user has stored preferences
_NUTRITION_PERSONALIZED_PROMPT = """You are the Nutrition Analyst, a personalized AI nutritionist.

USER DIETARY PROFILE (apply these to every response — never suggest anything that violates allergies or restrictions):
- Goals: {goals}
- Allergies (STRICT — never include): {allergies}
- Dietary restrictions: {dietary_restrictions}
- Disliked foods (avoid unless requested): {dislikes}
- Favorite foods / cuisines: {food_preferences} | {cuisine_preferences}
- Health conditions: {health_conditions}
- Meal timing preference: {meal_timing}
- Cooking skill: {cooking_skill}
- Budget: {budget}
- Notes: {notes}

Guidelines:
1. Always address the user by their first name (provided in the health profile below).
2. Every recommendation must respect allergies absolutely — check ingredients for hidden allergens.
3. Align meals with dietary restrictions and goals.
4. Favor preferred foods and cuisines when possible.
5. Tailor portions and calorie density to goals.
6. Proactively reference their recent meal logs, health conditions, symptoms, and lab results when available — never be generic.
7. Open each response by briefly stating which personal data you're basing your advice on.
8. Offer 2–3 concrete, practical options instead of generic advice.
9. Occasionally remind the user how a suggestion connects to their personal goals.
"""

# System prompt when no preferences exist — initiates onboarding
_NUTRITION_ONBOARDING_PROMPT = """You are the Nutrition Analyst, a personalized AI nutritionist.

This is the user's FIRST interaction. Before giving any nutrition advice, you MUST collect their preferences so every future recommendation is tailored specifically to them.

Ask the following in a warm, conversational tone (don't use a numbered list — make it feel like a natural conversation):
1. Their primary dietary goals (e.g. weight loss, muscle gain, energy, disease management)
2. Any food allergies that must be strictly avoided
3. Dietary restrictions or philosophy (vegetarian, vegan, gluten-free, keto, etc.)
4. Foods or ingredients they strongly dislike
5. Favourite foods, cuisines, or ingredients they love

Keep it friendly and encouraging. Explain that this helps personalise all future advice just for them.
Do NOT provide any nutrition advice yet — just collect preferences.
"""

# Prompt used to extract structured preferences from user's free-text answer
_PREFERENCE_EXTRACTION_PROMPT = """Extract nutritional preferences from the following user message.
Return ONLY a valid JSON object (no markdown fences, no extra text) with these keys:
{{
  "goals": [],
  "allergies": [],
  "dietary_restrictions": [],
  "dislikes": [],
  "food_preferences": [],
  "health_conditions": [],
  "cuisine_preferences": [],
  "meal_timing": "",
  "cooking_skill": "",
  "budget": "",
  "notes": ""
}}

User message: {user_message}
"""

_PREFERENCE_COLLECTION_PHRASES = (
    "dietary goals",
    "food allergies",
    "dietary restrictions",
    "personalis",  # covers personalise/personalize
    "allergies",
    "before i give",
    "before giving",
    "first interaction",
    "collect your preferences",
    "tailor",
)


async def _get_nutrition_prefs(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch stored nutrition analyst preferences for a user."""
    rows = await _supabase_get(
        "nutrition_analyst_prefs",
        f"user_id=eq.{user_id}&limit=1",
    )
    if rows:
        prefs = rows[0].get("preferences")
        if isinstance(prefs, dict):
            return prefs
    return None


async def _save_nutrition_prefs(user_id: str, prefs: Dict[str, Any]) -> None:
    """Upsert nutrition analyst preferences for a user."""
    await _supabase_upsert(
        "nutrition_analyst_prefs",
        {
            "user_id": user_id,
            "preferences": prefs,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def _prefs_are_set(prefs: Optional[Dict[str, Any]]) -> bool:
    """Return True if the user has provided at least goals or restrictions."""
    if not prefs:
        return False
    return bool(
        prefs.get("goals")
        or prefs.get("dietary_restrictions")
        or prefs.get("allergies")
        or prefs.get("food_preferences")
    )


def _last_assistant_was_onboarding(history: List[Dict[str, Any]]) -> bool:
    """Return True if the most recent assistant message was collecting preferences."""
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            content = (msg.get("content") or "").lower()
            return any(phrase in content for phrase in _PREFERENCE_COLLECTION_PHRASES)
    return False


async def _call_anthropic_messages(
    system: str,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Make a single Anthropic Messages API call and return the text content."""
    client = anthropic.AsyncAnthropic(api_key=_get_anthropic_key())
    result = await client.messages.create(
        model=model,
        system=system,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return result.content[0].text


def _fmt_pref_value(v: Any) -> str:
    """Format a single preference value for prompt injection."""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "none specified"
    return str(v) if v else "not specified"


def _build_nutrition_system_prompt(prefs: Optional[Dict[str, Any]]) -> str:
    """Return the appropriate system prompt for the Nutrition Analyst."""
    if not _prefs_are_set(prefs):
        return _NUTRITION_ONBOARDING_PROMPT
    assert prefs is not None  # satisfied by _prefs_are_set guard above
    return _NUTRITION_PERSONALIZED_PROMPT.format(
        goals=_fmt_pref_value(prefs.get("goals")),
        allergies=_fmt_pref_value(prefs.get("allergies")),
        dietary_restrictions=_fmt_pref_value(prefs.get("dietary_restrictions")),
        dislikes=_fmt_pref_value(prefs.get("dislikes")),
        food_preferences=_fmt_pref_value(prefs.get("food_preferences")),
        cuisine_preferences=_fmt_pref_value(prefs.get("cuisine_preferences")),
        health_conditions=_fmt_pref_value(prefs.get("health_conditions")),
        meal_timing=_fmt_pref_value(prefs.get("meal_timing")),
        cooking_skill=_fmt_pref_value(prefs.get("cooking_skill")),
        budget=_fmt_pref_value(prefs.get("budget")),
        notes=_fmt_pref_value(prefs.get("notes")),
    )


async def _maybe_collect_prefs(
    user_id: str,
    prefs: Optional[Dict[str, Any]],
    conversation_history: List[Dict],
    user_message: str,
) -> tuple:
    """
    If the last assistant turn was onboarding, extract and save preferences.
    Returns (updated_prefs, updated_user_message).
    """
    if _prefs_are_set(prefs) or not _last_assistant_was_onboarding(conversation_history):
        return prefs, user_message
    extracted = await _extract_prefs_from_message(user_message)
    if extracted and _prefs_are_set(extracted):
        await _save_nutrition_prefs(user_id, extracted)
        return extracted, (
            f"[Preferences saved] {user_message}\n\n"
            "Now provide personalised nutrition advice based on these preferences."
        )
    return prefs, user_message


async def _extract_prefs_from_message(
    user_message: str,
) -> Optional[Dict[str, Any]]:
    """Call Anthropic Claude to extract structured preferences from a free-text user reply."""
    api_key = _get_anthropic_key()
    if not api_key:
        return None
    extraction_prompt = _PREFERENCE_EXTRACTION_PROMPT.format(user_message=user_message)
    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0.1,
            max_tokens=400,
        )
        raw = result.content[0].text.strip()
        return json.loads(raw)
    except Exception as exc:
        logger.warning(f"Preference extraction failed: {exc}")
        return None


class NutritionAnalystAgent(Agent):
    """
    Nutrition Analyst agent with skill-driven preference management.

    First interaction: collects dietary preferences via guided conversation.
    Subsequent interactions: personalises every response using stored preferences.
    If the user is replying to an onboarding question, parses and saves their prefs.
    """

    async def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        conversation_history: List[Dict],
        user_id: Optional[str] = None,
    ) -> str:
        if not _get_anthropic_key():
            logger.info("Nutrition Analyst skipped: ANTHROPIC_API_KEY not set")
            return (
                f"I'm {self.agent_name}, your personalised nutritionist. "
                "(Anthropic API key not configured. Set ANTHROPIC_API_KEY in your deployment environment.)"
            )

        # Load preferences, collecting them if this is the first turn
        prefs: Optional[Dict[str, Any]] = await _get_nutrition_prefs(user_id) if user_id else None
        if user_id:
            prefs, user_message = await _maybe_collect_prefs(
                user_id, prefs, conversation_history, user_message
            )

        # Build system prompt with optional health context appended
        system_prompt = _build_nutrition_system_prompt(prefs)
        first_name = context.get("first_name", "the user") if context else "the user"
        ctx_summary = self._build_context_summary(context) if context else ""
        if ctx_summary:
            personalization = (
                f"\n\nPERSONALIZATION RULES (mandatory — follow in every response):\n"
                f"1. Always address the user as '{first_name}' — use their name naturally throughout.\n"
                f"2. Your response MUST reference their specific health data "
                f"(conditions, medications, symptoms, labs, meals) — never give generic advice when personal data is available.\n"
                f"3. Open your response by briefly stating which of their data you are drawing from "
                f"(e.g. 'Based on your recent meals and health conditions, {first_name}...').\n"
                f"4. Make every recommendation directly relevant to their personal profile."
            )
            system_prompt = (
                f"{system_prompt}\n\nUser Health Profile:\n{ctx_summary}"
                f"{personalization}"
            )

        # Build messages — only user/assistant roles (Anthropic requirement)
        messages: List[Dict[str, str]] = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history[-10:]
            if msg["role"] in ("user", "assistant")
        ]
        messages.append({"role": "user", "content": user_message})

        try:
            return await _call_anthropic_messages(
                system_prompt, messages, self.model, self.temperature, self.max_tokens
            )
        except Exception as exc:
            logger.error(f"NutritionAnalystAgent Anthropic error: {exc}")
            return "I'm experiencing technical difficulties. Please try again shortly."


class AgentOrchestrator:
    """Orchestrates multi-agent conversations."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    async def load_agents(self):
        """Load all active agents from database, falling back to defaults if unavailable."""
        agents_data = await _supabase_get("ai_agents", "is_active=eq.true")

        if not agents_data:
            logger.info("No agents found in Supabase — using built-in default agents")
            agents_data = _DEFAULT_AGENTS

        for agent_data in agents_data:
            if agent_data["agent_type"] == "nutrition_analyst":
                agent: Agent = NutritionAnalystAgent(agent_data)
            else:
                agent = Agent(agent_data)
            self.agents[agent_data["agent_type"]] = agent

        logger.info(f"Loaded {len(self.agents)} AI agents")

    def get_agent(self, agent_type: str) -> Optional[Agent]:
        """Get agent by type."""
        return self.agents.get(agent_type)

    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by its UUID."""
        for agent in self.agents.values():
            if agent.id == agent_id:
                return agent
        return None

    def get_default_agent(self) -> Agent:
        """Get default agent (health_coach)."""
        return self.agents.get("health_coach") or list(self.agents.values())[0]

    async def route_message(
        self, user_message: str, current_agent_type: Optional[str] = None
    ) -> str:
        """Determine which agent should handle the message."""
        # Simple routing based on keywords
        message_lower = user_message.lower()

        if any(
            word in message_lower
            for word in ["eat", "meal", "food", "nutrition", "diet"]
        ):
            return "nutrition_analyst"
        elif any(word in message_lower for word in ["symptom", "pain", "feel", "sick"]):
            return "symptom_investigator"
        elif any(
            word in message_lower
            for word in ["research", "study", "article", "evidence"]
        ):
            return "research_assistant"
        elif any(
            word in message_lower
            for word in ["medication", "drug", "pill", "supplement", "prescription"]
        ):
            return "medication_advisor"
        else:
            return current_agent_type or "health_coach"


# Global orchestrator
orchestrator = AgentOrchestrator()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def _get_user_context(
    user_id: str, current_user: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Gather comprehensive user context for agents including name, health data, and history."""
    context: Dict[str, Any] = {}

    # --- User name resolution (JWT metadata → profiles table → email fallback) ---
    name: Optional[str] = None
    if current_user:
        payload = current_user.get("token_payload") or {}
        meta = payload.get("user_metadata") or {}
        name = meta.get("full_name") or meta.get("name") or meta.get("display_name")

    if not name:
        profiles = await _supabase_get("profiles", f"id=eq.{user_id}&limit=1")
        if profiles:
            p = profiles[0]
            name = (
                p.get("full_name")
                or p.get("name")
                or (
                    f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or None
                )
            )

    if not name:
        email = (current_user or {}).get("email") or ""
        if email:
            local = email.split("@")[0]
            # Strip trailing ".demo" / ".test" suffixes for cleaner names
            local = local.replace(".demo", "").replace(".test", "")
            name = " ".join(p.capitalize() for p in local.replace("_", ".").split("."))

    context["user_name"] = name or "there"
    context["first_name"] = (name or "").split()[0] if name else "there"

    # --- Health conditions ---
    conditions = await _supabase_get(
        "health_conditions", f"user_id=eq.{user_id}&is_current=eq.true&limit=10"
    )
    if conditions:
        context["health_conditions"] = [c["condition_name"] for c in conditions]

    # --- Current medications ---
    medications = await _supabase_get(
        "medications", f"user_id=eq.{user_id}&is_active=eq.true&limit=10"
    )
    if medications:
        context["medications"] = [
            {
                "name": m.get("medication_name"),
                "dose": m.get("dosage"),
                "frequency": m.get("frequency"),
            }
            for m in medications
            if m.get("medication_name")
        ]

    # --- Recent symptoms (last 10, with severity and notes) ---
    symptoms = await _supabase_get(
        "symptom_journal",
        f"user_id=eq.{user_id}&order=symptom_date.desc&limit=10",
    )
    if symptoms:
        context["recent_symptoms"] = [
            {
                "name": s.get("symptom_name"),
                "severity": s.get("severity"),
                "date": (s.get("symptom_date") or "")[:10],
                "notes": s.get("notes"),
            }
            for s in symptoms
            if s.get("symptom_name")
        ]

    # --- Lab results (most recent 10) ---
    labs = await _supabase_get(
        "lab_results",
        f"user_id=eq.{user_id}&order=test_date.desc&limit=10",
    )
    if labs:
        context["lab_results"] = [
            {
                "test": l.get("test_name"),
                "value": l.get("value"),
                "unit": l.get("unit"),
                "date": (l.get("test_date") or "")[:10],
                "status": l.get("status"),
            }
            for l in labs
            if l.get("test_name")
        ]

    # --- Recent meal logs (last 7) ---
    meals = await _supabase_get(
        "meal_logs",
        f"user_id=eq.{user_id}&order=timestamp.desc&limit=7",
    )
    if meals:
        context["recent_meals"] = [
            {
                "meal": m.get("meal_name") or m.get("food_name"),
                "calories": m.get("calories"),
                "meal_type": m.get("meal_type"),
                "date": (m.get("timestamp") or "")[:10],
            }
            for m in meals
        ]

    # --- Active user goals ---
    goals = await _supabase_get(
        "user_goals",
        f"user_id=eq.{user_id}&status=eq.active&order=created_at.desc&limit=10",
    )
    if goals:
        context["user_goals"] = [g["goal_text"] for g in goals if g.get("goal_text")]

    # --- Active care plans (treatment targets set by doctor or self) ---
    care_plans = await _supabase_get(
        "care_plans",
        f"user_id=eq.{user_id}&status=eq.active&order=created_at.desc&limit=8",
    )
    if care_plans:
        context["care_plans"] = [
            {
                "title": p.get("title"),
                "metric_type": p.get("metric_type"),
                "target_value": p.get("target_value"),
                "target_unit": p.get("target_unit"),
                "target_date": p.get("target_date"),
                "current_value": p.get("current_value"),
                "source": p.get("source"),  # 'doctor' | 'self'
            }
            for p in care_plans
            if p.get("title")
        ]

    # --- Medication adherence rate (last 30 days) ---
    thirty_ago = (date.today() - timedelta(days=30)).isoformat()
    adherence_rows = await _supabase_get(
        "medication_adherence_log",
        f"user_id=eq.{user_id}&scheduled_time=gte.{thirty_ago}&select=was_taken",
    )
    if adherence_rows:
        total = len(adherence_rows)
        taken = sum(1 for r in adherence_rows if r.get("was_taken"))
        context["adherence_pct"] = round(taken / total * 100) if total else None

    # --- Weekly wellbeing trend (energy + mood from check-ins) ---
    checkins = await _supabase_get(
        "weekly_checkins",
        f"user_id=eq.{user_id}&order=week_start.desc&select=week_start,energy_level,mood_rating,pain_level&limit=4",
    )
    if checkins:
        energy_vals = [c.get("energy_level") for c in checkins if c.get("energy_level") is not None]
        mood_vals = [c.get("mood_rating") for c in checkins if c.get("mood_rating") is not None]
        pain_vals = [c.get("pain_level") for c in checkins if c.get("pain_level") is not None]
        if energy_vals:
            context["avg_energy"] = round(sum(energy_vals) / len(energy_vals), 1)
        if mood_vals:
            context["avg_mood"] = round(sum(mood_vals) / len(mood_vals), 1)
        if pain_vals:
            context["avg_pain"] = round(sum(pain_vals) / len(pain_vals), 1)

    # --- Recent AI insights (resurfaced findings) ---
    insights = await _supabase_get(
        "saved_insights",
        f"user_id=eq.{user_id}&order=created_at.desc&select=title,summary,metric_key,week_bucket&limit=5",
    )
    if insights:
        context["recent_insights"] = [
            {
                "title": ins.get("title"),
                "summary": ins.get("summary"),
                "week": ins.get("week_bucket"),
            }
            for ins in insights
            if ins.get("title")
        ]

    return context


def _parse_messages(raw: Any) -> List[Dict[str, Any]]:
    """Parse messages from DB: may be JSON string or already a list (Supabase JSONB)."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


async def _create_conversation(
    user_id: str, agent_id: str, conversation_type: str, initial_message: str
) -> str:
    """Create a new conversation, falling back to in-memory when Supabase is unavailable."""
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "user_id": user_id,
        "conversation_type": conversation_type,
        "primary_agent_id": agent_id,
        "participating_agents": [agent_id],
        "status": "active",
        "messages": json.dumps([]),
        "conversation_context": json.dumps({}),
        "last_message_at": now,
    }

    result = await _supabase_upsert("agent_conversations", payload)
    if result:
        return result["id"]

    # Supabase unavailable — store locally
    conv_id = str(_uuid.uuid4())
    _local_conversations[conv_id] = {
        "id": conv_id,
        "user_id": user_id,
        "title": None,
        "conversation_type": conversation_type,
        "primary_agent_id": agent_id,
        "participating_agents": [agent_id],
        "status": "active",
        "messages": [],
        "conversation_context": {},
        "conversation_summary": None,
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
    }
    logger.info(f"Conversation {conv_id} stored in-memory (Supabase unavailable)")
    return conv_id


async def _add_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    agent_id: Optional[str] = None,
):
    """Add message to conversation, falling back to in-memory when Supabase is unavailable."""
    now = datetime.now(timezone.utc).isoformat()
    message: Dict[str, Any] = {
        "role": role,
        "content": content,
        "agent_id": agent_id,
        "timestamp": now,
        "metadata": {},
    }

    # Try in-memory store first (set by _create_conversation fallback)
    if conversation_id in _local_conversations:
        conv = _local_conversations[conversation_id]
        conv["messages"].append(message)
        conv["last_message_at"] = now
        conv["updated_at"] = now
        return

    rows = await _supabase_get(
        "agent_conversations",
        f"id=eq.{conversation_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = rows[0]
    messages: List[Dict[str, Any]] = _parse_messages(conv.get("messages"))
    messages.append(message)

    updated = await _supabase_patch(
        "agent_conversations",
        f"id=eq.{conversation_id}&user_id=eq.{user_id}",
        {
            "messages": messages,
            "last_message_at": now,
            "updated_at": now,
        },
    )
    if not updated:
        logger.warning("_add_message: PATCH agent_conversations did not return a row")


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.on_event("startup")
async def load_agents():
    """Load agents on startup."""
    await orchestrator.load_agents()


@router.get("/agents", response_model=List[AgentInfo])
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List available AI agents."""
    agents_data = await _supabase_get(
        "ai_agents", "is_active=eq.true&order=agent_name.asc"
    )

    if not agents_data:
        agents_data = _DEFAULT_AGENTS

    return [
        AgentInfo(
            id=agent["id"],
            agent_type=agent["agent_type"],
            agent_name=agent["agent_name"],
            agent_description=agent["agent_description"],
            capabilities=agent.get("capabilities", []),
            is_active=agent["is_active"],
        )
        for agent in agents_data
    ]


@router.post("/chat", response_model=Conversation)
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(UsageGate("ai_agents")),
):
    """Send message to AI agent and get response."""
    user_id = current_user["id"]

    # Ensure agents are loaded
    if not orchestrator.agents:
        await orchestrator.load_agents()

    # Determine agent to use
    if request.agent_type:
        agent_type = request.agent_type
    elif request.conversation_id:
        # Get existing conversation's agent
        conv_rows = await _supabase_get(
            "agent_conversations", f"id=eq.{request.conversation_id}&limit=1"
        )
        if not conv_rows:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv_data = conv_rows[0]
        agent_rows = await _supabase_get(
            "ai_agents", f"id=eq.{conv_data['primary_agent_id']}"
        )
        agent_type = agent_rows[0]["agent_type"] if agent_rows else "health_coach"
    else:
        # Route to appropriate agent
        agent_type = await orchestrator.route_message(request.message)

    agent = orchestrator.get_agent(agent_type)
    if not agent:
        agent = orchestrator.get_default_agent()

    # Create or get conversation
    if not request.conversation_id:
        conversation_id = await _create_conversation(
            user_id, agent.id, request.conversation_type, request.message
        )
    else:
        conversation_id = request.conversation_id

    # Add user message
    await _add_message(conversation_id, user_id, "user", request.message)

    # Get conversation history (in-memory or Supabase)
    if conversation_id in _local_conversations:
        messages = list(_local_conversations[conversation_id]["messages"])
    else:
        conv_rows = await _supabase_get(
            "agent_conversations", f"id=eq.{conversation_id}&limit=1"
        )
        conv_data = conv_rows[0] if conv_rows else {"messages": []}
        messages = _parse_messages(conv_data.get("messages"))

    # Get user context (includes name resolution and all health data)
    context = await _get_user_context(user_id, current_user)

    # Generate agent response — pass user_id for preference-aware agents
    if isinstance(agent, NutritionAnalystAgent):
        response_content = await agent.generate_response(
            request.message, context, messages, user_id=user_id
        )
    else:
        response_content = await agent.generate_response(
            request.message, context, messages
        )

    # Add agent response
    await _add_message(
        conversation_id, user_id, "assistant", response_content, agent.id
    )

    # Return updated conversation
    return await get_conversation(conversation_id, current_user)


@router.get("/conversations", response_model=List[Conversation])
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """List user's agent conversations."""
    user_id = current_user["id"]

    rows = await _supabase_get(
        "agent_conversations",
        f"user_id=eq.{user_id}&status=eq.active&order=last_message_at.desc&limit=20",
    )

    conversations = []
    for row in rows:
        # Get agent info
        agent_rows = await _supabase_get(
            "ai_agents", f"id=eq.{row['primary_agent_id']}"
        )
        agent_name = agent_rows[0]["agent_name"] if agent_rows else "Assistant"

        messages = _parse_messages(row.get("messages"))

        conversations.append(
            Conversation(
                id=row["id"],
                title=row.get("title"),
                conversation_type=row["conversation_type"],
                primary_agent_id=row["primary_agent_id"],
                primary_agent_name=agent_name,
                participating_agents=row.get("participating_agents", []),
                status=row["status"],
                messages=[ChatMessage(**msg) for msg in messages],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_message_at=row["last_message_at"],
            )
        )

    return conversations


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """Get specific conversation."""
    user_id = current_user["id"]

    # Check in-memory store first
    if conversation_id in _local_conversations:
        row = _local_conversations[conversation_id]
    else:
        rows = await _supabase_get(
            "agent_conversations", f"id=eq.{conversation_id}&user_id=eq.{user_id}&limit=1"
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Conversation not found")
        row = rows[0]

    # Resolve agent name from orchestrator or Supabase
    agent = orchestrator.get_agent_by_id(row["primary_agent_id"])
    if agent:
        agent_name = agent.agent_name
    else:
        agent_rows = await _supabase_get("ai_agents", f"id=eq.{row['primary_agent_id']}")
        agent_name = agent_rows[0]["agent_name"] if agent_rows else "Assistant"

    messages = _parse_messages(row.get("messages"))

    return Conversation(
        id=row["id"],
        title=row.get("title"),
        conversation_type=row["conversation_type"],
        primary_agent_id=row["primary_agent_id"],
        primary_agent_name=agent_name,
        participating_agents=row.get("participating_agents") or [],
        status=row["status"],
        messages=[ChatMessage(**msg) for msg in messages],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_message_at=row["last_message_at"],
    )


@router.get("/actions", response_model=List[AgentAction])
async def list_actions(
    current_user: dict = Depends(get_current_user), status: Optional[str] = None
):
    """List agent-generated actions for the user."""
    user_id = current_user["id"]

    query = f"user_id=eq.{user_id}"
    if status:
        query += f"&status=eq.{status}"
    query += "&order=created_at.desc&limit=20"

    rows = await _supabase_get("agent_actions", query)

    actions = []
    for row in rows:
        # Get agent info
        agent_rows = await _supabase_get("ai_agents", f"id=eq.{row['agent_id']}")
        agent_name = agent_rows[0]["agent_name"] if agent_rows else "Assistant"

        actions.append(
            AgentAction(
                id=row["id"],
                agent_id=row["agent_id"],
                agent_name=agent_name,
                action_type=row["action_type"],
                action_description=row["action_description"],
                action_data=row.get("action_data", {}),
                priority=row["priority"],
                category=row.get("category"),
                status=row["status"],
                created_at=row["created_at"],
            )
        )

    return actions


@router.patch("/actions/{action_id}", response_model=AgentAction)
async def update_action(
    action_id: str,
    request: UpdateActionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update action status (approve, reject, complete, etc.)."""
    user_id = current_user["id"]

    # Get action
    rows = await _supabase_get(
        "agent_actions", f"id=eq.{action_id}&user_id=eq.{user_id}&limit=1"
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Action not found")

    # Update action
    payload = {
        "id": action_id,
        "status": request.status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if request.user_feedback:
        payload["user_feedback"] = request.user_feedback

    if request.status == "completed":
        payload["completed_at"] = datetime.now(timezone.utc).isoformat()

    await _supabase_upsert("agent_actions", payload)

    # Return updated action
    return await list_actions(current_user, None)
