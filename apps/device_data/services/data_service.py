"""
Data Service
Handles device data point management and analytics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, update, func, desc, asc
from sqlalchemy.sql import text
from fastapi import HTTPException, status

from common.services.base import BaseService
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience

from ..models.data_point import (
    DeviceDataPoint, DataType, DataQuality, DataSource,
    DataPointCreate, DataPointUpdate, DataPointResponse, DataPointSummary,
    DataPointBatch, DataPointQuery, DataPointAggregation, DataPointStatistics
)

logger = get_logger(__name__)


class DataService(BaseService):
    """Service for managing device data points"""
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
    
    @property
    def model_class(self):
        return DeviceDataPoint
    
    @property
    def schema_class(self):
        return DataPointResponse
    
    @property
    def create_schema_class(self):
        return DataPointCreate
    
    @property
    def update_schema_class(self):
        return DataPointUpdate
    
    async def create_data_point(self, user_id: UUID, data_point: DataPointCreate) -> DeviceDataPoint:
        """Create a new data point"""
        try:
            logger.info(f"Creating data point for user {user_id}: {data_point.data_type}")
            
            # Validate device ownership
            await self._validate_device_ownership(data_point.device_id, user_id)
            
            # Create data point
            db_data_point = DeviceDataPoint(
                user_id=user_id,
                **data_point.dict()
            )
            
            # Set quality based on validation
            db_data_point.quality = self._assess_data_quality(data_point)
            
            self.db.add(db_data_point)
            await self.db.commit()
            await self.db.refresh(db_data_point)
            
            logger.info(f"Data point created successfully: {db_data_point.id}")
            return db_data_point
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating data point: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create data point"
            )
    
    async def create_batch_data_points(self, user_id: UUID, batch: DataPointBatch) -> Dict[str, Any]:
        """Create multiple data points in a batch"""
        try:
            logger.info(f"Creating batch data points for user {user_id}: {len(batch.data_points)} points")
            
            # Validate device ownership
            await self._validate_device_ownership(batch.device_id, user_id)
            
            created_points = []
            errors = []
            
            for i, data_point in enumerate(batch.data_points):
                try:
                    db_data_point = DeviceDataPoint(
                        user_id=user_id,
                        device_id=batch.device_id,
                        **data_point.dict()
                    )
                    
                    # Set quality based on validation
                    db_data_point.quality = self._assess_data_quality(data_point)
                    
                    self.db.add(db_data_point)
                    created_points.append(db_data_point)
                    
                except Exception as e:
                    errors.append({
                        "index": i,
                        "error": str(e),
                        "data_point": data_point.dict()
                    })
            
            await self.db.commit()
            
            # Refresh created points
            for point in created_points:
                await self.db.refresh(point)
            
            result = {
                "created_count": len(created_points),
                "error_count": len(errors),
                "errors": errors,
                "data_points": [DataPointResponse.from_orm(point) for point in created_points]
            }
            
            logger.info(f"Batch data points created: {result['created_count']} successful, {result['error_count']} errors")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating batch data points: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create batch data points"
            )
    
    async def get_data_points(self, user_id: UUID, query: DataPointQuery) -> Tuple[List[DeviceDataPoint], int]:
        """Get data points with filtering and pagination"""
        try:
            # Build base query
            base_query = select(DeviceDataPoint).where(DeviceDataPoint.user_id == user_id)
            
            # Apply filters
            if query.device_id:
                base_query = base_query.where(DeviceDataPoint.device_id == query.device_id)
            
            if query.data_type:
                base_query = base_query.where(DeviceDataPoint.data_type == query.data_type)
            
            if query.start_date:
                base_query = base_query.where(DeviceDataPoint.timestamp >= query.start_date)
            
            if query.end_date:
                base_query = base_query.where(DeviceDataPoint.timestamp <= query.end_date)
            
            if query.quality:
                base_query = base_query.where(DeviceDataPoint.quality == query.quality)
            
            if query.is_anomaly is not None:
                base_query = base_query.where(DeviceDataPoint.is_anomaly == query.is_anomaly)
            
            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()
            
            # Apply ordering and pagination
            data_query = base_query.order_by(desc(DeviceDataPoint.timestamp))
            data_query = data_query.offset(query.offset).limit(query.limit)
            
            result = await self.db.execute(data_query)
            data_points = result.scalars().all()
            
            return data_points, total_count
            
        except Exception as e:
            logger.error(f"Error getting data points: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve data points"
            )
    
    async def get_data_point(self, data_point_id: UUID, user_id: UUID) -> Optional[DeviceDataPoint]:
        """Get a specific data point by ID"""
        try:
            query = select(DeviceDataPoint).where(
                and_(
                    DeviceDataPoint.id == data_point_id,
                    DeviceDataPoint.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            data_point = result.scalar_one_or_none()
            
            if not data_point:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data point not found"
                )
            
            return data_point
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting data point {data_point_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve data point"
            )
    
    async def update_data_point(self, data_point_id: UUID, user_id: UUID, data_point: DataPointUpdate) -> DeviceDataPoint:
        """Update data point information"""
        try:
            db_data_point = await self.get_data_point(data_point_id, user_id)
            
            # Update fields
            update_data = data_point.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(db_data_point, field, value)
            
            db_data_point.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(db_data_point)
            
            logger.info(f"Data point {data_point_id} updated successfully")
            return db_data_point
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating data point {data_point_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update data point"
            )
    
    async def delete_data_point(self, data_point_id: UUID, user_id: UUID) -> bool:
        """Delete a data point"""
        try:
            data_point = await self.get_data_point(data_point_id, user_id)
            
            await self.db.delete(data_point)
            await self.db.commit()
            
            logger.info(f"Data point {data_point_id} deleted successfully")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting data point {data_point_id}: {e}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete data point"
            )
    
    async def get_data_aggregation(self, user_id: UUID, data_type: DataType, 
                                 start_date: datetime, end_date: datetime,
                                 aggregation_period: str = "day") -> List[DataPointAggregation]:
        """Get aggregated data points"""
        try:
            # Validate aggregation period
            valid_periods = ["hour", "day", "week", "month"]
            if aggregation_period not in valid_periods:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid aggregation period. Must be one of: {valid_periods}"
                )
            
            # Build aggregation query based on period
            if aggregation_period == "hour":
                time_format = "YYYY-MM-DD HH24:00:00"
                group_by = "date_trunc('hour', timestamp)"
            elif aggregation_period == "day":
                time_format = "YYYY-MM-DD"
                group_by = "date_trunc('day', timestamp)"
            elif aggregation_period == "week":
                time_format = "YYYY-WW"
                group_by = "date_trunc('week', timestamp)"
            else:  # month
                time_format = "YYYY-MM"
                group_by = "date_trunc('month', timestamp)"
            
            # SQL query for aggregation
            sql = text(f"""
                SELECT 
                    '{data_type}' as data_type,
                    unit,
                    COUNT(*) as count,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    AVG(value) as avg_value,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median_value,
                    STDDEV(value) as std_deviation,
                    {group_by} as period_start,
                    {group_by} + INTERVAL '1 {aggregation_period}' as period_end
                FROM device_data_points
                WHERE user_id = :user_id 
                    AND data_type = :data_type
                    AND timestamp >= :start_date
                    AND timestamp < :end_date
                GROUP BY {group_by}, unit
                ORDER BY period_start
            """)
            
            result = await self.db.execute(sql, {
                "user_id": user_id,
                "data_type": data_type,
                "start_date": start_date,
                "end_date": end_date
            })
            
            aggregations = []
            for row in result:
                aggregation = DataPointAggregation(
                    data_type=row.data_type,
                    unit=row.unit,
                    count=row.count,
                    min_value=float(row.min_value) if row.min_value else None,
                    max_value=float(row.max_value) if row.max_value else None,
                    avg_value=float(row.avg_value) if row.avg_value else None,
                    median_value=float(row.median_value) if row.median_value else None,
                    std_deviation=float(row.std_deviation) if row.std_deviation else None,
                    start_date=row.period_start,
                    end_date=row.period_end,
                    aggregation_period=aggregation_period
                )
                aggregations.append(aggregation)
            
            return aggregations
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting data aggregation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get data aggregation"
            )
    
    async def get_data_statistics(self, user_id: UUID, 
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> DataPointStatistics:
        """Get comprehensive data statistics"""
        try:
            # Build base conditions
            conditions = [DeviceDataPoint.user_id == user_id]
            
            if start_date:
                conditions.append(DeviceDataPoint.timestamp >= start_date)
            if end_date:
                conditions.append(DeviceDataPoint.timestamp <= end_date)
            
            # Get total points
            total_query = select(func.count()).where(and_(*conditions))
            result = await self.db.execute(total_query)
            total_points = result.scalar()
            
            # Get valid points
            valid_query = select(func.count()).where(
                and_(*conditions, DeviceDataPoint.quality.in_([DataQuality.EXCELLENT, DataQuality.GOOD]))
            )
            result = await self.db.execute(valid_query)
            valid_points = result.scalar()
            
            # Get anomaly points
            anomaly_query = select(func.count()).where(
                and_(*conditions, DeviceDataPoint.is_anomaly == True)
            )
            result = await self.db.execute(anomaly_query)
            anomaly_points = result.scalar()
            
            # Get data types distribution
            type_query = select(
                DeviceDataPoint.data_type,
                func.count(DeviceDataPoint.id)
            ).where(and_(*conditions)).group_by(DeviceDataPoint.data_type)
            
            result = await self.db.execute(type_query)
            data_types = {row.data_type: row.count for row in result}
            
            # Get quality distribution
            quality_query = select(
                DeviceDataPoint.quality,
                func.count(DeviceDataPoint.id)
            ).where(and_(*conditions)).group_by(DeviceDataPoint.quality)
            
            result = await self.db.execute(quality_query)
            quality_distribution = {row.quality: row.count for row in result}
            
            # Get date range
            date_query = select(
                func.min(DeviceDataPoint.timestamp),
                func.max(DeviceDataPoint.timestamp)
            ).where(and_(*conditions))
            
            result = await self.db.execute(date_query)
            row = result.first()
            date_range = {
                "start": row[0],
                "end": row[1]
            }
            
            # Get device count
            device_query = select(func.count(func.distinct(DeviceDataPoint.device_id))).where(and_(*conditions))
            result = await self.db.execute(device_query)
            device_count = result.scalar()
            
            return DataPointStatistics(
                total_points=total_points,
                valid_points=valid_points,
                anomaly_points=anomaly_points,
                data_types=data_types,
                quality_distribution=quality_distribution,
                date_range=date_range,
                device_count=device_count
            )
            
        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get data statistics"
            )
    
    async def get_data_summary(self, user_id: UUID) -> Dict[str, Any]:
        """Get overall data summary for a user"""
        try:
            logger.info(f"Getting data summary for user {user_id}")
            
            # Get total data points count
            total_query = select(func.count(DeviceDataPoint.id)).where(
                DeviceDataPoint.user_id == user_id
            )
            total_result = await self.db.execute(total_query)
            total_records = total_result.scalar() or 0
            
            # Get data points by type
            type_query = select(
                DeviceDataPoint.data_type,
                func.count(DeviceDataPoint.id).label('count')
            ).where(
                DeviceDataPoint.user_id == user_id
            ).group_by(DeviceDataPoint.data_type)
            
            type_result = await self.db.execute(type_query)
            data_by_type = {row.data_type: row.count for row in type_result}
            
            # Get data points by quality
            quality_query = select(
                DeviceDataPoint.quality,
                func.count(DeviceDataPoint.id).label('count')
            ).where(
                DeviceDataPoint.user_id == user_id
            ).group_by(DeviceDataPoint.quality)
            
            quality_result = await self.db.execute(quality_query)
            data_by_quality = {row.quality: row.count for row in quality_result}
            
            # Get latest data point
            latest_query = select(DeviceDataPoint).where(
                DeviceDataPoint.user_id == user_id
            ).order_by(desc(DeviceDataPoint.timestamp)).limit(1)
            
            latest_result = await self.db.execute(latest_query)
            latest_data_point = latest_result.scalar_one_or_none()
            
            # Get anomaly count
            anomaly_query = select(func.count(DeviceDataPoint.id)).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.is_anomaly == True
                )
            )
            anomaly_result = await self.db.execute(anomaly_query)
            anomaly_count = anomaly_result.scalar() or 0
            
            summary = {
                "total_records": total_records,
                "data_by_type": data_by_type,
                "data_by_quality": data_by_quality,
                "anomaly_count": anomaly_count,
                "latest_data_point": latest_data_point.timestamp.isoformat() if latest_data_point else None,
                "data_types_count": len(data_by_type),
                "quality_distribution": {
                    quality: count for quality, count in data_by_quality.items()
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get data summary"
            )

    async def get_device_data_summary(self, user_id: UUID, device_id: UUID) -> Dict[str, Any]:
        """Get data summary for a specific device"""
        try:
            logger.info(f"Getting device data summary for user {user_id}, device {device_id}")
            
            # Validate device ownership
            await self._validate_device_ownership(device_id, user_id)
            
            # Get total data points for device
            total_query = select(func.count(DeviceDataPoint.id)).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.device_id == device_id
                )
            )
            result = await self.db.execute(total_query)
            total_points = result.scalar()
            
            # Get data points by type for device
            type_query = select(
                DeviceDataPoint.data_type,
                func.count(DeviceDataPoint.id).label('count')
            ).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.device_id == device_id
                )
            ).group_by(DeviceDataPoint.data_type)
            
            result = await self.db.execute(type_query)
            type_stats = {row.data_type.value: row.count for row in result}
            
            # Get latest data point
            latest_query = select(DeviceDataPoint).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.device_id == device_id
                )
            ).order_by(desc(DeviceDataPoint.timestamp)).limit(1)
            
            result = await self.db.execute(latest_query)
            latest_point = result.scalar_one_or_none()
            
            return {
                "device_id": str(device_id),
                "total_data_points": total_points,
                "data_types": type_stats,
                "latest_data_point": {
                    "timestamp": latest_point.timestamp.isoformat() if latest_point else None,
                    "data_type": latest_point.data_type.value if latest_point else None,
                    "value": latest_point.value if latest_point else None
                },
                "summary_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting device data summary for user {user_id}, device {device_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get device data summary"
            )

    async def get_device_daily_summary(self, user_id: UUID, device_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get daily summary for a specific device"""
        try:
            logger.info(f"Getting device daily summary for user {user_id}, device {device_id}")
            
            # Validate device ownership
            await self._validate_device_ownership(device_id, user_id)
            
            # Get data points for the date range
            query = select(DeviceDataPoint).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.device_id == device_id,
                    DeviceDataPoint.timestamp >= start_date,
                    DeviceDataPoint.timestamp < end_date
                )
            )
            
            result = await self.db.execute(query)
            data_points = result.scalars().all()
            
            # Calculate summary statistics
            summary = {
                "device_id": str(device_id),
                "date": start_date.date().isoformat(),
                "total_points": len(data_points),
                "data_types": {},
                "averages": {}
            }
            
            # Group by data type and calculate averages
            for point in data_points:
                data_type = point.data_type.value
                if data_type not in summary["data_types"]:
                    summary["data_types"][data_type] = 0
                summary["data_types"][data_type] += 1
                
                if data_type not in summary["averages"]:
                    summary["averages"][data_type] = []
                summary["averages"][data_type].append(point.value)
            
            # Calculate averages
            for data_type, values in summary["averages"].items():
                if values:
                    summary["averages"][data_type] = sum(values) / len(values)
                else:
                    summary["averages"][data_type] = 0
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting device daily summary for user {user_id}, device {device_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get device daily summary"
            )

    async def get_latest_data_point(self, user_id: UUID, device_id: UUID, data_type: DataType) -> Optional[DeviceDataPoint]:
        """Get the latest data point for a specific device and data type"""
        try:
            logger.info(f"Getting latest data point for user {user_id}, device {device_id}, type {data_type}")
            
            # Validate device ownership
            await self._validate_device_ownership(device_id, user_id)
            
            # Get latest data point
            query = select(DeviceDataPoint).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.device_id == device_id,
                    DeviceDataPoint.data_type == data_type
                )
            ).order_by(desc(DeviceDataPoint.timestamp)).limit(1)
            
            result = await self.db.execute(query)
            latest_point = result.scalar_one_or_none()
            
            return latest_point
            
        except Exception as e:
            logger.error(f"Error getting latest data point for user {user_id}, device {device_id}, type {data_type}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get latest data point"
            )

    async def get_daily_summary(self, user_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get daily summary for all user data"""
        try:
            logger.info(f"Getting daily summary for user {user_id}")
            
            # Get data points for the date range
            query = select(DeviceDataPoint).where(
                and_(
                    DeviceDataPoint.user_id == user_id,
                    DeviceDataPoint.timestamp >= start_date,
                    DeviceDataPoint.timestamp < end_date
                )
            )
            
            result = await self.db.execute(query)
            data_points = result.scalars().all()
            
            # Calculate summary statistics
            summary = {
                "date": start_date.date().isoformat(),
                "total_points": len(data_points),
                "data_types": {},
                "averages": {}
            }
            
            # Group by data type and calculate averages
            for point in data_points:
                data_type = point.data_type.value
                if data_type not in summary["data_types"]:
                    summary["data_types"][data_type] = 0
                summary["data_types"][data_type] += 1
                
                if data_type not in summary["averages"]:
                    summary["averages"][data_type] = []
                summary["averages"][data_type].append(point.value)
            
            # Calculate averages
            for data_type, values in summary["averages"].items():
                if values:
                    summary["averages"][data_type] = sum(values) / len(values)
                else:
                    summary["averages"][data_type] = 0
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting daily summary for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get daily summary"
            )

    async def detect_anomalies(self, user_id: UUID, data_type: Optional[DataType] = None) -> Dict[str, Any]:
        """Detect anomalies in data points"""
        try:
            # Build query
            conditions = [DeviceDataPoint.user_id == user_id]
            if data_type:
                conditions.append(DeviceDataPoint.data_type == data_type)
            
            # Get data for anomaly detection
            query = select(DeviceDataPoint).where(and_(*conditions)).order_by(DeviceDataPoint.timestamp)
            result = await self.db.execute(query)
            data_points = result.scalars().all()
            
            if not data_points:
                return {"anomalies": [], "total_checked": 0}
            
            # Simple anomaly detection using statistical methods
            anomalies = []
            for data_point in data_points:
                anomaly_score = await self._calculate_anomaly_score(data_point, data_points)
                
                if anomaly_score > 0.7:  # Threshold for anomaly
                    data_point.is_anomaly = True
                    data_point.anomaly_score = anomaly_score
                    anomalies.append({
                        "id": data_point.id,
                        "data_type": data_point.data_type,
                        "value": data_point.value,
                        "timestamp": data_point.timestamp,
                        "anomaly_score": anomaly_score
                    })
            
            # Update database with anomaly flags
            await self.db.commit()
            
            return {
                "anomalies": anomalies,
                "total_checked": len(data_points),
                "anomaly_count": len(anomalies)
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to detect anomalies"
            )
    
    # Private helper methods
    async def _validate_device_ownership(self, device_id: UUID, user_id: UUID):
        """Validate that device belongs to user"""
        from ..models.device import Device
        
        query = select(Device).where(
            and_(
                Device.id == device_id,
                Device.user_id == user_id,
                Device.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found or not owned by user"
            )
    
    def _assess_data_quality(self, data_point: DataPointCreate) -> DataQuality:
        """Assess data quality based on various factors"""
        # Simple quality assessment logic
        if data_point.raw_value:
            return DataQuality.GOOD
        else:
            return DataQuality.FAIR
    
    async def _calculate_anomaly_score(self, data_point: DeviceDataPoint, all_points: List[DeviceDataPoint]) -> float:
        """Calculate anomaly score for a data point"""
        # Simple statistical anomaly detection
        values = [p.value for p in all_points if p.data_type == data_point.data_type]
        
        if len(values) < 3:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        z_score = abs(data_point.value - mean) / std_dev
        
        # Convert z-score to anomaly score (0-1)
        if z_score > 3:
            return 1.0
        elif z_score > 2:
            return 0.8
        elif z_score > 1.5:
            return 0.6
        else:
            return 0.0


# Service factory
async def get_data_service(db: AsyncSession) -> DataService:
    """Get data service instance"""
    return DataService(db) 