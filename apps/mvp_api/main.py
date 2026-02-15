"""
MVP API Main Application
Consolidated FastAPI service for Personal Health Assistant MVP.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from common.utils.logging import get_logger
from common.middleware.error_handling import setup_error_handlers
from common.config.settings import get_settings

from .api.oura import router as oura_router
from .api.timeline import router as timeline_router
from .api.insights import router as insights_router
from .api.doctor_prep import router as doctor_prep_router
from .api.nutrition import router as nutrition_router
from .api.billing import router as billing_router
from .api.beta import router as beta_router
from .api.health_score import router as health_score_router
from .api.email_summary import router as email_summary_router

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Starting MVP API service...")
    yield
    logger.info("Shutting down MVP API service...")


app = FastAPI(
    title="Personal Health Assistant MVP API",
    description="Consolidated API endpoints for the MVP",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration – read from ALLOWED_ORIGINS env var in production
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "").strip()
if _allowed_origins_env and _allowed_origins_env != "*":
    _allowed_origins = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
elif _allowed_origins_env == "*":
    _allowed_origins = ["*"]
else:
    _allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if hasattr(settings, "frontend_url") and settings.frontend_url:
        _allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)

# Include routers
app.include_router(oura_router, prefix="/api/v1/oura", tags=["Oura Integration"])
app.include_router(timeline_router, prefix="/api/v1/health", tags=["Health Timeline"])
app.include_router(insights_router, prefix="/api/v1/insights", tags=["AI Insights"])
app.include_router(
    doctor_prep_router, prefix="/api/v1/doctor-prep", tags=["Doctor Prep"]
)
app.include_router(nutrition_router, prefix="/api/v1/nutrition", tags=["Nutrition"])
app.include_router(billing_router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(beta_router, prefix="/api/v1/beta", tags=["Beta"])
app.include_router(
    health_score_router, prefix="/api/v1/health-score", tags=["Health Score"]
)
app.include_router(email_summary_router, prefix="/api/v1/email", tags=["Email Summary"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mvp-api"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Personal Health Assistant MVP API",
        "version": "1.0.0",
        "docs": "/docs",
    }
