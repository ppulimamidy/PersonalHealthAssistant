"""
Agents API
RESTful API endpoints for AI agents.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/health")
async def health_check():
    """Health check endpoint for agents."""
    return {
        "service": "agents",
        "status": "healthy",
        "message": "Agents API is running"
    } 