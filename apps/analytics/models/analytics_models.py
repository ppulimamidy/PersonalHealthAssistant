"""
Analytics Models

Pydantic models for analytics requests, responses, and data structures.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator


class AnalyticsType(str, Enum):
    """Types of analytics."""
    PATIENT = "patient"
    POPULATION = "population"
    CLINICAL = "clinical"
    PERFORMANCE = "performance"
    PREDICTIVE = "predictive"
    TREND = "trend"
    COMPARATIVE = "comparative"
    CORRELATION = "correlation"


class TimeRange(str, Enum):
    """Time ranges for analytics."""
    HOUR = "1_hour"
    DAY = "1_day"
    WEEK = "1_week"
    MONTH = "1_month"
    QUARTER = "3_months"
    YEAR = "1_year"
    CUSTOM = "custom"


class MetricType(str, Enum):
    """Types of metrics."""
    COUNT = "count"
    AVERAGE = "average"
    SUM = "sum"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    TREND = "trend"
    CORRELATION = "correlation"
    PREDICTION = "prediction"


class DataSource(str, Enum):
    """Data sources for analytics."""
    HEALTH_TRACKING = "health_tracking"
    MEDICAL_RECORDS = "medical_records"
    DEVICE_DATA = "device_data"
    NUTRITION = "nutrition"
    VOICE_INPUT = "voice_input"
    AI_INSIGHTS = "ai_insights"
    CONSENT_AUDIT = "consent_audit"
    USER_PROFILE = "user_profile"
    AGGREGATED = "aggregated"


class RiskLevel(str, Enum):
    """Risk levels for health analytics."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend directions."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"


