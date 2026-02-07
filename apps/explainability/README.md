# Explainability Service

AI decision explainability (XAI) service for the Personal Health Assistant platform. Provides prediction explanations, recommendation explanations, feature importance analysis, model cards, counterfactual analysis, and AI decision audit trails. Currently in initial implementation with placeholder data.

## Port
- **Port**: 8014

## API Endpoints

### Infrastructure

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Service info |
| GET | `/health` | No | Health check |
| GET | `/ready` | No | Readiness probe |
| GET | `/metrics` | No | Prometheus metrics |

### Explanations (`/api/v1/explainability`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/explainability/explain/prediction` | Yes | Explain an AI prediction (SHAP, LIME, etc.) |
| POST | `/api/v1/explainability/explain/recommendation` | Yes | Explain an AI recommendation |
| GET | `/api/v1/explainability/explanations/{explanation_id}` | Yes | Get a stored explanation |
| GET | `/api/v1/explainability/explanations/patient/{patient_id}` | Yes | Get all explanations for a patient |

### Feature Importance

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/explainability/feature-importance` | Yes | Calculate feature importance for a model |

### Model Cards

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/explainability/model-cards` | Yes | List all AI model cards |
| GET | `/api/v1/explainability/model-cards/{model_id}` | Yes | Get a specific model card |

### Counterfactuals

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/explainability/counterfactuals` | Yes | Generate counterfactual explanations ("what-if" analysis) |

### Audit Trail

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/explainability/audit-trail/{decision_id}` | Yes | Get AI decision audit trail |

## Explanation Methods
- **SHAP** — SHapley Additive exPlanations for feature attribution
- **LIME** — Local Interpretable Model-agnostic Explanations

## Database
- **No dedicated tables yet** — returns placeholder data. Database integration planned for future iterations.

## Dependencies
- **None** — standalone service with no external service or database dependencies at this stage.

## Configuration
Key environment variables:

| Variable | Description |
|----------|-------------|
| `ENVIRONMENT` | Environment name (`development`, `production`) |
| `CORS_ORIGINS` | Allowed CORS origins |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

## Running Locally
```bash
cd apps/explainability
uvicorn main:app --host 0.0.0.0 --port 8014 --reload
```

## Docker
```bash
docker build -t explainability-service -f apps/explainability/Dockerfile .
docker run -p 8014:8014 explainability-service
```
