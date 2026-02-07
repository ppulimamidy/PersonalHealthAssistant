# User Profile Service - Comprehensive Documentation

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

The User Profile Service manages comprehensive user profiles, preferences, and personal information for the Personal Health Assistant platform. It provides a centralized repository for user data, preferences, and settings that are used across all other services in the platform.

### Key Responsibilities
- User profile management and storage
- Personal health information management
- User preferences and settings
- Emergency contact management
- Insurance and healthcare provider information
- Privacy settings and data consent management
- Profile synchronization across services

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │ User Profile    │
│                 │    │   (Traefik)     │    │   Service       │
│ - Web App       │───▶│                 │───▶│                 │
│ - Mobile App    │    │ - Rate Limiting │    │ - Profile Mgmt  │
│ - Third-party   │    │ - SSL/TLS       │    │ - Preferences   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - User Profiles │
                                              │ - Preferences   │
                                              │ - Health Info   │
                                              │ - Emergency     │
                                              │   Contacts      │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for profile data caching
- **Authentication**: JWT token validation
- **Validation**: Pydantic models for data validation

## Features

### 1. Profile Management
- **Basic Information**: Name, contact details, demographics
- **Health Information**: Medical history, conditions, medications
- **Emergency Contacts**: Family members, healthcare providers
- **Insurance Information**: Insurance cards, policy details
- **Healthcare Providers**: Primary care, specialists, facilities

### 2. Preferences & Settings
- **Notification Preferences**: Email, SMS, push notifications
- **Privacy Settings**: Data sharing controls, visibility options
- **Language & Regional**: Language preference, timezone, units
- **Accessibility**: Screen reader support, font size, contrast
- **Integration Settings**: Third-party app connections

### 3. Data Management
- **Profile Synchronization**: Real-time updates across services
- **Data Export**: GDPR-compliant data export
- **Data Import**: Bulk data import from external sources
- **Version Control**: Profile change history and audit trails
- **Backup & Recovery**: Automated backup and restore capabilities

### 4. Privacy & Security
- **Data Encryption**: At-rest and in-transit encryption
- **Access Control**: Role-based access to profile data
- **Audit Logging**: Comprehensive access and change logging
- **Consent Management**: Granular consent for data usage
- **Data Anonymization**: Support for anonymized data processing

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching layer
- **Pydantic**: Data validation and serialization

### Additional Libraries
- **httpx**: Async HTTP client for service communication
- **python-multipart**: File upload handling
- **Pillow**: Image processing for profile photos
- **cryptography**: Data encryption utilities

## API Endpoints

### Profile Management

