# Knowledge Graph Service - Quick Reference Guide

## 🚀 Quick Start

### Service URL
```
http://knowledge-graph.localhost
```

### Health Check
```bash
curl http://knowledge-graph.localhost/health
```

### Get Statistics
```bash
curl http://knowledge-graph.localhost/api/v1/knowledge-graph/statistics
```

## 📊 Current Status

- **Total Entities**: 218
- **Total Relationships**: 115
- **Entity Types**: 8 (Condition, Symptom, Medication, Treatment, Procedure, Lab Test, Vital Sign, Risk Factor)
- **Service Status**: ✅ Healthy
- **Integration Status**: ✅ Fully Integrated

## 🔗 Key API Endpoints

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/knowledge-graph/statistics` | Get statistics |
| GET | `/api/v1/knowledge-graph/entities` | List entities |
| POST | `/api/v1/knowledge-graph/entities` | Create entity |
| GET | `/api/v1/knowledge-graph/entities/{id}` | Get entity |
| PUT | `/api/v1/knowledge-graph/entities/{id}` | Update entity |
| DELETE | `/api/v1/knowledge-graph/entities/{id}` | Delete entity |

### Search Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/knowledge-graph/search/quick` | Quick search |
| POST | `/api/v1/knowledge-graph/search/semantic` | Semantic search |
| POST | `/api/v1/knowledge-graph/search/paths` | Find paths |

### Relationship Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/knowledge-graph/relationships` | List relationships |
| POST | `/api/v1/knowledge-graph/relationships` | Create relationship |

### Recommendation Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/knowledge-graph/recommendations/patient/{id}` | Get recommendations |

## 🏥 Entity Types

| Type | Count | Description |
|------|-------|-------------|
| Condition | 32 | Medical conditions and diseases |
| Symptom | 32 | Patient symptoms and signs |
| Medication | 20 | Drugs and pharmaceutical products |
| Treatment | 28 | Medical treatments and therapies |
| Procedure | 20 | Medical procedures and interventions |
| Lab Test | 28 | Laboratory tests and diagnostics |
| Vital Sign | 28 | Patient vital signs |
| Risk Factor | 30 | Health risk factors |

## 🔗 Relationship Types

| Type | Count | Description |
|------|-------|-------------|
| Manifests As | 30 | Condition manifests as symptom |
| Treated By | 25 | Condition treated by treatment/medication |
| Risk Factor For | 31 | Risk factor for condition |
| Interacts With | 5 | Medication interacts with other medication |
| Complicates | 8 | Condition complicates other condition |
| Monitored By | 16 | Condition monitored by lab test |

## 🔧 Python Client Usage

### Basic Setup
```python
from common.clients.knowledge_graph_client import KnowledgeGraphClient

async with KnowledgeGraphClient() as client:
    # Your code here
    pass
```

### Common Operations
```python
# Get statistics
stats = await client.get_statistics()

# Search entities
results = await client.search_entities("diabetes", entity_type="condition")

# Get entity
entity = await client.get_entity(entity_id)

# Create entity
entity = await client.create_entity(entity_data)

# Get recommendations
recommendations = await client.get_recommendations(patient_id)
```

## 🔗 Integration Endpoints

### Medical Records Service
- `POST /api/v1/medical-records/lab-results/{id}/enrich-with-knowledge-graph`
- `POST /api/v1/medical-records/lab-results/validate-medical-codes`

### AI Insights Service
- `POST /api/v1/ai-insights/insights/enrich-with-knowledge-graph`
- `POST /api/v1/ai-insights/insights/generate-evidence-based-recommendations`
- `POST /api/v1/ai-insights/insights/validate-medical-entities`
- `GET /api/v1/ai-insights/insights/knowledge-graph-stats`
- `POST /api/v1/ai-insights/insights/search-medical-entities`

### Health Tracking Service
- `POST /api/v1/health-tracking/analytics/enrich-metrics`
- `POST /api/v1/health-tracking/analytics/evidence-based-recommendations`
- `POST /api/v1/health-tracking/analytics/validate-health-entities`

## 🛠️ Management Tools

### Dashboard
```bash
python scripts/knowledge_graph_dashboard.py
```

### Analytics
```bash
python scripts/knowledge_graph_analytics.py
```

### Documentation Generator
```bash
python scripts/generate_api_documentation.py
```

### Integration Test
```bash
python scripts/test_knowledge_graph_integration.py
```

## 📋 Environment Variables

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
KNOWLEDGE_GRAPH_SERVICE_URL=http://knowledge-graph.localhost
```

## 🐳 Docker Commands

### Start Services
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs knowledge-graph
```

### Stop Services
```bash
docker-compose down
```

## 🔍 Troubleshooting

### Common Issues
1. **Connection refused**: Check if services are running
2. **Authentication failed**: Verify Neo4j credentials
3. **Search not working**: Check Qdrant connectivity
4. **Slow performance**: Check Redis cache

### Health Checks
```bash
# Service health
curl http://knowledge-graph.localhost/health

# Neo4j health
curl -u neo4j:password http://localhost:7474/browser/

# Qdrant health
curl http://localhost:6333/collections
```

## 📞 Support

- **Service Status**: All services healthy
- **Integration Status**: Fully integrated
- **Documentation**: Complete and up-to-date
- **Testing**: All tests passing

---

**Last Updated**: 2025-08-04  
**Version**: 1.0.0  
**Status**: Production Ready 