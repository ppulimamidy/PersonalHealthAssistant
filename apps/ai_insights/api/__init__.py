"""
AI Insights API
RESTful API endpoints for AI insights and recommendations.
"""

from .insights import router as insights_router
from .recommendations import router as recommendations_router
from .health_scores import router as health_scores_router
from .patterns import router as patterns_router
from .agents import router as agents_router 