#### GET /api/v1/profile
Get current user's complete profile.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "uuid",
  "basic_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "state": "NY",
      "zip_code": "10001",
      "country": "USA"
    }
  },
  "health_info": {
    "blood_type": "O+",
    "height_cm": 175,
    "weight_kg": 70,
    "allergies": ["peanuts", "penicillin"],
    "medical_conditions": ["hypertension"],
    "medications": ["lisinopril"]
  },
  "emergency_contacts": [
    {
      "id": "uuid",
      "name": "Jane Doe",
      "relationship": "spouse",
      "phone": "+1234567891",
      "email": "jane.doe@example.com"
    }
  ],
  "insurance": {
    "primary": {
      "provider": "Blue Cross Blue Shield",
      "policy_number": "123456789",
      "group_number": "987654321",
      "expiry_date": "2024-12-31"
    }
  },
  "preferences": {
    "notifications": {
      "email": true,
      "sms": false,
      "push": true
    },
    "privacy": {
      "profile_visibility": "private",
      "data_sharing": "minimal"
    },
    "language": "en",
    "timezone": "America/New_York",
    "units": "metric"
  },
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-12-01T12:00:00Z"
}
```

#### PUT /api/v1/profile
Update user profile information.

**Request Body:**
```json
{
  "basic_info": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
  },
  "health_info": {
    "blood_type": "O+",
    "height_cm": 175,
    "weight_kg": 70
  }
}
```

#### PATCH /api/v1/profile/basic-info
Update basic information only.

#### PATCH /api/v1/profile/health-info
Update health information only.

#### PATCH /api/v1/profile/preferences
Update user preferences.

### Emergency Contacts

#### GET /api/v1/profile/emergency-contacts
Get all emergency contacts.

#### POST /api/v1/profile/emergency-contacts
Add new emergency contact.

**Request Body:**
```json
{
  "name": "Jane Doe",
  "relationship": "spouse",
  "phone": "+1234567891",
  "email": "jane.doe@example.com",
  "is_primary": true
}
```

#### PUT /api/v1/profile/emergency-contacts/{contact_id}
Update emergency contact.

#### DELETE /api/v1/profile/emergency-contacts/{contact_id}
Delete emergency contact.

### Insurance Information

#### GET /api/v1/profile/insurance
Get insurance information.

#### POST /api/v1/profile/insurance
Add insurance information.

#### PUT /api/v1/profile/insurance/{insurance_id}
Update insurance information.

#### DELETE /api/v1/profile/insurance/{insurance_id}
Delete insurance information.

### Healthcare Providers

#### GET /api/v1/profile/healthcare-providers
Get healthcare providers.

#### POST /api/v1/profile/healthcare-providers
Add healthcare provider.

#### PUT /api/v1/profile/healthcare-providers/{provider_id}
Update healthcare provider.

#### DELETE /api/v1/profile/healthcare-providers/{provider_id}
Delete healthcare provider.

### Profile Photo

#### POST /api/v1/profile/photo
Upload profile photo.

**Request:**
```
Content-Type: multipart/form-data
photo: <file>
```

#### GET /api/v1/profile/photo
Get profile photo.

#### DELETE /api/v1/profile/photo
Delete profile photo.

### Data Export/Import

#### GET /api/v1/profile/export
Export user data (GDPR compliance).

#### POST /api/v1/profile/import
Import user data from external source.

### Privacy & Consent

#### GET /api/v1/profile/privacy-settings
Get privacy settings.

#### PUT /api/v1/profile/privacy-settings
Update privacy settings.

#### GET /api/v1/profile/consent-history
Get consent history.

#### POST /api/v1/profile/consent
Update consent preferences.

## Data Models

### User Profile Model
```python
class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {'schema': 'user_profile'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Basic Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(10))
    
    # Address Information
    address = Column(JSON)
    
    # Health Information
    blood_type = Column(String(5))
    height_cm = Column(Integer)
    weight_kg = Column(Float)
    allergies = Column(JSON, default=list)
    medical_conditions = Column(JSON, default=list)
    medications = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Emergency Contact Model
```python
class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    __table_args__ = {'schema': 'user_profile'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profile.user_profiles.user_id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255))
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Insurance Information Model
```python
class InsuranceInfo(Base):
    __tablename__ = "insurance_info"
    __table_args__ = {'schema': 'user_profile'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profile.user_profiles.user_id"), nullable=False)
    
    provider = Column(String(100), nullable=False)
    policy_number = Column(String(50), nullable=False)
    group_number = Column(String(50))
    member_id = Column(String(50))
    expiry_date = Column(Date)
    insurance_type = Column(String(50))  # primary, secondary, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### User Preferences Model
```python
class UserPreferences(Base):
    __tablename__ = "user_preferences"
    __table_args__ = {'schema': 'user_profile'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profile.user_profiles.user_id"), nullable=False)
    
    notifications = Column(JSON, default=dict)
    privacy_settings = Column(JSON, default=dict)
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    units = Column(String(20), default="metric")
    accessibility = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# Service Configuration
SERVICE_NAME=user-profile-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_IMAGE_TYPES=["image/jpeg", "image/png", "image/gif"]
UPLOAD_DIR=/app/uploads

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8002

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

### Configuration Files
- **config/settings.py**: Main configuration
- **config/database.py**: Database settings
- **config/security.py**: Security settings
- **config/storage.py**: File storage configuration

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

# Create upload directory
RUN mkdir -p /app/uploads

EXPOSE 8001

CMD ["uvicorn", "apps.user_profile.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose
```yaml
user-profile-service:
  build:
    context: .
    dockerfile: apps/user_profile/Dockerfile
  ports:
    - "8001:8001"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
  volumes:
    - ./uploads:/app/uploads
  depends_on:
    - postgres
    - redis
    - auth-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-profile-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-profile-service
  template:
    metadata:
      labels:
        app: user-profile-service
    spec:
      containers:
      - name: user-profile-service
        image: your-registry/user-profile-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: uploads-pvc
```

## Testing

### Unit Tests
```python
# tests/unit/test_profile.py
import pytest
from fastapi.testclient import TestClient
from apps.user_profile.main import app

client = TestClient(app)

def test_get_profile():
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v1/profile", headers=headers)
    assert response.status_code == 200
    assert "basic_info" in response.json()

def test_update_profile():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "basic_info": {
            "first_name": "John",
            "last_name": "Doe"
        }
    }
    response = client.put("/api/v1/profile", json=data, headers=headers)
    assert response.status_code == 200
