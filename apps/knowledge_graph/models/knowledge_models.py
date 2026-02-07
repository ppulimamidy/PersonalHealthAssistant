"""
Knowledge Graph Models for Personal Health Assistant.

This module defines comprehensive models for medical knowledge graph entities,
relationships, and queries following RDF/OWL standards.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, validator
import uuid


class EntityType(str, Enum):
    """Medical entity types in the knowledge graph."""
    CONDITION = "condition"
    SYMPTOM = "symptom"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LAB_TEST = "lab_test"
    VITAL_SIGN = "vital_sign"
    RISK_FACTOR = "risk_factor"
    BODY_PART = "body_part"
    ORGAN = "organ"
    DISEASE = "disease"
    SYNDROME = "syndrome"
    ALLERGY = "allergy"
    CONTRAINDICATION = "contraindication"
    SIDE_EFFECT = "side_effect"
    INTERACTION = "interaction"
    GUIDELINE = "guideline"
    EVIDENCE = "evidence"


class RelationshipType(str, Enum):
    """Relationship types in the medical knowledge graph."""
    # Condition relationships
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    ASSOCIATED_WITH = "associated_with"
    COMPLICATES = "complicates"
    COMPLICATED_BY = "complicated_by"
    
    # Symptom relationships
    MANIFESTS_AS = "manifests_as"
    INDICATES = "indicates"
    SUGGESTS = "suggests"
    
    # Treatment relationships
    TREATS = "treats"
    TREATED_BY = "treated_by"
    PREVENTS = "prevents"
    PREVENTED_BY = "prevented_by"
    CONTRAINDICATED_FOR = "contraindicated_for"
    
    # Medication relationships
    CONTAINS = "contains"
    INTERACTS_WITH = "interacts_with"
    ENHANCES = "enhances"
    REDUCES = "reduces"
    REPLACES = "replaces"
    
    # Anatomical relationships
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    CONNECTS_TO = "connects_to"
    
    # Risk relationships
    INCREASES_RISK_OF = "increases_risk_of"
    DECREASES_RISK_OF = "decreases_risk_of"
    RISK_FACTOR_FOR = "risk_factor_for"
    
    # Evidence relationships
    SUPPORTED_BY = "supported_by"
    CONTRADICTED_BY = "contradicted_by"
    BASED_ON = "based_on"
    
    # Patient relationships
    AFFECTS = "affects"
    MONITORED_BY = "monitored_by"
    INDICATED_FOR = "indicated_for"


class ConfidenceLevel(str, Enum):
    """Confidence levels for knowledge graph relationships."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EvidenceLevel(str, Enum):
    """Evidence levels for medical knowledge."""
    LEVEL_A = "level_a"  # High-quality evidence
    LEVEL_B = "level_b"  # Moderate-quality evidence
    LEVEL_C = "level_c"  # Low-quality evidence
    LEVEL_D = "level_d"  # Expert opinion
    LEVEL_E = "level_e"  # No evidence


class OntologySource(str, Enum):
    """Medical ontology sources."""
    SNOMED_CT = "snomed_ct"
    ICD_10 = "icd_10"
    ICD_11 = "icd_11"
    LOINC = "loinc"
    RxNorm = "rxnorm"
    UMLS = "umls"
    MESH = "mesh"
    DOID = "doid"
    HP = "hp"  # Human Phenotype Ontology
    CHEBI = "chebi"
    CUSTOM = "custom"


# Base Pydantic models for API responses
class MedicalEntityBase(BaseModel):
    """Base model for medical entities in the knowledge graph."""
    name: str = Field(..., min_length=1, description="Entity name")
    display_name: str = Field(..., description="Human-readable display name")
    entity_type: EntityType = Field(..., description="Type of medical entity")
    description: Optional[str] = Field(None, description="Entity description")
    synonyms: List[str] = Field(default_factory=list, description="Alternative names")
    ontology_ids: Dict[str, str] = Field(default_factory=dict, description="External ontology identifiers")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Confidence level")
    evidence_level: EvidenceLevel = Field(EvidenceLevel.LEVEL_C, description="Evidence level")
    source: OntologySource = Field(OntologySource.CUSTOM, description="Source ontology")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MedicalEntityCreate(MedicalEntityBase):
    """Model for creating medical entities."""
    pass


class MedicalEntityUpdate(BaseModel):
    """Model for updating medical entities."""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    synonyms: Optional[List[str]] = None
    ontology_ids: Optional[Dict[str, str]] = None
    confidence: Optional[ConfidenceLevel] = None
    evidence_level: Optional[EvidenceLevel] = None
    metadata: Optional[Dict[str, Any]] = None


