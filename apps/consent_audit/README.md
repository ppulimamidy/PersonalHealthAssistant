# Personal Health Assistant - Consent Audit Service

## Overview

The Consent Audit Service is a comprehensive microservice designed to handle consent audit logging, GDPR compliance monitoring, HIPAA validation, and data governance for the Personal Health Assistant platform. This service ensures regulatory compliance and provides detailed audit trails for all consent-related activities.

## Features

### 🔍 **Audit Logging**
- Comprehensive consent audit trail generation
- Data processing audit logging
- User activity tracking with IP and session information
- Risk assessment and severity classification
- Compliance violation detection and logging

### 🛡️ **GDPR Compliance**
- GDPR compliance monitoring and scoring
- Data subject rights management
- Data processing impact assessments (DPIA)
- Breach notification tracking
- GDPR audit trails and reporting

### 🏥 **HIPAA Compliance**
- HIPAA Privacy Rule compliance monitoring
- HIPAA Security Rule validation
- PHI access logging and monitoring
- Business associate agreement tracking
- HIPAA breach notification management

### 📊 **Compliance Reporting**
- Automated compliance score calculation
- Regulatory compliance reports
- Audit summary statistics
- Compliance checklist management
- Action item tracking and recommendations

### 🔐 **Data Subject Rights**
- Right to access personal data
- Right to rectification
- Right to erasure (right to be forgotten)
- Right to data portability
- Right to restrict processing
- Right to object to processing
- Right to withdraw consent

## Architecture

### Service Structure
```
apps/consent_audit/
├── main.py                 # FastAPI application entry point
├── models/
│   ├── __init__.py
│   └── audit.py           # Audit models and Pydantic schemas
├── api/
│   ├── __init__.py
│   ├── audit.py           # Audit logging endpoints
│   ├── compliance.py      # Compliance monitoring endpoints
│   ├── consent.py         # Consent management endpoints
│   ├── gdpr.py           # GDPR-specific endpoints
│   └── hipaa.py          # HIPAA-specific endpoints
├── services/
│   ├── __init__.py
│   └── audit_service.py   # Business logic and audit operations
├── agents/                # AI agents for automated compliance
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
├── create_tables.py      # Database migration script
└── README.md            # This file
```

### Database Schema

#### `consent_audit.consent_audit_logs`
- Comprehensive audit log for all consent-related events
- Tracks user actions, compliance status, and risk assessment
- Links to consent records and data subjects

#### `consent_audit.data_processing_audits`
- Detailed logging of data processing activities
- Tracks processing purposes, methods, and compliance
- Monitors third-party data sharing

#### `consent_audit.compliance_reports`
- Regulatory compliance reports and summaries
- Compliance scoring and metrics
- Action items and recommendations

## API Endpoints

### Audit Endpoints (`/api/v1/audit`)
- `POST /logs` - Create audit log entry
- `GET /logs/{audit_id}` - Get specific audit log
- `GET /logs/user/{user_id}` - Get user audit logs
- `GET /logs/my` - Get current user's audit logs
- `GET /violations` - Get compliance violations
- `GET /high-risk` - Get high-risk events
- `POST /processing` - Create data processing audit
- `GET /processing` - Get data processing audits
- `GET /summary` - Get audit summary statistics
- `POST /events/consent` - Log consent event
- `POST /verify` - Verify consent compliance

### Compliance Endpoints (`/api/v1/compliance`)
- `GET /gdpr/status` - Get GDPR compliance status
- `GET /hipaa/status` - Get HIPAA compliance status
- `GET /overall/status` - Get overall compliance status
- `POST /reports` - Create compliance report
- `GET /reports` - Get compliance reports
- `GET /checklist/gdpr` - Get GDPR compliance checklist
- `GET /checklist/hipaa` - Get HIPAA compliance checklist

### Consent Endpoints (`/api/v1/consent`)
- `POST /verify` - Verify consent for data processing
- `GET /status/{user_id}` - Get consent status
- `GET /rights/{user_id}` - Get data subject rights
- `POST /exercise-right` - Exercise data subject right
- `GET /history/{user_id}` - Get consent history

### GDPR Endpoints (`/api/v1/gdpr`)
- `GET /compliance/status` - Get GDPR compliance status
- `GET /data-subject-rights/{user_id}` - Get GDPR rights
- `POST /exercise-right` - Exercise GDPR right
- `GET /data-processing-impact` - Get DPIA
- `GET /breach-notification` - Get breach notification status

