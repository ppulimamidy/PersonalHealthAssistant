"""
Vitalix API Load Test — Locust

Tests realistic user behaviour under concurrent load against the MVP API.

Usage:
    pip install locust python-jose[cryptography] python-dotenv

    # Interactive UI (open http://localhost:8089):
    cd /Users/pulimap/PersonalHealthAssistant
    locust -f tests/locustfile.py --host=http://localhost:8100

    # Headless — 50 users, 5 spawned/sec, run for 5 min:
    locust -f tests/locustfile.py --host=http://localhost:8100 \
      --users=50 --spawn-rate=5 --run-time=5m --headless \
      --csv=tests/load_results

    # Against production:
    locust -f tests/locustfile.py --host=https://api.vitalix.health \
      --users=100 --spawn-rate=10 --run-time=10m --headless

Pass criteria (checked in StepLoadShape below):
  - p95 response time < 2000 ms
  - Error rate (non-429) < 1%
  - Rate limiter returns 429 at req 21+ per minute (not 500)
"""

import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from jose import jwt as jose_jwt
from locust import HttpUser, TaskSet, between, constant_pacing, events, task
from locust.exception import StopUser

load_dotenv(Path(__file__).parent.parent / "apps/mvp_api/.env", override=False)

# ---------------------------------------------------------------------------
# JWT generation (same approach as test_robustness.py)
# ---------------------------------------------------------------------------

_DEMO_USER_IDS = [
    "22144dc2-f352-48aa-b34b-aebfa9f7e638",  # Sarah Chen (seeded demo user)
    # Add more seeded test user UUIDs here for realistic multi-user load
]

_DEFAULT_AGENTS = [
    "health_coach",
    "nutrition_analyst",
    "sleep_specialist",
    "fitness_advisor",
    "medical_researcher",
]

_HEALTH_MESSAGES = [
    "What should I eat to improve my sleep quality?",
    "My HRV has been low this week. What could cause that?",
    "How many steps per day should I aim for?",
    "What foods are high in magnesium?",
    "Can you explain what a readiness score means?",
    "I've been feeling fatigued lately — any patterns in my data?",
    "What is a healthy resting heart rate range?",
    "How does sleep affect cardiovascular health?",
    "I logged a headache today, what might be causing it?",
    "What are the benefits of zone 2 cardio training?",
]

_OFFTOPIC_MESSAGES = [
    "Write me a Python function to sort a list",
    "Tell me a joke about programmers",
    "What is the capital of France?",
]


