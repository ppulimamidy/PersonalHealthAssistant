"""
Health Analytics Service
Provides analytics and insights from health metrics data.
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import statistics
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from common.clients.knowledge_graph_client import KnowledgeGraphClient
from ..models.health_metrics import HealthMetric, MetricType
from ..models.health_goals import HealthGoal, GoalStatus
from ..models.health_insights import HealthInsight, InsightType, InsightSeverity, InsightStatus

logger = get_logger(__name__)

def symptom_to_response_dict(symptom):
    return {
        "id": str(symptom.id),
        "user_id": str(symptom.user_id),
        "symptom_name": getattr(symptom, "symptom_name", ""),
        "symptom_category": getattr(symptom, "symptom_category", ""),
        "description": getattr(symptom, "description", None),
        "severity": getattr(symptom, "severity", ""),
        "severity_level": getattr(symptom, "severity_level", 0.0),
        "impact_on_daily_activities": getattr(symptom, "impact_on_daily_activities", None),
        "frequency": getattr(symptom, "frequency", None),
        "frequency_count": getattr(symptom, "frequency_count", None),
        "frequency_period": getattr(symptom, "frequency_period", None),
        "duration": getattr(symptom, "duration", None),
        "duration_hours": getattr(symptom, "duration_hours", None),
        "start_time": getattr(symptom, "start_time", None).isoformat() if getattr(symptom, "start_time", None) else None,
        "end_time": getattr(symptom, "end_time", None).isoformat() if getattr(symptom, "end_time", None) else None,
        "body_location": getattr(symptom, "body_location", None),
        "body_side": getattr(symptom, "body_side", None),
        "radiation": getattr(symptom, "radiation", None),
        "quality": getattr(symptom, "quality", None),
        "triggers": getattr(symptom, "triggers", []) or [],
        "context": getattr(symptom, "context", None),
        "associated_symptoms": getattr(symptom, "associated_symptoms", []) or [],
        "relief_factors": getattr(symptom, "relief_factors", []) or [],
        "aggravating_factors": getattr(symptom, "aggravating_factors", []) or [],
        "related_conditions": getattr(symptom, "related_conditions", []) or [],
        "medications_taken": getattr(symptom, "medications_taken", []) or [],
        "treatments_tried": getattr(symptom, "treatments_tried", []) or [],
        "sleep_impact": getattr(symptom, "sleep_impact", None),
        "work_impact": getattr(symptom, "work_impact", None),
        "social_impact": getattr(symptom, "social_impact", None),
        "emotional_impact": getattr(symptom, "emotional_impact", None),
        "is_recurring": getattr(symptom, "is_recurring", False),
        "recurrence_pattern": getattr(symptom, "recurrence_pattern", None),
        "last_occurrence": getattr(symptom, "last_occurrence", None).isoformat() if getattr(symptom, "last_occurrence", None) else None,
        "next_expected": getattr(symptom, "next_expected", None).isoformat() if getattr(symptom, "next_expected", None) else None,
        "requires_medical_attention": getattr(symptom, "requires_medical_attention", False),
        "medical_attention_urgency": getattr(symptom, "medical_attention_urgency", None),
        "medical_attention_received": getattr(symptom, "medical_attention_received", False),
        "medical_attention_date": getattr(symptom, "medical_attention_date", None).isoformat() if getattr(symptom, "medical_attention_date", None) else None,
        "medical_attention_notes": getattr(symptom, "medical_attention_notes", None),
        "created_at": symptom.created_at.isoformat() if getattr(symptom, "created_at", None) else "",
        "updated_at": symptom.updated_at.isoformat() if getattr(symptom, "updated_at", None) else (symptom.created_at.isoformat() if getattr(symptom, "created_at", None) else ""),
        "symptom_metadata": getattr(symptom, "symptom_metadata", {}) or {}
    }

class HealthAnalyticsService:
    """Service for health analytics and insights"""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def initialize(self):
        """Initialize the analytics service"""
        logger.info("Initializing Health Analytics Service")
        # Clear cache
        self.cache.clear()
    
    async def cleanup(self):
        """Cleanup the analytics service"""
        logger.info("Cleaning up Health Analytics Service")
        self.cache.clear()
    
    # CRUD Operations for Health Metrics
    async def create_metric(self, user_id: str, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new health metric"""
        try:
            from ..models.health_metrics import HealthMetricCreate
            
            # Validate the metric data
            metric_create = HealthMetricCreate(**metric_data)
            
            # Create the metric
            metric = HealthMetric(
                user_id=user_id,
                metric_type=metric_create.metric_type,
                value=metric_create.value,
                unit=metric_create.unit,
                timestamp=metric_create.timestamp or datetime.utcnow(),
                notes=metric_create.notes,
                source=metric_create.source,
                device_id=metric_create.device_id
            )
            
            self.db.add(metric)
            await self.db.commit()
            await self.db.refresh(metric)
            
            return {
                "id": str(metric.id),
                "user_id": str(metric.user_id),
                "metric_type": metric.metric_type,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "notes": metric.notes,
                "source": metric.source,
                "device_id": metric.device_id,
                "created_at": metric.created_at.isoformat(),
                "updated_at": metric.updated_at.isoformat() if metric.updated_at else metric.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating metric: {e}")
            raise ValueError(f"Failed to create metric: {str(e)}")

    async def get_metrics(self, user_id: str, filter_params: Any, db: AsyncSession = None) -> Dict[str, Any]:
        """Get health metrics with filtering"""
        try:
            # Use provided db session or fall back to instance db
            session = db or self.db
            if not session:
                raise ValueError("Database session is required")
                
            # Build base query
            base_query = select(HealthMetric).where(HealthMetric.user_id == user_id)
            
            # Apply filters
            if filter_params.metric_type:
                base_query = base_query.where(HealthMetric.metric_type == filter_params.metric_type)
            if filter_params.start_date:
                base_query = base_query.where(HealthMetric.timestamp >= filter_params.start_date)
            if filter_params.end_date:
                base_query = base_query.where(HealthMetric.timestamp <= filter_params.end_date)
            
            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination to main query
            query = base_query.order_by(desc(HealthMetric.timestamp))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            result = await session.execute(query)
            metrics = result.scalars().all()
            
            return {
                "data": [
                    {
                        "id": str(metric.id),
                        "user_id": str(metric.user_id),
                        "metric_type": metric.metric_type,
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat(),
                        "notes": metric.notes,
                        "source": metric.source,
                        "device_id": metric.device_id,
                        "created_at": metric.created_at.isoformat(),
                        "updated_at": metric.updated_at.isoformat() if metric.updated_at else metric.created_at.isoformat()
                    }
                    for metric in metrics
                ],
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            raise ValueError(f"Failed to retrieve metrics: {str(e)}")

    async def get_metric(self, user_id: str, metric_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific health metric by ID"""
        try:
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.id == metric_id,
                    HealthMetric.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            metric = result.scalar_one_or_none()
            
            if not metric:
                return None
            
            return {
                "id": str(metric.id),
                "user_id": str(metric.user_id),
                "metric_type": metric.metric_type,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "notes": metric.notes,
                "source": metric.source,
                "device_id": metric.device_id,
                "created_at": metric.created_at.isoformat(),
                "updated_at": metric.updated_at.isoformat() if metric.updated_at else metric.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving metric: {e}")
            raise ValueError(f"Failed to retrieve metric: {str(e)}")

    async def update_metric(self, user_id: str, metric_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a health metric"""
        try:
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.id == metric_id,
                    HealthMetric.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            metric = result.scalar_one_or_none()
            
            if not metric:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(metric, field):
                    setattr(metric, field, value)
            
            metric.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(metric)
            
            return {
                "id": str(metric.id),
                "user_id": str(metric.user_id),
                "metric_type": metric.metric_type,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "notes": metric.notes,
                "source": metric.source,
                "device_id": metric.device_id,
                "created_at": metric.created_at.isoformat(),
                "updated_at": metric.updated_at.isoformat() if metric.updated_at else metric.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating metric: {e}")
            raise ValueError(f"Failed to update metric: {str(e)}")

    async def delete_metric(self, user_id: str, metric_id: str) -> bool:
        """Delete a health metric"""
        try:
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.id == metric_id,
                    HealthMetric.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            metric = result.scalar_one_or_none()
            
            if not metric:
                return False
            
            await self.db.delete(metric)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting metric: {e}")
            raise ValueError(f"Failed to delete metric: {str(e)}")

    async def get_metrics_summary(self, user_id: str, metric_type: Optional[MetricType] = None) -> Dict[str, Any]:
        """Get summary statistics for metrics"""
        try:
            query = select(HealthMetric).where(HealthMetric.user_id == user_id)
            
            if metric_type:
                query = query.where(HealthMetric.metric_type == metric_type)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "total_metrics": 0,
                    "metric_types": [],
                    "summary": {}
                }
            
            # Group by metric type
            metrics_by_type = {}
            for metric in metrics:
                if metric.metric_type not in metrics_by_type:
                    metrics_by_type[metric.metric_type] = []
                metrics_by_type[metric.metric_type].append(metric)
            
            summary = {
                "total_metrics": len(metrics),
                "metric_types": list(metrics_by_type.keys()),
                "summary": {}
            }
            
            for metric_type, type_metrics in metrics_by_type.items():
                values = [m.value for m in type_metrics if m.value is not None]
                if values:
                    summary["summary"][metric_type] = {
                        "count": len(type_metrics),
                        "latest_value": type_metrics[-1].value,
                        "average": statistics.mean(values),
                        "min": min(values),
                        "max": max(values),
                        "unit": type_metrics[0].unit
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            raise ValueError(f"Failed to get metrics summary: {str(e)}")

    # CRUD Operations for Health Goals
    async def create_goal(self, user_id: str, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new health goal"""
        try:
            from ..models.health_goals import HealthGoalCreate
            
            # Validate the goal data
            goal_create = HealthGoalCreate(**goal_data)
            
            # Create the goal
            goal = HealthGoal(
                user_id=user_id,
                title=goal_create.title,
                description=goal_create.description,
                metric_type=goal_create.metric_type,
                goal_type=goal_create.goal_type,
                target_value=goal_create.target_value,
                unit=goal_create.unit,
                frequency=goal_create.frequency,
                start_date=goal_create.start_date,
                target_date=goal_create.target_date,
                status=goal_create.status
            )
            
            self.db.add(goal)
            await self.db.commit()
            await self.db.refresh(goal)
            
            return {
                "id": str(goal.id),
                "user_id": str(goal.user_id),
                "title": goal.title,
                "description": goal.description,
                "metric_type": goal.metric_type,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "frequency": goal.frequency,
                "start_date": goal.start_date.isoformat(),
                "target_date": goal.target_date.isoformat(),
                "status": goal.status,
                "created_at": goal.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating goal: {e}")
            raise ValueError(f"Failed to create goal: {str(e)}")

    async def get_goals(self, user_id: str, filter_params: Any) -> Dict[str, Any]:
        """Get health goals with filtering"""
        try:
            # First, get total count for pagination
            count_query = select(func.count(HealthGoal.id)).where(HealthGoal.user_id == user_id)
            
            # Apply filters to count query
            if filter_params.goal_type:
                count_query = count_query.where(HealthGoal.goal_type == filter_params.goal_type)
            if filter_params.status:
                count_query = count_query.where(HealthGoal.status == filter_params.status)
            
            result = await self.db.execute(count_query)
            total = result.scalar()
            
            # Then get the actual data with pagination
            query = select(HealthGoal).where(HealthGoal.user_id == user_id)
            
            # Apply filters
            if filter_params.goal_type:
                query = query.where(HealthGoal.goal_type == filter_params.goal_type)
            if filter_params.status:
                query = query.where(HealthGoal.status == filter_params.status)
            
            # Apply pagination
            query = query.order_by(desc(HealthGoal.created_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            result = await self.db.execute(query)
            goals = result.scalars().all()
            
            data = [
                {
                    "id": str(goal.id),
                    "user_id": str(goal.user_id),
                    "title": goal.title,
                    "description": goal.description,
                    "metric_type": goal.metric_type,
                    "goal_type": goal.goal_type,
                    "target_value": goal.target_value,
                    "unit": goal.unit,
                    "frequency": goal.frequency,
                    "start_date": goal.start_date.isoformat() if goal.start_date else None,
                    "target_date": goal.target_date.isoformat() if goal.target_date else None,
                    "status": goal.status,
                    "created_at": goal.created_at.isoformat() if getattr(goal, 'created_at', None) else None,
                    "updated_at": goal.updated_at.isoformat() if getattr(goal, 'updated_at', None) else None
                }
                for goal in goals
            ]
            
            return {
                "data": data,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error retrieving goals: {e}")
            raise ValueError(f"Failed to retrieve goals: {str(e)}")

    async def get_goal(self, user_id: str, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific health goal by ID"""
        try:
            query = select(HealthGoal).where(
                and_(
                    HealthGoal.id == goal_id,
                    HealthGoal.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            goal = result.scalar_one_or_none()
            
            if not goal:
                return None
            
            return {
                "id": str(goal.id),
                "user_id": str(goal.user_id),
                "title": goal.title,
                "description": goal.description,
                "metric_type": goal.metric_type,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "frequency": goal.frequency,
                "start_date": goal.start_date.isoformat(),
                "target_date": goal.target_date.isoformat(),
                "status": goal.status,
                "created_at": goal.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving goal: {e}")
            raise ValueError(f"Failed to retrieve goal: {str(e)}")

    async def update_goal(self, user_id: str, goal_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a health goal"""
        try:
            query = select(HealthGoal).where(
                and_(
                    HealthGoal.id == goal_id,
                    HealthGoal.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            goal = result.scalar_one_or_none()
            
            if not goal:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(goal, field):
                    setattr(goal, field, value)
            
            goal.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(goal)
            
            return {
                "id": str(goal.id),
                "user_id": str(goal.user_id),
                "title": goal.title,
                "description": goal.description,
                "metric_type": goal.metric_type,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "frequency": goal.frequency,
                "start_date": goal.start_date.isoformat(),
                "target_date": goal.target_date.isoformat(),
                "status": goal.status,
                "created_at": goal.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating goal: {e}")
            raise ValueError(f"Failed to update goal: {str(e)}")

    async def delete_goal(self, user_id: str, goal_id: str) -> bool:
        """Delete a health goal"""
        try:
            query = select(HealthGoal).where(
                and_(
                    HealthGoal.id == goal_id,
                    HealthGoal.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            goal = result.scalar_one_or_none()
            
            if not goal:
                return False
            
            await self.db.delete(goal)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting goal: {e}")
            raise ValueError(f"Failed to delete goal: {str(e)}")

    async def get_goal_progress(self, user_id: str, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a specific goal"""
        try:
            query = select(HealthGoal).where(
                and_(
                    HealthGoal.id == goal_id,
                    HealthGoal.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            goal = result.scalar_one_or_none()
            
            if not goal:
                return None
            
            # Calculate progress based on metrics
            metrics_query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == goal.metric_type,
                    HealthMetric.timestamp >= goal.start_date,
                    HealthMetric.timestamp <= goal.target_date
                )
            ).order_by(desc(HealthMetric.timestamp))
            
            result = await self.db.execute(metrics_query)
            metrics = result.scalars().all()
            
            current_value = metrics[0].value if metrics else 0
            progress_percentage = min((current_value / goal.target_value) * 100, 100) if goal.target_value > 0 else 0
            
            return {
                "goal_id": str(goal.id),
                "current_value": current_value,
                "target_value": goal.target_value,
                "progress_percentage": progress_percentage,
                "days_remaining": (goal.target_date - datetime.utcnow().date()).days,
                "status": goal.status
            }
            
        except Exception as e:
            logger.error(f"Error getting goal progress: {e}")
            raise ValueError(f"Failed to get goal progress: {str(e)}")

    async def complete_goal(self, user_id: str, goal_id: str) -> Optional[Dict[str, Any]]:
        """Mark a goal as completed"""
        try:
            query = select(HealthGoal).where(
                and_(
                    HealthGoal.id == goal_id,
                    HealthGoal.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            goal = result.scalar_one_or_none()
            
            if not goal:
                return None
            
            goal.status = GoalStatus.COMPLETED
            goal.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(goal)
            
            return {
                "id": str(goal.id),
                "user_id": str(goal.user_id),
                "title": goal.title,
                "description": goal.description,
                "metric_type": goal.metric_type,
                "goal_type": goal.goal_type,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "frequency": goal.frequency,
                "start_date": goal.start_date.isoformat(),
                "target_date": goal.target_date.isoformat(),
                "status": goal.status,
                "created_at": goal.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error completing goal: {e}")
            raise ValueError(f"Failed to complete goal: {str(e)}")

    # CRUD Operations for Symptoms
    async def create_symptom(self, user_id: str, symptom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new symptom"""
        try:
            from ..models.symptoms import Symptoms, SymptomCategory, SymptomSeverity
            
            # Ensure enums are saved as strings
            cat = symptom_data.get("symptom_category", SymptomCategory.GENERAL.value)
            if isinstance(cat, SymptomCategory):
                cat = cat.value
            sev = symptom_data.get("severity", SymptomSeverity.MILD.value)
            if isinstance(sev, SymptomSeverity):
                sev = sev.value

            # Create the symptom
            symptom = Symptoms(
                user_id=user_id,
                symptom_name=symptom_data.get("symptom_name"),
                symptom_category=cat,
                severity=sev,
                severity_level=symptom_data.get("severity_level", 3.0),
                description=symptom_data.get("description"),
                duration_hours=symptom_data.get("duration_hours"),
                body_location=symptom_data.get("body_location"),
                triggers=symptom_data.get("triggers", []),
                relief_factors=symptom_data.get("relief_factors", [])
            )
            
            self.db.add(symptom)
            await self.db.commit()
            await self.db.refresh(symptom)
            
            return symptom_to_response_dict(symptom)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating symptom: {e}")
            raise ValueError(f"Failed to create symptom: {str(e)}")

    async def get_symptoms(self, user_id: str, filter_params: Any) -> Dict[str, Any]:
        """Get symptoms with filtering"""
        try:
            from ..models.symptoms import Symptoms
            
            # First, get total count for pagination
            count_query = select(func.count(Symptoms.id)).where(Symptoms.user_id == user_id)
            
            # Apply filters to count query
            if filter_params.symptom_category:
                count_query = count_query.where(Symptoms.symptom_category == filter_params.symptom_category)
            if filter_params.severity:
                count_query = count_query.where(Symptoms.severity == filter_params.severity)
            if filter_params.frequency:
                count_query = count_query.where(Symptoms.frequency == filter_params.frequency)
            if filter_params.duration:
                count_query = count_query.where(Symptoms.duration == filter_params.duration)
            if filter_params.body_location:
                count_query = count_query.where(Symptoms.body_location.ilike(f"%{filter_params.body_location}%"))
            if filter_params.is_recurring is not None:
                count_query = count_query.where(Symptoms.is_recurring == filter_params.is_recurring)
            if filter_params.requires_medical_attention is not None:
                count_query = count_query.where(Symptoms.requires_medical_attention == filter_params.requires_medical_attention)
            
            result = await self.db.execute(count_query)
            total = result.scalar()
            
            # Then get the actual data with pagination
            query = select(Symptoms).where(Symptoms.user_id == user_id)
            
            # Apply filters
            if filter_params.symptom_category:
                query = query.where(Symptoms.symptom_category == filter_params.symptom_category)
            if filter_params.severity:
                query = query.where(Symptoms.severity == filter_params.severity)
            if filter_params.frequency:
                query = query.where(Symptoms.frequency == filter_params.frequency)
            if filter_params.duration:
                query = query.where(Symptoms.duration == filter_params.duration)
            if filter_params.body_location:
                query = query.where(Symptoms.body_location.ilike(f"%{filter_params.body_location}%"))
            if filter_params.is_recurring is not None:
                query = query.where(Symptoms.is_recurring == filter_params.is_recurring)
            if filter_params.requires_medical_attention is not None:
                query = query.where(Symptoms.requires_medical_attention == filter_params.requires_medical_attention)
            
            # Apply pagination
            query = query.order_by(desc(Symptoms.created_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            result = await self.db.execute(query)
            symptoms = result.scalars().all()
            
            data = [
                symptom_to_response_dict(symptom)
                for symptom in symptoms
            ]
            
            return {
                "data": data,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error retrieving symptoms: {e}")
            raise ValueError(f"Failed to retrieve symptoms: {str(e)}")

    async def get_symptom(self, user_id: str, symptom_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific symptom by ID"""
        try:
            from ..models.symptoms import Symptoms
            
            query = select(Symptoms).where(
                and_(
                    Symptoms.id == symptom_id,
                    Symptoms.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            symptom = result.scalar_one_or_none()
            
            if not symptom:
                return None
            
            return symptom_to_response_dict(symptom)
            
        except Exception as e:
            logger.error(f"Error retrieving symptom: {e}")
            raise ValueError(f"Failed to retrieve symptom: {str(e)}")

    async def update_symptom(self, user_id: str, symptom_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a symptom"""
        try:
            from ..models.symptoms import Symptoms
            
            query = select(Symptoms).where(
                and_(
                    Symptoms.id == symptom_id,
                    Symptoms.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            symptom = result.scalar_one_or_none()
            
            if not symptom:
                return None
            
            # Update fields
            for field, value in update_data.items():
                # Convert enums to string values if needed
                if field in ("severity", "symptom_category") and hasattr(value, "value"):
                    value = value.value
                if hasattr(symptom, field):
                    setattr(symptom, field, value)
            
            symptom.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(symptom)
            
            return symptom_to_response_dict(symptom)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating symptom: {e}")
            raise ValueError(f"Failed to update symptom: {str(e)}")

    async def delete_symptom(self, user_id: str, symptom_id: str) -> bool:
        """Delete a symptom"""
        try:
            from ..models.symptoms import Symptoms
            
            query = select(Symptoms).where(
                and_(
                    Symptoms.id == symptom_id,
                    Symptoms.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            symptom = result.scalar_one_or_none()
            
            if not symptom:
                return False
            
            await self.db.delete(symptom)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting symptom: {e}")
            raise ValueError(f"Failed to delete symptom: {str(e)}")

    # CRUD Operations for Health Insights
    async def create_insight(self, user_id: str, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new health insight"""
        try:
            from ..models.health_insights import HealthInsight, InsightType, InsightSeverity
            
            # Create the insight
            insight = HealthInsight(
                user_id=user_id,
                insight_type=insight_data.get("insight_type", InsightType.LIFESTYLE_SUGGESTION.value),
                title=insight_data.get("title"),
                description=insight_data.get("description"),
                severity=insight_data.get("severity", InsightSeverity.MEDIUM.value),
                summary=insight_data.get("summary"),
                confidence=insight_data.get("confidence"),
                actionable=insight_data.get("actionable", True),
                related_metrics=insight_data.get("related_metrics"),
                related_goals=insight_data.get("related_goals"),
                insight_metadata=insight_data.get("insight_metadata")
            )
            
            self.db.add(insight)
            await self.db.commit()
            await self.db.refresh(insight)
            
            return {
                "id": str(insight.id),
                "user_id": str(insight.user_id),
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "summary": insight.summary,
                "severity": insight.severity,
                "status": insight.status,
                "confidence": insight.confidence,
                "actionable": insight.actionable,
                "action_taken": insight.action_taken,
                "related_metrics": insight.related_metrics,
                "related_goals": insight.related_goals,
                "insight_metadata": insight.insight_metadata,
                "created_at": insight.created_at.isoformat(),
                "updated_at": insight.updated_at.isoformat() if insight.updated_at else insight.created_at.isoformat(),
                "read_at": insight.read_at.isoformat() if insight.read_at else None,
                "acted_upon_at": insight.acted_upon_at.isoformat() if insight.acted_upon_at else None
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating insight: {e}")
            raise ValueError(f"Failed to create insight: {str(e)}")

    async def get_insights(self, user_id: str, filter_params: Any) -> Dict[str, Any]:
        """Get health insights with filtering"""
        try:
            from ..models.health_insights import HealthInsight
            
            # Get total count
            count_query = select(func.count(HealthInsight.id)).where(HealthInsight.user_id == user_id)
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Get paginated data
            query = select(HealthInsight).where(HealthInsight.user_id == user_id)
            
            # Apply pagination
            query = query.order_by(desc(HealthInsight.created_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            result = await self.db.execute(query)
            insights = result.scalars().all()
            
            data = [
                {
                    "id": str(insight.id),
                    "user_id": str(insight.user_id),
                    "insight_type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "summary": insight.summary,
                    "severity": insight.severity,
                    "status": insight.status,
                    "confidence": insight.confidence,
                    "actionable": insight.actionable,
                    "action_taken": insight.action_taken,
                    "related_metrics": insight.related_metrics,
                    "related_goals": insight.related_goals,
                    "insight_metadata": insight.insight_metadata,
                    "created_at": insight.created_at.isoformat(),
                    "updated_at": insight.updated_at.isoformat() if insight.updated_at else insight.created_at.isoformat(),
                    "read_at": insight.read_at.isoformat() if insight.read_at else None,
                    "acted_upon_at": insight.acted_upon_at.isoformat() if insight.acted_upon_at else None
                }
                for insight in insights
            ]
            
            return {
                "data": data,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error retrieving insights: {e}")
            raise ValueError(f"Failed to retrieve insights: {str(e)}")

    async def get_insight(self, user_id: str, insight_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific health insight by ID"""
        try:
            from ..models.health_insights import HealthInsight
            
            query = select(HealthInsight).where(
                and_(
                    HealthInsight.id == insight_id,
                    HealthInsight.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return None
            
            return {
                "id": str(insight.id),
                "user_id": str(insight.user_id),
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "summary": insight.summary,
                "severity": insight.severity,
                "status": insight.status,
                "confidence": insight.confidence,
                "actionable": insight.actionable,
                "action_taken": insight.action_taken,
                "related_metrics": insight.related_metrics,
                "related_goals": insight.related_goals,
                "insight_metadata": insight.insight_metadata,
                "created_at": insight.created_at.isoformat(),
                "updated_at": insight.updated_at.isoformat() if insight.updated_at else insight.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving insight: {e}")
            raise ValueError(f"Failed to retrieve insight: {str(e)}")

    async def update_insight(self, user_id: str, insight_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a health insight"""
        try:
            from ..models.health_insights import HealthInsight
            
            query = select(HealthInsight).where(
                and_(
                    HealthInsight.id == insight_id,
                    HealthInsight.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(insight, field):
                    setattr(insight, field, value)
            
            insight.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(insight)
            
            return {
                "id": str(insight.id),
                "user_id": str(insight.user_id),
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "summary": insight.summary,
                "severity": insight.severity,
                "status": insight.status,
                "confidence": insight.confidence,
                "actionable": insight.actionable,
                "action_taken": insight.action_taken,
                "related_metrics": insight.related_metrics,
                "related_goals": insight.related_goals,
                "insight_metadata": insight.insight_metadata,
                "created_at": insight.created_at.isoformat(),
                "updated_at": insight.updated_at.isoformat() if insight.updated_at else insight.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating insight: {e}")
            raise ValueError(f"Failed to update insight: {str(e)}")

    async def delete_insight(self, user_id: str, insight_id: str) -> bool:
        """Delete a health insight"""
        try:
            from ..models.health_insights import HealthInsight
            
            query = select(HealthInsight).where(
                and_(
                    HealthInsight.id == insight_id,
                    HealthInsight.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return False
            
            await self.db.delete(insight)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting insight: {e}")
            raise ValueError(f"Failed to delete insight: {str(e)}")

    async def mark_insight_read(self, user_id: str, insight_id: str) -> Optional[Dict[str, Any]]:
        """Mark an insight as read"""
        try:
            from ..models.health_insights import HealthInsight
            
            query = select(HealthInsight).where(
                and_(
                    HealthInsight.id == insight_id,
                    HealthInsight.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return None
            
            insight.status = InsightStatus.READ.value
            insight.read_at = datetime.utcnow()
            insight.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(insight)
            
            # Return complete insight data matching the response model
            return {
                "id": str(insight.id),
                "user_id": str(insight.user_id),
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "severity": insight.severity,
                "actionable": insight.actionable,
                "action_taken": insight.action_taken,
                "status": insight.status,
                "read_at": insight.read_at.isoformat() if insight.read_at else None,
                "acted_upon_at": insight.acted_upon_at.isoformat() if insight.acted_upon_at else None,
                "created_at": insight.created_at.isoformat(),
                "updated_at": insight.updated_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking insight as read: {e}")
            raise ValueError(f"Failed to mark insight as read: {str(e)}")

    async def act_upon_insight(self, user_id: str, insight_id: str, action_taken: str) -> Optional[Dict[str, Any]]:
        """Record action taken on an insight"""
        try:
            from ..models.health_insights import HealthInsight
            
            query = select(HealthInsight).where(
                and_(
                    HealthInsight.id == insight_id,
                    HealthInsight.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return None
            
            insight.status = InsightStatus.ACTED_UPON.value
            insight.action_taken = True
            insight.acted_upon_at = datetime.utcnow()
            insight.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(insight)
            
            # Return complete insight data matching the response model
            return {
                "id": str(insight.id),
                "user_id": str(insight.user_id),
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "severity": insight.severity,
                "actionable": insight.actionable,
                "action_taken": insight.action_taken,
                "status": insight.status,
                "read_at": insight.read_at.isoformat() if insight.read_at else None,
                "acted_upon_at": insight.acted_upon_at.isoformat() if insight.acted_upon_at else None,
                "created_at": insight.created_at.isoformat(),
                "updated_at": insight.updated_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording action on insight: {e}")
            raise ValueError(f"Failed to record action on insight: {str(e)}")

    async def get_insights_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get insights dashboard data"""
        try:
            from ..models.health_insights import HealthInsight
            
            # Get recent insights
            recent_insights_query = select(HealthInsight).where(
                HealthInsight.user_id == user_id
            ).order_by(desc(HealthInsight.created_at)).limit(10)
            
            result = await self.db.execute(recent_insights_query)
            recent_insights = result.scalars().all()
            
            # Get insights by severity
            severity_counts_query = select(
                HealthInsight.severity,
                func.count(HealthInsight.id)
            ).where(
                HealthInsight.user_id == user_id
            ).group_by(HealthInsight.severity)
            
            result = await self.db.execute(severity_counts_query)
            severity_counts = result.all()
            
            return {
                "recent_insights": [
                    {
                        "id": str(insight.id),
                        "title": insight.title,
                        "severity": insight.severity,
                        "created_at": insight.created_at.isoformat()
                    }
                    for insight in recent_insights
                ],
                "severity_counts": {
                    severity: count for severity, count in severity_counts
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting insights dashboard: {e}")
            raise ValueError(f"Failed to get insights dashboard: {str(e)}")

    # CRUD Operations for Devices
    async def register_device(self, user_id: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new health device"""
        try:
            from ..models.devices import Device
            
            # Create the device
            device = Device(
                user_id=user_id,
                device_type=device_data.get("device_type"),
                device_name=device_data.get("device_name"),
                device_model=device_data.get("device_model"),
                manufacturer=device_data.get("manufacturer"),
                serial_number=device_data.get("serial_number"),
                firmware_version=device_data.get("firmware_version"),
                is_active=device_data.get("is_active", True)
            )
            
            self.db.add(device)
            await self.db.commit()
            await self.db.refresh(device)
            
            return {
                "id": str(device.id),
                "user_id": str(device.user_id),
                "device_type": device.device_type,
                "device_name": device.device_name,
                "device_model": device.device_model,
                "manufacturer": device.manufacturer,
                "serial_number": device.serial_number,
                "firmware_version": device.firmware_version,
                "is_active": device.is_active,
                "created_at": device.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error registering device: {e}")
            raise ValueError(f"Failed to register device: {str(e)}")

    async def list_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """List all devices for a user"""
        try:
            from ..models.devices import Device
            
            query = select(Device).where(Device.user_id == user_id)
            
            result = await self.db.execute(query)
            devices = result.scalars().all()
            
            return [
                {
                    "id": str(device.id),
                    "user_id": str(device.user_id),
                    "device_type": device.device_type,
                    "device_name": device.device_name,
                    "device_model": device.device_model,
                    "manufacturer": device.manufacturer,
                    "serial_number": device.serial_number,
                    "firmware_version": device.firmware_version,
                    "is_active": device.is_active,
                    "created_at": device.created_at.isoformat()
                }
                for device in devices
            ]
            
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            raise ValueError(f"Failed to list devices: {str(e)}")

    async def get_device(self, user_id: str, device_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific device by ID"""
        try:
            from ..models.devices import Device
            
            query = select(Device).where(
                and_(
                    Device.id == device_id,
                    Device.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()
            
            if not device:
                return None
            
            return {
                "id": str(device.id),
                "user_id": str(device.user_id),
                "device_type": device.device_type,
                "device_name": device.device_name,
                "device_model": device.device_model,
                "manufacturer": device.manufacturer,
                "serial_number": device.serial_number,
                "firmware_version": device.firmware_version,
                "is_active": device.is_active,
                "created_at": device.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving device: {e}")
            raise ValueError(f"Failed to retrieve device: {str(e)}")

    async def update_device(self, user_id: str, device_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a device"""
        try:
            from ..models.devices import Device
            
            query = select(Device).where(
                and_(
                    Device.id == device_id,
                    Device.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()
            
            if not device:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(device, field):
                    setattr(device, field, value)
            
            device.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(device)
            
            return {
                "id": str(device.id),
                "user_id": str(device.user_id),
                "device_type": device.device_type,
                "device_name": device.device_name,
                "device_model": device.device_model,
                "manufacturer": device.manufacturer,
                "serial_number": device.serial_number,
                "firmware_version": device.firmware_version,
                "is_active": device.is_active,
                "created_at": device.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating device: {e}")
            raise ValueError(f"Failed to update device: {str(e)}")

    async def delete_device(self, user_id: str, device_id: str) -> bool:
        """Delete a device"""
        try:
            from ..models.devices import Device
            
            query = select(Device).where(
                and_(
                    Device.id == device_id,
                    Device.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()
            
            if not device:
                return False
            
            await self.db.delete(device)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting device: {e}")
            raise ValueError(f"Failed to delete device: {str(e)}")

    # CRUD Operations for Alerts
    async def create_alert(self, user_id: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new health alert"""
        try:
            from ..models.alerts import Alert, AlertType, AlertSeverity
            
            # Create the alert
            alert = Alert(
                user_id=user_id,
                alert_type=alert_data.get("alert_type", AlertType.GENERAL.value),
                title=alert_data.get("title"),
                message=alert_data.get("message"),
                severity=alert_data.get("severity", AlertSeverity.INFO.value),
                is_active=alert_data.get("is_active", True),
                expires_at=alert_data.get("expires_at")
            )
            
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            
            return {
                "id": str(alert.id),
                "user_id": str(alert.user_id),
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "is_active": alert.is_active,
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                "created_at": alert.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating alert: {e}")
            raise ValueError(f"Failed to create alert: {str(e)}")

    async def list_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """List all alerts for a user"""
        try:
            from ..models.alerts import Alert
            
            query = select(Alert).where(Alert.user_id == user_id)
            
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            
            return [
                {
                    "id": str(alert.id),
                    "user_id": str(alert.user_id),
                    "alert_type": alert.alert_type,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "is_active": alert.is_active,
                    "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Error listing alerts: {e}")
            raise ValueError(f"Failed to list alerts: {str(e)}")

    async def get_alert(self, user_id: str, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific alert by ID"""
        try:
            from ..models.alerts import Alert
            
            query = select(Alert).where(
                and_(
                    Alert.id == alert_id,
                    Alert.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                return None
            
            return {
                "id": str(alert.id),
                "user_id": str(alert.user_id),
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "is_active": alert.is_active,
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                "created_at": alert.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving alert: {e}")
            raise ValueError(f"Failed to retrieve alert: {str(e)}")

    async def update_alert(self, user_id: str, alert_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an alert"""
        try:
            from ..models.alerts import Alert
            
            query = select(Alert).where(
                and_(
                    Alert.id == alert_id,
                    Alert.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(alert, field):
                    setattr(alert, field, value)
            
            alert.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(alert)
            
            return {
                "id": str(alert.id),
                "user_id": str(alert.user_id),
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "is_active": alert.is_active,
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                "created_at": alert.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating alert: {e}")
            raise ValueError(f"Failed to update alert: {str(e)}")

    async def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """Delete an alert"""
        try:
            from ..models.alerts import Alert
            
            query = select(Alert).where(
                and_(
                    Alert.id == alert_id,
                    Alert.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                return False
            
            await self.db.delete(alert)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting alert: {e}")
            raise ValueError(f"Failed to delete alert: {str(e)}")

    # Analytics methods for API endpoints
    async def analyze_trends(self, user_id: str, metric_type: MetricType, days: int = 30) -> Dict[str, Any]:
        """Analyze trends for a specific metric"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "metric_type": metric_type,
                    "period_days": days,
                    "data_points": 0,
                    "trend": "insufficient_data"
                }
            
            values = [m.value for m in metrics if m.value is not None]
            
            if len(values) < 2:
                return {
                    "metric_type": metric_type,
                    "period_days": days,
                    "data_points": len(values),
                    "trend": "insufficient_data"
                }
            
            # Calculate trend
            trend = "stable"
            if len(values) >= 2:
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                if first_half and second_half:
                    first_avg = statistics.mean(first_half)
                    second_avg = statistics.mean(second_half)
                    if second_avg > first_avg * 1.05:
                        trend = "increasing"
                    elif second_avg < first_avg * 0.95:
                        trend = "decreasing"
            
            return {
                "metric_type": metric_type,
                "period_days": days,
                "data_points": len(values),
                "current_value": values[-1] if values else None,
                "average": statistics.mean(values) if values else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "trend": trend
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise ValueError(f"Failed to analyze trends: {str(e)}")

    async def detect_anomalies(self, user_id: str, metric_type: MetricType, threshold: float = 2.0) -> Dict[str, Any]:
        """Detect anomalies in health metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "metric_type": metric_type,
                    "anomalies": [],
                    "total_data_points": 0
                }
            
            values = [m.value for m in metrics if m.value is not None]
            
            if len(values) < 3:
                return {
                    "metric_type": metric_type,
                    "anomalies": [],
                    "total_data_points": len(values)
                }
            
            # Calculate statistics for anomaly detection
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0
            
            anomalies = []
            for i, metric in enumerate(metrics):
                if metric.value is not None:
                    z_score = abs((metric.value - mean_val) / std_val) if std_val > 0 else 0
                    if z_score > threshold:
                        anomalies.append({
                            "timestamp": metric.timestamp.isoformat(),
                            "value": metric.value,
                            "z_score": z_score,
                            "severity": "high" if z_score > 3.0 else "medium"
                        })
            
            return {
                "metric_type": metric_type,
                "anomalies": anomalies,
                "total_data_points": len(values),
                "anomaly_count": len(anomalies)
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise ValueError(f"Failed to detect anomalies: {str(e)}")

    async def analyze_correlation(self, user_id: str, metric_type1: MetricType, metric_type2: MetricType, days: int = 30) -> Dict[str, Any]:
        """Analyze correlation between two metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get both metrics
            query1 = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type1,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            query2 = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type2,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result1 = await self.db.execute(query1)
            result2 = await self.db.execute(query2)
            
            metrics1 = result1.scalars().all()
            metrics2 = result2.scalars().all()
            
            if not metrics1 or not metrics2:
                return {
                    "metric1": metric_type1,
                    "metric2": metric_type2,
                    "correlation": None,
                    "data_points": 0
                }
            
            # Create time series and align data points
            # This is a simplified approach - in production, you'd want more sophisticated time alignment
            values1 = [m.value for m in metrics1 if m.value is not None]
            values2 = [m.value for m in metrics2 if m.value is not None]
            
            if len(values1) < 2 or len(values2) < 2:
                return {
                    "metric1": metric_type1,
                    "metric2": metric_type2,
                    "correlation": None,
                    "data_points": min(len(values1), len(values2))
                }
            
            # Calculate correlation (simplified - using the shorter series)
            min_len = min(len(values1), len(values2))
            aligned_values1 = values1[:min_len]
            aligned_values2 = values2[:min_len]
            
            if len(aligned_values1) < 2:
                return {
                    "metric1": metric_type1,
                    "metric2": metric_type2,
                    "correlation": None,
                    "data_points": len(aligned_values1)
                }
            
            # Calculate Pearson correlation
            try:
                correlation = statistics.correlation(aligned_values1, aligned_values2)
            except:
                correlation = 0.0
            
            return {
                "metric1": metric_type1,
                "metric2": metric_type2,
                "correlation": correlation,
                "data_points": len(aligned_values1),
                "strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.3 else "weak"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlation: {e}")
            raise ValueError(f"Failed to analyze correlation: {str(e)}")

    async def recognize_patterns(self, user_id: str, metric_type: MetricType, pattern_type: str = "daily") -> Dict[str, Any]:
        """Recognize patterns in health metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "metric_type": metric_type,
                    "pattern_type": pattern_type,
                    "patterns": [],
                    "data_points": 0
                }
            
            # Simple pattern recognition - looking for daily patterns
            patterns = []
            
            if pattern_type == "daily":
                # Group by hour of day
                hourly_data = {}
                for metric in metrics:
                    if metric.value is not None:
                        hour = metric.timestamp.hour
                        if hour not in hourly_data:
                            hourly_data[hour] = []
                        hourly_data[hour].append(metric.value)
                
                # Find peak hours
                for hour, values in hourly_data.items():
                    if len(values) >= 3:
                        avg_value = statistics.mean(values)
                        patterns.append({
                            "type": "daily_peak",
                            "hour": hour,
                            "average_value": avg_value,
                            "data_points": len(values)
                        })
            
            return {
                "metric_type": metric_type,
                "pattern_type": pattern_type,
                "patterns": patterns,
                "data_points": len(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error recognizing patterns: {e}")
            raise ValueError(f"Failed to recognize patterns: {str(e)}")

    async def predict_metrics(self, user_id: str, metric_type: MetricType, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict future metric values"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "metric_type": metric_type,
                    "predictions": [],
                    "confidence": "low",
                    "data_points": 0
                }
            
            values = [m.value for m in metrics if m.value is not None]
            
            if len(values) < 3:
                return {
                    "metric_type": metric_type,
                    "predictions": [],
                    "confidence": "low",
                    "data_points": len(values)
                }
            
            # Simple linear prediction
            # In production, you'd use more sophisticated ML models
            recent_values = values[-7:] if len(values) >= 7 else values
            
            if len(recent_values) < 2:
                return {
                    "metric_type": metric_type,
                    "predictions": [],
                    "confidence": "low",
                    "data_points": len(values)
                }
            
            # Calculate trend
            x = list(range(len(recent_values)))
            y = recent_values
            
            # Simple linear regression
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
            intercept = (sum_y - slope * sum_x) / n
            
            # Generate predictions
            predictions = []
            current_date = datetime.utcnow()
            
            for i in range(1, days_ahead + 1):
                predicted_value = intercept + slope * (len(recent_values) + i)
                prediction_date = current_date + timedelta(days=i)
                
                predictions.append({
                    "date": prediction_date.isoformat(),
                    "predicted_value": round(predicted_value, 2),
                    "confidence": "medium" if len(values) >= 10 else "low"
                })
            
            return {
                "metric_type": metric_type,
                "predictions": predictions,
                "confidence": "high" if len(values) >= 20 else "medium" if len(values) >= 10 else "low",
                "data_points": len(values),
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            }
            
        except Exception as e:
            logger.error(f"Error predicting metrics: {e}")
            raise ValueError(f"Failed to predict metrics: {str(e)}")

    async def get_analytics_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            # Get all metrics for the user
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            )
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "total_metrics": 0,
                    "metric_types": [],
                    "trends": {},
                    "anomalies": {},
                    "data_completeness": 0.0
                }
            
            # Group by metric type
            metrics_by_type = {}
            for metric in metrics:
                if metric.metric_type not in metrics_by_type:
                    metrics_by_type[metric.metric_type] = []
                metrics_by_type[metric.metric_type].append(metric)
            
            summary = {
                "total_metrics": len(metrics),
                "metric_types": list(metrics_by_type.keys()),
                "trends": {},
                "anomalies": {},
                "data_completeness": len(metrics) / (len(metrics_by_type) * 30) if metrics_by_type else 0.0
            }
            
            # Calculate trends for each metric type
            for metric_type, type_metrics in metrics_by_type.items():
                values = [m.value for m in type_metrics if m.value is not None]
                if len(values) >= 2:
                    first_half = values[:len(values)//2]
                    second_half = values[len(values)//2:]
                    if first_half and second_half:
                        first_avg = statistics.mean(first_half)
                        second_avg = statistics.mean(second_half)
                        if second_avg > first_avg * 1.05:
                            summary["trends"][metric_type] = "increasing"
                        elif second_avg < first_avg * 0.95:
                            summary["trends"][metric_type] = "decreasing"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            raise ValueError(f"Failed to get analytics summary: {str(e)}")

    async def generate_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate health recommendations based on analytics"""
        try:
            # Get recent metrics
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            )
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            recommendations = []
            
            if not metrics:
                recommendations.append({
                    "type": "data_collection",
                    "title": "Start Tracking Your Health",
                    "description": "Begin recording your health metrics to get personalized insights.",
                    "priority": "high"
                })
                return recommendations
            
            # Analyze metrics and generate recommendations
            metrics_by_type = {}
            for metric in metrics:
                if metric.metric_type not in metrics_by_type:
                    metrics_by_type[metric.metric_type] = []
                metrics_by_type[metric.metric_type].append(metric)
            
            for metric_type, type_metrics in metrics_by_type.items():
                values = [m.value for m in type_metrics if m.value is not None]
                if values:
                    latest_value = values[-1]
                    avg_value = statistics.mean(values)
                    
                    # Generate recommendations based on metric type and values
                    if metric_type == MetricType.STEPS:
                        if latest_value < 8000:
                            recommendations.append({
                                "type": "activity",
                                "title": "Increase Daily Steps",
                                "description": f"Your average is {int(avg_value)} steps. Aim for 10,000 steps daily.",
                                "priority": "medium"
                            })
                    
                    elif metric_type == MetricType.HEART_RATE:
                        if latest_value > 100:
                            recommendations.append({
                                "type": "health",
                                "title": "Monitor Heart Rate",
                                "description": "Your heart rate is elevated. Consider stress management techniques.",
                                "priority": "high"
                            })
            
            return recommendations[:5]  # Limit to top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise ValueError(f"Failed to generate recommendations: {str(e)}")

    async def analyze_goal_progress(self, user_id: str) -> Dict[str, Any]:
        """Analyze progress towards health goals"""
        try:
            # Get active goals
            query = select(HealthGoal).where(
                and_(
                    HealthGoal.user_id == user_id,
                    HealthGoal.status == GoalStatus.ACTIVE
                )
            )
            
            result = await self.db.execute(query)
            goals = result.scalars().all()
            
            if not goals:
                return {
                    "active_goals": 0,
                    "goals_progress": [],
                    "overall_progress": 0.0
                }
            
            goals_progress = []
            total_progress = 0.0
            
            for goal in goals:
                # Get metrics for this goal
                metrics_query = select(HealthMetric).where(
                    and_(
                        HealthMetric.user_id == user_id,
                        HealthMetric.metric_type == goal.metric_type,
                        HealthMetric.timestamp >= goal.start_date,
                        HealthMetric.timestamp <= goal.target_date
                    )
                ).order_by(desc(HealthMetric.timestamp))
                
                result = await self.db.execute(metrics_query)
                metrics = result.scalars().all()
                
                current_value = metrics[0].value if metrics else 0
                progress_percentage = min((current_value / goal.target_value) * 100, 100) if goal.target_value > 0 else 0
                
                goals_progress.append({
                    "goal_id": str(goal.id),
                    "title": goal.title,
                    "current_value": current_value,
                    "target_value": goal.target_value,
                    "progress_percentage": progress_percentage,
                    "days_remaining": (goal.target_date - datetime.utcnow().date()).days
                })
                
                total_progress += progress_percentage
            
            return {
                "active_goals": len(goals),
                "goals_progress": goals_progress,
                "overall_progress": total_progress / len(goals) if goals else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing goal progress: {e}")
            raise ValueError(f"Failed to analyze goal progress: {str(e)}")

    async def export_analytics_data(self, user_id: str, format: str = "json", start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Export analytics data in various formats"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get all metrics for the period
            query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            # Format data
            data = []
            for metric in metrics:
                data.append({
                    "id": str(metric.id),
                    "metric_type": metric.metric_type,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "source": metric.source,
                    "device_id": metric.device_id
                })
            
            return {
                "format": format,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_records": len(data),
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            raise ValueError(f"Failed to export analytics data: {str(e)}")

    # Analytics methods (existing ones)
    @with_resilience("health_analytics", max_concurrent=10, timeout=60.0, max_retries=3)
    async def generate_health_summary(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate comprehensive health summary for a user"""
        try:
            # Get metrics for the period
            metrics_query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await db.execute(metrics_query)
            metrics = result.scalars().all()
            
            # Get goals
            goals_query = select(HealthGoal).where(
                and_(
                    HealthGoal.user_id == user_id,
                    HealthGoal.status == GoalStatus.ACTIVE
                )
            )
            
            result = await db.execute(goals_query)
            goals = result.scalars().all()
            
            # Generate summary
            summary = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_days": (end_date - start_date).days
                },
                "metrics_overview": await self._generate_metrics_overview(metrics),
                "trends": await self._generate_trends(metrics),
                "goals_progress": await self._generate_goals_progress(goals, metrics),
                "health_score": await self._calculate_health_score(metrics),
                "recommendations": await self._generate_recommendations(metrics, goals)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating health summary: {e}")
            raise
    
    @with_resilience("health_analytics", max_concurrent=10, timeout=60.0, max_retries=3)
    async def generate_metric_trends(
        self,
        user_id: UUID,
        metric_type: MetricType,
        period: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate trends for a specific metric"""
        try:
            # Calculate date range based on period
            end_date = datetime.utcnow()
            if period == "1d":
                start_date = end_date - timedelta(days=1)
                group_by = "hour"
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
                group_by = "day"
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
                group_by = "day"
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
                group_by = "week"
            else:
                start_date = end_date - timedelta(days=7)
                group_by = "day"
            
            # Get metrics
            metrics_query = select(HealthMetric).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.timestamp >= start_date,
                    HealthMetric.timestamp <= end_date
                )
            ).order_by(HealthMetric.timestamp)
            
            result = await db.execute(metrics_query)
            metrics = result.scalars().all()
            
            # Generate trends
            trends = {
                "metric_type": metric_type,
                "period": period,
                "data_points": len(metrics),
                "current_value": metrics[-1].value if metrics else None,
                "previous_value": metrics[-2].value if len(metrics) > 1 else None,
                "change": self._calculate_change(metrics),
                "trend_direction": self._determine_trend_direction(metrics),
                "statistics": self._calculate_statistics(metrics),
                "time_series": self._generate_time_series(metrics, group_by)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error generating metric trends: {e}")
            raise
    
    async def _generate_metrics_overview(self, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """Generate overview of metrics"""
        if not metrics:
            return {"total_metrics": 0, "metric_types": []}
        
        # Group by metric type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        overview = {
            "total_metrics": len(metrics),
            "metric_types": list(metrics_by_type.keys()),
            "metrics_by_type": {}
        }
        
        for metric_type, type_metrics in metrics_by_type.items():
            values = [m.value for m in type_metrics]
            overview["metrics_by_type"][metric_type] = {
                "count": len(type_metrics),
                "latest_value": type_metrics[-1].value if type_metrics else None,
                "average": statistics.mean(values) if values else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "unit": type_metrics[0].unit if type_metrics else None
            }
        
        return overview
    
    async def _generate_trends(self, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """Generate trends from metrics"""
        if not metrics:
            return {"trends": []}
        
        trends = []
        
        # Group by metric type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        for metric_type, type_metrics in metrics_by_type.items():
            if len(type_metrics) < 2:
                continue
            
            # Sort by timestamp
            type_metrics.sort(key=lambda x: x.timestamp)
            
            # Calculate trend
            first_value = type_metrics[0].value
            last_value = type_metrics[-1].value
            change = last_value - first_value
            change_percent = (change / first_value * 100) if first_value != 0 else 0
            
            trend = {
                "metric_type": metric_type,
                "direction": "up" if change > 0 else "down" if change < 0 else "stable",
                "change": change,
                "change_percent": change_percent,
                "first_value": first_value,
                "last_value": last_value,
                "unit": type_metrics[0].unit,
                "data_points": len(type_metrics)
            }
            
            trends.append(trend)
        
        return {"trends": trends}
    
    async def _generate_goals_progress(self, goals: List[HealthGoal], metrics: List[HealthMetric]) -> Dict[str, Any]:
        """Generate goals progress"""
        if not goals:
            return {"total_goals": 0, "goals": []}
        
        goals_progress = {
            "total_goals": len(goals),
            "active_goals": len([g for g in goals if g.status == GoalStatus.ACTIVE]),
            "completed_goals": len([g for g in goals if g.status == GoalStatus.COMPLETED]),
            "goals": []
        }
        
        for goal in goals:
            # Find relevant metrics for this goal
            relevant_metrics = [
                m for m in metrics 
                if m.metric_type == goal.metric_type
            ]
            
            if relevant_metrics:
                # Update goal with current value
                goal.current_value = relevant_metrics[-1].value
                goal.progress = goal.calculate_progress()
            
            goal_data = {
                "id": str(goal.id),
                "title": goal.title,
                "metric_type": goal.metric_type,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "progress": goal.progress,
                "status": goal.status,
                "is_completed": goal.is_completed(),
                "is_overdue": goal.is_overdue()
            }
            
            goals_progress["goals"].append(goal_data)
        
        return goals_progress
    
    async def _calculate_health_score(self, metrics: List[HealthMetric]) -> Dict[str, Any]:
        """Calculate overall health score"""
        if not metrics:
            return {"score": 0, "factors": []}
        
        # Define health factors and their weights
        health_factors = {
            MetricType.WEIGHT: {"weight": 0.15, "optimal_range": (18.5, 25.0)},
            MetricType.HEART_RATE: {"weight": 0.20, "optimal_range": (60, 100)},
            MetricType.BLOOD_PRESSURE_SYSTOLIC: {"weight": 0.15, "optimal_range": (90, 140)},
            MetricType.STEPS: {"weight": 0.10, "optimal_range": (8000, float('inf'))},
            MetricType.SLEEP_DURATION: {"weight": 0.15, "optimal_range": (7, 9)},
            MetricType.MOOD: {"weight": 0.10, "optimal_range": (7, 10)},
            MetricType.ENERGY_LEVEL: {"weight": 0.15, "optimal_range": (7, 10)}
        }
        
        total_score = 0
        factors = []
        
        for metric_type, factor_config in health_factors.items():
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            
            if type_metrics:
                latest_value = type_metrics[-1].value
                optimal_min, optimal_max = factor_config["optimal_range"]
                
                # Calculate factor score (0-100)
                if latest_value >= optimal_min and latest_value <= optimal_max:
                    factor_score = 100
                elif latest_value < optimal_min:
                    factor_score = max(0, 100 - ((optimal_min - latest_value) / optimal_min * 50))
                else:
                    factor_score = max(0, 100 - ((latest_value - optimal_max) / optimal_max * 50))
                
                factor_data = {
                    "metric_type": metric_type,
                    "value": latest_value,
                    "optimal_range": factor_config["optimal_range"],
                    "score": factor_score,
                    "weight": factor_config["weight"]
                }
                
                factors.append(factor_data)
                total_score += factor_score * factor_config["weight"]
        
        return {
            "score": round(total_score, 1),
            "factors": factors,
            "interpretation": self._interpret_health_score(total_score)
        }
    
    async def _generate_recommendations(self, metrics: List[HealthMetric], goals: List[HealthGoal]) -> List[Dict[str, Any]]:
        """Generate health recommendations"""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # Generate recommendations based on metrics
        for metric_type, type_metrics in metrics_by_type.items():
            if len(type_metrics) < 2:
                continue
            
            latest_metric = type_metrics[-1]
            trend = self._determine_trend_direction(type_metrics)
            
            # Generate recommendation based on metric type and trend
            recommendation = self._generate_metric_recommendation(
                metric_type, latest_metric, trend, type_metrics
            )
            
            if recommendation:
                recommendations.append(recommendation)
        
        # Generate goal-based recommendations
        for goal in goals:
            if goal.status == GoalStatus.ACTIVE and goal.is_overdue():
                recommendation = {
                    "type": "goal_reminder",
                    "title": f"Goal Reminder: {goal.title}",
                    "description": f"Your goal '{goal.title}' is overdue. Consider reviewing your progress and adjusting your strategy.",
                    "priority": "medium",
                    "related_goal_id": str(goal.id)
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_change(self, metrics: List[HealthMetric]) -> Optional[float]:
        """Calculate change between first and last metric"""
        if len(metrics) < 2:
            return None
        
        return metrics[-1].value - metrics[0].value
    
    def _determine_trend_direction(self, metrics: List[HealthMetric]) -> str:
        """Determine trend direction"""
        if len(metrics) < 2:
            return "stable"
        
        # Simple trend analysis
        values = [m.value for m in metrics]
        if len(values) < 3:
            return "stable" if values[-1] == values[0] else "up" if values[-1] > values[0] else "down"
        
        # Use linear regression for better trend detection
        try:
            slope = statistics.linear_regression(range(len(values)), values)[0]
            if abs(slope) < 0.01:  # Threshold for stable
                return "stable"
            return "up" if slope > 0 else "down"
        except:
            # Fallback to simple comparison
            return "stable" if values[-1] == values[0] else "up" if values[-1] > values[0] else "down"
    
    def _calculate_statistics(self, metrics: List[HealthMetric]) -> Dict[str, float]:
        """Calculate statistics for metrics"""
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def _generate_time_series(self, metrics: List[HealthMetric], group_by: str) -> List[Dict[str, Any]]:
        """Generate time series data"""
        if not metrics:
            return []
        
        # Group metrics by time period
        grouped_data = {}
        for metric in metrics:
            if group_by == "hour":
                key = metric.timestamp.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = metric.timestamp.strftime("%Y-%m-%d")
            elif group_by == "week":
                key = metric.timestamp.strftime("%Y-W%U")
            else:
                key = metric.timestamp.strftime("%Y-%m-%d")
            
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(metric.value)
        
        # Calculate average for each period
        time_series = []
        for period, values in sorted(grouped_data.items()):
            time_series.append({
                "period": period,
                "value": statistics.mean(values),
                "count": len(values)
            })
        
        return time_series
    
    def _interpret_health_score(self, score: float) -> str:
        """Interpret health score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _generate_metric_recommendation(
        self,
        metric_type: str,
        latest_metric: HealthMetric,
        trend: str,
        all_metrics: List[HealthMetric]
    ) -> Optional[Dict[str, Any]]:
        """Generate a recommendation for a specific metric"""
        try:
            # Base recommendation structure
            recommendation = {
                "metric_type": metric_type,
                "current_value": latest_metric.value,
                "trend": trend,
                "recommendation_type": "improvement",
                "priority": "medium",
                "description": "",
                "actions": [],
                "knowledge_graph_context": {}
            }
            
            # Generate specific recommendations based on metric type and trend
            if metric_type == MetricType.HEART_RATE:
                if latest_metric.value > 100:
                    recommendation.update({
                        "recommendation_type": "alert",
                        "priority": "high",
                        "description": "Heart rate is elevated. Consider stress management techniques.",
                        "actions": ["Practice deep breathing", "Reduce caffeine intake", "Get adequate sleep"]
                    })
                elif latest_metric.value < 60:
                    recommendation.update({
                        "recommendation_type": "monitor",
                        "priority": "medium",
                        "description": "Heart rate is low. Monitor for symptoms.",
                        "actions": ["Check for dizziness", "Monitor energy levels", "Consult healthcare provider if symptoms persist"]
                    })
                    
            elif metric_type == MetricType.BLOOD_PRESSURE:
                systolic = latest_metric.value
                if systolic > 140:
                    recommendation.update({
                        "recommendation_type": "alert",
                        "priority": "high",
                        "description": "Blood pressure is elevated. Consider lifestyle changes.",
                        "actions": ["Reduce salt intake", "Exercise regularly", "Manage stress"]
                    })
                    
            elif metric_type == MetricType.BLOOD_GLUCOSE:
                if latest_metric.value > 140:
                    recommendation.update({
                        "recommendation_type": "alert",
                        "priority": "high",
                        "description": "Blood glucose is elevated. Monitor diet and activity.",
                        "actions": ["Check carbohydrate intake", "Exercise after meals", "Monitor symptoms"]
                    })
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating metric recommendation: {e}")
            return None

    # Knowledge Graph Integration Methods
    async def enrich_health_metrics_with_knowledge_graph(
        self, 
        metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enrich health metrics with knowledge graph entities and medical context.
        
        Args:
            metrics: List of health metrics to enrich
            
        Returns:
            Dict[str, Any]: Enriched metrics with knowledge graph context
        """
        try:
            async with KnowledgeGraphClient() as client:
                enriched_metrics = []
                total_entities_found = 0
                
                for metric in metrics:
                    # Create medical text from metric
                    metric_text = f"{metric.get('metric_type', '')} {metric.get('value', '')} {metric.get('unit', '')}"
                    
                    # Search for related medical entities
                    entities = await client.search_entities(metric_text, limit=5)
                    
                    # Get related medical information
                    related_conditions = []
                    related_treatments = []
                    
                    for entity in entities:
                        entity_type = entity.get("type", "").lower()
                        if entity_type == "condition":
                            related_conditions.append(entity)
                        elif entity_type == "treatment":
                            related_treatments.append(entity)
                    
                    # Enrich the metric
                    enriched_metric = {
                        **metric,
                        "knowledge_graph_entities": entities,
                        "related_conditions": related_conditions,
                        "related_treatments": related_treatments,
                        "enrichment_metadata": {
                            "entities_found": len(entities),
                            "conditions_identified": len(related_conditions),
                            "treatments_suggested": len(related_treatments)
                        }
                    }
                    
                    enriched_metrics.append(enriched_metric)
                    total_entities_found += len(entities)
                
                return {
                    "enriched_metrics": enriched_metrics,
                    "summary": {
                        "total_metrics": len(metrics),
                        "total_entities_found": total_entities_found,
                        "average_entities_per_metric": total_entities_found / len(metrics) if metrics else 0,
                        "enrichment_timestamp": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to enrich health metrics with knowledge graph: {e}")
            return {
                "enriched_metrics": metrics,
                "summary": {
                    "total_metrics": len(metrics),
                    "total_entities_found": 0,
                    "average_entities_per_metric": 0,
                    "error": str(e),
                    "enrichment_timestamp": datetime.utcnow().isoformat()
                }
            }

    async def generate_evidence_based_health_recommendations(
        self, 
        user_metrics: List[Dict[str, Any]],
        user_symptoms: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate evidence-based health recommendations using knowledge graph.
        
        Args:
            user_metrics: List of user health metrics
            user_symptoms: List of user symptoms (optional)
            
        Returns:
            Dict[str, Any]: Evidence-based health recommendations
        """
        try:
            async with KnowledgeGraphClient() as client:
                recommendations = {
                    "metric_based_recommendations": [],
                    "symptom_based_recommendations": [],
                    "lifestyle_recommendations": [],
                    "medical_recommendations": [],
                    "risk_assessments": []
                }
                
                # Extract conditions and symptoms from metrics
                conditions = []
                symptoms = []
                
                for metric in user_metrics:
                    metric_text = f"{metric.get('metric_type', '')} {metric.get('value', '')}"
                    entities = await client.search_entities(metric_text, limit=3)
                    
                    for entity in entities:
                        entity_type = entity.get("type", "").lower()
                        if entity_type == "condition":
                            conditions.append(entity.get("name", ""))
                        elif entity_type == "symptom":
                            symptoms.append(entity.get("name", ""))
                
                # Add symptoms from user input
                if user_symptoms:
                    for symptom in user_symptoms:
                        symptom_name = symptom.get("symptom_name", "")
                        if symptom_name:
                            symptoms.append(symptom_name)
                
                # Generate recommendations based on conditions
                for condition in conditions:
                    treatments = await client.get_condition_treatments(condition)
                    recommendations["medical_recommendations"].extend(treatments)
                
                # Generate recommendations based on symptoms
                for symptom in symptoms:
                    related_conditions = await client.search_entities(symptom, entity_type="condition", limit=2)
                    for condition in related_conditions:
                        condition_treatments = await client.get_condition_treatments(condition.get("name", ""))
                        recommendations["symptom_based_recommendations"].extend(condition_treatments)
                
                # Remove duplicates and limit results
                recommendations["medical_recommendations"] = list({r.get("id"): r for r in recommendations["medical_recommendations"]}.values())[:10]
                recommendations["symptom_based_recommendations"] = list({r.get("id"): r for r in recommendations["symptom_based_recommendations"]}.values())[:10]
                
                # Add metadata
                recommendations["metadata"] = {
                    "metrics_analyzed": len(user_metrics),
                    "symptoms_analyzed": len(symptoms),
                    "conditions_identified": len(conditions),
                    "total_medical_recommendations": len(recommendations["medical_recommendations"]),
                    "total_symptom_recommendations": len(recommendations["symptom_based_recommendations"]),
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
                
                return recommendations
                
        except Exception as e:
            logger.error(f"Failed to generate evidence-based health recommendations: {e}")
            return {
                "metric_based_recommendations": [],
                "symptom_based_recommendations": [],
                "lifestyle_recommendations": [],
                "medical_recommendations": [],
                "risk_assessments": [],
                "metadata": {
                    "error": str(e),
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
            }

    async def validate_health_entities(
        self, 
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate health-related entities against the knowledge graph.
        
        Args:
            entities: List of health entities to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            async with KnowledgeGraphClient() as client:
                validation_results = {
                    "valid_entities": [],
                    "invalid_entities": [],
                    "suggestions": [],
                    "validation_summary": {}
                }
                
                for entity in entities:
                    entity_name = entity.get("name", "")
                    entity_type = entity.get("type", "")
                    
                    # Search for the entity in the knowledge graph
                    search_results = await client.search_entities(entity_name, entity_type=entity_type, limit=1)
                    
                    if search_results:
                        # Entity found - validate it
                        kg_entity = search_results[0]
                        validation_results["valid_entities"].append({
                            "original": entity,
                            "validated": kg_entity,
                            "confidence": kg_entity.get("similarity_score", 0.0)
                        })
                    else:
                        # Entity not found - add to invalid list
                        validation_results["invalid_entities"].append(entity)
                        
                        # Try to find similar entities for suggestions
                        similar_results = await client.search_entities(entity_name, limit=3)
                        if similar_results:
                            validation_results["suggestions"].append({
                                "original": entity,
                                "suggestions": similar_results
                            })
                
                # Generate summary
                validation_results["validation_summary"] = {
                    "total_entities": len(entities),
                    "valid_count": len(validation_results["valid_entities"]),
                    "invalid_count": len(validation_results["invalid_entities"]),
                    "suggestions_count": len(validation_results["suggestions"]),
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
                
                return validation_results
                
        except Exception as e:
            logger.error(f"Failed to validate health entities: {e}")
            return {
                "valid_entities": [],
                "invalid_entities": entities,
                "suggestions": [],
                "validation_summary": {
                    "error": str(e),
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
            }