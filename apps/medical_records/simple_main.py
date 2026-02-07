"""
Medical Records Service - Simple Version
FastAPI application for medical records management without complex middleware.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:your-super-secret-and-long-postgres-password@localhost:5432/health_assistant"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🚀 Starting Medical Records Service...")
    
    # Startup
    print("✅ Medical Records Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Medical Records Service...")
    await engine.dispose()
    print("✅ Medical Records Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Medical Records Service",
    description="Medical records management microservice for VitaSense PPA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "docs": "/docs"
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
        "service": "medical_records",
        "items": []
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8005,  # Medical records service port
        reload=True,
        log_level="info"
    ) 