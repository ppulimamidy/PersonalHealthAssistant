"""
Medical Analysis Service
Main application for comprehensive medical analysis.
"""

import os
import sys
from contextlib import asynccontextmanager

# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from common.config.settings import MedicalAnalysisSettings
from common.utils.logging import get_logger
from common.middleware.error_handling import setup_error_handlers
from common.middleware.auth import AuthMiddleware
from common.middleware.prometheus_metrics import setup_prometheus_metrics
from apps.medical_analysis.api.medical_analysis import medical_analysis_router

# Get settings
settings = MedicalAnalysisSettings()
logger = get_logger(__name__)

# Log debug information
logger.debug(f"SERVICE_PORT: {settings.SERVICE_PORT}")
logger.debug(f"HOST: {settings.HOST}")
logger.debug(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🏥 Starting Medical Analysis Service...")

    # Initialize services
    try:
        # Initialize medical analysis service
        from apps.medical_analysis.services.medical_analysis_service import (
            MedicalAnalysisService,
        )

        app.state.medical_analysis_service = MedicalAnalysisService()
        logger.info("✅ Medical Analysis Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Medical Analysis Service: {e}")

    logger.info("✅ Medical Analysis Service started successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Medical Analysis Service...")

    # Cleanup services
    try:
        if hasattr(app.state, "medical_analysis_service"):
            del app.state.medical_analysis_service
    except Exception as e:
        logger.error(f"❌ Error cleaning up services: {e}")


# Create FastAPI application
app = FastAPI(
    title="Medical Analysis Service",
    description="Comprehensive medical analysis including diagnosis, prognosis, and literature insights",
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

# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=settings.ALLOWED_HOSTS
# )

# Setup error handlers
setup_error_handlers(app)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="medical-analysis-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "medical-analysis-service")
except ImportError:
    pass

# Include routers
app.include_router(medical_analysis_router, prefix="/api/v1")


@app.middleware("http")
async def log_request_headers(request, call_next):
    logger.debug(f"Incoming request: {request.method} {request.url}")
    for k, v in request.headers.items():
        logger.debug(f"Header: {k}: {v}")
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Medical Analysis Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Comprehensive medical analysis including diagnosis, prognosis, and literature insights",
        "features": [
            "Medical diagnosis based on symptoms and data",
            "Disease prognosis and outcome prediction",
            "Medical literature and research insights",
            "Comprehensive medical reports",
            "Multi-domain medical analysis",
            "AI-powered medical insights",
            "Evidence-based recommendations",
        ],
    }


@app.get("/health")
async def health_check(request):
    # Log the Host header for debugging
    host_header = request.headers.get("host")
    logger.debug(f"/health Host header: {host_header}")
    return {
        "service": "medical_analysis",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/v1/medical-analysis/analyze",
            "diagnosis": "/api/v1/medical-analysis/diagnosis",
            "prognosis": "/api/v1/medical-analysis/prognosis",
            "literature": "/api/v1/medical-analysis/literature",
            "comprehensive": "/api/v1/medical-analysis/comprehensive",
            "report": "/api/v1/medical-analysis/report",
        },
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"service": "medical_analysis", "status": "ready", "version": "1.0.0"}


@app.get("/capabilities")
async def get_capabilities():
    """Get service capabilities."""
    return {
        "service": "medical_analysis",
        "capabilities": {
            "analysis_types": {
                "diagnosis": {
                    "description": "Medical diagnosis based on symptoms and data",
                    "features": [
                        "condition_identification",
                        "differential_diagnoses",
                        "confidence_scoring",
                    ],
                    "supported_domains": [
                        "cardiology",
                        "dermatology",
                        "neurology",
                        "general",
                    ],
                },
                "prognosis": {
                    "description": "Disease progression and outcome prediction",
                    "features": [
                        "outcome_prediction",
                        "risk_assessment",
                        "progression_staging",
                    ],
                    "supported_domains": [
                        "cardiology",
                        "dermatology",
                        "neurology",
                        "general",
                    ],
                },
                "literature": {
                    "description": "Medical literature and research insights",
                    "features": [
                        "research_findings",
                        "clinical_guidelines",
                        "treatment_evidence",
                    ],
                    "supported_domains": [
                        "cardiology",
                        "dermatology",
                        "neurology",
                        "general",
                    ],
                },
                "comprehensive": {
                    "description": "Complete analysis combining all types",
                    "features": [
                        "diagnosis",
                        "prognosis",
                        "literature",
                        "treatment_recommendations",
                    ],
                    "supported_domains": [
                        "cardiology",
                        "dermatology",
                        "neurology",
                        "general",
                    ],
                },
            },
            "data_requirements": {
                "minimum": ["patient_id", "symptoms"],
                "recommended": ["medical_history", "vital_signs", "lab_results"],
                "optional": ["imaging_results", "family_history", "lifestyle_factors"],
            },
            "ai_models": {
                "primary": ["gpt-4", "llama-3.1-8b-instant"],
                "fallback": ["pattern_based_analysis"],
                "knowledge_base": ["medical_literature", "clinical_guidelines"],
            },
            "output_formats": {
                "analysis_result": "Structured analysis with confidence scores",
                "comprehensive_report": "Complete medical report with recommendations",
                "structured_data": "JSON format with all analysis components",
            },
            "safety_features": {
                "disclaimers": "Automatic medical disclaimers",
                "confidence_scoring": "Transparent confidence levels",
                "professional_consultation": "Always recommend professional consultation",
                "emergency_detection": "Automatic emergency situation detection",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
