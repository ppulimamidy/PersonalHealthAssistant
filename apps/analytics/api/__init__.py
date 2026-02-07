"""
Analytics API Package

API endpoints for analytics processing and insights.
"""

from .analytics import router as analytics_router

__all__ = [
    "analytics_router"
] 