"""
Analysis service for Personal Health Assistant.

This service handles genomic analysis workflows including:
- Analysis creation and management
- Background processing
- Results storage and retrieval
- Disease risk assessment
- Ancestry analysis
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.analysis import (
    GenomicAnalysis, DiseaseRiskAssessment, AncestryAnalysis,
    GenomicAnalysisCreate, GenomicAnalysisUpdate, GenomicAnalysisResponse,
    DiseaseRiskAssessmentCreate, DiseaseRiskAssessmentResponse,
    AncestryAnalysisCreate, AncestryAnalysisResponse,
    AnalysisType, AnalysisStatus, RiskLevel, ConfidenceLevel
)
from common.exceptions import NotFoundError, ValidationError


class AnalysisService:
    """Service for managing genomic analysis workflows."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_analysis(
        self, 
        analysis: GenomicAnalysisCreate, 
        user_id: uuid.UUID
    ) -> GenomicAnalysisResponse:
        """Create new genomic analysis."""
        try:
            # Create analysis record
            genomic_analysis = GenomicAnalysis(
                user_id=user_id,
                genomic_data_id=analysis.genomic_data_id,
                analysis_type=analysis.analysis_type,
                analysis_name=analysis.analysis_name,
                analysis_version=analysis.analysis_version,
                parameters=analysis.parameters,
                status=AnalysisStatus.PENDING,
                progress=0.0
            )
            
            self.db.add(genomic_analysis)
            self.db.commit()
            self.db.refresh(genomic_analysis)
            
            return GenomicAnalysisResponse.from_orm(genomic_analysis)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create analysis: {str(e)}")
    
    async def list_analyses(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        analysis_type: Optional[AnalysisType] = None,
        status: Optional[AnalysisStatus] = None
    ) -> List[GenomicAnalysisResponse]:
        """List genomic analyses for user."""
        try:
            query = self.db.query(GenomicAnalysis).filter(GenomicAnalysis.user_id == user_id)
            
            if analysis_type:
                query = query.filter(GenomicAnalysis.analysis_type == analysis_type)
            if status:
                query = query.filter(GenomicAnalysis.status == status)
            
            analyses = query.offset(skip).limit(limit).all()
            return [GenomicAnalysisResponse.from_orm(analysis) for analysis in analyses]
        except Exception as e:
            raise ValidationError(f"Failed to list analyses: {str(e)}")
    
    async def get_analysis(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> GenomicAnalysisResponse:
        """Get specific analysis by ID."""
        try:
            analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Analysis not found")
            
            return GenomicAnalysisResponse.from_orm(analysis)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get analysis: {str(e)}")
    
    async def update_analysis(
        self,
        analysis_id: str,
        analysis: GenomicAnalysisUpdate,
        user_id: uuid.UUID
    ) -> GenomicAnalysisResponse:
        """Update analysis."""
        try:
            genomic_analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not genomic_analysis:
                raise NotFoundError("Analysis not found")
            
            # Update fields
            update_data = analysis.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(genomic_analysis, field, value)
            
            genomic_analysis.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(genomic_analysis)
            
            return GenomicAnalysisResponse.from_orm(genomic_analysis)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update analysis: {str(e)}")
    
    async def delete_analysis(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete analysis."""
        try:
            analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Analysis not found")
            
            self.db.delete(analysis)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete analysis: {str(e)}")
    
    async def get_analysis_status(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get analysis status and progress."""
        try:
            analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Analysis not found")
            
            return {
                "id": str(analysis.id),
                "status": analysis.status,
                "progress": analysis.progress,
                "started_at": analysis.started_at,
                "completed_at": analysis.completed_at,
                "confidence_score": analysis.confidence_score
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get analysis status: {str(e)}")
    
    async def get_analysis_results(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get analysis results."""
        try:
            analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Analysis not found")
            
            if analysis.status != AnalysisStatus.COMPLETED:
                raise ValidationError("Analysis not completed")
            
            return {
                "id": str(analysis.id),
                "results": analysis.results,
                "summary": analysis.summary,
                "confidence_score": analysis.confidence_score,
                "quality_metrics": analysis.quality_metrics
            }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get analysis results: {str(e)}")
    
    async def cancel_analysis(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> GenomicAnalysisResponse:
        """Cancel running analysis."""
        try:
            analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Analysis not found")
            
            if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.IN_PROGRESS]:
                raise ValidationError("Analysis cannot be cancelled")
            
            analysis.status = AnalysisStatus.CANCELLED
            analysis.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(analysis)
            
            return GenomicAnalysisResponse.from_orm(analysis)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to cancel analysis: {str(e)}")
    
    async def run_analysis_background(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Run analysis in background (simulated)."""
        try:
            analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                return
            
            # Update status to in progress
            analysis.status = AnalysisStatus.IN_PROGRESS
            analysis.started_at = datetime.utcnow()
            analysis.progress = 0.1
            self.db.commit()
            
            # Simulate analysis processing
            import asyncio
            await asyncio.sleep(2)  # Simulate processing time
            
            # Update progress
            analysis.progress = 0.5
            self.db.commit()
            
            await asyncio.sleep(2)  # More processing
            
            # Complete analysis
            analysis.status = AnalysisStatus.COMPLETED
            analysis.progress = 1.0
            analysis.completed_at = datetime.utcnow()
            analysis.confidence_score = 0.95
            analysis.results = {
                "variants_found": 150,
                "significant_variants": 12,
                "quality_score": 0.95
            }
            analysis.summary = "Analysis completed successfully with 150 variants identified."
            
            self.db.commit()
            
        except Exception as e:
            # Mark analysis as failed
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.updated_at = datetime.utcnow()
                self.db.commit()
    
    # Disease Risk Assessment methods
    async def create_disease_risk_assessment(
        self, 
        assessment: DiseaseRiskAssessmentCreate, 
        user_id: uuid.UUID
    ) -> DiseaseRiskAssessmentResponse:
        """Create disease risk assessment."""
        try:
            disease_risk = DiseaseRiskAssessment(
                analysis_id=assessment.analysis_id,
                disease_name=assessment.disease_name,
                disease_id=assessment.disease_id,
                disease_category=assessment.disease_category,
                risk_level=assessment.risk_level,
                risk_score=assessment.risk_score,
                population_risk=assessment.population_risk,
                relative_risk=assessment.relative_risk,
                contributing_variants=assessment.contributing_variants,
                genetic_factors=assessment.genetic_factors,
                clinical_recommendations=assessment.clinical_recommendations,
                screening_recommendations=assessment.screening_recommendations,
                confidence_level=assessment.confidence_level,
                evidence_level=assessment.evidence_level,
                references=assessment.references
            )
            
            self.db.add(disease_risk)
            self.db.commit()
            self.db.refresh(disease_risk)
            
            return DiseaseRiskAssessmentResponse.from_orm(disease_risk)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create disease risk assessment: {str(e)}")
    
    async def get_disease_risk_assessment(
        self, 
        assessment_id: str, 
        user_id: uuid.UUID
    ) -> DiseaseRiskAssessmentResponse:
        """Get disease risk assessment."""
        try:
            assessment = self.db.query(DiseaseRiskAssessment).join(GenomicAnalysis).filter(
                DiseaseRiskAssessment.id == assessment_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not assessment:
                raise NotFoundError("Disease risk assessment not found")
            
            return DiseaseRiskAssessmentResponse.from_orm(assessment)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get disease risk assessment: {str(e)}")
    
    async def list_disease_risk_assessments(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DiseaseRiskAssessmentResponse]:
        """List disease risk assessments for user."""
        try:
            assessments = self.db.query(DiseaseRiskAssessment).join(GenomicAnalysis).filter(
                GenomicAnalysis.user_id == user_id
            ).offset(skip).limit(limit).all()
            
            return [DiseaseRiskAssessmentResponse.from_orm(assessment) for assessment in assessments]
        except Exception as e:
            raise ValidationError(f"Failed to list disease risk assessments: {str(e)}")
    
    # Ancestry Analysis methods
    async def create_ancestry_analysis(
        self, 
        analysis: AncestryAnalysisCreate, 
        user_id: uuid.UUID
    ) -> AncestryAnalysisResponse:
        """Create ancestry analysis."""
        try:
            ancestry_analysis = AncestryAnalysis(
                analysis_id=analysis.analysis_id,
                ancestry_composition=analysis.ancestry_composition,
                primary_ancestry=analysis.primary_ancestry,
                secondary_ancestries=analysis.secondary_ancestries,
                geographic_origins=analysis.geographic_origins,
                migration_patterns=analysis.migration_patterns,
                population_matches=analysis.population_matches,
                reference_populations=analysis.reference_populations,
                neanderthal_percentage=analysis.neanderthal_percentage,
                denisovan_percentage=analysis.denisovan_percentage,
                maternal_haplogroup=analysis.maternal_haplogroup,
                paternal_haplogroup=analysis.paternal_haplogroup,
                confidence_scores=analysis.confidence_scores,
                methodology=analysis.methodology,
                reference_database=analysis.reference_database
            )
            
            self.db.add(ancestry_analysis)
            self.db.commit()
            self.db.refresh(ancestry_analysis)
            
            return AncestryAnalysisResponse.from_orm(ancestry_analysis)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create ancestry analysis: {str(e)}")
    
    async def get_ancestry_analysis(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> AncestryAnalysisResponse:
        """Get ancestry analysis."""
        try:
            ancestry_analysis = self.db.query(AncestryAnalysis).join(GenomicAnalysis).filter(
                AncestryAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not ancestry_analysis:
                raise NotFoundError("Ancestry analysis not found")
            
            return AncestryAnalysisResponse.from_orm(ancestry_analysis)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get ancestry analysis: {str(e)}")
    
    async def list_ancestry_analyses(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[AncestryAnalysisResponse]:
        """List ancestry analyses for user."""
        try:
            analyses = self.db.query(AncestryAnalysis).join(GenomicAnalysis).filter(
                GenomicAnalysis.user_id == user_id
            ).offset(skip).limit(limit).all()
            
            return [AncestryAnalysisResponse.from_orm(analysis) for analysis in analyses]
        except Exception as e:
            raise ValidationError(f"Failed to list ancestry analyses: {str(e)}")
    
    # Batch analysis methods
    async def get_batch_status(
        self, 
        batch_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get batch analysis status."""
        try:
            analyses = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.user_id == user_id
            ).all()
            
            # For now, return a simple status
            return {
                "batch_id": batch_id,
                "total_analyses": len(analyses),
                "completed": len([a for a in analyses if a.status == AnalysisStatus.COMPLETED]),
                "in_progress": len([a for a in analyses if a.status == AnalysisStatus.IN_PROGRESS]),
                "failed": len([a for a in analyses if a.status == AnalysisStatus.FAILED])
            }
        except Exception as e:
            raise ValidationError(f"Failed to get batch status: {str(e)}") 