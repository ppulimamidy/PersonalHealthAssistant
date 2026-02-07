"""
Epic FHIR Configuration

This module contains configuration settings for Epic FHIR integration,
including test sandbox settings and production configurations.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from common.config.settings import get_settings

settings = get_settings()


class EpicEnvironment(str, Enum):
    """Epic FHIR environments."""
    SANDBOX = "sandbox"
    PRODUCTION = "production"
    STAGING = "staging"


class EpicFHIRConfig(BaseModel):
    """Epic FHIR configuration settings."""
    
    # Environment
    environment: EpicEnvironment = EpicEnvironment.SANDBOX
    
    # Base URLs for different environments
    base_urls: Dict[EpicEnvironment, str] = {
        EpicEnvironment.SANDBOX: "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
        EpicEnvironment.PRODUCTION: "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
        EpicEnvironment.STAGING: "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    }
    
    # OAuth2 endpoints
    oauth_urls: Dict[EpicEnvironment, str] = {
        EpicEnvironment.SANDBOX: "https://fhir.epic.com/interconnect-fhir-oauth/oauth2",
        EpicEnvironment.PRODUCTION: "https://fhir.epic.com/interconnect-fhir-oauth/oauth2",
        EpicEnvironment.STAGING: "https://fhir.epic.com/interconnect-fhir-oauth/oauth2"
    }
    
    # Client credentials (should be set via environment variables)
    client_id: str = Field(default="", description="Epic FHIR client ID")
    client_secret: str = Field(default="", description="Epic FHIR client secret")
    
    # Scopes for different access levels
    scopes: Dict[str, str] = {
        "patient_read": "patient/*.read",
        "patient_write": "patient/*.read patient/*.write",
        "system_read": "system/*.read",
        "system_write": "system/*.read system/*.write"
    }
    
    # Default scope - Standalone OAuth without launch context
    default_scope: str = "patient/*.read"
    
    # Timeout settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # FHIR version
    fhir_version: str = "R4"
    
    # Test patient IDs (from Epic sandbox)
    test_patients: Dict[str, str] = {
        "camila": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",  # Camila Lopez
        "derrick": "a1",  # Derrick Lin
        "desiree": "a2",  # Desiree Powell
        "elijah": "a3",   # Elijah Davis
        "linda": "a4",    # Linda Ross
        "olivia": "a5"    # Olivia Roberts
    }
    
    # Test MyChart users
    test_mychart_users: Dict[str, str] = {
        "camila": "camila",    # Camila Lopez
        "derrick": "derrick",  # Derrick Lin
        "desiree": "desiree",  # Desiree Powell
        "elijah": "elijah",    # Elijah Davis
        "linda": "linda",      # Linda Ross
        "olivia": "olivia"     # Olivia Roberts
    }
    
    # SMART on FHIR launch settings
    launch_url: Optional[str] = Field(None, description="SMART on FHIR launch URL")
    redirect_uri: Optional[str] = Field(None, description="OAuth2 redirect URI")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, **data):
        # Load from environment variables
        env_data = {}
        
        # Client credentials
        if "EPIC_FHIR_CLIENT_ID" in os.environ:
            env_data["client_id"] = os.environ["EPIC_FHIR_CLIENT_ID"]
        if "EPIC_FHIR_CLIENT_SECRET" in os.environ:
            env_data["client_secret"] = os.environ["EPIC_FHIR_CLIENT_SECRET"]
        
        # Environment
        if "EPIC_FHIR_ENVIRONMENT" in os.environ:
            env_data["environment"] = EpicEnvironment(os.environ["EPIC_FHIR_ENVIRONMENT"].lower())
        
        # Launch URL
        if "EPIC_FHIR_LAUNCH_URL" in os.environ:
            env_data["launch_url"] = os.environ["EPIC_FHIR_LAUNCH_URL"]
        
        # Redirect URI
        if "EPIC_FHIR_REDIRECT_URI" in os.environ:
            env_data["redirect_uri"] = os.environ["EPIC_FHIR_REDIRECT_URI"]
        
        # Merge environment data with provided data
        env_data.update(data)
        super().__init__(**env_data)
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the current environment."""
        return self.base_urls[self.environment]
    
    @property
    def oauth_url(self) -> str:
        """Get the OAuth URL for the current environment."""
        return self.oauth_urls[self.environment]
    
    @property
    def token_endpoint(self) -> str:
        """Get the token endpoint URL."""
        return f"{self.oauth_url}/token"
    
    @property
    def authorize_endpoint(self) -> str:
        """Get the authorize endpoint URL."""
        return f"{self.oauth_url}/authorize"
    
    @property
    def scope(self) -> str:
        """Get the current scope."""
        return self.default_scope
    
    def get_test_patient_id(self, patient_name: str) -> Optional[str]:
        """Get test patient ID by name."""
        return self.test_patients.get(patient_name.lower())
    
    def get_test_patient_name(self, patient_id: str) -> Optional[str]:
        """Get test patient name by ID."""
        for name, pid in self.test_patients.items():
            if pid == patient_id:
                return name
        return None
    
    def get_test_mychart_user(self, user_name: str) -> Optional[str]:
        """Get test MyChart user by name."""
        return self.test_mychart_users.get(user_name.lower())
    
    def validate_config(self) -> bool:
        """Validate the configuration."""
        if not self.client_id:
            raise ValueError("Epic FHIR client ID is required")
        if not self.client_secret:
            raise ValueError("Epic FHIR client secret is required")
        return True


