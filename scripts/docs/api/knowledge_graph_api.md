
# Knowledge Graph Service API Documentation

## Overview

The Knowledge Graph Service provides a comprehensive medical knowledge management system for the Personal Health Assistant platform. It stores and manages medical entities, relationships, and provides advanced search and recommendation capabilities.

**Base URL:** `http://knowledge-graph.localhost`

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








#### GET /api/v1/knowledge-graph/entities

List medical entities with optional filtering


**Parameters:**

- `entity_type` (string): Filter by entity type

- `source` (string): Filter by ontology source

- `limit` (integer) - Default: 50: Maximum number of results

- `offset` (integer): Number of results to skip









#### GET /api/v1/knowledge-graph/entities/{entity_id}

Get a specific medical entity by ID


**Parameters:**

- `entity_id` (UUID) - Required: Entity ID









#### POST /api/v1/knowledge-graph/entities

Create a new medical entity




**Request Body:**
```json
{
  "confidence": "string",
  "description": "string",
  "display_name": "string",
  "entity_type": "string",
  "evidence_level": "string",
  "metadata": {
    "string": "any"
  },
  "name": "string",
  "ontology_ids": {
    "string": "string"
  },
  "source": "string",
  "synonyms": [
    "string"
  ]
}
```






#### PUT /api/v1/knowledge-graph/entities/{entity_id}

Update a medical entity


**Parameters:**

- `entity_id` (UUID) - Required: Entity ID









#### DELETE /api/v1/knowledge-graph/entities/{entity_id}

Delete a medical entity


**Parameters:**

- `entity_id` (UUID) - Required: Entity ID




















### Search


















#### GET /api/v1/knowledge-graph/search/quick

Quick search for medical entities


**Parameters:**

- `q` (string) - Required: Search query

- `entity_type` (string): Filter by entity type

- `limit` (integer) - Default: 10: Maximum number of results









#### POST /api/v1/knowledge-graph/search/semantic

Semantic search for medical entities




**Request Body:**
```json
{
  "limit": "integer",
  "query_text": "string",
  "query_type": "string"
}
```






#### POST /api/v1/knowledge-graph/search/paths

Find paths between entities




**Request Body:**
```json
{
  "max_paths": "integer",
  "source_entity_id": "UUID",
  "target_entity_id": "UUID"
}
```











### Relationships
























#### GET /api/v1/knowledge-graph/relationships

List relationships with optional filtering


**Parameters:**

- `relationship_type` (string): Filter by relationship type

- `source_entity_id` (UUID): Filter by source entity

- `target_entity_id` (UUID): Filter by target entity

- `limit` (integer) - Default: 50: Maximum number of results









#### POST /api/v1/knowledge-graph/relationships

Create a new relationship




**Request Body:**
```json
{
  "confidence": "float",
  "evidence_level": "string",
  "metadata": {
    "string": "any"
  },
  "relationship_type": "string",
  "source_entity_id": "UUID",
  "target_entity_id": "UUID"
}
```







### Recommendations




























#### GET /api/v1/knowledge-graph/recommendations/patient/{patient_id}

Get personalized recommendations for a patient


**Parameters:**

- `patient_id` (UUID) - Required: Patient ID

- `recommendation_type` (string): Filter by recommendation type

- `limit` (integer) - Default: 10: Maximum number of results






## Integration Endpoints

### Medical Records Service

**Base URL:** `http://medical-records.localhost`



#### POST /api/v1/medical-records/lab-results/{lab_result_id}/enrich-with-knowledge-graph

Enrich lab result with knowledge graph entities and medical recommendations



#### POST /api/v1/medical-records/lab-results/validate-medical-codes

Validate medical codes against the knowledge graph



### AI Insights Service

**Base URL:** `http://ai-insights.localhost`



#### POST /api/v1/ai-insights/insights/enrich-with-knowledge-graph

Enrich insight text with knowledge graph entities and medical context



#### POST /api/v1/ai-insights/insights/generate-evidence-based-recommendations

Generate evidence-based recommendations using knowledge graph



