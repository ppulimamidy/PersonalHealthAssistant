"""
Main FastAPI application for the Personal Health Assistant Authentication Service.

This is the entry point for the authentication service, providing:
- FastAPI application setup
- Middleware configuration
- Router registration
- Health checks
- Error handling
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Add the project root to Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from common.config.settings import get_settings
from common.utils.logging import get_logger, setup_logging
from common.database.connection import get_db_manager
from common.models.registry import register_model
from common.middleware.prometheus_metrics import setup_prometheus_metrics

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Get database manager
db_manager = get_db_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Personal Health Assistant Authentication Service...")

    # Register models in the global registry
    try:
        from .models.user import User

        register_model("User", User)
        logger.info("User model registered in global registry")
    except Exception as e:
        logger.warning(f"Failed to register User model: {e}")

    # Start database health monitoring
    try:
        await db_manager.start_health_monitoring()
        logger.info("Database health monitoring started")
    except Exception as e:
        logger.error(f"Failed to start database health monitoring: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Personal Health Assistant Authentication Service...")

    # Stop database health monitoring and close connections
    try:
        await db_manager.stop_health_monitoring()
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title="Personal Health Assistant - Authentication Service",
    description="Comprehensive authentication and authorization service for the Personal Health Assistant platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # We'll configure this properly later
)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="auth-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "auth-service")
except ImportError:
    pass


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    logger.info("Readiness check started")
    try:
        # Try SQLAlchemy health check first
        logger.info("Attempting SQLAlchemy database health check...")
        health_result = await db_manager.health_check()
        logger.info(f"SQLAlchemy health check result: {health_result}")
        if health_result["status"] == "healthy":
            logger.info("Readiness check passed - service is ready")
            return {
                "status": "ready",
                "service": "auth-service",
                "database": "connected (sqlalchemy)",
                "version": "1.0.0",
            }
        else:
            logger.error(f"SQLAlchemy health check failed: {health_result}")
            raise Exception("SQLAlchemy health check failed")
    except Exception as e:
        logger.error(f"SQLAlchemy readiness check failed: {e}", exc_info=True)
        # Fallback: try direct asyncpg connection
        try:
            import asyncpg

            logger.info("Attempting direct asyncpg health check...")
            conn = await asyncpg.connect(settings.DATABASE_URL)
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            if result == 1:
                logger.info("Direct asyncpg health check succeeded.")
                return {
                    "status": "ready",
                    "service": "auth-service",
                    "database": "connected (asyncpg)",
                    "version": "1.0.0",
                }
            else:
                logger.error("Direct asyncpg health check failed: wrong result")
        except Exception as e2:
            logger.error(f"Direct asyncpg health check failed: {e2}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready (all checks failed)",
        )


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "message": "Personal Health Assistant - Authentication Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None,
        "health": "/health",
        "ready": "/ready",
    }


# Include routers
try:
    from apps.auth.api.auth import router as auth_router

    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    logger.info("Auth router included successfully")
except Exception as e:
    import traceback

    logger.error(f"Could not import auth router: {e}\n{traceback.format_exc()}")
