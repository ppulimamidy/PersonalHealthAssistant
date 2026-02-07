"""
AI Recommendations Data Models
Models for personalized health recommendations and action items.
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


class RecommendationType(str, Enum):
    """Types of health recommendations."""
    LIFESTYLE = "lifestyle"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    STRESS_MANAGEMENT = "stress_management"
    MEDICATION = "medication"
    PREVENTIVE_CARE = "preventive_care"
    SCREENING = "screening"
    VACCINATION = "vaccination"
    BEHAVIORAL = "behavioral"
    CLINICAL = "clinical"
    EMERGENCY = "emergency"
    MONITORING = "monitoring"
    EDUCATION = "education"
    REFERRAL = "referral"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class RecommendationStatus(str, Enum):
    """Status of recommendations."""
    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class ActionType(str, Enum):
    """Types of actions for recommendations."""
    SCHEDULE_APPOINTMENT = "schedule_appointment"
    TAKE_MEDICATION = "take_medication"
    EXERCISE = "exercise"
    DIET_CHANGE = "diet_change"
    SLEEP_ADJUSTMENT = "sleep_adjustment"
    STRESS_REDUCTION = "stress_reduction"
    MONITORING = "monitoring"
    EDUCATION = "education"
    LIFESTYLE_CHANGE = "lifestyle_change"
    EMERGENCY_ACTION = "emergency_action"


# SQLAlchemy Models
class RecommendationDB(Base):
    """Database model for health recommendations."""
    __tablename__ = "recommendations"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    insight_id = Column(PGUUID(as_uuid=True), ForeignKey("insights.id"), nullable=True)
    
    # Recommendation details
    recommendation_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    summary = Column(Text)
    priority = Column(String(20), nullable=False, default=RecommendationPriority.MEDIUM)
    status = Column(String(20), nullable=False, default=RecommendationStatus.PENDING)
    
    # Scoring and confidence
    confidence_score = Column(Float, nullable=False, default=0.0)
    effectiveness_score = Column(Float, nullable=False, default=0.0)
    adherence_score = Column(Float, nullable=False, default=0.0)
    
    # Actions and steps
    actions = Column(JSON)  # List of specific actions to take
    steps = Column(JSON)  # Step-by-step instructions
    resources = Column(JSON)  # Educational resources and links
    
    # Timing and scheduling
    due_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    frequency = Column(String(50))  # How often to perform the action
    duration = Column(String(50))  # How long to continue
    
    # Metadata
    data_sources = Column(JSON)  # Data sources used for recommendation
    reasoning = Column(JSON)  # AI reasoning behind the recommendation
    alternatives = Column(JSON)  # Alternative recommendations
    contraindications = Column(JSON)  # Any contraindications
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("UserDB", back_populates="recommendations")
    insight = relationship("InsightDB", back_populates="recommendations")
    actions_taken = relationship("RecommendationActionDB", back_populates="recommendation")


class RecommendationActionDB(Base):
    """Database model for actions taken on recommendations."""
    __tablename__ = "recommendation_actions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    recommendation_id = Column(PGUUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Action details
    action_type = Column(String(50), nullable=False)
    action_name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="pending")
    
    # Completion tracking
    completed_at = Column(DateTime)
    completion_notes = Column(Text)
    completion_evidence = Column(JSON)  # Evidence of completion
    
    # Effectiveness tracking
    effectiveness_rating = Column(Float)  # Patient's rating of effectiveness
    difficulty_rating = Column(Float)  # Patient's rating of difficulty
    adherence_rating = Column(Float)  # Patient's rating of adherence
    
    # Timestamps
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recommendation = relationship("RecommendationDB", back_populates="actions_taken")
    patient = relationship("UserDB", back_populates="recommendation_actions")


class HealthGoalDB(Base):
    """Database model for health goals."""
    __tablename__ = "health_goals"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Goal details
    goal_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    target_value = Column(Float)
    current_value = Column(Float)
    unit = Column(String(50))
    
    # Goal tracking
    status = Column(String(20), nullable=False, default="active")
    progress_percentage = Column(Float, default=0.0)
    milestone_count = Column(Integer, default=0)
    completed_milestones = Column(Integer, default=0)
    
    # Timeline
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    target_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Metadata
    priority = Column(String(20), default="medium")
    difficulty = Column(String(20), default="medium")
    motivation_level = Column(Integer)  # 1-10 scale
    barriers = Column(JSON)  # Potential barriers to achieving goal
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("UserDB", back_populates="health_goals")


# Pydantic Models for API
class RecommendationBase(BaseModel):
    """Base model for recommendations."""
    recommendation_type: RecommendationType
    title: str = Field(..., max_length=200)
    description: str
    summary: Optional[str] = None
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    effectiveness_score: float = Field(..., ge=0.0, le=1.0)
    adherence_score: float = Field(..., ge=0.0, le=1.0)
    actions: Optional[List[Dict[str, Any]]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    resources: Optional[List[Dict[str, Any]]] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    data_sources: Optional[List[str]] = None
    reasoning: Optional[Dict[str, Any]] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    contraindications: Optional[List[str]] = None


class RecommendationCreate(RecommendationBase):
    """Model for creating recommendations."""
    patient_id: UUID
    insight_id: Optional[UUID] = None


class RecommendationUpdate(BaseModel):
    """Model for updating recommendations."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[RecommendationPriority] = None
    status: Optional[RecommendationStatus] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    effectiveness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    adherence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    actions: Optional[List[Dict[str, Any]]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    resources: Optional[List[Dict[str, Any]]] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    contraindications: Optional[List[str]] = None


class RecommendationResponse(RecommendationBase):
    """Model for recommendation responses."""
    id: UUID
    patient_id: UUID
    insight_id: Optional[UUID] = None
    status: RecommendationStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationActionBase(BaseModel):
    """Base model for recommendation actions."""
    action_type: ActionType
    action_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: str = "pending"
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    completion_evidence: Optional[Dict[str, Any]] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    difficulty_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    adherence_rating: Optional[float] = Field(None, ge=0.0, le=10.0)


class RecommendationActionCreate(RecommendationActionBase):
    """Model for creating recommendation actions."""
    recommendation_id: UUID
    patient_id: UUID


class RecommendationActionUpdate(BaseModel):
    """Model for updating recommendation actions."""
    action_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    completion_evidence: Optional[Dict[str, Any]] = None
    effectiveness_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    difficulty_rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    adherence_rating: Optional[float] = Field(None, ge=0.0, le=10.0)


class RecommendationActionResponse(RecommendationActionBase):
    """Model for recommendation action responses."""
    id: UUID
    recommendation_id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HealthGoalBase(BaseModel):
    """Base model for health goals."""
    goal_type: str
    title: str = Field(..., max_length=200)
    description: str
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = None
    priority: str = "medium"
    difficulty: str = "medium"
    motivation_level: Optional[int] = Field(None, ge=1, le=10)
    barriers: Optional[List[str]] = None
    target_date: Optional[datetime] = None


class HealthGoalCreate(HealthGoalBase):
    """Model for creating health goals."""
    patient_id: UUID


class HealthGoalUpdate(BaseModel):
    """Model for updating health goals."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    priority: Optional[str] = None
    difficulty: Optional[str] = None
    motivation_level: Optional[int] = Field(None, ge=1, le=10)
    barriers: Optional[List[str]] = None
    target_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None


class HealthGoalResponse(HealthGoalBase):
    """Model for health goal responses."""
    id: UUID
    patient_id: UUID
    status: str
    progress_percentage: float
    milestone_count: int
    completed_milestones: int
    start_date: datetime
    target_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 