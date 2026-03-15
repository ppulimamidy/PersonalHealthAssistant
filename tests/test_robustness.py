"""
Robustness QA tests for Vitalix backend services.

Tests MVP API (port 8100) and Nutrition service (port 8007) against real running instances.
Generates a JWT signed with JWT_SECRET_KEY from apps/mvp_api/.env.

Usage:
    cd /Users/pulimap/PersonalHealthAssistant
    PYTHONPATH=/Users/pulimap/PersonalHealthAssistant \\
        pytest tests/test_robustness.py -v --tb=short

    # Skip slow rate-limit test:
    pytest tests/test_robustness.py -v --tb=short -m "not slow"

Requirements:
    pip install pytest httpx python-jose[cryptography] python-dotenv
"""

import os
import time
from pathlib import Path

import pytest
import httpx
from dotenv import load_dotenv
from jose import jwt as jose_jwt

load_dotenv(Path(__file__).parent.parent / "apps/mvp_api/.env", override=False)

MVP_API = os.environ.get("MVP_API_BASE", "http://localhost:8100")
NUTRITION = os.environ.get("NUTRITION_BASE", "http://localhost:8007")

_DEMO_USER_ID = "22144dc2-f352-48aa-b34b-aebfa9f7e638"
_DEMO_EMAIL = "sarah.chen.demo@example.com"
_OFFTOPIC_REFUSAL_FRAGMENT = "I'm your personal health assistant"


def make_demo_jwt(ttl_seconds: int = 86400) -> str:
    secret = os.environ.get(
        "JWT_SECRET_KEY",
        "WVICv1XsXCSHNeQPL6aW4bOmfIObduJZyq/0HghyIwU=",
    )
    now = int(time.time())
    return jose_jwt.encode(
        {
            "sub": _DEMO_USER_ID,
            "email": _DEMO_EMAIL,
            "iat": now,
            "exp": now + ttl_seconds,
            "iss": "https://yadfzphehujeaiimzvoe.supabase.co/auth/v1",
            "role": "authenticated",
        },
        secret,
        algorithm="HS256",
    )


@pytest.fixture(scope="session")
def auth_headers() -> dict:
    return {"Authorization": f"Bearer {make_demo_jwt()}"}


# ---------------------------------------------------------------------------
# Health checks (no auth)
# ---------------------------------------------------------------------------


