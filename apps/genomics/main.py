"""
Main FastAPI application for the Personal Health Assistant Genomics Service.

This is the entry point for the genomics service, providing:
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
    logger.info("🚀 Starting Personal Health Assistant Genomics Service...")
    
    # Register models in the global registry
    try:
        from .models.genomic_data import GenomicData, GeneticVariant, PharmacogenomicProfile
        from .models.analysis import GenomicAnalysis, DiseaseRiskAssessment, AncestryAnalysis
        register_model("GenomicData", GenomicData)
        register_model("GeneticVariant", GeneticVariant)
        register_model("PharmacogenomicProfile", PharmacogenomicProfile)
        register_model("GenomicAnalysis", GenomicAnalysis)
        register_model("DiseaseRiskAssessment", DiseaseRiskAssessment)
        register_model("AncestryAnalysis", AncestryAnalysis)
        logger.info("Genomics models registered in global registry")
    except Exception as e:
        logger.warning(f"Failed to register genomics models: {e}")
    
    # Start database health monitoring
    try:
        await db_manager.start_health_monitoring()
        logger.info("Database health monitoring started")
    except Exception as e:
        logger.error(f"Failed to start database health monitoring: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Personal Health Assistant Genomics Service...")
    
    # Stop database health monitoring and close connections
    try:
        await db_manager.stop_health_monitoring()
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title="Personal Health Assistant - Genomics Service",
    description="Comprehensive genomic analysis and genetic counseling service for the Personal Health Assistant platform",
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

# Add error handling middleware
from common.middleware.error_handling import ErrorHandlingMiddleware
app.add_middleware(ErrorHandlingMiddleware)

# Add security middleware
from common.middleware.security import SecurityMiddleware
app.add_middleware(SecurityMiddleware)

# Add authentication middleware
from common.middleware.auth import AuthMiddleware
app.add_middleware(AuthMiddleware)

# Include API routers
from .api import genomic_data, analysis, variants, pharmacogenomics, ancestry, counseling

app.include_router(genomic_data.router, prefix="/api/v1/genomic-data", tags=["Genomic Data"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Genomic Analysis"])
app.include_router(variants.router, prefix="/api/v1/variants", tags=["Genetic Variants"])
app.include_router(pharmacogenomics.router, prefix="/api/v1/pharmacogenomics", tags=["Pharmacogenomics"])
app.include_router(ancestry.router, prefix="/api/v1/ancestry", tags=["Ancestry Analysis"])
app.include_router(counseling.router, prefix="/api/v1/counseling", tags=["Genetic Counseling"])

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        # Check database connectivity using async health check
        health_result = await db_manager.health_check()
        
        if health_result["status"] == "healthy":
            return {
                "status": "healthy",
                "service": "genomics-service",
                "version": "1.0.0",
                "database": "connected",
                "timestamp": "2025-08-05T18:30:00Z"
            }
        else:
            logger.error(f"Database health check failed: {health_result}")
            raise HTTPException(status_code=503, detail="Service unhealthy")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    try:
        # Check database connectivity using async health check
        health_result = await db_manager.health_check()
        
        if health_result["status"] == "healthy":
            return {
                "status": "ready",
                "service": "genomics-service",
                "dependencies": {
                    "database": "ready",
                    "genomic_analysis": "ready",
                    "variant_detection": "ready",
                    "pharmacogenomics": "ready",
                    "ancestry_analysis": "ready",
                    "genetic_counseling": "ready"
                },
                "timestamp": "2025-08-05T18:30:00Z"
            }
        else:
            logger.error(f"Database readiness check failed: {health_result}")
            raise HTTPException(status_code=503, detail="Service not ready")
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "service": "Genomics Service",
        "version": "1.0.0",
        "description": "Comprehensive genomic analysis and genetic counseling",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "genomic_data": "/api/v1/genomic-data",
            "analysis": "/api/v1/analysis",
            "variants": "/api/v1/variants",
            "pharmacogenomics": "/api/v1/pharmacogenomics",
            "ancestry": "/api/v1/ancestry",
            "counseling": "/api/v1/counseling"
        }
    }


@app.get("/test", tags=["Test"])
async def test() -> Dict[str, Any]:
    """Test endpoint."""
    return {
        "message": "Genomics Service is running",
        "status": "success",
        "timestamp": "2025-08-05T18:30:00Z"
    }


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation exceptions."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"General exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012) 