# Health Tracking Service - Comprehensive Documentation

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

The Health Tracking Service is a comprehensive solution for monitoring and tracking various health metrics, activities, and wellness data. It provides real-time data collection, analysis, and insights for users to maintain and improve their health and fitness goals.

### Key Responsibilities
- Activity tracking and monitoring
- Vital signs and biometric data collection
- Goal setting and progress tracking
- Health metrics analysis and insights
- Integration with wearable devices and health apps
- Real-time data processing and alerts
- Historical data analysis and trends

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │ Health Tracking │
│                 │    │   (Traefik)     │    │   Service       │
│ - Mobile App    │───▶│                 │───▶│                 │
│ - Web App       │    │ - Rate Limiting │    │ - Activity      │
│ - Wearables     │    │ - SSL/TLS       │    │   Tracking      │
│ - IoT Devices   │    │                 │    │ - Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Activities    │
                                              │ - Metrics       │
                                              │ - Goals         │
                                              │ - Trends        │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Real-time     │
                                              │   Data          │
                                              │ - Caching       │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Caching**: Redis for real-time data and caching
- **Message Queue**: Kafka for event streaming
- **AI/ML**: Integration with AI Insights Service for predictive analytics

## Features

### 1. Activity Tracking
- **Physical Activities**: Steps, distance, calories burned
- **Exercise Sessions**: Workouts, sports, training sessions
- **Movement Patterns**: Sedentary time, active minutes
- **Sleep Tracking**: Sleep duration, quality, stages
- **Heart Rate Monitoring**: Resting HR, exercise HR, HRV

### 2. Vital Signs & Biometrics
- **Blood Pressure**: Systolic, diastolic, pulse pressure
- **Blood Glucose**: Fasting, post-meal, continuous monitoring
- **Weight & Body Composition**: Weight, BMI, body fat, muscle mass
- **Temperature**: Body temperature monitoring
- **Oxygen Saturation**: SpO2 levels

### 3. Goal Management
- **Goal Setting**: Custom health and fitness goals
- **Progress Tracking**: Real-time progress monitoring
- **Achievement System**: Milestones and rewards
- **Goal Recommendations**: AI-powered goal suggestions
- **Social Features**: Goal sharing and challenges

### 4. Data Analysis & Insights
- **Trend Analysis**: Historical data patterns
- **Predictive Analytics**: Health outcome predictions
- **Anomaly Detection**: Unusual health patterns
- **Correlation Analysis**: Health factor relationships
- **Personalized Insights**: Custom health recommendations

### 5. Device Integration
- **Wearable Devices**: Apple Watch, Fitbit, Garmin
- **Health Apps**: Integration with popular health apps
- **IoT Devices**: Smart scales, blood pressure monitors
- **Manual Entry**: Manual data input capabilities
- **Data Synchronization**: Real-time data sync

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **TimescaleDB**: Time-series data extension
- **Redis 7**: Caching and real-time data
- **Apache Kafka**: Event streaming

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **SciPy**: Scientific computing
- **Scikit-learn**: Machine learning algorithms

### Additional Libraries
- **Pydantic**: Data validation and serialization
- **Celery**: Background task processing
- **Prometheus**: Metrics collection
- **Grafana**: Data visualization

## API Endpoints

### Activity Tracking

#### POST /api/v1/activities
Record a new activity session.

**Request Body:**
```json
{
  "activity_type": "running",
  "start_time": "2023-12-01T10:00:00Z",
  "end_time": "2023-12-01T11:00:00Z",
  "duration_minutes": 60,
  "distance_km": 8.5,
  "calories_burned": 650,
  "heart_rate_data": [
    {
      "timestamp": "2023-12-01T10:05:00Z",
      "bpm": 145
    }
  ],
  "steps": 8500,
  "elevation_gain_m": 120,
  "pace_min_per_km": 7.1,
  "route": {
    "coordinates": [
      {"lat": 40.7128, "lng": -74.0060},
      {"lat": 40.7129, "lng": -74.0061}
    ]
  },
  "weather": {
    "temperature_c": 22,
    "humidity_percent": 65,
    "conditions": "sunny"
  }
}
```

#### GET /api/v1/activities
Get user's activity history.

**Query Parameters:**
- `activity_type`: Filter by activity type
- `start_date`: Start date for filtering
- `end_date`: End date for filtering
- `limit`: Number of records to return
- `offset`: Pagination offset

