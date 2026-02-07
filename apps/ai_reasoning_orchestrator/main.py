"""
AI Reasoning Orchestrator Service
Central intelligence layer for Personal Physician Assistant (PPA)
Orchestrates data from all microservices to provide unified, explainable health insights.
"""

import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import redis.asyncio as redis

from common.config.settings import settings
from common.models.base import create_success_response
from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker, RetryHandler, TimeoutHandler
from common.middleware.prometheus_metrics import setup_prometheus_metrics

# Import orchestrator components
from .services.reasoning_engine import AIReasoningEngine
from .services.data_aggregator import DataAggregator
from .services.knowledge_integrator import KnowledgeIntegrator

# Import routers
from .api.reasoning import router as reasoning_router
from .api.health_endpoints import router as health_router
from .api.websocket import router as ws_router

logger = get_logger(__name__)

# Service registry for microservices
SERVICE_REGISTRY = {
    "health_tracking": {
        "url": settings.HEALTH_TRACKING_SERVICE_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="health_tracking"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
    "medical_records": {
        "url": settings.MEDICAL_RECORDS_SERVICE_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="medical_records"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
    "ai_insights": {
        "url": settings.AI_INSIGHTS_SERVICE_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="ai_insights"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
    "knowledge_graph": {
        "url": settings.KNOWLEDGE_GRAPH_SERVICE_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="knowledge_graph"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
    "nutrition": {
        "url": settings.NUTRITION_SERVICE_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="nutrition"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
    "device_data": {
        "url": settings.DEVICE_DATA_SERVICE_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="device_data"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
}

# Redis client for caching and session management
redis_client: Optional[redis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting AI Reasoning Orchestrator...")

    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis client initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Redis client: {e}")
        redis_client = None

    # Store redis_client on app.state so routers can access it
    app.state.redis_client = redis_client

    # Initialize orchestrator components
    try:
        app.state.reasoning_engine = AIReasoningEngine()
        app.state.data_aggregator = DataAggregator(SERVICE_REGISTRY)
        app.state.knowledge_integrator = KnowledgeIntegrator()
        logger.info("✅ Orchestrator components initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator components: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down AI Reasoning Orchestrator...")
    if redis_client:
        await redis_client.close()


# Create FastAPI app
app = FastAPI(
    title="AI Reasoning Orchestrator",
    description="Central intelligence layer for Personal Physician Assistant (PPA)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="ai-reasoning-orchestrator-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "ai-reasoning-orchestrator-service")
except ImportError:
    pass

# Include routers
app.include_router(reasoning_router)
app.include_router(health_router)
app.include_router(ws_router)

# Health check endpoint (kept in main.py as it's app-level)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return create_success_response(
        data={
            "status": "healthy",
            "service": "ai-reasoning-orchestrator",
            "version": "1.0.0",
            "timestamp": time.time(),
        },
        message="AI Reasoning Orchestrator is healthy",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
