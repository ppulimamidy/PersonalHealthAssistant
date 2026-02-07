"""
Genomic data models for Personal Health Assistant.

This module contains models for storing and managing genomic data including:
- DNA sequences and raw genomic data
- Genetic variants and mutations
- Pharmacogenomic profiles
- Quality metrics and metadata
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Integer, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid

from common.models.base import Base


class DataSource(str, Enum):
    """Source of genomic data."""
    DIRECT_TO_CONSUMER = "direct_to_consumer"
    CLINICAL_LAB = "clinical_lab"
    RESEARCH_STUDY = "research_study"
    HOSPITAL = "hospital"
    PHARMACOGENOMIC_TEST = "pharmacogenomic_test"
    ANCESTRY_TEST = "ancestry_test"
    HEALTH_TEST = "health_test"


class DataFormat(str, Enum):
    """Format of genomic data."""
    FASTQ = "fastq"
    BAM = "bam"
    VCF = "vcf"
    GFF = "gff"
    BED = "bed"
    JSON = "json"
    CSV = "csv"
    TXT = "txt"


class QualityStatus(str, Enum):
    """Quality status of genomic data."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class VariantType(str, Enum):
    """Type of genetic variant."""
    SNV = "snv"  # Single nucleotide variant
    INDEL = "indel"  # Insertion/deletion
    CNV = "cnv"  # Copy number variant
    SV = "sv"  # Structural variant
    MNV = "mnv"  # Multi-nucleotide variant


class VariantClassification(str, Enum):
    """Clinical classification of variants."""
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


