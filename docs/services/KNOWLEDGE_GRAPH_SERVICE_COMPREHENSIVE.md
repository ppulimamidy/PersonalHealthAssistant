# Knowledge Graph Service - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [API Endpoints](#api-endpoints)
6. [Data Models](#data-models)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Monitoring & Logging](#monitoring--logging)
11. [Troubleshooting](#troubleshooting)

## Overview

The Knowledge Graph Service provides a comprehensive medical knowledge graph that integrates medical ontologies, clinical guidelines, drug information, and patient data to enable advanced reasoning, semantic search, and intelligent recommendations. It serves as the central knowledge repository for the Personal Health Assistant platform.

### Key Responsibilities
- Medical knowledge graph construction and maintenance
- Semantic search and reasoning capabilities
- Integration of medical ontologies and databases
- Clinical decision support through knowledge reasoning
- Drug interaction and contraindication analysis
- Medical concept mapping and standardization
- Integration with AI Insights and Analytics services

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   Knowledge     │
│                 │    │   (Traefik)     │    │   Graph         │
│ - Web App       │───▶│                 │───▶│   Service       │
│ - Mobile App    │    │ - Rate Limiting │    │                 │
│ - Clinician App │    │ - SSL/TLS       │    │ - Graph DB      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Neo4j       │
                                              │                 │
                                              │ - Knowledge     │
                                              │   Graph         │
                                              │ - Medical       │
                                              │   Ontologies    │
                                              │ - Relationships │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Qdrant      │
                                              │                 │
                                              │ - Vector        │
                                              │   Database      │
                                              │ - Semantic      │
                                              │   Search        │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Graph Database**: Neo4j for knowledge graph storage
- **Vector Database**: Qdrant for semantic search and embeddings
- **Knowledge Processing**: RDF/OWL standards for medical ontologies
- **Semantic Search**: Vector embeddings and similarity search
- **Integration**: Multiple medical data sources and ontologies

## Features

### 1. Medical Knowledge Graph
- **Ontology Integration**: Integrate SNOMED CT, ICD-10, ICD-11, LOINC, RxNorm
- **Medical Concepts**: Comprehensive medical concept mapping
- **Relationships**: Complex medical relationships and hierarchies
- **Drug Information**: Drug interactions, contraindications, and pharmacology
- **Clinical Guidelines**: Evidence-based clinical guidelines
- **Disease Pathways**: Disease mechanisms and pathways

### 2. Semantic Search & Reasoning
- **Natural Language Search**: Search medical concepts using natural language
- **Semantic Similarity**: Find similar medical concepts and conditions
- **Graph Traversal**: Navigate medical knowledge through relationships
- **Inference Engine**: Reason about medical concepts and relationships
- **Query Optimization**: Optimize complex medical queries
- **Contextual Search**: Context-aware medical search

### 3. Clinical Decision Support
- **Diagnosis Support**: Support diagnostic reasoning
- **Treatment Recommendations**: Suggest evidence-based treatments
- **Drug Interactions**: Identify potential drug interactions
- **Contraindications**: Check for contraindications
- **Clinical Guidelines**: Apply clinical practice guidelines
- **Risk Assessment**: Assess clinical risks

### 4. Knowledge Integration
- **Multi-Source Integration**: Integrate multiple medical data sources
- **Data Harmonization**: Harmonize different medical coding systems
- **Quality Control**: Ensure data quality and consistency
- **Version Management**: Manage ontology and knowledge updates
- **Custom Extensions**: Support custom medical knowledge extensions
- **Real-time Updates**: Real-time knowledge graph updates

### 5. Advanced Analytics
- **Graph Analytics**: Analyze knowledge graph structure and patterns
- **Network Analysis**: Analyze medical concept networks
- **Trend Analysis**: Identify medical knowledge trends
- **Anomaly Detection**: Detect unusual medical patterns
- **Predictive Modeling**: Predict medical outcomes
- **Research Support**: Support medical research applications

### 6. API & Integration
- **RESTful API**: Comprehensive REST API for knowledge access
- **GraphQL Support**: GraphQL interface for complex queries
- **WebSocket Support**: Real-time knowledge updates
- **Service Integration**: Integrate with all platform services
- **External APIs**: Connect to external medical databases
- **Export Capabilities**: Export knowledge in various formats

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **Neo4j**: Graph database for knowledge storage
- **Qdrant**: Vector database for semantic search
- **Redis 7**: Caching and session management

### Knowledge Graph & Semantics
- **RDFLib**: RDF processing and manipulation
- **OWL-RL**: OWL reasoning and inference
- **SPARQL**: SPARQL query language support
- **NetworkX**: Graph analysis and algorithms
- **Sentence-Transformers**: Text embeddings for semantic search

### Medical Ontologies & Data
- **SNOMED CT**: Clinical terminology
- **ICD-10/ICD-11**: Disease classification
- **LOINC**: Laboratory observations
- **RxNorm**: Drug nomenclature
- **UMLS**: Unified Medical Language System
- **MESH**: Medical Subject Headings

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **httpx**: Async HTTP client
- **PyYAML**: Configuration management
- **python-dateutil**: Date and time utilities

## API Endpoints

### Knowledge Graph Queries

#### POST /api/v1/graph/query
Execute Cypher query on knowledge graph.

**Request Body:**
```json
{
  "query": "MATCH (d:Disease {name: 'Diabetes'})-[r:TREATS]->(t:Treatment) RETURN d, r, t",
  "parameters": {},
  "timeout": 30
}
```

**Response:**
```json
{
  "results": [
    {
      "d": {"name": "Diabetes", "type": "Disease"},
      "r": {"type": "TREATS"},
      "t": {"name": "Metformin", "type": "Treatment"}
    }
  ],
  "execution_time": 0.15
}
```

#### GET /api/v1/graph/concepts/{concept_id}
Get medical concept details.

#### GET /api/v1/graph/concepts/{concept_id}/relationships
Get concept relationships.

#### GET /api/v1/graph/concepts/{concept_id}/neighbors
Get neighboring concepts.

### Semantic Search

#### POST /api/v1/search/semantic
Perform semantic search.

**Request Body:**
```json
{
  "query": "diabetes treatment options",
  "limit": 10,
  "threshold": 0.7,
  "filters": {
    "concept_types": ["Treatment", "Drug"],
    "ontologies": ["SNOMED", "RxNorm"]
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "concept_id": "uuid",
      "name": "Metformin",
      "type": "Drug",
      "similarity_score": 0.95,
      "description": "Oral antidiabetic medication"
    }
  ],
  "total_results": 25
}
```

#### GET /api/v1/search/similar/{concept_id}
Find similar concepts.

#### POST /api/v1/search/advanced
Advanced semantic search with filters.

### Clinical Decision Support

#### POST /api/v1/clinical/diagnosis-support
Get diagnosis support.

**Request Body:**
```json
{
  "symptoms": ["fatigue", "weight_gain", "increased_thirst"],
  "patient_data": {
    "age": 45,
    "gender": "female",
    "medical_history": ["hypertension"]
  }
}
```

#### POST /api/v1/clinical/treatment-recommendations
Get treatment recommendations.

**Request Body:**
```json
{
  "diagnosis": "Type 2 Diabetes",
  "patient_data": {
    "age": 45,
    "comorbidities": ["hypertension"],
    "medications": ["lisinopril"]
  }
}
```

#### POST /api/v1/clinical/drug-interactions
Check drug interactions.

**Request Body:**
```json
{
  "medications": [
    {"drug": "Metformin", "dosage": "500mg"},
    {"drug": "Warfarin", "dosage": "5mg"}
  ]
}
```

### Knowledge Management

#### POST /api/v1/knowledge/concepts
Add new medical concept.

**Request Body:**
```json
{
  "name": "New Treatment",
  "type": "Treatment",
  "description": "Novel treatment approach",
  "properties": {
    "mechanism": "Novel mechanism",
    "indications": ["Condition A", "Condition B"]
  },
  "relationships": [
    {
      "target_concept": "uuid",
      "relationship_type": "TREATS"
    }
  ]
}
```

#### PUT /api/v1/knowledge/concepts/{concept_id}
Update medical concept.

#### DELETE /api/v1/knowledge/concepts/{concept_id}
Delete medical concept.

### Ontology Management

#### GET /api/v1/ontologies
Get available ontologies.

#### POST /api/v1/ontologies/import
Import ontology.

#### GET /api/v1/ontologies/{ontology_id}
Get ontology details.

#### POST /api/v1/ontologies/{ontology_id}/sync
Sync ontology updates.

### Analytics & Insights

#### GET /api/v1/analytics/graph-stats
Get knowledge graph statistics.

#### POST /api/v1/analytics/path-analysis
Analyze paths between concepts.

**Request Body:**
```json
{
  "source_concept": "uuid",
  "target_concept": "uuid",
  "max_path_length": 3,
  "path_types": ["TREATS", "CAUSES", "ASSOCIATED_WITH"]
}
```

#### GET /api/v1/analytics/centrality
Get concept centrality measures.

### Export & Integration

#### GET /api/v1/export/rdf
Export knowledge graph as RDF.

#### GET /api/v1/export/json
Export knowledge graph as JSON.

#### POST /api/v1/integration/webhook
Receive external knowledge updates.

## Data Models

### Medical Concept Model
```python
class MedicalConcept(Base):
    __tablename__ = "medical_concepts"
    __table_args__ = {'schema': 'knowledge_graph'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text)
    
    ontology_id = Column(String(100))
    external_id = Column(String(200))
    
    properties = Column(JSON, default=dict)
    embeddings = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Relationship Model
```python
class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = {'schema': 'knowledge_graph'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    source_concept_id = Column(UUID(as_uuid=True), ForeignKey("medical_concepts.id"), nullable=False)
    target_concept_id = Column(UUID(as_uuid=True), ForeignKey("medical_concepts.id"), nullable=False)
    
    relationship_type = Column(String(100), nullable=False)
    properties = Column(JSON, default=dict)
    
    confidence_score = Column(Float, default=1.0)
    evidence_level = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Ontology Model
```python
class Ontology(Base):
    __tablename__ = "ontologies"
    __table_args__ = {'schema': 'knowledge_graph'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(200), nullable=False)
    version = Column(String(50))
    description = Column(Text)
    
    source_url = Column(String(500))
    last_sync = Column(DateTime)
    
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Search Query Model
```python
class SearchQuery(Base):
    __tablename__ = "search_queries"
    __table_args__ = {'schema': 'knowledge_graph'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)
    
    filters = Column(JSON, default=dict)
    results_count = Column(Integer)
    
    execution_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=knowledge-graph-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
ANALYTICS_SERVICE_URL=http://analytics-service:8210

# Knowledge Graph Configuration
GRAPH_UPDATE_INTERVAL=3600  # 1 hour
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.7

# Ontology Configuration
ONTOLOGY_SOURCES={
  "SNOMED": "https://snomed.org",
  "ICD10": "https://icd.who.int",
  "LOINC": "https://loinc.org",
  "RxNorm": "https://www.nlm.nih.gov/research/umls/rxnorm"
}

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8008

CMD ["uvicorn", "apps.knowledge_graph.main:app", "--host", "0.0.0.0", "--port", "8008"]
```

### Docker Compose
```yaml
knowledge-graph-service:
  build:
    context: .
    dockerfile: apps/knowledge_graph/Dockerfile
  ports:
    - "8008:8008"
  environment:
    - NEO4J_URI=bolt://neo4j:7687
    - NEO4J_USER=neo4j
    - NEO4J_PASSWORD=password
    - QDRANT_URL=http://qdrant:6333
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
    - ANALYTICS_SERVICE_URL=http://analytics-service:8210
  depends_on:
    - neo4j
    - qdrant
    - redis
    - auth-service
    - ai-insights-service
    - analytics-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
    interval: 30s
    timeout: 10s
    retries: 3

neo4j:
  image: neo4j:5.0
  ports:
    - "7474:7474"
    - "7687:7687"
  environment:
    - NEO4J_AUTH=neo4j/password
    - NEO4J_PLUGINS=["apoc"]
  volumes:
    - neo4j_data:/data
    - neo4j_logs:/logs

qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
```

## Testing

### Unit Tests
```python
# tests/unit/test_knowledge_graph.py
import pytest
from fastapi.testclient import TestClient
from apps.knowledge_graph.main import app

client = TestClient(app)

def test_graph_query():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "query": "MATCH (n) RETURN count(n) as count",
        "parameters": {}
    }
    response = client.post("/api/v1/graph/query", json=data, headers=headers)
    assert response.status_code == 200
    assert "results" in response.json()

def test_semantic_search():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "query": "diabetes treatment",
        "limit": 5
    }
    response = client.post("/api/v1/search/semantic", json=data, headers=headers)
    assert response.status_code == 200
    assert "results" in response.json()
```

### Integration Tests
```python
# tests/integration/test_clinical_support.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_diagnosis_support():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        data = {
            "symptoms": ["fatigue", "weight_gain"],
            "patient_data": {"age": 45, "gender": "female"}
        }
        response = await ac.post("/api/v1/clinical/diagnosis-support", json=data)
        assert response.status_code == 200
        assert "suggestions" in response.json()
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "knowledge-graph-service",
        "version": "1.0.0",
        "neo4j": "connected",
        "qdrant": "connected",
        "redis": "connected"
    }
