"""
Symptoms Models
Models for tracking health symptoms and their patterns.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Index, CheckConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator, EmailStr

from common.models.base import Base, BaseModel as CommonBaseModel

class SymptomCategory(Enum):
    """Categories of symptoms"""
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    NEUROLOGICAL = "neurological"
    MUSCULOSKELETAL = "musculoskeletal"
    DERMATOLOGICAL = "dermatological"
    ENDOCRINE = "endocrine"
    IMMUNOLOGICAL = "immunological"
    PSYCHIATRIC = "psychiatric"
    GENITOURINARY = "genitourinary"
    OPHTHALMOLOGICAL = "ophthalmological"
    OTOLARYNGOLOGICAL = "otolaryngological"
    GENERAL = "general"
    PAIN = "pain"
    FATIGUE = "fatigue"
    SLEEP = "sleep"
    MOOD = "mood"
    COGNITIVE = "cognitive"
    SEXUAL = "sexual"
    REPRODUCTIVE = "reproductive"

class SymptomSeverity(Enum):
    """Symptom severity levels"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

class SymptomFrequency(Enum):
    """Symptom frequency patterns"""
    RARELY = "rarely"
    OCCASIONALLY = "occasionally"
    FREQUENTLY = "frequently"
    CONSTANTLY = "constantly"
    INTERMITTENT = "intermittent"
    CYCLICAL = "cyclical"
    SEASONAL = "seasonal"

class SymptomDuration(Enum):
    """Symptom duration patterns"""
    ACUTE = "acute"  # < 6 weeks
    SUBACUTE = "subacute"  # 6 weeks - 3 months
    CHRONIC = "chronic"  # > 3 months
    EPISODIC = "episodic"
    PERSISTENT = "persistent"

class SymptomTrigger(Enum):
    """Common symptom triggers"""
    STRESS = "stress"
    EXERCISE = "exercise"
    FOOD = "food"
    ALLERGEN = "allergen"
    MEDICATION = "medication"
    ALCOHOL = "alcohol"
    CAFFEINE = "caffeine"
    SLEEP_DEPRIVATION = "sleep_deprivation"
    WEATHER = "weather"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    ALTITUDE = "altitude"
    TRAVEL = "travel"
    WORK = "work"
    RELATIONSHIP = "relationship"
    FINANCIAL = "financial"
    HORMONAL = "hormonal"
    INFECTION = "infection"
    INJURY = "injury"
    SURGERY = "surgery"
    OTHER = "other"

