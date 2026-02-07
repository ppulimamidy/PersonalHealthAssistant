# Core Infrastructure Documentation

This document provides comprehensive documentation for the core infrastructure components of the Personal Health Assistant project.

## Overview

The core infrastructure provides the foundation for all services in the Personal Health Assistant application. It includes:

- **Database Connection Management** - Connection pooling and health monitoring
- **Logging Infrastructure** - Structured logging with multiple handlers
- **Base Service Classes** - Common CRUD operations and error handling
- **Authentication Middleware** - JWT-based authentication and authorization
- **Error Handling Middleware** - Centralized error handling and response formatting
- **Monitoring Stack** - Prometheus metrics, Grafana dashboards, and distributed tracing
- **Resilience Patterns** - Circuit breakers, retries, timeouts with metrics
- **Security Middleware** - mTLS, security headers, threat detection
- **Rate Limiting** - Redis-backed rate limiting with configurable limits
- **Feature Flags** - Redis-backed feature flags with multiple evaluation rules

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Core Infrastructure                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Database      │  │    Logging      │  │   Settings   │ │
│  │   Connection    │  │  Infrastructure │  │  Management  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Base Service  │  │ Authentication  │  │    Error     │ │
│  │    Classes      │  │   Middleware    │  │   Handling   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Monitoring    │  │   Resilience    │  │   Security   │ │
│  │     Stack       │  │    Patterns     │  │  Middleware  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Rate Limiting │  │  Feature Flags  │  │   Testing    │ │
│  │   Middleware    │  │     System      │  │  Framework   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘

Monitoring Stack:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Prometheus    │  │     Grafana     │  │      Redis      │
│   (Metrics)     │  │  (Dashboards)   │  │   (Caching)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Components

### 1. Database Connection Management

**Location**: `common/database/connection.py`

**Purpose**: Manages database connections with connection pooling, health monitoring, and async support.

#### Key Features

- **Connection Pooling**: Configurable pool size and overflow settings
- **Health Monitoring**: Automatic health checks and monitoring
- **Async Support**: Both synchronous and asynchronous database operations
- **Session Management**: Automatic session cleanup and error handling

#### Usage

```python
from common.database.connection import get_db_manager, get_session, get_async_session

# Get database manager
db_manager = get_db_manager()

# Synchronous session
with db_manager.get_session() as session:
    # Use session for database operations
    pass

# Asynchronous session
async with db_manager.get_async_session() as session:
    # Use session for async database operations
    pass

# FastAPI dependencies
from common.database.connection import get_db, get_async_db

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    # Use db session
    pass
```

#### Configuration

```python
# Database settings in common/config/settings.py
class DatabaseSettings(BaseModel):
    url: str = "postgresql://postgres:postgres@localhost:5432/health_assistant"
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
```

### 2. Logging Infrastructure

**Location**: `common/utils/logging.py`

**Purpose**: Provides structured logging with multiple handlers, request tracking, and performance monitoring.

#### Key Features

- **Structured Logging**: JSON-formatted logs with context
- **Multiple Handlers**: Console, file, error, and database-specific handlers
- **Request Tracking**: Request ID and user ID context
- **Performance Monitoring**: Request duration and slow request detection
- **Security Logging**: Security events and audit trails

#### Usage

```python
from common.utils.logging import get_logger, log_request, log_error

# Get a logger
logger = get_logger("my_service")

# Log messages
logger.info("Processing request", user_id="123", action="create")
logger.error("Database error", error=str(e), context={"operation": "insert"})

# Log requests
log_request(
    request_id="req-123",
    method="POST",
    url="/api/users",
    status_code=201,
    duration=0.15,
    user_id="user-123"
)

# Log errors
log_error(
    error=exception,
    context={"operation": "user_creation"},
    user_id="user-123"
)
```

#### Configuration

```python
# Logging configuration
setup_logging(
    log_level="INFO",
    enable_console=True,
    enable_file=True,
    enable_json=True,
    max_file_size=10 * 1024 * 1024,  # 10MB
    backup_count=5
)
```

