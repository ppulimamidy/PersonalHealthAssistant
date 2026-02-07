"""
Device Data Point Model
Handles storage and management of health data points from devices.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, List
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer, Enum as SQLEnum, Numeric, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from pydantic import BaseModel, Field, validator

from common.models.base import Base


class DataType(str, Enum):
    """Types of health data that can be collected"""
    # Cardiovascular
    HEART_RATE = "heart_rate"
    HEART_RATE_VARIABILITY = "heart_rate_variability"
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    BLOOD_PRESSURE_MEAN = "blood_pressure_mean"
    BLOOD_PRESSURE_PULSE = "blood_pressure_pulse"
    ECG_DATA = "ecg_data"
    CARDIAC_OUTPUT = "cardiac_output"
    STROKE_VOLUME = "stroke_volume"
    
    # Metabolic
    BLOOD_GLUCOSE = "blood_glucose"
    CONTINUOUS_GLUCOSE = "continuous_glucose"
    INSULIN_LEVEL = "insulin_level"
    HBA1C = "hba1c"
    CHOLESTEROL_TOTAL = "cholesterol_total"
    CHOLESTEROL_HDL = "cholesterol_hdl"
    CHOLESTEROL_LDL = "cholesterol_ldl"
    TRIGLYCERIDES = "triglycerides"
    KETONES = "ketones"
    LACTATE = "lactate"
    
    # Dexcom CGM Specific
    GLUCOSE_CALIBRATION = "glucose_calibration"
    INSULIN_EVENT = "insulin_event"
    CARB_EVENT = "carb_event"
    GLUCOSE_ALERT = "glucose_alert"
    GLUCOSE_TREND = "glucose_trend"
    SENSOR_STATUS = "sensor_status"
    TRANSMITTER_STATUS = "transmitter_status"
    TIME_IN_RANGE = "time_in_range"
    
    # Body Composition
    BODY_TEMPERATURE = "body_temperature"
    BODY_WEIGHT = "body_weight"
    BODY_FAT_PERCENTAGE = "body_fat_percentage"
    BODY_MASS_INDEX = "body_mass_index"
    MUSCLE_MASS = "muscle_mass"
    BONE_MASS = "bone_mass"
    WATER_PERCENTAGE = "water_percentage"
    VISCERAL_FAT = "visceral_fat"
    LEAN_MASS = "lean_mass"
    BODY_COMPOSITION = "body_composition"
    
    # Respiratory
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    LUNG_CAPACITY = "lung_capacity"
    PEAK_FLOW = "peak_flow"
    BREATHING_PATTERN = "breathing_pattern"
    
    # Sleep
    SLEEP_DURATION = "sleep_duration"
    SLEEP_EFFICIENCY = "sleep_efficiency"
    SLEEP_STAGES = "sleep_stages"
    SLEEP_LATENCY = "sleep_latency"
    SLEEP_WAKE_TIME = "sleep_wake_time"
    SLEEP_QUALITY = "sleep_quality"
    SLEEP_SCORE = "sleep_score"
    REM_SLEEP = "rem_sleep"
    DEEP_SLEEP = "deep_sleep"
    LIGHT_SLEEP = "light_sleep"
    
    # Activity & Fitness
    STEPS_COUNT = "steps_count"
    CALORIES_BURNED = "calories_burned"
    DISTANCE_WALKED = "distance_walked"
    ACTIVE_MINUTES = "active_minutes"
    EXERCISE_DURATION = "exercise_duration"
    EXERCISE_INTENSITY = "exercise_intensity"
    WORKOUT_TYPE = "workout_type"
    VO2_MAX = "vo2_max"
    ANAEROBIC_THRESHOLD = "anaerobic_threshold"
    RECOVERY_SCORE = "recovery_score"
    STRAIN_SCORE = "strain_score"
    READINESS_SCORE = "readiness_score"
    
    # Environmental
    SKIN_TEMPERATURE = "skin_temperature"
    AMBIENT_TEMPERATURE = "ambient_temperature"
    HUMIDITY = "humidity"
    AIR_QUALITY = "air_quality"
    UV_INDEX = "uv_index"
    ALTITUDE = "altitude"
    BAROMETRIC_PRESSURE = "barometric_pressure"
    NOISE_LEVEL = "noise_level"
    LIGHT_EXPOSURE = "light_exposure"
    RADIATION_EXPOSURE = "radiation_exposure"
    
    # Mental Health & Wellness
    STRESS_LEVEL = "stress_level"
    MOOD_SCORE = "mood_score"
    ENERGY_LEVEL = "energy_level"
    PAIN_LEVEL = "pain_level"
    FATIGUE_LEVEL = "fatigue_level"
    HUNGER_LEVEL = "hunger_level"
    THIRST_LEVEL = "thirst_level"
    ANXIETY_SCORE = "anxiety_score"
    DEPRESSION_SCORE = "depression_score"
    MINDFULNESS_SCORE = "mindfulness_score"
    MEDITATION_DURATION = "meditation_duration"
    
    # Reproductive Health
    FERTILITY_SCORE = "fertility_score"
    OVULATION_PREDICTION = "ovulation_prediction"
    MENSTRUAL_CYCLE = "menstrual_cycle"
    PREGNANCY_WEEKS = "pregnancy_weeks"
    FETAL_HEART_RATE = "fetal_heart_rate"
    CONTRACTION_FREQUENCY = "contraction_frequency"
    
    # Urine Analysis
    URINE_PH = "urine_ph"
    URINE_SPECIFIC_GRAVITY = "urine_specific_gravity"
    URINE_GLUCOSE = "urine_glucose"
    URINE_KETONES = "urine_ketones"
    URINE_PROTEIN = "urine_protein"
    URINE_BLOOD = "urine_blood"
    URINE_NITRITE = "urine_nitrite"
    URINE_LEUKOCYTES = "urine_leukocytes"
    URINE_BILIRUBIN = "urine_bilirubin"
    URINE_UROBILINOGEN = "urine_urobilinogen"
    
    # Neurological
    BRAIN_ACTIVITY = "brain_activity"
    EEG_DATA = "eeg_data"
    COGNITIVE_PERFORMANCE = "cognitive_performance"
    REACTION_TIME = "reaction_time"
    MEMORY_SCORE = "memory_score"
    ATTENTION_SCORE = "attention_score"
    
    # Gastrointestinal
    DIGESTIVE_HEALTH = "digestive_health"
    STOOL_FREQUENCY = "stool_frequency"
    STOOL_CONSISTENCY = "stool_consistency"
    BLOATING_LEVEL = "bloating_level"
    NAUSEA_LEVEL = "nausea_level"
    
    # Musculoskeletal
    MUSCLE_ACTIVITY = "muscle_activity"
    JOINT_MOBILITY = "joint_mobility"
    POSTURE_SCORE = "posture_score"
    BALANCE_SCORE = "balance_score"
    FLEXIBILITY_SCORE = "flexibility_score"
    STRENGTH_SCORE = "strength_score"
    
    # Sensory
    VISION_ACUITY = "vision_acuity"
    HEARING_LEVEL = "hearing_level"
    TASTE_SENSITIVITY = "taste_sensitivity"
    SMELL_SENSITIVITY = "smell_sensitivity"
    TOUCH_SENSITIVITY = "touch_sensitivity"
    
    # Social & Behavioral
    SOCIAL_INTERACTIONS = "social_interactions"
    SCREEN_TIME = "screen_time"
    PHONE_USAGE = "phone_usage"
    LOCATION_DATA = "location_data"
    ACTIVITY_PATTERNS = "activity_patterns"
    
    # Medication & Treatment
    MEDICATION_ADHERENCE = "medication_adherence"
    TREATMENT_EFFECTIVENESS = "treatment_effectiveness"
    SIDE_EFFECTS = "side_effects"
    THERAPY_SESSIONS = "therapy_sessions"
    
    # Vital Signs (Comprehensive)
    BLOOD_ALCOHOL = "blood_alcohol"
    BLOOD_ALCOHOL_CONTENT = "blood_alcohol_content"
    BLOOD_TYPE = "blood_type"
    BLOOD_VOLUME = "blood_volume"
    BLOOD_FLOW = "blood_flow"
    
    # Calculated & Derived
    METABOLIC_AGE = "metabolic_age"
    BIOLOGICAL_AGE = "biological_age"
    HEALTH_SCORE = "health_score"
    WELLNESS_SCORE = "wellness_score"
    LONGEVITY_SCORE = "longevity_score"
    
    # Custom & Other
    CUSTOM_METRIC = "custom_metric"
    OTHER = "other"


class DataQuality(str, Enum):
    """Data quality indicators"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class DataSource(str, Enum):
    """Data source types"""
    DEVICE_SYNC = "device_sync"
    MANUAL_ENTRY = "manual_entry"
    API_IMPORT = "api_import"
    BATCH_UPLOAD = "batch_upload"
    REAL_TIME_STREAM = "real_time_stream"
    CALCULATED = "calculated"
    INFERRED = "inferred"


