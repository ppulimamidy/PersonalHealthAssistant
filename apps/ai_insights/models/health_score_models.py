"""
Health Score Data Models
Models for health scoring, wellness indices, and risk assessments.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from common.models.base import Base


class ScoreType(str, Enum):
    """Types of health scores."""
    OVERALL_HEALTH = "overall_health"
    CARDIOVASCULAR_HEALTH = "cardiovascular_health"
    RESPIRATORY_HEALTH = "respiratory_health"
    METABOLIC_HEALTH = "metabolic_health"
    MENTAL_HEALTH = "mental_health"
    PHYSICAL_FITNESS = "physical_fitness"
    NUTRITION_SCORE = "nutrition_score"
    SLEEP_QUALITY = "sleep_quality"
    STRESS_LEVEL = "stress_level"
    WELLNESS_INDEX = "wellness_index"
    BIOLOGICAL_AGE = "biological_age"
    HEALTH_RISK = "health_risk"
    LONGEVITY_SCORE = "longevity_score"
    QUALITY_OF_LIFE = "quality_of_life"
    FUNCTIONAL_CAPACITY = "functional_capacity"


class ScoreCategory(str, Enum):
    """Categories of health scores."""
    PHYSICAL = "physical"
    MENTAL = "mental"
    SOCIAL = "social"
    ENVIRONMENTAL = "environmental"
    SPIRITUAL = "spiritual"
    INTELLECTUAL = "intellectual"
    OCCUPATIONAL = "occupational"
    FINANCIAL = "financial"


class RiskLevel(str, Enum):
    """Risk levels for health assessments."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend directions for health scores."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    FLUCTUATING = "fluctuating"


# SQLAlchemy Models
class HealthScoreDB(Base):
    """Database model for health scores."""
    __tablename__ = "health_scores"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Score details
    score_type = Column(String(50), nullable=False)
    score_name = Column(String(100), nullable=False)
    score_value = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False, default=100.0)
    min_score = Column(Float, nullable=False, default=0.0)
    
    # Score components
    components = Column(JSON)  # Individual components contributing to score
    weights = Column(JSON)  # Weights for each component
    factors = Column(JSON)  # Factors affecting the score
    
    # Risk and trend analysis
    risk_level = Column(String(20))
    trend_direction = Column(String(20))
    trend_magnitude = Column(Float)  # How much the score is changing
    confidence_interval = Column(JSON)  # Confidence interval for the score
    
    # Metadata
    calculation_method = Column(String(100))
    data_sources = Column(JSON)
    algorithm_version = Column(String(50))
    last_calculation = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Timestamps
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("UserDB", back_populates="health_scores")
    trends = relationship("HealthScoreTrendDB", back_populates="health_score")


class HealthScoreTrendDB(Base):
    """Database model for health score trends."""
    __tablename__ = "health_score_trends"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    health_score_id = Column(PGUUID(as_uuid=True), ForeignKey("health_scores.id"), nullable=False)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Trend details
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    trend_type = Column(String(50), nullable=False)  # daily, weekly, monthly, yearly
    
    # Trend metrics
    start_value = Column(Float, nullable=False)
    end_value = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)
    change_percentage = Column(Float, nullable=False)
    average_value = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    
    # Trend analysis
    direction = Column(String(20), nullable=False)
    magnitude = Column(Float)
    consistency = Column(Float)  # How consistent the trend is
    volatility = Column(Float)  # How volatile the values are
    
    # Metadata
    data_points_count = Column(Integer, nullable=False)
    confidence_level = Column(Float)
    significance_level = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_score = relationship("HealthScoreDB", back_populates="trends")
    patient = relationship("UserDB", back_populates="health_score_trends")


