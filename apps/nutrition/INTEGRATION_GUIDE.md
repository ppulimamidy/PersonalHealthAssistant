# Nutrition Service Integration Guide

This guide documents the integration of the Nutrition Microservice with the Personal Health Assistant platform's authentication system, user profile service, and Traefik reverse proxy.

## Overview

The Nutrition Service has been fully integrated with:
- **Authentication Service**: JWT-based authentication and authorization
- **User Profile Service**: Personalized recommendations based on user preferences
- **Traefik Reverse Proxy**: Centralized routing and middleware management
- **Database**: Shared PostgreSQL database with other services
- **Redis**: Session management and caching

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Traefik        │    │   Auth Service  │
│   (React/Vue)   │───▶│   Reverse Proxy  │───▶│   (Port 8000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Nutrition      │
                       │   Service        │
                       │   (Port 8007)    │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   User Profile   │    │   PostgreSQL    │
                       │   Service        │    │   Database      │
                       │   (Port 8001)    │    │   (Port 5432)   │
                       └──────────────────┘    └─────────────────┘
```

## Authentication Integration

### JWT Token Flow

1. **User Login**: User authenticates through the Auth Service
2. **Token Generation**: Auth Service generates JWT access token
3. **Request Authorization**: Frontend includes token in Authorization header
4. **Token Validation**: Nutrition Service validates token using common middleware
5. **User Context**: User information is extracted and available in request state

### Protected Endpoints

All nutrition endpoints require authentication:

```python
@router.post("/analyze-meal")
@require_auth()
async def analyze_meal(
    request: Request,
    meal_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # current_user contains: id, email, roles, etc.
    user_id = current_user["id"]
    # ... rest of implementation
```

### Authentication Middleware

The service uses the common authentication middleware:

```python
# In main.py
from common.middleware.auth import auth_middleware

# Add auth middleware
app.middleware("http")(auth_middleware)
```

## User Profile Integration

### User Profile Client

The service includes a dedicated client for communicating with the User Profile Service:

```python
from apps.nutrition.services.user_profile_client import UserProfileClient

class NutritionService:
    def __init__(self):
        self.user_profile_client = UserProfileClient()
```

### Personalized Recommendations

The service fetches user preferences to generate personalized recommendations:

```python
async def analyze_meal(self, user_id: str, meal_data: Dict[str, Any], token: str = None):
    # Get user preferences if token is provided
    user_preferences = None
    if token:
        user_preferences = await self.user_profile_client.get_nutrition_preferences(user_id, token)
    
    # Generate recommendations with user preferences
    recommendations = await self.recommendations_service.get_recommendations(
        user_id, 
        aggregated,
        user_preferences=user_preferences
    )
```

### User Preferences Used

The service utilizes the following user profile data:
- **Dietary Restrictions**: vegetarian, vegan, gluten-free, etc.
- **Allergies**: food allergies and intolerances
- **Health Goals**: weight loss, muscle gain, heart health, etc.
- **Nutritional Targets**: calorie, protein, carb, fat targets
- **Health Attributes**: age, weight, height, activity level
- **Preferred Cuisines**: mediterranean, asian, etc.

## Traefik Integration

### Configuration

The service is configured in `traefik/nutrition.yml`:

```yaml
http:
  routers:
    nutrition:
      rule: "Host(`nutrition.localhost`)"
      service: nutrition
      entryPoints:
        - web
      middlewares:
        - nutrition-cors
        - nutrition-auth

  services:
    nutrition:
      loadBalancer:
        servers:
          - url: "http://host.docker.internal:8007"

  middlewares:
    nutrition-cors:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        accessControlAllowOriginList:
          - "http://localhost:3000"
          - "http://localhost:8080"
        accessControlAllowHeaders:
          - "*"
        accessControlAllowCredentials: true
    
    nutrition-auth:
      forwardAuth:
        address: "http://host.docker.internal:8000/api/v1/auth/validate"
        trustForwardHeader: true
        authResponseHeaders:
          - "X-User-ID"
          - "X-User-Email"
          - "X-User-Roles"
```

### Routing

- **Direct Access**: `http://localhost:8007` (development)
- **Through Traefik**: `http://nutrition.localhost` (production)
- **Health Check**: `http://nutrition.localhost/health`

## Docker Integration

### Docker Compose

The service is configured in `docker-compose.nutrition-integration.yml`:

```yaml
nutrition-service:
  build:
    context: .
    dockerfile: apps/nutrition/Dockerfile
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
    - AUTH_SERVICE_URL=http://auth-service:8000
    - NUTRITIONIX_API_KEY=${NUTRITIONIX_API_KEY}
    - USDA_API_KEY=${USDA_API_KEY}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  ports:
    - "8007:8007"
  depends_on:
    - auth-service
    - user-profile-service
```

### Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
REDIS_URL=redis://redis:6379

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Service URLs
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
AUTH_SERVICE_URL=http://auth-service:8000

# External APIs
NUTRITIONIX_API_KEY=your-nutritionix-key
NUTRITIONIX_APP_ID=your-nutritionix-app-id
USDA_API_KEY=your-usda-key
OPENAI_API_KEY=your-openai-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_ALLOW_CREDENTIALS=true
```

## API Endpoints

### Authentication Required

All endpoints require a valid JWT token in the Authorization header:

```bash
Authorization: Bearer <jwt-token>
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/nutrition/analyze-meal` | Analyze meal with personalized recommendations |
| POST | `/api/v1/nutrition/log-meal` | Log meal and store in database |
| GET | `/api/v1/nutrition/daily-nutrition/{date}` | Get daily nutrition summary |
| GET | `/api/v1/nutrition/nutrition-history` | Get nutrition history |
| GET | `/api/v1/nutrition/personalized-recommendations` | Get personalized recommendations |
| GET | `/api/v1/nutrition/nutrition-summary` | Get comprehensive nutrition summary |
| POST | `/api/v1/nutrition/calculate-nutrition` | Calculate nutrition for food items |
| GET | `/api/v1/nutrition/nutritional-insights` | Get nutritional insights |
| GET | `/api/v1/nutrition/nutritional-trends/{nutrient}` | Get nutritional trends |

### Food Recognition Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/food-recognition/recognize` | Recognize foods in image |
| POST | `/api/v1/food-recognition/estimate-portions` | Estimate portion sizes |

### Recommendations Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/recommendations/meal-suggestions` | Get meal suggestions |
| GET | `/api/v1/recommendations/personalized` | Get personalized recommendations |

### Goals Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/goals` | Create nutrition goal |
| GET | `/api/v1/goals` | Get user's nutrition goals |
| PUT | `/api/v1/goals/{goal_id}` | Update nutrition goal |
| DELETE | `/api/v1/goals/{goal_id}` | Delete nutrition goal |

## Testing

### Integration Tests

Run the comprehensive integration test:

```bash
cd apps/nutrition
python test_auth_integration.py
```

This test verifies:
- Authentication requirements
- User profile integration
- Personalized recommendations
- Database operations
- Traefik routing

### Manual Testing

1. **Start Services**:
   ```bash
   docker-compose -f docker-compose.nutrition-integration.yml up -d
   ```

2. **Create User**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"TestPass123!","first_name":"Test","last_name":"User"}'
   ```

3. **Login**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test@example.com","password":"TestPass123!"}'
   ```

4. **Analyze Meal**:
   ```bash
   curl -X POST http://nutrition.localhost/api/v1/nutrition/analyze-meal \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"food_items":[{"name":"apple","portion_g":100}]}'
   ```

## Security Considerations

### Authentication
- All endpoints require valid JWT tokens
- Tokens are validated on every request
- User context is extracted and verified

### Authorization
- Users can only access their own data
- User ID is extracted from JWT token
- No cross-user data access allowed

### Data Protection
- Sensitive data is not logged
- User preferences are handled securely
- API keys are stored as environment variables

### CORS
- Configured for specific origins
- Credentials are allowed
- Proper headers are set

## Monitoring and Health Checks

### Health Endpoints

- `/health`: Basic health check
- `/ready`: Readiness check for Kubernetes
- `/metrics`: Prometheus metrics (if enabled)

### Logging

The service uses structured logging with:
- Request/response logging
- Error tracking
- Performance metrics
- User activity (without sensitive data)

### Metrics

Available metrics:
- Request count and latency
- Error rates
- Service dependencies health
- Database connection status

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Check JWT token validity
   - Verify token expiration
   - Ensure proper Authorization header format

2. **User Profile Service Unavailable**:
   - Check service health
   - Verify network connectivity
   - Check environment variables

3. **Database Connection Issues**:
   - Verify database URL
   - Check database health
   - Ensure proper credentials

4. **Traefik Routing Issues**:
   - Check Traefik configuration
   - Verify service discovery
   - Check middleware configuration

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Service Dependencies

Check service dependencies:

```bash
# Check auth service
curl http://localhost:8000/health

# Check user profile service
curl http://localhost:8001/health

# Check nutrition service
curl http://localhost:8007/health
```

## Deployment

### Production Deployment

1. **Environment Variables**: Set all required environment variables
2. **Database Migration**: Run database migrations
3. **Service Startup**: Start services in dependency order
4. **Health Checks**: Verify all services are healthy
5. **Traefik Configuration**: Deploy Traefik configuration

### Kubernetes Deployment

The service includes Kubernetes manifests for production deployment.

### Scaling

The service is stateless and can be scaled horizontally:
- Multiple instances can run simultaneously
- Database connection pooling is configured
- Redis is used for session management

## Future Enhancements

### Planned Features

1. **Advanced Analytics**: More sophisticated nutrition analysis
2. **Machine Learning**: Personalized meal recommendations
3. **Real-time Notifications**: Nutrition alerts and reminders
4. **Social Features**: Sharing meals and achievements
5. **Integration APIs**: Third-party app integrations

### Performance Optimizations

1. **Caching**: Redis-based caching for frequently accessed data
2. **Database Optimization**: Query optimization and indexing
3. **CDN Integration**: Static asset delivery
4. **Load Balancing**: Advanced load balancing strategies

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Run integration tests
4. Contact the development team

## Contributing

When contributing to the nutrition service:
1. Follow the existing code patterns
2. Add appropriate tests
3. Update documentation
4. Ensure authentication integration
5. Test with user profile service 