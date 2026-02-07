"""
Counseling models for Personal Health Assistant.

This module contains models for genetic counseling including:
- Genetic counseling sessions
- Risk reports
- Counseling recommendations
- Patient education materials
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Integer, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid

from common.models.base import Base


class CounselingType(str, Enum):
    """Type of genetic counseling."""
    PRE_TEST = "pre_test"
    POST_TEST = "post_test"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    CARRIER = "carrier"
    CANCER = "cancer"
    CARDIOVASCULAR = "cardiovascular"
    PHARMACOGENOMIC = "pharmacogenomic"
    REPRODUCTIVE = "reproductive"
    PEDIATRIC = "pediatric"


class SessionStatus(str, Enum):
    """Status of counseling session."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ReportType(str, Enum):
    """Type of risk report."""
    COMPREHENSIVE = "comprehensive"
    DISEASE_SPECIFIC = "disease_specific"
    PHARMACOGENOMIC = "pharmacogenomic"
    ANCESTRY = "ancestry"
    CARRIER = "carrier"
    CANCER_RISK = "cancer_risk"
    CARDIOVASCULAR_RISK = "cardiovascular_risk"


class RiskCategory(str, Enum):
    """Category of risk in reports."""
    NO_INCREASED_RISK = "no_increased_risk"
    SLIGHTLY_INCREASED = "slightly_increased"
    MODERATELY_INCREASED = "moderately_increased"
    SIGNIFICANTLY_INCREASED = "significantly_increased"
    HIGH_RISK = "high_risk"


class GeneticCounseling(Base):
    """Model for genetic counseling sessions."""
    
    __tablename__ = "genetic_counseling"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    counselor_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True, index=True)
    
    # Session information
    counseling_type = Column(SQLEnum(CounselingType), nullable=False)
    session_status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED)
    
    # Scheduling
    scheduled_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Session details
    session_notes = Column(Text, nullable=True)
    patient_concerns = Column(Text, nullable=True)
    family_history = Column(JSON, default=dict)
    medical_history = Column(JSON, default=dict)
    
    # Recommendations
    recommendations = Column(JSON, default=list)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    
    # Additional data
    session_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("CounselingSession", back_populates="counseling")
    risk_reports = relationship("RiskReport", back_populates="counseling")
    
    def __repr__(self):
        return f"<GeneticCounseling(id={self.id}, type={self.counseling_type}, status={self.session_status})>"


class CounselingSession(Base):
    """Model for individual counseling session details."""
    
    __tablename__ = "counseling_sessions"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counseling_id = Column(UUID(as_uuid=True), ForeignKey("genomics.genetic_counseling.id"), nullable=False)
    
    # Session details
    session_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    session_date = Column(DateTime, nullable=False)
    session_duration = Column(Integer, nullable=True)  # in minutes
    
    # Content
    topics_discussed = Column(JSON, default=list)
    questions_answered = Column(JSON, default=list)
    concerns_addressed = Column(JSON, default=list)
    
    # Outcomes
    patient_understanding = Column(String, nullable=True)  # poor, fair, good, excellent
    emotional_response = Column(String, nullable=True)
    decision_made = Column(String, nullable=True)
    
    # Documentation
    session_summary = Column(Text, nullable=True)
    action_items = Column(JSON, default=list)
    next_steps = Column(JSON, default=list)
    
    # Additional data
    session_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    counseling = relationship("GeneticCounseling", back_populates="sessions")
    
    def __repr__(self):
        return f"<CounselingSession(id={self.id}, session_number={self.session_number})>"


