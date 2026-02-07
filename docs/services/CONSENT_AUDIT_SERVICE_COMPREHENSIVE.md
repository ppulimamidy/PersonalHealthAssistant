# Consent Audit Service - Comprehensive Documentation

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

The Consent Audit Service provides comprehensive consent management, tracking, and auditing capabilities for the Personal Health Assistant platform. It ensures compliance with healthcare regulations (HIPAA, GDPR) by maintaining detailed audit trails of all consent-related activities, data access, and user permissions.

### Key Responsibilities
- Consent management and tracking
- Audit trail maintenance
- Data access logging
- Compliance reporting
- Consent revocation and updates
- Integration with all platform services
- Regulatory compliance (HIPAA, GDPR)

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   Consent Audit │
│                 │    │   (Traefik)     │    │   Service       │
│ - Web App       │───▶│                 │───▶│                 │
│ - Mobile App    │    │ - Rate Limiting │    │ - Consent Mgmt  │
│ - Admin Panel   │    │ - SSL/TLS       │    │ - Audit Logging │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Consent Data  │
                                              │ - Audit Logs    │
                                              │ - Compliance    │
                                              │   Reports       │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Caching       │
                                              │ - Real-time     │
                                              │   Alerts        │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL for consent data and audit logs
- **Caching**: Redis for real-time alerts and caching
- **Audit Logging**: Comprehensive audit trail system
- **Integration**: Webhook notifications to other services
- **Compliance**: HIPAA and GDPR compliance features

## Features

### 1. Consent Management
- **Consent Collection**: Collect and store user consents
- **Consent Types**: Support for various consent types (data sharing, research, marketing)
- **Consent Updates**: Track consent modifications and updates
- **Consent Revocation**: Handle consent withdrawal requests
- **Granular Permissions**: Fine-grained consent controls

### 2. Audit Trail
- **Data Access Logging**: Log all data access attempts
- **User Activity Tracking**: Track user interactions with data
- **Service Integration Logs**: Log inter-service data sharing
- **Compliance Audits**: Generate compliance audit reports
- **Tamper Detection**: Detect unauthorized modifications

### 3. Compliance Reporting
- **HIPAA Compliance**: Generate HIPAA compliance reports
- **GDPR Compliance**: Generate GDPR compliance reports
- **Data Subject Rights**: Support for data subject requests
- **Breach Notification**: Automated breach detection and notification
- **Retention Policies**: Enforce data retention policies

### 4. Integration & Monitoring
- **Service Integration**: Monitor all platform services
- **Real-time Alerts**: Alert on compliance violations
- **Webhook Notifications**: Notify services of consent changes
- **API Monitoring**: Monitor API access and usage
- **Dashboard Integration**: Provide compliance dashboards

### 5. Security & Privacy
- **Encryption**: Encrypt sensitive consent data
- **Access Control**: Role-based access to audit data
- **Data Anonymization**: Anonymize audit logs for reporting
- **Secure Storage**: Secure storage of consent records
- **Audit Integrity**: Ensure audit log integrity

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and real-time alerts

### Security & Compliance
- **Cryptography**: Python cryptography library
- **JWT**: JSON Web Tokens for authentication
- **OAuth2**: OAuth2 integration for secure access
- **Audit Logging**: Custom audit logging framework

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **httpx**: Async HTTP client
- **PyYAML**: Configuration management
- **python-dateutil**: Date and time utilities

## API Endpoints

### Consent Management

#### POST /api/v1/consents
Create a new consent record.

**Request Body:**
```json
{
  "user_id": "uuid",
  "consent_type": "data_sharing",
  "scope": ["health_data", "analytics"],
  "duration": "permanent",
  "revocable": true,
  "description": "Consent to share health data for analytics"
}
```

**Response:**
```json
{
  "consent_id": "uuid",
  "user_id": "uuid",
  "consent_type": "data_sharing",
  "status": "active",
  "created_at": "2023-12-01T12:00:00Z",
  "expires_at": null
}
```

#### GET /api/v1/consents
Get user consents with filtering.

**Query Parameters:**
- `user_id`: User ID
- `consent_type`: Type of consent
- `status`: Consent status
- `limit`: Number of records
- `offset`: Pagination offset

#### GET /api/v1/consents/{consent_id}
Get specific consent details.

#### PUT /api/v1/consents/{consent_id}
Update consent record.

#### DELETE /api/v1/consents/{consent_id}
Revoke consent.

### Audit Logging

#### POST /api/v1/audit-logs
Create audit log entry.

**Request Body:**
```json
{
  "user_id": "uuid",
  "action": "data_access",
  "resource": "health_records",
  "service": "medical_records",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "record_id": "uuid",
    "access_type": "read"
  }
}
```

#### GET /api/v1/audit-logs
Get audit logs with filtering.

**Query Parameters:**
- `user_id`: User ID
- `action`: Action type
- `service`: Service name
- `start_date`: Start date
- `end_date`: End date
- `limit`: Number of records
- `offset`: Pagination offset

#### GET /api/v1/audit-logs/{log_id}
Get specific audit log details.

### Compliance Reporting

#### GET /api/v1/compliance/hipaa
Generate HIPAA compliance report.