```

### Integration Tests
```python
# tests/integration/test_emergency_contacts.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_emergency_contact_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create emergency contact
        contact_data = {
            "name": "Jane Doe",
            "relationship": "spouse",
            "phone": "+1234567891"
        }
        response = await ac.post("/api/v1/profile/emergency-contacts", json=contact_data)
        assert response.status_code == 201
        
        # Get emergency contacts
        response = await ac.get("/api/v1/profile/emergency-contacts")
        assert response.status_code == 200
        assert len(response.json()) > 0
```

### Load Testing
```python
# tests/load/profile_load_test.py
import asyncio
import aiohttp

async def load_test_profile_access():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            headers = {"Authorization": f"Bearer token-{i}"}
            task = session.get("http://localhost:8001/api/v1/profile", headers=headers)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        success_count = sum(1 for r in responses if r.status == 200)
        print(f"Success rate: {success_count/len(responses)*100}%")
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "user-profile-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected"
    }
```

### Metrics
- **Profile Access Rate**: Number of profile views per minute
- **Update Rate**: Number of profile updates per minute
- **Cache Hit Rate**: Redis cache effectiveness
- **Response Time**: Average API response time
- **Error Rate**: Percentage of failed requests

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.get("/api/v1/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    logger.info(f"Profile accessed for user: {current_user.id}")
    # ... profile retrieval logic
    logger.info(f"Profile retrieved successfully for user: {current_user.id}")
```

### Audit Logging
```python
async def log_profile_change(user_id: UUID, action: str, details: dict):
    audit_log = ProfileAuditLog(
        user_id=user_id,
        action=action,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    await db.commit()
```

## Troubleshooting

### Common Issues

#### 1. Profile Not Found
**Symptoms**: 404 errors when accessing profile
**Solution**: Check user authentication and profile creation

#### 2. Database Connection Issues
**Symptoms**: 503 Service Unavailable
**Solution**: Verify database connectivity and connection pool settings

#### 3. File Upload Failures
**Symptoms**: 413 Payload Too Large or 400 Bad Request
**Solution**: Check file size limits and allowed file types

#### 4. Cache Inconsistency
**Symptoms**: Stale data in responses
**Solution**: Clear Redis cache and verify cache invalidation logic

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Start service in debug mode
uvicorn apps.user_profile.main:app --reload --log-level debug
```

### Performance Tuning
- **Database Indexing**: Optimize queries with proper indexes
- **Caching Strategy**: Implement appropriate caching for frequently accessed data
- **Connection Pooling**: Optimize database connection pool settings
- **File Storage**: Use CDN for profile photos and large files

### Security Best Practices
1. **Data Encryption**: Encrypt sensitive profile data
2. **Access Control**: Implement proper authorization checks
3. **Input Validation**: Validate all user inputs
4. **Audit Logging**: Log all profile changes and access
5. **Privacy Compliance**: Ensure GDPR and HIPAA compliance

---

## Conclusion

The User Profile Service provides a comprehensive solution for managing user profiles, preferences, and personal information in the Personal Health Assistant platform. With robust data models, secure API endpoints, and comprehensive testing, it ensures reliable and secure profile management for all users.

For additional support or questions, please refer to the platform documentation or contact the development team. 