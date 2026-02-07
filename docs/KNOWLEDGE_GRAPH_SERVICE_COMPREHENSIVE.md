# Knowledge Graph Service - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Data Models](#data-models)
5. [API Endpoints](#api-endpoints)
6. [Integration Features](#integration-features)
7. [Deployment](#deployment)
8. [Usage Examples](#usage-examples)
9. [Monitoring & Analytics](#monitoring--analytics)
10. [Troubleshooting](#troubleshooting)

## Overview

The Knowledge Graph Service is a comprehensive medical knowledge management system designed for the Personal Health Assistant platform. It provides advanced capabilities for storing, querying, and analyzing medical entities and their relationships using graph database technology.

### Key Features
- **Medical Entity Management**: Store and manage medical conditions, symptoms, medications, treatments, procedures, lab tests, vital signs, and risk factors
- **Relationship Management**: Establish and query relationships between medical entities
- **Semantic Search**: AI-powered search using vector embeddings
- **Graph Analytics**: Analyze entity relationships and patterns
- **Evidence-based Recommendations**: Generate medical recommendations based on knowledge graph data
- **Multi-service Integration**: Seamless integration with other microservices

### Service Statistics
- **Total Entities**: 218
- **Total Relationships**: 115
- **Entity Types**: 8 (Condition, Symptom, Medication, Treatment, Procedure, Lab Test, Vital Sign, Risk Factor)
- **Graph Density**: 0.002431
- **Average Degree**: 1.06

## Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Graph Service                   │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Application Layer                                  │
│  ├── REST API Endpoints                                     │
│  ├── Authentication & Authorization                         │
│  ├── Request Validation                                     │
│  └── Error Handling                                         │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer                                       │
│  ├── Entity Management Service                              │
│  ├── Relationship Management Service                        │
│  ├── Search Service                                         │
│  └── Analytics Service                                      │
├─────────────────────────────────────────────────────────────┤
│  Data Access Layer                                          │
│  ├── Neo4j Graph Database                                   │
│  ├── Qdrant Vector Database                                 │
│  └── Redis Cache                                            │
└─────────────────────────────────────────────────────────────┘
```

### Database Architecture
- **Neo4j**: Primary graph database for storing entities and relationships
- **Qdrant**: Vector database for semantic search capabilities
- **Redis**: Caching layer for improved performance

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary programming language
- **FastAPI**: Modern web framework for building APIs
- **Neo4j**: Graph database for entity and relationship storage
- **Qdrant**: Vector database for semantic search
- **Redis**: In-memory caching
- **Docker**: Containerization
- **Traefik**: Reverse proxy and load balancer

### Dependencies
```python
# Core Dependencies
fastapi==0.104.1
uvicorn==0.24.0
neo4j==5.14.1
qdrant-client==1.7.0
redis==5.0.1
httpx==0.25.2
pydantic==2.5.0
python-multipart==0.0.6

# AI/ML Dependencies
sentence-transformers==2.2.2
huggingface-hub==0.19.4
numpy==1.24.3
scikit-learn==1.3.2

# Utilities
python-jose==3.3.0
passlib==1.7.4
python-dotenv==1.0.0
structlog==23.2.0
```

## Data Models

### Medical Entity Model
```python
class MedicalEntity(BaseModel):
    id: UUID
    name: str
    display_name: str
    entity_type: EntityType
    description: str
    synonyms: List[str]
    ontology_ids: Dict[str, str]
    confidence: ConfidenceLevel
    evidence_level: EvidenceLevel
    source: OntologySource
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    relationship_count: int
```

### Relationship Model
```python
class Relationship(BaseModel):
    id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: RelationshipType
    confidence: float
    evidence_level: EvidenceLevel
    metadata: Dict[str, Any]
    created_at: datetime
```

### Entity Types
- **CONDITION**: Medical conditions and diseases
- **SYMPTOM**: Patient symptoms and signs
- **MEDICATION**: Drugs and pharmaceutical products
- **TREATMENT**: Medical treatments and therapies
- **PROCEDURE**: Medical procedures and interventions
- **LAB_TEST**: Laboratory tests and diagnostics
- **VITAL_SIGN**: Patient vital signs
- **RISK_FACTOR**: Health risk factors

### Relationship Types
- **MANIFESTS_AS**: Condition manifests as symptom
- **TREATED_BY**: Condition treated by treatment/medication
- **RISK_FACTOR_FOR**: Risk factor for condition
- **INTERACTS_WITH**: Medication interacts with other medication
- **COMPLICATES**: Condition complicates other condition
- **MONITORED_BY**: Condition monitored by lab test

## API Endpoints

### Health & Status
```
GET /health
```
**Description**: Health check endpoint
**Response**: Service status, database connectivity, version information

### Analytics
```
GET /api/v1/knowledge-graph/statistics
```
**Description**: Get comprehensive knowledge graph statistics
**Response**: Entity counts, relationship counts, graph metrics

### Entity Management

#### List Entities
```
GET /api/v1/knowledge-graph/entities
```
**Parameters**:
- `entity_type` (optional): Filter by entity type
- `source` (optional): Filter by ontology source
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

#### Get Entity by ID
```
GET /api/v1/knowledge-graph/entities/{entity_id}
```
**Parameters**:
- `entity_id` (required): Entity UUID

#### Create Entity
```
POST /api/v1/knowledge-graph/entities
```
**Request Body**:
```json
{
  "name": "string",
  "display_name": "string",
  "entity_type": "condition",
  "description": "string",
  "synonyms": ["string"],
  "ontology_ids": {"string": "string"},
  "confidence": "high",
  "evidence_level": "level_a",
  "source": "icd_10",
  "metadata": {"string": "any"}
}
```

#### Update Entity
```
PUT /api/v1/knowledge-graph/entities/{entity_id}
```
**Parameters**:
- `entity_id` (required): Entity UUID

#### Delete Entity
```
DELETE /api/v1/knowledge-graph/entities/{entity_id}
```
**Parameters**:
- `entity_id` (required): Entity UUID

### Search Endpoints

#### Quick Search
```
GET /api/v1/knowledge-graph/search/quick
```
**Parameters**:
- `q` (required): Search query
- `entity_type` (optional): Filter by entity type
- `limit` (optional): Maximum number of results (default: 10)

#### Semantic Search
```
POST /api/v1/knowledge-graph/search/semantic
```
**Request Body**:
```json
{
  "query_type": "semantic_search",
  "query_text": "string",
  "limit": 10
}
```

#### Path Finding
```
POST /api/v1/knowledge-graph/search/paths
```
**Request Body**:
```json
{
  "source_entity_id": "uuid",
  "target_entity_id": "uuid",
  "max_paths": 5
}
```

### Relationship Management

#### List Relationships
```
GET /api/v1/knowledge-graph/relationships
```
**Parameters**:
- `relationship_type` (optional): Filter by relationship type
- `source_entity_id` (optional): Filter by source entity
- `target_entity_id` (optional): Filter by target entity
- `limit` (optional): Maximum number of results (default: 50)

#### Create Relationship
```
POST /api/v1/knowledge-graph/relationships
```
**Request Body**:
```json
{
  "source_entity_id": "uuid",
  "target_entity_id": "uuid",
  "relationship_type": "treated_by",
  "confidence": 0.95,
  "evidence_level": "level_a",
  "metadata": {"string": "any"}
}
```

### Recommendations

#### Patient Recommendations
```
GET /api/v1/knowledge-graph/recommendations/patient/{patient_id}
```
**Parameters**:
- `patient_id` (required): Patient UUID
- `recommendation_type` (optional): Filter by recommendation type
- `limit` (optional): Maximum number of results (default: 10)

## Integration Features

### Medical Records Service Integration

#### Enrich Lab Results
```
POST /api/v1/medical-records/lab-results/{lab_result_id}/enrich-with-knowledge-graph
```
**Description**: Enrich lab results with knowledge graph entities and medical recommendations

#### Validate Medical Codes
```
POST /api/v1/medical-records/lab-results/validate-medical-codes
```
**Description**: Validate medical codes against the knowledge graph

### AI Insights Service Integration

#### Enrich Insights
```
POST /api/v1/ai-insights/insights/enrich-with-knowledge-graph
```
**Description**: Enrich insight text with knowledge graph entities and medical context

#### Generate Evidence-based Recommendations
```
POST /api/v1/ai-insights/insights/generate-evidence-based-recommendations
```
**Description**: Generate evidence-based recommendations using knowledge graph

#### Validate Medical Entities
```
POST /api/v1/ai-insights/insights/validate-medical-entities
```
**Description**: Validate medical entities against the knowledge graph

#### Get Knowledge Graph Statistics
```
GET /api/v1/ai-insights/insights/knowledge-graph-stats
```
**Description**: Get knowledge graph statistics for insights generation

#### Search Medical Entities
```
POST /api/v1/ai-insights/insights/search-medical-entities
```
**Description**: Search for medical entities in the knowledge graph

### Health Tracking Service Integration

#### Enrich Health Metrics
```
POST /api/v1/health-tracking/analytics/enrich-metrics
```
**Description**: Enrich health metrics with knowledge graph entities

#### Generate Evidence-based Health Recommendations
```
POST /api/v1/health-tracking/analytics/evidence-based-recommendations
```
**Description**: Generate evidence-based health recommendations

#### Validate Health Entities
```
POST /api/v1/health-tracking/analytics/validate-health-entities
```
**Description**: Validate health-related entities against the knowledge graph

## Deployment

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  knowledge-graph:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379
    depends_on:
      - neo4j
      - qdrant
      - redis

  neo4j:
    image: neo4j:5.14
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  qdrant_data:
```

### Traefik Configuration
```yaml
http:
  routers:
    knowledge-graph:
      rule: "Host(`knowledge-graph.localhost`)"
      service: knowledge-graph
      tls: {}

  services:
    knowledge-graph:
      loadBalancer:
        servers:
          - url: "http://knowledge-graph:8000"
```

## Usage Examples

### Python Client Usage

#### Basic Client
```python
from common.clients.knowledge_graph_client import KnowledgeGraphClient

async def main():
    async with KnowledgeGraphClient() as client:
        # Get statistics
        stats = await client.get_statistics()
        print(f"Total entities: {stats['total_entities']}")
        
        # Search entities
        results = await client.search_entities("diabetes", entity_type="condition")
        for entity in results:
            print(f"Found: {entity['display_name']}")
        
        # Get recommendations
        recommendations = await client.get_recommendations(patient_id, limit=10)
        for rec in recommendations:
            print(f"Recommendation: {rec['title']}")

asyncio.run(main())
```

#### Entity Management
```python
async def manage_entities():
    async with KnowledgeGraphClient() as client:
        # Create entity
        entity_data = {
            "name": "DIABETES_MELLITUS_TYPE_2",
            "display_name": "Diabetes Mellitus Type 2",
            "entity_type": "condition",
            "description": "A chronic metabolic disorder",
            "confidence": "high",
            "evidence_level": "level_a",
            "source": "icd_10"
        }
        
        entity = await client.create_entity(entity_data)
        print(f"Created entity: {entity['id']}")
        
        # Get entity
        entity = await client.get_entity(entity['id'])
        print(f"Entity: {entity['display_name']}")
        
        # Update entity
        update_data = {"description": "Updated description"}
        updated_entity = await client.update_entity(entity['id'], update_data)
        
        # Delete entity
        await client.delete_entity(entity['id'])
```

#### Search Operations
```python
async def search_operations():
    async with KnowledgeGraphClient() as client:
        # Quick search
        results = await client.search_entities("hypertension", limit=5)
        
        # Semantic search
        semantic_results = await client.semantic_search("high blood pressure", limit=10)
        
        # Find paths
        paths = await client.find_paths(source_entity_id, target_entity_id, max_paths=3)
```

### Integration Examples

#### Medical Records Integration
```python
from apps.medical_records.services.service_integration import ServiceIntegrationManager

async def enrich_medical_record():
    integration_manager = ServiceIntegrationManager()
    
    # Enrich lab result
    enrichment = await integration_manager.enrich_medical_record_with_knowledge_graph(
        "Patient shows elevated glucose levels consistent with diabetes"
    )
    
    print(f"Found {enrichment['entity_count']} entities")
    for entity in enrichment['enriched_entities']:
        print(f"- {entity['display_name']} ({entity['entity_type']})")
    
    # Validate medical codes
    codes = [
        {"code": "E11", "system": "icd_10"},
        {"code": "44054006", "system": "snomed_ct"}
    ]
    
    validation = await integration_manager.validate_medical_codes(codes)
    print(f"Valid codes: {validation['valid_count']}")
```

#### AI Insights Integration
```python
from apps.ai_insights.services.insight_service import InsightService

async def enrich_insights():
    service = InsightService()
    
    # Enrich insight
    enriched = await service.enrich_insight_with_knowledge_graph(
        "Patient exhibits symptoms of diabetes including frequent urination and increased thirst"
    )
    
    print(f"Enriched with {enriched['enrichment_metadata']['entities_found']} entities")
    
    # Generate recommendations
    recommendations = await service.generate_evidence_based_recommendations(
        patient_conditions=["diabetes"],
        patient_medications=["metformin"],
        patient_symptoms=["frequent urination"]
    )
    
    print(f"Generated {len(recommendations['treatments'])} treatment recommendations")
```

## Monitoring & Analytics

### Health Monitoring
```python
# Health check
response = await client.health_check()
print(f"Service status: {response['status']}")
print(f"Neo4j: {response['neo4j']}")
print(f"Qdrant: {response['qdrant']}")
```

### Performance Metrics
```python
# Get statistics
stats = await client.get_statistics()
print(f"Graph density: {stats['graph_density']}")
print(f"Average degree: {stats['average_degree']}")
print(f"Total entities: {stats['total_entities']}")
print(f"Total relationships: {stats['total_relationships']}")
```

### Analytics Dashboard
```bash
# Run analytics
python scripts/knowledge_graph_analytics.py

# Run dashboard
python scripts/knowledge_graph_dashboard.py

# Generate documentation
python scripts/generate_api_documentation.py
```

## Troubleshooting

### Common Issues

#### Connection Issues
```python
# Check service connectivity
try:
    response = await client.health_check()
    print("Service is healthy")
except Exception as e:
    print(f"Connection failed: {e}")
```

#### Database Issues
```python
# Check Neo4j connectivity
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
try:
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"Neo4j entities: {count}")
finally:
    driver.close()
```

#### Search Issues
```python
# Check Qdrant connectivity
from qdrant_client import QdrantClient

client = QdrantClient("localhost", port=6333)
try:
    collections = client.get_collections()
    print(f"Qdrant collections: {len(collections.collections)}")
except Exception as e:
    print(f"Qdrant connection failed: {e}")
```

### Error Handling
```python
from common.exceptions import ServiceIntegrationError

try:
    result = await client.search_entities("query")
except ServiceIntegrationError as e:
    print(f"Service error: {e}")
except httpx.TimeoutException:
    print("Request timeout")
except httpx.ConnectError:
    print("Connection error")
```

### Logging
```python
import logging
from common.utils.logging import get_logger

logger = get_logger(__name__)

logger.info("Starting knowledge graph operation")
try:
    result = await client.search_entities("diabetes")
    logger.info(f"Found {len(result)} entities")
except Exception as e:
    logger.error(f"Search failed: {e}")
```

## Configuration

### Environment Variables
```bash
# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379

# Service Configuration
KNOWLEDGE_GRAPH_SERVICE_URL=http://knowledge-graph.localhost
LOG_LEVEL=INFO
ENVIRONMENT=development

# Security Configuration
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Configuration Files
```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379"
    
    # Service settings
    knowledge_graph_service_url: str = "http://knowledge-graph.localhost"
    log_level: str = "INFO"
    environment: str = "development"
    
    class Config:
        env_file = ".env"
```

## Security

### Authentication
```python
# JWT Token validation
from common.middleware.auth import get_current_user

@app.get("/protected-endpoint")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
    return {"message": "Access granted", "user": current_user}
```

### Authorization
```python
# Role-based access control
def require_role(required_role: str):
    def decorator(func):
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            if required_role not in current_user.get("roles", []):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### Rate Limiting
```python
# Rate limiting middleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/rate-limited")
@limiter.limit("100/minute")
async def rate_limited_endpoint(request: Request):
    return {"message": "Rate limited endpoint"}
```

## Performance Optimization

### Caching
```python
# Redis caching
import redis
import json

redis_client = redis.Redis.from_url(settings.redis_url)

async def get_cached_entities(entity_type: str):
    cache_key = f"entities:{entity_type}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    entities = await fetch_entities_from_db(entity_type)
    
    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(entities))
    return entities
```

### Database Optimization
```python
# Neo4j indexing
CREATE INDEX entity_name_index FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type_index FOR (e:Entity) ON (e.entity_type);
CREATE INDEX relationship_type_index FOR ()-[r:RELATIONSHIP]-() ON (r.type);
```

### Query Optimization
```python
# Optimized Cypher queries
# Instead of:
MATCH (e:Entity) WHERE e.name CONTAINS $query RETURN e

# Use:
MATCH (e:Entity) WHERE e.name CONTAINS $query 
WITH e ORDER BY e.confidence DESC 
LIMIT $limit RETURN e
```

## Testing

### Unit Tests
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_search_entities():
    with patch('common.clients.knowledge_graph_client.KnowledgeGraphClient') as mock_client:
        mock_client.return_value.search_entities = AsyncMock(return_value=[
            {"id": "1", "name": "Diabetes", "entity_type": "condition"}
        ])
        
        async with KnowledgeGraphClient() as client:
            results = await client.search_entities("diabetes")
            assert len(results) == 1
            assert results[0]["name"] == "Diabetes"
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_knowledge_graph_integration():
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        response = await client.get("http://knowledge-graph.localhost/health")
        assert response.status_code == 200
        
        # Test statistics endpoint
        response = await client.get("http://knowledge-graph.localhost/api/v1/knowledge-graph/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_entities" in data
```

### Load Testing
```python
import asyncio
import time

async def load_test():
    start_time = time.time()
    tasks = []
    
    async with KnowledgeGraphClient() as client:
        for i in range(100):
            task = client.search_entities(f"test_{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"Processed {len(results)} requests in {end_time - start_time:.2f} seconds")
```

## Maintenance

### Backup Procedures
```bash
# Neo4j backup
neo4j-admin backup --database=neo4j --backup-dir=/backups

# Qdrant backup
cp -r /qdrant/storage /backups/qdrant_$(date +%Y%m%d)

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backups/redis_$(date +%Y%m%d).rdb
```

### Monitoring Scripts
```python
# Health monitoring script
async def monitor_health():
    while True:
        try:
            async with KnowledgeGraphClient() as client:
                health = await client.health_check()
                if health["status"] != "healthy":
                    logger.error(f"Service unhealthy: {health}")
                else:
                    logger.info("Service healthy")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        await asyncio.sleep(60)  # Check every minute
```

### Data Maintenance
```python
# Clean up orphaned entities
async def cleanup_orphaned_entities():
    query = """
    MATCH (e:Entity)
    WHERE NOT (e)-[:RELATIONSHIP]-()
    DELETE e
    """
    await neo4j_session.run(query)

# Update entity confidence scores
async def update_confidence_scores():
    query = """
    MATCH (e:Entity)
    SET e.confidence = CASE
        WHEN e.evidence_level = 'level_a' THEN 'high'
        WHEN e.evidence_level = 'level_b' THEN 'medium'
        ELSE 'low'
    END
    """
    await neo4j_session.run(query)
```

---

**Generated on**: 2025-08-04  
**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2025-08-04
