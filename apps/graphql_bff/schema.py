"""
GraphQL Schema for Personal Physician Assistant (PPA)
Unified schema for health data, insights, and reasoning.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import strawberry
from strawberry.types import Info

# Define local types for GraphQL schema
from enum import Enum

class InsightType(str, Enum):
    SYMPTOM = "symptom"
    TREND = "trend"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"

class EvidenceSource(str, Enum):
    WEARABLE = "wearable"
    MEDICAL_RECORD = "medical_record"
    USER_INPUT = "user_input"
    LAB_RESULT = "lab_result"
    MEDICAL_LITERATURE = "medical_literature"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ReasoningType(str, Enum):
    SYMPTOM_ANALYSIS = "symptom_analysis"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    DAILY_SUMMARY = "daily_summary"
    DOCTOR_REPORT = "doctor_report"

# GraphQL Types
@strawberry.type
class Evidence:
    """Evidence supporting health insights"""
    source: str
    description: str
    confidence: str
    timestamp: Optional[datetime] = None

@strawberry.type
class Insight:
    """Health insight with evidence"""
    id: str
    type: str
    title: str
    description: str
    severity: Optional[str] = None
    confidence: str
    evidence: List[Evidence]
    actionable: bool
    timestamp: datetime

@strawberry.type
class Recommendation:
    """Health recommendation"""
    id: str
    title: str
    description: str
    category: str
    priority: str
    actionable: bool
    evidence: List[Evidence]
    follow_up: Optional[str] = None
    timestamp: datetime

@strawberry.type
class ReasoningResult:
    """Result of health reasoning"""
    query: str
    reasoning: str
    insights: List[Insight]
    recommendations: List[Recommendation]
    confidence: str
    processing_time: float
    data_sources: List[str]
    timestamp: datetime

@strawberry.type
class DailyInsight:
    """Daily health summary"""
    id: str
    date: datetime
    summary: str
    key_insights: List[Insight]
    recommendations: List[Recommendation]
    health_score: float
    data_quality_score: float

@strawberry.type
class DoctorReport:
    """Comprehensive doctor mode report"""
    id: str
    patient_id: str
    report_date: datetime
    time_period: str
    summary: str
    key_insights: List[Insight]
    recommendations: List[Recommendation]
    confidence_score: float
    next_steps: List[str]

@strawberry.type
class RealTimeInsight:
    """Real-time health insight"""
    id: str
    type: str
    message: str
    priority: str
    timestamp: datetime
    actionable: bool
    data_source: str

@strawberry.type
class HealthData:
    """Aggregated health data"""
    user_id: str
    time_window: str
    data_summary: str

@strawberry.type
class FeedbackResult:
    """Result of user feedback"""
    success: bool
    message: str
    insight_id: str
    feedback_id: str
    timestamp: datetime

# Input Types
@strawberry.input
class HealthQueryInput:
    """Input for health queries"""
    query: str
    reasoning_type: Optional[str] = "symptom_analysis"
    time_window: Optional[str] = "24h"
    data_types: Optional[List[str]] = None

@strawberry.input
class DoctorReportInput:
    """Input for doctor report generation"""
    time_window: str = "30d"
    include_trends: bool = True
    include_anomalies: bool = True
    include_recommendations: bool = True

@strawberry.input
class FeedbackInput:
    """Input for user feedback"""
    insight_id: str
    helpful: bool
    comment: Optional[str] = None

# Query Type
@strawberry.type
class Query:
    """Main query type for health data and reasoning"""
    
    @strawberry.field
    async def reason(
        self, 
        info: Info,
        query: str,
        reasoning_type: Optional[str] = "symptom_analysis",
        time_window: Optional[str] = "24h",
        data_types: Optional[List[str]] = None
    ) -> ReasoningResult:
        """Perform health reasoning on a query"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        reasoning_service = info.context["reasoning_service"]
        cache_service = info.context["cache_service"]
        
        # Check cache first
        cache_key = f"reasoning:{user['id']}:{hash(query)}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return ReasoningResult(**cached_result)
        
        # Perform reasoning
        result = await reasoning_service.query_health(
            query=query,
            reasoning_type=reasoning_type,
            time_window=time_window,
            data_types=data_types or ["vitals", "symptoms", "medications", "nutrition"],
            user_id=user["id"]
        )
        
        # Cache result
        await cache_service.set(cache_key, result.dict(), ttl=3600)
        
        return result
    
    @strawberry.field
    async def daily_summary(self, info: Info) -> DailyInsight:
        """Get daily health summary"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        cache_service = info.context["cache_service"]
        
        # Check cache first
        cache_key = f"daily_summary:{user['id']}:{datetime.now().date()}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return DailyInsight(**cached_result)
        
        # Get daily summary
        result = await data_service.get_daily_summary(user_id=user["id"])
        
        # Cache result
        await cache_service.set(cache_key, result.dict(), ttl=3600)
        
        return result
    
    @strawberry.field
    async def doctor_report(
        self, 
        info: Info,
        time_window: str = "30d"
    ) -> DoctorReport:
        """Generate comprehensive doctor report"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        reasoning_service = info.context["reasoning_service"]
        
        result = await reasoning_service.generate_doctor_report(
            user_id=user["id"],
            time_window=time_window
        )
        
        return result
    
    @strawberry.field
    async def real_time_insights(self, info: Info) -> List[RealTimeInsight]:
        """Get real-time health insights"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        
        result = await data_service.get_real_time_insights(user_id=user["id"])
        
        return result
    
    @strawberry.field
    async def health_data(
        self, 
        info: Info,
        time_window: str = "24h",
        data_types: Optional[List[str]] = None
    ) -> HealthData:
        """Get aggregated health data"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        
        result = await data_service.get_health_data(
            user_id=user["id"],
            time_window=time_window,
            data_types=data_types
        )
        
        return result
    
    @strawberry.field
    async def insights_history(
        self, 
        info: Info,
        limit: int = 20,
        offset: int = 0
    ) -> List[Insight]:
        """Get historical insights"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        
        result = await data_service.get_insights_history(
            user_id=user["id"],
            limit=limit,
            offset=offset
        )
        
        return result

# Mutation Type
@strawberry.type
class Mutation:
    """Main mutation type for health data and feedback"""
    
    @strawberry.mutation
    async def provide_feedback(
        self, 
        info: Info,
        insight_id: str,
        helpful: bool,
        comment: Optional[str] = None
    ) -> FeedbackResult:
        """Provide feedback on health insights"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        
        result = await data_service.provide_feedback(
            user_id=user["id"],
            insight_id=insight_id,
            helpful=helpful,
            comment=comment
        )
        
        return result
    
    @strawberry.mutation
    async def log_symptom(
        self, 
        info: Info,
        symptom: str,
        severity: Optional[str] = None,
        duration: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Log a new symptom"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        
        result = await data_service.log_symptom(
            user_id=user["id"],
            symptom=symptom,
            severity=severity,
            duration=duration,
            notes=notes
        )
        
        return result
    
    @strawberry.mutation
    async def log_vital(
        self, 
        info: Info,
        vital_type: str,
        value: float,
        unit: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log a vital sign measurement"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        data_service = info.context["data_service"]
        
        result = await data_service.log_vital(
            user_id=user["id"],
            vital_type=vital_type,
            value=value,
            unit=unit,
            timestamp=timestamp
        )
        
        return result

# Subscription Type (for real-time updates)
@strawberry.type
class Subscription:
    """Real-time subscriptions for health data"""
    
    @strawberry.subscription
    async def health_insights(self, info: Info) -> RealTimeInsight:
        """Subscribe to real-time health insights"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        
        # This would be implemented with WebSocket or Server-Sent Events
        # For now, return a placeholder
        yield RealTimeInsight(
            id="placeholder",
            type="real_time",
            message="Real-time insights not yet implemented",
            priority="normal",
            timestamp=datetime.now(),
            actionable=False,
            data_source="placeholder"
        )

# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
