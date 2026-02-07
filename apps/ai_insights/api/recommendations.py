"""
Recommendations API
RESTful API endpoints for health recommendations.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/health")
async def health_check():
    """Health check endpoint for recommendations."""
    return {
        "service": "recommendations",
        "status": "healthy",
        "message": "Recommendations API is running"
    } 