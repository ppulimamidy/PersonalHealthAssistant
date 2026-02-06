"""
Health Attributes Models

This module contains health attribute models including:
- HealthAttributes: Health-related profile information
- HealthAttributesCreate: Schema for creating health attributes
- HealthAttributesUpdate: Schema for updating health attributes
"""

from datetime import datetime
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.models.base import Base
from common.models.relationships import safe_relationship


class HealthGoal(str, Enum):
    """Health goal types"""
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MAINTENANCE = "maintenance"
    MUSCLE_GAIN = "muscle_gain"
    CARDIOVASCULAR_HEALTH = "cardiovascular_health"
    DIABETES_MANAGEMENT = "diabetes_management"
    BLOOD_PRESSURE_CONTROL = "blood_pressure_control"
    SLEEP_IMPROVEMENT = "sleep_improvement"
    STRESS_REDUCTION = "stress_reduction"
    GENERAL_WELLNESS = "general_wellness"


class ActivityGoal(str, Enum):
    """Activity goal types"""
    STEPS_PER_DAY = "steps_per_day"
    ACTIVE_MINUTES = "active_minutes"
    WORKOUTS_PER_WEEK = "workouts_per_week"
    CARDIO_MINUTES = "cardio_minutes"
    STRENGTH_TRAINING = "strength_training"
    FLEXIBILITY = "flexibility"


