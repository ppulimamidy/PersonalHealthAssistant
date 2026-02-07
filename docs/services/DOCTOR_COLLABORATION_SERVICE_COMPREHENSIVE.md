# Doctor Collaboration Service - Comprehensive Documentation

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

The Doctor Collaboration Service facilitates seamless collaboration between healthcare providers, patients, and the Personal Health Assistant platform. It enables secure communication, care coordination, treatment planning, and shared decision-making while maintaining HIPAA compliance and data security.

### Key Responsibilities
- Provider-patient communication
- Care coordination and treatment planning
- Secure messaging and file sharing
- Appointment scheduling and management
- Clinical decision support integration
- Team collaboration and case management
- Integration with medical records and analytics

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   Doctor Collab │
│                 │    │   (Traefik)     │    │   Service       │
│ - Provider App  │───▶│                 │───▶│                 │
│ - Patient App   │    │ - Rate Limiting │    │ - Messaging     │
│ - Admin Panel   │    │ - SSL/TLS       │    │ - Coordination  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Messages      │
                                              │ - Appointments  │
                                              │ - Care Plans    │
                                              │ - Team Data     │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Real-time     │
                                              │   Messaging     │
                                              │ - Notifications │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL for messages, appointments, and care data
- **Caching**: Redis for real-time messaging and notifications
- **Real-time Communication**: WebSocket support for live messaging
- **File Management**: Secure file upload and sharing
- **Integration**: Medical records, analytics, and AI insights

## Features

### 1. Secure Messaging
- **Provider-Patient Communication**: Secure messaging between providers and patients
- **Team Messaging**: Multi-provider team communication
- **Message Encryption**: End-to-end encryption for sensitive communications
- **Message Threading**: Organized conversation threads
- **File Attachments**: Secure file sharing (images, documents, reports)
- **Read Receipts**: Message delivery and read status tracking

### 2. Care Coordination
- **Care Team Management**: Manage care teams and roles
- **Treatment Planning**: Collaborative treatment plan creation
- **Progress Tracking**: Track patient progress and outcomes
- **Care Handoffs**: Smooth transitions between providers
- **Clinical Guidelines**: Integration with evidence-based guidelines
- **Decision Support**: AI-powered clinical decision support

### 3. Appointment Management
- **Scheduling**: Flexible appointment scheduling
- **Calendar Integration**: Provider calendar management
- **Reminders**: Automated appointment reminders
- **Rescheduling**: Easy appointment rescheduling
- **Video Consultations**: Integration with telemedicine platforms
- **Waitlist Management**: Manage appointment waitlists

### 4. Clinical Collaboration
- **Case Management**: Comprehensive case management tools
- **Shared Notes**: Collaborative clinical documentation
- **Treatment Reviews**: Multi-provider treatment reviews
- **Clinical Alerts**: Real-time clinical alerts and notifications
- **Evidence Integration**: Integration with medical literature
- **Outcome Tracking**: Track treatment outcomes and quality metrics

### 5. Integration & Analytics
- **Medical Records Integration**: Seamless EHR integration
- **Analytics Integration**: Patient analytics and insights
- **AI Insights**: AI-powered clinical insights and recommendations
- **Reporting**: Clinical collaboration reports and metrics
- **Compliance**: HIPAA-compliant data handling and audit trails

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Real-time messaging and caching

### Real-time Communication
- **WebSockets**: Real-time bidirectional communication
- **Redis Pub/Sub**: Message broadcasting and notifications
- **AsyncIO**: Asynchronous event handling

### File Management
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **Pillow**: Image processing and validation

### Additional Libraries
- **httpx**: Async HTTP client
- **python-jose**: JWT token handling
- **passlib**: Password hashing
- **email-validator**: Email validation
- **python-dateutil**: Date and time utilities

## API Endpoints

### Messaging

#### POST /api/v1/messages
Send a new message.

