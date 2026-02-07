"""
AI Insights Data Models
Models for health insights, patterns, and analysis results.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean, Float, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from common.models.base import Base


class InsightType(str, Enum):
    """Types of health insights."""
    TREND_ANALYSIS = "trend_analysis"
    PATTERN_DETECTION = "pattern_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    RISK_ASSESSMENT = "risk_assessment"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    BEHAVIORAL_INSIGHT = "behavioral_insight"
    CLINICAL_INSIGHT = "clinical_insight"
    LIFESTYLE_INSIGHT = "lifestyle_insight"
    NUTRITION_INSIGHT = "nutrition_insight"
    FITNESS_INSIGHT = "fitness_insight"
    SLEEP_INSIGHT = "sleep_insight"
    STRESS_INSIGHT = "stress_insight"
    MEDICATION_INSIGHT = "medication_insight"
    VITAL_SIGN_INSIGHT = "vital_sign_insight"
    LAB_RESULT_INSIGHT = "lab_result_insight"


class InsightSeverity(str, Enum):
    """Severity levels for insights."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InsightStatus(str, Enum):
    """Status of insights."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DISMISSED = "dismissed"


class InsightCategory(str, Enum):
    """Categories of insights."""
    HEALTH_METRICS = "health_metrics"
    BEHAVIOR = "behavior"
    LIFESTYLE = "lifestyle"
    CLINICAL = "clinical"
    PREVENTIVE = "preventive"
    DIAGNOSTIC = "diagnostic"
    PROGNOSTIC = "prognostic"
    THERAPEUTIC = "therapeutic"


# SQLAlchemy Models
class InsightDB(Base):
    """Database model for health insights."""
    __tablename__ = "insights"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    insight_type = Column(SQLEnum(InsightType), nullable=False)
    category = Column(SQLEnum(InsightCategory), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Integer, default=1)  # 1-5 scale
    confidence_score = Column(Float, default=0.0)  # 0.0-1.0
    data_sources = Column(JSON, default=list)
    insight_metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - using string references to avoid circular imports
    # The relationship will be resolved at runtime when the User model is available
    patient = relationship("User", back_populates="insights", lazy="select")


class HealthPatternDB(Base):
    """Database model for health patterns."""
    __tablename__ = "health_patterns"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pattern_type = Column(String(100), nullable=False)
    pattern_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)  # 0.0-1.0
    data_points = Column(JSON, default=list)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    first_detected = Column(DateTime, default=datetime.utcnow)
    last_observed = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    pattern_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - using string references to avoid circular imports
    # The relationship will be resolved at runtime when the User model is available
    patient = relationship("User", back_populates="health_patterns", lazy="select")


# Pydantic Models for API
class InsightBase(BaseModel):
    """Base model for insights."""
    insight_type: InsightType
    category: InsightCategory
    title: str = Field(..., max_length=200)
    description: str
    summary: Optional[str] = None
    severity: InsightSeverity = InsightSeverity.MEDIUM
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    data_sources: Optional[List[str]] = None
    analysis_parameters: Optional[Dict[str, Any]] = None
    supporting_evidence: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class InsightCreate(InsightBase):
    """Model for creating insights."""
    patient_id: UUID


class InsightUpdate(BaseModel):
    """Model for updating insights."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    summary: Optional[str] = None
    severity: Optional[InsightSeverity] = None
    status: Optional[InsightStatus] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    supporting_evidence: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None


class InsightResponse(InsightBase):
    """Model for insight responses."""
    id: UUID
    patient_id: UUID
    status: InsightStatus
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HealthPatternBase(BaseModel):
    """Base model for health patterns."""
    pattern_type: str
    pattern_name: str = Field(..., max_length=100)
    description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    data_points: Optional[List[Dict[str, Any]]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    pattern_metadata: Optional[Dict[str, Any]] = None


class HealthPatternCreate(HealthPatternBase):
    """Model for creating health patterns."""
    patient_id: UUID


class HealthPatternUpdate(BaseModel):
    """Model for updating health patterns."""
    pattern_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    data_points: Optional[List[Dict[str, Any]]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    pattern_metadata: Optional[Dict[str, Any]] = None


class HealthPatternResponse(HealthPatternBase):
    """Model for health pattern responses."""
    id: UUID
    patient_id: UUID
    first_detected: datetime
    last_observed: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
 