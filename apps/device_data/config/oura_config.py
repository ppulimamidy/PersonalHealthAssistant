"""
Oura API Configuration
Configuration settings for Oura Ring API integration.
"""

import os
from typing import Dict, Any
from pydantic import BaseModel, Field
from common.config.settings import get_settings

settings = get_settings()


class OuraAPIConfig(BaseModel):
    """Oura API configuration settings."""
    
    # Sandbox mode
    use_sandbox: bool = Field(
        default=False,
        description="Use Oura sandbox environment for testing"
    )
    
    # API Base URLs
    api_base_url: str = Field(
        default="https://api.ouraring.com/v2",
        description="Oura API base URL"
    )
    
    # Sandbox API Base URL
    sandbox_api_base_url: str = Field(
        default="https://api.ouraring.com/v2",
        description="Oura Sandbox API base URL"
    )
    
    # API Endpoints
    endpoints: Dict[str, str] = Field(
        default={
            "userinfo": "/userinfo",
            "daily_sleep": "/usercollection/daily_sleep",
            "daily_activity": "/usercollection/daily_activity", 
            "daily_readiness": "/usercollection/daily_readiness",
            "heart_rate": "/usercollection/heart_rate",
            "personal_info": "/usercollection/personal_info",
            "workout": "/usercollection/workout",
            "session": "/usercollection/session",
            "tag": "/usercollection/tag",
            "sleep": "/usercollection/sleep",
            "activity": "/usercollection/activity",
            "readiness": "/usercollection/readiness",
            "ideal_bedtime": "/usercollection/ideal_bedtime",
            "bedtime": "/usercollection/bedtime",
        },
        description="Oura API endpoints"
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
        default=30,
        description="Default number of days to sync when no date range specified"
    )
    
    max_sync_days: int = Field(
        default=365,
        description="Maximum number of days to sync in one request"
    )
    
    # Data types supported
    supported_data_types: Dict[str, list] = Field(
        default={
            "sleep": [
                "sleep_duration",
                "sleep_efficiency", 
                "sleep_latency",
                "sleep_rem",
                "sleep_deep",
                "sleep_light",
                "sleep_awake",
                "sleep_score",
                "sleep_temperature_deviation",
                "sleep_respiratory_rate",
                "sleep_hr_lowest",
                "sleep_hr_average",
                "sleep_rmssd",
                "sleep_hr_5min_lowest"
            ],
            "activity": [
                "steps",
                "calories_active",
                "calories_total",
                "activity_score",
                "daily_movement",
                "non_wear_time",
                "rest_mode",
                "active_calories",
                "met_min_inactive",
                "met_min_low",
                "met_min_medium",
                "met_min_high",
                "average_met",
                "class_5min",
                "steps_previous_day",
                "met_1min"
            ],
            "readiness": [
                "readiness_score",
                "readiness_score_previous_night",
                "readiness_score_sleep_balance",
                "readiness_score_previous_day_activity",
                "readiness_score_activity_balance",
                "readiness_score_resting_hr",
                "readiness_score_hrv_balance",
                "readiness_score_recovery_index",
                "readiness_score_temperature"
            ],
            "heart_rate": [
                "heart_rate",
                "heart_rate_variability"
            ],
            "temperature": [
                "temperature_deviation",
                "temperature_trend"
            ]
        },
        description="Supported Oura data types by category"
    )
    
    # Environment variables
    @classmethod
    def from_env(cls) -> "OuraAPIConfig":
        """Create config from environment variables."""
        return cls(
            use_sandbox=os.getenv("OURA_USE_SANDBOX", "false").lower() == "true",
            api_base_url=os.getenv("OURA_API_BASE_URL", "https://api.ouraring.com/v2"),
            sandbox_api_base_url=os.getenv("OURA_SANDBOX_API_BASE_URL", "https://api.ouraring.com/v2"),
            rate_limit_per_minute=int(os.getenv("OURA_RATE_LIMIT_PER_MINUTE", "60")),
            request_timeout=int(os.getenv("OURA_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("OURA_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("OURA_RETRY_DELAY", "1.0")),
            default_sync_days=int(os.getenv("OURA_DEFAULT_SYNC_DAYS", "30")),
            max_sync_days=int(os.getenv("OURA_MAX_SYNC_DAYS", "365"))
        )


# Global Oura config instance
oura_config = OuraAPIConfig.from_env() 