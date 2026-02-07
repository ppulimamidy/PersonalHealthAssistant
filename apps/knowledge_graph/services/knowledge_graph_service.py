"""
Knowledge Graph Service for Personal Health Assistant.

This service provides comprehensive medical knowledge graph functionality including:
- Neo4j graph database integration
- Qdrant vector database integration for embeddings
- Medical ontology integration (SNOMED CT, ICD-10, etc.)
- Semantic search and query capabilities
- Patient data integration and personalized insights
- Recommendation engine based on knowledge graph analysis
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4
import httpx
from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json

from common.utils.logging import get_logger
from common.config.settings import get_settings
from apps.knowledge_graph.models.knowledge_models import (
    EntityType, RelationshipType, ConfidenceLevel, EvidenceLevel, OntologySource,
    MedicalEntityCreate, MedicalEntityUpdate, MedicalEntityResponse,
    RelationshipCreate, RelationshipUpdate, RelationshipResponse,
    SemanticSearchQuery, PathQuery, RecommendationQuery, KnowledgeGraphResponse,
    MedicalRecommendation, OntologyImportRequest, OntologyImportResponse,
    KnowledgeGraphStats, HealthInsight
)

logger = get_logger(__name__)
settings = get_settings()


class KnowledgeGraphService:
    """Knowledge Graph Service for medical knowledge management."""
    
    def __init__(self):
        """Initialize the Knowledge Graph Service."""
        self.neo4j_driver = None
        self.qdrant_client = None
        self.initialized = False
        self.settings = get_settings()
        
    async def initialize(self):
        """Initialize database connections and services."""
        try:
            logger.info("Initializing Knowledge Graph Service...")
            
            # Initialize Neo4j connection
            if hasattr(self.settings, 'NEO4J_URI'):
                self.neo4j_driver = AsyncGraphDatabase.driver(
                    self.settings.NEO4J_URI,
                    auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
                )
                logger.info("Neo4j connection established")
            
            # Initialize Qdrant connection
            if hasattr(self.settings, 'QDRANT_URL'):
                self.qdrant_client = AsyncQdrantClient(
                    url=self.settings.QDRANT_URL,
                    timeout=30.0
                )
                logger.info("Qdrant connection established")
            
            # Initialize collections if they don't exist
            await self._initialize_collections()
            
            self.initialized = True
            logger.info("Knowledge Graph Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Graph Service: {e}")
            raise
    
    async def _initialize_collections(self):
        """Initialize Qdrant collections for embeddings."""
        try:
            if not self.qdrant_client:
                return
                
            # Check if collections exist, create if not
            collections = await self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            # Medical entities collection
            if "medical_entities" not in collection_names:
                await self.qdrant_client.create_collection(
                    collection_name="medical_entities",
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info("Created medical_entities collection")
            
            # Medical relationships collection
            if "medical_relationships" not in collection_names:
                await self.qdrant_client.create_collection(
                    collection_name="medical_relationships",
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info("Created medical_relationships collection")
                
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.neo4j_driver:
                await self.neo4j_driver.close()
                logger.info("Neo4j connection closed")
            
            if self.qdrant_client:
                await self.qdrant_client.close()
                logger.info("Qdrant connection closed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the knowledge graph service."""
        try:
            health_status = {
                "service": "knowledge-graph-service",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "neo4j": "unavailable",
                "qdrant": "unavailable",
                "version": "1.0.0"
            }
            
            # Check Neo4j
            if self.neo4j_driver:
                try:
                    async with self.neo4j_driver.session() as session:
                        result = await session.run("RETURN 1 as health_check")
                        record = await result.single()
                        if record and record["health_check"] == 1:
                            health_status["neo4j"] = "healthy"
                except Exception as e:
                    logger.error(f"Neo4j health check failed: {e}")
                    health_status["neo4j"] = "unhealthy"
            
            # Check Qdrant
            if self.qdrant_client:
                try:
                    collections = await self.qdrant_client.get_collections()
                    health_status["qdrant"] = "healthy"
                    health_status["collections"] = len(collections.collections)
                except Exception as e:
                    logger.error(f"Qdrant health check failed: {e}")
                    health_status["qdrant"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "service": "knowledge-graph-service",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_medical_entity(self, entity_data: MedicalEntityCreate) -> MedicalEntityResponse:
        """Create a new medical entity in the knowledge graph."""
        try:
            entity_id = uuid4()
            created_at = datetime.utcnow()
            
            # Create entity in Neo4j
            if self.neo4j_driver:
                async with self.neo4j_driver.session() as session:
                    query = """
                    CREATE (e:MedicalEntity {
                        id: $id,
                        name: $name,
                        display_name: $display_name,
                        entity_type: $entity_type,
                        description: $description,
                        synonyms: $synonyms,
                        ontology_ids: $ontology_ids,
                        confidence: $confidence,
                        evidence_level: $evidence_level,
                        source: $source,
                        metadata: $metadata,
                        created_at: $created_at,
                        updated_at: $updated_at
                    })
                    RETURN e
                    """
                    
                    # Convert empty dictionaries to None for Neo4j compatibility
                    metadata = json.dumps(entity_data.metadata) if entity_data.metadata else None
                    synonyms = entity_data.synonyms if entity_data.synonyms else []
                    ontology_ids = json.dumps(entity_data.ontology_ids) if entity_data.ontology_ids else None
                    
                    result = await session.run(query, {
                        "id": str(entity_id),
                        "name": entity_data.name,
                        "display_name": entity_data.display_name,
                        "entity_type": entity_data.entity_type.value,
                        "description": entity_data.description,
                        "synonyms": synonyms,
                        "ontology_ids": ontology_ids,
                        "confidence": entity_data.confidence.value,
                        "evidence_level": entity_data.evidence_level.value,
                        "source": entity_data.source.value,
                        "metadata": metadata,
                        "created_at": created_at.isoformat(),
                        "updated_at": created_at.isoformat()
                    })
                    
                    # Consume the result to ensure the transaction is committed
                    record = await result.single()
                    if not record:
                        raise Exception("Failed to create medical entity")
            
            # Create embedding in Qdrant
            if self.qdrant_client:
                # Generate embedding (placeholder - would use actual embedding model)
                embedding = [0.0] * 768  # Placeholder embedding
                
                await self.qdrant_client.upsert(
                    collection_name="medical_entities",
                    points=[
                        PointStruct(
                            id=str(entity_id),
                            vector=embedding,
                            payload={
                                "name": entity_data.name,
                                "entity_type": entity_data.entity_type.value,
                                "description": entity_data.description,
                                "synonyms": entity_data.synonyms,
                                "created_at": created_at.isoformat()
                            }
                        )
                    ]
                )
            
            # Create response
            response = MedicalEntityResponse(
                id=entity_id,
                name=entity_data.name,
                display_name=entity_data.display_name,
                entity_type=entity_data.entity_type,
                description=entity_data.description,
                synonyms=entity_data.synonyms,
                ontology_ids=entity_data.ontology_ids,
                confidence=entity_data.confidence,
                evidence_level=entity_data.evidence_level,
                source=entity_data.source,
                metadata=entity_data.metadata,
                created_at=created_at,
                updated_at=created_at,
                relationship_count=0
            )
            
            logger.info(f"Created medical entity: {entity_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create medical entity: {e}")
            raise
    
    async def get_medical_entity(self, entity_id: UUID) -> Optional[MedicalEntityResponse]:
        """Get a medical entity by ID."""
        try:
            if not self.neo4j_driver:
                return None
            
            async with self.neo4j_driver.session() as session:
                query = """
                MATCH (e:MedicalEntity {id: $id})
                RETURN e
                """
                
                result = await session.run(query, {"id": str(entity_id)})
                record = await result.single()
                
                if not record:
                    return None
                
                entity_data = record["e"]
                
                # Get relationship count
                rel_query = """
                MATCH (e:MedicalEntity {id: $id})-[r]-()
                RETURN count(r) as relationship_count
                """
                rel_result = await session.run(rel_query, {"id": str(entity_id)})
                rel_record = await rel_result.single()
                relationship_count = rel_record["relationship_count"] if rel_record else 0
                
                return MedicalEntityResponse(
                    id=UUID(entity_data["id"]),
                    name=entity_data["name"],
                    display_name=entity_data.get("display_name", entity_data["name"]),
                    entity_type=EntityType(entity_data["entity_type"]),
                    description=entity_data.get("description"),
                    synonyms=entity_data.get("synonyms", []),
                    ontology_ids=json.loads(entity_data["ontology_ids"]) if entity_data.get("ontology_ids") else {},
                    confidence=ConfidenceLevel(entity_data["confidence"]),
                    evidence_level=EvidenceLevel(entity_data["evidence_level"]),
                    source=OntologySource(entity_data["source"]),
                    metadata=json.loads(entity_data["metadata"]) if entity_data.get("metadata") else {},
                    created_at=entity_data.get("created_at"),
                    updated_at=entity_data.get("updated_at"),
                    relationship_count=0
                )
                
        except Exception as e:
            logger.error(f"Failed to get medical entity {entity_id}: {e}")
            return None
    
    async def create_relationship(self, relationship_data: RelationshipCreate) -> RelationshipResponse:
        """Create a new relationship in the knowledge graph."""
        try:
            relationship_id = uuid4()
            created_at = datetime.utcnow()
            
            if not self.neo4j_driver:
                raise Exception("Neo4j driver not initialized")
            
            async with self.neo4j_driver.session() as session:
                query = """
                MATCH (source:MedicalEntity {id: $source_id})
                MATCH (target:MedicalEntity {id: $target_id})
                CREATE (source)-[r:RELATES_TO {
                    id: $relationship_id,
                    relationship_type: $relationship_type,
                    confidence: $confidence,
                    evidence_level: $evidence_level,
                    weight: $weight,
                    metadata: $metadata,
                    source: $source,
                    created_at: $created_at,
                    updated_at: $updated_at
                }]->(target)
                RETURN r, source, target
                """
                
                # Convert metadata to JSON string for Neo4j compatibility
                metadata = json.dumps(relationship_data.metadata) if relationship_data.metadata else None
                
                result = await session.run(query, {
                    "source_id": str(relationship_data.source_entity_id),
                    "target_id": str(relationship_data.target_entity_id),
                    "relationship_id": str(relationship_id),
                    "relationship_type": relationship_data.relationship_type.value,
                    "confidence": relationship_data.confidence.value,
                    "evidence_level": relationship_data.evidence_level.value,
                    "weight": relationship_data.weight,
                    "metadata": metadata,
                    "source": relationship_data.source.value,
                    "created_at": created_at.isoformat(),
                    "updated_at": created_at.isoformat()
                })
                
                record = await result.single()
                if not record:
                    raise Exception("Failed to create relationship")
                
                # Get source and target entities
                source_entity = await self.get_medical_entity(relationship_data.source_entity_id)
                target_entity = await self.get_medical_entity(relationship_data.target_entity_id)
                
                if not source_entity or not target_entity:
                    raise Exception("Source or target entity not found")
                
                response = RelationshipResponse(
                    id=relationship_id,
                    source_entity_id=relationship_data.source_entity_id,
                    target_entity_id=relationship_data.target_entity_id,
                    relationship_type=relationship_data.relationship_type,
                    confidence=relationship_data.confidence,
                    evidence_level=relationship_data.evidence_level,
                    weight=relationship_data.weight,
                    metadata=relationship_data.metadata,
                    source=relationship_data.source,
                    source_entity=source_entity,
                    target_entity=target_entity,
                    created_at=created_at,
                    updated_at=created_at
                )
                
                logger.info(f"Created relationship: {relationship_id}")
                return response
                
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            raise
    
    async def semantic_search(self, query: SemanticSearchQuery) -> KnowledgeGraphResponse:
        """Perform semantic search in the knowledge graph."""
        try:
            start_time = datetime.utcnow()
            query_id = uuid4()
            
            results = []
            
            # Search in Qdrant for semantic similarity
            if self.qdrant_client:
                # Generate query embedding (placeholder)
                query_embedding = [0.0] * 768  # Placeholder
                
                search_result = await self.qdrant_client.search(
                    collection_name="medical_entities",
                    query_vector=query_embedding,
                    limit=query.limit,
                    with_payload=True
                )
                
                # Get full entity details from Neo4j
                if self.neo4j_driver:
                    for point in search_result:
                        entity_id = UUID(point.id)
                        entity = await self.get_medical_entity(entity_id)
                        if entity:
                            results.append({
                                "entity": entity.dict(),
                                "similarity_score": point.score,
                                "payload": point.payload
                            })
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = KnowledgeGraphResponse(
                query_id=query_id,
                query_type="semantic_search",
                results=results,
                total_count=len(results),
                execution_time=execution_time,
                metadata={
                    "query_text": query.query_text,
                    "entity_types": [et.value for et in query.entity_types] if query.entity_types else None,
                    "confidence_threshold": query.confidence_threshold.value if query.confidence_threshold else None
                }
            )
            
            logger.info(f"Semantic search completed: {len(results)} results")
            return response
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise
    
    async def find_paths(self, query: PathQuery) -> KnowledgeGraphResponse:
        """Find paths between entities in the knowledge graph."""
        try:
            start_time = datetime.utcnow()
            query_id = uuid4()
            
            if not self.neo4j_driver:
                raise Exception("Neo4j driver not initialized")
            
            async with self.neo4j_driver.session() as session:
                # Build Cypher query for path finding
                cypher_query = f"""
                MATCH path = (source:MedicalEntity {{id: $source_id}})-[r:RELATES_TO*1..{query.max_path_length}]-(target:MedicalEntity {{id: $target_id}})
                RETURN path, length(path) as path_length
                ORDER BY path_length
                LIMIT $limit
                """
                
                result = await session.run(cypher_query, {
                    "source_id": str(query.source_entity_id),
                    "target_id": str(query.target_entity_id),
                    "limit": query.limit
                })
                
                paths = []
                async for record in result:
                    path_data = record["path"]
                    path_length = record["path_length"]
                    
                    # Extract path information
                    path_info = {
                        "path_length": path_length,
                        "nodes": [],
                        "relationships": []
                    }
                    
                    # Process path nodes and relationships
                    for i, node in enumerate(path_data.nodes):
                        path_info["nodes"].append({
                            "id": node["id"],
                            "name": node["name"],
                            "entity_type": node["entity_type"]
                        })
                    
                    for i, rel in enumerate(path_data.relationships):
                        path_info["relationships"].append({
                            "id": rel["id"],
                            "relationship_type": rel["relationship_type"],
                            "confidence": rel["confidence"],
                            "weight": rel["weight"]
                        })
                    
                    paths.append(path_info)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                response = KnowledgeGraphResponse(
                    query_id=query_id,
                    query_type="path_query",
                    results=paths,
                    total_count=len(paths),
                    execution_time=execution_time,
                    metadata={
                        "source_entity_id": str(query.source_entity_id),
                        "target_entity_id": str(query.target_entity_id),
                        "max_path_length": query.max_path_length
                    }
                )
                
                logger.info(f"Path query completed: {len(paths)} paths found")
                return response
                
        except Exception as e:
            logger.error(f"Path query failed: {e}")
            raise
    
    async def generate_recommendations(self, query: RecommendationQuery) -> List[MedicalRecommendation]:
        """Generate medical recommendations based on knowledge graph analysis."""
        try:
            recommendations = []
            
            # Placeholder implementation - would integrate with patient data
            # and perform sophisticated graph analysis
            
            # Example recommendation
            recommendation = MedicalRecommendation(
                id=uuid4(),
                patient_id=query.patient_id,
                recommendation_type=query.recommendation_type,
                title="Health Monitoring Recommendation",
                description="Based on your health profile, we recommend regular monitoring of key metrics.",
                confidence=ConfidenceLevel.MEDIUM,
                evidence_level=EvidenceLevel.LEVEL_C,
                reasoning=[
                    "Analysis of your health patterns",
                    "Comparison with similar patient profiles",
                    "Evidence-based clinical guidelines"
                ],
                related_entities=[],
                actions=[
                    "Schedule regular health check-ups",
                    "Monitor blood pressure daily",
                    "Track physical activity levels"
                ],
                created_at=datetime.utcnow()
            )
            
            recommendations.append(recommendation)
            
            logger.info(f"Generated {len(recommendations)} recommendations for patient {query.patient_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            raise
    
    async def get_statistics(self) -> KnowledgeGraphStats:
        """Get knowledge graph statistics."""
        try:
            stats = KnowledgeGraphStats(
                total_entities=0,
                total_relationships=0,
                entities_by_type={},
                relationships_by_type={},
                ontology_coverage={},
                last_updated=datetime.utcnow(),
                graph_density=0.0,
                average_degree=0.0
            )
            
            if not self.neo4j_driver:
                return stats
            
            async with self.neo4j_driver.session() as session:
                # Get total entities
                entity_query = "MATCH (e:MedicalEntity) RETURN count(e) as total"
                result = await session.run(entity_query)
                record = await result.single()
                stats.total_entities = record["total"] if record else 0
                
                # Get total relationships
                rel_query = "MATCH ()-[r:RELATES_TO]->() RETURN count(r) as total"
                result = await session.run(rel_query)
                record = await result.single()
                stats.total_relationships = record["total"] if record else 0
                
                # Get entities by type
                type_query = """
                MATCH (e:MedicalEntity)
                RETURN e.entity_type as type, count(e) as count
                """
                result = await session.run(type_query)
                async for record in result:
                    stats.entities_by_type[record["type"]] = record["count"]
                
                # Get relationships by type
                rel_type_query = """
                MATCH ()-[r:RELATES_TO]->()
                RETURN r.relationship_type as type, count(r) as count
                """
                result = await session.run(rel_type_query)
                async for record in result:
                    stats.relationships_by_type[record["type"]] = record["count"]
                
                # Calculate graph density and average degree
                if stats.total_entities > 1:
                    max_edges = stats.total_entities * (stats.total_entities - 1)
                    stats.graph_density = stats.total_relationships / max_edges if max_edges > 0 else 0.0
                    stats.average_degree = (2 * stats.total_relationships) / stats.total_entities if stats.total_entities > 0 else 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    async def search_medical_entities(self, query: str, entity_type: Optional[EntityType] = None, limit: int = 10) -> List[MedicalEntityResponse]:
        """Search for medical entities by name or description."""
        try:
            if not self.neo4j_driver:
                raise Exception("Neo4j connection not available")
            
            async with self.neo4j_driver.session() as session:
                if entity_type:
                    result = await session.run(
                        """
                        MATCH (e:MedicalEntity)
                        WHERE e.entity_type = $entity_type 
                        AND (e.name CONTAINS $search_query OR e.display_name CONTAINS $search_query OR e.description CONTAINS $search_query)
                        RETURN e
                        LIMIT $limit
                        """,
                        entity_type=entity_type.value,
                        search_query=query,
                        limit=limit
                    )
                else:
                    result = await session.run(
                        """
                        MATCH (e:MedicalEntity)
                        WHERE e.name CONTAINS $search_query OR e.display_name CONTAINS $search_query OR e.description CONTAINS $search_query
                        RETURN e
                        LIMIT $limit
                        """,
                        search_query=query,
                        limit=limit
                    )
                
                entities = []
                async for record in result:
                    entity_data = record["e"]
                    entities.append(MedicalEntityResponse(
                        id=UUID(entity_data["id"]),
                        name=entity_data["name"],
                        display_name=entity_data.get("display_name", entity_data["name"]),
                        entity_type=EntityType(entity_data["entity_type"]),
                        description=entity_data.get("description", ""),
                        synonyms=entity_data.get("synonyms", []),
                        ontology_ids=json.loads(entity_data["ontology_ids"]) if entity_data.get("ontology_ids") else {},
                        confidence=ConfidenceLevel(entity_data["confidence"]),
                        evidence_level=EvidenceLevel(entity_data["evidence_level"]),
                        source=OntologySource(entity_data["source"]),
                        metadata=json.loads(entity_data["metadata"]) if entity_data.get("metadata") else {},
                        created_at=entity_data.get("created_at"),
                        updated_at=entity_data.get("updated_at"),
                        relationship_count=0
                    ))
                
                return entities
                
        except Exception as e:
            logger.error(f"Error searching medical entities: {e}")
            raise
    
    async def list_medical_entities(self, entity_type: Optional[EntityType] = None, ontology_source: Optional[OntologySource] = None, limit: int = 100) -> List[MedicalEntityResponse]:
        """List medical entities with optional filtering."""
        try:
            if not self.neo4j_driver:
                raise Exception("Neo4j connection not available")
            
            async with self.neo4j_driver.session() as session:
                query = "MATCH (e:MedicalEntity)"
                params = {}
                
                if entity_type or ontology_source:
                    query += " WHERE "
                    conditions = []
                    
                    if entity_type:
                        conditions.append("e.entity_type = $entity_type")
                        params["entity_type"] = entity_type.value
                    
                    if ontology_source:
                        conditions.append("e.ontology_source = $ontology_source")
                        params["ontology_source"] = ontology_source.value
                    
                    query += " AND ".join(conditions)
                
                query += " RETURN e LIMIT $limit"
                params["limit"] = limit
                
                result = await session.run(query, params)
                
                entities = []
                async for record in result:
                    entity_data = record["e"]
                    entities.append(MedicalEntityResponse(
                        id=UUID(entity_data["id"]),
                        name=entity_data["name"],
                        display_name=entity_data.get("display_name", entity_data["name"]),
                        entity_type=EntityType(entity_data["entity_type"]),
                        description=entity_data.get("description", ""),
                        synonyms=entity_data.get("synonyms", []),
                        ontology_ids=json.loads(entity_data["ontology_ids"]) if entity_data.get("ontology_ids") else {},
                        confidence=ConfidenceLevel(entity_data["confidence"]),
                        evidence_level=EvidenceLevel(entity_data["evidence_level"]),
                        source=OntologySource(entity_data["source"]),
                        metadata=json.loads(entity_data["metadata"]) if entity_data.get("metadata") else {},
                        created_at=entity_data.get("created_at"),
                        updated_at=entity_data.get("updated_at"),
                        relationship_count=0
                    ))
                
                return entities
                
        except Exception as e:
            logger.error(f"Error listing medical entities: {e}")
            raise
    
    async def list_relationships(self, relationship_type: Optional[RelationshipType] = None, limit: int = 100) -> List[RelationshipResponse]:
        """List relationships with optional filtering."""
        try:
            if not self.neo4j_driver:
                raise Exception("Neo4j connection not available")
            
            async with self.neo4j_driver.session() as session:
                query = "MATCH (source:MedicalEntity)-[r:RELATES_TO]->(target:MedicalEntity)"
                params = {}
                
                if relationship_type:
                    query += " WHERE r.relationship_type = $relationship_type"
                    params["relationship_type"] = relationship_type.value
                
                query += " RETURN source, r, target LIMIT $limit"
                params["limit"] = limit
                
                result = await session.run(query, params)
                
                relationships = []
                async for record in result:
                    source_data = record["source"]
                    target_data = record["target"]
                    rel_data = record["r"]
                    
                    relationships.append(RelationshipResponse(
                        id=rel_data["id"],
                        source_entity_id=source_data["id"],
                        target_entity_id=target_data["id"],
                        relationship_type=RelationshipType(rel_data["relationship_type"]),
                        confidence_level=ConfidenceLevel(rel_data["confidence_level"]),
                        evidence_level=EvidenceLevel(rel_data["evidence_level"]),
                        metadata=rel_data.get("metadata", {}),
                        created_at=rel_data.get("created_at"),
                        updated_at=rel_data.get("updated_at")
                    ))
                
                return relationships
                
        except Exception as e:
            logger.error(f"Error listing relationships: {e}")
            raise
    
    async def update_medical_entity(self, entity_id: UUID, update_data: Dict[str, Any]) -> MedicalEntityResponse:
        """Update a medical entity."""
        try:
            if not self.neo4j_driver:
                raise Exception("Neo4j connection not available")
            
            async with self.neo4j_driver.session() as session:
                # Build update query dynamically
                set_clauses = []
                params = {"entity_id": str(entity_id)}
                
                for key, value in update_data.items():
                    if key in ["name", "display_name", "description", "metadata"]:
                        set_clauses.append(f"e.{key} = ${key}")
                        params[key] = value
                
                if not set_clauses:
                    raise ValueError("No valid fields to update")
                
                query = f"""
                MATCH (e:MedicalEntity {{id: $entity_id}})
                SET {', '.join(set_clauses)}, e.updated_at = datetime()
                RETURN e
                """
                
                result = await session.run(query, params)
                record = await result.single()
                
                if not record:
                    raise Exception(f"Entity with id {entity_id} not found")
                
                entity_data = record["e"]
                return MedicalEntityResponse(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    display_name=entity_data["display_name"],
                    entity_type=EntityType(entity_data["entity_type"]),
                    description=entity_data.get("description", ""),
                    ontology_source=OntologySource(entity_data["ontology_source"]),
                    ontology_id=entity_data.get("ontology_id"),
                    confidence_level=ConfidenceLevel(entity_data["confidence_level"]),
                    evidence_level=EvidenceLevel(entity_data["evidence_level"]),
                    metadata=entity_data.get("metadata", {}),
                    created_at=entity_data.get("created_at"),
                    updated_at=entity_data.get("updated_at")
                )
                
        except Exception as e:
            logger.error(f"Error updating medical entity: {e}")
            raise
    
    async def delete_medical_entity(self, entity_id: UUID) -> bool:
        """Delete a medical entity and its relationships."""
        try:
            if not self.neo4j_driver:
                raise Exception("Neo4j connection not available")
            
            async with self.neo4j_driver.session() as session:
                # Delete relationships first
                await session.run(
                    """
                    MATCH (e:MedicalEntity {id: $entity_id})-[r:RELATES_TO]-()
                    DELETE r
                    """,
                    entity_id=str(entity_id)
                )
                
                # Delete the entity
                result = await session.run(
                    """
                    MATCH (e:MedicalEntity {id: $entity_id})
                    DELETE e
                    RETURN count(e) as deleted
                    """,
                    entity_id=str(entity_id)
                )
                
                record = await result.single()
                return record["deleted"] > 0
                
        except Exception as e:
            logger.error(f"Error deleting medical entity: {e}")
            raise
    
    async def create_entity_embedding(self, entity_id: UUID) -> bool:
        """Create embedding for a medical entity."""
        try:
            if not self.qdrant_client:
                raise Exception("Qdrant connection not available")
            
            # Get entity data
            entity = await self.get_medical_entity(entity_id)
            if not entity:
                raise Exception(f"Entity with id {entity_id} not found")
            
            # Create embedding text
            embedding_text = f"{entity.display_name} {entity.description}"
            
            # Generate embedding (simplified - in production, use proper embedding model)
            # For now, we'll create a dummy embedding
            import numpy as np
            embedding = np.random.rand(768).tolist()
            
            # Store in Qdrant
            await self.qdrant_client.upsert(
                collection_name="medical_entities",
                points=[
                    PointStruct(
                        id=str(entity_id),
                        vector=embedding,
                        payload={
                            "entity_id": str(entity_id),
                            "name": entity.name,
                            "display_name": entity.display_name,
                            "entity_type": entity.entity_type.value,
                            "description": entity.description
                        }
                    )
                ]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating entity embedding: {e}")
            return False


# Global service instance
knowledge_graph_service: KnowledgeGraphService = None


async def get_knowledge_graph_service() -> KnowledgeGraphService:
    """Get the global knowledge graph service instance."""
    global knowledge_graph_service
    if knowledge_graph_service is None:
        knowledge_graph_service = KnowledgeGraphService()
        await knowledge_graph_service.initialize()
    return knowledge_graph_service 