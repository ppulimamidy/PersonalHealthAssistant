# User Profile Service

## Overview

The User Profile Service is a comprehensive microservice for managing user profiles in the Personal Health Assistant platform. It provides complete profile management functionality including personal information, preferences, privacy settings, and health attributes.

## Features

### Core Profile Management
- **Personal Information**: Name, contact details, demographics
- **Health Attributes**: Physical measurements, vital signs, health goals
- **Preferences**: Notification settings, UI preferences, privacy controls
- **Privacy Settings**: Data sharing controls, consent management
- **Profile Completion**: Tracking and guidance for profile completion

### Key Capabilities
- ✅ Complete CRUD operations for user profiles
- ✅ Profile validation and sanitization
- ✅ Profile completion tracking and guidance
- ✅ Privacy controls and data sharing management
- ✅ Health attributes and goals management
- ✅ Data export/import functionality
- ✅ Comprehensive audit logging
- ✅ Rate limiting and security features

## Architecture

### Service Structure
```
apps/user_profile/
├── api/                    # API endpoints
│   ├── profile.py         # Main profile endpoints
│   ├── preferences.py     # Preferences endpoints
│   ├── privacy.py         # Privacy settings endpoints
│   └── health_attributes.py # Health attributes endpoints
├── models/                # Data models
│   ├── profile.py         # Profile model
│   ├── preferences.py     # Preferences model
│   ├── privacy_settings.py # Privacy settings model
│   └── health_attributes.py # Health attributes model
├── services/              # Business logic
│   ├── profile_service.py # Main profile service
│   ├── preferences_service.py # Preferences service
│   ├── privacy_service.py # Privacy service
│   └── health_attributes_service.py # Health attributes service
├── tests/                 # Test suite
├── main.py               # FastAPI application
├── Dockerfile            # Container configuration
└── requirements.txt      # Python dependencies
```

### Data Models

#### Profile Model
- Personal information (name, contact, demographics)
- Address information
- Health information (blood type, measurements)
- Professional information
- Profile completion tracking

#### Preferences Model
- Notification preferences
- UI preferences (theme, language, units)
- Privacy preferences
- Health tracking preferences
- Custom preferences

#### Privacy Settings Model
- Data sharing controls
- Provider sharing settings
- Research and analytics settings
- Third-party sharing settings
- Data retention settings

#### Health Attributes Model
- Physical measurements
- Vital signs baseline
- Health goals
- Activity goals
- Risk factors and conditions

## API Endpoints

### Profile Management
```
POST   /api/v1/user-profile/profile/          # Create profile
GET    /api/v1/user-profile/profile/me        # Get my profile
PUT    /api/v1/user-profile/profile/me        # Update my profile
DELETE /api/v1/user-profile/profile/me        # Delete my profile
GET    /api/v1/user-profile/profile/me/summary # Get profile summary
POST   /api/v1/user-profile/profile/me/validate # Validate profile data
GET    /api/v1/user-profile/profile/me/export # Export profile data
POST   /api/v1/user-profile/profile/me/import # Import profile data
GET    /api/v1/user-profile/profile/me/completion # Get completion status
```

### Preferences Management
```
GET    /api/v1/user-profile/preferences/me    # Get my preferences
PUT    /api/v1/user-profile/preferences/me    # Update my preferences
PUT    /api/v1/user-profile/preferences/notifications # Update notifications
PUT    /api/v1/user-profile/preferences/privacy # Update privacy preferences
```

### Privacy Settings
```
GET    /api/v1/user-profile/privacy/me        # Get my privacy settings
PUT    /api/v1/user-profile/privacy/me        # Update my privacy settings
POST   /api/v1/user-profile/privacy/consent   # Grant consent
DELETE /api/v1/user-profile/privacy/consent   # Revoke consent
```

### Health Attributes
```
GET    /api/v1/user-profile/health-attributes/me # Get my health attributes
PUT    /api/v1/user-profile/health-attributes/me # Update my health attributes
POST   /api/v1/user-profile/health-attributes/goals # Set health goals
GET    /api/v1/user-profile/health-attributes/summary # Get health summary
```

## Service Integration

### Authentication Flow
1. **User Registration**: Auth service creates user → Profile service creates default profile
2. **Profile Access**: JWT token validation → Profile service returns profile data
3. **Profile Updates**: Token validation → Profile service updates data → Event publishing
4. **Data Sharing**: Profile service provides privacy settings to other services

### Event-Driven Architecture
- **user.created**: Auth service → Profile service creates default profile
- **profile.updated**: Profile service → Other services update their data
- **privacy.changed**: Profile service → Other services adjust data access
- **user.deleted**: Auth service → Profile service archives data

