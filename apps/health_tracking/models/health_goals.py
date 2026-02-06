"""
Health Goals Models
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, Date, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from common.models.base import Base
from .health_metrics import MetricType, MetricUnit

class GoalStatus(str, Enum):
    """Goal status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class GoalType(str, Enum):
    """Goal types"""
    TARGET = "target"  # Reach a specific value
    IMPROVEMENT = "improvement"  # Improve by a certain amount
    MAINTENANCE = "maintenance"  # Maintain current level
    REDUCTION = "reduction"  # Reduce by a certain amount

class GoalFrequency(str, Enum):
    """Goal frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ONCE = "once"  # One-time goal

class HealthGoal(Base):
    """Health goal model"""
    __tablename__ = "health_goals"
    __table_args__ = (
        Index('idx_health_goals_user_status', 'user_id', 'status'),
        Index('idx_health_goals_type_status', 'goal_type', 'status'),
        {'schema': 'health_tracking'}
    )
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)  # Store user ID without foreign key constraint
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    metric_type = Column(String(50), nullable=False)
    goal_type = Column(String(20), nullable=False, default=GoalType.TARGET)
    target_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    unit = Column(String(20), nullable=False)
    frequency = Column(String(20), nullable=False, default=GoalFrequency.ONCE)
    start_date = Column(Date, nullable=False, default=date.today)
    target_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default=GoalStatus.ACTIVE)
    progress = Column(Float, nullable=True)  # Percentage progress (0-100)
    goal_metadata = Column(JSONB, nullable=True)  # Additional goal data
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # No relationships - microservices architecture
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "description": self.description,
            "metric_type": self.metric_type,
            "goal_type": self.goal_type,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "unit": self.unit,
            "frequency": self.frequency,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "status": self.status,
            "progress": self.progress,
            "metadata": self.goal_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthGoal':
        """Create from dictionary"""
        return cls(
            id=UUID(data.get("id")) if data.get("id") else None,
            user_id=UUID(data["user_id"]),
            title=data["title"],
            description=data.get("description"),
            metric_type=data["metric_type"],
            goal_type=data.get("goal_type", GoalType.TARGET),
            target_value=data.get("target_value"),
            current_value=data.get("current_value"),
            unit=data["unit"],
            frequency=data.get("frequency", GoalFrequency.ONCE),
            start_date=date.fromisoformat(data["start_date"]) if data.get("start_date") else date.today(),
            target_date=date.fromisoformat(data["target_date"]) if data.get("target_date") else None,
            status=data.get("status", GoalStatus.ACTIVE),
            progress=data.get("progress"),
            goal_metadata=data.get("metadata")
        )
    
    def calculate_progress(self) -> float:
        """Calculate progress percentage"""
        if not self.target_value or not self.current_value:
            return 0.0
        
        if self.goal_type == GoalType.TARGET:
            # For target goals, progress is current/target
            return min(100.0, (self.current_value / self.target_value) * 100)
        elif self.goal_type == GoalType.IMPROVEMENT:
            # For improvement goals, progress is improvement achieved
            return min(100.0, self.current_value * 100)
        elif self.goal_type == GoalType.REDUCTION:
            # For reduction goals, progress is reduction achieved
            return min(100.0, (1 - self.current_value) * 100)
        else:
            return 0.0
    
    def is_completed(self) -> bool:
        """Check if goal is completed"""
        if self.status == GoalStatus.COMPLETED:
            return True
        
        if self.goal_type == GoalType.TARGET:
            return self.current_value >= self.target_value
        elif self.goal_type == GoalType.IMPROVEMENT:
            return self.current_value >= 1.0
        elif self.goal_type == GoalType.REDUCTION:
            return self.current_value <= 0.0
        else:
            return False
    
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        if not self.target_date:
            return False
        
        return date.today() > self.target_date and self.status == GoalStatus.ACTIVE

# Pydantic models for API
class HealthGoalCreate(BaseModel):
    """Create health goal request"""
    title: str = Field(..., description="Goal title", max_length=200)
    description: Optional[str] = Field(None, description="Goal description")
    metric_type: MetricType = Field(..., description="Type of health metric")
    goal_type: GoalType = Field(default=GoalType.TARGET, description="Type of goal")
    target_value: Optional[float] = Field(None, description="Target value")
    unit: MetricUnit = Field(..., description="Unit of measurement")
    frequency: GoalFrequency = Field(default=GoalFrequency.ONCE, description="Goal frequency")
    start_date: Optional[date] = Field(None, description="Start date")
    target_date: Optional[date] = Field(None, description="Target completion date")
    goal_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator('target_value')
    def validate_target_value(cls, v, values):
        """Validate target value"""
        if v is not None and v < 0:
            raise ValueError("Target value cannot be negative")
        return v
    
    @validator('target_date')
    def validate_target_date(cls, v, values):
        """Validate target date"""
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError("Target date cannot be before start date")
        return v
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class HealthGoalUpdate(BaseModel):
    """Update health goal request"""
    title: Optional[str] = Field(None, description="Goal title", max_length=200)
    description: Optional[str] = Field(None, description="Goal description")
    target_value: Optional[float] = Field(None, description="Target value")
    current_value: Optional[float] = Field(None, description="Current value")
    unit: Optional[MetricUnit] = Field(None, description="Unit of measurement")
    target_date: Optional[date] = Field(None, description="Target completion date")
    status: Optional[GoalStatus] = Field(None, description="Goal status")
    goal_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class HealthGoalResponse(BaseModel):
    """Health goal response"""
    id: UUID = Field(..., description="Goal ID")
    user_id: UUID = Field(..., description="User ID")
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(None, description="Goal description")
    metric_type: MetricType = Field(..., description="Type of health metric")
    goal_type: GoalType = Field(..., description="Type of goal")
    target_value: Optional[float] = Field(None, description="Target value")
    current_value: Optional[float] = Field(None, description="Current value")
    unit: MetricUnit = Field(..., description="Unit of measurement")
    frequency: GoalFrequency = Field(..., description="Goal frequency")
    start_date: date = Field(..., description="Start date")
    target_date: Optional[date] = Field(None, description="Target completion date")
    status: GoalStatus = Field(..., description="Goal status")
    progress: Optional[float] = Field(None, description="Progress percentage")
    goal_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True

class HealthGoalFilter(BaseModel):
    """Health goal filter model"""
    goal_type: Optional[GoalType] = None
    status: Optional[GoalStatus] = None
    metric_type: Optional[MetricType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0) 