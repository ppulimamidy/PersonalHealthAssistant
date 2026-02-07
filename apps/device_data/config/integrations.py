"""
Device Integration Configuration
Configuration settings for various device integrations.
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings


class IntegrationSettings(BaseSettings):
    """Settings for device integrations"""
    
    # Apple Health
    APPLE_HEALTH_ENABLED: bool = True
    APPLE_HEALTH_CLIENT_ID: str = ""
    APPLE_HEALTH_CLIENT_SECRET: str = ""
    APPLE_HEALTH_REDIRECT_URI: str = ""
    
    # Fitbit
    FITBIT_ENABLED: bool = True
    FITBIT_CLIENT_ID: str = ""
    FITBIT_CLIENT_SECRET: str = ""
    FITBIT_REDIRECT_URI: str = ""
    
    # Whoop
    WHOOP_ENABLED: bool = True
    WHOOP_CLIENT_ID: str = ""
    WHOOP_CLIENT_SECRET: str = ""
    WHOOP_REDIRECT_URI: str = ""
    
    # CGM (Dexcom)
    CGM_ENABLED: bool = True
    CGM_CLIENT_ID: str = ""
    CGM_CLIENT_SECRET: str = ""
    CGM_REDIRECT_URI: str = ""
    
    # General settings
    SYNC_INTERVAL_HOURS: int = 24
    MAX_SYNC_DAYS: int = 30
    SYNC_TIMEOUT_SECONDS: int = 300
    
    class Config:
        env_file = ".env"


# Integration configurations
INTEGRATION_CONFIGS = {
    "apple_health": {
        "name": "Apple Health",
        "api_base_url": "https://health.apple.com/api",
        "auth_url": "https://appleid.apple.com/auth/authorize",
        "token_url": "https://appleid.apple.com/auth/token",
        "scopes": ["health.read", "health.write"],
        "supported_metrics": [
            "heart_rate", "steps", "sleep", "weight", "blood_pressure",
            "blood_glucose", "oxygen_saturation", "respiratory_rate"
        ]
    },
    "fitbit": {
        "name": "Fitbit",
        "api_base_url": "https://api.fitbit.com/1",
        "auth_url": "https://www.fitbit.com/oauth2/authorize",
        "token_url": "https://api.fitbit.com/oauth2/token",
        "scopes": ["activity", "heartrate", "sleep", "weight", "profile"],
        "supported_metrics": [
            "heart_rate", "steps", "sleep", "weight", "calories_burned",
            "distance_walked", "active_minutes", "exercise_duration"
        ]
    },
    "whoop": {
        "name": "Whoop",
        "api_base_url": "https://api.whoop.com/developer/v1",
        "auth_url": "https://api.whoop.com/oauth2/authorize",
        "token_url": "https://api.whoop.com/oauth2/token",
        "scopes": ["read:recovery", "read:sleep", "read:workout", "read:profile"],
        "supported_metrics": [
            "heart_rate", "sleep", "recovery", "strain", "respiratory_rate"
        ]
    },
    "cgm": {
        "name": "Continuous Glucose Monitor",
        "api_base_url": "https://api.dexcom.com/v2",
        "auth_url": "https://api.dexcom.com/v2/oauth2/login",
        "token_url": "https://api.dexcom.com/v2/oauth2/token",
        "scopes": ["offline_access", "egv", "calibration", "event"],
        "supported_metrics": [
            "blood_glucose", "calibration", "events"
        ]
    }
}


def get_integration_config(integration_type: str) -> Dict[str, Any]:
    """Get configuration for a specific integration"""
    return INTEGRATION_CONFIGS.get(integration_type.lower(), {})


def get_supported_integrations() -> Dict[str, Dict[str, Any]]:
    """Get all supported integrations"""
    return INTEGRATION_CONFIGS


def is_integration_enabled(integration_type: str) -> bool:
    """Check if an integration is enabled"""
    settings = IntegrationSettings()
    
    if integration_type.lower() == "apple_health":
        return settings.APPLE_HEALTH_ENABLED
    elif integration_type.lower() == "fitbit":
        return settings.FITBIT_ENABLED
    elif integration_type.lower() == "whoop":
        return settings.WHOOP_ENABLED
    elif integration_type.lower() == "cgm":
        return settings.CGM_ENABLED
    
    return False


def get_integration_credentials(integration_type: str) -> Dict[str, str]:
    """Get credentials for a specific integration"""
    settings = IntegrationSettings()
    
    if integration_type.lower() == "apple_health":
        return {
            "client_id": settings.APPLE_HEALTH_CLIENT_ID,
            "client_secret": settings.APPLE_HEALTH_CLIENT_SECRET,
            "redirect_uri": settings.APPLE_HEALTH_REDIRECT_URI
        }
    elif integration_type.lower() == "fitbit":
        return {
            "client_id": settings.FITBIT_CLIENT_ID,
            "client_secret": settings.FITBIT_CLIENT_SECRET,
            "redirect_uri": settings.FITBIT_REDIRECT_URI
        }
    elif integration_type.lower() == "whoop":
        return {
            "client_id": settings.WHOOP_CLIENT_ID,
            "client_secret": settings.WHOOP_CLIENT_SECRET,
            "redirect_uri": settings.WHOOP_REDIRECT_URI
        }
    elif integration_type.lower() == "cgm":
        return {
            "client_id": settings.CGM_CLIENT_ID,
            "client_secret": settings.CGM_CLIENT_SECRET,
            "redirect_uri": settings.CGM_REDIRECT_URI
        }
    
    return {}


# OAuth flow helpers
def get_oauth_url(integration_type: str, state: str = None) -> str:
    """Generate OAuth URL for an integration"""
    config = get_integration_config(integration_type)
    credentials = get_integration_credentials(integration_type)
    
    if not config or not credentials.get("client_id"):
        raise ValueError(f"Integration {integration_type} not configured")
    
    params = {
        "client_id": credentials["client_id"],
        "response_type": "code",
        "scope": " ".join(config["scopes"]),
        "redirect_uri": credentials["redirect_uri"]
    }
    
    if state:
        params["state"] = state
    
    # Build URL with parameters
    url = config["auth_url"]
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{url}?{param_str}"


def get_token_exchange_data(integration_type: str, auth_code: str) -> Dict[str, str]:
    """Get data for token exchange"""
    credentials = get_integration_credentials(integration_type)
    config = get_integration_config(integration_type)
    
    return {
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": credentials["redirect_uri"]
    } 