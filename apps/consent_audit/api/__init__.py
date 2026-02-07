"""
API endpoints for the Personal Health Assistant Consent Audit Service.

This package contains all the API endpoints for consent audit functionality.
"""

from .audit import router as audit_router
from .compliance import router as compliance_router
from .consent import router as consent_router
from .gdpr import router as gdpr_router
from .hipaa import router as hipaa_router

__all__ = [
    "audit_router",
    "compliance_router",
    "consent_router",
    "gdpr_router",
    "hipaa_router"
] 