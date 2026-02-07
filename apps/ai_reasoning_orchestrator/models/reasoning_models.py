"""
Data models for AI Reasoning Orchestrator
Defines the structure for health queries, reasoning requests, and responses.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

class InsightType(str, Enum):
    """Types of health insights"""
    SYMPTOM_ANALYSIS = "symptom_analysis"
    TREND_DETECTION = "trend_detection"
    CORRELATION = "correlation"
    ANOMALY_DETECTION = "anomaly_detection"
    RECOMMENDATION = "recommendation"
    RISK_ASSESSMENT = "risk_assessment"
    MEDICATION_INTERACTION = "medication_interaction"
    LIFESTYLE_OPTIMIZATION = "lifestyle_optimization"

class EvidenceSource(str, Enum):
    """Sources of evidence for reasoning"""
    WEARABLE_DATA = "wearable_data"
    MEDICAL_RECORDS = "medical_records"
    LAB_RESULTS = "lab_results"
    MEDICAL_LITERATURE = "medical_literature"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    USER_REPORTED = "user_reported"
    CLINICAL_GUIDELINES = "clinical_guidelines"
    DRUG_DATABASE = "drug_database"

class ConfidenceLevel(str, Enum):
    """Confidence levels for reasoning results"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"

class ReasoningType(str, Enum):
    """Types of reasoning to perform"""
    SYMPTOM_ANALYSIS = "symptom_analysis"
    DAILY_SUMMARY = "daily_summary"
    DOCTOR_REPORT = "doctor_report"
    REAL_TIME_INSIGHTS = "real_time_insights"
    TREND_ANALYSIS = "trend_analysis"
    CORRELATION_ANALYSIS = "correlation_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    MEDICATION_REVIEW = "medication_review"
    DASHBOARD_SUMMARY = "dashboard_summary"

class HealthQuery(BaseModel):
    """Natural language health query"""
    question: str = Field(..., description="Natural language health question")
    time_window: Optional[str] = Field("24h", description="Time window for analysis")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        if len(v) > 1000:
            raise ValueError("Question too long (max 1000 characters)")
        return v.strip()

class ReasoningRequest(BaseModel):
    """Request for AI reasoning about health"""
    query: str = Field(..., description="Health query or question")
    reasoning_type: ReasoningType = Field(ReasoningType.SYMPTOM_ANALYSIS, description="Type of reasoning to perform")
    time_window: str = Field("24h", description="Time window for data analysis")
    data_types: List[str] = Field(
        default=["vitals", "symptoms", "medications", "nutrition"],
        description="Types of data to include in analysis"
    )
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    priority: Optional[str] = Field("normal", description="Request priority")

    @validator('data_types')
    def validate_data_types(cls, v):
        valid_types = [
            "vitals", "symptoms", "medications", "nutrition", 
            "sleep", "activity", "lab_results", "medical_records",
            "device_data", "voice_input", "genomics"
        ]
        for data_type in v:
            if data_type not in valid_types:
                raise ValueError(f"Invalid data type: {data_type}")
        return v

class Evidence(BaseModel):
    """Evidence supporting reasoning"""
    source: EvidenceSource = Field(..., description="Source of evidence")
    description: str = Field(..., description="Description of evidence")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Confidence in evidence")
    timestamp: Optional[datetime] = Field(None, description="When evidence was collected")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class Insight(BaseModel):
    """Health insight"""
    type: InsightType = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    severity: Optional[str] = Field(None, description="Severity level")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Confidence level")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    actionable: bool = Field(True, description="Whether insight is actionable")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When insight was generated")

class Recommendation(BaseModel):
    """Health recommendation"""
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    category: str = Field(..., description="Category of recommendation")
    priority: str = Field("medium", description="Priority level")
    actionable: bool = Field(True, description="Whether recommendation is actionable")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    follow_up: Optional[str] = Field(None, description="Follow-up action required")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When recommendation was generated")

class ReasoningResponse(BaseModel):
    """Response from AI reasoning"""
    query: str = Field(..., description="Original query")
    reasoning: str = Field(..., description="Detailed reasoning explanation")
    insights: List[Insight] = Field(default_factory=list, description="Generated insights")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Generated recommendations")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Overall confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When response was generated")

class UserDataSummary(BaseModel):
    """Summary of user data for reasoning"""
    user_id: str = Field(..., description="User ID")
    time_window: str = Field(..., description="Time window analyzed")
    vitals_count: int = Field(0, description="Number of vital signs records")
    symptoms_count: int = Field(0, description="Number of symptoms recorded")
    medications_count: int = Field(0, description="Number of medications")
    nutrition_count: int = Field(0, description="Number of nutrition records")
    sleep_count: int = Field(0, description="Number of sleep records")
    activity_count: int = Field(0, description="Number of activity records")
    lab_results_count: int = Field(0, description="Number of lab results")
    data_quality_score: float = Field(0.0, description="Overall data quality score")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last data update")

class KnowledgeContext(BaseModel):
    """Medical knowledge context for reasoning"""
    relevant_conditions: List[str] = Field(default_factory=list, description="Relevant medical conditions")
    drug_interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant drug interactions")
    clinical_guidelines: List[str] = Field(default_factory=list, description="Relevant clinical guidelines")
    medical_literature: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant medical literature")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    evidence_level: str = Field("moderate", description="Level of evidence available")

class RealTimeInsight(BaseModel):
    """Real-time health insight"""
    type: str = Field(..., description="Type of insight")
    message: str = Field(..., description="Insight message")
    priority: str = Field("normal", description="Priority level")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When insight was generated")
    actionable: bool = Field(True, description="Whether insight requires action")
    data_source: str = Field(..., description="Source of data")

class DoctorReport(BaseModel):
    """Comprehensive doctor mode report"""
    patient_id: str = Field(..., description="Patient ID")
    report_date: datetime = Field(default_factory=datetime.utcnow, description="Report date")
    time_period: str = Field(..., description="Time period covered")
    summary: str = Field(..., description="Executive summary")
    key_insights: List[Insight] = Field(default_factory=list, description="Key insights")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Recommendations")
    trends: List[Dict[str, Any]] = Field(default_factory=list, description="Health trends")
    anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="Anomalies detected")
    data_quality: Dict[str, Any] = Field(default_factory=dict, description="Data quality assessment")
    confidence_score: float = Field(..., description="Overall confidence score")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
