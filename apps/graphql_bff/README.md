# GraphQL BFF Service

Unified GraphQL Backend-for-Frontend (BFF) interface for the Personal Physician Assistant. Built with Strawberry GraphQL on FastAPI, it provides type-safe, efficient data access for frontend applications by aggregating data from multiple downstream microservices.

## Port
- **Port**: 8400

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Service health check |
| GET | `/playground` | No | GraphQL playground redirect |
| POST | `/graphql` | Yes | GraphQL endpoint (queries, mutations, subscriptions) |
| GET | `/api/v1/health/daily-summary` | No | REST fallback — daily summary |
| GET | `/api/v1/health/daily-summary-test` | No | Test endpoint — daily summary |
| GET | `/api/v1/health/unified-dashboard-test` | No | Test endpoint — unified dashboard |
| POST | `/api/v1/health/analyze-symptoms` | No | REST fallback — symptom analysis |
| POST | `/api/v1/health/query` | No | REST fallback — natural language health query |
| POST | `/api/v1/health/doctor-report` | No | REST fallback — doctor mode report |
| GET | `/metrics` | No | Prometheus metrics |

### GraphQL Queries

| Query | Auth | Description |
|-------|------|-------------|
| `reason` | Yes | Perform health reasoning on a natural language query |
| `daily_summary` | Yes | Get daily health summary with insights and score |
| `doctor_report` | Yes | Generate comprehensive doctor report |
| `real_time_insights` | Yes | Get real-time health insights |
| `health_data` | Yes | Get aggregated health data by time window |
| `insights_history` | Yes | Get paginated historical insights |

### GraphQL Mutations

| Mutation | Auth | Description |
|----------|------|-------------|
| `provide_feedback` | Yes | Provide feedback (helpful/not helpful) on an insight |
| `log_symptom` | Yes | Log a new symptom with severity and duration |
| `log_vital` | Yes | Log a vital sign measurement |

### GraphQL Subscriptions

| Subscription | Auth | Description |
|--------------|------|-------------|
| `health_insights` | Yes | Subscribe to real-time health insights (WebSocket) |

## Database
- **No dedicated tables** — acts as an aggregation layer over downstream services.

## Dependencies
- **Redis** — response caching (optional, degrades gracefully)
- **Inter-service dependencies** (with circuit breaker, retry, and timeout):
  - `ai_reasoning_orchestrator` — health reasoning and doctor reports
  - `health_tracking` — vitals, symptoms, and health metrics
  - `medical_records` — patient medical records
  - `ai_insights` — AI-generated health insights
  - `knowledge_graph` — medical knowledge queries
  - `nutrition` — nutrition and dietary data
  - `device_data` — wearable and device data

## Configuration
Key environment variables:

| Variable | Description |
|----------|-------------|
| `REDIS_URL` | Redis connection URL for caching |
| `AI_REASONING_ORCHESTRATOR_URL` | AI reasoning orchestrator service URL |
| `HEALTH_TRACKING_SERVICE_URL` | Health tracking service URL |
| `MEDICAL_RECORDS_SERVICE_URL` | Medical records service URL |
| `AI_INSIGHTS_SERVICE_URL` | AI insights service URL |
| `KNOWLEDGE_GRAPH_SERVICE_URL` | Knowledge graph service URL |
| `NUTRITION_SERVICE_URL` | Nutrition service URL |
| `DEVICE_DATA_SERVICE_URL` | Device data service URL |
| `CORS_ORIGINS` | Allowed CORS origins |
| `DEBUG` | Enable debug mode / hot reload |

## Running Locally
```bash
cd apps/graphql_bff
uvicorn main:app --host 0.0.0.0 --port 8400 --reload
```

## Docker
```bash
docker build -t graphql-bff-service -f apps/graphql_bff/Dockerfile .
docker run -p 8400:8400 graphql-bff-service
```
