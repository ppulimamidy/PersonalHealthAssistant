"""
GraphQL BFF (Backend-for-Frontend) Service
Unified GraphQL interface for Personal Physician Assistant (PPA)
Provides type-safe, efficient data access for frontend applications.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from strawberry.fastapi import GraphQLRouter
import redis.asyncio as redis

from common.config.settings import settings
from common.middleware.auth import require_auth
from common.models.base import (
    create_success_response,
    create_error_response,
    ErrorCode,
    BaseServiceException,
)
from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker, RetryHandler, TimeoutHandler
from common.middleware.prometheus_metrics import setup_prometheus_metrics

# Import GraphQL schema and resolvers
from .schema import schema
from .services.data_service import DataService
from .services.reasoning_service import ReasoningService
from .services.cache_service import CacheService

logger = get_logger(__name__)

# Service registry for microservices
SERVICE_REGISTRY = {
    "ai_reasoning_orchestrator": {
        "url": settings.AI_REASONING_ORCHESTRATOR_URL,
        "circuit_breaker": CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, name="ai_reasoning_orchestrator"
        ),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3),
    },
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

# Redis client for caching
redis_client: Optional[redis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting GraphQL BFF Service...")

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

    # Initialize services
    try:
        app.state.data_service = DataService(SERVICE_REGISTRY)
        app.state.reasoning_service = ReasoningService(SERVICE_REGISTRY)
        app.state.cache_service = CacheService(redis_client)
        logger.info("✅ BFF services initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize BFF services: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down GraphQL BFF Service...")
    if redis_client:
        await redis_client.close()


# Create FastAPI app
app = FastAPI(
    title="GraphQL BFF Service",
    description="Unified GraphQL interface for Personal Physician Assistant (PPA)",
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
setup_prometheus_metrics(app, service_name="graphql-bff-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "graphql-bff-service")
except ImportError:
    pass

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    path="/graphql",
    context_getter=lambda request: {
        "request": request,
        "data_service": app.state.data_service,
        "reasoning_service": app.state.reasoning_service,
        "cache_service": app.state.cache_service,
        "user": getattr(request.state, "user", None),
    },
)

# Include GraphQL router
app.include_router(graphql_app)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return create_success_response(
        data={
            "status": "healthy",
            "service": "graphql-bff",
            "version": "1.0.0",
            "timestamp": time.time(),
        },
        message="GraphQL BFF Service is healthy",
    )


# GraphQL playground endpoint
@app.get("/playground")
async def graphql_playground():
    """Redirect to GraphQL playground"""
    return {"message": "GraphQL Playground available at /graphql"}


# REST fallback endpoints for non-GraphQL clients
# Note: Health query endpoint is now handled by the dedicated endpoint below


@app.get("/api/v1/health/daily-summary-test")
async def daily_summary_test():
    """
    Test endpoint for daily summary without authentication.
    """
    try:
        result = await app.state.data_service.get_daily_summary(user_id="test-user")

        return create_success_response(
            data=result, message="Daily summary retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Daily summary test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health/unified-dashboard-test")
async def unified_dashboard_test():
    """
    Test endpoint for unified dashboard without authentication.
    """
    try:
        result = await app.state.data_service.get_unified_dashboard(user_id="test-user")

        return create_success_response(
            data=result, message="Unified dashboard retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Unified dashboard test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health/daily-summary")
async def daily_summary():
    """
    Daily summary endpoint accessible via GraphQL BFF.
    """
    try:
        result = await app.state.data_service.get_daily_summary(user_id="test-user")

        return create_success_response(
            data=result, message="Daily summary retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Daily summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/health/analyze-symptoms")
async def analyze_symptoms(request: Request):
    """
    Symptom analysis endpoint accessible via GraphQL BFF.
    """
    try:
        result = await app.state.data_service.analyze_symptoms(
            user_id="test-user", request_data=await request.json()
        )

        return create_success_response(
            data=result, message="Symptom analysis completed successfully"
        )

    except Exception as e:
        logger.error(f"Symptom analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/health/query")
async def health_query(request: Request):
    """
    Health query endpoint accessible via GraphQL BFF.
    """
    try:
        result = await app.state.data_service.health_query(
            user_id="test-user", request_data=await request.json()
        )

        return create_success_response(
            data=result, message="Health query processed successfully"
        )

    except Exception as e:
        logger.error(f"Health query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/health/doctor-report")
async def doctor_report(request: Request):
    """
    Doctor report endpoint accessible via GraphQL BFF.
    """
    try:
        result = await app.state.data_service.doctor_report(
            user_id="test-user", request_data=await request.json()
        )

        return create_success_response(
            data=result, message="Doctor report generated successfully"
        )

    except Exception as e:
        logger.error(f"Doctor report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: Doctor report endpoint is now handled by the dedicated endpoint above

# Error handlers
@app.exception_handler(BaseServiceException)
async def service_exception_handler(request, exc: BaseServiceException):
    """Handle service exceptions"""
    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        error_details=exc.error_details,
        severity=exc.severity,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return create_error_response(
        error_code=ErrorCode.UNKNOWN_ERROR, message="An unexpected error occurred"
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
