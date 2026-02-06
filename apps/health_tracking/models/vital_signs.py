"""
Vital Signs Models
Models for tracking vital signs and physiological measurements.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator, EmailStr

from common.models.base import Base, BaseModel as CommonBaseModel

class VitalSignType(Enum):
    """Types of vital signs"""
    BLOOD_PRESSURE = "blood_pressure"
    HEART_RATE = "heart_rate"
    BODY_TEMPERATURE = "body_temperature"
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    BLOOD_GLUCOSE = "blood_glucose"
    WEIGHT = "weight"
    HEIGHT = "height"
    BODY_MASS_INDEX = "body_mass_index"
    WAIST_CIRCUMFERENCE = "waist_circumference"
    BODY_FAT_PERCENTAGE = "body_fat_percentage"
    MUSCLE_MASS = "muscle_mass"
    BONE_DENSITY = "bone_density"
    SKIN_TEMPERATURE = "skin_temperature"
    BLOOD_ALCOHOL_CONTENT = "blood_alcohol_content"
    CARBON_MONOXIDE = "carbon_monoxide"
    LUNG_CAPACITY = "lung_capacity"
    EYE_PRESSURE = "eye_pressure"
    HEARING_LEVEL = "hearing_level"

class VitalSignUnit(Enum):
    """Units for vital signs measurements"""
    # Blood Pressure
    MMHG = "mmHg"
    
    # Heart Rate
    BPM = "bpm"
    
    # Temperature
    CELSIUS = "°C"
    FAHRENHEIT = "°F"
    
    # Oxygen Saturation
    PERCENTAGE = "%"
    
    # Respiratory Rate
    BREATHS_PER_MINUTE = "breaths/min"
    
    # Blood Glucose
    MG_DL = "mg/dL"
    MMOL_L = "mmol/L"
    
    # Weight and Mass
    KG = "kg"
    LBS = "lbs"
    
    # Height
    CM = "cm"
    INCHES = "inches"
    FEET = "feet"
    
    # Body Composition
    PERCENT = "%"
    
    # Other
    PPM = "ppm"  # Parts per million
    DB = "dB"    # Decibels
    ML = "mL"    # Milliliters

class MeasurementMethod(Enum):
    """Method used for measurement"""
    MANUAL = "manual"
    DIGITAL_DEVICE = "digital_device"
    WEARABLE_DEVICE = "wearable_device"
    MEDICAL_DEVICE = "medical_device"
    LAB_TEST = "lab_test"
    ESTIMATED = "estimated"
    CALCULATED = "calculated"

class VitalSigns(Base):
    """Vital signs database model"""
    __tablename__ = "vital_signs"
    __table_args__ = (
        Index('idx_vital_signs_user_created', 'user_id', 'created_at'),
        Index('idx_vital_signs_type_created', 'vital_sign_type', 'created_at'),
        CheckConstraint('systolic >= 0', name='check_systolic_positive'),
        CheckConstraint('diastolic >= 0', name='check_diastolic_positive'),
        CheckConstraint('heart_rate >= 0', name='check_heart_rate_positive'),
        CheckConstraint('temperature >= 0', name='check_temperature_positive'),
        CheckConstraint('oxygen_saturation >= 0 AND oxygen_saturation <= 100', name='check_oxygen_range'),
        CheckConstraint('respiratory_rate >= 0', name='check_respiratory_rate_positive'),
        CheckConstraint('blood_glucose >= 0', name='check_blood_glucose_positive'),
        CheckConstraint('weight >= 0', name='check_weight_positive'),
        CheckConstraint('height >= 0', name='check_height_positive'),
        CheckConstraint('bmi >= 0', name='check_bmi_positive'),
        CheckConstraint('waist_circumference >= 0', name='check_waist_positive'),
        CheckConstraint('body_fat_percentage >= 0 AND body_fat_percentage <= 100', name='check_body_fat_range'),
        CheckConstraint('muscle_mass >= 0', name='check_muscle_mass_positive'),
        CheckConstraint('bone_density >= 0', name='check_bone_density_positive'),
        CheckConstraint('skin_temperature >= 0', name='check_skin_temp_positive'),
        CheckConstraint('blood_alcohol_content >= 0 AND blood_alcohol_content <= 1', name='check_bac_range'),
        CheckConstraint('carbon_monoxide >= 0', name='check_co_positive'),
        CheckConstraint('lung_capacity >= 0', name='check_lung_capacity_positive'),
        CheckConstraint('eye_pressure >= 0', name='check_eye_pressure_positive'),
        CheckConstraint('hearing_level >= 0', name='check_hearing_positive'),
        {'schema': 'health_tracking'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Store user ID without foreign key constraint
    
    # Vital sign type and measurement details
    vital_sign_type = Column(String(50), nullable=False)
    measurement_method = Column(String(50), nullable=False)
    measurement_location = Column(String(100))  # e.g., "left arm", "forehead", "finger"
    
    # Blood pressure specific fields
    systolic = Column(Float)  # mmHg
    diastolic = Column(Float)  # mmHg
    mean_arterial_pressure = Column(Float)  # mmHg
    
    # Heart rate specific fields
    heart_rate = Column(Float)  # bpm
    heart_rate_variability = Column(Float)  # ms
    irregular_heartbeat_detected = Column(String(10))  # "yes", "no", "unknown"
    
    # Temperature specific fields
    temperature = Column(Float)  # Celsius
    temperature_method = Column(String(50))  # "oral", "rectal", "axillary", "temporal", "tympanic"
    
    # Oxygen saturation specific fields
    oxygen_saturation = Column(Float)  # percentage
    perfusion_index = Column(Float)  # percentage
    
    # Respiratory rate specific fields
    respiratory_rate = Column(Float)  # breaths per minute
    respiratory_pattern = Column(String(50))  # "normal", "rapid", "slow", "irregular"
    
    # Blood glucose specific fields
    blood_glucose = Column(Float)  # mg/dL or mmol/L
    glucose_unit = Column(String(10))  # "mg/dL" or "mmol/L"
    glucose_context = Column(String(50))  # "fasting", "postprandial", "random"
    
    # Body composition fields
    weight = Column(Float)  # kg
    height = Column(Float)  # cm
    bmi = Column(Float)  # kg/m²
    waist_circumference = Column(Float)  # cm
    body_fat_percentage = Column(Float)  # percentage
    muscle_mass = Column(Float)  # kg
    bone_density = Column(Float)  # g/cm³
    
    # Other vital signs
    skin_temperature = Column(Float)  # Celsius
    blood_alcohol_content = Column(Float)  # percentage (0.0-1.0)
    carbon_monoxide = Column(Float)  # ppm
    lung_capacity = Column(Float)  # mL
    eye_pressure = Column(Float)  # mmHg
    hearing_level = Column(Float)  # dB
    
    # Metadata
    device_id = Column(String(100))  # ID of the device used for measurement
    device_model = Column(String(100))  # Model of the device
    measurement_notes = Column(Text)  # Additional notes about the measurement
    measurement_quality = Column(String(20))  # "excellent", "good", "fair", "poor"
    measurement_duration = Column(Float)  # seconds
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    vital_sign_metadata = Column(JSONB, default=dict)
    
    # Note: No relationship to User table to avoid cross-schema foreign key issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "vital_sign_type": self.vital_sign_type,
            "measurement_method": self.measurement_method,
            "measurement_location": self.measurement_location,
            "systolic": self.systolic,
            "diastolic": self.diastolic,
            "mean_arterial_pressure": self.mean_arterial_pressure,
            "heart_rate": self.heart_rate,
            "heart_rate_variability": self.heart_rate_variability,
            "irregular_heartbeat_detected": self.irregular_heartbeat_detected,
            "temperature": self.temperature,
            "temperature_method": self.temperature_method,
            "oxygen_saturation": self.oxygen_saturation,
            "perfusion_index": self.perfusion_index,
            "respiratory_rate": self.respiratory_rate,
            "respiratory_pattern": self.respiratory_pattern,
            "blood_glucose": self.blood_glucose,
            "glucose_unit": self.glucose_unit,
            "glucose_context": self.glucose_context,
            "weight": self.weight,
            "height": self.height,
            "bmi": self.bmi,
            "waist_circumference": self.waist_circumference,
            "body_fat_percentage": self.body_fat_percentage,
            "muscle_mass": self.muscle_mass,
            "bone_density": self.bone_density,
            "skin_temperature": self.skin_temperature,
            "blood_alcohol_content": self.blood_alcohol_content,
            "carbon_monoxide": self.carbon_monoxide,
            "lung_capacity": self.lung_capacity,
            "eye_pressure": self.eye_pressure,
            "hearing_level": self.hearing_level,
            "device_id": self.device_id,
            "device_model": self.device_model,
            "measurement_notes": self.measurement_notes,
            "measurement_quality": self.measurement_quality,
            "measurement_duration": self.measurement_duration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "vital_sign_metadata": self.vital_sign_metadata
        }

# Pydantic Models for API
class VitalSignsBase(CommonBaseModel):
    """Base vital signs model"""
    vital_sign_type: VitalSignType
    measurement_method: MeasurementMethod
    measurement_location: Optional[str] = Field(None, max_length=100)
    device_id: Optional[str] = Field(None, max_length=100)
    device_model: Optional[str] = Field(None, max_length=100)
    measurement_notes: Optional[str] = Field(None, max_length=1000)
    measurement_quality: Optional[str] = Field(None, pattern="^(excellent|good|fair|poor)$")
    measurement_duration: Optional[float] = Field(None, ge=0)
    vital_sign_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class BloodPressureCreate(VitalSignsBase):
    """Blood pressure creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.BLOOD_PRESSURE)
    systolic: float = Field(..., ge=0, le=300, description="Systolic blood pressure in mmHg")
    diastolic: float = Field(..., ge=0, le=200, description="Diastolic blood pressure in mmHg")
    mean_arterial_pressure: Optional[float] = Field(None, ge=0, description="Mean arterial pressure in mmHg")
    
    @validator('diastolic')
    def diastolic_less_than_systolic(cls, v, values):
        if 'systolic' in values and v >= values['systolic']:
            raise ValueError('Diastolic must be less than systolic')
        return v

