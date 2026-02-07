# Doctor Collaboration Service

A comprehensive microservice for managing doctor-patient collaboration, appointments, secure messaging, and medical consultation management in the Personal Health Assistant platform.

## 🏥 Overview

The Doctor Collaboration Service enables seamless communication and coordination between healthcare providers and patients. It provides a secure, HIPAA-compliant platform for appointment scheduling, messaging, consultations, and notifications.

## 🚀 Features

### Core Functionality
- **Appointment Management**: Schedule, reschedule, and manage appointments
- **Secure Messaging**: HIPAA-compliant messaging between doctors and patients
- **Consultation Management**: Track and manage medical consultations
- **Notification System**: Automated notifications for appointments and messages
- **Conflict Detection**: Intelligent scheduling conflict detection
- **Multi-modal Support**: In-person, telemedicine, phone, and video consultations

### Security & Compliance
- **HIPAA Compliance**: Full compliance with healthcare privacy regulations
- **End-to-end Encryption**: Secure message encryption
- **Audit Logging**: Comprehensive audit trails
- **Access Control**: Role-based access control
- **Data Retention**: Configurable data retention policies

### Integration
- **Auth Service**: User authentication and authorization
- **Medical Records**: Integration with patient medical records
- **User Profile**: Patient and doctor profile management
- **Knowledge Graph**: Medical knowledge integration
- **AI Insights**: AI-powered recommendations

## 🏗️ Architecture

### Service Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Doctor Collaboration Service              │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                  │
│  ├── Appointments API                                       │
│  ├── Messaging API                                          │
│  ├── Consultations API                                      │
│  └── Notifications API                                      │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer                                       │
│  ├── Appointment Service                                    │
│  ├── Messaging Service                                      │
│  ├── Consultation Service                                   │
│  └── Notification Service                                   │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── PostgreSQL Database                                    │
│  ├── Redis Cache                                            │
│  └── File Storage                                           │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Cache**: Redis 5.0.1
- **Authentication**: JWT with HTTPBearer
- **Containerization**: Docker with multi-stage builds
- **API Gateway**: Traefik integration
- **Monitoring**: Prometheus metrics and structured logging

## 📋 API Endpoints

### Appointments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/appointments/` | Create appointment |
| GET | `/api/v1/appointments/` | List appointments |
| GET | `/api/v1/appointments/{id}` | Get appointment |
| PUT | `/api/v1/appointments/{id}` | Update appointment |
| DELETE | `/api/v1/appointments/{id}` | Delete appointment |
| POST | `/api/v1/appointments/{id}/confirm` | Confirm appointment |
| POST | `/api/v1/appointments/{id}/cancel` | Cancel appointment |
| POST | `/api/v1/appointments/{id}/reschedule` | Reschedule appointment |
| GET | `/api/v1/appointments/{id}/conflicts` | Check conflicts |
| GET | `/api/v1/appointments/upcoming/` | Get upcoming appointments |
| GET | `/api/v1/appointments/overdue/` | Get overdue appointments |

### Messaging
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/messaging/` | Send message |
| GET | `/api/v1/messaging/` | List messages |
| GET | `/api/v1/messaging/{id}` | Get message |
| PUT | `/api/v1/messaging/{id}` | Update message |
| DELETE | `/api/v1/messaging/{id}` | Delete message |
| POST | `/api/v1/messaging/{id}/read` | Mark as read |
| GET | `/api/v1/messaging/threads/` | List message threads |
| GET | `/api/v1/messaging/unread/` | Get unread messages |

### Consultations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/consultations/` | Create consultation |
| GET | `/api/v1/consultations/` | List consultations |
| GET | `/api/v1/consultations/{id}` | Get consultation |
| PUT | `/api/v1/consultations/{id}` | Update consultation |
| DELETE | `/api/v1/consultations/{id}` | Delete consultation |
| POST | `/api/v1/consultations/{id}/start` | Start consultation |
| POST | `/api/v1/consultations/{id}/complete` | Complete consultation |
| POST | `/api/v1/consultations/{id}/notes` | Add consultation notes |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/notifications/` | Create notification |
| GET | `/api/v1/notifications/` | List notifications |
| GET | `/api/v1/notifications/{id}` | Get notification |
| PUT | `/api/v1/notifications/{id}` | Update notification |
| DELETE | `/api/v1/notifications/{id}` | Delete notification |
| POST | `/api/v1/notifications/{id}/mark-read` | Mark as read |
| GET | `/api/v1/notifications/unread/` | Get unread notifications |

## 🗄️ Data Models

### Appointment
```python
class Appointment(Base):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    appointment_type: AppointmentType
    status: AppointmentStatus
    scheduled_date: datetime
    duration_minutes: int
    timezone: str
    location: Optional[str]
    modality: str
    notes: Optional[str]
    # ... additional fields
```

### Message
```python
class Message(Base):
    id: UUID
    sender_id: UUID
    recipient_id: UUID
    message_type: MessageType
    priority: MessagePriority
    status: MessageStatus
    content: str
    subject: Optional[str]
    attachments: List[Dict]
    # ... additional fields