### 3. Base Service Classes

**Location**: `common/services/base.py`

**Purpose**: Provides common CRUD operations, error handling, and service patterns.

#### Key Features

- **Generic CRUD Operations**: Create, read, update, delete with pagination
- **Error Handling**: Standardized error types and responses
- **Type Safety**: Generic types for SQLAlchemy models and Pydantic schemas
- **Filtering and Sorting**: Flexible query building
- **Async Support**: Both sync and async service patterns

#### Usage

```python
from common.services.base import BaseService, ServiceError, NotFoundError

class UserService(BaseService[UserSchema, UserCreate, UserUpdate, UserModel]):
    @property
    def model_class(self):
        return UserModel
    
    @property
    def schema_class(self):
        return UserSchema
    
    @property
    def create_schema_class(self):
        return UserCreate
    
    @property
    def update_schema_class(self):
        return UserUpdate

# Use the service
user_service = UserService()

# Create user
user = await user_service.create(user_data)

# Get user by ID
user = await user_service.get_by_id(user_id)

# Get all users with pagination
users = await user_service.get_all(
    pagination=PaginationModel(page=1, size=20),
    sort=SortModel(field="created_at", order="desc"),
    filters=[FilterModel(field="is_active", operator="eq", value=True)]
)
```

#### Error Types

```python
# Service errors
ServiceError("General service error", "SERVICE_ERROR")
NotFoundError("User", user_id)
ValidationError("Invalid user data", {"email": "Invalid email format"})
DuplicateError("User", "email", "user@example.com")
```

### 4. Authentication Middleware

**Location**: `common/middleware/auth.py`

**Purpose**: Handles JWT token validation, user authentication, and role-based access control.

#### Key Features

- **JWT Token Management**: Access and refresh token creation/validation
- **Role-Based Access Control**: Flexible role checking
- **Request Context**: User ID and request tracking
- **Rate Limiting**: Configurable rate limiting per user/IP
- **CORS Support**: Cross-origin resource sharing configuration

#### Usage

```python
from common.middleware.auth import (
    get_current_user_required,
    require_roles,
    require_admin,
    create_tokens
)

# Protected endpoint
@app.get("/users/me")
async def get_current_user(user: Dict = Depends(get_current_user_required)):
    return user

# Role-based endpoint
@app.get("/admin/users")
async def get_all_users(user: Dict = Depends(require_admin)):
    return {"users": []}

# Create tokens
tokens = create_tokens(
    user_id=user.id,
    email=user.email,
    roles=["user", "admin"]
)
```

#### Dependencies

```python
# Authentication dependencies
get_current_user_required()  # Requires valid token
get_current_user_optional()  # Optional token
require_roles(["admin", "moderator"])  # Requires specific roles
require_admin()  # Requires admin role
require_healthcare_provider()  # Requires healthcare provider role
```

### 5. Error Handling Middleware

**Location**: `common/middleware/error_handling.py`

**Purpose**: Provides centralized error handling and consistent error responses.

#### Key Features

- **Exception Handling**: Catches and handles all types of exceptions
- **Structured Responses**: Consistent error response format
- **Logging Integration**: Automatic error logging with context
- **Security Monitoring**: Security event logging
- **Performance Tracking**: Request duration and performance monitoring

#### Error Response Format

```json
{
  "success": false,
  "error": "Resource not found",
  "error_code": "NOT_FOUND",
  "details": {
    "request_id": "req-123",
    "resource_type": "User",
    "resource_id": "user-456"
  }
}
```

#### Usage

```python
from common.middleware.error_handling import setup_error_handlers

# Setup error handlers for FastAPI app
setup_error_handlers(app)

# Create custom error responses
from common.middleware.error_handling import create_error_response

response = create_error_response(
    message="Validation failed",
    error_code="VALIDATION_ERROR",
    status_code=422,
    details={"field_errors": {"email": "Invalid format"}}
)
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/health_assistant
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
QDRANT_URL=http://localhost:6333
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379

# Security
SECURITY_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
SECURITY_CORS_ALLOW_CREDENTIALS=true

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
ENABLE_TRACING=true
```

