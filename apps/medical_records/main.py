"""
Medical Records Service Main Application
FastAPI application for medical records management.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(
    engine, class_=Session, expire_on_commit=False
)


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
    lifespan=lifespan
)

open_test_router = APIRouter(prefix="/open-test", tags=["OpenTest"])

@open_test_router.get("/hello")
async def open_hello():
    logger.warning("[DEBUG] Entered /open-test/hello endpoint (no auth)")
    return {"status": "open", "message": "Hello from open-test!"}

app.include_router(open_test_router)

# Add middleware in order (last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (if enabled)
# if settings.security.enable_security_headers:
#     app.middleware('http')(SecurityMiddleware())

# Error handling middleware
# app.add_middleware(ErrorHandlingMiddleware)

# Rate limiting middleware (if enabled)
# if settings.security.enable_rate_limiting:
#     app.add_middleware(RateLimitingMiddleware)

# Auth middleware
# app.add_middleware(AuthMiddleware)

# Trusted host middleware (if in production)
# if not settings.DEBUG:
#     app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "medical_records",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Records Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None
    }


# Test endpoint
@app.get("/test", tags=["Test"])
async def test():
    """Test endpoint."""
    return {"message": "Medical Records Service is working!"}


# Test lab results endpoint (no auth required)
@app.get("/test/lab-results", tags=["Test"])
async def test_lab_results():
    """Test lab results endpoint without authentication."""
    return {
        "message": "Lab results endpoint is accessible",
        "endpoints": [
            "GET /api/v1/medical-records/lab-results/",
            "POST /api/v1/medical-records/lab-results/",
            "GET /api/v1/medical-records/lab-results/{lab_result_id}",
            "PUT /api/v1/medical-records/lab-results/{lab_result_id}",
            "DELETE /api/v1/medical-records/lab-results/{lab_result_id}",
            "POST /api/v1/medical-records/lab-results/upload"
        ]
    }


# Test documents endpoint (no auth required)
@app.get("/test/documents", tags=["Test"])
async def test_documents():
    """Test documents endpoint without authentication."""
    return {
        "message": "Documents endpoint is accessible",
        "endpoints": [
            "GET /api/v1/medical-records/documents/",
            "POST /api/v1/medical-records/documents/",
            "POST /api/v1/medical-records/documents/upload",
            "GET /api/v1/medical-records/documents/{document_id}",
            "PUT /api/v1/medical-records/documents/{document_id}",
            "DELETE /api/v1/medical-records/documents/{document_id}",
            "GET /api/v1/medical-records/documents/{document_id}/status"
        ]
    }


# Test imaging endpoint (no auth required)
@app.get("/test/imaging", tags=["Test"])
async def test_imaging():
    """Test imaging endpoint without authentication."""
    return {
        "message": "Imaging endpoint is accessible",
        "endpoints": [
            "GET /api/v1/medical-records/imaging/studies",
            "POST /api/v1/medical-records/imaging/studies",
            "GET /api/v1/medical-records/imaging/studies/{study_id}",
            "PUT /api/v1/medical-records/imaging/studies/{study_id}",
            "DELETE /api/v1/medical-records/imaging/studies/{study_id}",
            "POST /api/v1/medical-records/imaging/studies/{study_id}/images",
            "POST /api/v1/medical-records/imaging/studies/{study_id}/dicom",
            "GET /api/v1/medical-records/imaging/studies/{study_id}/images",
            "GET /api/v1/medical-records/imaging/images/{image_id}",
            "DELETE /api/v1/medical-records/imaging/images/{image_id}",
            "GET /api/v1/medical-records/imaging/modalities",
            "GET /api/v1/medical-records/imaging/body-parts",
            "GET /api/v1/medical-records/imaging/image-formats",
            "GET /api/v1/medical-records/imaging/study-statuses"
        ]
    }


# Test clinical reports endpoint (no auth required)
@app.get("/test/clinical-reports", tags=["Test"])
async def test_clinical_reports():
    """Test clinical reports endpoint without authentication."""
    return {
        "message": "Clinical reports endpoint is accessible",
        "endpoints": [
            "GET /api/v1/medical-records/clinical-reports/",
            "POST /api/v1/medical-records/clinical-reports/",
            "GET /api/v1/medical-records/clinical-reports/{clinical_report_id}",
            "PUT /api/v1/medical-records/clinical-reports/{clinical_report_id}",
            "DELETE /api/v1/medical-records/clinical-reports/{clinical_report_id}",
            "POST /api/v1/medical-records/clinical-reports/upload"
        ]
    }


# Test agents endpoint (no auth required)
@app.get("/test/agents", tags=["Test"])
async def test_agents():
    """Test agents endpoint without authentication."""
    return {
        "message": "Agents endpoint is accessible",
        "endpoints": [
            "GET /api/v1/medical-records/agents/status",
            "GET /api/v1/medical-records/agents/status/{agent_name}",
            "GET /api/v1/medical-records/agents/health",
            "POST /api/v1/medical-records/agents/process-document/{document_id}",
            "POST /api/v1/medical-records/agents/process-document-with-content",
            "POST /api/v1/medical-records/agents/execute/{agent_name}",
            "POST /api/v1/medical-records/agents/document-reference-agent",
            "POST /api/v1/medical-records/agents/clinical-nlp-agent"
        ]
    }


# Service integration test endpoint
@app.get("/test/integration", tags=["Test"])
async def test_integration(credentials: HTTPBearer = Depends(security)):
    """Test service integration."""
    try:
        # Validate user access
        user_info = await service_integration.validate_user_access(credentials.credentials)
        
        return {
            "message": "Service integration working!",
            "user_info": {
                "user_id": user_info["user_id"],
                "has_data_access": user_info["has_data_access"]
            }
        }
    except Exception as e:
        logger.error(f"Service integration test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Service integration test failed: {str(e)}"
        )


# Test open endpoint (no auth required)
@app.get("/test-open", tags=["Test"])
async def test_open():
    logger.warning("[DEBUG] Entered /test-open endpoint (no auth)")
    return {"status": "open", "message": "This endpoint is open to all."}


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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


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
        log_level="info"
    ) 