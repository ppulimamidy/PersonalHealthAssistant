# Health Analysis Service - Comprehensive Documentation

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

The Health Analysis Service provides advanced health data analysis, pattern recognition, and health insights for the Personal Health Assistant platform. It processes data from multiple sources including health tracking, medical records, device data, and genomics to deliver comprehensive health assessments and personalized recommendations.

### Key Responsibilities
- Multi-source health data analysis
- Pattern recognition and trend analysis
- Health risk assessment and scoring
- Personalized health recommendations
- Integration with AI Insights and Analytics
- Clinical decision support
- Health outcome prediction

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   Health        │
│                 │    │   (Traefik)     │    │   Analysis      │
│ - Web App       │───▶│                 │───▶│   Service       │
│ - Mobile App    │    │ - Rate Limiting │    │                 │
│ - Clinician App │    │ - SSL/TLS       │    │ - Data Analysis │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Analysis      │
                                              │   Results       │
                                              │ - Health        │
                                              │   Assessments   │
                                              │ - Patterns      │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Caching       │
                                              │ - Real-time     │
                                              │   Analysis      │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL for analysis results and health assessments
- **Caching**: Redis for real-time analysis and caching
- **Data Processing**: Pandas, NumPy, SciPy for statistical analysis
- **Machine Learning**: scikit-learn for pattern recognition
- **Integration**: Multiple data source integration

## Features

### 1. Multi-Source Data Analysis
- **Health Tracking Data**: Analyze activity, sleep, nutrition, and vital signs
- **Medical Records**: Process clinical data and medical history
- **Device Data**: Analyze data from wearables and medical devices
- **Genomic Data**: Integrate genetic information for personalized analysis
- **Environmental Data**: Consider environmental factors affecting health
- **Social Determinants**: Analyze social and economic factors

### 2. Pattern Recognition & Trends
- **Temporal Patterns**: Identify patterns over time
- **Correlation Analysis**: Find relationships between health factors
- **Anomaly Detection**: Detect unusual health patterns
- **Seasonal Trends**: Identify seasonal health patterns
- **Longitudinal Analysis**: Track health changes over time
- **Predictive Modeling**: Predict future health outcomes

### 3. Health Risk Assessment
- **Risk Scoring**: Calculate health risk scores
- **Disease Risk**: Assess risk for specific diseases
- **Lifestyle Risk**: Evaluate lifestyle-related risks
- **Genetic Risk**: Incorporate genetic risk factors
- **Environmental Risk**: Assess environmental health risks
- **Comprehensive Risk**: Overall health risk assessment

### 4. Personalized Recommendations
- **Lifestyle Recommendations**: Personalized lifestyle advice
- **Preventive Measures**: Preventive health recommendations
- **Treatment Optimization**: Optimize treatment plans
- **Behavioral Interventions**: Suggest behavioral changes
- **Goal Setting**: Help set and track health goals
- **Progress Monitoring**: Monitor recommendation effectiveness

### 5. Clinical Decision Support
- **Evidence-Based Analysis**: Use evidence-based guidelines
- **Clinical Guidelines**: Integrate clinical practice guidelines
- **Treatment Recommendations**: Suggest treatment options
- **Medication Optimization**: Optimize medication regimens
- **Follow-up Planning**: Plan follow-up care
- **Quality Metrics**: Track quality of care

### 6. Health Outcome Prediction
- **Short-term Predictions**: Predict immediate health outcomes
- **Long-term Projections**: Project long-term health trajectories
- **Intervention Impact**: Predict intervention effectiveness
- **Quality of Life**: Predict quality of life outcomes
- **Healthcare Utilization**: Predict healthcare needs
- **Cost Projections**: Estimate healthcare costs

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and real-time analysis

### Data Analysis & Machine Learning
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **SciPy**: Scientific computing and statistics
- **Scikit-learn**: Machine learning algorithms
- **Matplotlib/Seaborn**: Data visualization
- **Plotly**: Interactive visualizations

### Statistical Analysis
- **Statsmodels**: Statistical modeling
- **Scipy.stats**: Statistical functions
- **Pingouin**: Statistical testing
- **Lifelines**: Survival analysis

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **httpx**: Async HTTP client
- **PyYAML**: Configuration management
- **python-dateutil**: Date and time utilities

## API Endpoints

### Health Analysis

#### POST /api/v1/analysis/comprehensive
Perform comprehensive health analysis.