### Settings Structure

```python
# Main settings class
class Settings(BaseModel):
    database: DatabaseSettings
    auth: AuthSettings
    external_services: ExternalServicesSettings
    ai: AISettings
    storage: StorageSettings
    monitoring: MonitoringSettings
    security: SecuritySettings
    development: DevelopmentSettings
    
    # Application settings
    app_name: str = "Personal Health Assistant"
    app_version: str = "1.0.0"
    
    # API settings
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
```

## Testing

### Running Tests

```bash
# Run all core infrastructure tests
PYTHONPATH=. python tests/test_core_infrastructure.py

# Run with pytest
PYTHONPATH=. pytest tests/test_core_infrastructure.py -v

# Run specific test class
PYTHONPATH=. pytest tests/test_core_infrastructure.py::TestDatabaseConnection -v
```

### Test Coverage

The core infrastructure includes comprehensive tests for:

- Database connection management
- Logging functionality
- Service base classes
- Authentication middleware
- Error handling
- Integration scenarios

## Best Practices

### 1. Database Usage

```python
# ✅ Good: Use context managers for automatic cleanup
with db_manager.get_session() as session:
    # Database operations
    pass

# ❌ Bad: Manual session management
session = db_manager.get_session_factory()()
try:
    # Database operations
    session.commit()
finally:
    session.close()
```

### 2. Logging

```python
# ✅ Good: Use structured logging with context
logger.info("User created", user_id=user.id, email=user.email)

# ❌ Bad: Simple string logging
logger.info(f"User {user.id} created with email {user.email}")
```

### 3. Error Handling

```python
# ✅ Good: Use specific error types
if not user:
    raise NotFoundError("User", user_id)

# ❌ Bad: Generic exceptions
if not user:
    raise Exception("User not found")
```

### 4. Authentication

```python
# ✅ Good: Use dependency injection
@app.get("/protected")
async def protected_endpoint(user: Dict = Depends(get_current_user_required)):
    return {"user": user}

# ❌ Bad: Manual token validation
@app.get("/protected")
async def protected_endpoint(request: Request):
    token = request.headers.get("Authorization")
    # Manual validation...
```

## Monitoring and Observability

### Health Checks

```python
# Database health check
health_status = await db_manager.health_check()

# Pool statistics
pool_stats = db_manager.get_pool_stats()
```

### Monitoring Stack

The application includes a comprehensive monitoring stack with:

#### Prometheus Metrics
- **Location**: `common/utils/opentelemetry_config.py`
- **Purpose**: Collect and expose application metrics
- **Access**: http://localhost:8000/metrics

```python
# Example metrics exposed
REQUEST_COUNT = Counter('request_count', 'Total request count', ['app_name', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['app_name', 'endpoint'])
CIRCUIT_BREAKER_STATE = Gauge('circuit_breaker_state', 'Circuit breaker state', ['service_name'])
```

#### Grafana Dashboards
- **Location**: `monitoring/grafana/provisioning/dashboards/`
- **Purpose**: Visualize metrics and application health
- **Access**: http://localhost:3002 (admin/admin)
- **Auto-provisioned**: FastAPI metrics dashboard included

#### Redis Backend
- **Purpose**: Caching, rate limiting, and feature flags
- **Access**: localhost:6379
- **Services**: Rate limiting, feature flags, session storage

### Resilience Patterns

#### Circuit Breakers
- **Location**: `common/utils/resilience.py`
- **Purpose**: Prevent cascading failures
- **Features**: Configurable failure thresholds, timeout settings, metrics

```python
from common.utils.resilience import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=Exception
)

# Use with async functions
@breaker
async def call_external_service():
    # Service call
    pass
```

#### Retries and Timeouts
- **Location**: `common/utils/resilience.py`
- **Purpose**: Handle transient failures
- **Features**: Exponential backoff, configurable retry counts

```python
from common.utils.resilience import retry_with_backoff

@retry_with_backoff(max_retries=3, base_delay=1)
async def unreliable_operation():
    # Operation that might fail
    pass
```