**Request Body:**
```json
{
  "recipient_id": "uuid",
  "subject": "Treatment Update",
  "content": "Patient shows significant improvement...",
  "message_type": "clinical",
  "priority": "normal",
  "attachments": [
    {
      "file_name": "lab_results.pdf",
      "file_type": "application/pdf",
      "file_size": 1024000
    }
  ]
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "sender_id": "uuid",
  "recipient_id": "uuid",
  "subject": "Treatment Update",
  "content": "Patient shows significant improvement...",
  "status": "sent",
  "created_at": "2023-12-01T12:00:00Z"
}
```

#### GET /api/v1/messages
Get messages with filtering.

**Query Parameters:**
- `conversation_id`: Conversation ID
- `sender_id`: Sender ID
- `recipient_id`: Recipient ID
- `message_type`: Type of message
- `status`: Message status
- `limit`: Number of records
- `offset`: Pagination offset

#### GET /api/v1/messages/{message_id}
Get specific message details.

#### PUT /api/v1/messages/{message_id}
Update message (mark as read, etc.).

#### DELETE /api/v1/messages/{message_id}
Delete message.

### Conversations

#### GET /api/v1/conversations
Get user conversations.

#### POST /api/v1/conversations
Create new conversation.

#### GET /api/v1/conversations/{conversation_id}
Get conversation details and messages.

#### PUT /api/v1/conversations/{conversation_id}
Update conversation settings.

### Care Teams

#### GET /api/v1/care-teams
Get care teams for user.

#### POST /api/v1/care-teams
Create new care team.

**Request Body:**
```json
{
  "name": "Diabetes Care Team",
  "description": "Multidisciplinary diabetes care team",
  "members": [
    {
      "user_id": "uuid",
      "role": "primary_care",
      "permissions": ["read", "write", "admin"]
    }
  ]
}
```

#### GET /api/v1/care-teams/{team_id}
Get care team details.

#### PUT /api/v1/care-teams/{team_id}
Update care team.

#### POST /api/v1/care-teams/{team_id}/members
Add member to care team.

#### DELETE /api/v1/care-teams/{team_id}/members/{member_id}
Remove member from care team.

### Appointments

#### GET /api/v1/appointments
Get appointments with filtering.

#### POST /api/v1/appointments
Schedule new appointment.

**Request Body:**
```json
{
  "patient_id": "uuid",
  "provider_id": "uuid",
  "appointment_type": "consultation",
  "scheduled_at": "2023-12-15T14:00:00Z",
  "duration_minutes": 30,
  "notes": "Follow-up consultation",
  "location": "virtual"
}
```

#### GET /api/v1/appointments/{appointment_id}
Get appointment details.

#### PUT /api/v1/appointments/{appointment_id}
Update appointment.

#### DELETE /api/v1/appointments/{appointment_id}
Cancel appointment.

### Care Plans

#### GET /api/v1/care-plans
Get care plans for patient.

#### POST /api/v1/care-plans
Create new care plan.

**Request Body:**
```json
{
  "patient_id": "uuid",
  "title": "Diabetes Management Plan",
  "description": "Comprehensive diabetes care plan",
  "goals": [
    {
      "description": "Maintain HbA1c below 7%",
      "target_value": 7.0,
      "unit": "%"
    }
  ],
  "interventions": [
    {
      "type": "medication",
      "description": "Metformin 500mg twice daily",
      "frequency": "twice_daily"
    }
  ]
}
```

#### GET /api/v1/care-plans/{plan_id}
Get care plan details.

#### PUT /api/v1/care-plans/{plan_id}
Update care plan.

#### POST /api/v1/care-plans/{plan_id}/progress
Add progress update.

### File Management

#### POST /api/v1/files/upload
Upload file for sharing.

#### GET /api/v1/files/{file_id}
Download file.

#### DELETE /api/v1/files/{file_id}
Delete file.

### WebSocket Endpoints

#### WS /api/v1/ws/messages
Real-time messaging WebSocket.

#### WS /api/v1/ws/notifications
Real-time notifications WebSocket.

## Data Models

