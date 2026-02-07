# Knowledge Graph Service

## Overview

The Knowledge Graph Service is a comprehensive medical knowledge management system for the Personal Health Assistant platform. It provides advanced graph-based analytics, semantic search, and medical recommendations using Neo4j graph database and Qdrant vector database.

## Features

### 🧠 **Medical Knowledge Graph**
- **Medical Entities**: Conditions, symptoms, treatments, medications, procedures, lab tests, vital signs, risk factors, body parts, organs, diseases, syndromes, allergies, contraindications, side effects, interactions, guidelines, and evidence
- **Relationship Mapping**: Complex medical relationships with confidence levels and evidence-based weighting
- **Ontology Integration**: Support for standard medical ontologies (SNOMED CT, ICD-10, ICD-11, LOINC, RxNorm, UMLS, MESH, DOID, HP, CHEBI)

### 🔍 **Advanced Search & Query**
- **Semantic Search**: Natural language search across medical concepts with vector embeddings
- **Path Finding**: Discover connections between medical entities
- **Graph Analytics**: Statistical analysis and insights from the knowledge graph
- **Quick Search**: Fast, simplified search interface

### 💡 **Intelligent Recommendations**
- **Personalized Recommendations**: Patient-specific medical recommendations based on health profile
- **Risk Assessment**: Identify health risks and provide preventive recommendations
- **Treatment Suggestions**: Evidence-based treatment recommendations
- **Health Insights**: Generate actionable health insights from patient data

### 🔗 **Integration Capabilities**
- **Patient Data Integration**: Connect patient health data with medical knowledge
- **Real-time Updates**: Dynamic knowledge graph updates as new data arrives
- **Multi-service Integration**: Seamless integration with other Personal Health Assistant services

## Architecture

### Technology Stack
- **Graph Database**: Neo4j 5.15.0 with APOC procedures
- **Vector Database**: Qdrant for semantic embeddings
- **API Framework**: FastAPI with async/await support
- **Data Models**: Pydantic with RDF/OWL standards compliance
- **Authentication**: JWT-based authentication with role-based access control
- **Monitoring**: Prometheus metrics and structured logging

### Service Structure
```
apps/knowledge_graph/
├── api/                    # API endpoints
│   └── knowledge.py       # Knowledge graph API routes
├── models/                # Data models
│   └── knowledge_models.py # Pydantic models for entities and relationships
├── services/              # Business logic
│   └── knowledge_graph_service.py # Core service implementation
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── README.md           # This file
```

## API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /ready` - Service readiness check
- `GET /info` - Service information

### Medical Entity Management
- `POST /api/v1/knowledge-graph/entities` - Create medical entity
- `GET /api/v1/knowledge-graph/entities/{entity_id}` - Get entity by ID
- `GET /api/v1/knowledge-graph/entities` - List entities with filtering

### Relationship Management
- `POST /api/v1/knowledge-graph/relationships` - Create relationship
- `GET /api/v1/knowledge-graph/relationships/{relationship_id}` - Get relationship by ID

### Search & Query
- `POST /api/v1/knowledge-graph/search/semantic` - Semantic search
- `POST /api/v1/knowledge-graph/search/paths` - Path finding
- `GET /api/v1/knowledge-graph/search/quick` - Quick search

### Recommendations
- `POST /api/v1/knowledge-graph/recommendations` - Generate recommendations
- `GET /api/v1/knowledge-graph/recommendations/patient/{patient_id}` - Get patient recommendations

### Analytics & Statistics
- `GET /api/v1/knowledge-graph/statistics` - Knowledge graph statistics
- `GET /api/v1/knowledge-graph/insights/patient/{patient_id}` - Patient health insights

### Ontology Management
- `POST /api/v1/knowledge-graph/ontology/import` - Import medical ontologies

## Data Models

### Medical Entity Types
- **CONDITION**: Medical conditions and diseases
- **SYMPTOM**: Patient symptoms and signs
- **TREATMENT**: Medical treatments and interventions
- **MEDICATION**: Drugs and pharmaceutical products
- **PROCEDURE**: Medical procedures and surgeries
- **LAB_TEST**: Laboratory tests and diagnostics
- **VITAL_SIGN**: Patient vital signs
- **RISK_FACTOR**: Health risk factors
- **BODY_PART**: Anatomical structures
- **ORGAN**: Body organs and systems
- **DISEASE**: Specific disease entities
- **SYNDROME**: Medical syndromes
- **ALLERGY**: Allergic reactions and sensitivities
- **CONTRAINDICATION**: Medical contraindications
- **SIDE_EFFECT**: Medication side effects
- **INTERACTION**: Drug interactions
- **GUIDELINE**: Clinical guidelines
- **EVIDENCE**: Evidence-based medical evidence

### Relationship Types
- **CAUSES/CAUSED_BY**: Causal relationships
- **TREATS/TREATED_BY**: Treatment relationships
- **MANIFESTS_AS**: Symptom manifestation
- **INDICATES/SUGGESTS**: Diagnostic indicators
- **INTERACTS_WITH**: Drug interactions
- **LOCATED_IN/PART_OF**: Anatomical relationships
- **INCREASES_RISK_OF**: Risk factor relationships
- **SUPPORTED_BY**: Evidence relationships
- **AFFECTS**: Patient impact relationships

