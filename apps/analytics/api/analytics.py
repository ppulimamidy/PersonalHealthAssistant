"""
Enhanced Analytics API

API endpoints for advanced analytics processing, real-time data processing,
and comprehensive health insights for the Personal Health Assistant.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse

from common.utils.logging import get_logger
from models.analytics_models import (
    AnalyticsType, TimeRange, AnalyticsRequest, AnalyticsResponse,
    PopulationHealthMetrics, ClinicalDecisionSupport, PerformanceMetrics,
    PredictiveModel, RiskAssessment, RealTimeDataPoint
)
from services.analytics_service import AnalyticsService

logger = get_logger(__name__)
router = APIRouter()

# Global analytics service instance - will be set by main.py
analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")
    return analytics_service


def set_analytics_service(service: AnalyticsService):
    """Set analytics service instance (called from main.py)"""
    global analytics_service
    analytics_service = service


@router.get("/health", response_model=dict)
async def get_analytics_health(request: Request):
    """Get analytics service health status."""
    try:
        logger.info("Getting analytics service health")
        
        health_status = {
            "status": "healthy",
            "service": "analytics-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "capabilities": [
                "patient_analytics",
                "population_analytics", 
                "clinical_analytics",
                "performance_analytics",
                "predictive_analytics",
                "trend_analysis",
                "correlation_analysis",
                "risk_assessment",
                "real_time_processing",
                "anomaly_detection",
                "seasonality_analysis",
                "breakpoint_detection",
                "forecasting",
                "clinical_decision_support"
            ],
            "real_time_processing": {
                "active_streams": len(analytics_service.real_time_processor.data_streams) if analytics_service else 0,
                "processing_enabled": analytics_service.real_time_processor.is_running if analytics_service else False
            }
        }
        
        logger.info("Analytics service health check completed")
        return health_status
        
    except Exception as e:
        logger.error(f"Analytics service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "analytics-service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/capabilities", response_model=dict)
async def get_analytics_capabilities(request: Request):
    """Get analytics service capabilities."""
    try:
        logger.info("Getting analytics service capabilities")
        
        capabilities = {
            "analytics_types": [
                {
                    "type": "patient",
                    "description": "Patient-specific health analytics with advanced algorithms",
                    "endpoints": [
                        "/patient/{patient_id}/health",
                        "/patient/{patient_id}/trends",
                        "/patient/{patient_id}/correlations", 
                        "/patient/{patient_id}/risk-assessment",
                        "/patient/{patient_id}/predictive-model"
                    ],
                    "features": [
                        "Real-time trend analysis",
                        "Anomaly detection",
                        "Risk assessment",
                        "Predictive modeling",
                        "Multi-source data integration"
                    ]
                },
                {
                    "type": "population", 
                    "description": "Population-level health analytics",
                    "endpoints": ["/population/health"],
                    "features": [
                        "Demographic analysis",
                        "Disease prevalence",
                        "Risk distribution",
                        "Trend analysis"
                    ]
                },
                {
                    "type": "clinical",
                    "description": "Clinical decision support analytics",
                    "endpoints": ["/clinical/decision-support"],
                    "features": [
                        "Differential diagnosis",
                        "Test recommendations",
                        "Urgency assessment",
                        "Risk stratification"
                    ]
                },
                {
                    "type": "performance",
                    "description": "Platform performance analytics", 
                    "endpoints": ["/performance/metrics"],
                    "features": [
                        "Service uptime",
                        "Response times",
                        "User activity",
                        "Data processing volume"
                    ]
                },
                {
                    "type": "predictive",
                    "description": "Predictive health analytics",
                    "endpoints": ["/predictive/{patient_id}"],
                    "features": [
                        "Linear regression models",
                        "Time series forecasting",
                        "Risk prediction",
                        "Trend forecasting"
                    ]
                }
            ],
            "data_sources": [
                "health_tracking",
                "medical_records", 
                "device_data",
                "nutrition",
                "voice_input",
                "ai_insights",
                "consent_audit",
                "user_profile"
            ],
            "time_ranges": [
                "1_hour",
                "1_day", 
                "1_week",
                "1_month",
                "3_months",
                "6_months",
                "1_year",
                "custom"
            ],
            "analysis_types": [
                "trend_analysis",
                "correlation_analysis",
                "risk_assessment",
                "predictive_modeling",
                "population_analysis",
                "clinical_decision_support",
                "anomaly_detection",
                "seasonality_analysis",
                "breakpoint_detection",
                "forecasting"
            ],
            "algorithms": [
                "Linear Regression",
                "Mann-Kendall Trend Test",
                "Sen's Slope Estimator",
                "Z-score Anomaly Detection",
                "FFT Seasonality Detection",
                "Structural Breakpoint Detection",
                "Exponential Smoothing Forecasting",
                "Pearson Correlation",
                "Spearman Correlation",
                "Risk Factor Analysis"
            ],
            "real_time_features": [
                "Stream processing",
                "Real-time anomaly detection",
                "Live trend analysis",
                "Alert threshold monitoring",
                "Instant data point processing"
            ]
        }
        
        logger.info("Analytics service capabilities retrieved")
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get analytics capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.post("/patient/{patient_id}/health", response_model=AnalyticsResponse)
async def analyze_patient_health(
    patient_id: UUID = Path(..., description="Patient ID"),
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for analysis"),
    request: Request = None,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Perform comprehensive patient health analysis."""
    try:
        logger.info(f"Starting patient health analysis for {patient_id}")
        
        result = await analytics_service.analyze_patient_health(patient_id, time_range)
        
        logger.info(f"Patient health analysis completed for {patient_id}")
        return result
        
    except Exception as e:
        logger.error(f"Patient health analysis failed for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/patient/{patient_id}/trends", response_model=dict)
