"""
Insights API
RESTful API endpoints for health insights management.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.insight_models import (
    InsightCreate, InsightUpdate, InsightResponse,
    InsightType, InsightSeverity, InsightStatus, InsightCategory
)
from ..services.insight_service import InsightService
from common.database import get_db
from common.middleware.auth import get_current_user
# Import User model if available, otherwise use a simple type
try:
    from apps.auth.models import User
except ImportError:
    # Create a simple User type for type hints when auth models are not available
    from typing import TypeVar
    User = TypeVar('User')

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/types")
async def get_insight_types():
    """
    Get available insight types.
    
    Returns:
        dict: Available insight types
    """
    return {
        "success": True,
        "data": {
            "insight_types": [insight_type.value for insight_type in InsightType],
            "categories": [category.value for category in InsightCategory],
            "severity_levels": [severity.value for severity in InsightSeverity],
            "statuses": [status.value for status in InsightStatus]
        }
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for insights service.
    
    Returns:
        dict: Health status
    """
    return {
        "service": "ai_insights",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.post("/generate", response_model=dict)
async def generate_insights(
    request: Request,
    patient_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate insights for a patient using AI agents.
    
    Args:
        patient_id: Patient ID
        data: Health data for analysis
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Generated insights and metadata
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        result = await service.generate_insights(patient_id, data, db)
        
        return {
            "success": True,
            "data": result,
            "message": f"Generated {result['metadata']['total_insights']} insights and {result['metadata']['total_patterns']} patterns"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/", response_model=List[InsightResponse])
async def get_insights(
    request: Request,
    patient_id: UUID,
    insight_type: Optional[InsightType] = Query(None, description="Filter by insight type"),
    category: Optional[InsightCategory] = Query(None, description="Filter by category"),
    severity: Optional[InsightSeverity] = Query(None, description="Filter by severity"),
    status: Optional[InsightStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get insights for a patient with optional filtering.
    
    Args:
        patient_id: Patient ID
        insight_type: Filter by insight type
        category: Filter by category
        severity: Filter by severity
        status: Filter by status
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[InsightResponse]: List of insights
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        insights = await service.get_insights(
            patient_id=patient_id,
            db=db,
            insight_type=insight_type,
            category=category,
            severity=severity,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight_by_id(
    request: Request,
    insight_id: UUID = Path(..., description="Insight ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    patient_id: UUID = Query(..., description="Patient ID")
):
    """
    Get a specific insight by ID.
    
    Args:
        insight_id: Insight ID
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        InsightResponse: Insight details
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        insight = await service.get_insight_by_id(insight_id, patient_id, db)
        
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        return insight
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insight: {str(e)}")


@router.post("/", response_model=InsightResponse)
async def create_insight(
    request: Request,
    insight_data: InsightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new insight.
    
    Args:
        insight_data: Insight creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        InsightResponse: Created insight
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(insight_data.patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        insight = await service.create_insight(insight_data, db)
        
        return insight
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create insight: {str(e)}")


@router.put("/{insight_id}", response_model=InsightResponse)
async def update_insight(
    request: Request,
    insight_id: UUID = Path(..., description="Insight ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    update_data: InsightUpdate = Body(..., description="Update data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing insight.
    
    Args:
        insight_id: Insight ID
        patient_id: Patient ID
        update_data: Update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        InsightResponse: Updated insight
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        insight = await service.update_insight(insight_id, patient_id, update_data, db)
        
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        return insight
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update insight: {str(e)}")


@router.delete("/{insight_id}")
async def delete_insight(
    request: Request,
    insight_id: UUID = Path(..., description="Insight ID"),
    patient_id: UUID = Query(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an insight (soft delete).
    
    Args:
        insight_id: Insight ID
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        deleted = await service.delete_insight(insight_id, patient_id, db)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        return {
            "success": True,
            "message": "Insight deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete insight: {str(e)}")


@router.get("/summary/{patient_id}")
async def get_insights_summary(
    request: Request,
    patient_id: UUID = Path(..., description="Patient ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics for patient insights.
    
    Args:
        patient_id: Patient ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Summary statistics
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        summary = await service.get_insights_summary(patient_id, db)
        
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights summary: {str(e)}")


@router.get("/search/{patient_id}")
async def search_insights(
    request: Request,
    patient_id: UUID = Path(..., description="Patient ID"),
    search_term: str = Query(..., description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search insights by title or description.
    
    Args:
        patient_id: Patient ID
        search_term: Search term
        limit: Maximum number of results
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[InsightResponse]: List of matching insights
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        insights = await service.search_insights(patient_id, search_term, db, limit)
        
        return {
            "success": True,
            "data": insights,
            "total_results": len(insights)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search insights: {str(e)}")


@router.get("/timeline/{patient_id}")
async def get_insights_timeline(
    request: Request,
    patient_id: UUID = Path(..., description="Patient ID"),
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get insights timeline for a patient within a date range.
    
    Args:
        patient_id: Patient ID
        start_date: Start date for timeline
        end_date: End date for timeline
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Timeline data with insights
    """
    try:
        # Verify user has access to patient data
        if str(current_user["id"]) != str(patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = InsightService()
        timeline = await service.get_insights_timeline(patient_id, start_date, end_date, db)
        
        return {
            "success": True,
            "data": timeline,
            "message": f"Retrieved timeline with {len(timeline)} insights"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights timeline: {str(e)}")


# Knowledge Graph Integration Endpoints
@router.post("/enrich-with-knowledge-graph")
async def enrich_insight_with_knowledge_graph(
    request: Request,
    insight_text: str = Body(..., description="Insight text to enrich"),
    insight_type: Optional[str] = Body(None, description="Type of insight for targeted enrichment"),
    current_user: User = Depends(get_current_user)
):
    """
    Enrich insight text with knowledge graph entities and medical context.
    
    Args:
        insight_text: The insight text to enrich
        insight_type: Type of insight for targeted enrichment
        current_user: Current authenticated user
        
    Returns:
        dict: Enriched insight with knowledge graph entities
    """
    try:
        service = InsightService()
        enriched_result = await service.enrich_insight_with_knowledge_graph(insight_text, insight_type)
        
        return {
            "success": True,
            "data": enriched_result,
            "message": f"Enriched insight with {enriched_result['enrichment_metadata']['entities_found']} entities"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enrich insight: {str(e)}")


@router.post("/generate-evidence-based-recommendations")
async def generate_evidence_based_recommendations(
    request: Request,
    patient_conditions: List[str] = Body(..., description="List of patient conditions"),
    patient_medications: List[str] = Body(..., description="List of patient medications"),
    patient_symptoms: List[str] = Body(..., description="List of patient symptoms"),
    current_user: User = Depends(get_current_user)
):
    """
    Generate evidence-based recommendations using knowledge graph.
    
    Args:
        patient_conditions: List of patient conditions
        patient_medications: List of patient medications
        patient_symptoms: List of patient symptoms
        current_user: Current authenticated user
        
    Returns:
        dict: Evidence-based recommendations
    """
    try:
        service = InsightService()
        recommendations = await service.generate_evidence_based_recommendations(
            patient_conditions, patient_medications, patient_symptoms
        )
        
        return {
            "success": True,
            "data": recommendations,
            "message": f"Generated {recommendations['metadata']['total_treatments']} treatment recommendations"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.post("/validate-medical-entities")
async def validate_medical_entities(
    request: Request,
    entities: List[dict] = Body(..., description="List of medical entities to validate"),
    current_user: User = Depends(get_current_user)
):
    """
    Validate medical entities against the knowledge graph.
    
    Args:
        entities: List of medical entities to validate
        current_user: Current authenticated user
        
    Returns:
        dict: Validation results
    """
    try:
        service = InsightService()
        validation_results = await service.validate_medical_entities(entities)
        
        return {
            "success": True,
            "data": validation_results,
            "message": f"Validated {validation_results['validation_summary']['total_entities']} entities"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate entities: {str(e)}")


@router.get("/knowledge-graph-stats")
async def get_knowledge_graph_statistics(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get knowledge graph statistics for insights generation.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Knowledge graph statistics
    """
    try:
        from common.clients.knowledge_graph_client import KnowledgeGraphClient
        
        async with KnowledgeGraphClient() as client:
            stats = await client.get_statistics()
            
        return {
            "success": True,
            "data": stats,
            "message": f"Knowledge graph has {stats['total_entities']} entities and {stats['total_relationships']} relationships"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get knowledge graph statistics: {str(e)}")


@router.post("/search-medical-entities")
async def search_medical_entities(
    request: Request,
    query: str = Body(..., description="Search query"),
    entity_type: Optional[str] = Body(None, description="Filter by entity type"),
    limit: int = Body(10, description="Maximum number of results"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for medical entities in the knowledge graph.
    
    Args:
        query: Search query
        entity_type: Filter by entity type
        limit: Maximum number of results
        current_user: Current authenticated user
        
    Returns:
        dict: Search results
    """
    try:
        from common.clients.knowledge_graph_client import KnowledgeGraphClient
        
        async with KnowledgeGraphClient() as client:
            results = await client.search_entities(query, entity_type, limit)
            
        return {
            "success": True,
            "data": {
                "query": query,
                "entity_type": entity_type,
                "results": results,
                "total_count": len(results)
            },
            "message": f"Found {len(results)} entities for query '{query}'"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search medical entities: {str(e)}") 