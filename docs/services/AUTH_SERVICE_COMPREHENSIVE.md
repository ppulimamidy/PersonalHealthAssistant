# Authentication Service - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [API Endpoints](#api-endpoints)
6. [Security Implementation](#security-implementation)
7. [Database Schema](#database-schema)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Testing](#testing)
11. [Monitoring & Logging](#monitoring--logging)
12. [Troubleshooting](#troubleshooting)

## Overview

The Authentication Service is the cornerstone of the Personal Health Assistant platform, providing secure user authentication, authorization, and session management. It implements industry-standard security practices including JWT tokens, OAuth2 integration, role-based access control (RBAC), and multi-factor authentication.

### Key Responsibilities
- User registration and authentication
- JWT token generation and validation
- OAuth2 provider integration (Google, Apple, Auth0)
- Role-based access control (RBAC)
- Session management and security
- Password management and recovery
- Multi-factor authentication (MFA)
- Audit logging for security events

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │  Auth Service   │
│                 │    │   (Traefik)     │    │                 │
│ - Web App       │───▶│                 │───▶│ - JWT Auth      │
│ - Mobile App    │    │ - Rate Limiting │    │ - OAuth2        │
│ - Third-party   │    │ - SSL/TLS       │    │ - RBAC          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Users         │
                                              │ - Roles         │
                                              │ - Sessions      │
                                              │ - Audit Logs    │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for session storage and rate limiting
- **Security**: JWT tokens, bcrypt password hashing
- **Integration**: OAuth2 providers (Google, Apple, Auth0)

## Features

### 1. User Authentication
- **Email/Password Authentication**: Traditional login with secure password hashing
- **OAuth2 Integration**: Support for Google, Apple, and Auth0 providers
- **Multi-Factor Authentication**: TOTP-based 2FA with QR code generation
- **Password Recovery**: Secure token-based password reset flow
- **Account Lockout**: Brute force protection with progressive delays

### 2. Authorization & Access Control
- **Role-Based Access Control (RBAC)**: Granular permission system
- **JWT Token Management**: Secure token generation, validation, and refresh
- **Session Management**: Redis-based session storage with TTL
- **API Key Management**: For third-party integrations
- **Permission Inheritance**: Hierarchical permission structure

### 3. Security Features
- **Password Security**: bcrypt hashing with configurable rounds
- **Token Security**: JWT with short expiration and refresh tokens
- **Rate Limiting**: Per-user and per-endpoint rate limiting
- **Audit Logging**: Comprehensive security event logging
- **CORS Configuration**: Secure cross-origin resource sharing
- **Input Validation**: Comprehensive request validation and sanitization

### 4. Integration Capabilities
- **OAuth2 Providers**: Google, Apple, Auth0 integration
- **Webhook Support**: Real-time event notifications
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Health Monitoring**: Built-in health checks and metrics

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and session storage
- **Pydantic**: Data validation and serialization

### Security Libraries
- **PyJWT**: JWT token handling
- **bcrypt**: Password hashing
- **python-jose**: JWT encoding/decoding
- **passlib**: Password hashing utilities
- **cryptography**: Cryptographic operations

### Development & Testing
- **pytest**: Testing framework
- **httpx**: Async HTTP client for testing
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "preferences": {
    "notifications": true,
    "privacy_level": "standard"
  }
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "status": "pending_verification",
  "message": "Registration successful. Please verify your email."
}
```

#### POST /auth/login
Authenticate user and return JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "remember_me": false
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "roles": ["user"],
    "permissions": ["read_profile", "write_health_data"]
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /auth/logout
Invalidate current session and tokens.

#### POST /auth/forgot-password
Initiate password reset process.

#### POST /auth/reset-password
Reset password using reset token.

### OAuth2 Endpoints

#### GET /auth/oauth/{provider}/authorize
Initiate OAuth2 authorization flow.

#### GET /auth/oauth/{provider}/callback
Handle OAuth2 callback and create user session.

### User Management Endpoints

#### GET /auth/users/me
Get current user profile.

#### PUT /auth/users/me
Update current user profile.

#### POST /auth/users/me/change-password
Change user password.

#### POST /auth/users/me/enable-2fa
Enable two-factor authentication.

#### POST /auth/users/me/verify-2fa
Verify 2FA setup.

### Admin Endpoints

#### GET /auth/admin/users
List all users (admin only).

#### GET /auth/admin/users/{user_id}
Get user details (admin only).

#### PUT /auth/admin/users/{user_id}
Update user (admin only).

#### DELETE /auth/admin/users/{user_id}
Delete user (admin only).

#### GET /auth/admin/audit-logs
Get audit logs (admin only).

## Security Implementation

### JWT Token Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "roles": ["user"],
    "permissions": ["read_profile"],
    "iat": 1640995200,
    "exp": 1640998800,
    "jti": "unique_token_id"
  }
}
```

### Password Security
- **Hashing Algorithm**: bcrypt with 12 rounds
- **Salt**: Automatically generated per password
- **Minimum Requirements**: 8 characters, uppercase, lowercase, number, special character

### Rate Limiting
- **Login Attempts**: 5 attempts per 15 minutes
- **Password Reset**: 3 attempts per hour
- **API Calls**: 1000 requests per hour per user
- **Registration**: 3 attempts per hour per IP

### Session Management
- **Access Token TTL**: 1 hour
- **Refresh Token TTL**: 7 days
- **Session Storage**: Redis with automatic cleanup
- **Concurrent Sessions**: Configurable limit per user

## Database Schema

### Users Table
```sql
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP,
    phone_verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Roles Table
```sql
CREATE TABLE auth.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### User Roles Table
```sql
CREATE TABLE auth.user_roles (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (user_id, role_id)
);
```

### Sessions Table
```sql
CREATE TABLE auth.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    access_token_jti VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Audit Logs Table
```sql
CREATE TABLE auth.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# Security Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth2 Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret

# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=1000
LOGIN_ATTEMPT_LIMIT=5
LOGIN_ATTEMPT_WINDOW=900
```

### Configuration Files
- **config/settings.py**: Main configuration file
- **config/security.py**: Security-specific settings
- **config/database.py**: Database configuration
- **config/oauth.py**: OAuth2 provider settings

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "apps.auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
auth-service:
  build:
    context: .
    dockerfile: apps/auth/Dockerfile
  ports:
    - "8000:8000"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
  depends_on:
    - postgres
    - redis
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: your-registry/auth-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Testing

### Unit Tests
```python
# tests/unit/test_auth.py
import pytest
from fastapi.testclient import TestClient
from apps.auth.main import app

client = TestClient(app)

def test_user_registration():
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    })
    assert response.status_code == 201
    assert "user_id" in response.json()

def test_user_login():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Integration Tests
```python
# tests/integration/test_oauth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_google_oauth_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/auth/oauth/google/authorize")
        assert response.status_code == 302
        assert "google.com" in response.headers["location"]
```

### Load Testing
```python
# tests/load/auth_load_test.py
import asyncio
import aiohttp

async def load_test_login():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.post("http://localhost:8000/auth/login", json={
                "email": f"user{i}@example.com",
                "password": "password123"
            })
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
        "service": "auth-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected"
    }
```

### Metrics
- **Request Rate**: Requests per second
- **Response Time**: Average response time
- **Error Rate**: Percentage of failed requests
- **Active Sessions**: Number of active user sessions
- **Failed Login Attempts**: Security metric

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/auth/login")
async def login(request: LoginRequest):
    logger.info(f"Login attempt for user: {request.email}")
    # ... authentication logic
    logger.info(f"Successful login for user: {request.email}")
```

### Audit Logging
```python
async def log_audit_event(
    user_id: UUID,
    action: str,
    resource_type: str = None,
    resource_id: UUID = None,
    details: dict = None
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {}
    )
    db.add(audit_log)
    await db.commit()
```

## Troubleshooting

### Common Issues

#### 1. JWT Token Expired
**Symptoms**: 401 Unauthorized errors
**Solution**: Use refresh token to get new access token

#### 2. Database Connection Issues
**Symptoms**: 503 Service Unavailable
**Solution**: Check database connectivity and connection pool settings

#### 3. Rate Limiting
**Symptoms**: 429 Too Many Requests
**Solution**: Implement exponential backoff in client applications

#### 4. OAuth2 Integration Issues
**Symptoms**: OAuth callback failures
**Solution**: Verify OAuth provider configuration and redirect URIs

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Start service in debug mode
uvicorn apps.auth.main:app --reload --log-level debug
```

### Performance Tuning
- **Database Connection Pool**: Adjust pool size based on load
- **Redis Configuration**: Optimize memory usage and persistence
- **JWT Token Size**: Minimize payload to reduce token size
- **Caching Strategy**: Implement appropriate caching for user data

### Security Best Practices
1. **Regular Security Audits**: Monthly security reviews
2. **Dependency Updates**: Keep all dependencies updated
3. **Secret Rotation**: Rotate JWT secrets regularly
4. **Monitoring**: Monitor for suspicious activity
5. **Backup Strategy**: Regular database backups with encryption

---

## Conclusion

The Authentication Service provides a robust, secure, and scalable foundation for user authentication and authorization in the Personal Health Assistant platform. With comprehensive security features, OAuth2 integration, and detailed audit logging, it ensures the highest standards of security and compliance for healthcare applications.

For additional support or questions, please refer to the platform documentation or contact the development team. 