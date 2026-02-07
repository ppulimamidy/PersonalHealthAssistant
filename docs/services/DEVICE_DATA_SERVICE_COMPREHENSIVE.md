# Device Data Service - Comprehensive Documentation

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

The Device Data Service manages the collection, processing, and synchronization of data from various health and fitness devices, wearables, and IoT sensors. It provides a unified interface for integrating with multiple device platforms and ensuring reliable data flow into the Personal Health Assistant platform.

### Key Responsibilities
- Device registration and management
- Data collection and synchronization
- Device authentication and security
- Data validation and quality control
- Real-time data streaming
- Historical data management
- Device health monitoring

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Devices   │    │   API Gateway   │    │  Device Data    │
│                 │    │   (Traefik)     │    │   Service       │
│ - Wearables     │───▶│                 │───▶│                 │
│ - Health Monitors│   │ - Rate Limiting │    │ - Device Mgmt   │
│ - Smart Scales  │    │ - SSL/TLS       │    │ - Data Sync     │
│ - Blood Pressure│    │                 │    │ - Validation    │
│   Monitors      │    │                 │    │ - Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Devices       │
                                              │ - Device Data   │
                                              │ - Sync History  │
                                              │ - Device Health │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Real-time     │
                                              │   Data          │
                                              │ - Device Cache  │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Caching**: Redis for real-time data and device caching
- **Message Queue**: Kafka for event streaming
- **Device Integration**: REST APIs, WebSockets, MQTT support

## Features

### 1. Device Management
- **Device Registration**: Register and configure new devices
- **Device Authentication**: Secure device authentication and authorization
- **Device Profiles**: Store device capabilities and configurations
- **Device Health Monitoring**: Monitor device connectivity and status
- **Firmware Management**: Track device firmware versions and updates
- **Device Groups**: Organize devices into logical groups

### 2. Data Collection & Synchronization
- **Real-time Data Streaming**: Stream data from connected devices
- **Batch Data Sync**: Synchronize historical data from devices
- **Incremental Sync**: Efficient incremental data synchronization
- **Data Validation**: Validate data quality and consistency
- **Data Transformation**: Transform device-specific data formats
- **Data Deduplication**: Remove duplicate data entries

### 3. Device Integration
- **Apple HealthKit**: Integration with Apple Health ecosystem
- **Google Fit**: Integration with Google Fit platform
- **Fitbit API**: Direct Fitbit device integration
- **Garmin Connect**: Garmin device integration
- **Oura Ring**: Oura sleep and activity tracking
- **Custom APIs**: Support for custom device APIs

### 4. Data Processing
- **Data Normalization**: Normalize data across different devices
- **Data Aggregation**: Aggregate data from multiple devices
- **Data Enrichment**: Add metadata and context to device data
- **Data Quality Scoring**: Assess and score data quality
- **Anomaly Detection**: Detect unusual data patterns
- **Data Compression**: Compress data for efficient storage

### 5. Security & Privacy
- **Device Authentication**: Secure device authentication
- **Data Encryption**: Encrypt sensitive device data
- **Access Control**: Role-based access to device data
- **Audit Logging**: Comprehensive audit trails
- **Data Retention**: Configurable data retention policies
- **Privacy Controls**: User-controlled data sharing

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **TimescaleDB**: Time-series data extension
- **Redis 7**: Caching and real-time data
- **Apache Kafka**: Event streaming

### Device Integration
- **httpx**: Async HTTP client for API calls
- **websockets**: WebSocket support for real-time communication
- **paho-mqtt**: MQTT client for IoT devices
- **aiohttp**: Async HTTP server/client

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Pydantic**: Data validation and serialization
- **Celery**: Background task processing

### Additional Libraries
- **cryptography**: Data encryption
- **python-jose**: JWT handling
- **redis**: Redis client
- **prometheus-client**: Metrics collection

## API Endpoints

### Device Management

#### POST /api/v1/devices
Register a new device.

**Request Body:**
```json
{
  "device_type": "fitbit_charge_5",
  "device_name": "My Fitbit",
  "manufacturer": "Fitbit",
  "model": "Charge 5",
  "serial_number": "FB123456789",
  "firmware_version": "1.2.3",
  "capabilities": [
    "heart_rate",
    "steps",
    "sleep",
    "gps"
  ],
  "integration_type": "api",
  "credentials": {
    "access_token": "fitbit_access_token",
    "refresh_token": "fitbit_refresh_token",
    "expires_at": "2023-12-31T23:59:59Z"
  },
  "sync_settings": {
    "auto_sync": true,
    "sync_interval_minutes": 15,
    "sync_historical_days": 30
  }
}
```

