"""
Analysis models for Personal Health Assistant.

This module contains models for storing analysis results including:
- Genomic analysis results
- Disease risk assessments
- Ancestry analysis
- Trait predictions
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


class AnalysisType(str, Enum):
    """Type of genomic analysis."""
    VARIANT_ANALYSIS = "variant_analysis"
    DISEASE_RISK = "disease_risk"
    ANCESTRY = "ancestry"
    TRAIT_PREDICTION = "trait_prediction"
    PHARMACOGENOMIC = "pharmacogenomic"
    CARRIER_SCREENING = "carrier_screening"
    CANCER_RISK = "cancer_risk"
    CARDIOVASCULAR_RISK = "cardiovascular_risk"


class AnalysisStatus(str, Enum):
    """Status of analysis."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    """Risk level classification."""
    VERY_LOW = "very_low"
    LOW = "low"
    AVERAGE = "average"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConfidenceLevel(str, Enum):
    """Confidence level of analysis."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class GenomicAnalysis(Base):
    """Model for storing genomic analysis results."""
    
    __tablename__ = "genomic_analyses"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    genomic_data_id = Column(UUID(as_uuid=True), ForeignKey("genomics.genomic_data.id"), nullable=False)
    
    # Analysis information
    analysis_type = Column(SQLEnum(AnalysisType), nullable=False)
    analysis_name = Column(String, nullable=False)
    analysis_version = Column(String, nullable=False)
    
    # Status and progress
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    results = Column(JSON, default=dict)
    summary = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Quality metrics
    quality_metrics = Column(JSON, default=dict)
    error_logs = Column(JSON, default=list)
    
    # Metadata
    parameters = Column(JSON, default=dict)
    extra_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    genomic_data = relationship("GenomicData", back_populates="analyses")
    disease_risks = relationship("DiseaseRiskAssessment", back_populates="analysis")
    ancestry_results = relationship("AncestryAnalysis", back_populates="analysis")
    
    def __repr__(self):
        return f"<GenomicAnalysis(id={self.id}, type={self.analysis_type}, status={self.status})>"


class DiseaseRiskAssessment(Base):
    """Model for storing disease risk assessments."""
    
    __tablename__ = "disease_risk_assessments"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("genomics.genomic_analyses.id"), nullable=False)
    
    # Disease information
    disease_name = Column(String, nullable=False, index=True)
    disease_id = Column(String, nullable=True)  # OMIM ID or similar
    disease_category = Column(String, nullable=True)
    
    # Risk assessment
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    risk_score = Column(Float, nullable=True)  # 0.0 to 1.0
    population_risk = Column(Float, nullable=True)  # Baseline population risk
    relative_risk = Column(Float, nullable=True)  # Risk relative to population
    
    # Genetic factors
    contributing_variants = Column(JSON, default=list)
    genetic_factors = Column(JSON, default=dict)
    
    # Clinical information
    clinical_significance = Column(String, nullable=True)
    clinical_recommendations = Column(JSON, default=list)
    screening_recommendations = Column(JSON, default=list)
    
    # Additional data
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=True)
    evidence_level = Column(String, nullable=True)
    references = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("GenomicAnalysis", back_populates="disease_risks")
    
    def __repr__(self):
        return f"<DiseaseRiskAssessment(id={self.id}, disease={self.disease_name}, risk={self.risk_level})>"


class AncestryAnalysis(Base):
    """Model for storing ancestry analysis results."""
    
    __tablename__ = "ancestry_analyses"
    __table_args__ = {'schema': 'genomics', 'extend_existing': True}
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("genomics.genomic_analyses.id"), nullable=False)
    
    # Ancestry composition
    ancestry_composition = Column(JSON, default=dict)  # {region: percentage}
    primary_ancestry = Column(String, nullable=True)
    secondary_ancestries = Column(JSON, default=list)
    
    # Geographic origins
    geographic_origins = Column(JSON, default=list)
    migration_patterns = Column(JSON, default=list)
    
    # Population matches
    population_matches = Column(JSON, default=list)
    reference_populations = Column(JSON, default=list)
    
    # Neanderthal and Denisovan ancestry
    neanderthal_percentage = Column(Float, nullable=True)
    denisovan_percentage = Column(Float, nullable=True)
    
    # Haplogroups
    maternal_haplogroup = Column(String, nullable=True)
    paternal_haplogroup = Column(String, nullable=True)
    
    # Additional data
    confidence_scores = Column(JSON, default=dict)
    methodology = Column(String, nullable=True)
    reference_database = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("GenomicAnalysis", back_populates="ancestry_results")
    
    def __repr__(self):
        return f"<AncestryAnalysis(id={self.id}, primary={self.primary_ancestry})>"


