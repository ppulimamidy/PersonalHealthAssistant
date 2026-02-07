"""
AI Insights Service Main Application
FastAPI application for AI-powered health insights and recommendations.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from apps.ai_insights.api import (
    insights_router,
    recommendations_router,
    health_scores_router,
    patterns_router,
    agents_router,
)
from common.middleware.auth import AuthMiddleware
from common.middleware.error_handling import ErrorHandlingMiddleware
from common.utils.logging import get_logger
from common.models.registry import register_model
from common.middleware.prometheus_metrics import setup_prometheus_metrics

# Import all models that are referenced in relationships
from .models.insight_models import InsightDB, HealthPatternDB

# Import User model from auth service for relationship resolution
try:
    from apps.auth.models.user import User
except ImportError:
    # If auth service is not available, create a stub
    class User:
        __tablename__ = "users"
        pass


# Global logger
logger = get_logger("ai_insights.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting AI Insights Service...")

    # Register models in the global registry
    try:
        register_model("InsightDB", InsightDB)
        register_model("HealthPatternDB", HealthPatternDB)
        logger.info("AI Insights models registered in global registry")
    except Exception as e:
        logger.warning(f"Failed to register AI Insights models: {e}")

    # Initialize services and connections
    logger.info("✅ AI Insights Service started successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down AI Insights Service...")


# Create FastAPI application
app = FastAPI(
    title="AI Insights Service",
    description="Advanced AI-powered health insights and recommendations for VitaSense",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
    ],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
# app.add_middleware(ErrorHandlingMiddleware)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="ai-insights-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "ai-insights-service")
except ImportError:
    pass

# Add auth middleware
from common.middleware.auth import AuthMiddleware

auth_middleware = AuthMiddleware()
app.middleware("http")(auth_middleware)

# Include routers
app.include_router(insights_router, prefix="/api/v1/ai-insights")
app.include_router(recommendations_router, prefix="/api/v1/ai-insights")
app.include_router(health_scores_router, prefix="/api/v1/ai-insights")
app.include_router(patterns_router, prefix="/api/v1/ai-insights")
app.include_router(agents_router, prefix="/api/v1/ai-insights")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Insights Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Advanced AI-powered health insights and recommendations",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "ai_insights",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "insights": "/api/v1/ai-insights/insights",
            "recommendations": "/api/v1/ai-insights/recommendations",
            "health_scores": "/api/v1/ai-insights/health-scores",
            "patterns": "/api/v1/ai-insights/patterns",
            "agents": "/api/v1/ai-insights/agents",
        },
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"service": "ai_insights", "status": "ready", "version": "1.0.0"}


@app.get("/test-public")
async def test_public_endpoint():
    """Test public endpoint to verify auth middleware behavior."""
    return {
        "message": "This is a public test endpoint",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8200, reload=True, log_level="info")