**Response:**
```json
{
  "device_id": "uuid",
  "status": "registered",
  "sync_status": "pending",
  "last_sync": null,
  "next_sync": "2023-12-01T12:15:00Z",
  "created_at": "2023-12-01T12:00:00Z"
}
```

#### GET /api/v1/devices
Get user's registered devices.

**Query Parameters:**
- `device_type`: Filter by device type
- `status`: Filter by device status
- `limit`: Number of devices to return
- `offset`: Pagination offset

#### GET /api/v1/devices/{device_id}
Get specific device details.

#### PUT /api/v1/devices/{device_id}
Update device configuration.

#### DELETE /api/v1/devices/{device_id}
Unregister device.

#### POST /api/v1/devices/{device_id}/sync
Manually trigger device synchronization.

### Data Collection

#### POST /api/v1/devices/{device_id}/data
Upload device data.

**Request Body:**
```json
{
  "data_type": "heart_rate",
  "timestamp": "2023-12-01T12:00:00Z",
  "values": [
    {
      "timestamp": "2023-12-01T12:00:00Z",
      "value": 72,
      "unit": "bpm",
      "quality": "good"
    },
    {
      "timestamp": "2023-12-01T12:01:00Z",
      "value": 75,
      "unit": "bpm",
      "quality": "good"
    }
  ],
  "metadata": {
    "source": "device",
    "accuracy": 0.95,
    "battery_level": 85
  }
}
```

#### GET /api/v1/devices/{device_id}/data
Get device data.

**Query Parameters:**
- `data_type`: Type of data to retrieve
- `start_time`: Start time for data range
- `end_time`: End time for data range
- `limit`: Number of data points to return

#### GET /api/v1/devices/{device_id}/data/latest
Get latest data from device.

#### DELETE /api/v1/devices/{device_id}/data
Delete device data.

### Device Health

#### GET /api/v1/devices/{device_id}/health
Get device health status.

**Response:**
```json
{
  "device_id": "uuid",
  "status": "online",
  "last_seen": "2023-12-01T12:00:00Z",
  "battery_level": 85,
  "signal_strength": "good",
  "sync_status": "successful",
  "last_sync": "2023-12-01T12:00:00Z",
  "next_sync": "2023-12-01T12:15:00Z",
  "errors": [],
  "warnings": []
}
```

#### GET /api/v1/devices/health/summary
Get health summary for all devices.

### Data Synchronization

#### GET /api/v1/sync/status
Get synchronization status for all devices.

#### POST /api/v1/sync/bulk
Trigger bulk synchronization for all devices.

#### GET /api/v1/sync/history
Get synchronization history.

#### POST /api/v1/sync/retry/{sync_id}
Retry failed synchronization.

### Device Integration

#### GET /api/v1/integrations
Get available device integrations.

#### POST /api/v1/integrations/{integration_type}/auth
Authenticate with device platform.

#### GET /api/v1/integrations/{integration_type}/devices
Get available devices from platform.

#### POST /api/v1/integrations/{integration_type}/import
Import devices from platform.

### Data Analytics

#### GET /api/v1/analytics/device-usage
Get device usage analytics.

#### GET /api/v1/analytics/data-quality
Get data quality metrics.

#### GET /api/v1/analytics/sync-performance
Get synchronization performance metrics.

## Data Models

### Device Model
```python
class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {'schema': 'device_data'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    device_type = Column(String(100), nullable=False)
    device_name = Column(String(200), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    firmware_version = Column(String(50))
    
    # Device capabilities
    capabilities = Column(JSON, default=list)
    
    # Integration settings
    integration_type = Column(String(50), nullable=False)  # api, bluetooth, wifi
    credentials = Column(JSON)  # Encrypted credentials
    sync_settings = Column(JSON, default=dict)
    
    # Status information
    status = Column(String(20), default="registered")  # registered, active, inactive, error
    last_seen = Column(DateTime)
    last_sync = Column(DateTime)
    next_sync = Column(DateTime)
    
    # Health information
    battery_level = Column(Integer)
    signal_strength = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Device Data Model
```python
class DeviceData(Base):
    __tablename__ = "device_data"
    __table_args__ = {'schema': 'device_data'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("device_data.devices.id"), nullable=False)
    
    data_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Data values
    values = Column(JSON, nullable=False)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    quality_score = Column(Float)
    
    # Processing information
    processed = Column(Boolean, default=False)
    validated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Sync History Model
