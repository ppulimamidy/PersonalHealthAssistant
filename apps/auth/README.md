# Authentication Service

## Overview

The Authentication Service is a comprehensive, HIPAA-compliant authentication and authorization system for the Personal Health Assistant platform. It provides secure user authentication, multi-factor authentication (MFA), role-based access control (RBAC), and comprehensive audit logging.

## Features

### 🔐 Authentication Methods
- **Supabase Auth**: Primary authentication system
- **Auth0 OAuth**: Multiple OAuth providers (Google, GitHub, etc.)
- **Local Authentication**: Email/password with bcrypt hashing
- **Multi-Factor Authentication**: TOTP with backup codes

### 🛡️ Security Features
- **Session Management**: Secure session handling with refresh tokens
- **Rate Limiting**: Brute force protection and DDoS mitigation
- **Security Headers**: Comprehensive security headers
- **Threat Detection**: Suspicious activity monitoring
- **Audit Logging**: Complete audit trail for compliance

### 👥 User Management
- **Role-Based Access Control**: Fine-grained permissions
- **User Profiles**: Comprehensive user information
- **Consent Management**: HIPAA-compliant consent tracking
- **Device Management**: MFA device tracking

### 📊 Compliance & Monitoring
- **HIPAA Compliance**: Privacy and security requirements
- **Audit Logging**: Complete event tracking
- **Health Monitoring**: Service health checks
- **Metrics**: Prometheus metrics integration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Service                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   API Layer     │  │  Middleware     │  │   Security   │ │
│  │   (FastAPI)     │  │   (Auth, Rate   │  │   (Headers,  │ │
│  │                 │  │   Limiting)     │  │   Threat     │ │
│  └─────────────────┘  └─────────────────┘  │   Detection) │ │
│                                             └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Auth Service  │  │   MFA Service   │  │  Role Service│ │
│  │   (Supabase,    │  │   (TOTP, Backup │  │   (RBAC,     │ │
│  │    Auth0)       │  │   Codes)        │  │   Permissions│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Audit Service  │  │ Consent Service │  │  Session     │ │
│  │   (Logging,     │  │   (HIPAA,       │  │  Management  │ │
│  │   Compliance)   │  │   Privacy)      │  │  (Tokens,    │ │
│  └─────────────────┘  └─────────────────┘  │   Refresh)   │ │
│                                             └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Supabase account
- Auth0 account (optional)

### Local Development Setup

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
   pip install -r requirements.txt
   ```

4. **Start dependencies**
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run database migrations**
   ```bash
   python scripts/setup/db_setup.py
   ```

6. **Start the authentication service**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Docker Setup

1. **Build the image**
   ```bash
   docker build -f apps/auth/Dockerfile -t auth-service .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env auth-service
   ```

## API Documentation

### Base URL
```
http://localhost:8000/api/v1/auth
```

### Authentication Endpoints

#### Login
```http
POST /auth/login
Authorization: Basic <base64(email:password)>
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "patient",
    "status": "active"
  },
  "session": {
    "id": "uuid",
    "session_token": "jwt_token",
    "refresh_token": "refresh_token",
    "expires_at": "2024-01-01T00:15:00Z"
  },
  "mfa_required": false
}
```

#### Login with Supabase
```http
POST /auth/login/supabase
Content-Type: application/json

{
  "supabase_token": "supabase_jwt_token"
}
```

#### Login with Auth0
```http
POST /auth/login/auth0
Content-Type: application/json

{
  "auth0_token": "auth0_jwt_token"
}
```

#### Refresh Token
```http
POST /auth/refresh
Cookie: refresh_token=<refresh_token>
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

### MFA Endpoints

#### Setup MFA
```http
POST /auth/mfa/setup
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "device_name": "iPhone 12"
}
```

**Response:**
```json
{
  "device_id": "uuid",
  "secret_key": "base32_secret",
  "qr_code_url": "data:image/png;base64,...",
  "backup_codes": ["12345678", "87654321"],
  "verification_required": true
}
```

#### Verify MFA
```http
POST /auth/mfa/verify
Content-Type: application/json

{
  "user_id": "uuid",
  "code": "123456",
  "device_id": "uuid"
}
```

### User Management Endpoints

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

#### Update User Profile
```http
PUT /auth/users/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

### Role Management Endpoints

#### Get User Roles
```http
GET /auth/roles/user/{user_id}
Authorization: Bearer <access_token>
```

#### Assign Role
```http
POST /auth/roles/assign
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "role_id": "uuid",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### Audit Endpoints

#### Get Audit Logs
```http
GET /auth/audit/logs
Authorization: Bearer <access_token>
Query Parameters:
  - user_id: UUID (optional)
  - event_type: string (optional)
  - start_date: ISO date (optional)
  - end_date: ISO date (optional)
  - page: int (default: 1)
  - size: int (default: 20)
```

### Consent Management Endpoints

#### Get User Consents
```http
GET /auth/consent/user/{user_id}
Authorization: Bearer <access_token>
```

#### Create Consent
```http
POST /auth/consent
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "consent_type": "hipaa_privacy",
  "title": "HIPAA Privacy Consent",
  "description": "Consent for use of health information",
  "hipaa_authorization": true
}
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key-here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Auth0
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# Security
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]
ALLOWED_HOSTS=["localhost", "your-domain.com"]

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Security Configuration

```python
# Rate limiting
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