### HIPAA Endpoints (`/api/v1/hipaa`)
- `GET /compliance/status` - Get HIPAA compliance status
- `GET /privacy-rule/status` - Get Privacy Rule status
- `GET /security-rule/status` - Get Security Rule status
- `GET /breach-notification` - Get breach notification status
- `GET /phi-access-log` - Get PHI access log
- `GET /business-associates` - Get business associates status

## Installation and Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   cd PersonalHealthAssistant
   ```

2. **Install dependencies**
   ```bash
   cd apps/consent_audit
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/health_assistant"
   export ENVIRONMENT="development"
   ```

4. **Create database tables**
   ```bash
   python create_tables.py
   ```

5. **Run the service**
   ```bash
   uvicorn apps.consent_audit.main:app --host 0.0.0.0 --port 8009 --reload
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t consent-audit-service .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name consent-audit-service \
     -p 8009:8009 \
     -e DATABASE_URL="postgresql://user:password@host:5432/health_assistant" \
     -e ENVIRONMENT="production" \
     consent-audit-service
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` |
| `ALLOWED_HOSTS` | Allowed host headers | `["*"]` |

### Database Configuration

The service requires the following PostgreSQL extensions:
- `uuid-ossp` (for UUID generation)
- `pgcrypto` (for encryption functions)

## Usage Examples

### Creating an Audit Log
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8009/api/v1/audit/logs",
        json={
            "user_id": "user-uuid",
            "event_type": "consent_granted",
            "event_description": "User granted consent for data processing",
            "actor_id": "user-uuid",
            "actor_type": "user",
            "severity": "medium"
        }
    )
```

### Checking GDPR Compliance
```python
response = await client.get(
    "http://localhost:8009/api/v1/gdpr/compliance/status",
    params={"user_id": "user-uuid"}
)
```

### Verifying Consent
```python
response = await client.post(
    "http://localhost:8009/api/v1/consent/verify",
    json={
        "user_id": "user-uuid",
        "consent_record_id": "consent-uuid",
        "data_categories": ["health_data", "personal_information"],
        "processing_purpose": "health_monitoring"
    }
)
```

## Monitoring and Health Checks

### Health Check Endpoint
```bash
curl http://localhost:8009/health
```

### Readiness Check
```bash
curl http://localhost:8009/ready
```

### Service Status
```bash
curl http://localhost:8009/api/v1/audit/health
curl http://localhost:8009/api/v1/compliance/health
curl http://localhost:8009/api/v1/consent/health
curl http://localhost:8009/api/v1/gdpr/health
curl http://localhost:8009/api/v1/hipaa/health
```

## Security Features

- **Authentication**: JWT token validation
- **Authorization**: Role-based access control
- **Rate Limiting**: Request rate limiting per endpoint
- **Input Validation**: Pydantic model validation
- **SQL Injection Protection**: Parameterized queries
- **Audit Logging**: Comprehensive activity logging
- **Data Encryption**: Database-level encryption

## Compliance Features

### GDPR Compliance
- ✅ Data subject rights management
- ✅ Consent verification and tracking
- ✅ Data processing impact assessments
- ✅ Breach notification procedures
- ✅ Data portability support
- ✅ Right to erasure implementation

### HIPAA Compliance
- ✅ Privacy Rule compliance monitoring
- ✅ Security Rule validation
- ✅ PHI access logging
- ✅ Business associate management
- ✅ Breach notification tracking
- ✅ Minimum necessary standard enforcement

## Testing

### Run Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests with coverage
pytest --cov=apps/consent_audit --cov-report=html
```

### Test Coverage
The service includes comprehensive test coverage for:
- API endpoints
- Business logic
- Database operations
- Compliance checks
- Error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Roadmap

### Planned Features
- [ ] Real-time compliance monitoring dashboard
- [ ] Automated compliance reporting
- [ ] Integration with external compliance tools
- [ ] Advanced risk assessment algorithms
- [ ] Machine learning for anomaly detection
- [ ] Multi-tenant support
- [ ] API rate limiting and throttling
- [ ] Advanced audit trail visualization

### Future Enhancements
- [ ] Blockchain-based audit trails
- [ ] AI-powered compliance recommendations
- [ ] Integration with regulatory APIs
- [ ] Advanced data anonymization
- [ ] Real-time compliance alerts
- [ ] Automated remediation workflows 