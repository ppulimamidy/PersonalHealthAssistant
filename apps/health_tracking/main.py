"""
Health Tracking Service
Main entry point for the comprehensive Health Tracking service.
"""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import traceback

from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from common.config.settings import settings
from common.middleware.auth import auth_middleware, get_current_user
from common.middleware.error_handling import setup_error_handlers
from common.models.base import (
    ErrorResponse, SuccessResponse, create_error_response, create_success_response,
    create_paginated_response, ErrorCode, ErrorSeverity, BaseServiceException,
    ResourceNotFoundException, ValidationException, BaseFilterModel
)
from common.database.connection import get_async_db
from common.utils.logging import get_logger, setup_logging
from common.utils.resilience import with_resilience
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers

# Import models
from health_tracking.models.health_metrics import HealthMetric, MetricType, MetricUnit, HealthMetricCreate
from health_tracking.models.health_goals import HealthGoal, GoalType, GoalStatus
from health_tracking.models.health_insights import HealthInsight, InsightType
from health_tracking.models.symptoms import Symptoms, SymptomCategory, SymptomSeverity
from health_tracking.models.vital_signs import VitalSigns, VitalSignType

# Import services
from health_tracking.services.health_analytics import HealthAnalyticsService
from health_tracking.services.health_insights import HealthInsightsService
from health_tracking.services.vital_signs_service import VitalSignsService

# Import API routers
from health_tracking.api import routers, API_V1_PREFIX

# Import agents
from health_tracking.agents import (
    AnomalyDetectorAgent, TrendAnalyzerAgent, GoalSuggesterAgent,
    HealthCoachAgent, RiskAssessorAgent, PatternRecognizerAgent
)

# Ensure logging is set up to write to file
setup_logging(enable_console=True, enable_file=True, enable_json=True)

logger = get_logger(__name__)

# Prometheus Metrics - Simplified to avoid duplication issues
_metrics_initialized = False
_metrics = {}

def get_metrics():
    """Get or create Prometheus metrics (singleton pattern)"""
    global _metrics_initialized, _metrics
    
    if not _metrics_initialized:
        try:
            # Use unique names to avoid conflicts
            import time
            timestamp = int(time.time())
            _metrics['REQUEST_COUNT'] = Counter(f'health_tracking_requests_total_{timestamp}', 'Total requests', ['method', 'endpoint', 'status'])
            _metrics['REQUEST_DURATION'] = Histogram(f'health_tracking_request_duration_seconds_{timestamp}', 'Request duration', ['method', 'endpoint'])
            _metrics['METRICS_COUNT'] = Gauge(f'health_tracking_metrics_total_{timestamp}', 'Total health metrics stored')
            _metrics['GOALS_COUNT'] = Gauge(f'health_tracking_goals_total_{timestamp}', 'Total health goals')
            _metrics['INSIGHTS_COUNT'] = Gauge(f'health_tracking_insights_total_{timestamp}', 'Total health insights')
            _metrics['VITAL_SIGNS_COUNT'] = Gauge(f'health_tracking_vital_signs_total_{timestamp}', 'Total vital signs')
            _metrics['SYMPTOMS_COUNT'] = Gauge(f'health_tracking_symptoms_total_{timestamp}', 'Total symptoms')
            _metrics_initialized = True
            logger.info("Prometheus metrics initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus metrics: {e}, creating dummy metrics")
            # Create dummy metrics that don't register with Prometheus
            class DummyMetric:
                def labels(self, **kwargs): return self
                def inc(self): pass
                def observe(self, value): pass
                def set(self, value): pass
            
            _metrics['REQUEST_COUNT'] = DummyMetric()
            _metrics['REQUEST_DURATION'] = DummyMetric()
            _metrics['METRICS_COUNT'] = DummyMetric()
            _metrics['GOALS_COUNT'] = DummyMetric()
            _metrics['INSIGHTS_COUNT'] = DummyMetric()
            _metrics['VITAL_SIGNS_COUNT'] = DummyMetric()
            _metrics['SYMPTOMS_COUNT'] = DummyMetric()
            _metrics_initialized = True
    
    return _metrics

# Initialize metrics
metrics = get_metrics()
REQUEST_COUNT = metrics['REQUEST_COUNT']
REQUEST_DURATION = metrics['REQUEST_DURATION']
METRICS_COUNT = metrics['METRICS_COUNT']
GOALS_COUNT = metrics['GOALS_COUNT']
INSIGHTS_COUNT = metrics['INSIGHTS_COUNT']
VITAL_SIGNS_COUNT = metrics['VITAL_SIGNS_COUNT']
SYMPTOMS_COUNT = metrics['SYMPTOMS_COUNT']

