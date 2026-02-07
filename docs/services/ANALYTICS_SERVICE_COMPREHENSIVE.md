# Analytics Service - Comprehensive Documentation

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

The Analytics Service provides advanced data analytics, reporting, and visualization capabilities for the Personal Health Assistant platform. It aggregates, processes, and analyzes data from all other microservices to deliver actionable insights, trends, and reports to users and clinicians.

### Key Responsibilities
- Aggregation of health, activity, and clinical data
- Real-time and batch analytics
- Trend and anomaly detection
- Custom and scheduled reporting
- Data visualization and dashboards
- Integration with AI Insights Service
- Export and sharing of analytics results

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   Analytics     │
│                 │    │   (Traefik)     │    │   Service       │
│ - Web App       │───▶│                 │───▶│                 │
│ - Mobile App    │    │ - Rate Limiting │    │ - Data Agg      │
│ - Dashboards    │    │ - SSL/TLS       │    │ - Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Analytics     │
                                              │   Results       │
                                              │ - Reports       │
                                              │ - Dashboards    │
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
- **Database**: PostgreSQL for analytics results and reports
- **Caching**: Redis for real-time analytics and dashboard data
- **Data Processing**: Pandas, NumPy, and Dask for analytics
- **Visualization**: Matplotlib, Seaborn, Plotly for charts
- **Integration**: AI Insights Service for ML-powered analytics

## Features

### 1. Data Aggregation & ETL
- **ETL Pipelines**: Extract, transform, and load data from all services
- **Data Normalization**: Standardize data formats
- **Data Cleansing**: Remove duplicates, handle missing values
- **Batch & Real-time Processing**: Support for both modes

### 2. Analytics & Insights
- **Trend Analysis**: Identify health and activity trends
- **Anomaly Detection**: Detect outliers and unusual patterns
- **Correlation Analysis**: Find relationships between health factors
- **Predictive Analytics**: Integrate with AI Insights for predictions
- **Personalized Insights**: User-specific analytics and recommendations

### 3. Reporting & Visualization
- **Custom Reports**: User-defined and scheduled reports
- **Dashboards**: Interactive dashboards for users and clinicians
- **Data Export**: Export analytics results in CSV, PDF, JSON
- **Visualization**: Charts, graphs, and heatmaps
- **Sharing**: Share reports with providers or family

### 4. Integration & Extensibility
- **API Integration**: Pull data from all microservices
- **Webhook Support**: Real-time analytics notifications
- **Plugin Architecture**: Support for custom analytics modules
- **Role-based Access**: Different dashboards for users, clinicians, admins

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and real-time data

### Data Processing & Analytics
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Dask**: Parallel and distributed analytics
- **Seaborn**: Statistical data visualization
- **Matplotlib**: Plotting and charting
- **Plotly**: Interactive visualizations
- **Scikit-learn**: Machine learning algorithms

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **httpx**: Async HTTP client
- **Jinja2**: Report templating
- **PyYAML**: Configuration management

## API Endpoints

### Analytics & Insights

#### GET /api/v1/analytics/overview
Get analytics overview for the user.

#### GET /api/v1/analytics/trends
Get health and activity trends.

#### GET /api/v1/analytics/anomalies
Get detected anomalies in user data.

#### GET /api/v1/analytics/correlations
Get correlation analysis results.

#### GET /api/v1/analytics/predictions
Get AI-powered predictions and risk scores.

#### GET /api/v1/analytics/recommendations
Get personalized recommendations.

### Reporting

#### GET /api/v1/reports
Get list of available reports.

#### POST /api/v1/reports
Create a new custom report.

#### GET /api/v1/reports/{report_id}
Get specific report details.

#### PUT /api/v1/reports/{report_id}
Update report configuration.

#### DELETE /api/v1/reports/{report_id}
Delete report.

#### GET /api/v1/reports/{report_id}/download
Download report in specified format (CSV, PDF, JSON).

### Dashboards

#### GET /api/v1/dashboards
Get available dashboards.

#### GET /api/v1/dashboards/{dashboard_id}
Get dashboard data and visualizations.

#### POST /api/v1/dashboards
Create a new dashboard.

#### PUT /api/v1/dashboards/{dashboard_id}
Update dashboard configuration.

#### DELETE /api/v1/dashboards/{dashboard_id}
Delete dashboard.

### Data Export

#### GET /api/v1/export
Export analytics data.

### Webhooks

#### POST /api/v1/webhooks/analytics
Receive analytics notifications via webhook.

## Data Models