class HeartRateCreate(VitalSignsBase):
    """Heart rate creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.HEART_RATE)
    heart_rate: float = Field(..., ge=0, le=300, description="Heart rate in bpm")
    heart_rate_variability: Optional[float] = Field(None, ge=0, description="Heart rate variability in ms")
    irregular_heartbeat_detected: Optional[str] = Field(None, pattern="^(yes|no|unknown)$")

class TemperatureCreate(VitalSignsBase):
    """Body temperature creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.BODY_TEMPERATURE)
    temperature: float = Field(..., ge=20, le=50, description="Body temperature in Celsius")
    temperature_method: Optional[str] = Field(None, pattern="^(oral|rectal|axillary|temporal|tympanic)$")

class OxygenSaturationCreate(VitalSignsBase):
    """Oxygen saturation creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.OXYGEN_SATURATION)
    oxygen_saturation: float = Field(..., ge=0, le=100, description="Oxygen saturation percentage")
    perfusion_index: Optional[float] = Field(None, ge=0, le=100, description="Perfusion index percentage")

class RespiratoryRateCreate(VitalSignsBase):
    """Respiratory rate creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.RESPIRATORY_RATE)
    respiratory_rate: float = Field(..., ge=0, le=100, description="Respiratory rate in breaths per minute")
    respiratory_pattern: Optional[str] = Field(None, pattern="^(normal|rapid|slow|irregular)$")

