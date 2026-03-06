"""
AI Agents Multi-Agent System API

Pro+ feature for conversational AI health assistants with specialized agents
that work together to provide personalized health insights.

Phase 3 of Health Intelligence Features
"""

import json
import os
from datetime import datetime, timezone
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
ANTHROPIC_API_KEY = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
_DEFAULT_MODEL = "claude-sonnet-4-6"

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
        if not ANTHROPIC_API_KEY:
            logger.info(
                "AI agent response skipped: ANTHROPIC_API_KEY not set (set it in server environment, e.g. Render)"
            )
            return (
                f"I'm {self.agent_name}, your {self.agent_description}. "
                "I'm here to help! (Anthropic API key not configured on the server. Set ANTHROPIC_API_KEY in your deployment environment, e.g. Render → Environment.)"
            )

        # Build system prompt — Anthropic takes system as a top-level string, not a message role
        system_prompt = self.system_prompt
        if context:
            context_summary = self._build_context_summary(context)
            if context_summary:
                system_prompt = f"{system_prompt}\n\nUser Context:\n{context_summary}"

        # Build messages array — only user/assistant roles (no system role)
        messages = []
        for msg in conversation_history[-10:]:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        # Call Anthropic Messages API
        try:
            client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
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
        """Build context summary for the agent."""
        parts = []

        if context.get("user_goals"):
            parts.append(f"User's health goals: {', '.join(context['user_goals'])}")

        if context.get("health_conditions"):
            parts.append(
                f"Health conditions: {', '.join(context['health_conditions'])}"
            )

        if context.get("recent_symptoms"):
            parts.append(f"Recent symptoms: {context['recent_symptoms']}")

        if context.get("recent_meals"):
            parts.append(f"Recent meals: {context['recent_meals']}")

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

USER PROFILE (apply these to every response — never suggest anything that violates allergies or restrictions):
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
1. Every recommendation must respect allergies absolutely — check ingredients for hidden allergens.
2. Align meals with dietary restrictions and goals.
3. Favor preferred foods and cuisines when possible.
4. Tailor portions and calorie density to goals.
5. When relevant, cite evidence-based nutritional science.
6. Offer 2–3 concrete, practical options instead of generic advice.
7. Occasionally remind the user how a suggestion connects to their personal goals.
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
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
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
    if not ANTHROPIC_API_KEY:
        return None
    extraction_prompt = _PREFERENCE_EXTRACTION_PROMPT.format(user_message=user_message)
    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
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
        if not ANTHROPIC_API_KEY:
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
        ctx_summary = self._build_context_summary(context) if context else ""
        if ctx_summary:
            system_prompt = f"{system_prompt}\n\nHealth Context:\n{ctx_summary}"

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
        """Load all active agents from database."""
        agents_data = await _supabase_get("ai_agents", "is_active=eq.true")

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


async def _get_user_context(user_id: str) -> Dict[str, Any]:
    """Gather user context for agents."""
    context = {}

    # Get health conditions
    conditions = await _supabase_get(
        "health_conditions", f"user_id=eq.{user_id}&is_current=eq.true&limit=5"
    )
    if conditions:
        context["health_conditions"] = [c["condition_name"] for c in conditions]

    # Get recent symptoms (last 7 days)
    symptoms = await _supabase_get(
        "symptom_journal",
        f"user_id=eq.{user_id}&order=symptom_date.desc&limit=5",
    )
    if symptoms:
        context["recent_symptoms"] = f"{len(symptoms)} entries in last 7 days"  # type: ignore

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
    """Create a new conversation."""
    payload = {
        "user_id": user_id,
        "conversation_type": conversation_type,
        "primary_agent_id": agent_id,
        "participating_agents": [agent_id],
        "status": "active",
        "messages": json.dumps([]),
        "conversation_context": json.dumps({}),
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("agent_conversations", payload)
    if result:
        return result["id"]
    raise HTTPException(status_code=500, detail="Failed to create conversation")


async def _add_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    agent_id: Optional[str] = None,
):
    """Add message to conversation. Uses PATCH so the update is applied correctly."""
    rows = await _supabase_get(
        "agent_conversations",
        f"id=eq.{conversation_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = rows[0]
    messages: List[Dict[str, Any]] = _parse_messages(conv.get("messages"))

    message: Dict[str, Any] = {
        "role": role,
        "content": content,
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
    }
    messages.append(message)

    # PATCH so we only update these columns (avoids upsert/insert confusion)
    updated = await _supabase_patch(
        "agent_conversations",
        f"id=eq.{conversation_id}&user_id=eq.{user_id}",
        {
            "messages": messages,  # PostgREST accepts list for JSONB
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
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

    # Get conversation history
    conv_rows = await _supabase_get(
        "agent_conversations", f"id=eq.{conversation_id}&limit=1"
    )
    conv_data = conv_rows[0]
    messages = _parse_messages(conv_data.get("messages"))

    # Get user context
    context = await _get_user_context(user_id)

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

    rows = await _supabase_get(
        "agent_conversations", f"id=eq.{conversation_id}&user_id=eq.{user_id}&limit=1"
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")

    row = rows[0]

    # Get agent info
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
