# Core Infrastructure Quick Reference

Quick reference guide for the Personal Health Assistant core infrastructure.

## 🚀 Quick Start

### 1. Database Operations

```python
from common.database.connection import get_db_manager, get_session, get_async_session

# Sync operations
with get_db_manager().get_session() as session:
    # Your database operations here
    pass

# Async operations
async with get_db_manager().get_async_session() as session:
    # Your async database operations here
    pass

# FastAPI dependency
from common.database.connection import get_db
@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    # Use db session
    pass
```

### 2. Logging

```python
from common.utils.logging import get_logger, log_request, log_error

# Get logger
logger = get_logger("my_service")

# Log with context
logger.info("User created", user_id=user.id, action="create")
logger.error("Database error", error=str(e), operation="insert")

# Log requests
log_request("req-123", "POST", "/api/users", 201, 0.15, "user-123")

# Log errors
log_error(exception, {"operation": "user_creation"}, "user-123")
```

### 3. Service Base Class

```python
from common.services.base import BaseService, NotFoundError

class UserService(BaseService[UserSchema, UserCreate, UserUpdate, UserModel]):
    @property
    def model_class(self): return UserModel
    @property
    def schema_class(self): return UserSchema
    @property
    def create_schema_class(self): return UserCreate
    @property
    def update_schema_class(self): return UserUpdate

# Usage
user_service = UserService()
user = await user_service.create(user_data)
user = await user_service.get_by_id(user_id)
users = await user_service.get_all(pagination=PaginationModel(page=1, size=20))
```

### 4. Authentication

```python
from common.middleware.auth import (
    get_current_user_required, require_roles, create_tokens
)

# Protected endpoint
@app.get("/users/me")
async def get_current_user(user: Dict = Depends(get_current_user_required)):
    return user

# Role-based endpoint
@app.get("/admin/users")
async def get_all_users(user: Dict = Depends(require_roles(["admin"]))):
    return {"users": []}

# Create tokens
tokens = create_tokens(user_id, email, ["user", "admin"])
```

### 5. Error Handling

```python
from common.services.base import NotFoundError, ValidationError, DuplicateError

# Raise specific errors
if not user:
    raise NotFoundError("User", user_id)

if not valid_email:
    raise ValidationError("Invalid email", {"email": "Invalid format"})

if user_exists:
    raise DuplicateError("User", "email", email)
```

## 📋 Common Patterns

### Database Session Pattern

```python
# ✅ Good
with db_manager.get_session() as session:
    try:
        # Database operations
        session.commit()
    except Exception:
        session.rollback()
        raise

# ❌ Bad
session = db_manager.get_session_factory()()
try:
    # Database operations
    session.commit()
finally:
    session.close()
```

### Logging Pattern

```python
# ✅ Good: Structured logging
logger.info("User created", user_id=user.id, email=user.email)

# ❌ Bad: String formatting
logger.info(f"User {user.id} created with email {user.email}")
```

### Error Handling Pattern

```python
# ✅ Good: Specific error types
if not resource:
    raise NotFoundError("Resource", resource_id)

# ❌ Bad: Generic exceptions
if not resource:
    raise Exception("Resource not found")
```

### Authentication Pattern

```python
# ✅ Good: Dependency injection
@app.get("/protected")
async def protected_endpoint(user: Dict = Depends(get_current_user_required)):
    return {"user": user}

# ❌ Bad: Manual validation
@app.get("/protected")
async def protected_endpoint(request: Request):
    token = request.headers.get("Authorization")
    # Manual validation...
```

## 🔧 Configuration

### Essential Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/health_assistant

# JWT (Change in production!)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# External Services
QDRANT_URL=http://localhost:6333
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Security
SECURITY_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Monitoring
LOG_LEVEL=INFO
```

### Settings Access

```python
from common.config.settings import get_settings

settings = get_settings()

# Access settings
db_url = settings.database.url
jwt_secret = settings.auth.secret_key
log_level = settings.monitoring.log_level
```

## 🧪 Testing

### Running Tests

```bash
# Run all core infrastructure tests
PYTHONPATH=. python tests/test_core_infrastructure.py

# Run with pytest
PYTHONPATH=. pytest tests/test_core_infrastructure.py -v
```

### Test Structure

```python
class TestMyService:
    def test_service_initialization(self):
        service = MyService()
        assert service is not None
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        service = MyService()
        result = await service.async_operation()
        assert result is not None
```

## 📊 Monitoring

### Health Checks

```python
# Database health
health = await db_manager.health_check()
print(f"Database status: {health['status']}")

# Pool statistics
stats = db_manager.get_pool_stats()
print(f"Pool size: {stats['pool_size']}")
```

### Log Analysis

```bash
# View application logs
tail -f logs/health_assistant.log

# View error logs
tail -f logs/health_assistant_error.log

# View database logs
tail -f logs/database.log
```

## 🚨 Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Input validation failed | 422 |
| `DUPLICATE_ERROR` | Resource already exists | 409 |
| `SERVICE_ERROR` | General service error | 500 |
| `JWT_ERROR` | Authentication error | 401 |
| `DATABASE_ERROR` | Database operation failed | 500 |

## 🔐 Security

### Authentication Dependencies

```python
# Required authentication
get_current_user_required()

# Optional authentication
get_current_user_optional()

# Role-based access
require_roles(["admin", "moderator"])
require_admin()
require_healthcare_provider()
```

### Rate Limiting

```python
# Configure in settings
rate_limit_requests: int = 100
rate_limit_window: int = 60  # seconds
```

## 📝 Best Practices

### 1. Always use context managers for database sessions
### 2. Use structured logging with context
### 3. Raise specific error types, not generic exceptions
### 4. Use dependency injection for authentication
### 5. Follow the established service patterns
### 6. Add comprehensive tests for new functionality
### 7. Use type hints and generic types
### 8. Monitor performance and health metrics

## 🔗 Related Documentation

- [Core Infrastructure Documentation](CORE_INFRASTRUCTURE.md) - Detailed documentation
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Development roadmap
- [Setup Guide](SETUP_GUIDE.md) - Environment setup
- [API Documentation](../docs/api/) - API reference

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH=.` is set
2. **Database Connection**: Check `DATABASE_URL` and database status
3. **Authentication**: Verify `JWT_SECRET_KEY` is set
4. **Logging**: Check log directory permissions
5. **Performance**: Monitor connection pool usage

### Debug Mode

```python
# Enable debug logging
settings.development.debug = True
settings.monitoring.log_level = "DEBUG"
```

---

**Need Help?** Check the full documentation or create an issue in the repository. 