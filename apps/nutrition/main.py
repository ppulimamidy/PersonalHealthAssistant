"""
Nutrition Service Main Application

FastAPI application for the nutrition microservice providing food recognition,
nutritional analysis, and personalized recommendations.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import uvicorn

# Add parent directories to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Ensure service-local .env files are loaded (e.g., USDA_API_KEY).
# Note: common Settings uses `env_file=".env"` relative to CWD, which may not be this folder.
load_dotenv(dotenv_path=current_dir / ".env", override=False)
load_dotenv(dotenv_path=current_dir / ".env.local", override=False)

from common.config.settings import get_settings
from common.database.connection import get_db_manager
from common.middleware.auth import AuthMiddleware
from common.utils.logging import setup_logging
from common.models.registry import register_model
from common.middleware.prometheus_metrics import setup_prometheus_metrics

from apps.nutrition.api.nutrition import nutrition_router
from apps.nutrition.api.food_recognition import food_recognition_router
from apps.nutrition.api.recommendations import recommendations_router
from apps.nutrition.api.goals import goals_router
from apps.nutrition.services.nutrition_service import NutritionService
from apps.nutrition.services.food_recognition_service import FoodRecognitionService
from apps.nutrition.services.recommendations_service import RecommendationsService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
ALLOW_NO_DB = os.getenv("NUTRITION_ALLOW_NO_DB", "true").lower() in ("true", "1", "yes")
AUTO_CREATE_TABLES = os.getenv("NUTRITION_AUTO_CREATE_TABLES", "false").lower() in ("true", "1", "yes")

# External service URLs
HEALTH_TRACKING_SERVICE_URL = os.getenv(
    "HEALTH_TRACKING_SERVICE_URL", "http://health-tracking-service:8002"
)
MEDICAL_ANALYSIS_SERVICE_URL = os.getenv(
    "MEDICAL_ANALYSIS_SERVICE_URL", "http://medical-analysis-service:8006"
)
USER_PROFILE_SERVICE_URL = os.getenv(
    "USER_PROFILE_SERVICE_URL", "http://user-profile-service:8001"
)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

# API Keys for external services
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
AZURE_VISION_API_KEY = os.getenv("AZURE_VISION_API_KEY")
NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY")
NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
USDA_API_KEY = os.getenv("USDA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Nutrition Service...")

    # Register models in the global registry
    try:
        from apps.nutrition.models.database_models import (
            FoodRecognitionResult,
            MealLog,
            NutritionGoal,
        )

        register_model("FoodRecognitionResult", FoodRecognitionResult)
        register_model("MealLog", MealLog)
        register_model("NutritionGoal", NutritionGoal)
        logger.info("Nutrition models registered in global registry")
    except Exception as e:
        logger.warning(f"Failed to register nutrition models: {e}")

    # Initialize services
    app.state.nutrition_service = NutritionService()
    app.state.food_recognition_service = FoodRecognitionService()
    app.state.recommendations_service = RecommendationsService()

    # Log which external nutrition sources are configured (never log secrets).
    try:
        ns = app.state.nutrition_service
        logger.info(
            "Nutrition sources configured: nutritionix=%s usda=%s openfoodfacts=%s",
            bool(getattr(ns, "nutritionix_available", False)),
            bool(getattr(ns, "usda_available", False)),
            bool(getattr(ns, "openfoodfacts_available", False)),
        )
    except Exception:
        pass

    # Test database connection
    try:
        db_manager = get_db_manager()
        async_session_factory = db_manager.get_async_session_factory()
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection established")
        app.state.db_available = True

        # Create schema/tables if missing (no seeding, just DDL)
        if AUTO_CREATE_TABLES:
            try:
                from common.models.base import Base
                import apps.nutrition.models.database_models  # noqa: F401

                engine = db_manager.create_async_engine()
                async with engine.begin() as conn:
                    await conn.execute(text("CREATE SCHEMA IF NOT EXISTS nutrition"))
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Nutrition schema/tables ensured (auto-create)")
            except Exception as e:
                logger.warning(f"Auto-create nutrition tables failed: {e}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        app.state.db_available = False
        if not ALLOW_NO_DB:
            raise
        logger.warning(
            "Starting Nutrition Service without a database (NUTRITION_ALLOW_NO_DB=true). "
            "Nutrition history/logging endpoints may return empty results."
        )

    logger.info("Nutrition Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Nutrition Service...")
    # No explicit disconnect needed for SQLAlchemy async engine


# Create FastAPI application
app = FastAPI(
    title="Nutrition Service",
    description="Comprehensive nutrition analysis and food recognition service",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="nutrition-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "nutrition-service")
except ImportError:
    pass

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Note: TrustedHostMiddleware is skipped – this microservice sits behind
# the MVP API gateway and Render's own routing; the default ALLOWED_HOSTS
# (localhost, 127.0.0.1) would reject Render's health-check probes.

# Add auth middleware
# Note: AuthMiddleware is an ASGI middleware (scope/receive/send), so it must be added via add_middleware.
app.add_middleware(AuthMiddleware)

# Note: setup_security and setup_error_handlers are omitted for the nutrition
# microservice to keep the middleware stack lean. The MVP API gateway handles
# security checks, and FastAPI's built-in exception handlers are sufficient here.

# Include routers
app.include_router(nutrition_router, prefix="/api/v1/nutrition", tags=["nutrition"])
app.include_router(
    food_recognition_router,
    prefix="/api/v1/food-recognition",
    tags=["food-recognition"],
)
app.include_router(
    recommendations_router, prefix="/api/v1/recommendations", tags=["recommendations"]
)
app.include_router(goals_router, prefix="/api/v1/goals", tags=["goals"])


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "message": "Personal Health Assistant - Nutrition Service",
        "version": "1.0.0",
        "docs": "/docs" if ENVIRONMENT == "development" else None,
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint — always returns 200 so Render's probe passes."""
    db_status = "unavailable"
    if getattr(app.state, "db_available", False):
        try:
            db_manager = get_db_manager()
            async_session_factory = db_manager.get_async_session_factory()
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

    return {
        "service": "nutrition",
        "status": "healthy",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "database": db_status,
    }


@app.get("/ready", tags=["health"])
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint for Kubernetes."""
    try:
        # Check database connection
        db_manager = get_db_manager()
        async_session_factory = db_manager.get_async_session_factory()
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))

        # Check if all required services are available
        required_services = [
            "nutrition_service",
            "food_recognition_service",
            "recommendations_service",
        ]

        for service_name in required_services:
            if not hasattr(app.state, service_name):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {service_name} not initialized",
                )

        return {"service": "nutrition", "status": "ready", "version": "1.0.0"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service not ready"
        )


if __name__ == "__main__":
    uvicorn.run(
        "apps.nutrition.main:app",
        host="0.0.0.0",
        port=8007,
        reload=ENVIRONMENT == "development",
        log_level=LOG_LEVEL.lower(),
    )
