"""
Health Tracking API Module
Organizes all API routers for the health tracking service.
"""

from .vitals import router as vitals_router
from .symptoms import router as symptoms_router
from .metrics import router as metrics_router
from .goals import router as goals_router
from .insights import router as insights_router
from .analytics import router as analytics_router
from .devices import router as devices_router
from .alerts import router as alerts_router

# API version prefix
API_V1_PREFIX = "/api/v1/health-tracking"

# All routers for easy inclusion
routers = [
    vitals_router,
    symptoms_router,
    metrics_router,
    goals_router,
    insights_router,
    analytics_router,
    devices_router,
    alerts_router
] 