class MedicalEntityResponse(MedicalEntityBase):
    """Model for medical entity API responses."""
    id: UUID = Field(..., description="Entity unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    relationship_count: int = Field(0, description="Number of relationships")
    
    class Config:
        from_attributes = True


class RelationshipBase(BaseModel):
    """Base model for relationships in the knowledge graph."""
    source_entity_id: UUID = Field(..., description="Source entity ID")
    target_entity_id: UUID = Field(..., description="Target entity ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    confidence: ConfidenceLevel = Field(ConfidenceLevel.MEDIUM, description="Confidence level")
    evidence_level: EvidenceLevel = Field(EvidenceLevel.LEVEL_C, description="Evidence level")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Relationship weight")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    source: OntologySource = Field(OntologySource.CUSTOM, description="Source ontology")


class RelationshipCreate(RelationshipBase):
    """Model for creating relationships."""
    pass


class RelationshipUpdate(BaseModel):
    """Model for updating relationships."""
    confidence: Optional[ConfidenceLevel] = None
    evidence_level: Optional[EvidenceLevel] = None
    weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class RelationshipResponse(RelationshipBase):
    """Model for relationship API responses."""
    id: UUID = Field(..., description="Relationship unique identifier")
    source_entity: MedicalEntityResponse = Field(..., description="Source entity")
    target_entity: MedicalEntityResponse = Field(..., description="Target entity")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class KnowledgeQueryBase(BaseModel):
    """Base model for knowledge graph queries."""
    query_type: str = Field(..., description="Type of query")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Result offset")


class SemanticSearchQuery(KnowledgeQueryBase):
    """Model for semantic search queries."""
    query_type: str = Field("semantic_search", description="Query type")
    query_text: str = Field(..., min_length=1, description="Search query text")
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter by entity types")
    confidence_threshold: Optional[ConfidenceLevel] = Field(None, description="Minimum confidence level")
    evidence_threshold: Optional[EvidenceLevel] = Field(None, description="Minimum evidence level")


class PathQuery(KnowledgeQueryBase):
    """Model for path queries in the knowledge graph."""
    query_type: str = Field("path_query", description="Query type")
    source_entity_id: UUID = Field(..., description="Source entity ID")
    target_entity_id: UUID = Field(..., description="Target entity ID")
    max_path_length: int = Field(3, ge=1, le=10, description="Maximum path length")
    relationship_types: Optional[List[RelationshipType]] = Field(None, description="Allowed relationship types")


class RecommendationQuery(KnowledgeQueryBase):
    """Model for recommendation queries."""
    query_type: str = Field("recommendation", description="Query type")
    patient_id: UUID = Field(..., description="Patient ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Patient context")
    recommendation_type: str = Field(..., description="Type of recommendation")
    max_recommendations: int = Field(10, ge=1, le=50, description="Maximum recommendations")


class KnowledgeGraphResponse(BaseModel):
    """Model for knowledge graph query responses."""
    query_id: UUID = Field(..., description="Query unique identifier")
    query_type: str = Field(..., description="Query type")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    total_count: int = Field(0, description="Total result count")
    execution_time: float = Field(0.0, description="Query execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MedicalRecommendation(BaseModel):
    """Model for medical recommendations based on knowledge graph."""
    id: UUID = Field(..., description="Recommendation unique identifier")
    patient_id: UUID = Field(..., description="Patient ID")
    recommendation_type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Recommendation description")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    evidence_level: EvidenceLevel = Field(..., description="Evidence level")
    reasoning: List[str] = Field(default_factory=list, description="Reasoning steps")
    related_entities: List[MedicalEntityResponse] = Field(default_factory=list, description="Related medical entities")
    actions: List[str] = Field(default_factory=list, description="Recommended actions")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class OntologyImportRequest(BaseModel):
    """Model for ontology import requests."""
    ontology_source: OntologySource = Field(..., description="Source ontology")
    import_type: str = Field(..., description="Type of import (full, incremental, specific)")
    entities: Optional[List[str]] = Field(None, description="Specific entities to import")
    relationships: Optional[List[str]] = Field(None, description="Specific relationships to import")
    update_existing: bool = Field(True, description="Update existing entities")
    validate_only: bool = Field(False, description="Validate without importing")


class OntologyImportResponse(BaseModel):
    """Model for ontology import responses."""
    import_id: UUID = Field(..., description="Import unique identifier")
    ontology_source: OntologySource = Field(..., description="Source ontology")
    status: str = Field(..., description="Import status")
    entities_imported: int = Field(0, description="Number of entities imported")
    relationships_imported: int = Field(0, description="Number of relationships imported")
    errors: List[str] = Field(default_factory=list, description="Import errors")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
    execution_time: float = Field(0.0, description="Import execution time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")


class KnowledgeGraphStats(BaseModel):
    """Model for knowledge graph statistics."""
    total_entities: int = Field(0, description="Total number of entities")
    total_relationships: int = Field(0, description="Total number of relationships")
    entities_by_type: Dict[str, int] = Field(default_factory=dict, description="Entities by type")
    relationships_by_type: Dict[str, int] = Field(default_factory=dict, description="Relationships by type")
    ontology_coverage: Dict[str, int] = Field(default_factory=dict, description="Coverage by ontology")
    last_updated: datetime = Field(..., description="Last update timestamp")
    graph_density: float = Field(0.0, description="Graph density")
    average_degree: float = Field(0.0, description="Average node degree")


class HealthInsight(BaseModel):
    """Model for health insights derived from knowledge graph."""
    id: UUID = Field(..., description="Insight unique identifier")
    patient_id: UUID = Field(..., description="Patient ID")
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    related_conditions: List[MedicalEntityResponse] = Field(default_factory=list, description="Related conditions")
    related_symptoms: List[MedicalEntityResponse] = Field(default_factory=list, description="Related symptoms")
    risk_factors: List[MedicalEntityResponse] = Field(default_factory=list, description="Risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True 