**Request Body:**
```json
{
  "user_id": "uuid",
  "analysis_type": "comprehensive",
  "data_sources": ["health_tracking", "medical_records", "device_data"],
  "time_range": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-01"
  },
  "include_genomics": true
}
```

**Response:**
```json
{
  "analysis_id": "uuid",
  "user_id": "uuid",
  "analysis_type": "comprehensive",
  "status": "completed",
  "results": {
    "risk_scores": {
      "cardiovascular": 0.15,
      "diabetes": 0.08,
      "overall": 0.12
    },
    "patterns": [
      {
        "type": "trend",
        "metric": "blood_pressure",
        "description": "Gradual increase over 6 months"
      }
    ],
    "recommendations": [
      {
        "category": "lifestyle",
        "priority": "high",
        "description": "Increase physical activity to 150 minutes/week"
      }
    ]
  },
  "created_at": "2023-12-01T12:00:00Z"
}
```

#### GET /api/v1/analysis/{analysis_id}
Get specific analysis results.

#### GET /api/v1/analysis
Get user's analysis history.

### Pattern Recognition

#### POST /api/v1/patterns/detect
Detect health patterns.

**Request Body:**
```json
{
  "user_id": "uuid",
  "metrics": ["heart_rate", "blood_pressure", "sleep_quality"],
  "pattern_types": ["trends", "correlations", "anomalies"],
  "time_window": "6_months"
}
```

#### GET /api/v1/patterns
Get detected patterns.

#### GET /api/v1/patterns/{pattern_id}
Get specific pattern details.

### Risk Assessment

#### POST /api/v1/risk-assessment
Perform health risk assessment.

**Request Body:**
```json
{
  "user_id": "uuid",
  "assessment_type": "comprehensive",
  "include_genetic_risk": true,
  "include_lifestyle_risk": true,
  "include_environmental_risk": true
}
```

#### GET /api/v1/risk-assessment/{assessment_id}
Get risk assessment results.

#### GET /api/v1/risk-assessment/history
Get risk assessment history.

### Recommendations

#### POST /api/v1/recommendations/generate
Generate personalized recommendations.

**Request Body:**
```json
{
  "user_id": "uuid",
  "recommendation_types": ["lifestyle", "preventive", "treatment"],
  "priority_level": "high",
  "timeframe": "3_months"
}
```

#### GET /api/v1/recommendations
Get user recommendations.

#### PUT /api/v1/recommendations/{recommendation_id}
Update recommendation status.

### Clinical Decision Support

#### POST /api/v1/clinical/decision-support
Get clinical decision support.

**Request Body:**
```json
{
  "user_id": "uuid",
  "clinical_context": {
    "symptoms": ["fatigue", "weight_gain"],
    "current_medications": ["metformin"],
    "lab_results": {
      "hba1c": 7.2,
      "glucose": 140
    }
  }
}
```

#### GET /api/v1/clinical/guidelines
Get relevant clinical guidelines.

### Outcome Prediction

#### POST /api/v1/predictions/health-outcomes
Predict health outcomes.

**Request Body:**
```json
{
  "user_id": "uuid",
  "prediction_type": "diabetes_progression",
  "timeframe": "1_year",
  "interventions": ["lifestyle_changes", "medication_adjustment"]
}
```

#### GET /api/v1/predictions
Get prediction history.

### Data Integration

#### POST /api/v1/integration/sync
Sync data from external sources.

#### GET /api/v1/integration/status
Get data integration status.

## Data Models

### Health Analysis Model
```python
class HealthAnalysis(Base):
    __tablename__ = "health_analysis"
    __table_args__ = {'schema': 'health_analysis'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    analysis_type = Column(String(50), nullable=False)
    data_sources = Column(JSON, nullable=False)
    time_range = Column(JSON)
    
    results = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
```

### Health Pattern Model
```python
class HealthPattern(Base):
    __tablename__ = "health_patterns"
    __table_args__ = {'schema': 'health_analysis'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    pattern_type = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=False)
    description = Column(Text)
    
    confidence_score = Column(Float)
    significance_level = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Risk Assessment Model
```python
class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = {'schema': 'health_analysis'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    assessment_type = Column(String(50), nullable=False)
    risk_scores = Column(JSON, nullable=False)
    risk_factors = Column(JSON)
    