#### POST /api/v1/ai-insights/insights/validate-medical-entities

Validate medical entities against the knowledge graph



#### GET /api/v1/ai-insights/insights/knowledge-graph-stats

Get knowledge graph statistics for insights generation



#### POST /api/v1/ai-insights/insights/search-medical-entities

Search for medical entities in the knowledge graph



### Health Tracking Service

**Base URL:** `http://health-tracking.localhost`



#### POST /api/v1/health-tracking/analytics/enrich-metrics

Enrich health metrics with knowledge graph entities



#### POST /api/v1/health-tracking/analytics/evidence-based-recommendations

Generate evidence-based health recommendations



#### POST /api/v1/health-tracking/analytics/validate-health-entities

Validate health-related entities against the knowledge graph



## Data Models



### MedicalEntity

| Field | Type | Description |
|-------|------|-------------|

| `id` | `UUID` | - |

| `name` | `string` | - |

| `display_name` | `string` | - |

| `entity_type` | `string` | - |

| `description` | `string` | - |

| `synonyms` | `['string']` | - |

| `ontology_ids` | `{'string': 'string'}` | - |

| `confidence` | `string` | - |

| `evidence_level` | `string` | - |

| `source` | `string` | - |

| `metadata` | `{'string': 'any'}` | - |

| `created_at` | `datetime` | - |

| `updated_at` | `datetime` | - |

| `relationship_count` | `integer` | - |




### Relationship

| Field | Type | Description |
|-------|------|-------------|

| `id` | `UUID` | - |

| `source_entity_id` | `UUID` | - |

| `target_entity_id` | `UUID` | - |

| `relationship_type` | `string` | - |

| `confidence` | `float` | - |

| `evidence_level` | `string` | - |

| `metadata` | `{'string': 'any'}` | - |

| `created_at` | `datetime` | - |




### SearchResult

| Field | Type | Description |
|-------|------|-------------|

| `results` | `['MedicalEntity']` | - |

| `total_count` | `integer` | - |

| `query` | `string` | - |

| `search_time` | `float` | - |




## Examples



### Create_entity

**Request:**
```json
{
  "confidence": "high",
  "description": "A chronic metabolic disorder characterized by high blood sugar",
  "display_name": "Diabetes Mellitus Type 2",
  "entity_type": "condition",
  "evidence_level": "level_a",
  "name": "DIABETES_MELLITUS_TYPE_2",
  "ontology_ids": {
    "icd_10": "E11",
    "snomed_ct": "44054006"
  },
  "source": "icd_10",
  "synonyms": [
    "Type 2 Diabetes",
    "T2DM"
  ]
}
```

**Response:**
```json
{
  "confidence": "high",
  "created_at": "2025-08-04T20:48:37.123456",
  "description": "A chronic metabolic disorder characterized by high blood sugar",
  "display_name": "Diabetes Mellitus Type 2",
  "entity_type": "condition",
  "evidence_level": "level_a",
  "id": "e8f2ef83-2828-4d89-baac-cd452c088b55",
  "name": "DIABETES_MELLITUS_TYPE_2",
  "ontology_ids": {
    "icd_10": "E11",
    "snomed_ct": "44054006"
  },
  "relationship_count": 0,
  "source": "icd_10",
  "synonyms": [
    "Type 2 Diabetes",
    "T2DM"
  ],
  "updated_at": "2025-08-04T20:48:37.123456"
}
```



### Search_entities

**Request:**
```json
{
  "entity_type": "condition",
  "limit": 5,
  "q": "diabetes"
}
```

**Response:**
```json
{
  "query": "diabetes",
  "results": [
    {
      "display_name": "Diabetes Mellitus Type 2",
      "entity_type": "condition",
      "id": "e8f2ef83-2828-4d89-baac-cd452c088b55",
      "name": "DIABETES_MELLITUS_TYPE_2",
      "similarity_score": 0.95
    }
  ],
  "search_time": 0.023,
  "total_count": 1
}
```



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

*Generated on: 2025-08-04T23:12:34.713460*