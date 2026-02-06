"""
Health Analytics API Router
Handles endpoints for health analytics and data analysis.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from ..models.health_metrics import MetricType
from ..services.health_analytics import HealthAnalyticsService

router = APIRouter(prefix="/analytics", tags=["health-analytics"])

@router.get("/trends", response_model=Dict[str, Any])
async def get_trends(
    metric_type: Optional[MetricType] = Query(None, description="Metric type to analyze"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get trend analysis for health metrics.
    
    - **metric_type**: Optional metric type to filter by
    - **days**: Number of days to analyze (1-365)
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        trends = await analytics_service.analyze_trends(
            user_id=current_user["id"],
            metric_type=metric_type,
            days=days
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/anomalies", response_model=Dict[str, Any])
async def get_anomalies(
    metric_type: Optional[MetricType] = Query(None, description="Metric type to analyze"),
    threshold: float = Query(2.0, ge=0.1, le=10.0, description="Anomaly detection threshold"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get anomaly detection results for health metrics.
    
    - **metric_type**: Optional metric type to filter by
    - **threshold**: Anomaly detection threshold (0.1-10.0)
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        anomalies = await analytics_service.detect_anomalies(
            user_id=current_user["id"],
            metric_type=metric_type,
            threshold=threshold
        )
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/correlations", response_model=Dict[str, Any])
async def get_correlations(
    metric_type1: MetricType = Query(..., description="First metric type"),
    metric_type2: MetricType = Query(..., description="Second metric type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get correlation analysis between two metric types.
    
    - **metric_type1**: First metric type for correlation
    - **metric_type2**: Second metric type for correlation
    - **days**: Number of days to analyze (1-365)
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        correlation = await analytics_service.analyze_correlation(
            user_id=current_user["id"],
            metric_type1=metric_type1,
            metric_type2=metric_type2,
            days=days
        )
        return correlation
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/patterns", response_model=Dict[str, Any])
async def get_patterns(
    metric_type: Optional[MetricType] = Query(None, description="Metric type to analyze"),
    pattern_type: str = Query("daily", description="Pattern type (daily, weekly, monthly)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get pattern recognition results for health metrics.
    
    - **metric_type**: Optional metric type to filter by
    - **pattern_type**: Type of pattern to detect (daily, weekly, monthly)
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        patterns = await analytics_service.recognize_patterns(
            user_id=current_user["id"],
            metric_type=metric_type,
            pattern_type=pattern_type
        )
        return patterns
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/predictions", response_model=Dict[str, Any])
async def get_predictions(
    metric_type: MetricType = Query(..., description="Metric type to predict"),
    days_ahead: int = Query(7, ge=1, le=30, description="Days to predict ahead"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get predictions for health metrics.
    
    - **metric_type**: Metric type to predict
    - **days_ahead**: Number of days to predict ahead (1-30)
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        predictions = await analytics_service.predict_metrics(
            user_id=current_user["id"],
            metric_type=metric_type,
            days_ahead=days_ahead
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive analytics summary for all metrics.
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        summary = await analytics_service.get_analytics_summary(
            user_id=current_user["id"]
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_recommendations(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get personalized health recommendations based on analytics.
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        recommendations = await analytics_service.generate_recommendations(
            user_id=current_user["id"]
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/goal-analysis", response_model=Dict[str, Any])
async def get_goal_analysis(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get analysis of progress towards health goals.
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        analysis = await analytics_service.analyze_goal_progress(
            user_id=current_user["id"]
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/export", response_model=Dict[str, Any])
async def export_analytics_data(
    format: str = Query("json", description="Export format (json, csv)"),
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Export analytics data in specified format.
    
    - **format**: Export format (json, csv)
    - **start_date**: Optional start date for export
    - **end_date**: Optional end date for export
    """
    try:
        analytics_service = HealthAnalyticsService(db)
        export_data = await analytics_service.export_analytics_data(
            user_id=current_user["id"],
            format=format,
            start_date=start_date,
            end_date=end_date
        )
        return export_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