# Session configuration
SESSION_TIMEOUT_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# MFA configuration
MFA_MAX_ATTEMPTS = 5
MFA_LOCKOUT_DURATION_MINUTES = 30

# Password policy
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True
```

## Database Schema

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supabase_user_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    user_type user_type NOT NULL,
    status user_status DEFAULT 'pending_verification',
    mfa_status mfa_status DEFAULT 'disabled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Sessions
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_token TEXT UNIQUE NOT NULL,
    refresh_token TEXT UNIQUE NOT NULL,
    status session_status DEFAULT 'active',
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Roles and Permissions
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    resource_type TEXT NOT NULL,
    action TEXT NOT NULL
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Security Features

### Authentication Flow

1. **User Login**
   - Validate credentials
   - Check account status
   - Verify MFA if enabled
   - Create session
   - Log audit event

2. **Session Management**
   - Short-lived access tokens (15 minutes)
   - Long-lived refresh tokens (7 days)
   - Automatic token rotation
   - Session revocation

3. **MFA Implementation**
   - TOTP (Time-based One-Time Password)
   - QR code generation
   - Backup codes
   - Device management

4. **Rate Limiting**
   - Login attempts: 5 per 5 minutes
   - API requests: 100 per minute
   - MFA attempts: 5 per 5 minutes

### HIPAA Compliance

- **Audit Logging**: All access to PHI is logged
- **Consent Management**: Explicit consent tracking
- **Access Controls**: Role-based access to health data
- **Data Encryption**: All data encrypted in transit and at rest
- **Session Security**: Secure session management

## Monitoring and Observability

### Health Checks

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "auth-service",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### Metrics

The service exposes Prometheus metrics at `/metrics`:

- `auth_login_attempts_total`: Total login attempts
- `auth_login_success_total`: Successful logins
- `auth_login_failure_total`: Failed logins
- `auth_sessions_active`: Active sessions
- `auth_mfa_verifications_total`: MFA verifications
- `auth_rate_limit_hits_total`: Rate limit violations

### Logging

Structured logging with the following levels:
- **INFO**: Normal operations
- **WARNING**: Potential issues
- **ERROR**: Errors that need attention
- **CRITICAL**: Security incidents

## Testing

### Running Tests

```bash
# Run all tests
pytest apps/auth/tests/ -v

# Run unit tests only
pytest apps/auth/tests/unit/ -v

# Run integration tests only
pytest apps/auth/tests/integration/ -v

# Run with coverage
pytest apps/auth/tests/ --cov=apps/auth --cov-report=html

# Run security tests
pytest apps/auth/tests/ -m "security" -v
```

### Test Categories

- **Unit Tests**: Individual service and model tests
- **Integration Tests**: API endpoint tests
- **Security Tests**: Authentication and authorization tests
- **Performance Tests**: Load and stress tests

## Deployment

### Docker Deployment

```bash
# Build image
docker build -f apps/auth/Dockerfile -t auth-service .

# Run container
docker run -d \
  --name auth-service \
  -p 8000:8000 \
  --env-file .env \
  auth-service
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f apps/auth/kubernetes/

# Check deployment status
kubectl get pods -n personal-health-assistant

# View logs
kubectl logs -f deployment/auth-service -n personal-health-assistant
```

### CI/CD Pipeline

The service includes a comprehensive CI/CD pipeline with:

- **Security Scanning**: Bandit, Trivy, Safety
- **Code Quality**: Black, Flake8, MyPy
- **Testing**: Unit, integration, security tests
- **Deployment**: Multi-environment deployment
- **Monitoring**: Health checks and metrics

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # Check connection
   python -c "from common.database.connection import get_db; print('DB OK')"
   ```

2. **Redis Connection Issues**
   ```bash
   # Check Redis status
   docker-compose ps redis
   
   # Test Redis connection
   redis-cli ping
   ```

3. **MFA Issues**
   ```bash
   # Check MFA device status
   curl -H "Authorization: Bearer <token>" \
        http://localhost:8000/api/v1/auth/mfa/devices
   ```

4. **Session Issues**
   ```bash
   # Check active sessions
   curl -H "Authorization: Bearer <token>" \
        http://localhost:8000/api/v1/auth/sessions
   ```

### Log Analysis

```bash
# View service logs
docker logs auth-service

# Filter for errors
docker logs auth-service 2>&1 | grep ERROR

# Filter for security events
docker logs auth-service 2>&1 | grep "SECURITY"
```

## Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests**
5. **Run the test suite**
6. **Submit a pull request**

### Code Standards

- **Python**: PEP 8, type hints
- **Security**: OWASP guidelines
- **Testing**: 90%+ coverage
- **Documentation**: Comprehensive docstrings

## Support

For support and questions:

- **Documentation**: This README and API docs
- **Issues**: GitHub Issues
- **Security**: Security advisories via GitHub
- **Email**: security@your-domain.com

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial release
- Supabase Auth integration
- Auth0 OAuth support
- Multi-factor authentication
- Role-based access control
- Comprehensive audit logging
- HIPAA compliance features
- CI/CD pipeline
- Kubernetes deployment 