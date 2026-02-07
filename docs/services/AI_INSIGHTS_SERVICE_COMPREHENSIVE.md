# AI Insights Service - Comprehensive Documentation

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

The AI Insights Service provides advanced machine learning and artificial intelligence capabilities for the Personal Health Assistant platform. It powers predictive analytics, anomaly detection, trend analysis, and personalized health recommendations by leveraging state-of-the-art AI models and data science techniques.

### Key Responsibilities
- Predictive analytics and risk scoring
- Anomaly detection in health data
- Trend and pattern recognition
- Personalized health recommendations
- Integration with analytics and health tracking services
- Model training, evaluation, and deployment
- Explainable AI and transparency

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   AI Insights   │
│                 │    │   (Traefik)     │    │   Service       │
│ - Analytics     │───▶│                 │───▶│                 │
│ - Dashboards    │    │ - Rate Limiting │    │ - ML Models     │
│ - Health Track  │    │ - SSL/TLS       │    │ - Predictions   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Model Results │
                                              │ - Predictions   │
                                              │ - Audit Logs    │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Caching       │
                                              │ - Real-time     │
                                              │   Data          │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL for model results and predictions
- **Caching**: Redis for real-time data and model caching
- **ML/AI**: scikit-learn, TensorFlow, PyTorch, transformers
- **Data Processing**: Pandas, NumPy, Dask
- **Explainability**: SHAP, LIME for model transparency

## Features

### 1. Predictive Analytics
- **Risk Scoring**: Predict risk of chronic diseases (diabetes, CVD, etc.)
- **Outcome Prediction**: Predict health outcomes based on user data
- **Event Forecasting**: Forecast future health events (e.g., hospitalizations)
- **Personalized Recommendations**: AI-driven health advice

### 2. Anomaly Detection
- **Outlier Detection**: Identify unusual health patterns
- **Alert Generation**: Trigger alerts for critical anomalies
- **Trend Breaks**: Detect sudden changes in health metrics
- **Continuous Monitoring**: Real-time anomaly detection

### 3. Trend & Pattern Analysis
- **Time Series Analysis**: Analyze trends in health data
- **Pattern Recognition**: Identify recurring health patterns
- **Clustering**: Group similar users or health events
- **Dimensionality Reduction**: Visualize high-dimensional data

### 4. Model Management
- **Model Training**: Train new ML models on health data
- **Model Evaluation**: Evaluate model performance
- **Model Deployment**: Deploy models for real-time inference
- **Model Versioning**: Track model versions and performance
- **Explainable AI**: Provide explanations for predictions

### 5. Integration & Extensibility
- **API Integration**: Serve predictions to other services
- **Batch & Real-time Inference**: Support both modes
- **Webhook Support**: Real-time prediction notifications
- **Role-based Access**: Restrict access to sensitive predictions

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and real-time data

### Machine Learning & AI
- **scikit-learn**: Classical ML algorithms
- **TensorFlow**: Deep learning models
- **PyTorch**: Deep learning and transformers
- **transformers**: Hugging Face transformer models
- **SHAP/LIME**: Model explainability
- **XGBoost/LightGBM**: Gradient boosting models

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Dask**: Parallel and distributed analytics

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **httpx**: Async HTTP client
- **Jinja2**: Report templating
- **PyYAML**: Configuration management

## API Endpoints

### Predictions & Insights

#### POST /api/v1/predict
Get predictions for user data.

**Request Body:**
```json
{
  "user_id": "uuid",
  "input_data": {
    "age": 45,
    "gender": "male",
    "bmi": 28.5,
    "blood_pressure": 130,
    "cholesterol": 210,
    "glucose": 110,
    "activity_level": "moderate"
  },
  "model": "risk_score_v1"
}
```

**Response:**
```json
{
  "prediction_id": "uuid",
  "model": "risk_score_v1",
  "prediction": 0.72,
  "risk_level": "high",
  "explanation": {
    "age": 0.15,
    "bmi": 0.25,
    "blood_pressure": 0.20
  },
  "confidence": 0.91,
  "timestamp": "2023-12-01T12:00:00Z"
}
```

#### GET /api/v1/predictions/{prediction_id}
Get specific prediction details.

#### GET /api/v1/predictions
Get prediction history for a user.

### Anomaly Detection

#### POST /api/v1/anomaly-detection
Detect anomalies in user data.

**Request Body:**
```json
{
  "user_id": "uuid",
  "data": [
    {"timestamp": "2023-12-01T10:00:00Z", "value": 120},
    {"timestamp": "2023-12-01T11:00:00Z", "value": 180}
  ],
  "metric": "blood_pressure"
}
```

**Response:**
```json
{
  "anomalies": [
    {
      "timestamp": "2023-12-01T11:00:00Z",
      "value": 180,
      "score": 0.95,
      "type": "high"
    }
  ]
}
```

### Trend Analysis

#### GET /api/v1/trends
Get trend analysis for user data.