class HealthMetric(BaseModel):
    """A health metric measurement."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    
    # Metadata
    timestamp: datetime = Field(..., description="Measurement timestamp")
    source: DataSource = Field(..., description="Data source")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level")
    
    # Context
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    category: Optional[str] = Field(None, description="Metric category")
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TrendAnalysis(BaseModel):
    """Analysis of trends in health data."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    metric_name: str = Field(..., description="Metric name")
    
    # Trend information
    direction: TrendDirection = Field(..., description="Trend direction")
    slope: float = Field(..., description="Trend slope")
    r_squared: float = Field(..., ge=0.0, le=1.0, description="R-squared value")
    
    # Time period
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    data_points: int = Field(..., description="Number of data points")
    
    # Analysis
    significance: str = Field(..., description="Statistical significance")
    confidence_interval: List[float] = Field(..., description="Confidence interval")
    
    # Context
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    category: Optional[str] = Field(None, description="Metric category")
    
    # Additional insights
    insights: List[str] = Field(default_factory=list, description="Trend insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class CorrelationAnalysis(BaseModel):
    """Analysis of correlations between health metrics."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Correlation details
    metric1: str = Field(..., description="First metric")
    metric2: str = Field(..., description="Second metric")
    correlation_coefficient: float = Field(..., ge=-1.0, le=1.0, description="Correlation coefficient")
    p_value: float = Field(..., ge=0.0, le=1.0, description="P-value")
    
    # Strength and significance
    strength: str = Field(..., description="Correlation strength")
    significance: str = Field(..., description="Statistical significance")
    
    # Time period
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    data_points: int = Field(..., description="Number of data points")
    
    # Context
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    
    # Additional insights
    insights: List[str] = Field(default_factory=list, description="Correlation insights")
    clinical_relevance: str = Field(..., description="Clinical relevance")


class RiskAssessment(BaseModel):
    """Health risk assessment based on analytics."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Risk assessment
    overall_risk: RiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Risk score (0-10)")
    
    # Risk factors
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    risk_probabilities: Dict[str, float] = Field(default_factory=dict, description="Risk probabilities")
    
    # Time horizons
    short_term_risk: RiskLevel = Field(..., description="Short-term risk (30 days)")
    medium_term_risk: RiskLevel = Field(..., description="Medium-term risk (6 months)")
    long_term_risk: RiskLevel = Field(..., description="Long-term risk (1 year)")
    
    # Context
    patient_id: str = Field(..., description="Patient identifier")
    assessment_date: datetime = Field(default_factory=datetime.utcnow, description="Assessment date")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Risk mitigation recommendations")
    monitoring_requirements: List[str] = Field(default_factory=list, description="Monitoring requirements")


class PredictiveModel(BaseModel):
    """Predictive model for health outcomes."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Model details
    model_name: str = Field(..., description="Model name")
    outcome: str = Field(..., description="Predicted outcome")
    prediction_horizon: str = Field(..., description="Prediction horizon")
    
    # Prediction results
    probability: float = Field(..., ge=0.0, le=1.0, description="Prediction probability")
    confidence_interval: List[float] = Field(..., description="Confidence interval")
    
    # Model performance
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Model accuracy")
    precision: float = Field(..., ge=0.0, le=1.0, description="Model precision")
    recall: float = Field(..., ge=0.0, le=1.0, description="Model recall")
    
    # Input features
    input_features: List[str] = Field(default_factory=list, description="Input features")
    feature_importance: Dict[str, float] = Field(default_factory=dict, description="Feature importance")
    
    # Context
    patient_id: str = Field(..., description="Patient identifier")
    prediction_date: datetime = Field(default_factory=datetime.utcnow, description="Prediction date")
    
    # Additional information
    model_version: str = Field(..., description="Model version")
    training_data_size: int = Field(..., description="Training data size")
    last_updated: datetime = Field(..., description="Last model update")


class PopulationHealthMetrics(BaseModel):
    """Population-level health metrics."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Population details
    population_size: int = Field(..., description="Population size")
    age_group: Optional[str] = Field(None, description="Age group")
    gender: Optional[str] = Field(None, description="Gender")
    region: Optional[str] = Field(None, description="Geographic region")
    
    # Health metrics
    average_bmi: float = Field(..., description="Average BMI")
    average_blood_pressure: Dict[str, float] = Field(..., description="Average blood pressure")
    average_heart_rate: float = Field(..., description="Average heart rate")
    average_steps: float = Field(..., description="Average daily steps")
    
    # Risk distribution
    risk_distribution: Dict[RiskLevel, int] = Field(..., description="Risk level distribution")
    chronic_conditions: Dict[str, int] = Field(..., description="Chronic conditions prevalence")
    
    # Time period
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    
    # Additional metrics
    health_score: float = Field(..., ge=0.0, le=100.0, description="Population health score")
    wellness_index: float = Field(..., ge=0.0, le=100.0, description="Wellness index")
    
    # Insights
    insights: List[str] = Field(default_factory=list, description="Population insights")
    recommendations: List[str] = Field(default_factory=list, description="Population recommendations")


class ClinicalDecisionSupport(BaseModel):
    """Clinical decision support based on analytics."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Clinical context
    patient_id: str = Field(..., description="Patient identifier")
    clinical_scenario: str = Field(..., description="Clinical scenario")
    
    # Evidence-based recommendations
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    evidence_level: str = Field(..., description="Level of evidence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    
    # Risk assessment
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    contraindications: List[str] = Field(default_factory=list, description="Contraindications")
    
    # Alternative options
    alternatives: List[str] = Field(default_factory=list, description="Alternative approaches")
    cost_benefit: Dict[str, Any] = Field(default_factory=dict, description="Cost-benefit analysis")
    
    # Guidelines and protocols
    guidelines: List[str] = Field(default_factory=list, description="Relevant guidelines")
    protocols: List[str] = Field(default_factory=list, description="Clinical protocols")
    
    # Timestamp
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class PerformanceMetrics(BaseModel):
    """Platform performance metrics."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Service performance
    service_name: str = Field(..., description="Service name")
    response_time: float = Field(..., description="Average response time (ms)")
    throughput: float = Field(..., description="Requests per second")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate")
    availability: float = Field(..., ge=0.0, le=1.0, description="Service availability")
    
    # Resource utilization
    cpu_usage: float = Field(..., ge=0.0, le=1.0, description="CPU usage")
    memory_usage: float = Field(..., ge=0.0, le=1.0, description="Memory usage")
    disk_usage: float = Field(..., ge=0.0, le=1.0, description="Disk usage")
    
    # Database performance
    db_connection_pool: int = Field(..., description="Database connection pool size")
    db_query_time: float = Field(..., description="Average database query time")
    db_connections_active: int = Field(..., description="Active database connections")
    
    # Time period
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    
    # Additional metrics
    user_sessions: int = Field(..., description="Active user sessions")
    api_calls: int = Field(..., description="Total API calls")
    data_processed: int = Field(..., description="Data processed (MB)")


class AnalyticsRequest(BaseModel):
    """Request for analytics processing."""
    
    analytics_type: AnalyticsType = Field(..., description="Type of analytics")
    time_range: TimeRange = Field(..., description="Time range")
    
    # Optional parameters
    start_date: Optional[datetime] = Field(None, description="Start date (for custom range)")
    end_date: Optional[datetime] = Field(None, description="End date (for custom range)")
    
    # Filters
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to analyze")
    data_sources: Optional[List[DataSource]] = Field(None, description="Data sources to include")
    
    # Analysis options
    include_trends: bool = Field(True, description="Include trend analysis")
    include_correlations: bool = Field(True, description="Include correlation analysis")
    include_predictions: bool = Field(False, description="Include predictive analytics")
    
    # Context
    user_id: str = Field(..., description="User identifier")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request identifier")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")