async def get_patient_trends(
    patient_id: UUID = Path(..., description="Patient ID"),
    metric: str = Query(..., description="Metric to analyze"),
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get trend analysis for a specific patient metric."""
    try:
        logger.info(f"Getting trends for patient {patient_id}, metric: {metric}")
        
        # Collect data
        data = await analytics_service.collect_data_from_services(patient_id, time_range)
        
        # Perform trend analysis
        if data['health_tracking']:
            trend = await analytics_service.analytics_engine.perform_trend_analysis(
                data['health_tracking'], metric
            )
            return {
                "patient_id": patient_id,
                "metric": metric,
                "time_range": time_range,
                "trend": trend,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "patient_id": patient_id,
                "metric": metric,
                "time_range": time_range,
                "trend": None,
                "message": "No data available for trend analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Trend analysis failed for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/patient/{patient_id}/correlations", response_model=dict)
async def get_patient_correlations(
    patient_id: UUID = Path(..., description="Patient ID"),
    metric1: str = Query(..., description="First metric"),
    metric2: str = Query(..., description="Second metric"),
    time_range: TimeRange = Query(TimeRange.MONTH, description="Time range for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get correlation analysis between two metrics for a patient."""
    try:
        logger.info(f"Getting correlations for patient {patient_id}: {metric1} vs {metric2}")
        
        # Collect data
        data = await analytics_service.collect_data_from_services(patient_id, time_range)
        
        # Perform correlation analysis
        if data['health_tracking'] and data['nutrition']:
            correlation = await analytics_service.analytics_engine.perform_correlation_analysis(
                data['health_tracking'], data['nutrition'], metric1, metric2
            )
            return {
                "patient_id": patient_id,
                "metric1": metric1,
                "metric2": metric2,
                "time_range": time_range,
                "correlation": correlation,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "patient_id": patient_id,
                "metric1": metric1,
                "metric2": metric2,
                "time_range": time_range,
                "correlation": None,
                "message": "Insufficient data for correlation analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Correlation analysis failed for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")


@router.get("/patient/{patient_id}/risk-assessment", response_model=RiskAssessment)
async def get_patient_risk_assessment(
    patient_id: UUID = Path(..., description="Patient ID"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive risk assessment for a patient."""
    try:
        logger.info(f"Getting risk assessment for patient {patient_id}")
        
        # Collect data
        data = await analytics_service.collect_data_from_services(patient_id, TimeRange.MONTH)
        
        # Perform risk assessment
        patient_data = analytics_service._aggregate_patient_data(data)
        risk_assessment = await analytics_service.analytics_engine.perform_risk_assessment(patient_data)
        
        logger.info(f"Risk assessment completed for {patient_id}")
        return risk_assessment
        
    except Exception as e:
        logger.error(f"Risk assessment failed for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.post("/patient/{patient_id}/predictive-model", response_model=PredictiveModel)
async def create_predictive_model(
    patient_id: UUID = Path(..., description="Patient ID"),
    target_metric: str = Body(..., embed=True, description="Target metric for prediction"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Create predictive model for a patient."""
    try:
        logger.info(f"Creating predictive model for patient {patient_id}, metric: {target_metric}")
        
        model = await analytics_service.create_predictive_model(patient_id, target_metric)
        
        logger.info(f"Predictive model created for {patient_id}")
        return model
        
    except Exception as e:
        logger.error(f"Predictive model creation failed for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Model creation failed: {str(e)}")


@router.post("/population/health", response_model=PopulationHealthMetrics)
async def analyze_population_health(
    filters: Dict[str, Any] = Body(default={}, description="Population filters"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Perform population health analysis."""
    try:
        logger.info("Starting population health analysis")
        
        result = await analytics_service.analyze_population_health(filters)
        
        logger.info("Population health analysis completed")
        return result
        
    except Exception as e:
        logger.error(f"Population health analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Population analysis failed: {str(e)}")


@router.post("/clinical/decision-support", response_model=ClinicalDecisionSupport)
async def provide_clinical_decision_support(
    user_id: UUID = Body(..., embed=True, description="User ID"),
    symptoms: List[str] = Body(..., embed=True, description="List of symptoms"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Provide clinical decision support."""
    try:
        logger.info(f"Providing clinical decision support for user {user_id}")
        
        result = await analytics_service.provide_clinical_decision_support(user_id, symptoms)
        
        logger.info(f"Clinical decision support completed for {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Clinical decision support failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Clinical decision support failed: {str(e)}")


@router.get("/performance/metrics", response_model=PerformanceMetrics)
async def get_performance_metrics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get platform performance metrics."""
    try:
        logger.info("Getting performance metrics")
        
        result = await analytics_service.analyze_performance_metrics()
        
        logger.info("Performance metrics retrieved")
        return result
        
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")


@router.post("/real-time/data", response_model=dict)
async def add_real_time_data(
    stream_id: str = Body(..., embed=True, description="Stream ID"),
    value: float = Body(..., embed=True, description="Data value"),
    metric: str = Body(..., embed=True, description="Metric name"),
    user_id: UUID = Body(..., embed=True, description="User ID"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Add real-time data point for processing."""
    try:
        logger.info(f"Adding real-time data point for stream {stream_id}")
        
        await analytics_service.add_real_time_data(stream_id, value, metric, user_id)
        
        return {
            "message": "Real-time data point added successfully",
            "stream_id": stream_id,
            "value": value,
            "metric": metric,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to add real-time data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add real-time data: {str(e)}")


@router.get("/real-time/streams", response_model=dict)
async def get_real_time_streams(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get information about active real-time streams."""
    try:
        processor = analytics_service.real_time_processor
        
        streams_info = {}
        for stream_id, data_points in processor.data_streams.items():
            streams_info[stream_id] = {
                "data_points_count": len(data_points),
                "latest_value": data_points[-1].value if data_points else None,
                "latest_timestamp": data_points[-1].timestamp.isoformat() if data_points else None,
                "metric": data_points[-1].metric if data_points else None,
                "user_id": data_points[-1].user_id if data_points else None
            }
            
        return {
            "active_streams": len(streams_info),
            "processing_enabled": processor.is_running,
            "streams": streams_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time streams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get streams: {str(e)}")


@router.post("/real-time/alerts/thresholds", response_model=dict)
async def set_alert_thresholds(
    stream_id: str = Body(..., embed=True, description="Stream ID"),
    thresholds: Dict[str, float] = Body(..., embed=True, description="Alert thresholds"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Set alert thresholds for a real-time stream."""
    try:
        logger.info(f"Setting alert thresholds for stream {stream_id}")
        
        analytics_service.real_time_processor.alert_thresholds[stream_id] = thresholds
        
        return {
            "message": "Alert thresholds set successfully",
            "stream_id": stream_id,
            "thresholds": thresholds,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to set alert thresholds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set thresholds: {str(e)}")


@router.get("/test", response_model=dict)
async def test_analytics(request: Request):
    """Test endpoint for analytics service."""
    return {
        "message": "Analytics service is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "analytics-service",
        "features": [
            "Advanced analytics algorithms",
            "Real-time data processing",
            "Multi-source data integration",
            "Predictive modeling",
            "Clinical decision support"
        ]
    } 