class RiskReport(Base):
    """Model for genetic risk reports."""
    
    __tablename__ = "risk_reports"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    counseling_id = Column(UUID(as_uuid=True), ForeignKey("genomics.genetic_counseling.id"), nullable=True)
    
    # Report information
    report_type = Column(SQLEnum(ReportType), nullable=False)
    report_title = Column(String, nullable=False)
    report_date = Column(DateTime, nullable=False)
    
    # Risk assessment
    overall_risk_category = Column(SQLEnum(RiskCategory), nullable=False)
    risk_score = Column(Float, nullable=True)  # 0.0 to 1.0
    confidence_level = Column(String, nullable=True)
    
    # Content
    executive_summary = Column(Text, nullable=True)
    detailed_analysis = Column(Text, nullable=True)
    risk_factors = Column(JSON, default=list)
    protective_factors = Column(JSON, default=list)
    
    # Recommendations
    clinical_recommendations = Column(JSON, default=list)
    lifestyle_recommendations = Column(JSON, default=list)
    screening_recommendations = Column(JSON, default=list)
    prevention_strategies = Column(JSON, default=list)
    
    # Educational content
    educational_materials = Column(JSON, default=list)
    resources = Column(JSON, default=list)
    references = Column(JSON, default=list)
    
    # Additional data
    report_metadata = Column(JSON, default=dict)
    is_confidential = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    counseling = relationship("GeneticCounseling", back_populates="risk_reports")
    
    def __repr__(self):
        return f"<RiskReport(id={self.id}, type={self.report_type}, risk={self.overall_risk_category})>"


# Pydantic models for API
class GeneticCounselingBase(BaseModel):
    """Base model for genetic counseling."""
    counseling_type: CounselingType
    scheduled_date: datetime
    duration_minutes: int = 60
    patient_concerns: Optional[str] = None
    family_history: Dict[str, Any] = Field(default_factory=dict)
    medical_history: Dict[str, Any] = Field(default_factory=dict)


class GeneticCounselingCreate(GeneticCounselingBase):
    """Model for creating genetic counseling."""
    counselor_id: Optional[uuid.UUID] = None


class GeneticCounselingUpdate(BaseModel):
    """Model for updating genetic counseling."""
    session_status: Optional[SessionStatus] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    session_notes: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None


class GeneticCounselingResponse(GeneticCounselingBase):
    """Model for genetic counseling API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    counselor_id: Optional[uuid.UUID] = None
    session_status: SessionStatus
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    session_notes: Optional[str] = None
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_required: bool
    follow_up_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CounselingSessionBase(BaseModel):
    """Base model for counseling session."""
    session_number: int
    session_date: datetime
    session_duration: Optional[int] = None
    topics_discussed: List[str] = Field(default_factory=list)
    questions_answered: List[str] = Field(default_factory=list)
    concerns_addressed: List[str] = Field(default_factory=list)


class CounselingSessionCreate(CounselingSessionBase):
    """Model for creating counseling session."""
    counseling_id: uuid.UUID
    patient_understanding: Optional[str] = None
    emotional_response: Optional[str] = None
    decision_made: Optional[str] = None
    session_summary: Optional[str] = None
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[Dict[str, Any]] = Field(default_factory=list)


class CounselingSessionResponse(CounselingSessionBase):
    """Model for counseling session API responses."""
    id: uuid.UUID
    counseling_id: uuid.UUID
    patient_understanding: Optional[str] = None
    emotional_response: Optional[str] = None
    decision_made: Optional[str] = None
    session_summary: Optional[str] = None
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RiskReportBase(BaseModel):
    """Base model for risk report."""
    report_type: ReportType
    report_title: str
    report_date: datetime
    overall_risk_category: RiskCategory
    risk_score: Optional[float] = None
    confidence_level: Optional[str] = None


class RiskReportCreate(RiskReportBase):
    """Model for creating risk report."""
    counseling_id: Optional[uuid.UUID] = None
    executive_summary: Optional[str] = None
    detailed_analysis: Optional[str] = None
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    protective_factors: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    lifestyle_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    screening_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    prevention_strategies: List[Dict[str, Any]] = Field(default_factory=list)
    educational_materials: List[Dict[str, Any]] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    is_confidential: bool = True


class RiskReportResponse(RiskReportBase):
    """Model for risk report API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    counseling_id: Optional[uuid.UUID] = None
    executive_summary: Optional[str] = None
    detailed_analysis: Optional[str] = None
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    protective_factors: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    lifestyle_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    screening_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    prevention_strategies: List[Dict[str, Any]] = Field(default_factory=list)
    educational_materials: List[Dict[str, Any]] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    is_confidential: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 