# Pydantic models for API
class GenomicAnalysisBase(BaseModel):
    """Base model for genomic analysis."""
    analysis_type: AnalysisType
    analysis_name: str
    analysis_version: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class GenomicAnalysisCreate(GenomicAnalysisBase):
    """Model for creating genomic analysis."""
    genomic_data_id: uuid.UUID


class GenomicAnalysisUpdate(BaseModel):
    """Model for updating genomic analysis."""
    status: Optional[AnalysisStatus] = None
    progress: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    error_logs: Optional[List[str]] = None


class GenomicAnalysisResponse(GenomicAnalysisBase):
    """Model for genomic analysis API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    genomic_data_id: uuid.UUID
    status: AnalysisStatus
    progress: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DiseaseRiskAssessmentBase(BaseModel):
    """Base model for disease risk assessment."""
    disease_name: str
    disease_id: Optional[str] = None
    disease_category: Optional[str] = None
    risk_level: RiskLevel
    risk_score: Optional[float] = None
    population_risk: Optional[float] = None
    relative_risk: Optional[float] = None


class DiseaseRiskAssessmentCreate(DiseaseRiskAssessmentBase):
    """Model for creating disease risk assessment."""
    analysis_id: uuid.UUID
    contributing_variants: List[Dict[str, Any]] = Field(default_factory=list)
    genetic_factors: Dict[str, Any] = Field(default_factory=dict)
    clinical_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    screening_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_level: Optional[ConfidenceLevel] = None
    evidence_level: Optional[str] = None
    references: List[str] = Field(default_factory=list)


class DiseaseRiskAssessmentResponse(DiseaseRiskAssessmentBase):
    """Model for disease risk assessment API responses."""
    id: uuid.UUID
    analysis_id: uuid.UUID
    contributing_variants: List[Dict[str, Any]] = Field(default_factory=list)
    genetic_factors: Dict[str, Any] = Field(default_factory=dict)
    clinical_significance: Optional[str] = None
    clinical_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    screening_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_level: Optional[ConfidenceLevel] = None
    evidence_level: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    created_at: datetime
    
    class Config:
        from_attributes = True


class AncestryAnalysisBase(BaseModel):
    """Base model for ancestry analysis."""
    ancestry_composition: Dict[str, float] = Field(default_factory=dict)
    primary_ancestry: Optional[str] = None
    secondary_ancestries: List[str] = Field(default_factory=list)
    geographic_origins: List[Dict[str, Any]] = Field(default_factory=list)


class AncestryAnalysisCreate(AncestryAnalysisBase):
    """Model for creating ancestry analysis."""
    analysis_id: uuid.UUID
    migration_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    population_matches: List[Dict[str, Any]] = Field(default_factory=list)
    reference_populations: List[Dict[str, Any]] = Field(default_factory=list)
    neanderthal_percentage: Optional[float] = None
    denisovan_percentage: Optional[float] = None
    maternal_haplogroup: Optional[str] = None
    paternal_haplogroup: Optional[str] = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    methodology: Optional[str] = None
    reference_database: Optional[str] = None


class AncestryAnalysisResponse(AncestryAnalysisBase):
    """Model for ancestry analysis API responses."""
    id: uuid.UUID
    analysis_id: uuid.UUID
    migration_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    population_matches: List[Dict[str, Any]] = Field(default_factory=list)
    reference_populations: List[Dict[str, Any]] = Field(default_factory=list)
    neanderthal_percentage: Optional[float] = None
    denisovan_percentage: Optional[float] = None
    maternal_haplogroup: Optional[str] = None
    paternal_haplogroup: Optional[str] = None
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    methodology: Optional[str] = None
    reference_database: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 