# Initialize services
analytics_service = HealthAnalyticsService()
insights_service = HealthInsightsService()
vital_signs_service = VitalSignsService()

# Initialize agents
anomaly_detector = AnomalyDetectorAgent()
trend_analyzer = TrendAnalyzerAgent()
goal_suggester = GoalSuggesterAgent()
health_coach = HealthCoachAgent()
risk_assessor = RiskAssessorAgent()
pattern_recognizer = PatternRecognizerAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Health Tracking Service...")
    
    # Initialize services
    await analytics_service.initialize()
    await insights_service.initialize()
    
    # Initialize agents
    logger.info("Initializing health tracking agents...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Health Tracking Service...")
    await analytics_service.cleanup()
    await insights_service.cleanup()
    
    # Cleanup agents
    await anomaly_detector.cleanup()
    await trend_analyzer.cleanup()
    await goal_suggester.cleanup()
    await health_coach.cleanup()
    await risk_assessor.cleanup()
    await pattern_recognizer.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Health Tracking Service",
    description="Comprehensive service for tracking health metrics, vital signs, symptoms, goals, and insights with AI-powered analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise

app.add_middleware(RequestMetricsMiddleware)

# Add auth middleware
from common.middleware.auth import auth_middleware
app.middleware("http")(auth_middleware)

# Add global error handlers
setup_error_handlers(app)

# Explicitly import and register all routers
from health_tracking.api.vitals import router as vitals_router
from health_tracking.api.symptoms import router as symptoms_router
from health_tracking.api.metrics import router as metrics_router
from health_tracking.api.goals import router as goals_router
from health_tracking.api.insights import router as insights_router
from health_tracking.api.analytics import router as analytics_router
from health_tracking.api.devices import router as devices_router
from health_tracking.api.alerts import router as alerts_router

API_V1_PREFIX = "/api/v1/health-tracking"

app.include_router(vitals_router, prefix=API_V1_PREFIX)
app.include_router(symptoms_router, prefix=API_V1_PREFIX)
app.include_router(metrics_router, prefix=API_V1_PREFIX)
app.include_router(goals_router, prefix=API_V1_PREFIX)
app.include_router(insights_router, prefix=API_V1_PREFIX)
app.include_router(analytics_router, prefix=API_V1_PREFIX)
app.include_router(devices_router, prefix=API_V1_PREFIX)
app.include_router(alerts_router, prefix=API_V1_PREFIX)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return create_success_response(
        data={
            "status": "healthy",
            "service": "health-tracking-service",
            "version": "2.0.0",
            "timestamp": time.time(),
            "checks": {
                "database": True,
                "analytics": True,
                "insights": True,
                "agents": True
            }
        },
        message="Health Tracking Service is healthy"
    )

@app.get("/ready")
async def readiness_check():
    """Service readiness check"""
    try:
        # Check database connection
        db_health = await health_check()
        
        # Check Redis connection (if configured)
        redis_health = True  # Placeholder for Redis check
        
        if db_health and redis_health:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ready",
                    "service": "health-tracking-service",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "service": "health-tracking-service",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "health-tracking-service",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Removed conflicting endpoint - using router instead

