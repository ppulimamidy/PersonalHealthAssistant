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

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import UsageGate, _supabase_get, _supabase_upsert

logger = get_logger(__name__)
router = APIRouter()

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

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
        self.model = agent_data.get("model", "gpt-4o-mini")
        self.temperature = agent_data.get("temperature", 0.7)
        self.max_tokens = agent_data.get("max_tokens", 1000)

    async def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        conversation_history: List[Dict],
    ) -> str:
        """Generate AI response using OpenAI."""
        if not OPENAI_API_KEY:
            return (
                f"I'm {self.agent_name}, your {self.agent_description}. "
                "I'm here to help! (OpenAI API key not configured)"
            )

        # Build messages for OpenAI
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add context if available
        if context:
            context_summary = self._build_context_summary(context)
            if context_summary:
                messages.append(
                    {"role": "system", "content": f"User Context:\n{context_summary}"}
                )

        # Add conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add user message
        messages.append({"role": "user", "content": user_message})

        # Call OpenAI
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    OPENAI_API_URL,
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                    },
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"OpenAI API error: {resp.status}")
                        return "I apologize, but I'm having trouble generating a response right now."

                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]

        except Exception as exc:
            logger.error(f"Error calling OpenAI: {exc}")
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


class AgentOrchestrator:
    """Orchestrates multi-agent conversations."""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    async def load_agents(self):
        """Load all active agents from database."""
        agents_data = await _supabase_get("ai_agents", "is_active=eq.true")

        for agent_data in agents_data:
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
    conversation_id: str, role: str, content: str, agent_id: Optional[str] = None
):
    """Add message to conversation."""
    # Get current conversation
    rows = await _supabase_get(
        "agent_conversations", f"id=eq.{conversation_id}&limit=1"
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = rows[0]
    messages: List[Dict[str, Any]] = json.loads(conv.get("messages", "[]"))

    # Add new message
    message: Dict[str, Any] = {
        "role": role,
        "content": content,
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
    }
    messages.append(message)

    # Update conversation
    await _supabase_upsert(
        "agent_conversations",
        {
            "id": conversation_id,
            "messages": json.dumps(messages),
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )


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
    await _add_message(conversation_id, "user", request.message)

    # Get conversation history
    conv_rows = await _supabase_get(
        "agent_conversations", f"id=eq.{conversation_id}&limit=1"
    )
    conv_data = conv_rows[0]
    messages = json.loads(conv_data.get("messages", "[]"))

    # Get user context
    context = await _get_user_context(user_id)

    # Generate agent response
    response_content = await agent.generate_response(request.message, context, messages)

    # Add agent response
    await _add_message(conversation_id, "assistant", response_content, agent.id)

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

        messages = json.loads(row.get("messages", "[]"))

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

    messages = json.loads(row.get("messages", "[]"))

    return Conversation(
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
