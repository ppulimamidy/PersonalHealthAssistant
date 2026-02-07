"""
Counseling service for Personal Health Assistant.

This service handles genetic counseling including:
- Counseling session management
- Risk report generation
- Educational materials
- Follow-up scheduling
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.counseling import (
    GeneticCounseling, CounselingSession, RiskReport,
    GeneticCounselingCreate, GeneticCounselingUpdate, GeneticCounselingResponse,
    CounselingSessionCreate, CounselingSessionResponse,
    RiskReportCreate, RiskReportResponse,
    CounselingType, SessionStatus, ReportType, RiskCategory
)
from common.exceptions import NotFoundError, ValidationError


class CounselingService:
    """Service for managing genetic counseling."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_counseling(
        self, 
        counseling: GeneticCounselingCreate, 
        user_id: uuid.UUID
    ) -> GeneticCounselingResponse:
        """Create new genetic counseling session."""
        try:
            genetic_counseling = GeneticCounseling(
                user_id=user_id,
                counselor_id=counseling.counselor_id,
                counseling_type=counseling.counseling_type,
                scheduled_date=counseling.scheduled_date,
                duration_minutes=counseling.duration_minutes,
                patient_concerns=counseling.patient_concerns,
                family_history=counseling.family_history,
                medical_history=counseling.medical_history
            )
            
            self.db.add(genetic_counseling)
            self.db.commit()
            self.db.refresh(genetic_counseling)
            
            return GeneticCounselingResponse.from_orm(genetic_counseling)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create genetic counseling: {str(e)}")
    
    async def list_counseling(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        counseling_type: Optional[CounselingType] = None,
        status: Optional[SessionStatus] = None
    ) -> List[GeneticCounselingResponse]:
        """List genetic counseling sessions for user."""
        try:
            query = self.db.query(GeneticCounseling).filter(GeneticCounseling.user_id == user_id)
            
            if counseling_type:
                query = query.filter(GeneticCounseling.counseling_type == counseling_type)
            if status:
                query = query.filter(GeneticCounseling.session_status == status)
            
            counseling_sessions = query.offset(skip).limit(limit).all()
            return [GeneticCounselingResponse.from_orm(session) for session in counseling_sessions]
        except Exception as e:
            raise ValidationError(f"Failed to list counseling sessions: {str(e)}")
    
    async def get_counseling(
        self, 
        counseling_id: str, 
        user_id: uuid.UUID
    ) -> GeneticCounselingResponse:
        """Get specific genetic counseling by ID."""
        try:
            counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not counseling:
                raise NotFoundError("Genetic counseling not found")
            
            return GeneticCounselingResponse.from_orm(counseling)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get genetic counseling: {str(e)}")
    
    async def update_counseling(
        self,
        counseling_id: str,
        counseling: GeneticCounselingUpdate,
        user_id: uuid.UUID
    ) -> GeneticCounselingResponse:
        """Update genetic counseling."""
        try:
            existing_counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not existing_counseling:
                raise NotFoundError("Genetic counseling not found")
            
            # Update fields
            update_data = counseling.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(existing_counseling, field, value)
            
            existing_counseling.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_counseling)
            
            return GeneticCounselingResponse.from_orm(existing_counseling)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update genetic counseling: {str(e)}")
    
    async def delete_counseling(
        self, 
        counseling_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete genetic counseling."""
        try:
            counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not counseling:
                raise NotFoundError("Genetic counseling not found")
            
            self.db.delete(counseling)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete genetic counseling: {str(e)}")
    
    # Counseling Session methods
    async def create_counseling_session(
        self,
        counseling_id: str,
        session: CounselingSessionCreate,
        user_id: uuid.UUID
    ) -> CounselingSessionResponse:
        """Create new counseling session."""
        try:
            # Verify user has access to the counseling
            counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not counseling:
                raise ValidationError("Counseling not found or access denied")
            
            counseling_session = CounselingSession(
                counseling_id=counseling_id,
                session_number=session.session_number,
                session_date=session.session_date,
                session_duration=session.session_duration,
                topics_discussed=session.topics_discussed,
                questions_answered=session.questions_answered,
                concerns_addressed=session.concerns_addressed,
                patient_understanding=session.patient_understanding,
                emotional_response=session.emotional_response,
                decision_made=session.decision_made,
                session_summary=session.session_summary,
                action_items=session.action_items,
                next_steps=session.next_steps
            )
            
            self.db.add(counseling_session)
            self.db.commit()
            self.db.refresh(counseling_session)
            
            return CounselingSessionResponse.from_orm(counseling_session)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create counseling session: {str(e)}")
    
    async def list_counseling_sessions(
        self,
        counseling_id: str,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[CounselingSessionResponse]:
        """List counseling sessions for a specific counseling."""
        try:
            # Verify user has access to the counseling
            counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not counseling:
                raise ValidationError("Counseling not found or access denied")
            
            sessions = self.db.query(CounselingSession).filter(
                CounselingSession.counseling_id == counseling_id
            ).offset(skip).limit(limit).all()
            
            return [CounselingSessionResponse.from_orm(session) for session in sessions]
        except Exception as e:
            raise ValidationError(f"Failed to list counseling sessions: {str(e)}")
    
    async def get_counseling_session(
        self, 
        session_id: str, 
        user_id: uuid.UUID
    ) -> CounselingSessionResponse:
        """Get specific counseling session by ID."""
        try:
            session = self.db.query(CounselingSession).join(
                GeneticCounseling, CounselingSession.counseling_id == GeneticCounseling.id
            ).filter(
                CounselingSession.id == session_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not session:
                raise NotFoundError("Counseling session not found")
            
            return CounselingSessionResponse.from_orm(session)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get counseling session: {str(e)}")
    
    async def update_counseling_session(
        self,
        session_id: str,
        session: CounselingSessionCreate,
        user_id: uuid.UUID
    ) -> CounselingSessionResponse:
        """Update counseling session."""
        try:
            existing_session = self.db.query(CounselingSession).join(
                GeneticCounseling, CounselingSession.counseling_id == GeneticCounseling.id
            ).filter(
                CounselingSession.id == session_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not existing_session:
                raise NotFoundError("Counseling session not found")
            
            # Update fields
            for field, value in session.dict(exclude={'counseling_id'}).items():
                setattr(existing_session, field, value)
            
            existing_session.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_session)
            
            return CounselingSessionResponse.from_orm(existing_session)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update counseling session: {str(e)}")
    
    async def delete_counseling_session(
        self, 
        session_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete counseling session."""
        try:
            session = self.db.query(CounselingSession).join(
                GeneticCounseling, CounselingSession.counseling_id == GeneticCounseling.id
            ).filter(
                CounselingSession.id == session_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not session:
                raise NotFoundError("Counseling session not found")
            
            self.db.delete(session)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete counseling session: {str(e)}")
    
    # Risk Report methods
    async def create_risk_report(
        self, 
        report: RiskReportCreate, 
        user_id: uuid.UUID
    ) -> RiskReportResponse:
        """Create new risk report."""
        try:
            risk_report = RiskReport(
                user_id=user_id,
                counseling_id=report.counseling_id,
                report_type=report.report_type,
                report_title=report.report_title,
                report_date=report.report_date,
                overall_risk_category=report.overall_risk_category,
                risk_score=report.risk_score,
                executive_summary=report.executive_summary,
                detailed_analysis=report.detailed_analysis,
                risk_factors=report.risk_factors,
                protective_factors=report.protective_factors,
                clinical_recommendations=report.clinical_recommendations,
                lifestyle_recommendations=report.lifestyle_recommendations,
                screening_recommendations=report.screening_recommendations,
                prevention_strategies=report.prevention_strategies,
                educational_materials=report.educational_materials,
                resources=report.resources,
                references=report.references,
                is_confidential=report.is_confidential
            )
            
            self.db.add(risk_report)
            self.db.commit()
            self.db.refresh(risk_report)
            
            return RiskReportResponse.from_orm(risk_report)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create risk report: {str(e)}")
    
    async def list_risk_reports(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        report_type: Optional[ReportType] = None
    ) -> List[RiskReportResponse]:
        """List risk reports for user."""
        try:
            query = self.db.query(RiskReport).filter(RiskReport.user_id == user_id)
            
            if report_type:
                query = query.filter(RiskReport.report_type == report_type)
            
            reports = query.offset(skip).limit(limit).all()
            return [RiskReportResponse.from_orm(report) for report in reports]
        except Exception as e:
            raise ValidationError(f"Failed to list risk reports: {str(e)}")
    
    async def get_risk_report(
        self, 
        report_id: str, 
        user_id: uuid.UUID
    ) -> RiskReportResponse:
        """Get specific risk report by ID."""
        try:
            report = self.db.query(RiskReport).filter(
                RiskReport.id == report_id,
                RiskReport.user_id == user_id
            ).first()
            
            if not report:
                raise NotFoundError("Risk report not found")
            
            return RiskReportResponse.from_orm(report)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get risk report: {str(e)}")
    
    async def update_risk_report(
        self,
        report_id: str,
        report: RiskReportCreate,
        user_id: uuid.UUID
    ) -> RiskReportResponse:
        """Update risk report."""
        try:
            existing_report = self.db.query(RiskReport).filter(
                RiskReport.id == report_id,
                RiskReport.user_id == user_id
            ).first()
            
            if not existing_report:
                raise NotFoundError("Risk report not found")
            
            # Update fields
            for field, value in report.dict(exclude={'user_id'}).items():
                setattr(existing_report, field, value)
            
            existing_report.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_report)
            
            return RiskReportResponse.from_orm(existing_report)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update risk report: {str(e)}")
    
    async def delete_risk_report(
        self, 
        report_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete risk report."""
        try:
            report = self.db.query(RiskReport).filter(
                RiskReport.id == report_id,
                RiskReport.user_id == user_id
            ).first()
            
            if not report:
                raise NotFoundError("Risk report not found")
            
            self.db.delete(report)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete risk report: {str(e)}")
    
    # Additional counseling methods
    async def get_educational_materials(
        self,
        user_id: uuid.UUID,
        topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get educational materials for genetic counseling."""
        try:
            # Get user's counseling sessions to determine relevant materials
            counseling_sessions = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.user_id == user_id
            ).all()
            
            # Generate educational materials based on counseling type
            materials = []
            
            for session in counseling_sessions:
                if topic and topic.lower() not in session.counseling_type.value.lower():
                    continue
                
                materials.extend(self._get_materials_for_counseling_type(session.counseling_type))
            
            return materials
        except Exception as e:
            raise ValidationError(f"Failed to get educational materials: {str(e)}")
    
    async def get_counseling_recommendations(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get personalized counseling recommendations."""
        try:
            # Get user's existing counseling sessions
            existing_counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.user_id == user_id
            ).all()
            
            recommendations = []
            
            # Check for gaps in counseling types
            counseling_types = {session.counseling_type for session in existing_counseling}
            
            if CounselingType.PRE_TEST not in counseling_types:
                recommendations.append({
                    "type": "pre_test_counseling",
                    "priority": "high",
                    "description": "Consider pre-test genetic counseling before undergoing genetic testing",
                    "reason": "Important for informed consent and understanding test implications"
                })
            
            if CounselingType.POST_TEST not in counseling_types:
                recommendations.append({
                    "type": "post_test_counseling",
                    "priority": "high",
                    "description": "Schedule post-test counseling to discuss results",
                    "reason": "Essential for understanding test results and next steps"
                })
            
            return recommendations
        except Exception as e:
            raise ValidationError(f"Failed to get counseling recommendations: {str(e)}")
    
    async def schedule_followup(
        self,
        counseling_id: str,
        user_id: uuid.UUID,
        followup_date: str
    ) -> GeneticCounselingResponse:
        """Schedule follow-up counseling session."""
        try:
            counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not counseling:
                raise NotFoundError("Genetic counseling not found")
            
            # Update follow-up information
            counseling.follow_up_required = True
            counseling.follow_up_date = datetime.fromisoformat(followup_date)
            counseling.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(counseling)
            
            return GeneticCounselingResponse.from_orm(counseling)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to schedule follow-up: {str(e)}")
    
    async def get_available_counselors(
        self,
        user_id: uuid.UUID,
        specialization: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available genetic counselors."""
        try:
            # This would typically query a counselor database
            # For now, return sample data
            counselors = [
                {
                    "id": "counselor-1",
                    "name": "Dr. Sarah Johnson",
                    "specialization": "cancer_genetics",
                    "experience_years": 8,
                    "availability": "weekdays",
                    "rating": 4.8
                },
                {
                    "id": "counselor-2", 
                    "name": "Dr. Michael Chen",
                    "specialization": "cardiovascular_genetics",
                    "experience_years": 12,
                    "availability": "weekdays_weekends",
                    "rating": 4.9
                }
            ]
            
            if specialization:
                counselors = [c for c in counselors if specialization.lower() in c["specialization"].lower()]
            
            return counselors
        except Exception as e:
            raise ValidationError(f"Failed to get available counselors: {str(e)}")
    
    async def export_counseling_report(
        self,
        counseling_id: str,
        user_id: uuid.UUID,
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """Export counseling report."""
        try:
            counseling = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.id == counseling_id,
                GeneticCounseling.user_id == user_id
            ).first()
            
            if not counseling:
                raise NotFoundError("Genetic counseling not found")
            
            # Generate report content
            report_content = self._generate_counseling_report(counseling, format)
            
            return {
                "counseling_id": str(counseling.id),
                "format": format,
                "content": report_content,
                "filename": f"counseling_report_{counseling.counseling_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to export counseling report: {str(e)}")
    
    async def get_counseling_statistics(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get counseling statistics for the user."""
        try:
            counseling_sessions = self.db.query(GeneticCounseling).filter(
                GeneticCounseling.user_id == user_id
            ).all()
            
            if not counseling_sessions:
                return {"message": "No counseling sessions found"}
            
            total_sessions = len(counseling_sessions)
            completed_sessions = len([s for s in counseling_sessions if s.session_status == SessionStatus.COMPLETED])
            
            # Count by counseling type
            type_counts = {}
            for session in counseling_sessions:
                type_counts[session.counseling_type.value] = type_counts.get(session.counseling_type.value, 0) + 1
            
            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                "counseling_types": type_counts,
                "latest_session": max(counseling_sessions, key=lambda s: s.created_at).created_at if counseling_sessions else None
            }
        except Exception as e:
            raise ValidationError(f"Failed to get counseling statistics: {str(e)}")
    
    def _get_materials_for_counseling_type(self, counseling_type: CounselingType) -> List[Dict[str, Any]]:
        """Get educational materials for specific counseling type."""
        materials_map = {
            CounselingType.PRE_TEST: [
                {
                    "title": "Understanding Genetic Testing",
                    "type": "video",
                    "duration": "15 minutes",
                    "description": "Introduction to genetic testing and what to expect"
                },
                {
                    "title": "Informed Consent Guide",
                    "type": "document",
                    "pages": 8,
                    "description": "Comprehensive guide to informed consent process"
                }
            ],
            CounselingType.POST_TEST: [
                {
                    "title": "Understanding Your Results",
                    "type": "video",
                    "duration": "20 minutes",
                    "description": "How to interpret genetic test results"
                },
                {
                    "title": "Next Steps After Testing",
                    "type": "document",
                    "pages": 12,
                    "description": "Guidance on next steps and follow-up care"
                }
            ],
            CounselingType.CANCER: [
                {
                    "title": "Cancer Genetics Overview",
                    "type": "video",
                    "duration": "25 minutes",
                    "description": "Understanding cancer risk and genetic factors"
                },
                {
                    "title": "Cancer Screening Guidelines",
                    "type": "document",
                    "pages": 15,
                    "description": "Personalized screening recommendations"
                }
            ]
        }
        
        return materials_map.get(counseling_type, [])
    
    def _generate_counseling_report(
        self, 
        counseling: GeneticCounseling, 
        format: str
    ) -> str:
        """Generate counseling report in specified format."""
        if format.lower() == "json":
            return {
                "counseling_id": str(counseling.id),
                "counseling_type": counseling.counseling_type.value,
                "scheduled_date": counseling.scheduled_date.isoformat(),
                "session_status": counseling.session_status.value,
                "patient_concerns": counseling.patient_concerns,
                "family_history": counseling.family_history,
                "recommendations": counseling.recommendations
            }
        else:
            # Default to text format
            content = f"""
Genetic Counseling Report
=========================

Counseling Type: {counseling.counseling_type.value}
Scheduled Date: {counseling.scheduled_date}
Status: {counseling.session_status.value}

Patient Concerns: {counseling.patient_concerns or 'None specified'}

Family History: {len(counseling.family_history)} items recorded

Recommendations: {len(counseling.recommendations)} recommendations provided
"""
            return content 