# Global Epic FHIR configuration instance
epic_fhir_config = EpicFHIRConfig()


# Epic FHIR specific constants
EPIC_FHIR_RESOURCES = {
    "Patient": "Patient",
    "Observation": "Observation", 
    "DiagnosticReport": "DiagnosticReport",
    "DocumentReference": "DocumentReference",
    "ImagingStudy": "ImagingStudy",
    "MedicationRequest": "MedicationRequest",
    "Procedure": "Procedure",
    "Condition": "Condition",
    "AllergyIntolerance": "AllergyIntolerance",
    "Immunization": "Immunization",
    "Encounter": "Encounter",
    "Practitioner": "Practitioner",
    "Organization": "Organization"
}

# Epic FHIR search parameters
EPIC_FHIR_SEARCH_PARAMS = {
    "Patient": ["_id", "identifier", "name", "birthdate", "gender"],
    "Observation": ["patient", "category", "code", "date", "status"],
    "DiagnosticReport": ["patient", "category", "date", "status"],
    "DocumentReference": ["patient", "type", "date", "status"],
    "ImagingStudy": ["patient", "modality", "date", "status"],
    "MedicationRequest": ["patient", "status", "intent", "date"],
    "Procedure": ["patient", "date", "status", "category"],
    "Condition": ["patient", "category", "clinical-status", "date"],
    "AllergyIntolerance": ["patient", "category", "clinical-status"],
    "Immunization": ["patient", "date", "status", "vaccine-code"],
    "Encounter": ["patient", "date", "status", "type"],
    "Practitioner": ["name", "identifier", "specialty"],
    "Organization": ["name", "identifier", "type"]
}

# Epic FHIR error codes
EPIC_FHIR_ERROR_CODES = {
    "invalid_token": "Invalid or expired access token",
    "insufficient_scope": "Insufficient scope for requested resource",
    "patient_not_found": "Patient not found or access denied",
    "resource_not_found": "Requested resource not found",
    "invalid_request": "Invalid request format or parameters",
    "server_error": "Internal server error",
    "rate_limit_exceeded": "Rate limit exceeded"
}

# Epic FHIR content types
EPIC_FHIR_CONTENT_TYPES = {
    "json": "application/fhir+json",
    "xml": "application/fhir+xml",
    "ndjson": "application/fhir+ndjson"
}

# Epic FHIR headers
EPIC_FHIR_HEADERS = {
    "Accept": "application/fhir+json",
    "Content-Type": "application/fhir+json",
    "User-Agent": "PersonalHealthAssistant/1.0.0"
} 