**Query Parameters:**
- `start_date`: Report start date
- `end_date`: Report end date
- `format`: Report format (json, csv, pdf)

#### GET /api/v1/compliance/gdpr
Generate GDPR compliance report.

#### GET /api/v1/compliance/data-subject/{user_id}
Generate data subject report for GDPR compliance.

#### POST /api/v1/compliance/data-subject-request
Submit data subject request (GDPR).

### Data Access Monitoring

#### GET /api/v1/monitoring/data-access
Get data access statistics.

#### GET /api/v1/monitoring/consent-violations
Get consent violation alerts.

#### POST /api/v1/monitoring/alerts
Create compliance alert.

### Webhooks

#### POST /api/v1/webhooks/consent-updates
Receive consent update notifications.

#### POST /api/v1/webhooks/data-access
Receive data access notifications.

## Data Models

### Consent Model
```python
class Consent(Base):
    __tablename__ = "consents"
    __table_args__ = {'schema': 'consent_audit'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    consent_type = Column(String(50), nullable=False)
    scope = Column(JSON, nullable=False)
    duration = Column(String(20), nullable=False)
    revocable = Column(Boolean, default=True)
    description = Column(Text)
    
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
```

### Audit Log Model
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'schema': 'consent_audit'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    action = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=False)
    service = Column(String(50), nullable=False)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    details = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Compliance Report Model
```python
class ComplianceReport(Base):
    __tablename__ = "compliance_reports"
    __table_args__ = {'schema': 'consent_audit'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    report_type = Column(String(20), nullable=False)  # hipaa, gdpr
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    data = Column(JSON, nullable=False)
    status = Column(String(20), default="generated")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=consent-audit-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001

# Compliance Configuration
RETENTION_DAYS=2555  # 7 years for HIPAA
GDPR_RETENTION_DAYS=1095  # 3 years
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key
AUDIT_LOG_ENCRYPTION_KEY=your-audit-encryption-key

# Alert Configuration
ALERT_WEBHOOK_URL=https://your-webhook-url.com
ALERT_EMAIL=compliance@yourdomain.com

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

EXPOSE 8003

CMD ["uvicorn", "apps.consent_audit.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Docker Compose
```yaml
consent-audit-service:
  build:
    context: .
    dockerfile: apps/consent_audit/Dockerfile
  ports:
    - "8003:8003"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
  depends_on:
    - postgres
    - redis
    - auth-service
    - user-profile-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_consent.py
import pytest
from fastapi.testclient import TestClient
from apps.consent_audit.main import app

client = TestClient(app)

def test_create_consent():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "consent_type": "data_sharing",
        "scope": ["health_data"],
        "duration": "permanent"
    }
    response = client.post("/api/v1/consents", json=data, headers=headers)
    assert response.status_code == 201
    assert "consent_id" in response.json()

def test_audit_log_creation():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "action": "data_access",
        "resource": "health_records",
        "service": "medical_records"
    }
    response = client.post("/api/v1/audit-logs", json=data, headers=headers)
    assert response.status_code == 201
```

### Integration Tests
```python
# tests/integration/test_compliance.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_hipaa_compliance_report():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/compliance/hipaa?start_date=2023-01-01&end_date=2023-12-31")
        assert response.status_code == 200
        assert "compliance_data" in response.json()
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "consent-audit-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "compliance_status": "compliant"
    }
```

### Metrics
- **Consent Operations**: Number of consent operations
- **Audit Log Volume**: Number of audit log entries
- **Compliance Violations**: Number of compliance violations
- **Data Access Attempts**: Number of data access attempts
- **Report Generation**: Compliance report generation metrics

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/consents")
async def create_consent(consent: ConsentCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"Consent creation requested by user: {current_user.id}")
    # ... consent creation logic
    logger.info(f"Consent created: {consent_id}")
```

## Troubleshooting

### Common Issues

#### 1. Audit Log Performance
**Symptoms**: Slow audit log queries
**Solution**: Implement audit log partitioning and indexing

#### 2. Compliance Report Generation
**Symptoms**: Report generation failures
**Solution**: Check data availability and report configuration

#### 3. Consent Synchronization
**Symptoms**: Inconsistent consent states
**Solution**: Implement consent synchronization mechanisms

#### 4. Data Retention Issues
**Symptoms**: Data retention policy violations
**Solution**: Implement automated data cleanup processes

### Performance Optimization
- **Audit Log Partitioning**: Partition audit logs by date
- **Indexing Strategy**: Optimize database indexes for audit queries
- **Caching**: Cache frequently accessed consent data
- **Batch Processing**: Process audit logs in batches

### Security Considerations
1. **Audit Log Integrity**: Ensure audit logs cannot be tampered with
2. **Data Encryption**: Encrypt sensitive consent and audit data
3. **Access Control**: Implement strict access controls for audit data
4. **Compliance Monitoring**: Monitor for compliance violations
5. **Data Retention**: Enforce data retention policies

---

## Conclusion

The Consent Audit Service provides comprehensive consent management and audit capabilities for the Personal Health Assistant platform. With robust compliance features, detailed audit trails, and regulatory compliance support, it ensures the platform meets healthcare privacy and security requirements.

For additional support or questions, please refer to the platform documentation or contact the development team. 