### Message Model
```python
class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {'schema': 'doctor_collaboration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    sender_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    subject = Column(String(200))
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="general")
    priority = Column(String(20), default="normal")
    
    status = Column(String(20), default="sent")
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Conversation Model
```python
class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {'schema': 'doctor_collaboration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(200))
    conversation_type = Column(String(20), default="direct")
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Care Team Model
```python
class CareTeam(Base):
    __tablename__ = "care_teams"
    __table_args__ = {'schema': 'doctor_collaboration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Appointment Model
```python
class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = {'schema': 'doctor_collaboration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    appointment_type = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    
    status = Column(String(20), default="scheduled")
    notes = Column(Text)
    location = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=doctor-collaboration-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001

# File Storage Configuration
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=["pdf", "jpg", "png", "doc", "docx"]

# Messaging Configuration
MESSAGE_RETENTION_DAYS=2555  # 7 years
MAX_MESSAGE_LENGTH=10000

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

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8004

CMD ["uvicorn", "apps.doctor_collaboration.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

### Docker Compose
```yaml
doctor-collaboration-service:
  build:
    context: .
    dockerfile: apps/doctor_collaboration/Dockerfile
  ports:
    - "8004:8004"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002
    - USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
  volumes:
    - ./uploads:/app/uploads
  depends_on:
    - postgres
    - redis
    - auth-service
    - medical-records-service
    - user-profile-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_messaging.py
import pytest
from fastapi.testclient import TestClient
from apps.doctor_collaboration.main import app

client = TestClient(app)

def test_send_message():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "recipient_id": "test-recipient-id",
        "subject": "Test Message",
        "content": "This is a test message",
        "message_type": "general"
    }
    response = client.post("/api/v1/messages", json=data, headers=headers)
    assert response.status_code == 201
    assert "message_id" in response.json()

def test_create_care_team():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "name": "Test Care Team",
        "description": "Test team description",
        "members": []
    }
    response = client.post("/api/v1/care-teams", json=data, headers=headers)
    assert response.status_code == 201
    assert "team_id" in response.json()
```

### Integration Tests
```python
# tests/integration/test_appointments.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_appointment_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create appointment
        appointment_data = {
            "patient_id": "test-patient-id",
            "provider_id": "test-provider-id",
            "appointment_type": "consultation",
            "scheduled_at": "2023-12-15T14:00:00Z"
        }
        response = await ac.post("/api/v1/appointments", json=appointment_data)
        assert response.status_code == 201
        
        # Get appointments
        response = await ac.get("/api/v1/appointments")
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
        "service": "doctor-collaboration-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "websocket": "active"
    }
```

### Metrics
- **Message Volume**: Number of messages sent/received
- **Appointment Metrics**: Appointment scheduling and completion rates
- **Care Team Activity**: Care team collaboration metrics
- **File Uploads**: File upload volume and types
- **API Performance**: Response times and error rates

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/messages")
async def send_message(message: MessageCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"Message sent by user: {current_user.id} to: {message.recipient_id}")
    # ... message sending logic
    logger.info(f"Message delivered: {message_id}")
```

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Issues
**Symptoms**: Real-time messaging not working
**Solution**: Check WebSocket configuration and Redis connectivity

#### 2. File Upload Failures
**Symptoms**: File upload errors
**Solution**: Check file permissions and storage configuration

#### 3. Message Delivery Issues
**Symptoms**: Messages not being delivered
**Solution**: Check Redis connectivity and message queue

#### 4. Appointment Conflicts
**Symptoms**: Double booking or scheduling conflicts
**Solution**: Implement appointment conflict detection

### Performance Optimization
- **Message Caching**: Cache frequently accessed messages
- **Database Indexing**: Optimize database indexes for queries
- **File Compression**: Compress large files for storage
- **Connection Pooling**: Optimize database connection pooling

### Security Considerations
1. **Message Encryption**: Encrypt sensitive messages
2. **File Security**: Secure file storage and access
3. **Access Control**: Implement role-based access controls
4. **Audit Logging**: Log all collaboration activities
5. **HIPAA Compliance**: Ensure HIPAA compliance for all communications

---

## Conclusion

The Doctor Collaboration Service provides comprehensive collaboration tools for healthcare providers and patients. With secure messaging, care coordination, appointment management, and clinical collaboration features, it enhances the quality of care delivery while maintaining security and compliance standards.

For additional support or questions, please refer to the platform documentation or contact the development team. 