"""
Dexcom API Configuration
Configuration settings for Dexcom CGM API integration.
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from common.config.settings import get_settings

settings = get_settings()


class DexcomAPIConfig(BaseModel):
    """Dexcom API configuration settings."""
    
    # Sandbox mode
    use_sandbox: bool = Field(
        default=False,
        description="Use Dexcom sandbox environment for testing"
    )
    
    # API Base URLs
    api_base_url: str = Field(
        default="https://api.dexcom.com/v3",
        description="Dexcom API base URL"
    )
    
    # Sandbox API Base URL
    sandbox_api_base_url: str = Field(
        default="https://sandbox-api.dexcom.com/v3",
        description="Dexcom Sandbox API base URL"
    )
    
    # API Endpoints
    endpoints: Dict[str, str] = Field(
        default={
            "authorize": "/oauth2/auth",
            "token": "/oauth2/token",
            "refresh_token": "/oauth2/token",
            "userinfo": "/users/self",
            "data_range": "/users/self/dataRange",
            "egvs": "/users/self/egvs",
            "calibrations": "/users/self/calibrations",
            "events": "/users/self/events",
            "alerts": "/users/self/alerts",
            "devices": "/users/self/devices",
            "statistics": "/users/self/statistics",
        },
        description="Dexcom API endpoints"
    )
    
    # OAuth settings
    client_id: str = Field(
        default="",
        description="Dexcom OAuth client ID"
    )
    
    client_secret: str = Field(
        default="",
        description="Dexcom OAuth client secret"
    )
    
    redirect_uri: str = Field(
        default="",
        description="OAuth redirect URI"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="API rate limit per minute"
    )
    
    # Timeout settings
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    # Retry settings
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    
    retry_delay: float = Field(
        default=1.0,
        description="Delay between retries in seconds"
    )
    
    # Data sync settings
    default_sync_days: int = Field(
        default=7,
        description="Default number of days to sync when no date range specified"
    )
    
    max_sync_days: int = Field(
        default=30,
        description="Maximum number of days to sync in one request"
    )
    
    # Data types supported
    supported_data_types: Dict[str, list] = Field(
        default={
            "glucose": [
                "continuous_glucose",
                "glucose_trend",
                "glucose_calibration"
            ],
            "events": [
                "insulin_event",
                "carb_event",
                "glucose_alert"
            ],
            "device": [
                "sensor_status",
                "transmitter_status"
            ]
        },
        description="Supported Dexcom data types by category"
    )
    
    # Sandbox users
    sandbox_users: Dict[str, str] = Field(
        default={
            "User7": "G7 Mobile App",
            "User8": "ONE+ Mobile App", 
            "User6": "G6 Mobile App",
            "User4": "G6 Touchscreen Receiver"
        },
        description="Available sandbox users for testing"
    )
    
    # Environment variables
    @classmethod
    def from_env(cls) -> "DexcomAPIConfig":
        """Create config from environment variables."""
        return cls(
            use_sandbox=os.getenv("DEXCOM_USE_SANDBOX", "false").lower() == "true",
            api_base_url=os.getenv("DEXCOM_API_BASE_URL", "https://api.dexcom.com/v3"),
            sandbox_api_base_url=os.getenv("DEXCOM_SANDBOX_API_BASE_URL", "https://sandbox-api.dexcom.com/v3"),
            client_id=os.getenv("DEXCOM_CLIENT_ID", ""),
            client_secret=os.getenv("DEXCOM_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("DEXCOM_REDIRECT_URI", ""),
            rate_limit_per_minute=int(os.getenv("DEXCOM_RATE_LIMIT_PER_MINUTE", "60")),
            request_timeout=int(os.getenv("DEXCOM_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("DEXCOM_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("DEXCOM_RETRY_DELAY", "1.0")),
            default_sync_days=int(os.getenv("DEXCOM_DEFAULT_SYNC_DAYS", "7")),
            max_sync_days=int(os.getenv("DEXCOM_MAX_SYNC_DAYS", "30"))
        )


# Global Dexcom config instance
dexcom_config = DexcomAPIConfig.from_env() 