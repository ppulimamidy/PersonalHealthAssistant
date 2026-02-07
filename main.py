"""
Main FastAPI application for the Personal Health Assistant Authentication Service.

This is the entry point for the authentication service, providing:
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.config.settings import get_settings
from common.utils.logging import get_logger, setup_logging
from common.database.connection import get_db_manager

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
    logger.info("Starting Personal Health Assistant Authentication Service...")
    
    # Start database health monitoring
    try:
        await db_manager.start_health_monitoring()
        logger.info("Database health monitoring started")
    except Exception as e:
        logger.error(f"Failed to start database health monitoring: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Personal Health Assistant Authentication Service...")
    
    # Stop database health monitoring and close connections
    try:
        await db_manager.stop_health_monitoring()
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title="Personal Health Assistant - Authentication Service",
    description="Comprehensive authentication and authorization service for the Personal Health Assistant platform",
    version="1.0.0",
    docs_url="/docs" if settings.development.environment != "production" else None,
    redoc_url="/redoc" if settings.development.environment != "production" else None,
    openapi_url="/openapi.json" if settings.development.environment != "production" else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=settings.security.cors_allow_methods,
    allow_headers=settings.security.cors_allow_headers,
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # We'll configure this properly later
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
        "environment": settings.development.environment
    }


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    logger.info("Readiness check started")
    try:
        # Try SQLAlchemy health check first
        logger.info("Attempting SQLAlchemy database health check...")
        health_result = await db_manager.health_check()
        logger.info(f"SQLAlchemy health check result: {health_result}")
        if health_result["status"] == "healthy":
            logger.info("Readiness check passed - service is ready")
            return {
                "status": "ready",
                "service": "auth-service",
                "database": "connected (sqlalchemy)",
                "version": "1.0.0"
            }
        else:
            logger.error(f"SQLAlchemy health check failed: {health_result}")
            raise Exception("SQLAlchemy health check failed")
    except Exception as e:
        logger.error(f"SQLAlchemy readiness check failed: {e}", exc_info=True)
        # Fallback: try direct asyncpg connection
        try:
            import asyncpg
            logger.info("Attempting direct asyncpg health check...")
            conn = await asyncpg.connect('postgresql://postgres:your-super-secret-and-long-postgres-password@postgres-db:5432/health_assistant')
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            if result == 1:
                logger.info("Direct asyncpg health check succeeded.")
                return {
                    "status": "ready",
                    "service": "auth-service",
                    "database": "connected (asyncpg)",
                    "version": "1.0.0"
                }
            else:
                logger.error("Direct asyncpg health check failed: wrong result")
        except Exception as e2:
            logger.error(f"Direct asyncpg health check failed: {e2}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready (all checks failed)"
        )


# Include routers
try:
    from apps.auth.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    logger.info("Auth router included successfully")
except Exception as e:
    import traceback
    logger.error(f"Could not import auth router: {e}\n{traceback.format_exc()}")

# --- Add Medical Records Agents Router ---
try:
    from apps.medical_records.api.agents import router as agents_router
    app.include_router(agents_router, prefix="/agents", tags=["Medical Records Agents"])
    logger.info("Medical Records Agents router included successfully")
except Exception as e:
    import traceback
    logger.error(f"Could not import medical records agents router: {e}\n{traceback.format_exc()}")

# Try to include additional routers if they exist
additional_routers = [
    ("users", "apps.auth.api.users"),
    ("sessions", "apps.auth.api.sessions"),
    ("mfa", "apps.auth.api.mfa"),
    ("roles", "apps.auth.api.roles"),
    ("audit", "apps.auth.api.audit"),
    ("consent", "apps.auth.api.consent")
]

for router_name, module_path in additional_routers:
    try:
        module = __import__(module_path, fromlist=["router"])
        router = getattr(module, "router")
        app.include_router(router, prefix=f"/auth/{router_name}", tags=[router_name.title()])
        logger.info(f"{router_name.title()} router included successfully")
    except ImportError:
        logger.info(f"{router_name.title()} router not available - skipping")
    except Exception as e:
        logger.warning(f"Error including {router_name} router: {e}")


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "Personal Health Assistant Authentication Service",
        "version": "1.0.0",
        "docs": "/docs" if settings.development.environment != "production" else None,
        "health": "/health",
        "ready": "/ready"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.development.host,
        port=settings.development.port,
        reload=settings.development.environment == "development",
        log_level=settings.monitoring.log_level.lower(),
        access_log=True
    ) 