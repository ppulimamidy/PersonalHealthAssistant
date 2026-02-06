"""
Health Insights Models
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from common.models.base import Base

class InsightType(str, Enum):
    """Types of health insights"""
    # Trend insights
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    TREND_STABLE = "trend_stable"
    
    # Goal insights
    GOAL_PROGRESS = "goal_progress"
    GOAL_COMPLETED = "goal_completed"
    GOAL_AT_RISK = "goal_at_risk"
    
    # Health insights
    HEALTH_ALERT = "health_alert"
    HEALTH_RECOMMENDATION = "health_recommendation"
    HEALTH_CELEBRATION = "health_celebration"
    
    # Pattern insights
    PATTERN_DETECTED = "pattern_detected"
    CORRELATION_FOUND = "correlation_found"
    ANOMALY_DETECTED = "anomaly_detected"
    
    # Lifestyle insights
    LIFESTYLE_SUGGESTION = "lifestyle_suggestion"
    ACTIVITY_RECOMMENDATION = "activity_recommendation"
    NUTRITION_ADVICE = "nutrition_advice"
    
    # Medical insights
    MEDICAL_REMINDER = "medical_reminder"
    MEDICAL_RECOMMENDATION = "medical_recommendation"
    MEDICAL_ALERT = "medical_alert"

class InsightSeverity(str, Enum):
    """Insight severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class InsightStatus(str, Enum):
    """Insight status"""
    NEW = "new"
    READ = "read"
    ACTED_UPON = "acted_upon"
    DISMISSED = "dismissed"

class HealthInsight(Base):
    """Health insight model"""
    __tablename__ = "health_insights"
    __table_args__ = (
        Index('idx_health_insights_user_status', 'user_id', 'status'),
        Index('idx_health_insights_type_created', 'insight_type', 'created_at'),
        {'schema': 'health_tracking'}
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)  # Store user ID without foreign key constraint
    insight_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # Short summary for notifications
    severity = Column(String(20), nullable=False, default=InsightSeverity.MEDIUM)
    status = Column(String(20), nullable=False, default=InsightStatus.NEW)
    confidence = Column(Float, nullable=True)  # AI confidence score (0-1)
    actionable = Column(Boolean, nullable=False, default=True)
    action_taken = Column(Boolean, nullable=False, default=False)
    related_metrics = Column(JSONB, nullable=True)  # Related metric IDs
    related_goals = Column(JSONB, nullable=True)  # Related goal IDs
    insight_metadata = Column(JSONB, nullable=True)  # Additional insight data
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    acted_upon_at = Column(DateTime, nullable=True)
    
    # No relationships - microservices architecture
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "insight_type": self.insight_type,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "severity": self.severity,
            "status": self.status,
            "confidence": self.confidence,
            "actionable": self.actionable,
            "action_taken": self.action_taken,
            "related_metrics": self.related_metrics,
            "related_goals": self.related_goals,
            "insight_metadata": self.insight_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "acted_upon_at": self.acted_upon_at.isoformat() if self.acted_upon_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthInsight':
        """Create from dictionary"""
        return cls(
            id=UUID(data.get("id")) if data.get("id") else None,
            user_id=UUID(data["user_id"]),
            insight_type=data["insight_type"],
            title=data["title"],
            description=data["description"],
            summary=data.get("summary"),
            severity=data.get("severity", InsightSeverity.MEDIUM),
            status=data.get("status", InsightStatus.NEW),
            confidence=data.get("confidence"),
            actionable=data.get("actionable", True),
            action_taken=data.get("action_taken", False),
            related_metrics=data.get("related_metrics"),
            related_goals=data.get("related_goals"),
            insight_metadata=data.get("insight_metadata")
        )
    
    def mark_as_read(self):
        """Mark insight as read"""
        self.status = InsightStatus.READ
        self.read_at = datetime.utcnow()
    
    def mark_as_acted_upon(self):
        """Mark insight as acted upon"""
        self.status = InsightStatus.ACTED_UPON
        self.action_taken = True
        self.acted_upon_at = datetime.utcnow()
    
    def dismiss(self):
        """Dismiss insight"""
        self.status = InsightStatus.DISMISSED