```

### Metrics
- **Graph Queries**: Number and performance of graph queries
- **Semantic Searches**: Search volume and accuracy
- **Knowledge Updates**: Ontology and knowledge updates
- **API Performance**: Response times and error rates
- **Storage Usage**: Neo4j and Qdrant storage usage

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/graph/query")
async def execute_query(query: GraphQuery, current_user: User = Depends(get_current_user)):
    logger.info(f"Graph query executed by user: {current_user.id}")
    # ... query execution logic
    logger.info(f"Query completed in {execution_time}s")
```

## Troubleshooting

### Common Issues

#### 1. Neo4j Connection Issues
**Symptoms**: Graph queries failing
**Solution**: Check Neo4j connectivity and authentication

#### 2. Qdrant Performance Issues
**Symptoms**: Slow semantic searches
**Solution**: Optimize vector database configuration

#### 3. Knowledge Graph Consistency
**Symptoms**: Inconsistent knowledge relationships
**Solution**: Validate ontology imports and relationships

#### 4. Memory Usage
**Symptoms**: High memory usage
**Solution**: Optimize graph queries and caching

### Performance Optimization
- **Query Optimization**: Optimize Cypher queries
- **Indexing Strategy**: Implement proper Neo4j indexes
- **Caching**: Cache frequently accessed knowledge
- **Vector Optimization**: Optimize Qdrant vector operations

### Security Considerations
1. **Access Control**: Implement role-based access to knowledge
2. **Data Validation**: Validate all knowledge updates
3. **Audit Logging**: Log all knowledge modifications
4. **Backup Strategy**: Regular knowledge graph backups
5. **Version Control**: Track knowledge graph versions

---

## Conclusion

The Knowledge Graph Service provides a comprehensive medical knowledge repository for the Personal Health Assistant platform. With advanced semantic search, clinical decision support, and knowledge reasoning capabilities, it enables intelligent healthcare applications and improved clinical outcomes.

For additional support or questions, please refer to the platform documentation or contact the development team. 