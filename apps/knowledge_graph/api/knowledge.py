"""
Knowledge Graph API endpoints for Personal Health Assistant.

This module provides comprehensive API endpoints for:
- Medical entity management
- Relationship management
- Semantic search and queries
- Path finding
- Recommendations
- Statistics and analytics
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger

from apps.knowledge_graph.models.knowledge_models import (
    EntityType,
    RelationshipType,
    ConfidenceLevel,
    EvidenceLevel,
    OntologySource,
    MedicalEntityCreate,
    MedicalEntityUpdate,
    MedicalEntityResponse,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipResponse,
    SemanticSearchQuery,
    PathQuery,
    RecommendationQuery,
    KnowledgeGraphResponse,
    MedicalRecommendation,
    OntologyImportRequest,
    OntologyImportResponse,
    KnowledgeGraphStats,
    HealthInsight,
)
from apps.knowledge_graph.services.knowledge_graph_service import (
    KnowledgeGraphService,
    get_knowledge_graph_service,
)

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(
    current_user: dict = Depends(get_current_user),
) -> str:
    """Extract user ID from the authenticated user."""
    return current_user.get("id", current_user.get("sub", str(uuid.uuid4())))


# Health and Status Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for the Knowledge Graph Service."""
    try:
        service = await get_knowledge_graph_service()
        health_status = await service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {str(e)}",
        )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint for the Knowledge Graph Service."""
    try:
        service = await get_knowledge_graph_service()
        health_status = await service.health_check()

        if health_status["status"] == "healthy":
            return {"status": "ready", "service": "knowledge-graph-service"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready",
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}",
        )


# Medical Entity Management
@router.post("/entities", response_model=MedicalEntityResponse)
@rate_limit(requests_per_minute=60)
@security_headers
async def create_medical_entity(
    request: Request,
    entity_data: MedicalEntityCreate,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Create a new medical entity in the knowledge graph."""
    try:
        logger.info(f"Creating medical entity: {entity_data.name}")

        entity = await service.create_medical_entity(entity_data)
        logger.info(f"Successfully created medical entity: {entity.id}")

        return entity

    except Exception as e:
        logger.error(f"Failed to create medical entity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create medical entity: {str(e)}",
        )


@router.get("/entities/{entity_id}", response_model=MedicalEntityResponse)
@security_headers
async def get_medical_entity(
    entity_id: UUID,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Get a medical entity by ID."""
    try:
        entity = await service.get_medical_entity(entity_id)

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medical entity {entity_id} not found",
            )

        return entity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get medical entity {entity_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get medical entity: {str(e)}",
        )


@router.get("/entities", response_model=List[MedicalEntityResponse])
@security_headers
async def list_medical_entities(
    entity_type: Optional[EntityType] = Query(
        None, description="Filter by entity type"
    ),
    confidence: Optional[ConfidenceLevel] = Query(
        None, description="Filter by confidence level"
    ),
    source: Optional[OntologySource] = Query(
        None, description="Filter by ontology source"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of entities to return"),
    offset: int = Query(0, ge=0, description="Number of entities to skip"),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """List medical entities with optional filtering."""
    try:
        logger.info(
            f"Listing medical entities with filters: type={entity_type}, limit={limit}"
        )

        entities = await service.list_medical_entities(
            entity_type=entity_type, ontology_source=source, limit=limit
        )

        logger.info(f"Retrieved {len(entities)} medical entities")
        return entities

    except Exception as e:
        logger.error(f"Failed to list medical entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list medical entities: {str(e)}",
        )


# Relationship Management
@router.post("/relationships", response_model=RelationshipResponse)
@rate_limit(requests_per_minute=60)
@security_headers
async def create_relationship(
    request: Request,
    relationship_data: RelationshipCreate,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Create a new relationship in the knowledge graph."""
    try:
        logger.info(
            f"Creating relationship between {relationship_data.source_entity_id} and {relationship_data.target_entity_id}"
        )

        relationship = await service.create_relationship(relationship_data)
        logger.info(f"Successfully created relationship: {relationship.id}")

        return relationship

    except Exception as e:
        logger.error(f"Failed to create relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create relationship: {str(e)}",
        )


@router.get("/relationships/{relationship_id}", response_model=RelationshipResponse)
@security_headers
async def get_relationship(
    relationship_id: UUID,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Get a relationship by ID."""
    try:
        # Placeholder implementation
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Get relationship by ID not yet implemented",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get relationship {relationship_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get relationship: {str(e)}",
        )


# Search and Query Endpoints
@router.post("/search/semantic", response_model=KnowledgeGraphResponse)
@rate_limit(requests_per_minute=30)
@security_headers
async def semantic_search(
    request: Request,
    query: SemanticSearchQuery,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Perform semantic search in the knowledge graph."""
    try:
        logger.info(f"Performing semantic search: {query.query_text}")

        results = await service.semantic_search(query)
        logger.info(f"Semantic search completed: {results.total_count} results")

        return results

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}",
        )


