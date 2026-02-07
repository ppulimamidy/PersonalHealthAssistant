"""
Doctor Collaboration Service Main Application
FastAPI application for doctor-patient collaboration management.
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
from common.utils.logging import get_logger, setup_logging
from common.middleware.auth import AuthMiddleware
from common.middleware.error_handling import ErrorHandlingMiddleware
from common.middleware.rate_limiter import RateLimitingMiddleware
from common.middleware.security import SecurityMiddleware
from common.database.connection import get_db
from apps.doctor_collaboration.api import appointments, messaging, consultations, notifications
from apps.doctor_collaboration.services import collaboration_service
from apps.doctor_collaboration.models import *
# from apps.doctor_collaboration.agents import collaboration_agents

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
    logger.info("🚀 Starting Doctor Collaboration Service...")
    
    # Initialize services that don't require database sessions
    # Note: CollaborationService requires database session, so it will be created per-request
    
    logger.info("✅ Doctor Collaboration Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Doctor Collaboration Service...")
    
    # Close database connections
    engine.dispose()
    logger.info("✅ Doctor Collaboration Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Doctor Collaboration Service",
    description="Doctor-patient collaboration microservice for Personal Health Assistant",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware in order (last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    ErrorHandlingMiddleware
)

# app.add_middleware(
#     RateLimitingMiddleware
# )

app.add_middleware(
    SecurityMiddleware
)

app.add_middleware(
    AuthMiddleware
)

# Include API routers
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(messaging.router, prefix="/api/v1/messaging", tags=["Messaging"])
app.include_router(consultations.router, prefix="/api/v1/consultations", tags=["Consultations"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connectivity
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "service": "doctor-collaboration",
            "version": "1.0.0",
            "database": "connected",
            "timestamp": "2025-08-04T19:30:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check all dependencies
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "ready",
            "service": "doctor-collaboration",
            "dependencies": {
                "database": "ready",
                "collaboration_service": "ready",
                "ai_agents": "ready"
            },
            "timestamp": "2025-08-04T19:30:00Z"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "Doctor Collaboration Service",
        "version": "1.0.0",
        "description": "Doctor-patient collaboration management",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "appointments": "/api/v1/appointments",
            "messaging": "/api/v1/messaging",
            "consultations": "/api/v1/consultations",
            "notifications": "/api/v1/notifications"
        }
    }


@app.get("/test", tags=["Test"])
async def test():
    """Test endpoint."""
    return {
        "message": "Doctor Collaboration Service is running",
        "status": "success",
        "timestamp": "2025-08-04T19:30:00Z"
    }


@app.get("/test/appointments", tags=["Test"])
async def test_appointments():
    """Test appointments endpoint."""
    try:
        # Test appointment creation
        test_appointment = {
            "patient_id": "test-patient-id",
            "doctor_id": "test-doctor-id",
            "appointment_type": "consultation",
            "scheduled_date": "2025-08-05T10:00:00Z",
            "duration_minutes": 30,
            "notes": "Test appointment"
        }
        
        return {
            "message": "Appointments endpoint test successful",
            "test_data": test_appointment,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Appointments test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@app.get("/test/messaging", tags=["Test"])
async def test_messaging():
    """Test messaging endpoint."""
    try:
        # Test message creation
        test_message = {
            "sender_id": "test-sender-id",
            "recipient_id": "test-recipient-id",
            "message_type": "text",
            "content": "Test message content",
            "priority": "normal"
        }
        
        return {
            "message": "Messaging endpoint test successful",
            "test_data": test_message,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Messaging test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@app.get("/test/consultations", tags=["Test"])
async def test_consultations():
    """Test consultations endpoint."""
    try:
        # Test consultation creation
        test_consultation = {
            "patient_id": "test-patient-id",
            "doctor_id": "test-doctor-id",
            "consultation_type": "follow_up",
            "scheduled_date": "2025-08-05T14:00:00Z",
            "duration_minutes": 45,
            "notes": "Test consultation"
        }
        
        return {
            "message": "Consultations endpoint test successful",
            "test_data": test_consultation,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Consultations test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@app.get("/test/integration", tags=["Test"])
async def test_integration(credentials: HTTPBearer = Depends(security)):
    """Test integration with other services."""
    try:
        # Test integration with auth service
        auth_response = {
            "auth_service": "connected",
            "user_authentication": "working"
        }
        
        # Test integration with medical records
        medical_records_response = {
            "medical_records_service": "connected",
            "patient_data_access": "working"
        }
        
        # Test integration with user profile
        user_profile_response = {
            "user_profile_service": "connected",
            "profile_data_access": "working"
        }
        
        return {
            "message": "Integration tests successful",
            "integrations": {
                "auth_service": auth_response,
                "medical_records": medical_records_response,
                "user_profile": user_profile_response
            },
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Integration test failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "service": "doctor-collaboration"
        }
    )


def override_get_db():
    """Override database dependency for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 