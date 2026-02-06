"""
Health Metrics Models
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from common.models.base import Base

class MetricType(str, Enum):
    """Types of health metrics"""
    # Physical metrics
    WEIGHT = "weight"
    HEIGHT = "height"
    BMI = "bmi"
    BODY_FAT = "body_fat"
    MUSCLE_MASS = "muscle_mass"
    BONE_DENSITY = "bone_density"
    
    # Vital signs
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    BLOOD_PRESSURE_MEAN = "blood_pressure_mean"
    TEMPERATURE = "temperature"
    RESPIRATORY_RATE = "respiratory_rate"
    OXYGEN_SATURATION = "oxygen_saturation"
    
    # Activity metrics
    STEPS = "steps"
    DISTANCE = "distance"
    CALORIES_BURNED = "calories_burned"
    ACTIVE_MINUTES = "active_minutes"
    SLEEP_DURATION = "sleep_duration"
    SLEEP_QUALITY = "sleep_quality"
    SLEEP_DEEP = "sleep_deep"
    SLEEP_REM = "sleep_rem"
    SLEEP_LIGHT = "sleep_light"
    
    # Nutrition metrics
    CALORIES_CONSUMED = "calories_consumed"
    PROTEIN = "protein"
    CARBS = "carbs"
    FAT = "fat"
    FIBER = "fiber"
    SUGAR = "sugar"
    SODIUM = "sodium"
    WATER = "water"
    
    # Mental health metrics
    MOOD = "mood"
    STRESS_LEVEL = "stress_level"
    ANXIETY_LEVEL = "anxiety_level"
    ENERGY_LEVEL = "energy_level"
    FOCUS_LEVEL = "focus_level"
    
    # Lab results
    GLUCOSE = "glucose"
    BLOOD_GLUCOSE = "blood_glucose"
    CHOLESTEROL_TOTAL = "cholesterol_total"
    CHOLESTEROL_HDL = "cholesterol_hdl"
    CHOLESTEROL_LDL = "cholesterol_ldl"
    TRIGLYCERIDES = "triglycerides"
    HEMOGLOBIN_A1C = "hemoglobin_a1c"
    VITAMIN_D = "vitamin_d"
    VITAMIN_B12 = "vitamin_b12"
    IRON = "iron"
    CALCIUM = "calcium"
    
    # Custom metrics
    CUSTOM = "custom"

class MetricUnit(str, Enum):
    """Units for health metrics"""
    # Weight units
    KG = "kg"
    LBS = "lbs"
    G = "g"
    
    # Length units
    CM = "cm"
    INCHES = "inches"
    M = "m"
    FT = "ft"
    
    # Volume units
    ML = "ml"
    L = "l"
    OZ = "oz"
    CUPS = "cups"
    
    # Energy units
    KCAL = "kcal"
    CAL = "cal"
    KJ = "kj"
    
    # Time units
    MINUTES = "minutes"
    HOURS = "hours"
    SECONDS = "seconds"
    
    # Count units
    COUNT = "count"
    STEPS = "steps"
    BEATS_PER_MINUTE = "bpm"
    BREATHS_PER_MINUTE = "breaths/min"
    
    # Pressure units
    MMHG = "mmHg"
    KPA = "kPa"
    
    # Temperature units
    CELSIUS = "°C"
    FAHRENHEIT = "°F"
    
    # Percentage
    PERCENT = "%"
    
    # Concentration units
    MG_DL = "mg/dL"
    MMOL_L = "mmol/L"
    NG_ML = "ng/mL"
    MCG_DL = "mcg/dL"
    
    # Distance units
    KM = "km"
    MILES = "miles"
    METERS = "meters"
    
    # Custom units
    CUSTOM = "custom"

class HealthMetric(Base):
    """Health metric model"""
    __tablename__ = "health_metrics"
    __table_args__ = (
        Index('idx_health_metrics_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_health_metrics_type_timestamp', 'metric_type', 'timestamp'),
        {'schema': 'health_tracking'}
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)  # Store user ID without foreign key constraint
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    source = Column(String(100), nullable=True)  # e.g., "manual", "fitbit", "apple_health"
    device_id = Column(String(100), nullable=True)  # Device identifier
    notes = Column(Text, nullable=True)
    metric_metadata = Column(JSONB, nullable=True)  # Additional data like location, device info, etc.
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @validator('value')
    def validate_value(cls, v):
        """Validate metric value"""
        if v is None:
            raise ValueError("Value cannot be null")
        if v < 0 and cls.metric_type not in [
            MetricType.MOOD, MetricType.STRESS_LEVEL, MetricType.ANXIETY_LEVEL,
            MetricType.ENERGY_LEVEL, MetricType.FOCUS_LEVEL, MetricType.SLEEP_QUALITY
        ]:
            raise ValueError("Value cannot be negative for this metric type")
        return v
    
    @validator('metric_type')
    def validate_metric_type(cls, v):
        """Validate metric type"""
        try:
            MetricType(v)
        except ValueError:
            raise ValueError(f"Invalid metric type: {v}")
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        """Validate unit"""
        try:
            MetricUnit(v)
        except ValueError:
            raise ValueError(f"Invalid unit: {v}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        def safe_decode(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8')
                except Exception:
                    return str(val)
            elif isinstance(val, dict):
                return {k: safe_decode(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [safe_decode(v) for v in val]
            return val

        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "metric_type": safe_decode(self.metric_type),
            "value": self.value,
            "unit": safe_decode(self.unit),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": safe_decode(self.source),
            "notes": safe_decode(self.notes),
            "metric_metadata": safe_decode(self.metric_metadata),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthMetric':
        """Create from dictionary"""
        return cls(
            id=UUID(data.get("id")) if data.get("id") else None,
            user_id=UUID(data["user_id"]),
            metric_type=data["metric_type"],
            value=data["value"],
            unit=data["unit"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            source=data.get("source"),
            notes=data.get("notes"),
            metric_metadata=data.get("metadata")
        )

# Pydantic models for API
class HealthMetricCreate(BaseModel):
    """Create health metric request"""
    metric_type: MetricType = Field(..., description="Type of health metric")
    value: float = Field(..., description="Metric value")
    unit: MetricUnit = Field(..., description="Unit of measurement")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of measurement")
    source: Optional[str] = Field(None, description="Source of the metric")
    device_id: Optional[str] = Field(None, description="Device identifier")
    notes: Optional[str] = Field(None, description="Additional notes")
    metric_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthMetricUpdate(BaseModel):
    """Update health metric request"""
    value: Optional[float] = Field(None, description="Metric value")
    unit: Optional[MetricUnit] = Field(None, description="Unit of measurement")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of measurement")
    source: Optional[str] = Field(None, description="Source of the metric")
    device_id: Optional[str] = Field(None, description="Device identifier")
    notes: Optional[str] = Field(None, description="Additional notes")
    metric_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthMetricResponse(BaseModel):
    """Health metric response"""
    id: UUID = Field(..., description="Metric ID")
    user_id: UUID = Field(..., description="User ID")
    metric_type: MetricType = Field(..., description="Type of health metric")
    value: float = Field(..., description="Metric value")
    unit: MetricUnit = Field(..., description="Unit of measurement")
    timestamp: datetime = Field(..., description="Timestamp of measurement")
    source: Optional[str] = Field(None, description="Source of the metric")
    device_id: Optional[str] = Field(None, description="Device identifier")
    notes: Optional[str] = Field(None, description="Additional notes")
    metric_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
        from_attributes = True

class HealthMetricFilter(BaseModel):
    """Health metric filter model"""
    metric_type: Optional[MetricType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0) 