@router.post("/search/paths", response_model=KnowledgeGraphResponse)
@rate_limit(requests_per_minute=30)
@security_headers
async def find_paths(
    request: Request,
    query: PathQuery,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Find paths between entities in the knowledge graph."""
    try:
        logger.info(
            f"Finding paths between {query.source_entity_id} and {query.target_entity_id}"
        )

        results = await service.find_paths(query)
        logger.info(f"Path search completed: {results.total_count} paths found")

        return results

    except Exception as e:
        logger.error(f"Path search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Path search failed: {str(e)}",
        )


# Recommendation Endpoints
@router.post("/recommendations", response_model=List[MedicalRecommendation])
@rate_limit(requests_per_minute=20)
@security_headers
async def generate_recommendations(
    request: Request,
    query: RecommendationQuery,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Generate medical recommendations based on knowledge graph analysis."""
    try:
        logger.info(f"Generating recommendations for patient {query.patient_id}")

        recommendations = await service.generate_recommendations(query)
        logger.info(f"Generated {len(recommendations)} recommendations")

        return recommendations

    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.get(
    "/recommendations/patient/{patient_id}", response_model=List[MedicalRecommendation]
)
@security_headers
async def get_patient_recommendations(
    patient_id: UUID,
    recommendation_type: Optional[str] = Query(
        None, description="Filter by recommendation type"
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Number of recommendations to return"
    ),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Get recommendations for a specific patient."""
    try:
        logger.info(f"Getting recommendations for patient {patient_id}")

        query = RecommendationQuery(
            query_type="recommendation",
            patient_id=patient_id,
            context={},
            recommendation_type=recommendation_type or "general",
            max_recommendations=limit,
        )

        recommendations = await service.generate_recommendations(query)
        logger.info(
            f"Retrieved {len(recommendations)} recommendations for patient {patient_id}"
        )

        return recommendations

    except Exception as e:
        logger.error(f"Failed to get patient recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient recommendations: {str(e)}",
        )


# Statistics and Analytics
@router.get("/statistics", response_model=KnowledgeGraphStats)
@security_headers
async def get_statistics(
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Get knowledge graph statistics."""
    try:
        logger.info("Getting knowledge graph statistics")

        stats = await service.get_statistics()
        logger.info(
            f"Retrieved statistics: {stats.total_entities} entities, {stats.total_relationships} relationships"
        )

        return stats

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


# Ontology Import
@router.post("/ontology/import", response_model=OntologyImportResponse)
@rate_limit(requests_per_minute=10)
@security_headers
async def import_ontology(
    request: Request,
    import_request: OntologyImportRequest,
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Import medical ontology data."""
    try:
        logger.info(f"Importing ontology: {import_request.ontology_source.value}")

        import_response = await service.import_ontology(import_request)

        logger.info(
            f"Ontology import completed: {import_response.entities_imported} entities, {import_response.relationships_imported} relationships"
        )

        return import_response

    except Exception as e:
        logger.error(f"Failed to import ontology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import ontology: {str(e)}",
        )


# Health Insights
@router.get("/insights/patient/{patient_id}", response_model=List[HealthInsight])
@security_headers
async def get_patient_insights(
    patient_id: UUID,
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    limit: int = Query(10, ge=1, le=50, description="Number of insights to return"),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Get health insights for a specific patient."""
    try:
        logger.info(f"Getting health insights for patient {patient_id}")

        insights = await service.get_patient_insights(
            patient_id=patient_id,
            insight_type=insight_type,
            limit=limit,
        )

        logger.info(f"Retrieved {len(insights)} insights for patient {patient_id}")

        return insights

    except Exception as e:
        logger.error(f"Failed to get patient insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient insights: {str(e)}",
        )


# Quick Search Endpoints
@router.get("/search/quick")
@security_headers
async def quick_search(
    q: str = Query(..., min_length=1, description="Search query"),
    entity_type: Optional[EntityType] = Query(
        None, description="Filter by entity type"
    ),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Quick search endpoint for simple queries."""
    try:
        logger.info(f"Quick search: {q}")

        # Convert to semantic search query
        query = SemanticSearchQuery(
            query_type="semantic_search",
            query_text=q,
            entity_types=[entity_type] if entity_type else None,
            limit=limit,
        )

        results = await service.semantic_search(query)

        # Simplify response for quick search
        simplified_results = []
        for result in results.results[:limit]:
            if "entity" in result:
                simplified_results.append(
                    {
                        "id": result["entity"]["id"],
                        "name": result["entity"]["name"],
                        "type": result["entity"]["entity_type"],
                        "description": result["entity"]["description"],
                        "similarity_score": result.get("similarity_score", 0.0),
                    }
                )

        return {
            "query": q,
            "results": simplified_results,
            "total_count": len(simplified_results),
            "execution_time": results.execution_time,
        }

    except Exception as e:
        logger.error(f"Quick search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick search failed: {str(e)}",
        )