class RiskAssessmentDB(Base):
    """Database model for health risk assessments."""
    __tablename__ = "risk_assessments"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Assessment details
    assessment_type = Column(String(50), nullable=False)
    risk_category = Column(String(50), nullable=False)
    overall_risk_level = Column(String(20), nullable=False)
    overall_risk_score = Column(Float, nullable=False)
    
    # Risk factors
    risk_factors = Column(JSON)  # List of identified risk factors
    protective_factors = Column(JSON)  # List of protective factors
    modifiable_risks = Column(JSON)  # Risks that can be modified
    non_modifiable_risks = Column(JSON)  # Risks that cannot be modified
    
    # Risk calculations
    risk_probability = Column(Float)  # Probability of risk event occurring
    risk_severity = Column(Float)  # Severity of potential outcome
    risk_urgency = Column(Float)  # How urgent intervention is needed
    
    # Recommendations
    recommendations = Column(JSON)  # Risk mitigation recommendations
    monitoring_plan = Column(JSON)  # Plan for monitoring risk factors
    follow_up_schedule = Column(JSON)  # Schedule for follow-up assessments
    
    # Metadata
    assessment_method = Column(String(100))
    data_sources = Column(JSON)
    confidence_level = Column(Float)
    validity_period = Column(Integer)  # Days until assessment expires
    
    # Timestamps
    assessed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("UserDB", back_populates="risk_assessments")


class WellnessIndexDB(Base):
    """Database model for wellness indices."""
    __tablename__ = "wellness_indices"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Index details
    index_type = Column(String(50), nullable=False)
    index_name = Column(String(100), nullable=False)
    overall_score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False, default=100.0)
    
    # Dimension scores
    physical_score = Column(Float)
    mental_score = Column(Float)
    social_score = Column(Float)
    environmental_score = Column(Float)
    spiritual_score = Column(Float)
    intellectual_score = Column(Float)
    occupational_score = Column(Float)
    financial_score = Column(Float)
    
    # Dimension weights
    dimension_weights = Column(JSON)  # Weights for each dimension
    dimension_contributions = Column(JSON)  # How much each dimension contributes
    
    # Analysis
    strongest_dimension = Column(String(50))
    weakest_dimension = Column(String(50))
    improvement_opportunities = Column(JSON)  # Areas for improvement
    strengths = Column(JSON)  # Areas of strength
    
    # Metadata
    calculation_method = Column(String(100))
    data_sources = Column(JSON)
    last_calculation = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Timestamps
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("UserDB", back_populates="wellness_indices")


# Pydantic Models for API
class HealthScoreBase(BaseModel):
    """Base model for health scores."""
    score_type: ScoreType
    score_name: str = Field(..., max_length=100)
    score_value: float
    max_score: float = 100.0
    min_score: float = 0.0
    components: Optional[Dict[str, float]] = None
    weights: Optional[Dict[str, float]] = None
    factors: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    trend_direction: Optional[TrendDirection] = None
    trend_magnitude: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None
    calculation_method: Optional[str] = None
    data_sources: Optional[List[str]] = None
    algorithm_version: Optional[str] = None


class HealthScoreCreate(HealthScoreBase):
    """Model for creating health scores."""
    patient_id: UUID


class HealthScoreUpdate(BaseModel):
    """Model for updating health scores."""
    score_value: Optional[float] = None
    components: Optional[Dict[str, float]] = None
    weights: Optional[Dict[str, float]] = None
    factors: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    trend_direction: Optional[TrendDirection] = None
    trend_magnitude: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None
    calculation_method: Optional[str] = None
    data_sources: Optional[List[str]] = None
    algorithm_version: Optional[str] = None


class HealthScoreResponse(HealthScoreBase):
    """Model for health score responses."""
    id: UUID
    patient_id: UUID
    last_calculation: datetime
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HealthScoreTrendBase(BaseModel):
    """Base model for health score trends."""
    period_start: datetime
    period_end: datetime
    trend_type: str
    start_value: float
    end_value: float
    change_amount: float
    change_percentage: float
    average_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    direction: TrendDirection
    magnitude: Optional[float] = None
    consistency: Optional[float] = Field(None, ge=0.0, le=1.0)
    volatility: Optional[float] = Field(None, ge=0.0, le=1.0)
    data_points_count: int
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    significance_level: Optional[float] = Field(None, ge=0.0, le=1.0)


