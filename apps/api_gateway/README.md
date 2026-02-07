# API Gateway Service

Central API Gateway for the Personal Health Assistant platform. Routes all incoming traffic to the appropriate microservice, enforces authentication and rate limiting, and provides resilience patterns (circuit breaker, retry, timeout) for every downstream service.

## Port
- **Port**: 8080

## API Endpoints

### Gateway Infrastructure

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Gateway health check |
| GET | `/ready` | No | Readiness check (probes all downstream services) |
| GET | `/metrics` | No | Prometheus metrics (request count, duration, active requests) |

### Composite Health Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/health/analyze-symptoms` | Yes | Composite symptom analysis via AI Reasoning Orchestrator |
| GET | `/health/daily-summary` | Yes | Composite daily health summary |
| POST | `/health/doctor-report` | Yes | Composite doctor mode report |
| POST | `/health/query` | Yes | Natural language health query |
| GET | `/health/unified-dashboard` | Yes | Unified dashboard data (via GraphQL BFF) |

### Service Routes

All routes below proxy to the corresponding microservice. Every route supports `GET`, `POST`, `PUT`, `DELETE`, and `PATCH` methods.

| Route Prefix | Target Service |
|--------------|----------------|
| `/auth/{path}` | Auth Service |
| `/user-profile/{path}` | User Profile Service |
| `/health-tracking/{path}` | Health Tracking Service |
| `/ai-reasoning/{path}` | AI Reasoning Orchestrator |
| `/graphql/{path}` | GraphQL BFF Service |
| `/ai-insights/{path}` | AI Insights Service |
| `/medical-records/{path}` | Medical Records Service |
| `/nutrition/{path}` | Nutrition Service |
| `/device-data/{path}` | Device Data Service |
| `/voice-input/{path}` | Voice Input Service |
| `/medical-analysis/{path}` | Medical Analysis Service |
| `/health-analysis/{path}` | Health Analysis Service |
| `/consent-audit/{path}` | Consent Audit Service |
| `/knowledge-graph/{path}` | Knowledge Graph Service |
| `/doctor-collaboration/{path}` | Doctor Collaboration Service |
| `/genomics/{path}` | Genomics Service |
| `/analytics/{path}` | Analytics Service |
| `/ecommerce/{path}` | E-commerce Service |
| `/explainability/{path}` | Explainability Service |

### Public Endpoints (no auth required)
- `/auth/register`
- `/auth/login`
- `/auth/refresh`
- `/health`
- `/ready`
- `/metrics`

## Database
- **No dedicated tables** — stateless routing layer.

## Resilience Patterns
Each downstream service is wrapped with:
- **Circuit Breaker** — failure threshold: 5, recovery timeout: 60s
- **Retry** — max attempts: 2–3 (AI services use fewer retries)
- **Timeout** — 30s default, 60s for AI/voice/genomics services

## Rate Limiting
- **Redis-backed** distributed rate limiting (falls back to in-memory if Redis is unavailable)
- Default: configurable via `RATE_LIMIT_PER_MINUTE` setting
- Client identification: JWT user ID or IP address

## Dependencies
- **Redis** — distributed rate limiting and caching
- **All downstream microservices** — see service routes table above

## Configuration
Key environment variables:

| Variable | Description |
|----------|-------------|
| `REDIS_URL` | Redis connection URL |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute per client |
| `AUTH_SERVICE_URL` | Auth service base URL |
| `USER_PROFILE_SERVICE_URL` | User profile service base URL |
| `HEALTH_TRACKING_SERVICE_URL` | Health tracking service base URL |
| `AI_REASONING_ORCHESTRATOR_URL` | AI reasoning orchestrator base URL |
| `GRAPHQL_BFF_URL` | GraphQL BFF service base URL |
| `AI_INSIGHTS_SERVICE_URL` | AI insights service base URL |
| `MEDICAL_RECORDS_SERVICE_URL` | Medical records service base URL |
| `NUTRITION_SERVICE_URL` | Nutrition service base URL |
| `DEVICE_DATA_SERVICE_URL` | Device data service base URL |
| `VOICE_INPUT_SERVICE_URL` | Voice input service base URL |
| `MEDICAL_ANALYSIS_SERVICE_URL` | Medical analysis service base URL |
| `HEALTH_ANALYSIS_SERVICE_URL` | Health analysis service base URL |
| `CONSENT_AUDIT_SERVICE_URL` | Consent audit service base URL |
| `KNOWLEDGE_GRAPH_SERVICE_URL` | Knowledge graph service base URL |
| `DOCTOR_COLLABORATION_SERVICE_URL` | Doctor collaboration service base URL |
| `GENOMICS_SERVICE_URL` | Genomics service base URL |
| `ANALYTICS_SERVICE_URL` | Analytics service base URL |
| `ECOMMERCE_SERVICE_URL` | E-commerce service base URL |
| `EXPLAINABILITY_SERVICE_URL` | Explainability service base URL |
| `CORS_ORIGINS` | Allowed CORS origins |
| `DEBUG` | Enable debug mode / hot reload |

## Running Locally
```bash
cd apps/api_gateway
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## Docker
```bash
docker build -t api-gateway -f apps/api_gateway/Dockerfile .
docker run -p 8080:8080 api-gateway
```
