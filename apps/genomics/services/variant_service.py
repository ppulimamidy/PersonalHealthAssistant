"""
Variant service for Personal Health Assistant.

This service handles genetic variant management including:
- Variant detection and storage
- Variant annotation
- Clinical significance assessment
- Variant filtering and search
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.genomic_data import (
    GeneticVariant, GeneticVariantCreate, GeneticVariantResponse,
    VariantType, VariantClassification
)
from common.exceptions import NotFoundError, ValidationError


class VariantService:
    """Service for managing genetic variants."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_variant(
        self, 
        variant: GeneticVariantCreate, 
        user_id: uuid.UUID
    ) -> GeneticVariantResponse:
        """Create new genetic variant."""
        try:
            # Verify user has access to the genomic data
            from ..models.genomic_data import GenomicData
            genomic_data = self.db.query(GenomicData).filter(
                GenomicData.id == variant.genomic_data_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not genomic_data:
                raise ValidationError("Genomic data not found or access denied")
            
            # Create variant record
            genetic_variant = GeneticVariant(
                genomic_data_id=variant.genomic_data_id,
                chromosome=variant.chromosome,
                position=variant.position,
                reference_allele=variant.reference_allele,
                alternate_allele=variant.alternate_allele,
                variant_type=variant.variant_type,
                rs_id=variant.rs_id,
                gene_name=variant.gene_name,
                gene_id=variant.gene_id,
                protein_change=variant.protein_change,
                allele_frequency=variant.allele_frequency,
                clinical_significance=variant.clinical_significance,
                quality_score=variant.quality_score,
                read_depth=variant.read_depth,
                allele_depth=variant.allele_depth,
                annotations=variant.annotations
            )
            
            self.db.add(genetic_variant)
            self.db.commit()
            self.db.refresh(genetic_variant)
            
            return GeneticVariantResponse.from_orm(genetic_variant)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create variant: {str(e)}")
    
    async def list_variants(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        chromosome: Optional[str] = None,
        gene_name: Optional[str] = None,
        variant_type: Optional[VariantType] = None,
        clinical_significance: Optional[VariantClassification] = None,
        genomic_data_id: Optional[str] = None
    ) -> List[GeneticVariantResponse]:
        """List genetic variants for user."""
        try:
            query = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(GenomicData.user_id == user_id)
            
            if chromosome:
                query = query.filter(GeneticVariant.chromosome == chromosome)
            if gene_name:
                query = query.filter(GeneticVariant.gene_name == gene_name)
            if variant_type:
                query = query.filter(GeneticVariant.variant_type == variant_type)
            if clinical_significance:
                query = query.filter(GeneticVariant.clinical_significance == clinical_significance)
            if genomic_data_id:
                query = query.filter(GeneticVariant.genomic_data_id == genomic_data_id)
            
            variants = query.offset(skip).limit(limit).all()
            return [GeneticVariantResponse.from_orm(variant) for variant in variants]
        except Exception as e:
            raise ValidationError(f"Failed to list variants: {str(e)}")
    
    async def get_variant(
        self, 
        variant_id: str, 
        user_id: uuid.UUID
    ) -> GeneticVariantResponse:
        """Get specific variant by ID."""
        try:
            variant = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GeneticVariant.id == variant_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not variant:
                raise NotFoundError("Variant not found")
            
            return GeneticVariantResponse.from_orm(variant)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get variant: {str(e)}")
    
    async def update_variant(
        self,
        variant_id: str,
        variant: GeneticVariantCreate,
        user_id: uuid.UUID
    ) -> GeneticVariantResponse:
        """Update variant."""
        try:
            existing_variant = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GeneticVariant.id == variant_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not existing_variant:
                raise NotFoundError("Variant not found")
            
            # Update fields
            for field, value in variant.dict(exclude={'genomic_data_id'}).items():
                setattr(existing_variant, field, value)
            
            existing_variant.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_variant)
            
            return GeneticVariantResponse.from_orm(existing_variant)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update variant: {str(e)}")
    
    async def delete_variant(
        self, 
        variant_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete variant."""
        try:
            variant = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GeneticVariant.id == variant_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not variant:
                raise NotFoundError("Variant not found")
            
            self.db.delete(variant)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete variant: {str(e)}")
    
    async def search_variants(
        self,
        query: str,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[GeneticVariantResponse]:
        """Search variants by various criteria."""
        try:
            # Search in gene names, rs IDs, and chromosome positions
            variants = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GenomicData.user_id == user_id
            ).filter(
                (GeneticVariant.gene_name.ilike(f"%{query}%")) |
                (GeneticVariant.rs_id.ilike(f"%{query}%")) |
                (GeneticVariant.chromosome.ilike(f"%{query}%"))
            ).offset(skip).limit(limit).all()
            
            return [GeneticVariantResponse.from_orm(variant) for variant in variants]
        except Exception as e:
            raise ValidationError(f"Failed to search variants: {str(e)}")
    
    async def get_variants_by_chromosome(
        self,
        chromosome: str,
        user_id: uuid.UUID,
        start_position: Optional[int] = None,
        end_position: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GeneticVariantResponse]:
        """Get variants by chromosome and position range."""
        try:
            query = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GenomicData.user_id == user_id,
                GeneticVariant.chromosome == chromosome
            )
            
            if start_position:
                query = query.filter(GeneticVariant.position >= start_position)
            if end_position:
                query = query.filter(GeneticVariant.position <= end_position)
            
            variants = query.offset(skip).limit(limit).all()
            return [GeneticVariantResponse.from_orm(variant) for variant in variants]
        except Exception as e:
            raise ValidationError(f"Failed to get variants by chromosome: {str(e)}")
    
    async def get_variants_by_gene(
        self,
        gene_name: str,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[GeneticVariantResponse]:
        """Get variants by gene name."""
        try:
            variants = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GenomicData.user_id == user_id,
                GeneticVariant.gene_name == gene_name
            ).offset(skip).limit(limit).all()
            
            return [GeneticVariantResponse.from_orm(variant) for variant in variants]
        except Exception as e:
            raise ValidationError(f"Failed to get variants by gene: {str(e)}")
    
    async def get_variants_by_rs_id(
        self, 
        rs_id: str, 
        user_id: uuid.UUID
    ) -> List[GeneticVariantResponse]:
        """Get variants by dbSNP rs ID."""
        try:
            variants = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GenomicData.user_id == user_id,
                GeneticVariant.rs_id == rs_id
            ).all()
            
            return [GeneticVariantResponse.from_orm(variant) for variant in variants]
        except Exception as e:
            raise ValidationError(f"Failed to get variants by rs ID: {str(e)}")
    
    async def annotate_variant(
        self, 
        variant_id: str, 
        user_id: uuid.UUID
    ) -> GeneticVariantResponse:
        """Annotate variant with additional information."""
        try:
            variant = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GeneticVariant.id == variant_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not variant:
                raise NotFoundError("Variant not found")
            
            # Simulate annotation process
            # In a real implementation, this would call external annotation services
            annotation_data = {
                "functional_impact": "MODERATE",
                "consequence": "missense_variant",
                "sift_score": 0.05,
                "polyphen_score": 0.85,
                "cadd_score": 15.2,
                "clinvar_entries": [
                    {
                        "accession": "RCV000123456",
                        "clinical_significance": "Likely_pathogenic",
                        "review_status": "criteria_provided,_multiple_submitters,_no_conflicts"
                    }
                ]
            }
            
            variant.annotations.update(annotation_data)
            variant.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(variant)
            
            return GeneticVariantResponse.from_orm(variant)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to annotate variant: {str(e)}")
    
    async def get_variant_clinical_info(
        self, 
        variant_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get clinical information for variant."""
        try:
            variant = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GeneticVariant.id == variant_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not variant:
                raise NotFoundError("Variant not found")
            
            return {
                "clinical_significance": variant.clinical_significance,
                "clinical_annotations": variant.clinical_annotations,
                "gene_name": variant.gene_name,
                "protein_change": variant.protein_change,
                "rs_id": variant.rs_id
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get variant clinical info: {str(e)}")
    
    async def get_variant_frequency(
        self, 
        variant_id: str, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get population frequency data for variant."""
        try:
            variant = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(
                GeneticVariant.id == variant_id,
                GenomicData.user_id == user_id
            ).first()
            
            if not variant:
                raise NotFoundError("Variant not found")
            
            return {
                "allele_frequency": variant.allele_frequency,
                "population_frequency": variant.population_frequency,
                "rs_id": variant.rs_id
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get variant frequency: {str(e)}")
    
    async def get_variant_statistics(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get variant statistics for the user."""
        try:
            total_variants = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(GenomicData.user_id == user_id).count()
            
            # Count by variant type
            variant_types = self.db.query(GeneticVariant.variant_type).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(GenomicData.user_id == user_id).all()
            
            type_counts = {}
            for vt in variant_types:
                type_counts[vt[0]] = type_counts.get(vt[0], 0) + 1
            
            # Count by clinical significance
            clinical_significance = self.db.query(GeneticVariant.clinical_significance).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(GenomicData.user_id == user_id).all()
            
            significance_counts = {}
            for cs in clinical_significance:
                if cs[0]:
                    significance_counts[cs[0]] = significance_counts.get(cs[0], 0) + 1
            
            return {
                "total_variants": total_variants,
                "variant_types": type_counts,
                "clinical_significance": significance_counts
            }
        except Exception as e:
            raise ValidationError(f"Failed to get variant statistics: {str(e)}")
    
    async def export_variants(
        self,
        user_id: uuid.UUID,
        format: str = "vcf",
        chromosome: Optional[str] = None,
        gene_name: Optional[str] = None,
        clinical_significance: Optional[VariantClassification] = None
    ) -> Dict[str, Any]:
        """Export variants in specified format."""
        try:
            query = self.db.query(GeneticVariant).join(
                GenomicData, GeneticVariant.genomic_data_id == GenomicData.id
            ).filter(GenomicData.user_id == user_id)
            
            if chromosome:
                query = query.filter(GeneticVariant.chromosome == chromosome)
            if gene_name:
                query = query.filter(GeneticVariant.gene_name == gene_name)
            if clinical_significance:
                query = query.filter(GeneticVariant.clinical_significance == clinical_significance)
            
            variants = query.all()
            
            # Convert to specified format
            if format.lower() == "vcf":
                return self._export_to_vcf(variants)
            elif format.lower() == "json":
                return self._export_to_json(variants)
            elif format.lower() == "csv":
                return self._export_to_csv(variants)
            else:
                raise ValidationError(f"Unsupported export format: {format}")
                
        except Exception as e:
            raise ValidationError(f"Failed to export variants: {str(e)}")
    
    def _export_to_vcf(self, variants: List[GeneticVariant]) -> Dict[str, Any]:
        """Export variants to VCF format."""
        vcf_lines = [
            "##fileformat=VCFv4.2",
            "##fileDate=" + datetime.now().strftime("%Y%m%d"),
            "##source=PersonalHealthAssistant",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
        ]
        
        for variant in variants:
            vcf_line = f"{variant.chromosome}\t{variant.position}\t{variant.rs_id or '.'}\t{variant.reference_allele}\t{variant.alternate_allele}\t100\tPASS\tNS=1;DP=100"
            vcf_lines.append(vcf_line)
        
        return {
            "format": "vcf",
            "content": "\n".join(vcf_lines),
            "filename": f"variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.vcf"
        }
    
    def _export_to_json(self, variants: List[GeneticVariant]) -> Dict[str, Any]:
        """Export variants to JSON format."""
        variant_data = []
        for variant in variants:
            variant_data.append({
                "chromosome": variant.chromosome,
                "position": variant.position,
                "rs_id": variant.rs_id,
                "reference_allele": variant.reference_allele,
                "alternate_allele": variant.alternate_allele,
                "gene_name": variant.gene_name,
                "clinical_significance": variant.clinical_significance,
                "allele_frequency": variant.allele_frequency
            })
        
        return {
            "format": "json",
            "content": variant_data,
            "filename": f"variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    
    def _export_to_csv(self, variants: List[GeneticVariant]) -> Dict[str, Any]:
        """Export variants to CSV format."""
        csv_lines = ["chromosome,position,rs_id,reference_allele,alternate_allele,gene_name,clinical_significance,allele_frequency"]
        
        for variant in variants:
            csv_line = f"{variant.chromosome},{variant.position},{variant.rs_id or ''},{variant.reference_allele},{variant.alternate_allele},{variant.gene_name or ''},{variant.clinical_significance or ''},{variant.allele_frequency or ''}"
            csv_lines.append(csv_line)
        
        return {
            "format": "csv",
            "content": "\n".join(csv_lines),
            "filename": f"variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        } 