class Symptoms(Base):
    """Symptoms database model"""
    __tablename__ = "symptoms"
    __table_args__ = (
        Index('idx_symptoms_user_created', 'user_id', 'created_at'),
        Index('idx_symptoms_category_created', 'symptom_category', 'created_at'),
        Index('idx_symptoms_severity_created', 'severity', 'created_at'),
        CheckConstraint('severity_level >= 1 AND severity_level <= 10', name='check_severity_level_range'),
        CheckConstraint('duration_hours >= 0', name='check_duration_positive'),
        CheckConstraint('frequency_count >= 0', name='check_frequency_positive'),
        {'schema': 'health_tracking'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Store user ID without foreign key constraint
    
    # Symptom details
    symptom_name = Column(String(200), nullable=False)
    symptom_category = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Severity and impact
    severity = Column(String(20), nullable=False)  # mild, moderate, severe, critical
    severity_level = Column(Float, nullable=False)  # 1-10 scale
    impact_on_daily_activities = Column(String(20))  # none, mild, moderate, severe
    
    # Timing and frequency
    frequency = Column(String(20))  # rarely, occasionally, frequently, constantly, etc.
    frequency_count = Column(Float)  # Number of occurrences per time period
    frequency_period = Column(String(20))  # per day, per week, per month
    duration = Column(String(20))  # acute, subacute, chronic, episodic, persistent
    duration_hours = Column(Float)  # Duration in hours
    start_time = Column(DateTime)  # When symptom started
    end_time = Column(DateTime)  # When symptom ended (if applicable)
    
    # Location and characteristics
    body_location = Column(String(200))  # Specific body location
    body_side = Column(String(20))  # left, right, bilateral, central
    radiation = Column(String(200))  # Where pain radiates to
    quality = Column(String(100))  # sharp, dull, throbbing, burning, etc.
    
    # Triggers and context
    triggers = Column(ARRAY(String))  # Array of trigger factors
    context = Column(Text)  # What was happening when symptom occurred
    associated_symptoms = Column(ARRAY(String))  # Other symptoms that occur together
    
    # Relief factors
    relief_factors = Column(ARRAY(String))  # What makes it better
    aggravating_factors = Column(ARRAY(String))  # What makes it worse
    
    # Medical context
    related_conditions = Column(ARRAY(String))  # Related medical conditions
    medications_taken = Column(ARRAY(String))  # Medications taken for this symptom
    treatments_tried = Column(ARRAY(String))  # Treatments that have been tried
    
    # Impact assessment
    sleep_impact = Column(String(20))  # none, mild, moderate, severe
    work_impact = Column(String(20))  # none, mild, moderate, severe
    social_impact = Column(String(20))  # none, mild, moderate, severe
    emotional_impact = Column(String(20))  # none, mild, moderate, severe
    
    # Monitoring and tracking
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100))  # Pattern of recurrence
    last_occurrence = Column(DateTime)  # When it last occurred
    next_expected = Column(DateTime)  # When it's expected to occur next
    
    # Medical attention
    requires_medical_attention = Column(Boolean, default=False)
    medical_attention_urgency = Column(String(20))  # none, routine, urgent, emergency
    medical_attention_received = Column(Boolean, default=False)
    medical_attention_date = Column(DateTime)
    medical_attention_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    symptom_metadata = Column(JSONB, default=dict)
    
    # Note: No relationship to User table to avoid cross-schema foreign key issues

# Pydantic Models for API
class SymptomBase(CommonBaseModel):
    """Base symptom model"""
    symptom_name: str = Field(..., max_length=200)
    symptom_category: SymptomCategory
    description: Optional[str] = Field(None, max_length=2000)
    severity: SymptomSeverity
    severity_level: float = Field(..., ge=1, le=10)
    impact_on_daily_activities: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    frequency: Optional[SymptomFrequency] = None
    frequency_count: Optional[float] = Field(None, ge=0)
    frequency_period: Optional[str] = Field(None, pattern="^(per day|per week|per month|per year)$")
    duration: Optional[SymptomDuration] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    body_location: Optional[str] = Field(None, max_length=200)
    body_side: Optional[str] = Field(None, pattern="^(left|right|bilateral|central)$")
    radiation: Optional[str] = Field(None, max_length=200)
    quality: Optional[str] = Field(None, max_length=100)
    triggers: Optional[List[str]] = Field(default_factory=list)
    context: Optional[str] = Field(None, max_length=1000)
    associated_symptoms: Optional[List[str]] = Field(default_factory=list)
    relief_factors: Optional[List[str]] = Field(default_factory=list)
    aggravating_factors: Optional[List[str]] = Field(default_factory=list)
    related_conditions: Optional[List[str]] = Field(default_factory=list)
    medications_taken: Optional[List[str]] = Field(default_factory=list)
    treatments_tried: Optional[List[str]] = Field(default_factory=list)
    sleep_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    work_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    social_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    emotional_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    is_recurring: Optional[bool] = False
    recurrence_pattern: Optional[str] = Field(None, max_length=100)
    requires_medical_attention: Optional[bool] = False
    medical_attention_urgency: Optional[str] = Field(None, pattern="^(none|routine|urgent|emergency)$")
    symptom_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SymptomCreate(SymptomBase):
    """Symptom creation model"""
    pass