### Security Middleware

#### mTLS Support
- **Location**: `common/middleware/security.py`
- **Purpose**: Mutual TLS for service-to-service communication
- **Features**: Certificate validation, secure headers

#### Security Headers
- **Location**: `common/middleware/security.py`
- **Purpose**: Add security headers to all responses
- **Headers**: HSTS, CSP, X-Frame-Options, etc.

#### Threat Detection
- **Location**: `common/middleware/security.py`
- **Purpose**: Detect and block suspicious requests
- **Features**: Rate limiting, IP blocking, anomaly detection

### Rate Limiting

#### Redis-Backed Rate Limiting
- **Location**: `common/middleware/rate_limiter.py`
- **Purpose**: Prevent API abuse
- **Features**: Per-user limits, configurable windows, Redis storage

```python
from common.middleware.rate_limiter import RateLimiter

# Apply rate limiting to endpoint
@app.post("/api/login")
@RateLimiter(requests=5, window=60)  # 5 requests per minute
async def login():
    pass
```

### Feature Flags

#### Redis-Backed Feature Flags
- **Location**: `common/config/feature_flags.py`
- **Purpose**: Enable/disable features dynamically
- **Features**: User-based flags, percentage rollouts, Redis storage

```python
from common.config.feature_flags import is_feature_enabled

# Check if feature is enabled
if is_feature_enabled("new_dashboard", user):
    # Use new dashboard
    pass
else:
    # Use old dashboard
    pass
```

### Metrics

The infrastructure automatically logs:

- Request duration and performance
- Database operation metrics
- Error rates and types
- Security events
- Authentication attempts
- Circuit breaker states
- Rate limiting events
- Feature flag usage

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL configuration
   - Verify database is running
   - Check connection pool settings

2. **Authentication Errors**
   - Verify JWT_SECRET_KEY is set
   - Check token expiration settings
   - Validate token format

3. **Logging Issues**
   - Check log directory permissions
   - Verify log level configuration
   - Ensure disk space is available

4. **Performance Issues**
   - Monitor connection pool usage
   - Check for slow queries
   - Review rate limiting settings

5. **Monitoring Stack Issues**
   - Check Prometheus targets: http://localhost:9090/api/v1/targets
   - Verify Grafana datasources: http://localhost:3002/api/datasources
   - Test Redis connection: `docker-compose exec redis redis-cli ping`
   - Check service logs: `docker-compose logs prometheus grafana redis`

6. **Circuit Breaker Issues**
   - Check circuit breaker metrics in Prometheus
   - Verify failure threshold settings
   - Monitor recovery timeouts

7. **Rate Limiting Issues**
   - Check Redis connection for rate limiter
   - Verify rate limit configuration
   - Monitor rate limit metrics

8. **Feature Flag Issues**
   - Check Redis connection for feature flags
   - Verify flag configuration
   - Test flag evaluation logic

### Debug Mode

Enable debug mode for detailed logging:

```python
# In settings
development.debug = True
monitoring.log_level = "DEBUG"
```

### Monitoring Stack Validation

```bash
# Check all monitoring services
docker-compose ps prometheus grafana redis

# Validate Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana datasources
curl -u admin:admin http://localhost:3002/api/datasources

# Test Redis connection
docker-compose exec redis redis-cli ping

# Run NFR tests
pytest tests/test_non_functional_requirements.py -v
```

## Next Steps

With the core infrastructure in place, you can now:

1. **Implement Service Layer**: Build specific services using the base classes
2. **Create API Endpoints**: Use the middleware for authentication and error handling
3. **Add Business Logic**: Focus on domain-specific functionality
4. **Implement Testing**: Use the testing patterns established
5. **Deploy and Monitor**: Use the observability features for production monitoring

## Contributing

When contributing to the core infrastructure:

1. Follow the established patterns and conventions
2. Add comprehensive tests for new functionality
3. Update documentation for any changes
4. Ensure backward compatibility
5. Follow the error handling and logging patterns 