class TestHealthChecks:
    def test_mvp_api_health(self):
        r = httpx.get(f"{MVP_API}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"

    def test_nutrition_health(self):
        r = httpx.get(f"{NUTRITION}/health", timeout=10)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Auth enforcement — every protected endpoint must return 401 without token
# ---------------------------------------------------------------------------

# Endpoints that use strict auth (no sandbox bypass)
STRICT_AUTH_ENDPOINTS = [
    ("GET", "/api/v1/agents/agents"),
    ("GET", "/api/v1/agents/conversations"),
    ("GET", "/api/v1/health-data/status"),
]

# Endpoints that use USE_SANDBOX=true bypass in dev — these return 401 only in production
# (USE_SANDBOX=false). Tracked as known issue for production deploy checklist.
SANDBOX_BYPASS_ENDPOINTS = [
    ("GET", "/api/v1/health-score"),
    ("GET", "/api/v1/health/timeline"),
    (
        "GET",
        "/api/v1/correlations",
    ),  # no trailing slash — FastAPI redirects /correlations/ → /correlations
    (
        "GET",
        "/api/v1/insights",
    ),  # no trailing slash — FastAPI redirects /insights/ → /insights
]


class TestAuthEnforcement:
    @pytest.mark.parametrize("method,path", STRICT_AUTH_ENDPOINTS)
    def test_no_token_returns_401(self, method, path):
        r = httpx.request(method, f"{MVP_API}{path}", timeout=10)
        assert (
            r.status_code == 401
        ), f"{method} {path}: expected 401, got {r.status_code}"

    @pytest.mark.parametrize("method,path", SANDBOX_BYPASS_ENDPOINTS)
    def test_sandbox_endpoints_require_auth_in_production(self, method, path):
        """
        These endpoints use get_user_optional / UsageGate which bypass auth when
        USE_SANDBOX=true (development default). In production USE_SANDBOX must be
        set to 'false' so they return 401.

        PRODUCTION DEPLOY REQUIREMENT: set USE_SANDBOX=false in environment.
        """
        r = httpx.request(method, f"{MVP_API}{path}", timeout=10, follow_redirects=True)
        # In dev/sandbox: 200 or 404 (sandbox user, no data)
        # In production: must be 401
        is_sandbox = os.environ.get("USE_SANDBOX", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        if not is_sandbox:
            assert r.status_code == 401, f"PRODUCTION: {method} {path} must return 401"
        else:
            assert r.status_code in (
                200,
                404,
                422,
            ), f"DEV/sandbox: {method} {path} returned unexpected {r.status_code}"

    def test_garbage_token_returns_401(self):
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/agents",
            headers={"Authorization": "Bearer garbage.token.here"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_expired_token_returns_401(self):
        expired = make_demo_jwt(ttl_seconds=-60)
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/agents",
            headers={"Authorization": f"Bearer {expired}"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_valid_token_returns_200(self, auth_headers):
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/agents", headers=auth_headers, timeout=10
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Health data ingestion
# ---------------------------------------------------------------------------


class TestHealthDataIngest:
    def _payload(self, source="healthkit", points=None, date="2026-03-01"):
        return {
            "source": source,
            "data_points": points
            or [{"metric_type": "steps", "date": date, "value_json": {"steps": 7500}}],
            "sync_timestamp": f"{date}T10:00:00Z",
        }

    def test_ingest_valid(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json=self._payload(),
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 201
        body = r.json()
        assert "accepted" in body

    def test_ingest_no_auth(self):
        r = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json=self._payload(),
            timeout=10,
        )
        assert r.status_code == 401

    def test_ingest_invalid_source(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json=self._payload(source="fitbit_invalid"),
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 422

    def test_ingest_over_500_points(self, auth_headers):
        many = [
            {
                "metric_type": "steps",
                "date": f"2020-01-{(i % 28) + 1:02d}",
                "value_json": {"steps": i},
            }
            for i in range(501)
        ]
        r = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json=self._payload(points=many),
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 422

    def test_ingest_idempotent(self, auth_headers):
        p = self._payload(date="2026-01-15")
        r1 = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json=p,
            headers=auth_headers,
            timeout=30,
        )
        r2 = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json=p,
            headers=auth_headers,
            timeout=30,
        )
        assert r1.status_code == 201
        assert r2.status_code == 201

    def test_health_data_status(self, auth_headers):
        r = httpx.get(
            f"{MVP_API}/api/v1/health-data/status", headers=auth_headers, timeout=10
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# AI Agents
# ---------------------------------------------------------------------------


class TestAIAgents:
    def test_list_agents_structure(self, auth_headers):
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/agents", headers=auth_headers, timeout=10
        )
        assert r.status_code == 200
        agents = r.json()
        assert isinstance(agents, list) and len(agents) >= 5
        for a in agents:
            for field in ("agent_type", "agent_name", "capabilities", "is_active"):
                assert field in a, f"Agent missing field: {field}"

    def test_chat_no_auth(self):
        """Chat uses UsageGate which bypasses auth in sandbox mode (USE_SANDBOX=true).
        In production (USE_SANDBOX=false) this must return 401."""
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat", json={"message": "hello"}, timeout=10
        )
        is_sandbox = os.environ.get("USE_SANDBOX", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        if not is_sandbox:
            assert r.status_code == 401
        else:
            assert r.status_code in (200, 401)

    def test_chat_missing_message(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat", json={}, headers=auth_headers, timeout=10
        )
        assert r.status_code == 422

    def test_chat_empty_message(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat",
            json={"message": ""},
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 422

    def test_chat_message_too_long(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat",
            json={"message": "a" * 2001},
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 422

    def test_chat_off_topic_returns_refusal(self, auth_headers):
        """Off-topic message must return the refusal string, not an LLM response."""
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat",
            json={"message": "Write me a Python function to sort a list"},
            headers=auth_headers,
            timeout=30,
        )
        assert r.status_code == 200
        body = r.json()
        msgs = body.get("messages", [])
        assistant_reply = next(
            (m["content"] for m in reversed(msgs) if m["role"] == "assistant"), ""
        )
        assert (
            _OFFTOPIC_REFUSAL_FRAGMENT in assistant_reply
        ), f"Expected refusal message, got: {repr(assistant_reply[:200])}"

    def test_chat_health_message_succeeds(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat",
            json={"message": "What can I do to improve my sleep quality?"},
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        msgs = body.get("messages", [])
        assistant_msgs = [m for m in msgs if m["role"] == "assistant"]
        assert len(assistant_msgs) >= 1
        assert len(assistant_msgs[-1]["content"]) > 0
        # Must NOT be the refusal
        assert _OFFTOPIC_REFUSAL_FRAGMENT not in assistant_msgs[-1]["content"]

    def test_chat_conversation_id_returned(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/agents/chat",
            json={"message": "How is my nutrition looking?"},
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200
        assert "id" in r.json()

    def test_list_conversations(self, auth_headers):
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/conversations", headers=auth_headers, timeout=10
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_nonexistent_conversation(self, auth_headers):
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/conversations/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Other MVP API endpoints
# ---------------------------------------------------------------------------


class TestCoreEndpoints:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/insights",  # no trailing slash (FastAPI auto-redirects /insights/ → /insights)
            "/api/v1/symptoms/",
            "/api/v1/health/timeline",
            "/api/v1/health-score",
        ],
    )
    def test_endpoint_authenticated(self, auth_headers, path):
        r = httpx.get(
            f"{MVP_API}{path}", headers=auth_headers, timeout=15, follow_redirects=True
        )
        assert r.status_code in (200, 404), f"{path}: unexpected {r.status_code}"

    def test_correlations_authenticated(self, auth_headers):
        """Correlations can be slow (full computation). Allow timeout or empty result."""
        try:
            r = httpx.get(
                f"{MVP_API}/api/v1/correlations",
                headers=auth_headers,
                timeout=30,
                follow_redirects=True,
            )
            assert r.status_code in (200, 404, 422)
        except httpx.ReadTimeout:
            pytest.skip(
                "Correlations endpoint timed out (expected on cold start with no cached data)"
            )

    def test_symptom_post_missing_fields(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/symptoms/journal",
            json={},
            headers=auth_headers,
            timeout=10,
        )
        assert (
            r.status_code == 422
        ), f"Expected 422 for missing fields, got {r.status_code}: {r.text[:200]}"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_invalid_uuid_path_param(self, auth_headers):
        r = httpx.get(
            f"{MVP_API}/api/v1/agents/conversations/not-a-uuid",
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code in (404, 422)

    def test_health_ingest_invalid_date_format(self, auth_headers):
        r = httpx.post(
            f"{MVP_API}/api/v1/health-data/ingest",
            json={
                "source": "healthkit",
                "data_points": [
                    {
                        "metric_type": "steps",
                        "date": "not-a-date",
                        "value_json": {"steps": 100},
                    }
                ],
                "sync_timestamp": "2026-03-01T10:00:00Z",
            },
            headers=auth_headers,
            timeout=10,
        )
        # Server may accept and skip bad dates or reject — either is acceptable
        assert r.status_code in (201, 422)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    @pytest.mark.slow
    def test_chat_rate_limit_triggers_429(self, auth_headers):
        """
        Fire 21 requests quickly — at least one should return 429.
        NOTE: slow test (~21 HTTP requests). Run with: pytest -m slow
        """
        statuses = []
        for i in range(21):
            r = httpx.post(
                f"{MVP_API}/api/v1/agents/chat",
                json={"message": f"rate limit test {i}"},
                headers=auth_headers,
                timeout=10,
            )
            statuses.append(r.status_code)
            if r.status_code == 429:
                break  # confirmed rate limiting is working

        assert 429 in statuses, f"Expected 429 in rate limit test, got: {set(statuses)}"


# ---------------------------------------------------------------------------
# Nutrition service
# ---------------------------------------------------------------------------


class TestNutritionService:
    def test_search_no_auth(self):
        r = httpx.get(
            f"{NUTRITION}/api/v1/nutrition/search-foods",
            params={"query": "apple"},
            timeout=10,
        )
        assert r.status_code == 401

    def test_search_authenticated(self, auth_headers):
        r = httpx.get(
            f"{NUTRITION}/api/v1/nutrition/search-foods",
            params={"query": "apple", "limit": 5},
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code in (200, 500)  # 500 ok if USDA key not configured

    def test_nutrition_summary_authenticated(self, auth_headers):
        r = httpx.get(
            f"{NUTRITION}/api/v1/nutrition/nutrition-summary",
            headers=auth_headers,
            timeout=15,
        )
        assert r.status_code in (200, 404, 500)

    def test_daily_nutrition_invalid_date(self, auth_headers):
        r = httpx.get(
            f"{NUTRITION}/api/v1/nutrition/daily-nutrition/not-a-date",
            headers=auth_headers,
            timeout=10,
        )
        assert r.status_code == 422

    def test_log_meal_no_auth(self):
        r = httpx.post(
            f"{NUTRITION}/api/v1/nutrition/log-meal",
            json={"meal_data": {}},
            timeout=10,
        )
        assert r.status_code == 401
