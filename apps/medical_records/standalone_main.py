"""
Medical Records Service Main Application - Standalone Version
FastAPI application for medical records management.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

# Add common directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
common_path = os.path.join(project_root, "common")
sys.path.insert(0, common_path)

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import get_settings
from utils.logging import get_logger
from middleware.auth import AuthMiddleware
from middleware.error_handling import ErrorHandlingMiddleware
from middleware.rate_limiter import RateLimitingMiddleware
from middleware.security import SecurityMiddleware
from database.connection import get_db

# Get settings and logger
settings = get_settings()
logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()

# Database setup
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Medical Records Service...")
    
    # Startup
    logger.info("✅ Medical Records Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Medical Records Service...")
    await engine.dispose()
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

# Add middleware in order (last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Security middleware (if enabled)
if settings.security.enable_security_headers:
    app.add_middleware(SecurityMiddleware)

# Error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Rate limiting middleware (if enabled)
if settings.security.enable_rate_limiting:
    app.add_middleware(RateLimitingMiddleware)

# Auth middleware
app.add_middleware(AuthMiddleware)

# Trusted host middleware (if in production)
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


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


# Simple lab results endpoint for testing
@app.get("/api/v1/medical-records/lab-results", tags=["Lab Results"])
async def list_lab_results():
    """List lab results endpoint."""
    return {
        "message": "Lab results endpoint working!",
        "service": "medical_records"
    }


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
async def override_get_db():
    """Override database dependency for testing."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "standalone_main:app",
        host="0.0.0.0",
        port=8005,  # Medical records service port
        reload=settings.DEBUG,
        log_level="info"
    ) 