class SymptomUpdate(CommonBaseModel):
    """Symptom update model"""
    symptom_name: Optional[str] = Field(None, max_length=200)
    symptom_category: Optional[SymptomCategory] = None
    description: Optional[str] = Field(None, max_length=2000)
    severity: Optional[SymptomSeverity] = None
    severity_level: Optional[float] = Field(None, ge=1, le=10)
    impact_on_daily_activities: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    frequency: Optional[SymptomFrequency] = None
    frequency_count: Optional[float] = Field(None, ge=0)
    frequency_period: Optional[str] = Field(None, pattern="^(per day|per week|per month|per year)$")
    duration: Optional[SymptomDuration] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    body_location: Optional[str] = Field(None, max_length=200)
    body_side: Optional[str] = Field(None, pattern="^(left|right|bilateral|central)$")
    radiation: Optional[str] = Field(None, max_length=200)
    quality: Optional[str] = Field(None, max_length=100)
    triggers: Optional[List[str]] = None
    context: Optional[str] = Field(None, max_length=1000)
    associated_symptoms: Optional[List[str]] = None
    relief_factors: Optional[List[str]] = None
    aggravating_factors: Optional[List[str]] = None
    related_conditions: Optional[List[str]] = None
    medications_taken: Optional[List[str]] = None
    treatments_tried: Optional[List[str]] = None
    sleep_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    work_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    social_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    emotional_impact: Optional[str] = Field(None, pattern="^(none|mild|moderate|severe)$")
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = Field(None, max_length=100)
    requires_medical_attention: Optional[bool] = None
    medical_attention_urgency: Optional[str] = Field(None, pattern="^(none|routine|urgent|emergency)$")
    medical_attention_received: Optional[bool] = None
    medical_attention_date: Optional[datetime] = None
    medical_attention_notes: Optional[str] = Field(None, max_length=1000)
    symptom_metadata: Optional[Dict[str, Any]] = None

class SymptomResponse(CommonBaseModel):
    """Symptom response model"""
    id: str
    user_id: str
    symptom_name: str
    symptom_category: str
    description: Optional[str]
    severity: str
    severity_level: float
    impact_on_daily_activities: Optional[str]
    frequency: Optional[str]
    frequency_count: Optional[float]
    frequency_period: Optional[str]
    duration: Optional[str]
    duration_hours: Optional[float]
    start_time: Optional[str]
    end_time: Optional[str]
    body_location: Optional[str]
    body_side: Optional[str]
    radiation: Optional[str]
    quality: Optional[str]
    triggers: Optional[List[str]]
    context: Optional[str]
    associated_symptoms: Optional[List[str]]
    relief_factors: Optional[List[str]]
    aggravating_factors: Optional[List[str]]
    related_conditions: Optional[List[str]]
    medications_taken: Optional[List[str]]
    treatments_tried: Optional[List[str]]
    sleep_impact: Optional[str]
    work_impact: Optional[str]
    social_impact: Optional[str]
    emotional_impact: Optional[str]
    is_recurring: Optional[bool]
    recurrence_pattern: Optional[str]
    last_occurrence: Optional[str]
    next_expected: Optional[str]
    requires_medical_attention: Optional[bool]
    medical_attention_urgency: Optional[str]
    medical_attention_received: Optional[bool]
    medical_attention_date: Optional[str]
    medical_attention_notes: Optional[str]
    created_at: str
    updated_at: str
    symptom_metadata: Dict[str, Any]

    class Config:
        from_attributes = True

class SymptomFilter(CommonBaseModel):
    """Symptom filter model"""
    symptom_category: Optional[SymptomCategory] = None
    severity: Optional[SymptomSeverity] = None
    frequency: Optional[SymptomFrequency] = None
    duration: Optional[SymptomDuration] = None
    body_location: Optional[str] = None
    is_recurring: Optional[bool] = None
    requires_medical_attention: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class SymptomPattern(CommonBaseModel):
    """Symptom pattern analysis result"""
    symptom_name: str
    frequency: str
    average_severity: float
    common_triggers: List[str]
    common_relief_factors: List[str]
    impact_level: str
    recurrence_rate: float
    seasonal_pattern: Optional[str]
    time_of_day_pattern: Optional[str]
    duration_pattern: str
    associated_conditions: List[str]
    recommendations: List[str] 