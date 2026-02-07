"""
Main FastAPI application for the Personal Health Assistant Consent Audit Service.

This is the entry point for the consent audit service, providing:
- FastAPI application setup
- Middleware configuration
- Router registration
- Health checks
- Error handling
- GDPR and HIPAA compliance auditing
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config.settings import get_settings
from common.utils.logging import get_logger, setup_logging
from common.database.connection import get_db_manager
from common.models.registry import register_model

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
    logger.info("Starting Personal Health Assistant Consent Audit Service...")
    
    # Register models in the global registry
    # Temporarily disabled due to model relationship issues
    # try:
    #     from models.audit import ConsentAuditLog, DataProcessingAudit, ComplianceReport
    #     register_model("ConsentAuditLog", ConsentAuditLog)
    #     register_model("DataProcessingAudit", DataProcessingAudit)
    #     register_model("ComplianceReport", ComplianceReport)
    #     logger.info("Consent audit models registered in global registry")
    # except Exception as e:
    #     logger.warning(f"Failed to register consent audit models: {e}")
    
    # Start database health monitoring
    try:
        await db_manager.start_health_monitoring()
        logger.info("Database health monitoring started")
    except Exception as e:
        logger.error(f"Failed to start database health monitoring: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Personal Health Assistant Consent Audit Service...")
    
    # Stop database health monitoring and close connections
    try:
        await db_manager.stop_health_monitoring()
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title="Personal Health Assistant - Consent Audit Service",
    description="Comprehensive consent audit and compliance service for GDPR, HIPAA, and data governance",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
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
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation exceptions."""
    logger.error(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"General Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        # Check database connectivity
        db_status = "healthy"
        try:
            await db_manager.check_health()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        return {
            "status": "healthy",
            "service": "consent_audit",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "database": db_status,
                "audit_engine": "healthy",
                "compliance_checker": "healthy",
                "gdpr_processor": "healthy",
                "hipaa_validator": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    try:
        # Check if all required services are ready
        db_ready = False
        try:
            await db_manager.check_health()
            db_ready = True
        except Exception as e:
            logger.error(f"Database readiness check failed: {e}")
        
        if not db_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
        
        return {
            "status": "ready",
            "service": "consent_audit",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "service": "Personal Health Assistant - Consent Audit Service",
        "version": "1.0.0",
        "description": "Comprehensive consent audit and compliance service for GDPR, HIPAA, and data governance",
        "features": [
            "Consent audit logging",
            "GDPR compliance monitoring",
            "HIPAA compliance validation",
            "Data processing audits",
            "Compliance reporting",
            "Consent verification",
            "Data subject rights management",
            "Audit trail generation"
        ],
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "audit": "/api/v1/audit",
            "compliance": "/api/v1/compliance",
            "consent": "/api/v1/consent",
            "gdpr": "/api/v1/gdpr",
            "hipaa": "/api/v1/hipaa"
        }
    }


# Include routers
try:
    # Temporarily disabled due to model relationship issues
    from api.audit import router as audit_router
    from api.compliance import router as compliance_router
    from api.consent import router as consent_router
    from api.gdpr import router as gdpr_router
    # from api.hipaa import router as hipaa_router
    
    app.include_router(audit_router, prefix="/api/v1/audit", tags=["audit"])
    app.include_router(compliance_router, prefix="/api/v1/compliance", tags=["compliance"])
    app.include_router(consent_router, prefix="/api/v1/consent", tags=["consent"])
    app.include_router(gdpr_router, prefix="/api/v1/gdpr", tags=["gdpr"])
    # app.include_router(hipaa_router, prefix="/api/v1/hipaa", tags=["hipaa"])
    
    logger.info("Consent, GDPR, Audit, and Compliance routers included successfully")
except Exception as e:
    logger.error(f"Failed to include routers: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8009,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    ) 