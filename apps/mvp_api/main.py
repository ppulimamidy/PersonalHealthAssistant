"""
MVP API Main Application
Consolidated FastAPI service for Personal Health Assistant MVP.
"""
# pylint: disable=wrong-import-position,wrong-import-order,redefined-outer-name,unused-argument

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env files before any module-level os.environ reads
_base = Path(__file__).parent
load_dotenv(dotenv_path=_base / ".env", override=False)
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env", override=False)

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
from .api.referral import router as referral_router
from .api.correlations import router as correlations_router
from .api.recommendations import router as recommendations_router
from .api.health_conditions import router as health_conditions_router
from .api.health_questionnaire import router as health_questionnaire_router
from .api.medications_supplements import router as medications_supplements_router
from .api.symptom_journal import router as symptom_journal_router
from .api.medical_literature import router as medical_literature_router
from .api.ai_agents import router as ai_agents_router
from .api.predictive_health import router as predictive_health_router
from .api.lab_results import router as lab_results_router
from .api.health_twin import router as health_twin_router
from .api.medication_intelligence import router as medication_intelligence_router
from .api.symptom_correlations import router as symptom_correlations_router
from .api.specialist_agents import router as specialist_agents_router
from .api.profile import router as profile_router
from .api.export import router as export_router
from .api.user_goals import router as goals_router
from .api.weekly_checkins import router as weekly_checkins_router
from .api.care_plans import router as care_plans_router
from .api.sharing import router as sharing_router
from .api.caregiver import router as caregiver_router
from .api.notifications import router as notifications_router
from .api.interventions import router as interventions_router
from .api.efficacy import router as efficacy_router
from .api.nudges import router as nudges_router
from .api.journeys import router as journeys_router
from .api.cycle_tracking import router as cycle_tracking_router
from .api.onboarding import router as onboarding_router
from .api.batch import router as batch_router
from .api.medical_records_api import router as medical_records_router
from .api.profile_intelligence import router as profile_intelligence_router
from .api.clinical_research import router as clinical_research_router
from .api.insights_intelligence import router as insights_intelligence_router
from .api.symptom_intelligence import router as symptom_intelligence_router
from .api.daily_brief import router as daily_brief_router
from .api.med_intelligence_api import router as med_intelligence_router
from .api.lab_intelligence import router as lab_intelligence_router
from .api.nutrition_assistant import router as nutrition_assistant_router
from .api.timeline_actions import router as timeline_actions_router
from .api.weekly_review import router as weekly_review_router
from .api.auth_refresh import router as auth_refresh_router
from .api.health_data import router as health_data_router

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
app.include_router(referral_router, prefix="/api/v1/referral", tags=["Referral"])
app.include_router(
    correlations_router,
    prefix="/api/v1/correlations",
    tags=["Metabolic Intelligence"],
)
app.include_router(
    recommendations_router,
    prefix="/api/v1/recommendations",
    tags=["Metabolic Intelligence"],
)
app.include_router(
    health_conditions_router,
    prefix="/api/v1/health-conditions",
    tags=["Health Conditions"],
)
app.include_router(
    health_questionnaire_router,
    prefix="/api/v1/health-questionnaire",
    tags=["Health Questionnaire"],
)
app.include_router(
    medications_supplements_router,
    prefix="/api/v1",
    tags=["Medications & Supplements"],
)
app.include_router(
    symptom_journal_router,
    prefix="/api/v1/symptoms",
    tags=["Symptom Journal"],
)
app.include_router(
    medical_literature_router,
    prefix="/api/v1/research",
    tags=["Medical Literature"],
)
app.include_router(
    ai_agents_router,
    prefix="/api/v1/agents",
    tags=["AI Agents"],
)
app.include_router(
    predictive_health_router,
    prefix="/api/v1/predictions",
    tags=["Predictive Health"],
)
app.include_router(
    lab_results_router,
    prefix="/api/v1/lab-results",
    tags=["Lab Results"],
)
app.include_router(
    health_twin_router,
    prefix="/api/v1/health-twin",
    tags=["Health Twin"],
)
app.include_router(
    medication_intelligence_router,
    prefix="/api/v1",
    tags=["Medication Intelligence"],
)
app.include_router(
    symptom_correlations_router,
    prefix="/api/v1",
    tags=["Symptom Correlations"],
)
app.include_router(
    specialist_agents_router,
    prefix="/api/v1/specialist-agents",
    tags=["AI Agents"],
)
app.include_router(profile_router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(export_router, prefix="/api/v1/export", tags=["Export"])
app.include_router(goals_router, prefix="/api/v1/goals", tags=["Goals"])
app.include_router(
    weekly_checkins_router, prefix="/api/v1/checkins", tags=["Check-ins"]
)
app.include_router(care_plans_router, prefix="/api/v1/care-plans", tags=["Care Plans"])
app.include_router(sharing_router, prefix="/api/v1/share", tags=["Care Team Sharing"])
app.include_router(caregiver_router, prefix="/api/v1/caregiver", tags=["Caregiver"])
app.include_router(
    notifications_router, prefix="/api/v1/notifications", tags=["Notifications"]
)
app.include_router(
    interventions_router,
    prefix="/api/v1/interventions",
    tags=["N-of-1 Interventions"],
)
app.include_router(
    efficacy_router,
    prefix="/api/v1/efficacy",
    tags=["Personal Efficacy"],
)
app.include_router(
    nudges_router,
    prefix="/api/v1/nudges",
    tags=["Nudge Engine"],
)
app.include_router(
    journeys_router,
    prefix="/api/v1/journeys",
    tags=["Goal Journeys"],
)
app.include_router(
    cycle_tracking_router,
    prefix="/api/v1/cycle",
    tags=["Cycle Tracking"],
)
app.include_router(
    onboarding_router,
    prefix="/api/v1/onboarding",
    tags=["Onboarding"],
)
app.include_router(batch_router, prefix="/api/v1/batch", tags=["Batch"])
app.include_router(
    medical_records_router,
    prefix="/api/v1/medical-records",
    tags=["Medical Records"],
)
app.include_router(
    profile_intelligence_router,
    prefix="/api/v1/profile-intelligence",
    tags=["Profile Intelligence"],
)
app.include_router(
    clinical_research_router,
    prefix="/api/v1/research",
    tags=["Clinical Research"],
)
app.include_router(
    insights_intelligence_router,
    prefix="/api/v1/insights-intelligence",
    tags=["Insights Intelligence"],
)
app.include_router(
    symptom_intelligence_router,
    prefix="/api/v1/symptom-intelligence",
    tags=["Symptom Intelligence"],
)
app.include_router(
    daily_brief_router,
    prefix="/api/v1/health-brief",
    tags=["Daily Health Brief"],
)
app.include_router(
    med_intelligence_router,
    prefix="/api/v1/med-intelligence",
    tags=["Medication Intelligence"],
)
app.include_router(
    lab_intelligence_router,
    prefix="/api/v1/lab-intelligence",
    tags=["Lab Intelligence"],
)
app.include_router(
    nutrition_assistant_router,
    prefix="/api/v1/nutrition-ai",
    tags=["Nutrition Assistant"],
)
app.include_router(
    timeline_actions_router,
    prefix="/api/v1/timeline-actions",
    tags=["Timeline Actions"],
)
app.include_router(
    weekly_review_router,
    prefix="/api/v1/insights",
    tags=["AI Insights"],
)
app.include_router(auth_refresh_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(
    health_data_router,
    prefix="/api/v1/health-data",
    tags=["Native Health Data"],
)


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
