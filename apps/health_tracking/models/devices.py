"""
Health Devices Models
Defines database models and Pydantic schemas for health device management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from common.models.base import Base


class DeviceType(str, Enum):
    """Health device types"""
    FITNESS_TRACKER = "fitness_tracker"
    SMARTWATCH = "smartwatch"
    BLOOD_PRESSURE_MONITOR = "blood_pressure_monitor"
    GLUCOSE_MONITOR = "glucose_monitor"
    WEIGHT_SCALE = "weight_scale"
    THERMOMETER = "thermometer"
    PULSE_OXIMETER = "pulse_oximeter"
    ECG_MONITOR = "ecg_monitor"
    SLEEP_TRACKER = "sleep_tracker"
    HEART_RATE_MONITOR = "heart_rate_monitor"
    OTHER = "other"


class DeviceStatus(str, Enum):
    """Device connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Device(Base):
    """Health device database model"""
    __tablename__ = "devices"
    __table_args__ = {"schema": "health_tracking"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)
    manufacturer = Column(String(255))
    model = Column(String(255))
    serial_number = Column(String(255), unique=True)
    firmware_version = Column(String(100))
    device_status = Column(String(20), default=DeviceStatus.INACTIVE.value)
    last_sync = Column(DateTime)
    battery_level = Column(Integer)
    is_connected = Column(Boolean, default=False)
    connection_method = Column(String(50))  # bluetooth, wifi, usb, etc.
    device_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "device_name": self.device_name,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "device_status": self.device_status,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "battery_level": self.battery_level,
            "is_connected": self.is_connected,
            "connection_method": self.connection_method,
            "device_metadata": self.device_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Pydantic Models
class DeviceBase(BaseModel):
    """Base device model"""
    device_name: str = Field(..., min_length=1, max_length=255, description="Device name")
    device_type: DeviceType = Field(..., description="Type of health device")
    manufacturer: Optional[str] = Field(None, max_length=255, description="Device manufacturer")
    model: Optional[str] = Field(None, max_length=255, description="Device model")
    serial_number: Optional[str] = Field(None, max_length=255, description="Device serial number")
    firmware_version: Optional[str] = Field(None, max_length=100, description="Firmware version")
    connection_method: Optional[str] = Field(None, max_length=50, description="Connection method")
    device_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional device metadata")


class DeviceCreate(DeviceBase):
    """Device creation model"""
    pass


class DeviceUpdate(BaseModel):
    """Device update model"""
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_type: Optional[DeviceType] = None
    manufacturer: Optional[str] = Field(None, max_length=255)
    model: Optional[str] = Field(None, max_length=255)
    firmware_version: Optional[str] = Field(None, max_length=100)
    device_status: Optional[DeviceStatus] = None
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    is_connected: Optional[bool] = None
    connection_method: Optional[str] = Field(None, max_length=50)
    device_metadata: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    """Device response model"""
    id: str
    user_id: str
    device_status: str
    last_sync: Optional[str] = None
    battery_level: Optional[int] = None
    is_connected: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DeviceFilter(BaseModel):
    """Device filter model"""
    device_type: Optional[DeviceType] = None
    device_status: Optional[DeviceStatus] = None
    is_connected: Optional[bool] = None
    manufacturer: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0) 