# Pydantic models for API
class HealthInsightCreate(BaseModel):
    """Create health insight request"""
    insight_type: InsightType = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title", max_length=200)
    description: str = Field(..., description="Insight description")
    summary: Optional[str] = Field(None, description="Short summary")
    severity: InsightSeverity = Field(default=InsightSeverity.MEDIUM, description="Insight severity")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    actionable: bool = Field(default=True, description="Whether insight is actionable")
    related_metrics: Optional[List[str]] = Field(None, description="Related metric IDs")
    related_goals: Optional[List[str]] = Field(None, description="Related goal IDs")
    insight_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence score"""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

class HealthInsightUpdate(BaseModel):
    """Update health insight request"""
    status: Optional[InsightStatus] = Field(None, description="Insight status")
    action_taken: Optional[bool] = Field(None, description="Whether action was taken")
    insight_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class HealthInsightResponse(BaseModel):
    """Health insight response"""
    id: UUID = Field(..., description="Insight ID")
    user_id: UUID = Field(..., description="User ID")
    insight_type: InsightType = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    summary: Optional[str] = Field(None, description="Short summary")
    severity: InsightSeverity = Field(..., description="Insight severity")
    status: InsightStatus = Field(..., description="Insight status")
    confidence: Optional[float] = Field(None, description="AI confidence score")
    actionable: bool = Field(..., description="Whether insight is actionable")
    action_taken: bool = Field(..., description="Whether action was taken")
    related_metrics: Optional[List[str]] = Field(None, description="Related metric IDs")
    related_goals: Optional[List[str]] = Field(None, description="Related goal IDs")
    insight_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    acted_upon_at: Optional[datetime] = Field(None, description="Acted upon timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Insight templates for common patterns
class InsightTemplate(BaseModel):
    """Template for generating insights"""
    insight_type: InsightType
    title_template: str
    description_template: str
    severity: InsightSeverity
    actionable: bool = True
    
    def generate_insight(self, **kwargs) -> Dict[str, Any]:
        """Generate insight from template"""
        return {
            "insight_type": self.insight_type,
            "title": self.title_template.format(**kwargs),
            "description": self.description_template.format(**kwargs),
            "severity": self.severity,
            "actionable": self.actionable
        }

# Common insight templates
INSIGHT_TEMPLATES = {
    "weight_trend_up": InsightTemplate(
        insight_type=InsightType.TREND_UP,
        title_template="Weight trending upward",
        description_template="Your weight has increased by {change} {unit} over the past {period}. Consider reviewing your nutrition and activity levels.",
        severity=InsightSeverity.MEDIUM
    ),
    "weight_trend_down": InsightTemplate(
        insight_type=InsightType.TREND_DOWN,
        title_template="Weight trending downward",
        description_template="Great progress! Your weight has decreased by {change} {unit} over the past {period}. Keep up the good work!",
        severity=InsightSeverity.LOW
    ),
    "goal_progress": InsightTemplate(
        insight_type=InsightType.GOAL_PROGRESS,
        title_template="Goal progress update",
        description_template="You're {progress}% of the way to your {goal_title} goal. {encouragement}",
        severity=InsightSeverity.LOW
    ),
    "goal_completed": InsightTemplate(
        insight_type=InsightType.GOAL_COMPLETED,
        title_template="Goal achieved!",
        description_template="Congratulations! You've successfully achieved your {goal_title} goal. {celebration_message}",
        severity=InsightSeverity.LOW
    ),
    "health_alert": InsightTemplate(
        insight_type=InsightType.HEALTH_ALERT,
        title_template="Health alert",
        description_template="Your {metric_type} reading of {value} {unit} is outside the normal range. Consider consulting with a healthcare provider.",
        severity=InsightSeverity.HIGH
    ),
    "activity_recommendation": InsightTemplate(
        insight_type=InsightType.ACTIVITY_RECOMMENDATION,
        title_template="Activity recommendation",
        description_template="Based on your recent activity levels, consider {recommendation} to improve your health.",
        severity=InsightSeverity.MEDIUM
    ),
    "nutrition_advice": InsightTemplate(
        insight_type=InsightType.NUTRITION_ADVICE,
        title_template="Nutrition advice",
        description_template="Your {nutrient} intake is {status}. Consider {advice} to maintain a balanced diet.",
        severity=InsightSeverity.MEDIUM
    ),
    "sleep_quality": InsightTemplate(
        insight_type=InsightType.HEALTH_RECOMMENDATION,
        title_template="Sleep quality insight",
        description_template="Your sleep quality has been {quality} recently. {recommendation}",
        severity=InsightSeverity.MEDIUM
    ),
    "correlation_found": InsightTemplate(
        insight_type=InsightType.CORRELATION_FOUND,
        title_template="Pattern detected",
        description_template="We found a correlation between {metric1} and {metric2}. {explanation}",
        severity=InsightSeverity.MEDIUM
    ),
    "anomaly_detected": InsightTemplate(
        insight_type=InsightType.ANOMALY_DETECTED,
        title_template="Unusual pattern detected",
        description_template="Your {metric_type} reading of {value} {unit} is unusual compared to your typical pattern. {explanation}",
        severity=InsightSeverity.MEDIUM
    )
}

class HealthInsightFilter(BaseModel):
    """Health insight filter model"""
    insight_type: Optional[InsightType] = None
    status: Optional[InsightStatus] = None
    severity: Optional[InsightSeverity] = None
    actionable: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0) 