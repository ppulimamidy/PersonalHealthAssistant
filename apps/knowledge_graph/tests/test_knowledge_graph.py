"""Unit tests for Knowledge Graph service models."""
import pytest
from uuid import uuid4


class TestMedicalEntityModels:
    def test_entity_create(self):
        """Test MedicalEntityCreate model with valid data."""
        from apps.knowledge_graph.models.knowledge_models import MedicalEntityCreate

        entity = MedicalEntityCreate(
            name="type_2_diabetes",
            display_name="Type 2 Diabetes Mellitus",
            entity_type="condition",
            description="A chronic condition affecting how the body processes blood sugar.",
            synonyms=["T2DM", "adult-onset diabetes", "non-insulin-dependent diabetes"],
            ontology_ids={"snomed_ct": "44054006", "icd_10": "E11"},
            confidence="high",
            evidence_level="level_a",
            source="snomed_ct",
        )
        assert entity.name == "type_2_diabetes"
        assert entity.entity_type == "condition"
        assert len(entity.synonyms) == 3
        assert entity.ontology_ids["icd_10"] == "E11"

    def test_entity_create_minimal(self):
        """Test MedicalEntityCreate with minimal fields."""
        from apps.knowledge_graph.models.knowledge_models import MedicalEntityCreate

        entity = MedicalEntityCreate(
            name="headache",
            display_name="Headache",
            entity_type="symptom",
        )
        assert entity.synonyms == []
        assert entity.confidence == "medium"
        assert entity.metadata == {}

    def test_entity_update_partial(self):
        """Test MedicalEntityUpdate allows partial updates."""
        from apps.knowledge_graph.models.knowledge_models import MedicalEntityUpdate

        update = MedicalEntityUpdate(description="Updated description")
        assert update.description == "Updated description"
        assert update.name is None

    def test_entity_missing_required(self):
        """Test MedicalEntityCreate fails without required fields."""
        from apps.knowledge_graph.models.knowledge_models import MedicalEntityCreate

        with pytest.raises(Exception):
            MedicalEntityCreate(name="incomplete")


class TestRelationshipModels:
    def test_relationship_create(self):
        """Test RelationshipCreate model with valid data."""
        from apps.knowledge_graph.models.knowledge_models import RelationshipCreate

        rel = RelationshipCreate(
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            relationship_type="treats",
            confidence="high",
            evidence_level="level_a",
            weight=0.95,
            source="snomed_ct",
        )
        assert rel.relationship_type == "treats"
        assert rel.weight == 0.95
        assert rel.confidence == "high"

    def test_relationship_create_defaults(self):
        """Test RelationshipCreate default values."""
        from apps.knowledge_graph.models.knowledge_models import RelationshipCreate

        rel = RelationshipCreate(
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            relationship_type="associated_with",
        )
        assert rel.confidence == "medium"
        assert rel.weight == 1.0
        assert rel.metadata == {}

    def test_relationship_invalid_weight(self):
        """Test RelationshipCreate rejects invalid weight."""
        from apps.knowledge_graph.models.knowledge_models import RelationshipCreate

        with pytest.raises(Exception):
            RelationshipCreate(
                source_entity_id=uuid4(),
                target_entity_id=uuid4(),
                relationship_type="treats",
                weight=1.5,  # Over max of 1.0
            )

    def test_relationship_update_partial(self):
        """Test RelationshipUpdate allows partial updates."""
        from apps.knowledge_graph.models.knowledge_models import RelationshipUpdate

        update = RelationshipUpdate(weight=0.8, confidence="high")
        assert update.weight == 0.8
        assert update.evidence_level is None

    def test_relationship_missing_required(self):
        """Test RelationshipCreate fails without required fields."""
        from apps.knowledge_graph.models.knowledge_models import RelationshipCreate

        with pytest.raises(Exception):
            RelationshipCreate(relationship_type="treats")


class TestQueryModels:
    def test_semantic_search_query(self):
        """Test SemanticSearchQuery model."""
        from apps.knowledge_graph.models.knowledge_models import SemanticSearchQuery

        query = SemanticSearchQuery(
            query_text="treatments for type 2 diabetes",
            entity_types=["treatment", "medication"],
            confidence_threshold="high",
            limit=20,
        )
        assert query.query_text == "treatments for type 2 diabetes"
        assert query.query_type == "semantic_search"
        assert query.limit == 20

    def test_path_query(self):
        """Test PathQuery model."""
        from apps.knowledge_graph.models.knowledge_models import PathQuery

        query = PathQuery(
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            max_path_length=5,
            relationship_types=["treats", "causes"],
        )
        assert query.query_type == "path_query"
        assert query.max_path_length == 5


class TestKnowledgeGraphEnums:
    def test_entity_type_enum(self):
        """Test EntityType enum values."""
        from apps.knowledge_graph.models.knowledge_models import EntityType

        assert EntityType.CONDITION == "condition"
        assert EntityType.MEDICATION == "medication"
        assert EntityType.SYMPTOM == "symptom"

    def test_relationship_type_enum(self):
        """Test RelationshipType enum values."""
        from apps.knowledge_graph.models.knowledge_models import RelationshipType

        assert RelationshipType.TREATS == "treats"
        assert RelationshipType.CAUSES == "causes"
        assert RelationshipType.INTERACTS_WITH == "interacts_with"

    def test_evidence_level_enum(self):
        """Test EvidenceLevel enum values."""
        from apps.knowledge_graph.models.knowledge_models import EvidenceLevel

        assert EvidenceLevel.LEVEL_A == "level_a"
        assert EvidenceLevel.LEVEL_E == "level_e"
