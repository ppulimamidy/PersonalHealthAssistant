"""
Analytics Service

Main FastAPI application for the Analytics Service.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from common.utils.logging import get_logger, setup_logging
from common.database.connection import get_db_manager
from api.analytics import router as analytics_router


# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get database manager
db_manager = get_db_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Personal Health Assistant Analytics Service...")
    
    # Start database health monitoring
    try:
        await db_manager.start_health_monitoring()
        logger.info("Database health monitoring started")
    except Exception as e:
        logger.error(f"Failed to start database health monitoring: {e}")
        raise
    
    # Initialize analytics service
    try:
        from services.analytics_service import AnalyticsService
        from api.analytics import set_analytics_service
        global analytics_service
        analytics_service = AnalyticsService()
        await analytics_service.start()
        set_analytics_service(analytics_service)
        logger.info("Analytics service initialized with real-time processing")
    except Exception as e:
        logger.error(f"Failed to initialize analytics service: {e}")
        raise
    
    logger.info("Analytics Service startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Personal Health Assistant Analytics Service...")
    
    # Stop analytics service
    try:
        if analytics_service:
            await analytics_service.stop()
            logger.info("Analytics service stopped")
    except Exception as e:
        logger.error(f"Error stopping analytics service: {e}")
    
    # Stop database health monitoring and close connections
    try:
        await db_manager.stop_health_monitoring()
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title="Personal Health Assistant Analytics Service",
    description="Comprehensive analytics service for health data processing and insights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)



# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check_endpoint():
    """Health check endpoint."""
    try:
        # Check database health
        health_status = await db_manager.health_check()
        
        return {
            "status": "healthy",
            "service": "analytics-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check database readiness
        health_status = await db_manager.health_check()
        
        return {
            "status": "ready",
            "service": "analytics-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Personal Health Assistant Analytics Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs"
        }
    }


# Initialize analytics service
analytics_service = None

# Include routers
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])

# Test endpoint
@app.get("/test")
async def test():
    """Test endpoint."""
    return {
        "message": "Analytics service is working!",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8210,
        reload=False,
        log_level="info"
    ) 