**Query Parameters:**
- `user_id`: User ID
- `metric`: Metric to analyze
- `start_date`: Start date
- `end_date`: End date

### Model Management

#### GET /api/v1/models
Get list of available models.

#### POST /api/v1/models/train
Train a new model.

**Request Body:**
```json
{
  "model_name": "risk_score_v2",
  "training_data": [ ... ],
  "parameters": { ... }
}
```

#### GET /api/v1/models/{model_id}
Get model details and performance.

#### POST /api/v1/models/{model_id}/deploy
Deploy a trained model for inference.

#### GET /api/v1/models/{model_id}/explain
Get model explainability report.

### Explainable AI

#### GET /api/v1/explain/{prediction_id}
Get explanation for a specific prediction.

### Webhooks

#### POST /api/v1/webhooks/predictions
Receive prediction notifications via webhook.

## Data Models

### Prediction Model
```python
class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {'schema': 'ai_insights'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    model = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=False)
    prediction = Column(Float, nullable=False)
    risk_level = Column(String(20))
    explanation = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Anomaly Model
```python
class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = {'schema': 'ai_insights'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    metric = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    score = Column(Float)
    anomaly_type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Model Metadata
```python
class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    __table_args__ = {'schema': 'ai_insights'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    version = Column(String(20))
    parameters = Column(JSON)
    performance = Column(JSON)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=ai-insights-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# Model Configuration
MODEL_DIR=/app/models
DEFAULT_MODEL=risk_score_v1

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
ANALYTICS_SERVICE_URL=http://analytics-service:8210
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001

# Data Processing Configuration
BATCH_SIZE=1000
PROCESSING_INTERVAL=300  # 5 minutes
RETENTION_DAYS=1095  # 3 years

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

# Create models directory
RUN mkdir -p /app/models

EXPOSE 8200

CMD ["uvicorn", "apps.ai_insights.main:app", "--host", "0.0.0.0", "--port", "8200"]
```

### Docker Compose
```yaml
ai-insights-service:
  build:
    context: .
    dockerfile: apps/ai_insights/Dockerfile
  ports:
    - "8200:8200"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - ANALYTICS_SERVICE_URL=http://analytics-service:8210
  volumes:
    - ./models:/app/models
  depends_on:
    - postgres
    - redis
    - auth-service
    - analytics-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8200/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_predictions.py
import pytest
from fastapi.testclient import TestClient
from apps.ai_insights.main import app

client = TestClient(app)

def test_predict():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "input_data": {"age": 45, "bmi": 28.5},
        "model": "risk_score_v1"
    }
    response = client.post("/api/v1/predict", json=data, headers=headers)
    assert response.status_code == 200
    assert "prediction" in response.json()
```

### Integration Tests
```python
# tests/integration/test_anomaly_detection.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_anomaly_detection_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        data = {
            "user_id": "test-user-id",
            "data": [{"timestamp": "2023-12-01T10:00:00Z", "value": 120}],
            "metric": "blood_pressure"
        }
        response = await ac.post("/api/v1/anomaly-detection", json=data)
        assert response.status_code == 200
        assert "anomalies" in response.json()
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-insights-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "models_loaded": True
    }
```

### Metrics
- **Prediction Volume**: Number of predictions served
- **Model Performance**: Model accuracy and latency
- **Anomaly Detection Rate**: Number of anomalies detected
- **API Performance**: Response times and error rates
- **Storage Usage**: Database and model storage usage

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/predict")
async def predict(request: PredictRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Prediction requested by user: {current_user.id}, model: {request.model}")
    # ... prediction logic
    logger.info(f"Prediction completed: {prediction_id}")
```

## Troubleshooting

### Common Issues

#### 1. Model Loading Failures
**Symptoms**: Service startup failures
**Solution**: Verify model files and dependencies

#### 2. Prediction Errors
**Symptoms**: 500 errors on prediction requests
**Solution**: Check input data format and model compatibility

#### 3. Performance Issues
**Symptoms**: Slow predictions or timeouts
**Solution**: Optimize model inference and use model caching

#### 4. Data Quality Issues
**Symptoms**: Poor prediction accuracy
**Solution**: Improve training data quality and retrain models

### Performance Optimization
- **Model Caching**: Cache loaded models in memory
- **Batch Inference**: Process multiple predictions in batches
- **Parallel Processing**: Use Dask for distributed inference
- **Model Pruning**: Optimize model size for faster inference

### Security Considerations
1. **Model Security**: Secure model files and access
2. **Data Privacy**: Ensure input data is anonymized
3. **Access Control**: Implement role-based access to predictions
4. **Audit Logging**: Log all prediction and model access
5. **Compliance**: Ensure compliance with HIPAA/GDPR

---

## Conclusion

The AI Insights Service provides advanced machine learning and AI capabilities for the Personal Health Assistant platform. With robust predictive analytics, anomaly detection, and explainable AI, it empowers users and clinicians with actionable insights for better health outcomes.

For additional support or questions, please refer to the platform documentation or contact the development team. 