"""
Medical Records API Package
Contains all API routers for the medical records service.
"""

from . import lab_results, documents, imaging, clinical_reports, agents, epic_fhir

__all__ = ["lab_results", "documents", "imaging", "clinical_reports", "agents", "epic_fhir"] 