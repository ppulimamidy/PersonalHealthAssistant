#!/usr/bin/env python3
"""
Knowledge Graph Service API Documentation Generator

Automatically generates comprehensive API documentation for the Knowledge Graph Service
and its integrations with other microservices in the Personal Health Assistant platform.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import yaml
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
SERVICES = {
    "knowledge_graph": "http://knowledge-graph.localhost",
    "medical_records": "http://medical-records.localhost",
    "auth": "http://auth.localhost",
    "ai_insights": "http://ai-insights.localhost",
    "health_tracking": "http://health-tracking.localhost"
}


class APIDocumentationGenerator:
    """Generate comprehensive API documentation for Knowledge Graph Service"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.documentation_data = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def discover_knowledge_graph_endpoints(self) -> Dict[str, Any]:
        """Discover and document Knowledge Graph Service endpoints"""
        endpoints = {
            "base_url": SERVICES["knowledge_graph"],
            "endpoints": [],
            "models": {},
            "examples": {}
        }
        
        # Define known endpoints based on the service structure
        kg_endpoints = [
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint",
                "category": "health"
            },
            {
                "path": "/api/v1/knowledge-graph/statistics",
                "method": "GET",
                "description": "Get knowledge graph statistics",
                "category": "analytics"
            },
            {
                "path": "/api/v1/knowledge-graph/entities",
                "method": "GET",
                "description": "List medical entities with optional filtering",
                "category": "entities",
                "parameters": [
                    {"name": "entity_type", "type": "string", "required": False, "description": "Filter by entity type"},
                    {"name": "source", "type": "string", "required": False, "description": "Filter by ontology source"},
                    {"name": "limit", "type": "integer", "required": False, "description": "Maximum number of results", "default": 50},
                    {"name": "offset", "type": "integer", "required": False, "description": "Number of results to skip", "default": 0}
                ]
            },
            {
                "path": "/api/v1/knowledge-graph/entities/{entity_id}",
                "method": "GET",
                "description": "Get a specific medical entity by ID",
                "category": "entities",
                "parameters": [
                    {"name": "entity_id", "type": "UUID", "required": True, "description": "Entity ID"}
                ]
            },
            {
                "path": "/api/v1/knowledge-graph/entities",
                "method": "POST",
                "description": "Create a new medical entity",
                "category": "entities",
                "request_body": {
                    "name": "string",
                    "display_name": "string",
                    "entity_type": "string",
                    "description": "string",
                    "synonyms": ["string"],
                    "ontology_ids": {"string": "string"},
                    "confidence": "string",
                    "evidence_level": "string",
                    "source": "string",
                    "metadata": {"string": "any"}
                }
            },
            {
                "path": "/api/v1/knowledge-graph/entities/{entity_id}",
                "method": "PUT",
                "description": "Update a medical entity",
                "category": "entities",
                "parameters": [
                    {"name": "entity_id", "type": "UUID", "required": True, "description": "Entity ID"}
                ]
            },
            {
                "path": "/api/v1/knowledge-graph/entities/{entity_id}",
                "method": "DELETE",
                "description": "Delete a medical entity",
                "category": "entities",
                "parameters": [
                    {"name": "entity_id", "type": "UUID", "required": True, "description": "Entity ID"}
                ]
            },
            {
                "path": "/api/v1/knowledge-graph/search/quick",
                "method": "GET",
                "description": "Quick search for medical entities",
                "category": "search",
                "parameters": [
                    {"name": "q", "type": "string", "required": True, "description": "Search query"},
                    {"name": "entity_type", "type": "string", "required": False, "description": "Filter by entity type"},
                    {"name": "limit", "type": "integer", "required": False, "description": "Maximum number of results", "default": 10}
                ]
            },
            {
                "path": "/api/v1/knowledge-graph/search/semantic",
                "method": "POST",
                "description": "Semantic search for medical entities",
                "category": "search",
                "request_body": {
                    "query_type": "string",
                    "query_text": "string",
                    "limit": "integer"
                }
            },
            {
                "path": "/api/v1/knowledge-graph/search/paths",
                "method": "POST",
                "description": "Find paths between entities",
                "category": "search",
                "request_body": {
                    "source_entity_id": "UUID",
                    "target_entity_id": "UUID",
                    "max_paths": "integer"
                }
            },
            {
                "path": "/api/v1/knowledge-graph/relationships",
                "method": "GET",
                "description": "List relationships with optional filtering",
                "category": "relationships",
                "parameters": [
                    {"name": "relationship_type", "type": "string", "required": False, "description": "Filter by relationship type"},
                    {"name": "source_entity_id", "type": "UUID", "required": False, "description": "Filter by source entity"},
                    {"name": "target_entity_id", "type": "UUID", "required": False, "description": "Filter by target entity"},
                    {"name": "limit", "type": "integer", "required": False, "description": "Maximum number of results", "default": 50}
                ]
            },
            {
                "path": "/api/v1/knowledge-graph/relationships",
                "method": "POST",
                "description": "Create a new relationship",
                "category": "relationships",
                "request_body": {
                    "source_entity_id": "UUID",
                    "target_entity_id": "UUID",
                    "relationship_type": "string",
                    "confidence": "float",
                    "evidence_level": "string",
                    "metadata": {"string": "any"}
                }
            },
            {
                "path": "/api/v1/knowledge-graph/recommendations/patient/{patient_id}",
                "method": "GET",
                "description": "Get personalized recommendations for a patient",
                "category": "recommendations",
                "parameters": [
                    {"name": "patient_id", "type": "UUID", "required": True, "description": "Patient ID"},
                    {"name": "recommendation_type", "type": "string", "required": False, "description": "Filter by recommendation type"},
                    {"name": "limit", "type": "integer", "required": False, "description": "Maximum number of results", "default": 10}
                ]
            }
        ]
        
        endpoints["endpoints"] = kg_endpoints
        
        # Add data models
        endpoints["models"] = {
            "MedicalEntity": {
                "id": "UUID",
                "name": "string",
                "display_name": "string",
                "entity_type": "string",
                "description": "string",
                "synonyms": ["string"],
                "ontology_ids": {"string": "string"},
                "confidence": "string",
                "evidence_level": "string",
                "source": "string",
                "metadata": {"string": "any"},
                "created_at": "datetime",
                "updated_at": "datetime",
                "relationship_count": "integer"
            },
            "Relationship": {
                "id": "UUID",
                "source_entity_id": "UUID",
                "target_entity_id": "UUID",
                "relationship_type": "string",
                "confidence": "float",
                "evidence_level": "string",
                "metadata": {"string": "any"},
                "created_at": "datetime"
            },
            "SearchResult": {
                "results": ["MedicalEntity"],
                "total_count": "integer",
                "query": "string",
                "search_time": "float"
            }
        }
        
        # Add example requests and responses
        endpoints["examples"] = {
            "create_entity": {
                "request": {
                    "name": "DIABETES_MELLITUS_TYPE_2",
                    "display_name": "Diabetes Mellitus Type 2",
                    "entity_type": "condition",
                    "description": "A chronic metabolic disorder characterized by high blood sugar",
                    "synonyms": ["Type 2 Diabetes", "T2DM"],
                    "ontology_ids": {"icd_10": "E11", "snomed_ct": "44054006"},
                    "confidence": "high",
                    "evidence_level": "level_a",
                    "source": "icd_10"
                },
                "response": {
                    "id": "e8f2ef83-2828-4d89-baac-cd452c088b55",
                    "name": "DIABETES_MELLITUS_TYPE_2",
                    "display_name": "Diabetes Mellitus Type 2",
                    "entity_type": "condition",
                    "description": "A chronic metabolic disorder characterized by high blood sugar",
                    "synonyms": ["Type 2 Diabetes", "T2DM"],
                    "ontology_ids": {"icd_10": "E11", "snomed_ct": "44054006"},
                    "confidence": "high",
                    "evidence_level": "level_a",
                    "source": "icd_10",
                    "created_at": "2025-08-04T20:48:37.123456",
                    "updated_at": "2025-08-04T20:48:37.123456",
                    "relationship_count": 0
                }
            },
            "search_entities": {
                "request": {
                    "q": "diabetes",
                    "entity_type": "condition",
                    "limit": 5
                },
                "response": {
                    "results": [
                        {
                            "id": "e8f2ef83-2828-4d89-baac-cd452c088b55",
                            "name": "DIABETES_MELLITUS_TYPE_2",
                            "display_name": "Diabetes Mellitus Type 2",
                            "entity_type": "condition",
                            "similarity_score": 0.95
                        }
                    ],
                    "total_count": 1,
                    "query": "diabetes",
                    "search_time": 0.023
                }
            }
        }
        
        return endpoints
    
    async def discover_integration_endpoints(self) -> Dict[str, Any]:
        """Discover and document integration endpoints"""
        integrations = {
            "medical_records": {
                "base_url": SERVICES["medical_records"],
                "endpoints": [
                    {
                        "path": "/api/v1/medical-records/lab-results/{lab_result_id}/enrich-with-knowledge-graph",
                        "method": "POST",
                        "description": "Enrich lab result with knowledge graph entities and medical recommendations",
                        "category": "enrichment"
                    },
                    {
                        "path": "/api/v1/medical-records/lab-results/validate-medical-codes",
                        "method": "POST",
                        "description": "Validate medical codes against the knowledge graph",
                        "category": "validation"
                    }
                ]
            },
            "ai_insights": {
                "base_url": SERVICES["ai_insights"],
                "endpoints": [
                    {
                        "path": "/api/v1/ai-insights/insights/enrich-with-knowledge-graph",
                        "method": "POST",
                        "description": "Enrich insight text with knowledge graph entities and medical context",
                        "category": "enrichment"
                    },
                    {
                        "path": "/api/v1/ai-insights/insights/generate-evidence-based-recommendations",
                        "method": "POST",
                        "description": "Generate evidence-based recommendations using knowledge graph",
                        "category": "recommendations"
                    },
                    {
                        "path": "/api/v1/ai-insights/insights/validate-medical-entities",
                        "method": "POST",
                        "description": "Validate medical entities against the knowledge graph",
                        "category": "validation"
                    },
                    {
                        "path": "/api/v1/ai-insights/insights/knowledge-graph-stats",
                        "method": "GET",
                        "description": "Get knowledge graph statistics for insights generation",
                        "category": "analytics"
                    },
                    {
                        "path": "/api/v1/ai-insights/insights/search-medical-entities",
                        "method": "POST",
                        "description": "Search for medical entities in the knowledge graph",
                        "category": "search"
                    }
                ]
            },
            "health_tracking": {
                "base_url": SERVICES["health_tracking"],
                "endpoints": [
                    {
                        "path": "/api/v1/health-tracking/analytics/enrich-metrics",
                        "method": "POST",
                        "description": "Enrich health metrics with knowledge graph entities",
                        "category": "enrichment"
                    },
                    {
                        "path": "/api/v1/health-tracking/analytics/evidence-based-recommendations",
                        "method": "POST",
                        "description": "Generate evidence-based health recommendations",
                        "category": "recommendations"
                    },
                    {
                        "path": "/api/v1/health-tracking/analytics/validate-health-entities",
                        "method": "POST",
                        "description": "Validate health-related entities against the knowledge graph",
                        "category": "validation"
                    }
                ]
            }
        }
        
        return integrations
    
    def generate_markdown_documentation(self, kg_endpoints: Dict[str, Any], integrations: Dict[str, Any]) -> str:
        """Generate comprehensive Markdown documentation"""
        
        markdown_template = """
# Knowledge Graph Service API Documentation

## Overview

The Knowledge Graph Service provides a comprehensive medical knowledge management system for the Personal Health Assistant platform. It stores and manages medical entities, relationships, and provides advanced search and recommendation capabilities.

**Base URL:** `{{ kg_endpoints.base_url }}`

**Version:** 1.0.0

## Table of Contents

- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
- [Integration Endpoints](#integration-endpoints)
- [Data Models](#data-models)
- [Examples](#examples)
- [Error Handling](#error-handling)

## Authentication

All API endpoints require authentication. Include the following header in your requests:

```
Authorization: Bearer <your_access_token>
```

## Core Endpoints

### Health Check

#### GET /health

Check the health status of the Knowledge Graph Service.

**Response:**
```json
{
  "service": "knowledge-graph-service",
  "status": "healthy",
  "timestamp": "2025-08-04T20:48:37.123456",
  "neo4j": "healthy",
  "qdrant": "healthy",
  "version": "1.0.0"
}
```

### Analytics

#### GET /api/v1/knowledge-graph/statistics

Get comprehensive statistics about the knowledge graph.

**Response:**
```json
{
  "total_entities": 218,
  "total_relationships": 115,
  "entities_by_type": {
    "condition": 32,
    "symptom": 32,
    "medication": 20,
    "treatment": 28,
    "procedure": 20,
    "lab_test": 28,
    "vital_sign": 28,
    "risk_factor": 30
  },
  "relationships_by_type": {
    "manifests_as": 30,
    "treated_by": 25,
    "risk_factor_for": 31,
    "interacts_with": 5,
    "complicates": 8,
    "monitored_by": 16
  },
  "graph_density": 0.002431,
  "average_degree": 1.06
}
```

### Entities

{% for endpoint in kg_endpoints.endpoints %}
{% if endpoint.category == "entities" %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}){% if param.required %} - Required{% endif %}{% if param.default %} - Default: {{ param.default }}{% endif %}: {{ param.description }}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
**Request Body:**
```json
{{ endpoint.request_body | tojson(indent=2) }}
```
{% endif %}

{% endif %}
{% endfor %}

### Search

{% for endpoint in kg_endpoints.endpoints %}
{% if endpoint.category == "search" %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}){% if param.required %} - Required{% endif %}{% if param.default %} - Default: {{ param.default }}{% endif %}: {{ param.description }}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
**Request Body:**
```json
{{ endpoint.request_body | tojson(indent=2) }}
```
{% endif %}

{% endif %}
{% endfor %}

### Relationships

{% for endpoint in kg_endpoints.endpoints %}
{% if endpoint.category == "relationships" %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}){% if param.required %} - Required{% endif %}{% if param.default %} - Default: {{ param.default }}{% endif %}: {{ param.description }}
{% endfor %}
{% endif %}

{% if endpoint.request_body %}
**Request Body:**
```json
{{ endpoint.request_body | tojson(indent=2) }}
```
{% endif %}

{% endif %}
{% endfor %}

### Recommendations

{% for endpoint in kg_endpoints.endpoints %}
{% if endpoint.category == "recommendations" %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}){% if param.required %} - Required{% endif %}{% if param.default %} - Default: {{ param.default }}{% endif %}: {{ param.description }}
{% endfor %}
{% endif %}

{% endif %}
{% endfor %}

## Integration Endpoints

### Medical Records Service

**Base URL:** `{{ integrations.medical_records.base_url }}`

{% for endpoint in integrations.medical_records.endpoints %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% endfor %}

### AI Insights Service

**Base URL:** `{{ integrations.ai_insights.base_url }}`

{% for endpoint in integrations.ai_insights.endpoints %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% endfor %}

### Health Tracking Service

**Base URL:** `{{ integrations.health_tracking.base_url }}`

{% for endpoint in integrations.health_tracking.endpoints %}

#### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

{% endfor %}

## Data Models

{% for model_name, model_fields in kg_endpoints.models.items() %}

### {{ model_name }}

| Field | Type | Description |
|-------|------|-------------|
{% for field_name, field_type in model_fields.items() %}
| `{{ field_name }}` | `{{ field_type }}` | - |
{% endfor %}

{% endfor %}

## Examples

{% for example_name, example_data in kg_endpoints.examples.items() %}

### {{ example_name | title }}

**Request:**
```json
{{ example_data.request | tojson(indent=2) }}
```

**Response:**
```json
{{ example_data.response | tojson(indent=2) }}
```

{% endfor %}

## Error Handling

The API uses standard HTTP status codes and returns error responses in the following format:

```json
{
  "error": "Error message",
  "status_code": 400,
  "timestamp": "2025-08-04T20:48:37.123456"
}
```

### Common Error Codes

- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Rate Limit:** 1000 requests per hour per API key
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Support

For support and questions, please contact the development team or refer to the internal documentation.

---

*Generated on: {{ generation_timestamp }}*
"""
        
        template = Template(markdown_template)
        return template.render(
            kg_endpoints=kg_endpoints,
            integrations=integrations,
            generation_timestamp=datetime.utcnow().isoformat()
        )
    
    def generate_openapi_spec(self, kg_endpoints: Dict[str, Any], integrations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Knowledge Graph Service API",
                "description": "Comprehensive medical knowledge management system for the Personal Health Assistant platform",
                "version": "1.0.0",
                "contact": {
                    "name": "Development Team",
                    "email": "dev@personalhealthassistant.com"
                }
            },
            "servers": [
                {
                    "url": kg_endpoints["base_url"],
                    "description": "Knowledge Graph Service"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "security": [
                {
                    "bearerAuth": []
                }
            ]
        }
        
        # Add paths for Knowledge Graph endpoints
        for endpoint in kg_endpoints["endpoints"]:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            openapi_spec["paths"][path][method] = {
                "summary": endpoint["description"],
                "tags": [endpoint["category"]],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{endpoint['category'].title()}Response"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request"
                    },
                    "401": {
                        "description": "Unauthorized"
                    },
                    "404": {
                        "description": "Not found"
                    },
                    "500": {
                        "description": "Internal server error"
                    }
                }
            }
            
            # Add parameters
            if "parameters" in endpoint:
                openapi_spec["paths"][path][method]["parameters"] = []
                for param in endpoint["parameters"]:
                    param_type = param["type"]
                    if isinstance(param_type, str):
                        schema_type = param_type.lower() if param_type.lower() in ["string", "integer", "boolean"] else "string"
                    else:
                        schema_type = "string"
                    
                    openapi_spec["paths"][path][method]["parameters"].append({
                        "name": param["name"],
                        "in": "path" if "{" in path and param["name"] in path else "query",
                        "required": param.get("required", False),
                        "schema": {
                            "type": schema_type
                        },
                        "description": param["description"]
                    })
            
            # Add request body
            if "request_body" in endpoint:
                openapi_spec["paths"][path][method]["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    key: {"type": "string"} if isinstance(value, str) else {"type": "array", "items": {"type": "string"}} if isinstance(value, list) else {"type": "object"}
                                    for key, value in endpoint["request_body"].items()
                                }
                            }
                        }
                    }
                }
        
        # Add schemas
        for model_name, model_fields in kg_endpoints["models"].items():
            openapi_spec["components"]["schemas"][model_name] = {
                "type": "object",
                "properties": {}
            }
            
            for field_name, field_type in model_fields.items():
                if isinstance(field_type, str):
                    schema_type = field_type.lower() if field_type.lower() in ["string", "integer", "boolean"] else "string"
                else:
                    schema_type = "string"
                
                openapi_spec["components"]["schemas"][model_name]["properties"][field_name] = {
                    "type": schema_type
                }
        
        return openapi_spec
    
    async def generate_documentation(self):
        """Generate comprehensive API documentation"""
        print("📚 Generating Knowledge Graph Service API Documentation...")
        
        # Discover endpoints
        kg_endpoints = await self.discover_knowledge_graph_endpoints()
        integrations = await self.discover_integration_endpoints()
        
        # Generate documentation
        markdown_doc = self.generate_markdown_documentation(kg_endpoints, integrations)
        openapi_spec = self.generate_openapi_spec(kg_endpoints, integrations)
        
        # Create documentation directory
        docs_dir = Path("docs/api")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Save documentation files
        with open(docs_dir / "knowledge_graph_api.md", "w") as f:
            f.write(markdown_doc)
        
        with open(docs_dir / "knowledge_graph_openapi.yaml", "w") as f:
            yaml.dump(openapi_spec, f, default_flow_style=False, sort_keys=False)
        
        with open(docs_dir / "knowledge_graph_openapi.json", "w") as f:
            json.dump(openapi_spec, f, indent=2)
        
        # Generate integration documentation
        integration_docs = {
            "knowledge_graph": kg_endpoints,
            "integrations": integrations,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
        with open(docs_dir / "integration_endpoints.json", "w") as f:
            json.dump(integration_docs, f, indent=2)
        
        print(f"✅ Documentation generated successfully!")
        print(f"📁 Files saved to: {docs_dir.absolute()}")
        print(f"   - knowledge_graph_api.md (Markdown documentation)")
        print(f"   - knowledge_graph_openapi.yaml (OpenAPI YAML)")
        print(f"   - knowledge_graph_openapi.json (OpenAPI JSON)")
        print(f"   - integration_endpoints.json (Integration endpoints)")
        
        return {
            "markdown": markdown_doc,
            "openapi": openapi_spec,
            "integrations": integrations
        }


async def main():
    """Main function"""
    async with APIDocumentationGenerator() as generator:
        await generator.generate_documentation()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Documentation generation stopped by user")
    except Exception as e:
        print(f"\n❌ Documentation generation error: {e}") 