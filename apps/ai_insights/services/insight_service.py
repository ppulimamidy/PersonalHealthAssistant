"""
Insight Service
Service for managing health insights and analysis results.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    InsightDB, InsightType, InsightSeverity, InsightStatus, InsightCategory,
    InsightCreate, InsightUpdate, InsightResponse,
    HealthPatternDB, HealthPatternCreate, HealthPatternUpdate, HealthPatternResponse,
    HealthScoreDB, HealthScoreCreate, HealthScoreUpdate, HealthScoreResponse
)
from ..agents.insight_generator_agent import InsightGeneratorAgent
from ..agents.pattern_detection_agent import PatternDetectionAgent
from common.utils.logging import get_logger
from common.clients.knowledge_graph_client import KnowledgeGraphClient
from ..utils import ensure_python_uuids


class InsightService:
    """Service for managing health insights and analysis."""
    
    def __init__(self):
        self.logger = get_logger("ai_insights.services.insight_service")
        
        # Initialize AI agents
        self.insight_generator = InsightGeneratorAgent()
        self.pattern_detector = PatternDetectionAgent()
    
    async def generate_insights(
        self, 
        patient_id: UUID, 
        data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate insights for a patient using AI agents.
        
        Args:
            patient_id: Patient ID
            data: Health data for analysis
            db: Database session
            
        Returns:
            Dict[str, Any]: Generated insights and metadata
        """
        try:
            self.logger.info(f"🚀 Starting insight generation for patient {patient_id}")
            
            # Add patient_id to data
            data['patient_id'] = patient_id
            
            # Generate insights using AI agents
            insight_result = await self.insight_generator.execute(data, db)
            
            # Generate patterns
            pattern_result = await self.pattern_detector.execute(data, db)
            
            # Combine results
            combined_result = {
                'insights': insight_result.insights or [],
                'patterns': pattern_result.patterns or [],
                'recommendations': insight_result.recommendations or [],
                'metadata': {
                    'total_insights': len(insight_result.insights or []),
                    'total_patterns': len(pattern_result.patterns or []),
                    'total_recommendations': len(insight_result.recommendations or []),
                    'generation_timestamp': datetime.utcnow().isoformat(),
                    'insight_confidence': insight_result.confidence_score,
                    'pattern_confidence': pattern_result.confidence_score
                }
            }
            
            self.logger.info(f"✅ Insight generation completed for patient {patient_id}")
            return combined_result
            
        except Exception as e:
            self.logger.error(f"❌ Insight generation failed for patient {patient_id}: {e}")
            raise
    
    async def get_insights(
        self, 
        patient_id: UUID, 
        db: AsyncSession,
        insight_type: Optional[InsightType] = None,
        category: Optional[InsightCategory] = None,
        severity: Optional[InsightSeverity] = None,
        status: Optional[InsightStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[InsightResponse]:
        """
        Get insights for a patient with optional filtering.
        
        Args:
            patient_id: Patient ID
            db: Database session
            insight_type: Filter by insight type
            category: Filter by category
            severity: Filter by severity
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[InsightResponse]: List of insights
        """
        try:
            # Build query
            query = select(InsightDB).where(InsightDB.patient_id == patient_id)
            
            if insight_type:
                query = query.where(InsightDB.insight_type == insight_type)
            if category:
                query = query.where(InsightDB.category == category)
            if severity:
                query = query.where(InsightDB.severity == severity)
            if status:
                query = query.where(InsightDB.status == status)
            
            # Order by creation date (newest first)
            query = query.order_by(desc(InsightDB.created_at))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(query)
            insights = result.scalars().all()
            
            # Convert to response models
            return [InsightResponse.from_orm(ensure_python_uuids(insight)) for insight in insights]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get insights for patient {patient_id}: {e}")
            raise
    
    async def get_insight_by_id(
        self, 
        insight_id: UUID, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> Optional[InsightResponse]:
        """
        Get a specific insight by ID.
        
        Args:
            insight_id: Insight ID
            patient_id: Patient ID
            db: Database session
            
        Returns:
            Optional[InsightResponse]: Insight if found
        """
        try:
            query = select(InsightDB).where(
                and_(
                    InsightDB.id == insight_id,
                    InsightDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            insight = result.scalar_one_or_none()
            
            if insight:
                return InsightResponse.from_orm(ensure_python_uuids(insight))
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get insight {insight_id}: {e}")
            raise
    
    async def create_insight(
        self, 
        insight_data: InsightCreate, 
        db: AsyncSession
    ) -> InsightResponse:
        """
        Create a new insight.
        
        Args:
            insight_data: Insight creation data
            db: Database session
            
        Returns:
            InsightResponse: Created insight
        """
        try:
            # Create insight record
            insight_db = InsightDB(**insight_data.dict())
            db.add(insight_db)
            await db.flush()
            await db.refresh(insight_db)
            
            self.logger.info(f"✅ Created insight {insight_db.id} for patient {insight_data.patient_id}")
            
            return InsightResponse.from_orm(ensure_python_uuids(insight_db))
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create insight: {e}")
            raise
    
    async def update_insight(
        self, 
        insight_id: UUID, 
        patient_id: UUID, 
        update_data: InsightUpdate, 
        db: AsyncSession
    ) -> Optional[InsightResponse]:
        """
        Update an existing insight.
        
        Args:
            insight_id: Insight ID
            patient_id: Patient ID
            update_data: Update data
            db: Database session
            
        Returns:
            Optional[InsightResponse]: Updated insight if found
        """
        try:
            # Get existing insight
            query = select(InsightDB).where(
                and_(
                    InsightDB.id == insight_id,
                    InsightDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(insight, field, value)
            
            insight.updated_at = datetime.utcnow()
            
            await db.flush()
            await db.refresh(insight)
            
            self.logger.info(f"✅ Updated insight {insight_id}")
            
            return InsightResponse.from_orm(ensure_python_uuids(insight))
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update insight {insight_id}: {e}")
            raise
    
    async def delete_insight(
        self, 
        insight_id: UUID, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> bool:
        """
        Delete an insight.
        
        Args:
            insight_id: Insight ID
            patient_id: Patient ID
            db: Database session
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Get existing insight
            query = select(InsightDB).where(
                and_(
                    InsightDB.id == insight_id,
                    InsightDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            insight = result.scalar_one_or_none()
            
            if not insight:
                return False
            
            # Soft delete by setting status to archived
            insight.status = InsightStatus.ARCHIVED
            insight.updated_at = datetime.utcnow()
            
            await db.flush()
            
            self.logger.info(f"✅ Archived insight {insight_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete insight {insight_id}: {e}")
            raise
    
    async def get_insights_summary(
        self, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get summary statistics for patient insights.
        
        Args:
            patient_id: Patient ID
            db: Database session
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        try:
            # Get total counts by category
            category_query = select(
                InsightDB.category,
                func.count(InsightDB.id).label('count')
            ).where(
                and_(
                    InsightDB.patient_id == patient_id,
                    InsightDB.status == InsightStatus.ACTIVE
                )
            ).group_by(InsightDB.category)
            
            result = await db.execute(category_query)
            category_counts = {row.category: row.count for row in result}
            
            # Get total counts by severity
            severity_query = select(
                InsightDB.severity,
                func.count(InsightDB.id).label('count')
            ).where(
                and_(
                    InsightDB.patient_id == patient_id,
                    InsightDB.status == InsightStatus.ACTIVE
                )
            ).group_by(InsightDB.severity)
            
            result = await db.execute(severity_query)
            severity_counts = {row.severity: row.count for row in result}
            
            # Get recent insights
            recent_query = select(InsightDB).where(
                and_(
                    InsightDB.patient_id == patient_id,
                    InsightDB.status == InsightStatus.ACTIVE
                )
            ).order_by(desc(InsightDB.created_at)).limit(5)
            
            result = await db.execute(recent_query)
            recent_insights = result.scalars().all()
            
            # Get average confidence score
            confidence_query = select(func.avg(InsightDB.confidence_score)).where(
                and_(
                    InsightDB.patient_id == patient_id,
                    InsightDB.status == InsightStatus.ACTIVE
                )
            )
            
            result = await db.execute(confidence_query)
            avg_confidence = result.scalar() or 0.0
            
            return {
                'total_insights': sum(category_counts.values()),
                'insights_by_category': category_counts,
                'insights_by_severity': severity_counts,
                'average_confidence': float(avg_confidence),
                'recent_insights': [
                    {
                        'id': str(insight.id),
                        'title': insight.title,
                        'category': insight.category,
                        'severity': insight.severity,
                        'created_at': insight.created_at.isoformat()
                    }
                    for insight in recent_insights
                ],
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get insights summary for patient {patient_id}: {e}")
            raise
    
    async def get_health_patterns(
        self, 
        patient_id: UUID, 
        db: AsyncSession,
        pattern_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HealthPatternResponse]:
        """
        Get health patterns for a patient.
        
        Args:
            patient_id: Patient ID
            db: Database session
            pattern_type: Filter by pattern type
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[HealthPatternResponse]: List of health patterns
        """
        try:
            # Build query
            query = select(HealthPatternDB).where(HealthPatternDB.patient_id == patient_id)
            
            if pattern_type:
                query = query.where(HealthPatternDB.pattern_type == pattern_type)
            
            # Order by last observed (newest first)
            query = query.order_by(desc(HealthPatternDB.last_observed))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(query)
            patterns = result.scalars().all()
            
            # Convert to response models
            return [HealthPatternResponse.from_orm(pattern) for pattern in patterns]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get health patterns for patient {patient_id}: {e}")
            raise
    
    async def get_health_scores(
        self, 
        patient_id: UUID, 
        db: AsyncSession,
        score_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HealthScoreResponse]:
        """
        Get health scores for a patient.
        
        Args:
            patient_id: Patient ID
            db: Database session
            score_type: Filter by score type
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[HealthScoreResponse]: List of health scores
        """
        try:
            # Build query
            query = select(HealthScoreDB).where(HealthScoreDB.patient_id == patient_id)
            
            if score_type:
                query = query.where(HealthScoreDB.score_type == score_type)
            
            # Order by calculation date (newest first)
            query = query.order_by(desc(HealthScoreDB.calculated_at))
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = await db.execute(query)
            scores = result.scalars().all()
            
            # Convert to response models
            return [HealthScoreResponse.from_orm(score) for score in scores]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get health scores for patient {patient_id}: {e}")
            raise
    
    async def search_insights(
        self, 
        patient_id: UUID, 
        search_term: str, 
        db: AsyncSession,
        limit: int = 20
    ) -> List[InsightResponse]:
        """
        Search insights by title or description.
        
        Args:
            patient_id: Patient ID
            search_term: Search term
            db: Database session
            limit: Maximum number of results
            
        Returns:
            List[InsightResponse]: List of matching insights
        """
        try:
            # Build search query
            query = select(InsightDB).where(
                and_(
                    InsightDB.patient_id == patient_id,
                    InsightDB.status == InsightStatus.ACTIVE,
                    or_(
                        InsightDB.title.ilike(f"%{search_term}%"),
                        InsightDB.description.ilike(f"%{search_term}%"),
                        InsightDB.summary.ilike(f"%{search_term}%")
                    )
                )
            ).order_by(desc(InsightDB.created_at)).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            insights = result.scalars().all()
            
            # Convert to response models
            return [InsightResponse.from_orm(ensure_python_uuids(insight)) for insight in insights]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to search insights for patient {patient_id}: {e}")
            raise
    
    async def get_insights_timeline(
        self, 
        patient_id: UUID, 
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get insights timeline for a date range.
        
        Args:
            patient_id: Patient ID
            start_date: Start date
            end_date: End date
            db: Database session
            
        Returns:
            List[Dict[str, Any]]: Timeline of insights
        """
        try:
            # Get insights in date range
            query = select(InsightDB).where(
                and_(
                    InsightDB.patient_id == patient_id,
                    InsightDB.status == InsightStatus.ACTIVE,
                    InsightDB.created_at >= start_date,
                    InsightDB.created_at <= end_date
                )
            ).order_by(InsightDB.created_at)
            
            result = await db.execute(query)
            insights = result.scalars().all()
            
            # Group by date
            timeline = {}
            for insight in insights:
                date_key = insight.created_at.date().isoformat()
                if date_key not in timeline:
                    timeline[date_key] = []
                
                timeline[date_key].append({
                    'id': str(insight.id),
                    'title': insight.title,
                    'category': insight.category,
                    'severity': insight.severity,
                    'confidence_score': insight.confidence_score,
                    'created_at': insight.created_at.isoformat()
                })
            
            # Convert to sorted list
            timeline_list = [
                {
                    'date': date,
                    'insights': insights
                }
                for date, insights in sorted(timeline.items())
            ]
            
            return timeline_list
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get insights timeline for patient {patient_id}: {e}")
            raise
    
    async def get_health_pattern_by_id(
        self, 
        pattern_id: UUID, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> Optional[HealthPatternResponse]:
        """
        Get a specific health pattern by ID.
        
        Args:
            pattern_id: Pattern ID
            patient_id: Patient ID
            db: Database session
            
        Returns:
            Optional[HealthPatternResponse]: Pattern if found
        """
        try:
            query = select(HealthPatternDB).where(
                and_(
                    HealthPatternDB.id == pattern_id,
                    HealthPatternDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            pattern = result.scalar_one_or_none()
            
            if pattern:
                return HealthPatternResponse.from_orm(pattern)
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get pattern {pattern_id}: {e}")
            raise
    
    async def create_health_pattern(
        self, 
        pattern_data: HealthPatternCreate, 
        db: AsyncSession
    ) -> HealthPatternResponse:
        """
        Create a new health pattern.
        
        Args:
            pattern_data: Pattern creation data
            db: Database session
            
        Returns:
            HealthPatternResponse: Created pattern
        """
        try:
            # Create pattern record
            pattern_db = HealthPatternDB(**pattern_data.dict())
            db.add(pattern_db)
            await db.flush()
            await db.refresh(pattern_db)
            
            self.logger.info(f"✅ Created pattern {pattern_db.id} for patient {pattern_data.patient_id}")
            
            return HealthPatternResponse.from_orm(pattern_db)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create pattern: {e}")
            raise
    
    async def update_health_pattern(
        self, 
        pattern_id: UUID, 
        patient_id: UUID, 
        update_data: HealthPatternUpdate, 
        db: AsyncSession
    ) -> Optional[HealthPatternResponse]:
        """
        Update an existing health pattern.
        
        Args:
            pattern_id: Pattern ID
            patient_id: Patient ID
            update_data: Update data
            db: Database session
            
        Returns:
            Optional[HealthPatternResponse]: Updated pattern if found
        """
        try:
            # Get existing pattern
            query = select(HealthPatternDB).where(
                and_(
                    HealthPatternDB.id == pattern_id,
                    HealthPatternDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            pattern = result.scalar_one_or_none()
            
            if not pattern:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(pattern, field, value)
            
            pattern.updated_at = datetime.utcnow()
            
            await db.flush()
            await db.refresh(pattern)
            
            self.logger.info(f"✅ Updated pattern {pattern_id}")
            
            return HealthPatternResponse.from_orm(pattern)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update pattern {pattern_id}: {e}")
            raise
    
    async def delete_health_pattern(
        self, 
        pattern_id: UUID, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> bool:
        """
        Delete a health pattern.
        
        Args:
            pattern_id: Pattern ID
            patient_id: Patient ID
            db: Database session
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Get existing pattern
            query = select(HealthPatternDB).where(
                and_(
                    HealthPatternDB.id == pattern_id,
                    HealthPatternDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            pattern = result.scalar_one_or_none()
            
            if not pattern:
                return False
            
            # Delete the pattern
            await db.delete(pattern)
            await db.flush()
            
            self.logger.info(f"✅ Deleted pattern {pattern_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete pattern {pattern_id}: {e}")
            raise
    
    async def get_health_score_by_id(
        self, 
        score_id: UUID, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> Optional[HealthScoreResponse]:
        """
        Get a specific health score by ID.
        
        Args:
            score_id: Health Score ID
            patient_id: Patient ID
            db: Database session
            
        Returns:
            Optional[HealthScoreResponse]: Health score if found
        """
        try:
            query = select(HealthScoreDB).where(
                and_(
                    HealthScoreDB.id == score_id,
                    HealthScoreDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            score = result.scalar_one_or_none()
            
            if score:
                return HealthScoreResponse.from_orm(ensure_python_uuids(score))
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get health score {score_id}: {e}")
            raise
    
    async def create_health_score(
        self, 
        score_data: HealthScoreCreate, 
        db: AsyncSession
    ) -> HealthScoreResponse:
        """
        Create a new health score.
        
        Args:
            score_data: Health score creation data
            db: Database session
            
        Returns:
            HealthScoreResponse: Created health score
        """
        try:
            # Create health score record
            score_db = HealthScoreDB(**score_data.dict())
            db.add(score_db)
            await db.flush()
            await db.refresh(score_db)
            
            self.logger.info(f"✅ Created health score {score_db.id} for patient {score_data.patient_id}")
            
            return HealthScoreResponse.from_orm(ensure_python_uuids(score_db))
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create health score: {e}")
            raise
    
    async def update_health_score(
        self, 
        score_id: UUID, 
        patient_id: UUID, 
        update_data: HealthScoreUpdate, 
        db: AsyncSession
    ) -> Optional[HealthScoreResponse]:
        """
        Update an existing health score.
        
        Args:
            score_id: Health Score ID
            patient_id: Patient ID
            update_data: Update data
            db: Database session
            
        Returns:
            Optional[HealthScoreResponse]: Updated health score if found
        """
        try:
            # Get existing health score
            query = select(HealthScoreDB).where(
                and_(
                    HealthScoreDB.id == score_id,
                    HealthScoreDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            score = result.scalar_one_or_none()
            
            if not score:
                return None
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(score, field, value)
            
            score.updated_at = datetime.utcnow()
            
            await db.flush()
            await db.refresh(score)
            
            self.logger.info(f"✅ Updated health score {score_id}")
            
            return HealthScoreResponse.from_orm(ensure_python_uuids(score))
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update health score {score_id}: {e}")
            raise
    
    async def delete_health_score(
        self, 
        score_id: UUID, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> bool:
        """
        Delete a health score.
        
        Args:
            score_id: Health Score ID
            patient_id: Patient ID
            db: Database session
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            # Get existing health score
            query = select(HealthScoreDB).where(
                and_(
                    HealthScoreDB.id == score_id,
                    HealthScoreDB.patient_id == patient_id
                )
            )
            
            result = await db.execute(query)
            score = result.scalar_one_or_none()
            
            if not score:
                return False
            
            # Delete the health score
            await db.delete(score)
            await db.flush()
            
            self.logger.info(f"✅ Deleted health score {score_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete health score {score_id}: {e}")
            raise
    
    async def get_health_scores_summary(
        self, 
        patient_id: UUID, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get a summary of health scores for a patient.
        
        Args:
            patient_id: Patient ID
            db: Database session
            
        Returns:
            Dict[str, Any]: Health scores summary
        """
        try:
            # Get all health scores for the patient
            scores = await self.get_health_scores(patient_id, db, limit=1000)
            
            if not scores:
                return {
                    'patient_id': str(patient_id),
                    'total_scores': 0,
                    'average_score': 0,
                    'score_distribution': {},
                    'latest_scores': [],
                    'trends': []
                }
            
            # Calculate summary statistics
            total_scores = len(scores)
            average_score = sum(score.score for score in scores) / total_scores
            
            # Score distribution by type
            score_distribution = {}
            for score in scores:
                score_type = score.score_type
                if score_type not in score_distribution:
                    score_distribution[score_type] = {
                        'count': 0,
                        'average': 0,
                        'min': float('inf'),
                        'max': float('-inf')
                    }
                
                dist = score_distribution[score_type]
                dist['count'] += 1
                dist['average'] = (dist['average'] * (dist['count'] - 1) + score.score) / dist['count']
                dist['min'] = min(dist['min'], score.score)
                dist['max'] = max(dist['max'], score.score)
            
            # Get latest scores (most recent 5)
            latest_scores = sorted(scores, key=lambda x: x.created_at, reverse=True)[:5]
            
            # Calculate trends (simplified - could be enhanced with time series analysis)
            trends = []
            for score_type in score_distribution:
                type_scores = [s for s in scores if s.score_type == score_type]
                if len(type_scores) >= 2:
                    sorted_scores = sorted(type_scores, key=lambda x: x.created_at)
                    first_score = sorted_scores[0].score
                    last_score = sorted_scores[-1].score
                    trend = "improving" if last_score > first_score else "declining" if last_score < first_score else "stable"
                    trends.append({
                        'score_type': score_type,
                        'trend': trend,
                        'change': last_score - first_score
                    })
            
            return {
                'patient_id': str(patient_id),
                'total_scores': total_scores,
                'average_score': round(average_score, 2),
                'score_distribution': score_distribution,
                'latest_scores': [
                    {
                        'id': str(score.id),
                        'score_type': score.score_type,
                        'score': score.score,
                        'created_at': score.created_at.isoformat()
                    }
                    for score in latest_scores
                ],
                'trends': trends
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health scores summary for patient {patient_id}: {e}")
            raise

    # Knowledge Graph Integration Methods
    async def enrich_insight_with_knowledge_graph(
        self, 
        insight_text: str,
        insight_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich insight text with knowledge graph entities and medical context.
        
        Args:
            insight_text: The insight text to enrich
            insight_type: Type of insight for targeted enrichment
            
        Returns:
            Dict[str, Any]: Enriched insight with knowledge graph entities
        """
        try:
            async with KnowledgeGraphClient() as client:
                # Search for medical entities in the insight text
                entities = await client.search_entities(insight_text, limit=15)
                
                # Get related medical information based on entities found
                related_conditions = []
                related_treatments = []
                related_medications = []
                
                for entity in entities:
                    entity_type = entity.get("type", "").lower()
                    entity_name = entity.get("name", "")
                    
                    if entity_type == "condition":
                        # Get treatments for this condition
                        treatments = await client.get_entities(entity_type="treatment", limit=5)
                        related_treatments.extend(treatments)
                        
                    elif entity_type == "medication":
                        # Get potential interactions
                        interactions = await client.get_medication_interactions(entity_name)
                        related_medications.extend(interactions)
                
                # Remove duplicates
                related_treatments = list({t.get("id"): t for t in related_treatments}.values())
                related_medications = list({m.get("id"): m for m in related_medications}.values())
                
                return {
                    "original_text": insight_text,
                    "enriched_entities": entities,
                    "related_conditions": [e for e in entities if e.get("type", "").lower() == "condition"],
                    "related_treatments": related_treatments[:10],
                    "related_medications": related_medications[:10],
                    "enrichment_metadata": {
                        "entities_found": len(entities),
                        "conditions_identified": len([e for e in entities if e.get("type", "").lower() == "condition"]),
                        "treatments_suggested": len(related_treatments),
                        "medications_identified": len(related_medications),
                        "enrichment_timestamp": datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to enrich insight with knowledge graph: {e}")
            return {
                "original_text": insight_text,
                "enriched_entities": [],
                "related_conditions": [],
                "related_treatments": [],
                "related_medications": [],
                "enrichment_metadata": {
                    "entities_found": 0,
                    "conditions_identified": 0,
                    "treatments_suggested": 0,
                    "medications_identified": 0,
                    "error": str(e),
                    "enrichment_timestamp": datetime.utcnow().isoformat()
                }
            }

    async def generate_evidence_based_recommendations(
        self, 
        patient_conditions: List[str],
        patient_medications: List[str],
        patient_symptoms: List[str]
    ) -> Dict[str, Any]:
        """
        Generate evidence-based recommendations using knowledge graph.
        
        Args:
            patient_conditions: List of patient conditions
            patient_medications: List of patient medications
            patient_symptoms: List of patient symptoms
            
        Returns:
            Dict[str, Any]: Evidence-based recommendations
        """
        try:
            async with KnowledgeGraphClient() as client:
                recommendations = {
                    "treatments": [],
                    "medication_recommendations": [],
                    "lifestyle_recommendations": [],
                    "monitoring_recommendations": [],
                    "risk_assessments": []
                }
                
                # Get treatments for each condition
                for condition in patient_conditions:
                    treatments = await client.get_condition_treatments(condition)
                    recommendations["treatments"].extend(treatments)
                
                # Get medication interactions and recommendations
                for medication in patient_medications:
                    interactions = await client.get_medication_interactions(medication)
                    recommendations["medication_recommendations"].extend(interactions)
                
                # Get related conditions for symptoms
                for symptom in patient_symptoms:
                    related_conditions = await client.search_entities(symptom, entity_type="condition", limit=3)
                    for condition in related_conditions:
                        condition_treatments = await client.get_condition_treatments(condition.get("name", ""))
                        recommendations["treatments"].extend(condition_treatments)
                
                # Remove duplicates and limit results
                recommendations["treatments"] = list({t.get("id"): t for t in recommendations["treatments"]}.values())[:15]
                recommendations["medication_recommendations"] = list({m.get("id"): m for m in recommendations["medication_recommendations"]}.values())[:10]
                
                # Add metadata
                recommendations["metadata"] = {
                    "conditions_analyzed": len(patient_conditions),
                    "medications_analyzed": len(patient_medications),
                    "symptoms_analyzed": len(patient_symptoms),
                    "total_treatments": len(recommendations["treatments"]),
                    "total_medication_recommendations": len(recommendations["medication_recommendations"]),
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
                
                return recommendations
                
        except Exception as e:
            self.logger.error(f"Failed to generate evidence-based recommendations: {e}")
            return {
                "treatments": [],
                "medication_recommendations": [],
                "lifestyle_recommendations": [],
                "monitoring_recommendations": [],
                "risk_assessments": [],
                "metadata": {
                    "error": str(e),
                    "generation_timestamp": datetime.utcnow().isoformat()
                }
            }

    async def validate_medical_entities(
        self, 
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate medical entities against the knowledge graph.
        
        Args:
            entities: List of medical entities to validate
            
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
            self.logger.error(f"Failed to validate medical entities: {e}")
            return {
                "valid_entities": [],
                "invalid_entities": entities,
                "suggestions": [],
                "validation_summary": {
                    "error": str(e),
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
            } 