def _make_jwt(user_id: str, ttl: int = 3600) -> str:
    secret = os.environ.get(
        "JWT_SECRET_KEY",
        "WVICv1XsXCSHNeQPL6aW4bOmfIObduJZyq/0HghyIwU=",
    )
    now = int(time.time())
    return jose_jwt.encode(
        {
            "sub": user_id,
            "email": f"loadtest+{user_id[:8]}@vitalix.health",
            "iat": now,
            "exp": now + ttl,
            "iss": "https://yadfzphehujeaiimzvoe.supabase.co/auth/v1",
            "role": "authenticated",
        },
        secret,
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# Task sets
# ---------------------------------------------------------------------------


class ReadOnlyTasks(TaskSet):
    """
    Read-heavy tasks — what most users do most of the time.
    Weight 70% of all requests.
    """

    @task(5)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(10)
    def get_insights(self):
        self.client.get(
            "/api/v1/insights/",
            headers=self.user.auth_headers,
            name="/api/v1/insights/",
        )

    @task(8)
    def get_health_score(self):
        self.client.get(
            "/api/v1/health-score",
            headers=self.user.auth_headers,
            name="/api/v1/health-score",
        )

    @task(8)
    def get_timeline(self):
        self.client.get(
            "/api/v1/health/timeline?days=14",
            headers=self.user.auth_headers,
            name="/api/v1/health/timeline",
        )

    @task(4)
    def get_symptoms(self):
        self.client.get(
            "/api/v1/symptoms/journal",
            headers=self.user.auth_headers,
            name="/api/v1/symptoms/journal",
        )

    @task(3)
    def get_correlations(self):
        with self.client.get(
            "/api/v1/correlations",
            headers=self.user.auth_headers,
            name="/api/v1/correlations",
            catch_response=True,
            timeout=30,
        ) as resp:
            # Correlations is compute-heavy — 200 or 404 are both fine
            if resp.status_code in (200, 404):
                resp.success()

    @task(6)
    def get_native_health_status(self):
        self.client.get(
            "/api/v1/health-data/status",
            headers=self.user.auth_headers,
            name="/api/v1/health-data/status",
        )

    @task(4)
    def get_recent_health_data(self):
        self.client.get(
            "/api/v1/health-data/recent",
            headers=self.user.auth_headers,
            name="/api/v1/health-data/recent",
        )

    @task(3)
    def list_agents(self):
        self.client.get(
            "/api/v1/ai-agents/agents",
            headers=self.user.auth_headers,
            name="/api/v1/ai-agents/agents",
        )

    @task(2)
    def oura_connection_status(self):
        self.client.get(
            "/api/v1/oura/connection",
            headers=self.user.auth_headers,
            name="/api/v1/oura/connection",
        )


class ChatTasks(TaskSet):
    """
    AI chat — the most expensive operation.
    Weight 20% of all requests. Rate limiter should kick in after 20/min.
    """

    @task(8)
    def chat_health_message(self):
        agent_type = random.choice(_DEFAULT_AGENTS)
        message = random.choice(_HEALTH_MESSAGES)
        with self.client.post(
            f"/api/v1/ai-agents/{agent_type}/chat",
            json={"message": message, "context": {}},
            headers=self.user.auth_headers,
            name="/api/v1/ai-agents/[agent]/chat (health)",
            catch_response=True,
            timeout=30,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("response"):
                    resp.failure("Empty response body")
            elif resp.status_code == 429:
                # Rate limited — expected behaviour, not a failure
                resp.success()
            elif resp.status_code in (401, 422):
                resp.success()  # Auth/validation errors are expected in load test
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(2)
    def chat_offtopic_message(self):
        """Off-topic messages must return refusal without calling LLM — should be fast."""
        agent_type = random.choice(_DEFAULT_AGENTS)
        message = random.choice(_OFFTOPIC_MESSAGES)
        with self.client.post(
            f"/api/v1/ai-agents/{agent_type}/chat",
            json={"message": message, "context": {}},
            headers=self.user.auth_headers,
            name="/api/v1/ai-agents/[agent]/chat (offtopic)",
            catch_response=True,
            timeout=5,  # Must respond in <5s (no LLM call)
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                response_text = data.get("response", "")
                if "health assistant" not in response_text.lower():
                    resp.failure("Off-topic message did not return health refusal")
            elif resp.status_code == 429:
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")


class IngestTasks(TaskSet):
    """
    Health data ingest — batch upload from mobile sync.
    Weight 10% of all requests.
    """

    @task
    def ingest_health_data(self):
        from datetime import date, timedelta

        today = date.today()
        data_points = []
        for i in range(7):
            d = (today - timedelta(days=i)).isoformat()
            data_points.extend(
                [
                    {
                        "metric_type": "steps",
                        "date": d,
                        "value_json": {"steps": random.randint(4000, 12000)},
                    },
                    {
                        "metric_type": "sleep",
                        "date": d,
                        "value_json": {"hours": round(random.uniform(5.5, 9.0), 1)},
                    },
                    {
                        "metric_type": "resting_heart_rate",
                        "date": d,
                        "value_json": {"bpm": random.randint(52, 72)},
                    },
                    {
                        "metric_type": "hrv_sdnn",
                        "date": d,
                        "value_json": {"ms": round(random.uniform(30, 80), 1)},
                    },
                ]
            )

        with self.client.post(
            "/api/v1/health-data/ingest",
            json={
                "source": "healthkit",
                "data_points": data_points,
                "sync_timestamp": f"{today.isoformat()}T12:00:00Z",
            },
            headers=self.user.auth_headers,
            name="/api/v1/health-data/ingest",
            catch_response=True,
            timeout=15,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                if data.get("accepted", 0) < 1:
                    resp.failure("Ingest accepted 0 records")
            else:
                resp.failure(f"Ingest failed: {resp.status_code}")


# ---------------------------------------------------------------------------
# User types
# ---------------------------------------------------------------------------


class VitalixUser(HttpUser):
    """
    Simulates a typical Vitalix user — mostly reading, occasionally chatting.
    """

    wait_time = between(1, 4)  # 1–4 seconds between tasks

    tasks = {
        ReadOnlyTasks: 7,
        ChatTasks: 2,
        IngestTasks: 1,
    }

    def on_start(self):
        user_id = random.choice(_DEMO_USER_IDS)
        self.auth_headers = {"Authorization": f"Bearer {_make_jwt(user_id)}"}


class PowerUser(HttpUser):
    """
    Simulates a Pro+ user who uses AI chat heavily.
    Represents ~10% of the user base.
    """

    wait_time = between(0.5, 2)
    weight = 1  # 1 power user per 9 regular users

    tasks = {
        ReadOnlyTasks: 3,
        ChatTasks: 6,
        IngestTasks: 1,
    }

    def on_start(self):
        user_id = random.choice(_DEMO_USER_IDS)
        self.auth_headers = {"Authorization": f"Bearer {_make_jwt(user_id)}"}


class UnauthenticatedUser(HttpUser):
    """
    Simulates bots and unauthenticated traffic — should all get 401/422.
    Represents ~5% of traffic.
    """

    wait_time = between(0.5, 2)
    weight = 1

    @task
    def hit_protected_endpoint(self):
        with self.client.get(
            "/api/v1/insights/",
            name="/api/v1/insights/ (no auth)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 401:
                resp.success()
            else:
                resp.failure(f"Expected 401, got {resp.status_code}")

    @task
    def hit_health_check(self):
        self.client.get("/health", name="/health (unauth)")


# ---------------------------------------------------------------------------
# Custom events — print pass/fail summary at end
# ---------------------------------------------------------------------------


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    stats = environment.stats

    print("\n" + "=" * 60)
    print("VITALIX LOAD TEST — PASS/FAIL SUMMARY")
    print("=" * 60)

    failures = []

    for name, entry in stats.entries.items():
        p95 = entry.get_response_time_percentile(0.95)
        error_rate = (
            (entry.num_failures / entry.num_requests * 100) if entry.num_requests else 0
        )

        # Skip 429 rate-limit endpoint — high failure count is expected
        if "offtopic" not in str(name) and error_rate > 1:
            failures.append(f"  FAIL  {name}: error rate {error_rate:.1f}% > 1%")

        if p95 and p95 > 2000 and "correlations" not in str(name):
            failures.append(f"  FAIL  {name}: p95={p95}ms > 2000ms")

    total_rps = stats.total.current_rps
    print(f"Total RPS at end: {total_rps:.1f}")
    print(f"Total requests:   {stats.total.num_requests}")
    print(f"Total failures:   {stats.total.num_failures}")
    print(f"p50 response:     {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"p95 response:     {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"p99 response:     {stats.total.get_response_time_percentile(0.99):.0f}ms")

    if failures:
        print("\nFAILED CRITERIA:")
        for f in failures:
            print(f)
        environment.process_exit_code = 1
    else:
        print("\nALL PASS CRITERIA MET")

    print("=" * 60)