class GenomicData(Base):
    """Model for storing genomic data files and metadata."""
    
    __tablename__ = "genomic_data"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    
    # Data information
    data_source = Column(SQLEnum(DataSource), nullable=False)
    data_format = Column(SQLEnum(DataFormat), nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # in bytes
    checksum = Column(String, nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    quality_status = Column(SQLEnum(QualityStatus), default=QualityStatus.UNKNOWN)
    coverage_depth = Column(Float, nullable=True)
    coverage_breadth = Column(Float, nullable=True)
    
    # Metadata
    sample_id = Column(String, nullable=True)
    collection_date = Column(DateTime, nullable=True)
    processing_date = Column(DateTime, nullable=True)
    lab_name = Column(String, nullable=True)
    test_name = Column(String, nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, default=dict)
    
    # Status
    is_processed = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    variants = relationship("GeneticVariant", back_populates="genomic_data")
    analyses = relationship("GenomicAnalysis", back_populates="genomic_data")
    
    def __repr__(self):
        return f"<GenomicData(id={self.id}, user_id={self.user_id}, source={self.data_source})>"


class GeneticVariant(Base):
    """Model for storing genetic variants."""
    
    __tablename__ = "genetic_variants"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    genomic_data_id = Column(UUID(as_uuid=True), ForeignKey("genomics.genomic_data.id"), nullable=False)
    
    # Variant information
    chromosome = Column(String, nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    reference_allele = Column(String, nullable=False)
    alternate_allele = Column(String, nullable=False)
    variant_type = Column(SQLEnum(VariantType), nullable=False)
    
    # Clinical information
    rs_id = Column(String, nullable=True, index=True)  # dbSNP ID
    gene_name = Column(String, nullable=True, index=True)
    gene_id = Column(String, nullable=True)
    transcript_id = Column(String, nullable=True)
    protein_change = Column(String, nullable=True)
    
    # Frequency and population data
    allele_frequency = Column(Float, nullable=True)
    population_frequency = Column(JSON, default=dict)
    
    # Clinical significance
    clinical_significance = Column(SQLEnum(VariantClassification), nullable=True)
    clinical_annotations = Column(JSON, default=dict)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    read_depth = Column(Integer, nullable=True)
    allele_depth = Column(Integer, nullable=True)
    
    # Additional annotations
    annotations = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    genomic_data = relationship("GenomicData", back_populates="variants")
    
    def __repr__(self):
        return f"<GeneticVariant(id={self.id}, chr{self.chromosome}:{self.position})>"


class PharmacogenomicProfile(Base):
    """Model for storing pharmacogenomic profiles."""
    
    __tablename__ = "pharmacogenomic_profiles"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    
    # Profile information
    profile_name = Column(String, nullable=False)
    test_date = Column(DateTime, nullable=False)
    lab_name = Column(String, nullable=True)
    test_method = Column(String, nullable=True)
    
    # Gene-drug interactions
    gene_drug_interactions = Column(JSON, default=list)
    
    # Metabolizer status
    metabolizer_status = Column(JSON, default=dict)
    
    # Risk factors
    drug_risks = Column(JSON, default=list)
    drug_recommendations = Column(JSON, default=list)
    
    # Additional data
    raw_data = Column(JSON, default=dict)
    interpretation = Column(Text, nullable=True)
    
    # Status
    is_interpreted = Column(Boolean, default=False)
    is_reviewed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PharmacogenomicProfile(id={self.id}, user_id={self.user_id})>"


# Pydantic models for API
class GenomicDataBase(BaseModel):
    """Base model for genomic data."""
    data_source: DataSource
    data_format: DataFormat
    sample_id: Optional[str] = None
    collection_date: Optional[datetime] = None
    lab_name: Optional[str] = None
    test_name: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class GenomicDataCreate(GenomicDataBase):
    """Model for creating genomic data."""
    file_path: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None


class GenomicDataUpdate(BaseModel):
    """Model for updating genomic data."""
    quality_score: Optional[float] = None
    quality_status: Optional[QualityStatus] = None
    coverage_depth: Optional[float] = None
    coverage_breadth: Optional[float] = None
    is_processed: Optional[bool] = None
    is_analyzed: Optional[bool] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class GenomicDataResponse(GenomicDataBase):
    """Model for genomic data API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    file_path: str
    file_size: Optional[int] = None
    quality_score: Optional[float] = None
    quality_status: QualityStatus
    is_processed: bool
    is_analyzed: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GeneticVariantBase(BaseModel):
    """Base model for genetic variants."""
    chromosome: str
    position: int
    reference_allele: str
    alternate_allele: str
    variant_type: VariantType
    rs_id: Optional[str] = None
    gene_name: Optional[str] = None
    gene_id: Optional[str] = None
    protein_change: Optional[str] = None
    allele_frequency: Optional[float] = None
    clinical_significance: Optional[VariantClassification] = None


class GeneticVariantCreate(GeneticVariantBase):
    """Model for creating genetic variants."""
    genomic_data_id: uuid.UUID
    quality_score: Optional[float] = None
    read_depth: Optional[int] = None
    allele_depth: Optional[int] = None
    annotations: Dict[str, Any] = Field(default_factory=dict)


class GeneticVariantResponse(GeneticVariantBase):
    """Model for genetic variant API responses."""
    id: uuid.UUID
    genomic_data_id: uuid.UUID
    quality_score: Optional[float] = None
    read_depth: Optional[int] = None
    allele_depth: Optional[int] = None
    clinical_annotations: Dict[str, Any] = Field(default_factory=dict)
    annotations: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class PharmacogenomicProfileBase(BaseModel):
    """Base model for pharmacogenomic profiles."""
    profile_name: str
    test_date: datetime
    lab_name: Optional[str] = None
    test_method: Optional[str] = None


class PharmacogenomicProfileCreate(PharmacogenomicProfileBase):
    """Model for creating pharmacogenomic profiles."""
    gene_drug_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    metabolizer_status: Dict[str, Any] = Field(default_factory=dict)
    drug_risks: List[Dict[str, Any]] = Field(default_factory=list)
    drug_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    interpretation: Optional[str] = None


class PharmacogenomicProfileResponse(PharmacogenomicProfileBase):
    """Model for pharmacogenomic profile API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    gene_drug_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    metabolizer_status: Dict[str, Any] = Field(default_factory=dict)
    drug_risks: List[Dict[str, Any]] = Field(default_factory=list)
    drug_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    is_interpreted: bool
    is_reviewed: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 