class DeviceDataPoint(Base):
    """Device data point model for health data storage"""
    __tablename__ = "device_data_points"
    __table_args__ = (
        Index('idx_device_data_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_device_data_device_timestamp', 'device_id', 'timestamp'),
        Index('idx_device_data_type_timestamp', 'data_type', 'timestamp'),
        Index('idx_device_data_quality', 'quality'),
        Index('idx_device_data_anomaly', 'is_anomaly'),
        {"schema": "device_data"}
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relationships
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    device_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Data identification
    data_type: Mapped[DataType] = mapped_column(SQLEnum(DataType), nullable=False)
    source: Mapped[DataSource] = mapped_column(SQLEnum(DataSource), default=DataSource.DEVICE_SYNC)
    
    # Data values
    value: Mapped[Union[float, int, str]] = mapped_column(Numeric(10, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Data quality and validation
    quality: Mapped[DataQuality] = mapped_column(SQLEnum(DataQuality), default=DataQuality.UNKNOWN)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validation_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    data_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    
    # Processing flags
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anomaly: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    anomaly_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    
    # Relationships
    # device = relationship("Device", back_populates="data_points")  # Temporarily disabled due to foreign key constraints
    
    def __repr__(self):
        return f"<DeviceDataPoint(id={self.id}, type='{self.data_type}', value={self.value}, timestamp='{self.timestamp}')>"


# Pydantic Models for API
class DataPointBase(BaseModel):
    """Base data point model for API requests/responses"""
    data_type: DataType = Field(..., description="Type of health data")
    value: Union[float, int, str] = Field(..., description="Data value")
    unit: str = Field(..., min_length=1, max_length=50, description="Unit of measurement")
    timestamp: datetime = Field(..., description="When the data was recorded")
    source: DataSource = Field(default=DataSource.DEVICE_SYNC, description="Data source")
    quality: DataQuality = Field(default=DataQuality.UNKNOWN, description="Data quality")
    raw_value: Optional[str] = Field(None, description="Raw data value from device")
    data_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: list = Field(default_factory=list, description="Data tags")
    
    @validator('value')
    def validate_value(cls, v):
        if isinstance(v, (int, float)) and (v < -1000000 or v > 1000000):
            raise ValueError('Value must be between -1,000,000 and 1,000,000')
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        # Allow future timestamps for development/sandbox mode
        # In production, this should be more strict
        if v > datetime.utcnow() + timedelta(days=1):  # Allow up to 1 day in future
            raise ValueError('Timestamp cannot be more than 1 day in the future')
        return v


class DataPointCreate(DataPointBase):
    """Model for creating a new data point"""
    device_id: UUID = Field(..., description="Device ID that generated this data")


class DataPointUpdate(BaseModel):
    """Model for updating data point information"""
    value: Optional[Union[float, int, str]] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    timestamp: Optional[datetime] = None
    source: Optional[DataSource] = None
    quality: Optional[DataQuality] = None
    raw_value: Optional[str] = None
    data_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[list] = None
    is_validated: Optional[bool] = None
    validation_score: Optional[float] = Field(None, ge=0, le=1)
    is_processed: Optional[bool] = None
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = Field(None, ge=0, le=1)
    
    @validator('value')
    def validate_value(cls, v):
        if v is not None and isinstance(v, (int, float)) and (v < -1000000 or v > 1000000):
            raise ValueError('Value must be between -1,000,000 and 1,000,000')
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is not None and v > datetime.utcnow():
            raise ValueError('Timestamp cannot be in the future')
        return v


class DataPointResponse(DataPointBase):
    """Model for data point API responses"""
    id: UUID
    user_id: UUID
    device_id: UUID
    is_validated: bool
    validation_score: Optional[float]
    is_processed: bool
    is_anomaly: Optional[bool]
    anomaly_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DataPointSummary(BaseModel):
    """Simplified data point model for lists and summaries"""
    id: UUID
    data_type: DataType
    value: Union[float, int, str]
    unit: str
    timestamp: datetime
    quality: DataQuality
    is_anomaly: Optional[bool]
    anomaly_score: Optional[float]
    
    class Config:
        from_attributes = True


class DataPointBatch(BaseModel):
    """Model for batch data point operations"""
    device_id: UUID = Field(..., description="Device ID")
    data_points: List[DataPointBase] = Field(..., min_items=1, max_items=1000, description="List of data points")
    
    @validator('data_points')
    def validate_data_points(cls, v):
        if len(v) > 1000:
            raise ValueError('Maximum 1000 data points per batch')
        return v


class DataPointQuery(BaseModel):
    """Model for querying data points"""
    device_id: Optional[UUID] = Field(None, description="Filter by device ID")
    data_type: Optional[DataType] = Field(None, description="Filter by data type")
    start_date: Optional[datetime] = Field(None, description="Start date for data range")
    end_date: Optional[datetime] = Field(None, description="End date for data range")
    quality: Optional[DataQuality] = Field(None, description="Filter by data quality")
    is_anomaly: Optional[bool] = Field(None, description="Filter by anomaly status")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    @validator('start_date', 'end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'start_date' in values and 'end_date' in values:
            if values['start_date'] and values['end_date'] and values['start_date'] > values['end_date']:
                raise ValueError('Start date must be before end date')
        return v


class DataPointAggregation(BaseModel):
    """Model for data point aggregation results"""
    data_type: DataType
    unit: str
    count: int
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    median_value: Optional[float]
    std_deviation: Optional[float]
    start_date: datetime
    end_date: datetime
    aggregation_period: str = Field(..., description="Aggregation period (hour, day, week, month)")
    
    class Config:
        from_attributes = True


class DataPointStatistics(BaseModel):
    """Model for data point statistics"""
    total_points: int
    valid_points: int
    anomaly_points: int
    data_types: Dict[str, int] = Field(..., description="Count by data type")
    quality_distribution: Dict[str, int] = Field(..., description="Count by quality level")
    date_range: Dict[str, datetime] = Field(..., description="Start and end dates")
    device_count: int = Field(..., description="Number of devices with data")
    
    class Config:
        from_attributes = True 