### Confidence Levels
- **LOW**: Low confidence relationship
- **MEDIUM**: Medium confidence relationship
- **HIGH**: High confidence relationship
- **VERY_HIGH**: Very high confidence relationship

### Evidence Levels
- **LEVEL_A**: High-quality evidence
- **LEVEL_B**: Moderate-quality evidence
- **LEVEL_C**: Low-quality evidence
- **LEVEL_D**: Expert opinion
- **LEVEL_E**: No evidence

## Configuration

### Environment Variables
```bash
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-super-secret-neo4j-password

# Qdrant Configuration
QDRANT_URL=http://qdrant:6333

# Service URLs
DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
REDIS_URL=redis://redis:6379
AUTH_SERVICE_URL=http://auth-service:8000
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8002
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8005
DEVICE_DATA_SERVICE_URL=http://device-data-service:8004
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
VOICE_INPUT_SERVICE_URL=http://voice-input-service:8003
MEDICAL_ANALYSIS_SERVICE_URL=http://medical-analysis-service:8006
NUTRITION_SERVICE_URL=http://nutrition-service:8007
HEALTH_ANALYSIS_SERVICE_URL=http://health-analysis-service:8008
CONSENT_AUDIT_SERVICE_URL=http://consent-audit-service:8009
ANALYTICS_SERVICE_URL=http://analytics-service:8210
```

## Development

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Neo4j 5.15.0+
- Qdrant 1.7.0+

### Local Development Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PersonalHealthAssistant
   ```

2. **Start dependencies**
   ```bash
   docker-compose up -d neo4j qdrant postgres-health-assistant redis
   ```

3. **Install dependencies**
   ```bash
   cd apps/knowledge_graph
   pip install -r requirements.txt
   ```

4. **Run the service**
   ```bash
   python main.py
   ```

### Docker Development
```bash
# Build and run the service
docker-compose up -d knowledge-graph-service

# View logs
docker-compose logs -f knowledge-graph-service

# Access the service
curl http://localhost:8010/health
```

## Testing

### API Testing
```bash
# Health check
curl http://localhost:8010/health

# Create medical entity
curl -X POST http://localhost:8010/api/v1/knowledge-graph/entities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Diabetes Mellitus Type 2",
    "entity_type": "condition",
    "description": "A chronic condition affecting blood sugar regulation",
    "synonyms": ["Type 2 Diabetes", "T2DM"],
    "ontology_ids": {"icd_10": "E11", "snomed_ct": "44054006"},
    "confidence": "high",
    "evidence_level": "level_a",
    "source": "icd_10"
  }'

# Semantic search
curl -X POST http://localhost:8010/api/v1/knowledge-graph/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "semantic_search",
    "query_text": "diabetes symptoms",
    "limit": 10
  }'
```

### Unit Testing
```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=apps/knowledge_graph --cov-report=html
```

## Monitoring & Observability

### Health Checks
- **Health Endpoint**: `GET /health` - Service health status
- **Readiness Endpoint**: `GET /ready` - Service readiness status
- **Metrics Endpoint**: Prometheus metrics available

### Logging
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Output**: Console and file logging with rotation

### Metrics
- **Request Metrics**: Request count, duration, error rates
- **Database Metrics**: Neo4j and Qdrant connection health
- **Business Metrics**: Entity count, relationship count, search performance

## Security

### Authentication & Authorization
- **JWT Authentication**: Token-based authentication
- **Role-based Access Control**: User roles and permissions
- **API Rate Limiting**: Request rate limiting per user
- **CORS Configuration**: Cross-origin resource sharing settings

### Data Protection
- **Input Validation**: Comprehensive input validation and sanitization
- **SQL Injection Prevention**: Parameterized queries and ORM usage
- **XSS Protection**: Content Security Policy headers
- **HTTPS Enforcement**: Secure communication protocols

## Deployment

### Docker Deployment
```bash
# Build and deploy
docker-compose up -d knowledge-graph-service

# Scale the service
docker-compose up -d --scale knowledge-graph-service=3
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods -l app=knowledge-graph-service
```

### Production Considerations
- **High Availability**: Multi-instance deployment with load balancing
- **Data Backup**: Regular Neo4j and Qdrant backups
- **Monitoring**: Comprehensive monitoring and alerting
- **Security**: Production-grade security configurations
- **Performance**: Optimized database queries and caching

## Integration Examples

### Health Analysis Integration
```python
# Get health insights for a patient
response = await knowledge_graph_service.get_patient_insights(
    patient_id=patient_id,
    insight_type="risk_assessment"
)
```

### AI Insights Integration
```python
# Generate recommendations based on knowledge graph
recommendations = await knowledge_graph_service.generate_recommendations(
    patient_id=patient_id,
    context=patient_context
)
```

### Medical Records Integration
```python
# Search for related medical conditions
search_results = await knowledge_graph_service.semantic_search(
    query_text="diabetes complications",
    entity_types=["condition", "symptom"]
)
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Support

For support and questions:
- **Documentation**: Check the main project documentation
- **Issues**: Create an issue in the GitHub repository
- **Discussions**: Use GitHub Discussions for questions and ideas

---

**Knowledge Graph Service** - Empowering medical insights through intelligent graph analytics 🧠 