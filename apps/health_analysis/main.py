"""
Health Analysis Service Main Application

FastAPI application for medical image analysis and health insights.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import common modules
from common.config.settings import get_settings
from common.database.connection import get_async_db
from sqlalchemy import text
from common.middleware.auth import auth_middleware
from common.middleware.error_handling import setup_error_handlers
from common.utils.logging import setup_logging
from common.utils.opentelemetry_config import configure_opentelemetry

# Import service modules
from apps.health_analysis.api import health_analysis, medical_insights, emergency_triage
from apps.health_analysis.services.health_analysis_service import HealthAnalysisService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Global service instance
health_analysis_service: HealthAnalysisService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global health_analysis_service
    
    # Startup
    logger.info("Starting Health Analysis Service...")
    
    try:
        # Setup OpenTelemetry
        if settings.TRACING_ENABLED:
            configure_opentelemetry(app, "health-analysis-service")
            logger.info("OpenTelemetry configured")
        
        # Initialize database connection
        async for session in get_async_db():
            await session.execute(text("SELECT 1"))
            logger.info("Database connection established")
            break
        
        # Initialize health analysis service
        health_analysis_service = HealthAnalysisService()
        
        # Initialize service without AI models - they will be loaded on-demand
        try:
            logger.info("Health Analysis Service initialized without AI models (lazy loading enabled)")
            logger.info("AI models will be loaded when first needed")
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
        
        logger.info("Health Analysis Service ready for operations")
        
        # Set global service instance in API modules
        health_analysis.health_analysis_service = health_analysis_service
        medical_insights.health_analysis_service = health_analysis_service
        emergency_triage.health_analysis_service = health_analysis_service
        logger.info("Global service instances set in API modules")
        
        logger.info("Health Analysis Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Health Analysis Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Health Analysis Service...")
    
    if health_analysis_service:
        await health_analysis_service.cleanup()
        logger.info("Health Analysis Service cleaned up")


# Create FastAPI app
app = FastAPI(
    title="Health Analysis Service",
    description="Comprehensive medical AI service for health image analysis and insights",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add auth middleware
app.middleware("http")(auth_middleware)

# Add error handling
setup_error_handlers(app)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(
    health_analysis.router,
    prefix="/api/v1/health-analysis",
    tags=["Health Analysis"]
)

app.include_router(
    medical_insights.router,
    prefix="/api/v1/medical-insights",
    tags=["Medical Insights"]
)

app.include_router(
    emergency_triage.router,
    prefix="/api/v1/emergency-triage",
    tags=["Emergency Triage"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        async for session in get_async_db():
            await session.execute(text("SELECT 1"))
            break
        
        # Check service health
        service_health = await health_analysis_service.get_health_status() if health_analysis_service else {"status": "initializing"}
        
        return {
            "service": "health-analysis",
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "services": {
                "database": "healthy",
                "health_analysis": service_health.get("status", "unknown"),
                "ai_models": service_health.get("ai_models", {}),
                "emergency_triage": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check if service is initialized (even if models are still loading)
        if not health_analysis_service:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        # Check AI models availability (but don't fail if some are still loading)
        try:
            models_status = await health_analysis_service.get_models_status()
        except Exception as e:
            logger.warning(f"Models status check failed: {e}")
            models_status = {"status": "initializing"}
        
        # Service is ready if it's initialized, even if models are still loading
        return {
            "status": "ready",
            "models": models_status,
            "note": "Service is ready for basic operations. AI models may still be loading."
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "details": {"request_id": "unknown"}
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    ) 