    overall_risk = Column(Float)
    risk_level = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Health Recommendation Model
```python
class HealthRecommendation(Base):
    __tablename__ = "health_recommendations"
    __table_args__ = {'schema': 'health_analysis'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    category = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    
    evidence_level = Column(String(20))
    implementation_steps = Column(JSON)
    
    status = Column(String(20), default="pending")
    completed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=health-analysis-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8005
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002
DEVICE_DATA_SERVICE_URL=http://device-data-service:8006
GENOMICS_SERVICE_URL=http://genomics-service:8012
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200

# Analysis Configuration
ANALYSIS_WORKERS=4
MAX_ANALYSIS_TIME_HOURS=2
CACHE_TTL_HOURS=24

# Risk Assessment Configuration
RISK_THRESHOLDS={
  "low": 0.1,
  "medium": 0.3,
  "high": 0.7
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

EXPOSE 8007

CMD ["uvicorn", "apps.health_analysis.main:app", "--host", "0.0.0.0", "--port", "8007"]
```

### Docker Compose
```yaml
health-analysis-service:
  build:
    context: .
    dockerfile: apps/health_analysis/Dockerfile
  ports:
    - "8007:8007"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8005
    - MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002
    - DEVICE_DATA_SERVICE_URL=http://device-data-service:8006
    - GENOMICS_SERVICE_URL=http://genomics-service:8012
    - AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
  depends_on:
    - postgres
    - redis
    - auth-service
    - health-tracking-service
    - medical-records-service
    - device-data-service
    - genomics-service
    - ai-insights-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8007/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_health_analysis.py
import pytest
from fastapi.testclient import TestClient
from apps.health_analysis.main import app

client = TestClient(app)

def test_comprehensive_analysis():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "analysis_type": "comprehensive",
        "data_sources": ["health_tracking", "medical_records"]
    }
    response = client.post("/api/v1/analysis/comprehensive", json=data, headers=headers)
    assert response.status_code == 202
    assert "analysis_id" in response.json()

def test_risk_assessment():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "assessment_type": "comprehensive"
    }
    response = client.post("/api/v1/risk-assessment", json=data, headers=headers)
    assert response.status_code == 201
    assert "assessment_id" in response.json()
```

### Integration Tests
```python
# tests/integration/test_pattern_detection.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_pattern_detection_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Detect patterns
        pattern_data = {
            "user_id": "test-user-id",
            "metrics": ["heart_rate", "blood_pressure"],
            "pattern_types": ["trends", "correlations"]
        }
        response = await ac.post("/api/v1/patterns/detect", json=pattern_data)
        assert response.status_code == 202
        
        # Get patterns
        response = await ac.get("/api/v1/patterns")
        assert response.status_code == 200
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "health-analysis-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "analysis_workers": "active"
    }
```

### Metrics
- **Analysis Jobs**: Number of analysis jobs processed
- **Pattern Detection**: Number of patterns detected
- **Risk Assessments**: Risk assessment completion rates
- **Recommendations**: Recommendation generation and adoption rates
- **API Performance**: Response times and error rates

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/analysis/comprehensive")
async def comprehensive_analysis(request: AnalysisRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Comprehensive analysis requested by user: {current_user.id}")
    # ... analysis logic
    logger.info(f"Analysis completed: {analysis_id}")
```

## Troubleshooting

### Common Issues

#### 1. Data Integration Failures
**Symptoms**: Missing or incomplete data from external services
**Solution**: Check service connectivity and data availability

#### 2. Analysis Performance Issues
**Symptoms**: Slow analysis completion times
**Solution**: Optimize analysis algorithms and increase resources

#### 3. Pattern Detection Accuracy
**Symptoms**: Low pattern detection accuracy
**Solution**: Improve pattern detection algorithms and data quality

#### 4. Risk Assessment Errors
**Symptoms**: Inaccurate risk assessments
**Solution**: Validate risk models and input data quality

### Performance Optimization
- **Parallel Processing**: Use multiple workers for analysis
- **Caching Strategy**: Cache analysis results and intermediate data
- **Database Optimization**: Optimize database queries and indexing
- **Algorithm Optimization**: Optimize analysis algorithms

### Security Considerations
1. **Data Privacy**: Ensure health data privacy and security
2. **Access Control**: Implement role-based access to analysis results
3. **Audit Logging**: Log all analysis and data access activities
4. **Data Encryption**: Encrypt sensitive health analysis data
5. **Compliance**: Ensure compliance with healthcare regulations

---

## Conclusion

The Health Analysis Service provides comprehensive health data analysis and insights for the Personal Health Assistant platform. With advanced pattern recognition, risk assessment, and personalized recommendations, it enables data-driven health decisions and improved health outcomes.

For additional support or questions, please refer to the platform documentation or contact the development team. 