class AnalyticsResponse(BaseModel):
    """Response from analytics processing."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    request_id: str = Field(..., description="Original request identifier")
    
    # Analytics results
    analytics_type: AnalyticsType = Field(..., description="Type of analytics performed")
    time_range: TimeRange = Field(..., description="Time range analyzed")
    
    # Data summary
    data_points: int = Field(..., description="Number of data points analyzed")
    data_sources: List[DataSource] = Field(..., description="Data sources used")
    
    # Results by type
    trends: Optional[List[TrendAnalysis]] = Field(None, description="Trend analysis results")
    correlations: Optional[List[CorrelationAnalysis]] = Field(None, description="Correlation analysis results")
    predictions: Optional[List[PredictiveModel]] = Field(None, description="Predictive model results")
    risk_assessments: Optional[List[RiskAssessment]] = Field(None, description="Risk assessment results")
    
    # Population metrics (if applicable)
    population_metrics: Optional[PopulationHealthMetrics] = Field(None, description="Population health metrics")
    
    # Clinical decision support (if applicable)
    clinical_support: Optional[ClinicalDecisionSupport] = Field(None, description="Clinical decision support")
    
    # Performance metrics (if applicable)
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    
    # Processing information
    processing_time: float = Field(..., description="Processing time in seconds")
    models_used: List[str] = Field(default_factory=list, description="Models used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    
    # Insights and recommendations
    insights: List[str] = Field(default_factory=list, description="Key insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    
    # Warnings and limitations
    warnings: List[str] = Field(default_factory=list, description="Important warnings")
    limitations: List[str] = Field(default_factory=list, description="Analysis limitations")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class AnalyticsDashboard(BaseModel):
    """Analytics dashboard configuration and data."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Dashboard name")
    description: str = Field(..., description="Dashboard description")
    
    # Dashboard configuration
    widgets: List[Dict[str, Any]] = Field(default_factory=list, description="Dashboard widgets")
    layout: Dict[str, Any] = Field(default_factory=dict, description="Widget layout")
    
    # Access control
    user_id: str = Field(..., description="Dashboard owner")
    is_public: bool = Field(False, description="Whether dashboard is public")
    shared_with: List[str] = Field(default_factory=list, description="Users with access")
    
    # Data configuration
    refresh_interval: int = Field(300, description="Refresh interval in seconds")
    data_sources: List[DataSource] = Field(default_factory=list, description="Data sources")
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class AnalyticsExport(BaseModel):
    """Analytics data export configuration."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    
    # Export configuration
    format: str = Field(..., description="Export format (csv, json, excel, pdf)")
    analytics_type: AnalyticsType = Field(..., description="Type of analytics to export")
    time_range: TimeRange = Field(..., description="Time range")
    
    # Filters
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics")
    
    # Export options
    include_charts: bool = Field(True, description="Include charts and visualizations")
    include_insights: bool = Field(True, description="Include insights and recommendations")
    include_raw_data: bool = Field(False, description="Include raw data")
    
    # User context
    user_id: str = Field(..., description="User identifier")
    
    # Status
    status: str = Field("pending", description="Export status")
    file_url: Optional[str] = Field(None, description="Download URL")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    # Timestamps
    requested_at: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class RealTimeDataPoint(BaseModel):
    """Real-time data point for streaming analytics."""
    
    stream_id: str = Field(..., description="Stream identifier")
    value: float = Field(..., description="Data value")
    metric: str = Field(..., description="Metric name")
    user_id: Union[str, UUID] = Field(..., description="User identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data timestamp")
    
    # Additional metadata
    source: Optional[DataSource] = Field(None, description="Data source")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Data confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata") 