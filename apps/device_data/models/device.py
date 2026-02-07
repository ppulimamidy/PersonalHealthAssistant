"""
Device Model
Handles device registration, management, and metadata.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pydantic import BaseModel, Field, validator

from common.models.base import Base

# Note: We use string references for foreign keys to avoid circular imports
# This follows the microservices pattern where each service owns its schema


class DeviceType(str, Enum):
    """Types of health devices"""
    # Wearables
    WEARABLE = "wearable"
    SMARTWATCH = "smartwatch"
    FITNESS_TRACKER = "fitness_tracker"
    SMART_RING = "smart_ring"  # Oura Ring, etc.
    SMART_BAND = "smart_band"
    SMART_CLOTHING = "smart_clothing"
    SMART_SHOES = "smart_shoes"
    SMART_GLASSES = "smart_glasses"
    SMART_EARBUDS = "smart_earbuds"
    
    # Health Monitors
    BLOOD_PRESSURE_MONITOR = "blood_pressure_monitor"
    GLUCOSE_MONITOR = "glucose_monitor"
    THERMOMETER = "thermometer"
    SCALE = "scale"
    SLEEP_TRACKER = "sleep_tracker"
    HEART_RATE_MONITOR = "heart_rate_monitor"
    OXYGEN_MONITOR = "oxygen_monitor"
    ECG_MONITOR = "ecg_monitor"
    BLOOD_GLUCOSE_METER = "blood_glucose_meter"
    INSULIN_PUMP = "insulin_pump"
    CONTINUOUS_GLUCOSE_MONITOR = "continuous_glucose_monitor"
    PULSE_OXIMETER = "pulse_oximeter"
    BLOOD_PRESSURE_CUFF = "blood_pressure_cuff"
    
    # Medical Devices
    THERAPY_DEVICE = "therapy_device"
    MEDICATION_DISPENSER = "medication_dispenser"
    CPAP_MACHINE = "cpap_machine"
    INHALER = "inhaler"
    HEARING_AID = "hearing_aid"
    PROSTHETIC = "prosthetic"
    
    # Mobile Apps & Platforms
    MOBILE_APP = "mobile_app"
    HEALTH_PLATFORM = "health_platform"
    FITNESS_APP = "fitness_app"
    NUTRITION_APP = "nutrition_app"
    MEDITATION_APP = "meditation_app"
    
    # Smart Home Health
    SMART_MIRROR = "smart_mirror"
    SMART_TOILET = "smart_toilet"
    SMART_SHOWER = "smart_shower"
    AIR_QUALITY_MONITOR = "air_quality_monitor"
    WATER_QUALITY_MONITOR = "water_quality_monitor"
    
    # Specialized Devices
    FERTILITY_TRACKER = "fertility_tracker"
    PREGNANCY_MONITOR = "pregnancy_monitor"
    BABY_MONITOR = "baby_monitor"
    PET_HEALTH_TRACKER = "pet_health_tracker"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    
    # Research & Clinical
    CLINICAL_DEVICE = "clinical_device"
    RESEARCH_DEVICE = "research_device"
    LAB_EQUIPMENT = "lab_equipment"
    
    # Generic
    OTHER = "other"


class DeviceStatus(str, Enum):
    """Device connection and health status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    SYNCING = "syncing"


class ConnectionType(str, Enum):
    """Device connection methods"""
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    USB = "usb"
    NFC = "nfc"
    CELLULAR = "cellular"
    MANUAL = "manual"
    API = "api"


