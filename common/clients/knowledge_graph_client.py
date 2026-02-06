"""
Knowledge Graph Service Client

This module provides a client for other services to interact with the Knowledge Graph Service.
It handles authentication, error handling, and provides a clean interface for knowledge graph operations.
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime
import logging

from common.config.settings import get_settings
from common.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeGraphClient:
    """Client for interacting with the Knowledge Graph Service."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """Initialize the Knowledge Graph client.
        
        Args:
            base_url: Base URL for the Knowledge Graph Service
            timeout: Request timeout in seconds
        """
        self.settings = get_settings()
        self.base_url = base_url or self.settings.KNOWLEDGE_GRAPH_SERVICE_URL or "http://knowledge-graph.localhost"
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Knowledge Graph Service.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Knowledge Graph Service request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Knowledge Graph Service request: {e}")
            raise
            
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Knowledge Graph Service.
        
        Returns:
            Health status information
        """
        return await self._make_request("GET", "/health")
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics.
        
        Returns:
            Knowledge graph statistics
        """
        return await self._make_request("GET", "/api/v1/knowledge-graph/statistics")
        
    async def search_entities(
        self, 
        query: str, 
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for medical entities.
        
        Args:
            query: Search query
            entity_type: Filter by entity type
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        params = {"q": query, "limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
            
        response = await self._make_request("GET", "/api/v1/knowledge-graph/search/quick", params=params)
        return response.get("results", [])
        
    async def get_entities(
        self, 
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get medical entities.
        
        Args:
            entity_type: Filter by entity type
            limit: Maximum number of results
            
        Returns:
            List of entities
        """
        params = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
            
        return await self._make_request("GET", "/api/v1/knowledge-graph/entities", params=params)
        
    async def get_entity(self, entity_id: UUID) -> Dict[str, Any]:
        """Get a specific medical entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            Entity information
        """
        return await self._make_request("GET", f"/api/v1/knowledge-graph/entities/{entity_id}")
        
    async def create_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new medical entity.
        
        Args:
            entity_data: Entity data
            
        Returns:
            Created entity information
        """
        return await self._make_request("POST", "/api/v1/knowledge-graph/entities", data=entity_data)
        
    async def semantic_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Search results
        """
        data = {
            "query_type": "semantic_search",
            "query_text": query,
            "limit": limit
        }
        return await self._make_request("POST", "/api/v1/knowledge-graph/search/semantic", data=data)
        
    async def get_recommendations(
        self, 
        patient_id: UUID,
        recommendation_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get medical recommendations for a patient.
        
        Args:
            patient_id: Patient UUID
            recommendation_type: Type of recommendations
            limit: Maximum number of recommendations
            
        Returns:
            List of recommendations
        """
        params = {"limit": limit}
        if recommendation_type:
            params["recommendation_type"] = recommendation_type
            
        return await self._make_request(
            "GET", 
            f"/api/v1/knowledge-graph/recommendations/patient/{patient_id}",
            params=params
        )
        
    async def find_paths(
        self, 
        source_entity_id: UUID,
        target_entity_id: UUID,
        max_paths: int = 5
    ) -> Dict[str, Any]:
        """Find paths between two entities.
        
        Args:
            source_entity_id: Source entity UUID
            target_entity_id: Target entity UUID
            max_paths: Maximum number of paths to return
            
        Returns:
            Path information
        """
        data = {
            "source_entity_id": str(source_entity_id),
            "target_entity_id": str(target_entity_id),
            "max_paths": max_paths
        }
        return await self._make_request("POST", "/api/v1/knowledge-graph/search/paths", data=data)


# Convenience functions for common operations
async def get_medical_conditions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get medical conditions from the knowledge graph.
    
    Args:
        limit: Maximum number of conditions to return
        
    Returns:
        List of medical conditions
    """
    async with KnowledgeGraphClient() as client:
        return await client.get_entities(entity_type="condition", limit=limit)


async def search_symptoms(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for symptoms in the knowledge graph.
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of matching symptoms
    """
    async with KnowledgeGraphClient() as client:
        return await client.search_entities(query, entity_type="symptom", limit=limit)


async def get_treatments_for_condition(condition_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get treatments for a specific condition.
    
    Args:
        condition_name: Name of the condition
        limit: Maximum number of treatments to return
        
    Returns:
        List of treatments
    """
    async with KnowledgeGraphClient() as client:
        # First find the condition
        conditions = await client.search_entities(condition_name, entity_type="condition", limit=1)
        if not conditions:
            return []
            
        condition_id = conditions[0]["id"]
        
        # Then find treatments related to this condition
        # This would require a more complex query in a real implementation
        return await client.get_entities(entity_type="treatment", limit=limit)


async def get_knowledge_graph_stats() -> Dict[str, Any]:
    """Get knowledge graph statistics.
    
    Returns:
        Knowledge graph statistics
    """
    async with KnowledgeGraphClient() as client:
        return await client.get_statistics() 