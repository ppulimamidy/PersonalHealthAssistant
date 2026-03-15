"""
Unit tests for the AI agent topic guard (_is_off_topic function).

Runs fully offline — no LLM calls, no network required.

Usage:
    cd /Users/pulimap/PersonalHealthAssistant
    PYTHONPATH=/Users/pulimap/PersonalHealthAssistant pytest tests/test_ai_guard.py -v
"""

import sys
import asyncio
import os
from pathlib import Path

sys.path.insert(0, "/Users/pulimap/PersonalHealthAssistant")

from dotenv import load_dotenv

load_dotenv(
    Path("/Users/pulimap/PersonalHealthAssistant/apps/mvp_api/.env"), override=False
)

import pytest
from apps.mvp_api.api.ai_agents import _is_off_topic, _OFFTOPIC_REFUSAL


# ---------------------------------------------------------------------------
# Off-topic messages — MUST be blocked
# ---------------------------------------------------------------------------

OFF_TOPIC_PROMPTS = [
    "Write me a Python function to sort a list of integers",
    "Can you debug this JavaScript code for me?",
    "Explain how Kubernetes works",
    "Tell me a joke about programmers",
    "Write a poem about the ocean at sunset",
    "Write a short story about a dragon",
    "Explain quantum entanglement to me like I'm five",
    "What is string theory and how does it relate to black holes?",
    "Give me stock market investment advice",
    "Should I buy Bitcoin right now? I need investment tips",
    "What is the capital of Australia?",
    "Translate 'good morning' into Japanese",
    "Help me plan a trip to Bali",
    "Proofread my cover letter for me",
    "Write me a Python script for web scraping",
]


@pytest.mark.parametrize("prompt", OFF_TOPIC_PROMPTS)
def test_off_topic_blocked(prompt):
    assert (
        _is_off_topic(prompt) is True
    ), f"Expected off-topic block for: {repr(prompt)}"


# ---------------------------------------------------------------------------
# On-topic messages — MUST be allowed
# ---------------------------------------------------------------------------

ON_TOPIC_PROMPTS = [
    "What should I eat to lower my blood sugar?",
    "I've been feeling really tired lately, what could be causing that?",
    "Can you explain the side effects of metformin?",
    "My HRV has been low this week, what does that mean?",
    "I logged a headache and fatigue symptom, do you see any patterns?",
    "What foods are high in magnesium?",
    "How does sleep affect my immune system?",
    "I'm on lisinopril for hypertension — any interaction concerns?",
    "My A1C came back at 6.4, is that pre-diabetic?",
    "How many steps per day should I aim for to improve cardiovascular health?",
    "What is a healthy resting heart rate?",
    "Can you help me understand my lab results?",
    "I want to improve my nutrition",
    "My doctor prescribed a new medication",
    "What are the symptoms of vitamin D deficiency?",
]


@pytest.mark.parametrize("prompt", ON_TOPIC_PROMPTS)
def test_on_topic_allowed(prompt):
    assert (
        _is_off_topic(prompt) is False
    ), f"False positive — health message incorrectly blocked: {repr(prompt)}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_message_not_blocked():
    assert _is_off_topic("") is False


def test_very_long_off_topic_blocked():
    long_msg = "Write me a Python function to " + ("parse JSON " * 200)
    assert _is_off_topic(long_msg) is True


def test_health_term_overrides_offtopic_signal():
    # Contains 'code' but also 'blood glucose' — health wins
    msg = "Explain the chemistry of blood glucose regulation in the body"
    assert _is_off_topic(msg) is False


def test_health_app_question_allowed():
    msg = "Can you help me understand how diabetes tracking apps work?"
    assert _is_off_topic(msg) is False


def test_case_insensitive_block():
    assert _is_off_topic("WRITE ME A PYTHON SCRIPT") is True


def test_case_insensitive_allow():
    assert _is_off_topic("WHAT IS MY BLOOD PRESSURE READING") is False


def test_refusal_message_is_health_focused():
    assert "health" in _OFFTOPIC_REFUSAL.lower()
    assert "general-purpose assistant" in _OFFTOPIC_REFUSAL.lower()
    assert len(_OFFTOPIC_REFUSAL) < 500


# ---------------------------------------------------------------------------
# Integration: Agent.generate_response short-circuits for off-topic
# ---------------------------------------------------------------------------


class TestAgentGuardIntegration:
    def test_agent_returns_refusal_without_calling_anthropic(self, monkeypatch):
        from apps.mvp_api.api.ai_agents import Agent, _DEFAULT_AGENTS

        agent = Agent(_DEFAULT_AGENTS[0])  # health_coach
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")

        anthropic_called = False

        import anthropic as _anthropic

        class FakeMessages:
            async def create(self, **kwargs):
                nonlocal anthropic_called
                anthropic_called = True
                raise AssertionError(
                    "Anthropic must NOT be called for off-topic message"
                )

        class FakeClient:
            messages = FakeMessages()

        monkeypatch.setattr(_anthropic, "AsyncAnthropic", lambda **kw: FakeClient())

        result = asyncio.run(
            agent.generate_response(
                user_message="Write me a Python sorting algorithm",
                context={},
                conversation_history=[],
            )
        )

        assert result == _OFFTOPIC_REFUSAL
        assert not anthropic_called

    def test_agent_calls_anthropic_for_health_message(self, monkeypatch):
        from apps.mvp_api.api.ai_agents import Agent, _DEFAULT_AGENTS, _OFFTOPIC_REFUSAL

        agent = Agent(_DEFAULT_AGENTS[0])
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-placeholder")

        import anthropic as _anthropic

        class FakeContent:
            text = "Here is personalised health advice for you."

        class FakeResult:
            content = [FakeContent()]

        class FakeMessages:
            async def create(self, **kwargs):
                return FakeResult()

        class FakeClient:
            messages = FakeMessages()

        monkeypatch.setattr(_anthropic, "AsyncAnthropic", lambda **kw: FakeClient())

        result = asyncio.run(
            agent.generate_response(
                user_message="What should I eat to improve my sleep?",
                context={"first_name": "Sarah"},
                conversation_history=[],
            )
        )

        assert result != _OFFTOPIC_REFUSAL
        assert len(result) > 0
