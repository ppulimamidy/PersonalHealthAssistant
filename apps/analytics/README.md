# Analytics Service

Comprehensive analytics service for health data processing and insights. Provides population health analytics, patient-level trend analysis, correlations, risk assessment, clinical decision support, and real-time data stream processing.

## Port
- **Port**: 8210

## API Endpoints

All endpoints are prefixed with `/api/v1/analytics`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Service health check |
| GET | `/ready` | No | Readiness probe |
| GET | `/metrics` | No | Prometheus metrics |
| GET | `/api/v1/analytics/health` | No | Analytics service health with capabilities |
| GET | `/api/v1/analytics/capabilities` | No | List all analytics capabilities and algorithms |
| POST | `/api/v1/analytics/patient/{patient_id}/health` | Yes | Comprehensive patient health analysis |
| GET | `/api/v1/analytics/patient/{patient_id}/trends` | Yes | Trend analysis for a specific patient metric |
| GET | `/api/v1/analytics/patient/{patient_id}/correlations` | Yes | Correlation analysis between two patient metrics |
| GET | `/api/v1/analytics/patient/{patient_id}/risk-assessment` | Yes | Comprehensive risk assessment for a patient |
| POST | `/api/v1/analytics/patient/{patient_id}/predictive-model` | Yes | Create predictive model for a patient metric |
| POST | `/api/v1/analytics/population/health` | Yes | Population-level health analysis |
| POST | `/api/v1/analytics/clinical/decision-support` | Yes | Clinical decision support given symptoms |
| GET | `/api/v1/analytics/performance/metrics` | Yes | Platform performance metrics |
| POST | `/api/v1/analytics/real-time/data` | Yes | Add real-time data point for processing |
| GET | `/api/v1/analytics/real-time/streams` | Yes | Get active real-time stream info |
| POST | `/api/v1/analytics/real-time/alerts/thresholds` | Yes | Set alert thresholds for a stream |
| GET | `/api/v1/analytics/test` | No | Test endpoint |

## Database
- **No dedicated tables** — aggregates data from other services via HTTP calls.

## Dependencies
- **PostgreSQL** — database health monitoring (shared connection manager)
- **Redis** — caching (optional)
- **Inter-service dependencies**:
  - `health_tracking` — vitals, symptoms, sleep data
  - `medical_records` — patient records and history
  - `nutrition` — dietary and nutrition data
  - `device_data` — wearable and device telemetry

## Algorithms
- Linear Regression
- Mann-Kendall Trend Test
- Sen's Slope Estimator
- Z-score Anomaly Detection
- FFT Seasonality Detection
- Structural Breakpoint Detection
- Exponential Smoothing Forecasting
- Pearson & Spearman Correlation
- Risk Factor Analysis

## Configuration
Key environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `HEALTH_TRACKING_SERVICE_URL` | Health tracking service URL |
| `MEDICAL_RECORDS_SERVICE_URL` | Medical records service URL |
| `NUTRITION_SERVICE_URL` | Nutrition service URL |
| `DEVICE_DATA_SERVICE_URL` | Device data service URL |
| `LOG_LEVEL` | Logging level (default: `info`) |

## Running Locally
```bash
cd apps/analytics
uvicorn main:app --host 0.0.0.0 --port 8210 --reload
```

## Docker
```bash
docker build -t analytics-service -f apps/analytics/Dockerfile .
docker run -p 8210:8210 analytics-service
```
