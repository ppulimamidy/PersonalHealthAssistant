"""
Medical Records Service Main Application
FastAPI application for medical records management.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

# Add project root to path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.config.settings import get_settings
from common.utils.logging import get_logger
from common.middleware.auth import AuthMiddleware
from common.middleware.error_handling import ErrorHandlingMiddleware
from common.middleware.rate_limiter import RateLimitingMiddleware
from common.middleware.security import SecurityMiddleware
from common.database.connection import get_db
from common.middleware.prometheus_metrics import setup_prometheus_metrics
from apps.medical_records.api import lab_results, documents, imaging
from apps.medical_records.services import service_integration
from apps.medical_records.api import clinical_reports, agents, epic_fhir
from apps.medical_records.models import *
from apps.medical_records.agents import advanced_ai_models

# Get settings and logger
settings = get_settings()
logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()

# Database setup
engine = create_engine(
    settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True, pool_recycle=300
)

SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Medical Records Service...")
    app.state.ai_model_manager = advanced_ai_models.AIModelManager()
    logger.info("✅ Medical Records Service started successfully")
    yield
    # After yield, schedule model loading in the background
    import asyncio

    asyncio.create_task(app.state.ai_model_manager.load_models())
    logger.info("🚀 Model loading scheduled in background")
    # Shutdown
    logger.info("🛑 Shutting down Medical Records Service...")
    engine.dispose()
    logger.info("✅ Medical Records Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Medical Records Service",
    description="Medical records management microservice for VitaSense PPA",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="medical-records-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "medical-records-service")
except ImportError:
    pass

# Add middleware in order (last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Security middleware
try:
    app.add_middleware(SecurityMiddleware)
except Exception as e:
    logger.warning(f"Security middleware setup failed (non-critical): {e}")

# Rate limiting middleware
try:
    app.add_middleware(RateLimitingMiddleware)
except Exception as e:
    logger.warning(f"Rate limiting middleware setup failed (non-critical): {e}")

# Auth middleware
app.add_middleware(AuthMiddleware)

# Trusted host middleware
if hasattr(settings, "ALLOWED_HOSTS") and settings.ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "medical_records",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Records Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None,
    }


# Include API routers
app.include_router(lab_results.router, prefix="/api/v1/medical-records")
app.include_router(documents.router, prefix="/api/v1/medical-records")
app.include_router(imaging.router, prefix="/api/v1/medical-records")
app.include_router(clinical_reports.router, prefix="/api/v1/medical-records")
app.include_router(agents.router, prefix="/api/v1/medical-records")
app.include_router(epic_fhir.router, prefix="/api/v1/medical-records")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Database dependency override for testing
def override_get_db():
    """Override database dependency for testing."""
    with SessionLocal() as session:
        try:
            yield session
        finally:
            session.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,  # Medical records service port
        reload=settings.DEBUG,
        log_level="info",
    )
