"""
Knowledge Graph API Package.

This package contains all the API endpoints for the Knowledge Graph Service.
"""

from .knowledge import router as knowledge_router

__all__ = ["knowledge_router"] 