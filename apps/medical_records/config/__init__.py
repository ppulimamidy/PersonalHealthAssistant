"""
Medical Records Configuration Module

This module contains configuration settings for the medical records service,
including Epic FHIR integration settings.
"""

from .epic_fhir_config import epic_fhir_config, EpicEnvironment, EPIC_FHIR_RESOURCES

__all__ = [
    "epic_fhir_config",
    "EpicEnvironment", 
    "EPIC_FHIR_RESOURCES"
] 