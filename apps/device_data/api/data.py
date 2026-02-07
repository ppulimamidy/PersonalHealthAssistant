"""
Data API Endpoints
Handles device data point management and analytics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from pydantic import BaseModel

from common.database.connection import get_async_db
from common.middleware.rate_limiter import rate_limit
from common.utils.logging import get_logger
from common.config.settings import get_settings

from ..models.data_point import (
    DataPointCreate, DataPointUpdate, DataPointResponse, DataPointSummary,
    DataPointBatch, DataPointQuery, DataPointAggregation, DataPointStatistics,
    DataType, DataQuality, DataSource
)
from ..services.data_service import DataService, get_data_service

logger = get_logger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


class UserStub(BaseModel):
    """Stub user model for device data service"""
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: Optional[str] = None


async def get_current_user(request: Request) -> UserStub:
    """Get current user from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        token = auth_header.split(" ")[1]
        settings = get_settings()
        
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return UserStub(
            id=UUID(user_id),
            email=email
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/points", response_model=DataPointResponse, status_code=status.HTTP_201_CREATED)
async def create_data_point(
    data_point: DataPointCreate,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new data point from a device.
    
    - **device_id**: Device that generated this data
    - **data_type**: Type of health data
    - **value**: Data value
    - **unit**: Unit of measurement
    - **timestamp**: When the data was recorded
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        db_data_point = await data_service.create_data_point(user_id, data_point)
        
        logger.info(f"Data point created for user {user_id}: {db_data_point.id}")
        return DataPointResponse.from_orm(db_data_point)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data point: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create data point"
        )


@router.post("/points/batch", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_batch_data_points(
    batch: DataPointBatch,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create multiple data points in a batch operation.
    
    - **device_id**: Device that generated these data points
    - **data_points**: List of data points to create
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        result = await data_service.create_batch_data_points(user_id, batch)
        
        logger.info(f"Batch data points created for user {user_id}: {result['created_count']} successful")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch data points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create batch data points"
        )


@router.get("/points", response_model=Dict[str, Any])
async def get_data_points(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    data_type: Optional[DataType] = Query(None, description="Filter by data type"),
    start_date: Optional[datetime] = Query(None, description="Start date for data range"),
    end_date: Optional[datetime] = Query(None, description="End date for data range"),
    quality: Optional[DataQuality] = Query(None, description="Filter by data quality"),
    is_anomaly: Optional[bool] = Query(None, description="Filter by anomaly status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get data points with filtering and pagination.
    
    - **device_id**: Filter by specific device
    - **data_type**: Filter by data type
    - **start_date**: Start of date range
    - **end_date**: End of date range
    - **quality**: Filter by data quality
    - **is_anomaly**: Filter by anomaly status
    - **limit**: Maximum results per page
    - **offset**: Results to skip
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        query = DataPointQuery(
            device_id=device_id,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date,
            quality=quality,
            is_anomaly=is_anomaly,
            limit=limit,
            offset=offset
        )
        
        data_points, total_count = await data_service.get_data_points(user_id, query)
        
        return {
            "data_points": [DataPointSummary.from_orm(point) for point in data_points],
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting data points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data points"
        )


@router.get("/points/{data_point_id}", response_model=DataPointResponse)
async def get_data_point(
    data_point_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific data point by ID.
    
    - **data_point_id**: Unique data point identifier
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        data_point = await data_service.get_data_point(data_point_id, user_id)
        
        return DataPointResponse.from_orm(data_point)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data point {data_point_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data point"
        )


@router.put("/points/{data_point_id}", response_model=DataPointResponse)
async def update_data_point(
    data_point_id: UUID,
    data_point: DataPointUpdate,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update a data point.
    
    - **data_point_id**: Unique data point identifier
    - **data_point**: Updated data point information
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        updated_point = await data_service.update_data_point(data_point_id, user_id, data_point)
        
        logger.info(f"Data point {data_point_id} updated for user {user_id}")
        return DataPointResponse.from_orm(updated_point)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating data point {data_point_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update data point"
        )


@router.delete("/points/{data_point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_point(
    data_point_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a data point.
    
    - **data_point_id**: Unique data point identifier
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        await data_service.delete_data_point(data_point_id, user_id)
        
        logger.info(f"Data point {data_point_id} deleted for user {user_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting data point {data_point_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete data point"
        )


@router.get("/aggregation", response_model=List[DataPointAggregation])
async def get_data_aggregation(
    data_type: DataType = Query(..., description="Data type to aggregate"),
    start_date: datetime = Query(..., description="Start date for aggregation"),
    end_date: datetime = Query(..., description="End date for aggregation"),
    aggregation_period: str = Query("day", description="Aggregation period (hour, day, week, month)"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get aggregated data points for analysis.
    
    - **data_type**: Type of data to aggregate
    - **start_date**: Start of aggregation period
    - **end_date**: End of aggregation period
    - **aggregation_period**: Time period for aggregation
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        aggregations = await data_service.get_data_aggregation(
            user_id, data_type, start_date, end_date, aggregation_period
        )
        
        return aggregations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data aggregation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data aggregation"
        )


@router.get("/statistics", response_model=DataPointStatistics)
async def get_data_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get comprehensive data statistics.
    
    - **start_date**: Start of statistics period
    - **end_date**: End of statistics period
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        statistics = await data_service.get_data_statistics(user_id, start_date, end_date)
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting data statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data statistics"
        )


@router.post("/anomalies/detect", response_model=Dict[str, Any])
async def detect_anomalies(
    data_type: Optional[DataType] = Query(None, description="Data type to analyze for anomalies"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Detect anomalies in data points.
    
    - **data_type**: Optional data type to analyze (if not provided, analyzes all types)
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        anomalies = await data_service.detect_anomalies(user_id, data_type)
        
        logger.info(f"Anomaly detection completed for user {user_id}: {anomalies['anomaly_count']} anomalies found")
        return anomalies
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect anomalies"
        )


@router.get("/types/supported", response_model=List[Dict[str, str]])
async def get_supported_data_types():
    """
    Get list of supported data types.
    
    Returns all available data types that can be collected from devices.
    """
    try:
        data_types = [
            {"value": data_type.value, "label": data_type.value.replace("_", " ").title()}
            for data_type in DataType
        ]
        
        return data_types
        
    except Exception as e:
        logger.error(f"Error getting data types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data types"
        )


@router.get("/quality-levels", response_model=List[Dict[str, str]])
async def get_data_quality_levels():
    """
    Get list of data quality levels.
    
    Returns all available data quality indicators.
    """
    try:
        quality_levels = [
            {"value": quality.value, "label": quality.value.replace("_", " ").title()}
            for quality in DataQuality
        ]
        
        return quality_levels
        
    except Exception as e:
        logger.error(f"Error getting quality levels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quality levels"
        )


@router.get("/recent/{data_type}", response_model=List[DataPointSummary])
async def get_recent_data(
    data_type: DataType,
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of recent data points"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get recent data points for a specific data type.
    
    - **data_type**: Type of data to retrieve
    - **limit**: Number of recent data points to return
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        query = DataPointQuery(
            data_type=data_type,
            limit=limit,
            offset=0
        )
        
        data_points, _ = await data_service.get_data_points(user_id, query)
        
        return [DataPointSummary.from_orm(point) for point in data_points]
        
    except Exception as e:
        logger.error(f"Error getting recent data for {data_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent data"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_data_summary(
    device_id: Optional[UUID] = Query(None, description="Filter by device ID"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get overall data summary for the user or specific device.
    
    Returns summary statistics of all data points.
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        if device_id:
            # Get summary for specific device
            summary = await data_service.get_device_data_summary(user_id, device_id)
        else:
            # Get summary for all user data
            summary = await data_service.get_data_summary(user_id)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting data summary for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data summary"
        )


@router.get("/summary/today", response_model=Dict[str, Any])
async def get_today_summary(
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a summary of today's data across all devices.
    
    Returns aggregated statistics for the current day.
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        summary = await data_service.get_daily_summary(user_id, today_start, today_end)
        
        return {
            "date": today_start.date().isoformat(),
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting today's summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve today's summary"
        )


# Real-time Data Endpoints

@router.get("/stream/{device_id}")
async def get_data_stream(
    device_id: UUID,
    data_type: Optional[DataType] = Query(None, description="Filter by data type"),
    limit: int = Query(50, ge=1, le=200, description="Number of recent data points"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get real-time data stream for a specific device.
    
    Returns the most recent data points for real-time monitoring.
    
    - **device_id**: Device to stream data from
    - **data_type**: Optional filter by data type
    - **limit**: Number of recent data points to return
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        # Get recent data points
        query = DataPointQuery(
            device_id=device_id,
            data_type=data_type,
            limit=limit,
            offset=0
        )
        
        data_points, total_count = await data_service.get_data_points(user_id, query)
        
        # Format for real-time streaming
        stream_data = {
            "device_id": str(device_id),
            "data_type": data_type.value if data_type else "all",
            "data_points": [
                {
                    "id": str(point.id),
                    "data_type": point.data_type,
                    "value": point.value,
                    "unit": point.unit,
                    "timestamp": point.timestamp.isoformat(),
                    "quality": point.quality,
                    "is_anomaly": point.is_anomaly
                }
                for point in data_points
            ],
            "total_points": total_count,
            "stream_timestamp": datetime.utcnow().isoformat()
        }
        
        return stream_data
        
    except Exception as e:
        logger.error(f"Error getting data stream for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data stream"
        )


@router.get("/anomalies/{device_id}")
async def get_device_anomalies(
    device_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for anomaly search"),
    end_date: Optional[datetime] = Query(None, description="End date for anomaly search"),
    severity: Optional[str] = Query(None, description="Filter by anomaly severity (low, medium, high)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of anomalies"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get anomalies detected for a specific device.
    
    Returns data points that have been flagged as anomalies.
    
    - **device_id**: Device to check for anomalies
    - **start_date**: Start of date range
    - **end_date**: End of date range
    - **severity**: Filter by anomaly severity
    - **limit**: Maximum number of anomalies to return
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        # Get anomalies
        query = DataPointQuery(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            is_anomaly=True,
            limit=limit,
            offset=0
        )
        
        anomalies, total_count = await data_service.get_data_points(user_id, query)
        
        # Format anomalies with additional context
        anomaly_data = []
        for anomaly in anomalies:
            anomaly_info = {
                "id": str(anomaly.id),
                "data_type": anomaly.data_type,
                "value": anomaly.value,
                "unit": anomaly.unit,
                "timestamp": anomaly.timestamp.isoformat(),
                "quality": anomaly.quality,
                "anomaly_score": getattr(anomaly, 'anomaly_score', None),
                "anomaly_type": getattr(anomaly, 'anomaly_type', 'unknown'),
                "metadata": anomaly.metadata
            }
            anomaly_data.append(anomaly_info)
        
        return {
            "device_id": str(device_id),
            "anomalies": anomaly_data,
            "total_anomalies": total_count,
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting anomalies for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anomalies"
        )


@router.get("/quality/{device_id}")
async def get_data_quality_report(
    device_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date for quality analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for quality analysis"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get data quality report for a specific device.
    
    Returns comprehensive quality metrics and issues detected.
    
    - **device_id**: Device to analyze
    - **start_date**: Start of analysis period
    - **end_date**: End of analysis period
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # Get quality metrics
        quality_metrics = await data_service.get_data_quality_metrics(
            user_id, device_id, start_date, end_date
        )
        
        # Get quality issues
        quality_issues = await data_service.get_data_quality_issues(
            user_id, device_id, start_date, end_date
        )
        
        # Calculate quality score
        total_points = quality_metrics.get("total_points", 0)
        good_points = quality_metrics.get("good_quality", 0)
        quality_score = (good_points / total_points * 100) if total_points > 0 else 0
        
        return {
            "device_id": str(device_id),
            "quality_score": round(quality_score, 2),
            "metrics": quality_metrics,
            "issues": quality_issues,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting quality report for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quality report"
        )


@router.get("/realtime/{device_id}/latest")
async def get_latest_data(
    device_id: UUID,
    data_types: Optional[str] = Query(None, description="Comma-separated list of data types"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get the latest data point for each data type from a device.
    
    Returns the most recent reading for each requested data type.
    
    - **device_id**: Device to get latest data from
    - **data_types**: Comma-separated list of data types (e.g., "heart_rate,steps,sleep")
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        # Parse data types
        requested_types = []
        if data_types:
            requested_types = [DataType(dt.strip()) for dt in data_types.split(",")]
        
        # Get latest data for each type
        latest_data = {}
        for data_type in requested_types:
            latest_point = await data_service.get_latest_data_point(user_id, device_id, data_type)
            if latest_point:
                latest_data[data_type.value] = {
                    "id": str(latest_point.id),
                    "value": latest_point.value,
                    "unit": latest_point.unit,
                    "timestamp": latest_point.timestamp.isoformat(),
                    "quality": latest_point.quality,
                    "is_anomaly": latest_point.is_anomaly
                }
        
        return {
            "device_id": str(device_id),
            "latest_data": latest_data,
            "data_types_requested": [dt.value for dt in requested_types],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting latest data for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest data"
        )


# Device-specific data endpoints for frontend compatibility
@router.get("/devices/{device_id}/data/{data_type}")
async def get_device_data_by_type(
    device_id: UUID,
    data_type: DataType,
    limit: int = Query(7, ge=1, le=100, description="Number of data points"),
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get data points for a specific device and data type.
    
    This endpoint is designed for frontend compatibility.
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        # Get data points for specific device and type
        query = DataPointQuery(
            device_id=device_id,
            data_type=data_type,
            limit=limit,
            offset=0
        )
        
        data_points, total_count = await data_service.get_data_points(user_id, query)
        
        return {
            "device_id": str(device_id),
            "data_type": data_type.value,
            "data_points": [
                {
                    "id": str(point.id),
                    "value": point.value,
                    "unit": point.unit,
                    "timestamp": point.timestamp.isoformat(),
                    "quality": point.quality.value,
                    "metadata": point.data_metadata
                }
                for point in data_points
            ],
            "total": total_count,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting device data for {device_id}, type {data_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device data"
        )


@router.get("/devices/{device_id}/summary")
async def get_device_summary(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get summary for a specific device.
    
    This endpoint is designed for frontend compatibility.
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        summary = await data_service.get_device_data_summary(user_id, device_id)
        
        return {
            "device_id": str(device_id),
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting device summary for {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device summary"
        )


@router.get("/devices/{device_id}/summary/today")
async def get_device_today_summary(
    device_id: UUID,
    current_user: UserStub = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get today's summary for a specific device.
    
    This endpoint is designed for frontend compatibility.
    """
    try:
        user_id = current_user.id
        data_service = await get_data_service(db)
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        summary = await data_service.get_device_daily_summary(user_id, device_id, today_start, today_end)
        
        return {
            "device_id": str(device_id),
            "date": today_start.date().isoformat(),
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting device today summary for {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device today summary"
        ) 