class HealthScoreTrendCreate(HealthScoreTrendBase):
    """Model for creating health score trends."""
    health_score_id: UUID
    patient_id: UUID


class HealthScoreTrendResponse(HealthScoreTrendBase):
    """Model for health score trend responses."""
    id: UUID
    health_score_id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RiskAssessmentBase(BaseModel):
    """Base model for risk assessments."""
    assessment_type: str
    risk_category: str
    overall_risk_level: RiskLevel
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_factors: Optional[List[Dict[str, Any]]] = None
    protective_factors: Optional[List[Dict[str, Any]]] = None
    modifiable_risks: Optional[List[Dict[str, Any]]] = None
    non_modifiable_risks: Optional[List[Dict[str, Any]]] = None
    risk_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_severity: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_urgency: Optional[float] = Field(None, ge=0.0, le=1.0)
    recommendations: Optional[List[Dict[str, Any]]] = None
    monitoring_plan: Optional[Dict[str, Any]] = None
    follow_up_schedule: Optional[Dict[str, Any]] = None
    assessment_method: Optional[str] = None
    data_sources: Optional[List[str]] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    validity_period: Optional[int] = None
    expires_at: Optional[datetime] = None


class RiskAssessmentCreate(RiskAssessmentBase):
    """Model for creating risk assessments."""
    patient_id: UUID


class RiskAssessmentUpdate(BaseModel):
    """Model for updating risk assessments."""
    overall_risk_level: Optional[RiskLevel] = None
    overall_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_factors: Optional[List[Dict[str, Any]]] = None
    protective_factors: Optional[List[Dict[str, Any]]] = None
    modifiable_risks: Optional[List[Dict[str, Any]]] = None
    non_modifiable_risks: Optional[List[Dict[str, Any]]] = None
    risk_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_severity: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_urgency: Optional[float] = Field(None, ge=0.0, le=1.0)
    recommendations: Optional[List[Dict[str, Any]]] = None
    monitoring_plan: Optional[Dict[str, Any]] = None
    follow_up_schedule: Optional[Dict[str, Any]] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    validity_period: Optional[int] = None
    expires_at: Optional[datetime] = None


class RiskAssessmentResponse(RiskAssessmentBase):
    """Model for risk assessment responses."""
    id: UUID
    patient_id: UUID
    assessed_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WellnessIndexBase(BaseModel):
    """Base model for wellness indices."""
    index_type: str
    index_name: str = Field(..., max_length=100)
    overall_score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = 100.0
    physical_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    mental_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    social_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    environmental_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    spiritual_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    intellectual_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    occupational_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    financial_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    dimension_weights: Optional[Dict[str, float]] = None
    dimension_contributions: Optional[Dict[str, float]] = None
    strongest_dimension: Optional[str] = None
    weakest_dimension: Optional[str] = None
    improvement_opportunities: Optional[List[Dict[str, Any]]] = None
    strengths: Optional[List[Dict[str, Any]]] = None
    calculation_method: Optional[str] = None
    data_sources: Optional[List[str]] = None


class WellnessIndexCreate(WellnessIndexBase):
    """Model for creating wellness indices."""
    patient_id: UUID


class WellnessIndexUpdate(BaseModel):
    """Model for updating wellness indices."""
    overall_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    physical_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    mental_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    social_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    environmental_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    spiritual_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    intellectual_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    occupational_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    financial_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    dimension_weights: Optional[Dict[str, float]] = None
    dimension_contributions: Optional[Dict[str, float]] = None
    strongest_dimension: Optional[str] = None
    weakest_dimension: Optional[str] = None
    improvement_opportunities: Optional[List[Dict[str, Any]]] = None
    strengths: Optional[List[Dict[str, Any]]] = None
    calculation_method: Optional[str] = None
    data_sources: Optional[List[str]] = None


class WellnessIndexResponse(WellnessIndexBase):
    """Model for wellness index responses."""
    id: UUID
    patient_id: UUID
    last_calculation: datetime
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
 