### Analytics Result Model
```python
class AnalyticsResult(Base):
    __tablename__ = "analytics_results"
    __table_args__ = {'schema': 'analytics'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    result_type = Column(String(50), nullable=False)  # trend, anomaly, correlation, etc.
    data = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Report Model
```python
class Report(Base):
    __tablename__ = "reports"
    __table_args__ = {'schema': 'analytics'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text)
    report_type = Column(String(50), nullable=False)
    configuration = Column(JSON, default=dict)
    status = Column(String(20), default="pending")
    generated_at = Column(DateTime)
    file_path = Column(String(500))
    file_format = Column(String(10))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Dashboard Model
```python
class Dashboard(Base):
    __tablename__ = "dashboards"
    __table_args__ = {'schema': 'analytics'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    description = Column(Text)
    widgets = Column(JSON, default=list)
    configuration = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=analytics-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001

# Data Processing Configuration
BATCH_SIZE=1000
PROCESSING_INTERVAL=300  # 5 minutes
RETENTION_DAYS=1095  # 3 years

# Reporting Configuration
REPORTS_DIR=/app/reports
MAX_REPORT_SIZE_MB=10
ALLOWED_REPORT_FORMATS=["csv", "pdf", "json"]

# Visualization Configuration
PLOTLY_API_KEY=your-plotly-api-key

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

# Create reports directory
RUN mkdir -p /app/reports

EXPOSE 8210

CMD ["uvicorn", "apps.analytics.main:app", "--host", "0.0.0.0", "--port", "8210"]
```

### Docker Compose
```yaml
analytics-service:
  build:
    context: .
    dockerfile: apps/analytics/Dockerfile
  ports:
    - "8210:8210"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
  volumes:
    - ./reports:/app/reports
  depends_on:
    - postgres
    - redis
    - auth-service
    - ai-insights-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8210/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_analytics.py
import pytest
from fastapi.testclient import TestClient
from apps.analytics.main import app

client = TestClient(app)

def test_get_analytics_overview():
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v1/analytics/overview", headers=headers)
    assert response.status_code == 200
    assert "trends" in response.json()

def test_create_report():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "title": "Weekly Health Report",
        "report_type": "weekly",
        "configuration": {"metrics": ["steps", "sleep"]}
    }
    response = client.post("/api/v1/reports", json=data, headers=headers)
    assert response.status_code == 201
    assert "report_id" in response.json()
```

### Integration Tests
```python
# tests/integration/test_dashboards.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_dashboard_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create dashboard
        dashboard_data = {
            "title": "My Health Dashboard",
            "widgets": [
                {"type": "trend", "metric": "steps"},
                {"type": "pie", "metric": "activity_distribution"}
            ]
        }
        response = await ac.post("/api/v1/dashboards", json=dashboard_data)
        assert response.status_code == 201
        
        # Get dashboards
        response = await ac.get("/api/v1/dashboards")
        assert response.status_code == 200
        assert len(response.json()) > 0
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected"
    }
```

### Metrics
- **Analytics Jobs**: Number of analytics jobs processed
- **Report Generation**: Report generation times and success rates
- **Dashboard Usage**: Dashboard access and usage metrics
- **API Performance**: Response times and error rates
- **Storage Usage**: Database and file storage usage

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.get("/api/v1/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    logger.info(f"Analytics overview requested by user: {current_user.id}")
    # ... analytics logic
    logger.info(f"Analytics overview generated for user: {current_user.id}")
```

## Troubleshooting

### Common Issues

#### 1. Data Aggregation Failures
**Symptoms**: Missing or incomplete analytics data
**Solution**: Check ETL pipeline logs and data source connectivity

#### 2. Report Generation Errors
**Symptoms**: Report generation failures
**Solution**: Check report configuration and file storage permissions

#### 3. Visualization Issues
**Symptoms**: Broken or missing charts
**Solution**: Verify data format and visualization library versions

#### 4. Performance Issues
**Symptoms**: Slow analytics or dashboard loading
**Solution**: Optimize queries, use caching, and scale resources

### Performance Optimization
- **Batch Processing**: Process large datasets in batches
- **Caching Strategy**: Cache frequently accessed analytics data
- **Parallel Processing**: Use Dask for distributed analytics
- **Visualization Optimization**: Optimize chart rendering

### Security Considerations
1. **Data Privacy**: Ensure analytics data is anonymized
2. **Access Control**: Implement role-based access to analytics
3. **Audit Logging**: Log all analytics and report access
4. **Data Encryption**: Encrypt sensitive analytics data
5. **Compliance**: Ensure compliance with HIPAA/GDPR

---

## Conclusion

The Analytics Service provides advanced analytics, reporting, and visualization capabilities for the Personal Health Assistant platform. With robust ETL pipelines, real-time and batch analytics, and seamless integration with AI Insights, it delivers actionable insights and empowers users to make informed health decisions.

For additional support or questions, please refer to the platform documentation or contact the development team. 