#### GET /api/v1/activities/{activity_id}
Get specific activity details.

#### PUT /api/v1/activities/{activity_id}
Update activity data.

#### DELETE /api/v1/activities/{activity_id}
Delete activity record.

### Vital Signs & Metrics

#### POST /api/v1/metrics
Record health metrics.

**Request Body:**
```json
{
  "metric_type": "blood_pressure",
  "timestamp": "2023-12-01T12:00:00Z",
  "values": {
    "systolic": 120,
    "diastolic": 80,
    "pulse": 72
  },
  "device_id": "bp_monitor_001",
  "notes": "Morning reading"
}
```

#### GET /api/v1/metrics
Get health metrics history.

**Query Parameters:**
- `metric_type`: Type of metric (blood_pressure, glucose, weight, etc.)
- `start_date`: Start date for filtering
- `end_date`: End date for filtering
- `limit`: Number of records to return

#### GET /api/v1/metrics/summary
Get metrics summary and trends.

#### GET /api/v1/metrics/latest
Get latest metrics for all types.

### Goals & Progress

#### POST /api/v1/goals
Create a new health goal.

**Request Body:**
```json
{
  "goal_type": "steps",
  "target_value": 10000,
  "target_date": "2023-12-31",
  "frequency": "daily",
  "description": "Walk 10,000 steps daily",
  "category": "fitness"
}
```

#### GET /api/v1/goals
Get user's goals.

#### GET /api/v1/goals/{goal_id}
Get specific goal details.

#### PUT /api/v1/goals/{goal_id}
Update goal.

#### DELETE /api/v1/goals/{goal_id}
Delete goal.

#### GET /api/v1/goals/{goal_id}/progress
Get goal progress tracking.

### Sleep Tracking

#### POST /api/v1/sleep
Record sleep data.

**Request Body:**
```json
{
  "start_time": "2023-12-01T23:00:00Z",
  "end_time": "2023-12-02T07:00:00Z",
  "duration_hours": 8,
  "sleep_stages": {
    "light_sleep_hours": 4.5,
    "deep_sleep_hours": 2.0,
    "rem_sleep_hours": 1.5
  },
  "sleep_score": 85,
  "sleep_efficiency": 92,
  "device_id": "sleep_tracker_001"
}
```

#### GET /api/v1/sleep
Get sleep history.

#### GET /api/v1/sleep/analysis
Get sleep analysis and insights.

### Heart Rate Monitoring

#### POST /api/v1/heart-rate
Record heart rate data.

**Request Body:**
```json
{
  "timestamp": "2023-12-01T10:00:00Z",
  "bpm": 72,
  "hrv_ms": 45,
  "context": "resting",
  "device_id": "hr_monitor_001"
}
```

#### GET /api/v1/heart-rate
Get heart rate history.

#### GET /api/v1/heart-rate/zones
Get heart rate zones analysis.

### Analytics & Insights

#### GET /api/v1/analytics/trends
Get health trends analysis.

#### GET /api/v1/analytics/correlations
Get health factor correlations.

#### GET /api/v1/analytics/recommendations
Get personalized health recommendations.

#### GET /api/v1/analytics/anomalies
Get detected health anomalies.

### Device Integration

#### POST /api/v1/devices
Register a new device.

#### GET /api/v1/devices
Get user's connected devices.

#### POST /api/v1/devices/{device_id}/sync
Sync data from device.

#### DELETE /api/v1/devices/{device_id}
Disconnect device.

## Data Models