class RiskLevel(str, Enum):
    """Health risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class HealthAttributes(Base):
    """Health attributes model"""
    __tablename__ = "health_attributes"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False, index=True)
    
    # Physical Measurements
    height_cm = Column(Integer)  # Height in centimeters
    weight_kg = Column(Float)  # Weight in kilograms
    bmi = Column(Float)  # Calculated BMI
    body_fat_percentage = Column(Float)  # Body fat percentage
    muscle_mass_kg = Column(Float)  # Muscle mass in kilograms
    waist_circumference_cm = Column(Float)  # Waist circumference
    hip_circumference_cm = Column(Float)  # Hip circumference
    body_water_percentage = Column(Float)  # Body water percentage
    
    # Vital Signs (Baseline)
    resting_heart_rate = Column(Integer)  # Resting heart rate (BPM)
    blood_pressure_systolic = Column(Integer)  # Systolic blood pressure
    blood_pressure_diastolic = Column(Integer)  # Diastolic blood pressure
    oxygen_saturation = Column(Float)  # Blood oxygen saturation (%)
    body_temperature = Column(Float)  # Body temperature (°C)
    
    # Health Goals
    primary_health_goal = Column(String(50))  # Primary health goal
    secondary_health_goals = Column(JSON)  # List of secondary goals
    target_weight_kg = Column(Float)  # Target weight
    target_bmi = Column(Float)  # Target BMI
    target_resting_heart_rate = Column(Integer)  # Target resting heart rate
    target_blood_pressure_systolic = Column(Integer)  # Target systolic BP
    target_blood_pressure_diastolic = Column(Integer)  # Target diastolic BP
    
    # Activity Goals
    daily_step_goal = Column(Integer, default=10000)  # Daily step goal
    weekly_workout_goal = Column(Integer, default=3)  # Weekly workout goal
    daily_active_minutes_goal = Column(Integer, default=30)  # Daily active minutes
    weekly_cardio_minutes_goal = Column(Integer, default=150)  # Weekly cardio minutes
    
    # Risk Factors
    smoking_status = Column(Boolean, default=False)  # Current smoker
    alcohol_consumption = Column(String(20))  # Alcohol consumption level
    family_history_diabetes = Column(Boolean, default=False)
    family_history_heart_disease = Column(Boolean, default=False)
    family_history_cancer = Column(Boolean, default=False)
    family_history_hypertension = Column(Boolean, default=False)
    
    # Health Conditions
    has_diabetes = Column(Boolean, default=False)
    has_hypertension = Column(Boolean, default=False)
    has_heart_disease = Column(Boolean, default=False)
    has_asthma = Column(Boolean, default=False)
    has_arthritis = Column(Boolean, default=False)
    has_depression = Column(Boolean, default=False)
    has_anxiety = Column(Boolean, default=False)
    has_sleep_apnea = Column(Boolean, default=False)
    
    # Lifestyle Factors
    sleep_hours_per_night = Column(Float)  # Average sleep hours
    stress_level = Column(String(20))  # Stress level assessment
    diet_type = Column(String(50))  # Diet type (vegetarian, keto, etc.)
    exercise_frequency = Column(String(20))  # Exercise frequency
    sedentary_hours_per_day = Column(Float)  # Sedentary hours per day
    
    # Health Metrics
    overall_health_score = Column(Integer)  # Calculated health score (0-100)
    cardiovascular_risk_score = Column(Integer)  # Cardiovascular risk score
    diabetes_risk_score = Column(Integer)  # Diabetes risk score
    obesity_risk_score = Column(Integer)  # Obesity risk score
    
    # Custom Health Data
    custom_health_data = Column(JSON, default=dict)  # Custom health metrics
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - using robust relationship system
    user = safe_relationship("User", back_populates="health_attributes")
    profile = safe_relationship("UserProfile", back_populates="health_attributes")


# Pydantic Models for API
class HealthAttributesBase(BaseModel):
    """Base health attributes schema"""
    # Physical Measurements
    height_cm: Optional[int] = Field(None, ge=50, le=300, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=20, le=500, description="Weight in kilograms")
    bmi: Optional[float] = Field(None, ge=10, le=100, description="Body Mass Index")
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100, description="Body fat percentage")
    muscle_mass_kg: Optional[float] = Field(None, ge=0, le=200, description="Muscle mass in kilograms")
    waist_circumference_cm: Optional[float] = Field(None, ge=30, le=200, description="Waist circumference")
    hip_circumference_cm: Optional[float] = Field(None, ge=30, le=200, description="Hip circumference")
    body_water_percentage: Optional[float] = Field(None, ge=0, le=100, description="Body water percentage")
    
    # Vital Signs
    resting_heart_rate: Optional[int] = Field(None, ge=30, le=200, description="Resting heart rate (BPM)")
    blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=300, description="Systolic blood pressure")
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=200, description="Diastolic blood pressure")
    oxygen_saturation: Optional[float] = Field(None, ge=70, le=100, description="Blood oxygen saturation (%)")
    body_temperature: Optional[float] = Field(None, ge=30, le=45, description="Body temperature (°C)")
    
    # Health Goals
    primary_health_goal: Optional[HealthGoal] = Field(None, description="Primary health goal")
    secondary_health_goals: Optional[List[HealthGoal]] = Field(default_factory=list, description="Secondary health goals")
    target_weight_kg: Optional[float] = Field(None, ge=20, le=500, description="Target weight")
    target_bmi: Optional[float] = Field(None, ge=10, le=100, description="Target BMI")
    target_resting_heart_rate: Optional[int] = Field(None, ge=30, le=200, description="Target resting heart rate")
    target_blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=300, description="Target systolic BP")
    target_blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=200, description="Target diastolic BP")
    
    # Activity Goals
    daily_step_goal: Optional[int] = Field(None, ge=1000, le=50000, description="Daily step goal")
    weekly_workout_goal: Optional[int] = Field(None, ge=0, le=7, description="Weekly workout goal")
    daily_active_minutes_goal: Optional[int] = Field(None, ge=0, le=300, description="Daily active minutes goal")
    weekly_cardio_minutes_goal: Optional[int] = Field(None, ge=0, le=1000, description="Weekly cardio minutes goal")
    
    # Risk Factors
    smoking_status: Optional[bool] = Field(False, description="Current smoker")
    alcohol_consumption: Optional[str] = Field(None, description="Alcohol consumption level")
    family_history_diabetes: Optional[bool] = Field(False, description="Family history of diabetes")
    family_history_heart_disease: Optional[bool] = Field(False, description="Family history of heart disease")
    family_history_cancer: Optional[bool] = Field(False, description="Family history of cancer")
    family_history_hypertension: Optional[bool] = Field(False, description="Family history of hypertension")
    
    # Health Conditions
    has_diabetes: Optional[bool] = Field(False, description="Has diabetes")
    has_hypertension: Optional[bool] = Field(False, description="Has hypertension")
    has_heart_disease: Optional[bool] = Field(False, description="Has heart disease")
    has_asthma: Optional[bool] = Field(False, description="Has asthma")
    has_arthritis: Optional[bool] = Field(False, description="Has arthritis")
    has_depression: Optional[bool] = Field(False, description="Has depression")
    has_anxiety: Optional[bool] = Field(False, description="Has anxiety")
    has_sleep_apnea: Optional[bool] = Field(False, description="Has sleep apnea")
    
    # Lifestyle Factors
    sleep_hours_per_night: Optional[float] = Field(None, ge=0, le=24, description="Average sleep hours per night")
    stress_level: Optional[str] = Field(None, description="Stress level assessment")
    diet_type: Optional[str] = Field(None, description="Diet type")
    exercise_frequency: Optional[str] = Field(None, description="Exercise frequency")
    sedentary_hours_per_day: Optional[float] = Field(None, ge=0, le=24, description="Sedentary hours per day")
    
    # Health Metrics
    overall_health_score: Optional[int] = Field(None, ge=0, le=100, description="Overall health score")
    cardiovascular_risk_score: Optional[int] = Field(None, ge=0, le=100, description="Cardiovascular risk score")
    diabetes_risk_score: Optional[int] = Field(None, ge=0, le=100, description="Diabetes risk score")
    obesity_risk_score: Optional[int] = Field(None, ge=0, le=100, description="Obesity risk score")
    
    # Custom Health Data
    custom_health_data: Optional[dict] = Field(default_factory=dict, description="Custom health metrics")

    @validator('bmi')
    def validate_bmi(cls, v):
        """Validate BMI range"""
        if v and (v < 10 or v > 100):
            raise ValueError('BMI must be between 10 and 100')
        return v

    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        """Validate body fat percentage"""
        if v and (v < 0 or v > 100):
            raise ValueError('Body fat percentage must be between 0 and 100')
        return v

    @validator('resting_heart_rate')
    def validate_heart_rate(cls, v):
        """Validate resting heart rate"""
        if v and (v < 30 or v > 200):
            raise ValueError('Resting heart rate must be between 30 and 200 BPM')
        return v

    @validator('blood_pressure_systolic')
    def validate_systolic_bp(cls, v):
        """Validate systolic blood pressure"""
        if v and (v < 70 or v > 300):
            raise ValueError('Systolic blood pressure must be between 70 and 300 mmHg')
        return v

    @validator('blood_pressure_diastolic')
    def validate_diastolic_bp(cls, v):
        """Validate diastolic blood pressure"""
        if v and (v < 40 or v > 200):
            raise ValueError('Diastolic blood pressure must be between 40 and 200 mmHg')
        return v


class HealthAttributesCreate(HealthAttributesBase):
    """Schema for creating health attributes"""
    user_id: uuid.UUID = Field(..., description="Associated user ID")
    profile_id: int = Field(..., description="Associated profile ID")


class HealthAttributesUpdate(BaseModel):
    """Schema for updating health attributes (all fields optional)"""
    # Physical Measurements
    height_cm: Optional[int] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=20, le=500)
    bmi: Optional[float] = Field(None, ge=10, le=100)
    body_fat_percentage: Optional[float] = Field(None, ge=0, le=100)
    muscle_mass_kg: Optional[float] = Field(None, ge=0, le=200)
    waist_circumference_cm: Optional[float] = Field(None, ge=30, le=200)
    hip_circumference_cm: Optional[float] = Field(None, ge=30, le=200)
    body_water_percentage: Optional[float] = Field(None, ge=0, le=100)
    
    # Vital Signs
    resting_heart_rate: Optional[int] = Field(None, ge=30, le=200)
    blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=300)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=200)
    oxygen_saturation: Optional[float] = Field(None, ge=70, le=100)
    body_temperature: Optional[float] = Field(None, ge=30, le=45)
    
    # Health Goals
    primary_health_goal: Optional[HealthGoal] = None
    secondary_health_goals: Optional[List[HealthGoal]] = None
    target_weight_kg: Optional[float] = Field(None, ge=20, le=500)
    target_bmi: Optional[float] = Field(None, ge=10, le=100)
    target_resting_heart_rate: Optional[int] = Field(None, ge=30, le=200)
    target_blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=300)
    target_blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=200)
    
    # Activity Goals
    daily_step_goal: Optional[int] = Field(None, ge=1000, le=50000)
    weekly_workout_goal: Optional[int] = Field(None, ge=0, le=7)
    daily_active_minutes_goal: Optional[int] = Field(None, ge=0, le=300)
    weekly_cardio_minutes_goal: Optional[int] = Field(None, ge=0, le=1000)
    
    # Risk Factors
    smoking_status: Optional[bool] = None
    alcohol_consumption: Optional[str] = None
    family_history_diabetes: Optional[bool] = None
    family_history_heart_disease: Optional[bool] = None
    family_history_cancer: Optional[bool] = None
    family_history_hypertension: Optional[bool] = None
    
    # Health Conditions
    has_diabetes: Optional[bool] = None
    has_hypertension: Optional[bool] = None
    has_heart_disease: Optional[bool] = None
    has_asthma: Optional[bool] = None
    has_arthritis: Optional[bool] = None
    has_depression: Optional[bool] = None
    has_anxiety: Optional[bool] = None
    has_sleep_apnea: Optional[bool] = None
    
    # Lifestyle Factors
    sleep_hours_per_night: Optional[float] = Field(None, ge=0, le=24)
    stress_level: Optional[str] = None
    diet_type: Optional[str] = None
    exercise_frequency: Optional[str] = None
    sedentary_hours_per_day: Optional[float] = Field(None, ge=0, le=24)
    
    # Health Metrics
    overall_health_score: Optional[int] = Field(None, ge=0, le=100)
    cardiovascular_risk_score: Optional[int] = Field(None, ge=0, le=100)
    diabetes_risk_score: Optional[int] = Field(None, ge=0, le=100)
    obesity_risk_score: Optional[int] = Field(None, ge=0, le=100)
    
    # Custom Health Data
    custom_health_data: Optional[dict] = None

    @validator('bmi')
    def validate_bmi(cls, v):
        """Validate BMI range"""
        if v and (v < 10 or v > 100):
            raise ValueError('BMI must be between 10 and 100')
        return v

    @validator('body_fat_percentage')
    def validate_body_fat(cls, v):
        """Validate body fat percentage"""
        if v and (v < 0 or v > 100):
            raise ValueError('Body fat percentage must be between 0 and 100')
        return v

    @validator('resting_heart_rate')
    def validate_heart_rate(cls, v):
        """Validate resting heart rate"""
        if v and (v < 30 or v > 200):
            raise ValueError('Resting heart rate must be between 30 and 200 BPM')
        return v

    @validator('blood_pressure_systolic')
    def validate_systolic_bp(cls, v):
        """Validate systolic blood pressure"""
        if v and (v < 70 or v > 300):
            raise ValueError('Systolic blood pressure must be between 70 and 300 mmHg')
        return v

    @validator('blood_pressure_diastolic')
    def validate_diastolic_bp(cls, v):
        """Validate diastolic blood pressure"""
        if v and (v < 40 or v > 200):
            raise ValueError('Diastolic blood pressure must be between 40 and 200 mmHg')
        return v


class HealthAttributesResponse(HealthAttributesBase):
    """Schema for health attributes API responses"""
    id: int
    user_id: uuid.UUID
    profile_id: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class HealthSummary(BaseModel):
    """Simplified health summary for quick views"""
    id: int
    user_id: uuid.UUID
    bmi: Optional[float]
    overall_health_score: Optional[int]
    primary_health_goal: Optional[HealthGoal]
    daily_step_goal: Optional[int]
    last_updated: datetime

    class Config:
        from_attributes = True 