### Cross-Service Communication
- **Synchronous**: Direct API calls for immediate data needs
- **Asynchronous**: Kafka events for background processing
- **Shared Database**: Consistent data across services
- **JWT Tokens**: Secure authentication and authorization

## Service Integration with Auth Service

The User Profile Service is designed to work seamlessly with the Auth Service:

- **JWT Validation**: All protected endpoints require a valid JWT issued by the Auth Service in the `Authorization: Bearer <token>` header. The service validates the token and extracts the user ID for profile operations.
- **User Creation on Registration**: When a new user registers via the Auth Service, the User Profile Service can be triggered to create a default profile for the user. This can be done via a direct API call from the Auth Service to the User Profile Service, or via an event-driven mechanism (e.g., Kafka event `user.created`).
- **Cross-Service Communication**: The User Profile Service exposes endpoints for profile management that can be called by other services (e.g., Auth, Analytics) as needed. It is recommended to use service-to-service authentication for internal calls.

Example API call from Auth Service to User Profile Service on user registration:

```python
import httpx

async def create_user_profile(user_id, email, token):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://user-profile-service:8001/api/v1/user-profile/profile/",
            json={"user_id": user_id, "email": email},
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
```

See the implementation guide for more details on service integration and event-driven workflows.

## Setup and Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis (for rate limiting)
- Docker (optional)

### Local Development
```bash
# Clone the repository
git clone <repository-url>
cd PersonalHealthAssistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r apps/user_profile/requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/health_assistant"
export REDIS_URL="redis://localhost:6379"

# Run the service
cd apps/user_profile
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker Deployment
```bash
# Build the image
docker build -f apps/user_profile/Dockerfile -t user-profile-service .

# Run the container
docker run -p 8001:8001 \
  -e DATABASE_URL="postgresql+asyncpg://user:password@host/health_assistant" \
  -e REDIS_URL="redis://host:6379" \
  user-profile-service
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f apps/user_profile/kubernetes/

# Check deployment status
kubectl get pods -l app=user-profile-service
kubectl get svc -l app=user-profile-service
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host/database

# Redis
REDIS_URL=redis://host:6379

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Monitoring
ENABLE_OPENTELEMETRY=true
PROMETHEUS_ENABLED=true

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Database Schema
The service requires the following database tables:
- `user_profiles`: Main profile data
- `user_preferences`: User preferences
- `privacy_settings`: Privacy controls
- `health_attributes`: Health-related data

Run the database migrations to create the schema:
```bash
alembic upgrade head
```

## Testing

### Run Tests
```bash
# Run all tests
pytest apps/user_profile/tests/

# Run specific test categories
pytest apps/user_profile/tests/unit/
pytest apps/user_profile/tests/integration/

# Run with coverage
pytest apps/user_profile/tests/ --cov=apps/user_profile --cov-report=html
```

### Test Categories
- **Unit Tests**: Individual service methods
- **Integration Tests**: API endpoints and database operations
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load and stress testing

## Monitoring and Observability

### Health Checks
- **Health Endpoint**: `/health` - Basic service health
- **Readiness Endpoint**: `/ready` - Service readiness for traffic
- **Metrics Endpoint**: `/metrics` - Prometheus metrics

### Metrics
- Request count and latency
- Profile completion rates
- Error rates and types
- Database connection health
- Rate limiting statistics

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking and alerting
- Audit trail for privacy changes

## Security Features

### Authentication & Authorization
- JWT token validation
- Role-based access control
- Session management
- Multi-factor authentication support

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

### Privacy Controls
- Granular data sharing controls
- Consent management
- Data retention policies
- Audit logging

### Rate Limiting
- Request rate limiting
- IP-based blocking
- DDoS protection
- API abuse prevention

## Performance Optimization

### Database Optimization
- Connection pooling
- Query optimization
- Indexing strategy
- Caching layer

### API Optimization
- Response caching
- Pagination support
- Field selection
- Compression

### Scalability
- Horizontal scaling
- Load balancing
- Auto-scaling
- Resource management

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python -c "import asyncpg; print('Database connection OK')"

# Check database schema
psql -d health_assistant -c "\dt user_profiles"
```

#### Redis Connection Issues
```bash
# Check Redis connectivity
redis-cli ping

# Check Redis configuration
redis-cli config get maxmemory
```

#### Service Startup Issues
```bash
# Check logs
docker logs user-profile-service

# Check environment variables
docker exec user-profile-service env | grep DATABASE
```

### Debug Mode
Enable debug mode for detailed logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Contributing

### Development Workflow
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

### Code Standards
- Follow PEP 8 style guide
- Use type hints
- Write comprehensive tests
- Update documentation

### Testing Requirements
- Minimum 80% code coverage
- All tests must pass
- Performance benchmarks
- Security scanning

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review troubleshooting guide
- Contact the development team 