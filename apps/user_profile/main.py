"""
User Profile Service Main Application

This module provides the main FastAPI application for the User Profile Service.
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
import time
import structlog
import prometheus_client

# Add parent directories to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from common.config.settings import get_settings
from common.middleware.error_handling import setup_error_handlers
from common.middleware.security import setup_security
from common.utils.logging import setup_logging
from common.utils.opentelemetry_config import configure_opentelemetry
from common.middleware.rate_limiter import setup_rate_limiting
from common.models.registry import register_model

# Import API routers
from apps.user_profile.api import router as profile_router

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)

# Prometheus metrics
if not hasattr(prometheus_client.REGISTRY, '_user_profile_metrics_registered'):
    REQUEST_COUNT = Counter('user_profile_request_count', 'Total request count', ['app_name', 'endpoint'])
    REQUEST_LATENCY = Histogram('user_profile_request_latency_seconds', 'Request latency', ['app_name', 'endpoint'])
    prometheus_client.REGISTRY._user_profile_metrics_registered = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global logger
    logger = structlog.get_logger(__name__)
    logger.info("Starting User Profile Service...")
    
    # Register models in the global registry
    try:
        from .models.health_attributes import HealthAttributes
        register_model("HealthAttributes", HealthAttributes)
        logger.info("HealthAttributes model registered in global registry")
    except Exception as e:
        logger.warning(f"Failed to register HealthAttributes model: {e}")
    
    # Initialize services
    settings = get_settings()
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Setup OpenTelemetry if enabled
    if hasattr(settings, "TRACING_ENABLED") and settings.TRACING_ENABLED:
        configure_opentelemetry(app, "user-profile-service")
        logger.info("OpenTelemetry configured")
    
    # Setup rate limiting
    # Temporarily disabled to fix startup issue
    # if settings.security.enable_rate_limiting:
    #     setup_rate_limiting(app)
    #     logger.info("Rate limiting configured")
    
    logger.info("User Profile Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down User Profile Service...")


# Create FastAPI application
app = FastAPI(
    title="User Profile Service",
    description="Comprehensive user profile management service for the Personal Health Assistant",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Setup OpenTelemetry if enabled
if hasattr(settings, "TRACING_ENABLED") and settings.TRACING_ENABLED:
    configure_opentelemetry(app, "user-profile-service")
    logger.info("OpenTelemetry configured")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add trusted host middleware
if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Add auth middleware first (will be executed last)
from common.middleware.auth import auth_middleware
app.middleware("http")(auth_middleware)

# Add security middleware (will be executed before auth)
# Temporarily disabled to debug auth issue
# setup_security(app)

# Add error handling
setup_error_handlers(app)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware for collecting metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    REQUEST_LATENCY.labels(
        app_name="user-profile-service",
        endpoint=request.url.path
    ).observe(process_time)
    
    REQUEST_COUNT.labels(
        app_name="user-profile-service",
        endpoint=request.url.path
    ).inc()
    
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware for request logging."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response


# Include routers
app.include_router(profile_router, prefix="/api/v1/user-profile")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "message": "Personal Health Assistant - User Profile Service",
        "version": "1.0.0",
        "docs": "/docs" if os.getenv("ENABLE_DOCS", "true").lower() == "true" else None,
        "health": "/health",
        "ready": "/ready"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "user-profile-service",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }


# Readiness check endpoint
@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Add any readiness checks here (database connection, etc.)
        return {
            "status": "ready",
            "service": "user-profile-service",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "service": "user-profile-service",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": request.url.path
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "path": request.url.path
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port from auth service
        reload=settings.development.environment == "development",
        log_level="info"
    ) 