```

### Consultation
```python
class Consultation(Base):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    consultation_type: ConsultationType
    status: ConsultationStatus
    priority: ConsultationPriority
    scheduled_date: datetime
    duration_minutes: int
    chief_complaint: Optional[str]
    symptoms: List[str]
    # ... additional fields
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd PersonalHealthAssistant
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Install dependencies**
```bash
pip install -r apps/doctor_collaboration/requirements.txt
```

4. **Run database migrations**
```bash
# Create tables
python apps/doctor_collaboration/create_tables.py
```

5. **Start the service**
```bash
cd apps/doctor_collaboration
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. **Build the image**
```bash
docker build -f apps/doctor_collaboration/Dockerfile -t doctor-collaboration .
```

2. **Run with Docker Compose**
```bash
docker-compose up doctor-collaboration
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant

# Redis
REDIS_URL=redis://localhost:6379

# JWT Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
MEDICAL_RECORDS_SERVICE_URL=http://medical-records:8000
USER_PROFILE_SERVICE_URL=http://user-profile:8000

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=INFO
```

### Traefik Configuration
The service is configured to work with Traefik for routing and load balancing. Configuration is located in `traefik/config/doctor-collaboration.yml`.

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest apps/doctor_collaboration/tests/unit/

# Integration tests
pytest apps/doctor_collaboration/tests/integration/

# All tests with coverage
pytest apps/doctor_collaboration/tests/ --cov=apps.doctor_collaboration --cov-report=html
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Create appointment
curl -X POST http://localhost:8000/api/v1/appointments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "uuid",
    "doctor_id": "uuid",
    "appointment_type": "consultation",
    "scheduled_date": "2025-08-05T10:00:00Z",
    "duration_minutes": 30
  }'
```

## 📊 Monitoring

### Health Checks
- **Health Endpoint**: `GET /health`
- **Readiness Endpoint**: `GET /ready`
- **Metrics Endpoint**: `GET /metrics`

### Metrics
The service exposes Prometheus metrics for:
- Request counts and durations
- Appointment statistics
- Message delivery rates
- Error rates
- Database connection status

### Logging
Structured logging with the following levels:
- **INFO**: Normal operations
- **WARNING**: Potential issues
- **ERROR**: Errors that need attention
- **DEBUG**: Detailed debugging information

## 🔒 Security

### Authentication
- JWT-based authentication
- Role-based access control
- Token expiration and refresh

### Authorization
- Patient access: Own appointments and messages
- Doctor access: Own appointments and patient messages
- Admin access: Full system access

### Data Protection
- End-to-end message encryption
- HIPAA-compliant data handling
- Audit logging for all operations
- Configurable data retention

## 🔄 Integration

### Service Dependencies
- **Auth Service**: User authentication and authorization
- **Medical Records**: Patient medical data access
- **User Profile**: User profile information
- **Knowledge Graph**: Medical knowledge integration

### External Integrations
- **Email Service**: Appointment notifications
- **SMS Service**: Text message notifications
- **Calendar Service**: Calendar integration
- **Video Service**: Telemedicine support

## 🚀 Deployment

### Production Deployment
1. **Build production image**
```bash
docker build -f apps/doctor_collaboration/Dockerfile -t doctor-collaboration:latest .
```

2. **Deploy with Kubernetes**
```bash
kubectl apply -f apps/doctor_collaboration/kubernetes/
```

3. **Configure Traefik**
```bash
kubectl apply -f traefik/config/doctor-collaboration.yml
```

### Environment-Specific Configurations
- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: High-availability production deployment

## 📈 Performance

### Optimization Strategies
- Database connection pooling
- Redis caching for frequently accessed data
- Asynchronous processing for notifications
- Rate limiting to prevent abuse
- Circuit breaker pattern for external services

### Scalability
- Horizontal scaling with load balancing
- Database read replicas
- Redis cluster for high availability
- Microservices architecture

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Issues**
```bash
# Check database connectivity
python -c "from common.database.connection import get_db; print('DB OK')"
```

2. **Authentication Issues**
```bash
# Verify JWT token
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/appointments/
```

3. **Service Integration Issues**
```bash
# Check service health
curl http://auth-service:8000/health
curl http://medical-records:8000/health
```

### Debug Mode
Enable debug mode for detailed logging:
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

## 📚 Documentation

### API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### Additional Resources
- [Architecture Documentation](../docs/ARCHITECTURE.md)
- [API Specification](../docs/API_SPECIFICATION.md)
- [Security Guide](../docs/SECURITY_GUIDE.md)
- [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)

## 🤝 Contributing

### Development Workflow
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

### Code Standards
- Follow PEP 8 style guide
- Use type hints
- Add docstrings
- Write unit tests
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check the docs folder
- **Issues**: Create GitHub issues
- **Discussions**: Use GitHub discussions
- **Email**: Contact the development team

### Emergency Contacts
- **On-call Engineer**: [Contact Information]
- **System Administrator**: [Contact Information]
- **Security Team**: [Contact Information]

---

**Version**: 1.0.0  
**Last Updated**: 2025-08-04  
**Status**: Production Ready 