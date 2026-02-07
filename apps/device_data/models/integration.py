"""
Device Integration Models
Handles integration with external health platforms and devices.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class IntegrationType(str, Enum):
    """Types of device integrations"""
    APPLE_HEALTH = "apple_health"
    FITBIT = "fitbit"
    WHOOP = "whoop"
    GARMIN = "garmin"
    POLAR = "polar"
    SUUNTO = "suunto"
    CGM = "cgm"
    BLOOD_PRESSURE_MONITOR = "blood_pressure_monitor"
    SCALE = "scale"
    SLEEP_TRACKER = "sleep_tracker"
    FITNESS_TRACKER = "fitness_tracker"
    SMARTWATCH = "smartwatch"
    CUSTOM = "custom"


class IntegrationStatus(str, Enum):
    """Integration connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    EXPIRED = "expired"


class IntegrationCreate(BaseModel):
    """Model for creating a new integration"""
    device_id: UUID = Field(..., description="Device ID to integrate")
    integration_type: IntegrationType = Field(..., description="Type of integration")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Integration credentials")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Integration settings")
    sync_interval_hours: int = Field(default=24, ge=1, le=168, description="Sync interval in hours")


class IntegrationUpdate(BaseModel):
    """Model for updating integration information"""
    credentials: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    sync_interval_hours: Optional[int] = Field(None, ge=1, le=168)
    is_active: Optional[bool] = None


class IntegrationResponse(BaseModel):
    """Model for integration API responses"""
    id: UUID
    device_id: UUID
    integration_type: IntegrationType
    status: IntegrationStatus
    is_active: bool
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    sync_interval_hours: int
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    sync_count: int = 0
    last_sync_duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class IntegrationSummary(BaseModel):
    """Simplified integration model for lists and summaries"""
    id: UUID
    device_id: UUID
    integration_type: IntegrationType
    status: IntegrationStatus
    is_active: bool
    last_sync_at: Optional[datetime]
    sync_count: int

    class Config:
        from_attributes = True


class IntegrationConnectionRequest(BaseModel):
    """Model for integration connection requests"""
    device_id: UUID = Field(..., description="Device ID to connect")
    integration_type: IntegrationType = Field(..., description="Type of integration")
    auth_code: Optional[str] = Field(None, description="Authorization code for OAuth")
    refresh_token: Optional[str] = Field(None, description="Refresh token for OAuth")
    api_key: Optional[str] = Field(None, description="API key for direct integration")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Connection settings")


class IntegrationSyncRequest(BaseModel):
    """Model for integration sync requests"""
    device_id: UUID = Field(..., description="Device ID to sync")
    start_date: Optional[datetime] = Field(None, description="Start date for sync")
    end_date: Optional[datetime] = Field(None, description="End date for sync")
    data_types: Optional[List[str]] = Field(None, description="Specific data types to sync")
    force_full_sync: bool = Field(default=False, description="Force a full sync")


class IntegrationHealthCheck(BaseModel):
    """Model for integration health check results"""
    integration_id: UUID
    status: IntegrationStatus
    is_healthy: bool
    last_check_at: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    data_types_available: List[str] = Field(default_factory=list)
    sync_status: Dict[str, Any] = Field(default_factory=dict)