### Activity Model
```python
class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = {'schema': 'health_tracking'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    activity_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # Activity-specific data
    distance_km = Column(Float)
    calories_burned = Column(Integer)
    steps = Column(Integer)
    elevation_gain_m = Column(Float)
    pace_min_per_km = Column(Float)
    
    # Additional data
    heart_rate_data = Column(JSON)
    route = Column(JSON)
    weather = Column(JSON)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Health Metric Model
```python
class HealthMetric(Base):
    __tablename__ = "health_metrics"
    __table_args__ = {'schema': 'health_tracking'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    metric_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    values = Column(JSON, nullable=False)
    
    device_id = Column(String(100))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Goal Model
```python
class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = {'schema': 'health_tracking'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    goal_type = Column(String(50), nullable=False)
    target_value = Column(Float, nullable=False)
    target_date = Column(Date, nullable=False)
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    description = Column(Text)
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Sleep Model
```python
class Sleep(Base):
    __tablename__ = "sleep"
    __table_args__ = {'schema': 'health_tracking'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_hours = Column(Float, nullable=False)
    
    sleep_stages = Column(JSON)
    sleep_score = Column(Integer)
    sleep_efficiency = Column(Float)
    
    device_id = Column(String(100))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Service Configuration
SERVICE_NAME=health-tracking-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001

# Data Processing Configuration
BATCH_SIZE=1000
PROCESSING_INTERVAL=300  # 5 minutes
RETENTION_DAYS=1095  # 3 years

# Device Integration
DEVICE_SYNC_INTERVAL=3600  # 1 hour
MAX_DEVICE_CONNECTIONS=10

# Analytics Configuration
TREND_ANALYSIS_DAYS=30
ANOMALY_DETECTION_SENSITIVITY=0.8
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

EXPOSE 8002

CMD ["uvicorn", "apps.health_tracking.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Docker Compose
```yaml
health-tracking-service:
  build:
    context: .
    dockerfile: apps/health_tracking/Dockerfile
  ports:
    - "8002:8002"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    - AUTH_SERVICE_URL=http://auth-service:8000
  depends_on:
    - postgres
    - redis
    - kafka
    - auth-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_activities.py
import pytest
from fastapi.testclient import TestClient
from apps.health_tracking.main import app

client = TestClient(app)

def test_create_activity():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "activity_type": "running",
        "start_time": "2023-12-01T10:00:00Z",
        "end_time": "2023-12-01T11:00:00Z",
        "duration_minutes": 60,
        "distance_km": 8.5,
        "calories_burned": 650
    }
    response = client.post("/api/v1/activities", json=data, headers=headers)
    assert response.status_code == 201
    assert "id" in response.json()

def test_get_activities():
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v1/activities", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Integration Tests
```python
# tests/integration/test_metrics.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_metrics_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create metric
        metric_data = {
            "metric_type": "blood_pressure",
            "timestamp": "2023-12-01T12:00:00Z",
            "values": {"systolic": 120, "diastolic": 80}
        }
        response = await ac.post("/api/v1/metrics", json=metric_data)
        assert response.status_code == 201
        
        # Get metrics
        response = await ac.get("/api/v1/metrics?metric_type=blood_pressure")
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
        "service": "health-tracking-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "kafka": "connected"
    }
```

### Metrics
- **Data Ingestion Rate**: Records per minute
- **Processing Latency**: Time to process data
- **Storage Usage**: Database and cache usage
- **Device Connections**: Active device connections
- **API Performance**: Response times and error rates

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/activities")
async def create_activity(activity: ActivityCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"Activity created for user: {current_user.id}, type: {activity.activity_type}")
    # ... activity creation logic
    logger.info(f"Activity saved successfully: {activity_id}")
```

## Troubleshooting

### Common Issues

#### 1. Data Synchronization Failures
**Symptoms**: Missing or delayed data from devices
**Solution**: Check device connectivity and sync intervals

#### 2. High Database Load
**Symptoms**: Slow response times, connection timeouts
**Solution**: Optimize queries, add indexes, implement caching

#### 3. Memory Usage Issues
**Symptoms**: Service crashes, high memory consumption
**Solution**: Optimize data processing, implement pagination

#### 4. Device Integration Problems
**Symptoms**: Device connection failures
**Solution**: Verify device API credentials and connection limits

### Performance Optimization
- **Database Indexing**: Optimize time-series queries
- **Caching Strategy**: Cache frequently accessed data
- **Data Partitioning**: Partition large datasets by time
- **Batch Processing**: Process data in batches for efficiency

### Security Considerations
1. **Data Encryption**: Encrypt sensitive health data
2. **Access Control**: Implement proper authorization
3. **Audit Logging**: Log all data access and modifications
4. **Privacy Compliance**: Ensure HIPAA and GDPR compliance
5. **Device Security**: Secure device authentication and data transmission

---

## Conclusion

The Health Tracking Service provides a comprehensive solution for monitoring and analyzing health and fitness data. With robust data models, real-time processing capabilities, and extensive device integration, it enables users to track their health journey effectively and gain valuable insights for better health outcomes.

For additional support or questions, please refer to the platform documentation or contact the development team. 