class Device(Base):
    """Device model for health tracking devices"""
    __tablename__ = "devices"
    __table_args__ = {"schema": "device_data"}
    
    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # User relationship - using string reference to avoid circular imports
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Device identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[DeviceType] = mapped_column(SQLEnum(DeviceType, name="devicetype"), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), unique=True, nullable=True)
    
    # Connection details
    connection_type: Mapped[ConnectionType] = mapped_column(SQLEnum(ConnectionType, name="connectiontype"), nullable=False)
    connection_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Device status
    status: Mapped[DeviceStatus] = mapped_column(SQLEnum(DeviceStatus, name="devicestatus"), default=DeviceStatus.INACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Device capabilities
    supported_metrics: Mapped[List[str]] = mapped_column(JSON, default=list)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    battery_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Metadata
    device_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    # data_points = relationship("DeviceDataPoint", back_populates="device", cascade="all, delete-orphan")  # Temporarily disabled due to foreign key constraints
    
    def __repr__(self):
        return f"<Device(id={self.id}, name='{self.name}', type='{self.device_type}', status='{self.status}')>"


# Pydantic Models for API
class DeviceBase(BaseModel):
    """Base device model for API requests/responses"""
    name: str = Field(..., min_length=1, max_length=255, description="Device name")
    device_type: DeviceType = Field(..., description="Type of health device")
    manufacturer: str = Field(..., min_length=1, max_length=255, description="Device manufacturer")
    model: str = Field(..., min_length=1, max_length=255, description="Device model")
    serial_number: Optional[str] = Field(None, max_length=255, description="Device serial number")
    mac_address: Optional[str] = Field(None, max_length=17, description="Device MAC address")
    connection_type: ConnectionType = Field(..., description="Connection method")
    connection_id: Optional[str] = Field(None, max_length=255, description="Connection identifier")
    supported_metrics: List[str] = Field(default_factory=list, description="Supported health metrics")
    device_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional device metadata")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Device settings")
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is not None:
            # Basic MAC address validation
            import re
            if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
                raise ValueError('Invalid MAC address format')
        return v


class DeviceCreate(DeviceBase):
    """Model for creating a new device"""
    pass


class DeviceUpdate(BaseModel):
    """Model for updating device information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_type: Optional[DeviceType] = None
    manufacturer: Optional[str] = Field(None, min_length=1, max_length=255)
    model: Optional[str] = Field(None, min_length=1, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    mac_address: Optional[str] = Field(None, max_length=17)
    connection_type: Optional[ConnectionType] = None
    connection_id: Optional[str] = Field(None, max_length=255)
    api_key: Optional[str] = Field(None, max_length=500)
    api_secret: Optional[str] = Field(None, max_length=500)
    status: Optional[DeviceStatus] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    supported_metrics: Optional[List[str]] = None
    firmware_version: Optional[str] = Field(None, max_length=100)
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    device_metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is not None:
            import re
            if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
                raise ValueError('Invalid MAC address format')
        return v


class DeviceResponse(DeviceBase):
    """Model for device API responses"""
    id: UUID
    user_id: UUID
    status: DeviceStatus
    is_active: bool
    is_primary: bool
    firmware_version: Optional[str]
    battery_level: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime]
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DeviceSummary(BaseModel):
    """Simplified device model for lists and summaries"""
    id: UUID
    name: str
    device_type: DeviceType
    manufacturer: str
    model: str
    status: DeviceStatus
    is_active: bool
    is_primary: bool
    battery_level: Optional[int]
    last_sync_at: Optional[datetime]
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DeviceConnectionRequest(BaseModel):
    """Model for device connection requests"""
    connection_type: ConnectionType
    connection_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


class DeviceSyncRequest(BaseModel):
    """Model for device sync requests"""
    force_sync: bool = Field(default=False, description="Force full sync")
    sync_metrics: Optional[List[str]] = Field(None, description="Specific metrics to sync")
    sync_from_date: Optional[datetime] = Field(None, description="Sync data from this date")
    sync_to_date: Optional[datetime] = Field(None, description="Sync data to this date")


class DeviceHealthCheck(BaseModel):
    """Model for device health status"""
    device_id: UUID
    status: DeviceStatus
    battery_level: Optional[int]
    connection_quality: Optional[str] = Field(None, description="Connection quality indicator")
    last_sync_status: Optional[str] = Field(None, description="Last sync operation status")
    error_message: Optional[str] = Field(None, description="Error message if any")
    firmware_version: Optional[str]
    sync_latency: Optional[float] = Field(None, description="Sync latency in seconds")
    
    class Config:
        from_attributes = True 