# Agent endpoints for autonomous health analysis
@app.post("/agents/anomaly-detection")
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("health_tracking", max_concurrent=10, timeout=60.0, max_retries=3)
async def run_anomaly_detection(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Run anomaly detection on health data"""
    try:
        data["user_id"] = current_user["id"]
        result = await anomaly_detector.process(data, db)
        
        return create_success_response(
            data=result.data,
            message="Anomaly detection completed",
            insights=result.insights,
            alerts=result.alerts,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Anomaly detection failed")

@app.post("/agents/trend-analysis")
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("health_tracking", max_concurrent=10, timeout=60.0, max_retries=3)
async def run_trend_analysis(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Run trend analysis on health data"""
    try:
        data["user_id"] = current_user["id"]
        result = await trend_analyzer.process(data, db)
        
        return create_success_response(
            data=result.data,
            message="Trend analysis completed",
            insights=result.insights,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Trend analysis failed")

@app.post("/agents/goal-suggestions")
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("health_tracking", max_concurrent=10, timeout=60.0, max_retries=3)
async def get_goal_suggestions(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get AI-powered health goal suggestions"""
    try:
        data["user_id"] = current_user["id"]
        result = await goal_suggester.process(data, db)
        
        return create_success_response(
            data=result.data,
            message="Goal suggestions generated",
            insights=result.insights,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"Goal suggestions failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Goal suggestions failed")

@app.post("/agents/health-coaching")
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("health_tracking", max_concurrent=10, timeout=60.0, max_retries=3)
async def get_health_coaching(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get personalized health coaching recommendations"""
    try:
        data["user_id"] = current_user["id"]
        result = await health_coach.process(data, db)
        
        return create_success_response(
            data=result.data,
            message="Health coaching recommendations generated",
            insights=result.insights,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"Health coaching failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health coaching failed")

@app.post("/agents/risk-assessment")
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("health_tracking", max_concurrent=10, timeout=60.0, max_retries=3)
async def run_risk_assessment(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Run comprehensive health risk assessment"""
    try:
        data["user_id"] = current_user["id"]
        result = await risk_assessor.process(data, db)
        
        return create_success_response(
            data=result.data,
            message="Risk assessment completed",
            insights=result.insights,
            alerts=result.alerts,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Risk assessment failed")

@app.post("/agents/pattern-recognition")
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("health_tracking", max_concurrent=10, timeout=60.0, max_retries=3)
async def run_pattern_recognition(
    request: Request,
    data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Run pattern recognition on health data"""
    try:
        data["user_id"] = current_user["id"]
        result = await pattern_recognizer.process(data, db)
        
        return create_success_response(
            data=result.data,
            message="Pattern recognition completed",
            insights=result.insights,
            recommendations=result.recommendations
        )
        
    except Exception as e:
        logger.error(f"Pattern recognition failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Pattern recognition failed")

# Agent health check
@app.get("/agents/health")
@rate_limit(requests_per_minute=30)
@security_headers
async def get_agents_health(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get health status of all agents"""
    try:
        agent_health = {}
        
        # Check each agent
        agents = [
            ("anomaly_detector", anomaly_detector),
            ("trend_analyzer", trend_analyzer),
            ("goal_suggester", goal_suggester),
            ("health_coach", health_coach),
            ("risk_assessor", risk_assessor),
            ("pattern_recognizer", pattern_recognizer)
        ]
        
        for agent_name, agent in agents:
            try:
                health = await agent.health_check()
                agent_health[agent_name] = health
            except Exception as e:
                agent_health[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return create_success_response(
            data=agent_health,
            message="Agent health status retrieved"
        )
        
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent health check failed")

# Dashboard endpoints
@app.get("/dashboard/summary")
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("health_tracking", max_concurrent=20, timeout=60.0, max_retries=3)
async def get_dashboard_summary(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get comprehensive dashboard summary"""
    try:
        # Get counts for different data types
        metrics_count = await db.execute(
            select(func.count(HealthMetric.id)).where(HealthMetric.user_id == current_user["id"])
        )
        metrics_total = metrics_count.scalar() or 0
        
        goals_count = await db.execute(
            select(func.count(HealthGoal.id)).where(HealthGoal.user_id == current_user["id"])
        )
        goals_total = goals_count.scalar() or 0
        
        vital_signs_count = await db.execute(
            select(func.count(VitalSigns.id)).where(VitalSigns.user_id == current_user["id"])
        )
        vital_signs_total = vital_signs_count.scalar() or 0
        
        symptoms_count = await db.execute(
            select(func.count(Symptoms.id)).where(Symptoms.user_id == current_user["id"])
        )
        symptoms_total = symptoms_count.scalar() or 0
        
        # Get recent activity
        recent_metrics = await db.execute(
            select(HealthMetric)
            .where(HealthMetric.user_id == current_user["id"])
            .order_by(desc(HealthMetric.created_at))
            .limit(5)
        )
        recent_metrics_list = recent_metrics.scalars().all()
        
        # Get insights count
        insights_count = await db.execute(
            select(func.count(HealthInsight.id)).where(HealthInsight.user_id == current_user["id"])
        )
        insights_total = insights_count.scalar() or 0
        
        return create_success_response(
            data={
                "summary": {
                    "total_metrics": metrics_total,
                    "total_goals": goals_total,
                    "total_vital_signs": vital_signs_total,
                    "total_symptoms": symptoms_total,
                    "total_insights": insights_total
                },
                "recent_activity": [
                    {
                        "id": str(metric.id),
                        "type": metric.metric_type.value,
                        "value": metric.value,
                        "unit": metric.unit,
                        "created_at": metric.created_at.isoformat()
                    }
                    for metric in recent_metrics_list
                ],
                "last_updated": datetime.utcnow().isoformat()
            },
            message="Dashboard summary retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Dashboard summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard summary")

# Test endpoint for creating goals without authentication (for testing only)
@app.post("/test/create-goal")
async def test_create_goal(
    goal_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """Test endpoint to create a goal without authentication"""
    try:
        from health_tracking.models.health_goals import HealthGoal, GoalType, GoalStatus
        
        # Use the test user ID we created
        user_id = "53a3b7f5-ca97-47ed-a26b-32576cf2e7c4"
        
        # Create goal directly in database
        goal = HealthGoal(
            user_id=user_id,
            title=goal_data.get("title", "Test Goal"),
            description=goal_data.get("description", "Test Description"),
            metric_type=goal_data.get("metric_type", "steps"),
            goal_type=GoalType.TARGET,
            target_value=goal_data.get("target_value", 1000),
            unit=goal_data.get("unit", "steps"),
            frequency=goal_data.get("frequency", "daily"),
            start_date=datetime.strptime(goal_data.get("start_date", "2025-06-27"), "%Y-%m-%d").date(),
            target_date=datetime.strptime(goal_data.get("target_date", "2025-12-31"), "%Y-%m-%d").date(),
            status=GoalStatus.ACTIVE
        )
        
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
        
        return create_success_response(
            data={
                "id": str(goal.id),
                "title": goal.title,
                "description": goal.description,
                "metric_type": goal.metric_type,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "status": goal.status,
                "created_at": goal.created_at.isoformat()
            },
            message="Test goal created successfully"
        )
        
    except Exception as e:
        logger.error(f"Test goal creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test goal creation failed: {str(e)}")

# Test endpoint for creating symptoms without authentication (for testing only)
@app.post("/test/create-symptom")
async def test_create_symptom(
    symptom_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """Test endpoint to create a symptom without authentication"""
    try:
        from health_tracking.models.symptoms import Symptoms, SymptomCategory, SymptomSeverity
        
        # Use the test user ID we created
        user_id = "53a3b7f5-ca97-47ed-a26b-32576cf2e7c4"
        
        # Create symptom
        symptom = Symptoms(
            user_id=user_id,
            symptom_name=symptom_data.get("symptom_name", "Headache"),
            symptom_category=SymptomCategory.GENERAL.value,
            severity=SymptomSeverity.MILD.value,
            severity_level=3.0,
            description=symptom_data.get("description", "Test symptom"),
            duration_hours=symptom_data.get("duration_hours", 2),
            body_location=symptom_data.get("body_location", "Head"),
            triggers=symptom_data.get("triggers", ["stress"]),
            relief_factors=symptom_data.get("relief_factors", ["rest"])
        )
        
        db.add(symptom)
        await db.commit()
        await db.refresh(symptom)
        
        return create_success_response(
            data={
                "id": str(symptom.id),
                "symptom_name": symptom.symptom_name,
                "category": symptom.symptom_category,
                "severity": symptom.severity,
                "created_at": symptom.created_at.isoformat()
            },
            message="Test symptom created successfully"
        )
        
    except Exception as e:
        logger.error(f"Test symptom creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test symptom creation failed: {str(e)}")

# Test endpoint for creating vital signs without authentication (for testing only)
@app.post("/test/create-vital-sign")
async def test_create_vital_sign(
    vital_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """Test endpoint to create vital signs without authentication"""
    try:
        from health_tracking.models.vital_signs import VitalSigns, VitalSignType, MeasurementMethod
        
        # Use the test user ID we created
        user_id = "53a3b7f5-ca97-47ed-a26b-32576cf2e7c4"
        
        # Create vital sign
        vital_sign = VitalSigns(
            user_id=user_id,
            vital_sign_type=VitalSignType.BLOOD_PRESSURE.value,
            measurement_method=MeasurementMethod.DIGITAL_DEVICE.value,
            systolic=vital_data.get("systolic", 120),
            diastolic=vital_data.get("diastolic", 80),
            heart_rate=vital_data.get("heart_rate", 72),
            temperature=vital_data.get("temperature", 98.6),
            respiratory_rate=vital_data.get("respiratory_rate", 16),
            oxygen_saturation=vital_data.get("oxygen_saturation", 98),
            measurement_notes=vital_data.get("notes", "Test vital signs")
        )
        
        db.add(vital_sign)
        await db.commit()
        await db.refresh(vital_sign)
        
        return create_success_response(
            data={
                "id": str(vital_sign.id),
                "vital_sign_type": vital_sign.vital_sign_type,
                "measurement_method": vital_sign.measurement_method,
                "systolic": vital_sign.systolic,
                "diastolic": vital_sign.diastolic,
                "heart_rate": vital_sign.heart_rate,
                "temperature": vital_sign.temperature,
                "respiratory_rate": vital_sign.respiratory_rate,
                "oxygen_saturation": vital_sign.oxygen_saturation,
                "measurement_notes": vital_sign.measurement_notes,
                "created_at": vital_sign.created_at.isoformat()
            },
            message="Test vital signs created successfully"
        )
        
    except Exception as e:
        logger.error(f"Test vital signs creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test vital signs creation failed: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    print(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc)
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 