class BloodGlucoseCreate(VitalSignsBase):
    """Blood glucose creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.BLOOD_GLUCOSE)
    blood_glucose: float = Field(..., ge=0, le=1000, description="Blood glucose level")
    glucose_unit: str = Field(..., pattern="^(mg/dL|mmol/L)$")
    glucose_context: Optional[str] = Field(None, pattern="^(fasting|postprandial|random)$")

class BodyCompositionCreate(VitalSignsBase):
    """Body composition creation model"""
    vital_sign_type: VitalSignType = Field(default=VitalSignType.WEIGHT)
    weight: Optional[float] = Field(None, ge=0, le=500, description="Weight in kg")
    height: Optional[float] = Field(None, ge=0, le=300, description="Height in cm")
    bmi: Optional[float] = Field(None, ge=0, le=100, description="BMI in kg/m²")
    waist_circumference: Optional[float] = Field(None, ge=0, le=200, description="Waist circumference in cm")
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100, description="Body fat percentage")
    muscle_mass: Optional[float] = Field(None, ge=0, le=200, description="Muscle mass in kg")
    bone_density: Optional[float] = Field(None, ge=0, le=10, description="Bone density in g/cm³")

class VitalSignsResponse(CommonBaseModel):
    """Vital signs response model"""
    id: str
    user_id: str
    vital_sign_type: str
    measurement_method: str
    measurement_location: Optional[str]
    systolic: Optional[float]
    diastolic: Optional[float]
    mean_arterial_pressure: Optional[float]
    heart_rate: Optional[float]
    heart_rate_variability: Optional[float]
    irregular_heartbeat_detected: Optional[str]
    temperature: Optional[float]
    temperature_method: Optional[str]
    oxygen_saturation: Optional[float]
    perfusion_index: Optional[float]
    respiratory_rate: Optional[float]
    respiratory_pattern: Optional[str]
    blood_glucose: Optional[float]
    glucose_unit: Optional[str]
    glucose_context: Optional[str]
    weight: Optional[float]
    height: Optional[float]
    bmi: Optional[float]
    waist_circumference: Optional[float]
    body_fat_percentage: Optional[float]
    muscle_mass: Optional[float]
    bone_density: Optional[float]
    skin_temperature: Optional[float]
    blood_alcohol_content: Optional[float]
    carbon_monoxide: Optional[float]
    lung_capacity: Optional[float]
    eye_pressure: Optional[float]
    hearing_level: Optional[float]
    device_id: Optional[str]
    device_model: Optional[str]
    measurement_notes: Optional[str]
    measurement_quality: Optional[str]
    measurement_duration: Optional[float]
    created_at: str
    updated_at: str
    vital_sign_metadata: Dict[str, Any]

    class Config:
        from_attributes = True

class VitalSignsFilter(CommonBaseModel):
    """Vital signs filter model"""
    vital_sign_type: Optional[VitalSignType] = None
    measurement_method: Optional[MeasurementMethod] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    device_id: Optional[str] = None
    measurement_quality: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0) 