```python
class SyncHistory(Base):
    __tablename__ = "sync_history"
    __table_args__ = {'schema': 'device_data'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("device_data.devices.id"), nullable=False)
    
    sync_type = Column(String(20), nullable=False)  # manual, automatic, bulk
    status = Column(String(20), nullable=False)  # pending, running, completed, failed
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Sync results
    records_processed = Column(Integer, default=0)
    records_synced = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text)
    error_details = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Device Health Model
```python
class DeviceHealth(Base):
    __tablename__ = "device_health"
    __table_args__ = {'schema': 'device_data'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("device_data.devices.id"), nullable=False)
    
    timestamp = Column(DateTime, nullable=False)
    
    # Health metrics
    battery_level = Column(Integer)
    signal_strength = Column(String(20))
    temperature = Column(Float)
    
    # Status information
    status = Column(String(20), nullable=False)
    is_online = Column(Boolean, default=True)
    
    # Error information
    errors = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=device-data-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Device Integration Configuration
FITBIT_CLIENT_ID=your-fitbit-client-id
FITBIT_CLIENT_SECRET=your-fitbit-client-secret
GARMIN_CONSUMER_KEY=your-garmin-consumer-key
GARMIN_CONSUMER_SECRET=your-garmin-consumer-secret
OURA_PERSONAL_ACCESS_TOKEN=your-oura-token

# Sync Configuration
DEFAULT_SYNC_INTERVAL_MINUTES=15
MAX_SYNC_RETRIES=3
SYNC_TIMEOUT_SECONDS=300
BATCH_SIZE=1000

# Data Processing Configuration
DATA_RETENTION_DAYS=1095  # 3 years
DATA_COMPRESSION_ENABLED=true
QUALITY_THRESHOLD=0.8

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8002

# Security Configuration
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key
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

EXPOSE 8004

CMD ["uvicorn", "apps.device_data.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

### Docker Compose
```yaml
device-data-service:
  build:
    context: .
    dockerfile: apps/device_data/Dockerfile
  ports:
    - "8004:8004"
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
    test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_devices.py
import pytest
from fastapi.testclient import TestClient
from apps.device_data.main import app

client = TestClient(app)

def test_register_device():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "device_type": "fitbit_charge_5",
        "device_name": "My Fitbit",
        "manufacturer": "Fitbit",
        "model": "Charge 5",
        "serial_number": "FB123456789",
        "integration_type": "api"
    }
    response = client.post("/api/v1/devices", json=data, headers=headers)
    assert response.status_code == 201
    assert "device_id" in response.json()

def test_get_devices():
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v1/devices", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Integration Tests
```python
# tests/integration/test_sync.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_device_sync_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register device
        device_data = {
            "device_type": "fitbit_charge_5",
            "device_name": "Test Fitbit",
            "integration_type": "api"
        }
        response = await ac.post("/api/v1/devices", json=device_data)
        assert response.status_code == 201
        device_id = response.json()["device_id"]
        
        # Trigger sync
        response = await ac.post(f"/api/v1/devices/{device_id}/sync")
        assert response.status_code == 202
        
        # Check sync status
        response = await ac.get(f"/api/v1/devices/{device_id}/health")
        assert response.status_code == 200
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "device-data-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "kafka": "connected"
    }
```

### Metrics
- **Device Connectivity**: Number of active devices
- **Sync Performance**: Sync success rates and durations
- **Data Quality**: Data quality scores and validation rates
- **API Performance**: Response times and error rates
- **Storage Usage**: Database and cache usage

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/devices")
async def register_device(device: DeviceCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"Device registration requested by user: {current_user.id}, type: {device.device_type}")
    # ... device registration logic
    logger.info(f"Device registered successfully: {device_id}")
```

## Troubleshooting

### Common Issues

#### 1. Device Authentication Failures
**Symptoms**: Sync failures due to authentication errors
**Solution**: Refresh device tokens and verify credentials

#### 2. Data Sync Issues
**Symptoms**: Missing or incomplete data synchronization
**Solution**: Check device connectivity and API rate limits

#### 3. High Memory Usage
**Symptoms**: Service crashes or slow performance
**Solution**: Optimize data processing and implement cleanup

#### 4. Database Performance
**Symptoms**: Slow queries and timeouts
**Solution**: Optimize indexes and implement data partitioning

### Performance Optimization
- **Data Partitioning**: Partition large datasets by time
- **Caching Strategy**: Cache frequently accessed device data
- **Batch Processing**: Process data in batches for efficiency
- **Connection Pooling**: Optimize database connections

### Security Considerations
1. **Credential Encryption**: Encrypt stored device credentials
2. **Access Control**: Implement proper authorization
3. **Data Privacy**: Ensure data privacy compliance
4. **Audit Logging**: Log all device access and data operations
5. **Token Management**: Secure token storage and rotation

---

## Conclusion

The Device Data Service provides comprehensive device management and data synchronization capabilities for the Personal Health Assistant platform. With support for multiple device types, real-time data collection, and robust synchronization mechanisms, it ensures reliable integration with various health and fitness devices.

For additional support or questions, please refer to the platform documentation or contact the development team. 