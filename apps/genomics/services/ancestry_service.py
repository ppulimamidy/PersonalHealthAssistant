"""
Ancestry service for Personal Health Assistant.

This service handles ancestry analysis including:
- Ancestry composition analysis
- Geographic origins mapping
- Haplogroup analysis
- Population matching
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.analysis import (
    AncestryAnalysis, AncestryAnalysisCreate, AncestryAnalysisResponse
)
from common.exceptions import NotFoundError, ValidationError


class AncestryService:
    """Service for managing ancestry analysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_ancestry_analysis(
        self, 
        analysis: AncestryAnalysisCreate, 
        user_id: uuid.UUID
    ) -> AncestryAnalysisResponse:
        """Create new ancestry analysis."""
        try:
            # Verify user has access to the analysis
            from ..models.analysis import GenomicAnalysis
            genomic_analysis = self.db.query(GenomicAnalysis).filter(
                GenomicAnalysis.id == analysis.analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not genomic_analysis:
                raise ValidationError("Analysis not found or access denied")
            
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
    
    async def list_ancestry_analyses(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[AncestryAnalysisResponse]:
        """List ancestry analyses for user."""
        try:
            analyses = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).offset(skip).limit(limit).all()
            
            return [AncestryAnalysisResponse.from_orm(analysis) for analysis in analyses]
        except Exception as e:
            raise ValidationError(f"Failed to list ancestry analyses: {str(e)}")
    
    async def get_ancestry_analysis(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> AncestryAnalysisResponse:
        """Get specific ancestry analysis by ID."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(
                AncestryAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Ancestry analysis not found")
            
            return AncestryAnalysisResponse.from_orm(analysis)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get ancestry analysis: {str(e)}")
    
    async def update_ancestry_analysis(
        self,
        analysis_id: str,
        analysis: AncestryAnalysisCreate,
        user_id: uuid.UUID
    ) -> AncestryAnalysisResponse:
        """Update ancestry analysis."""
        try:
            existing_analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(
                AncestryAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not existing_analysis:
                raise NotFoundError("Ancestry analysis not found")
            
            # Update fields
            for field, value in analysis.dict(exclude={'analysis_id'}).items():
                setattr(existing_analysis, field, value)
            
            existing_analysis.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_analysis)
            
            return AncestryAnalysisResponse.from_orm(existing_analysis)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update ancestry analysis: {str(e)}")
    
    async def delete_ancestry_analysis(
        self, 
        analysis_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete ancestry analysis."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(
                AncestryAnalysis.id == analysis_id,
                GenomicAnalysis.user_id == user_id
            ).first()
            
            if not analysis:
                raise NotFoundError("Ancestry analysis not found")
            
            self.db.delete(analysis)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete ancestry analysis: {str(e)}")
    
    async def get_ancestry_composition(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get ancestry composition for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return {"message": "No ancestry analysis found"}
            
            return {
                "analysis_id": str(analysis.id),
                "ancestry_composition": analysis.ancestry_composition,
                "primary_ancestry": analysis.primary_ancestry,
                "secondary_ancestries": analysis.secondary_ancestries
            }
        except Exception as e:
            raise ValidationError(f"Failed to get ancestry composition: {str(e)}")
    
    async def get_geographic_origins(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get geographic origins for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return []
            
            return analysis.geographic_origins
        except Exception as e:
            raise ValidationError(f"Failed to get geographic origins: {str(e)}")
    
    async def get_haplogroups(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get haplogroups for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return {"message": "No ancestry analysis found"}
            
            return {
                "maternal_haplogroup": analysis.maternal_haplogroup,
                "paternal_haplogroup": analysis.paternal_haplogroup,
                "neanderthal_percentage": analysis.neanderthal_percentage,
                "denisovan_percentage": analysis.denisovan_percentage
            }
        except Exception as e:
            raise ValidationError(f"Failed to get haplogroups: {str(e)}")
    
    async def get_population_matches(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get population matches for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return []
            
            return analysis.population_matches
        except Exception as e:
            raise ValidationError(f"Failed to get population matches: {str(e)}")
    
    async def get_migration_patterns(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get migration patterns for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return []
            
            return analysis.migration_patterns
        except Exception as e:
            raise ValidationError(f"Failed to get migration patterns: {str(e)}")
    
    async def get_neanderthal_ancestry(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get Neanderthal ancestry percentage for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return {"message": "No ancestry analysis found"}
            
            return {
                "neanderthal_percentage": analysis.neanderthal_percentage,
                "interpretation": self._interpret_neanderthal_percentage(analysis.neanderthal_percentage)
            }
        except Exception as e:
            raise ValidationError(f"Failed to get Neanderthal ancestry: {str(e)}")
    
    async def get_denisovan_ancestry(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get Denisovan ancestry percentage for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return {"message": "No ancestry analysis found"}
            
            return {
                "denisovan_percentage": analysis.denisovan_percentage,
                "interpretation": self._interpret_denisovan_percentage(analysis.denisovan_percentage)
            }
        except Exception as e:
            raise ValidationError(f"Failed to get Denisovan ancestry: {str(e)}")
    
    async def get_reference_populations(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get reference populations for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return []
            
            return analysis.reference_populations
        except Exception as e:
            raise ValidationError(f"Failed to get reference populations: {str(e)}")
    
    async def compare_ancestry(
        self, 
        user_id: uuid.UUID, 
        other_user_id: str
    ) -> Dict[str, Any]:
        """Compare ancestry with another user."""
        try:
            # Get current user's ancestry
            user_analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            # Get other user's ancestry
            other_analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == other_user_id).first()
            
            if not user_analysis or not other_analysis:
                return {"message": "One or both users lack ancestry analysis"}
            
            # Calculate similarity
            similarity = self._calculate_ancestry_similarity(
                user_analysis.ancestry_composition,
                other_analysis.ancestry_composition
            )
            
            return {
                "user_ancestry": user_analysis.ancestry_composition,
                "other_user_ancestry": other_analysis.ancestry_composition,
                "similarity_score": similarity,
                "shared_ancestries": self._find_shared_ancestries(
                    user_analysis.ancestry_composition,
                    other_analysis.ancestry_composition
                )
            }
        except Exception as e:
            raise ValidationError(f"Failed to compare ancestry: {str(e)}")
    
    async def get_ancestry_regions(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get ancestry regions for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return []
            
            regions = []
            for region, percentage in analysis.ancestry_composition.items():
                regions.append({
                    "region": region,
                    "percentage": percentage,
                    "category": self._categorize_region(region)
                })
            
            return sorted(regions, key=lambda x: x["percentage"], reverse=True)
        except Exception as e:
            raise ValidationError(f"Failed to get ancestry regions: {str(e)}")
    
    async def get_confidence_scores(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get confidence scores for ancestry analysis."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return {"message": "No ancestry analysis found"}
            
            return {
                "confidence_scores": analysis.confidence_scores,
                "methodology": analysis.methodology,
                "reference_database": analysis.reference_database
            }
        except Exception as e:
            raise ValidationError(f"Failed to get confidence scores: {str(e)}")
    
    async def export_ancestry_report(
        self,
        user_id: uuid.UUID,
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """Export ancestry analysis report."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                raise ValidationError("No ancestry analysis found")
            
            # Generate report content
            report_content = self._generate_ancestry_report(analysis, format)
            
            return {
                "analysis_id": str(analysis.id),
                "format": format,
                "content": report_content,
                "filename": f"ancestry_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        except Exception as e:
            raise ValidationError(f"Failed to export ancestry report: {str(e)}")
    
    async def get_ancestry_statistics(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get ancestry statistics for the user."""
        try:
            analysis = self.db.query(AncestryAnalysis).join(
                GenomicAnalysis, AncestryAnalysis.analysis_id == GenomicAnalysis.id
            ).filter(GenomicAnalysis.user_id == user_id).first()
            
            if not analysis:
                return {"message": "No ancestry analysis found"}
            
            total_regions = len(analysis.ancestry_composition)
            primary_region_percentage = max(analysis.ancestry_composition.values()) if analysis.ancestry_composition else 0
            
            return {
                "total_regions": total_regions,
                "primary_ancestry": analysis.primary_ancestry,
                "primary_region_percentage": primary_region_percentage,
                "neanderthal_percentage": analysis.neanderthal_percentage,
                "denisovan_percentage": analysis.denisovan_percentage,
                "maternal_haplogroup": analysis.maternal_haplogroup,
                "paternal_haplogroup": analysis.paternal_haplogroup
            }
        except Exception as e:
            raise ValidationError(f"Failed to get ancestry statistics: {str(e)}")
    
    def _interpret_neanderthal_percentage(self, percentage: Optional[float]) -> str:
        """Interpret Neanderthal ancestry percentage."""
        if percentage is None:
            return "Not analyzed"
        elif percentage < 1.0:
            return "Below average Neanderthal ancestry"
        elif percentage < 2.0:
            return "Average Neanderthal ancestry"
        elif percentage < 3.0:
            return "Above average Neanderthal ancestry"
        else:
            return "High Neanderthal ancestry"
    
    def _interpret_denisovan_percentage(self, percentage: Optional[float]) -> str:
        """Interpret Denisovan ancestry percentage."""
        if percentage is None:
            return "Not analyzed"
        elif percentage < 0.1:
            return "Below average Denisovan ancestry"
        elif percentage < 0.5:
            return "Average Denisovan ancestry"
        elif percentage < 1.0:
            return "Above average Denisovan ancestry"
        else:
            return "High Denisovan ancestry"
    
    def _calculate_ancestry_similarity(
        self, 
        ancestry1: Dict[str, float], 
        ancestry2: Dict[str, float]
    ) -> float:
        """Calculate similarity between two ancestry compositions."""
        if not ancestry1 or not ancestry2:
            return 0.0
        
        # Calculate cosine similarity
        all_regions = set(ancestry1.keys()) | set(ancestry2.keys())
        
        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0
        
        for region in all_regions:
            val1 = ancestry1.get(region, 0.0)
            val2 = ancestry2.get(region, 0.0)
            
            dot_product += val1 * val2
            norm1 += val1 * val1
            norm2 += val2 * val2
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 ** 0.5 * norm2 ** 0.5)
    
    def _find_shared_ancestries(
        self, 
        ancestry1: Dict[str, float], 
        ancestry2: Dict[str, float]
    ) -> List[str]:
        """Find ancestries shared between two users."""
        shared = []
        for region in ancestry1:
            if region in ancestry2 and ancestry1[region] > 5.0 and ancestry2[region] > 5.0:
                shared.append(region)
        return shared
    
    def _categorize_region(self, region: str) -> str:
        """Categorize ancestry region."""
        region_lower = region.lower()
        
        if any(continent in region_lower for continent in ['africa', 'african']):
            return "African"
        elif any(continent in region_lower for continent in ['europe', 'european']):
            return "European"
        elif any(continent in region_lower for continent in ['asia', 'asian']):
            return "Asian"
        elif any(continent in region_lower for continent in ['america', 'american']):
            return "American"
        elif any(continent in region_lower for continent in ['oceania', 'pacific']):
            return "Oceanian"
        else:
            return "Other"
    
    def _generate_ancestry_report(
        self, 
        analysis: AncestryAnalysis, 
        format: str
    ) -> str:
        """Generate ancestry report in specified format."""
        if format.lower() == "json":
            return {
                "ancestry_composition": analysis.ancestry_composition,
                "primary_ancestry": analysis.primary_ancestry,
                "geographic_origins": analysis.geographic_origins,
                "haplogroups": {
                    "maternal": analysis.maternal_haplogroup,
                    "paternal": analysis.paternal_haplogroup
                },
                "ancient_ancestry": {
                    "neanderthal": analysis.neanderthal_percentage,
                    "denisovan": analysis.denisovan_percentage
                }
            }
        else:
            # Default to text format
            content = f"""
Ancestry Analysis Report
========================

Primary Ancestry: {analysis.primary_ancestry}

Ancestry Composition:
"""
            for region, percentage in sorted(analysis.ancestry_composition.items(), key=lambda x: x[1], reverse=True):
                content += f"- {region}: {percentage:.1f}%\n"
            
            content += f"""
Haplogroups:
- Maternal: {analysis.maternal_haplogroup or 'Not determined'}
- Paternal: {analysis.paternal_haplogroup or 'Not determined'}

Ancient Ancestry:
- Neanderthal: {analysis.neanderthal_percentage or 0:.2f}%
- Denisovan: {analysis.denisovan_percentage or 0:.2f}%
"""
            return content 