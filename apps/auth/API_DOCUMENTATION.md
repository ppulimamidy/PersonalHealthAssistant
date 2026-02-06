# Authentication Service API Documentation

## Overview

This document provides comprehensive API documentation for the Authentication Service of the Personal Health Assistant platform. The API follows RESTful principles and uses JSON for data exchange.

## Base Information

- **Base URL**: `http://localhost:8000/api/v1/auth`
- **Content-Type**: `application/json`
- **Authentication**: Bearer tokens or session cookies
- **Rate Limiting**: 100 requests per minute per IP
- **Version**: 1.0.0

## Authentication

### Bearer Token Authentication
Most endpoints require authentication using Bearer tokens in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Session Cookie Authentication
For web applications, session cookies are automatically set after login:

```http
Cookie: access_token=<access_token>; refresh_token=<refresh_token>
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "details": {
    "field": "Specific error details"
  },
  "status_code": 400
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Rate Limited
- `500`: Internal Server Error

## Authentication Endpoints

### 1. Login

Authenticate user with email and password.

**Endpoint**: `POST /auth/login`

**Headers**:
```http
Authorization: Basic <base64(email:password)>
Content-Type: application/json
```

**Request Body**: None (credentials in Authorization header)

**Response** (200):
```json
{
  "message": "Login successful",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "patient",
    "status": "active",
    "email_verified": true,
    "mfa_status": "disabled",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login_at": "2024-01-01T00:00:00Z"
  },
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "status": "active",
    "access_token_expires_at": "2024-01-01T00:15:00Z",
    "refresh_token_expires_at": "2024-01-08T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "mfa_required": false
}
```

**Response** (401 - MFA Required):
```json
{
  "message": "MFA verification required",
  "mfa_required": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "mfa_status": "enabled"
}
```

**Error Responses**:
- `401`: Invalid credentials
- `429`: Too many login attempts

### 2. Login with Supabase

Authenticate user with Supabase token.

**Endpoint**: `POST /auth/login/supabase`

**Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "supabase_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200): Same as regular login

**Error Responses**:
- `401`: Invalid Supabase token
- `500`: Supabase service error

### 3. Login with Auth0

Authenticate user with Auth0 token.

**Endpoint**: `POST /auth/login/auth0`

**Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "auth0_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200): Same as regular login

**Error Responses**:
- `401`: Invalid Auth0 token
- `500`: Auth0 service error

### 4. Register

Register a new user account.

**Endpoint**: `POST /auth/register`

**Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "user_type": "patient",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "gender": "female"
}
```

**Response** (201):
```json
{
  "message": "User registration successful",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "verification_required": true
}
```

**Error Responses**:
- `400`: Validation error
- `409`: User already exists
- `429`: Too many registration attempts

### 5. Refresh Token

Refresh access token using refresh token.

**Endpoint**: `POST /auth/refresh`

**Headers**:
```http
Cookie: refresh_token=<refresh_token>
```

**Request Body**: None

**Response** (200):
```json
{
  "message": "Token refreshed successfully",
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access_token_expires_at": "2024-01-01T00:15:00Z",
    "refresh_token_expires_at": "2024-01-08T00:00:00Z"
  }
}
```

**Error Responses**:
- `401`: Invalid refresh token
- `401`: Expired refresh token

### 6. Logout

Logout user and revoke session.

**Endpoint**: `POST /auth/logout`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Request Body**: None

**Response** (200):
```json
{
  "message": "Logout successful"
}
```

## MFA Endpoints

### 1. Setup MFA

Setup multi-factor authentication for user account.

**Endpoint**: `POST /auth/mfa/setup`

**Headers**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "device_name": "iPhone 12"
}
```

**Response** (200):
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440003",
  "secret_key": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": [
    "12345678",
    "87654321",
    "11111111",
    "22222222",
    "33333333",
    "44444444",
    "55555555",
    "66666666",
    "77777777",
    "88888888"
  ],
  "verification_required": true
}
```

### 2. Verify MFA

Verify MFA code for authentication.

**Endpoint**: `POST /auth/mfa/verify`

**Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "123456",
  "device_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

**Response** (200):
```json
{
  "message": "MFA verification successful",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### 3. Get MFA Devices

Get user's MFA devices.

**Endpoint**: `GET /auth/mfa/devices`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "devices": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "device_name": "iPhone 12",
      "device_type": "totp",
      "status": "active",
      "is_primary": true,
      "last_used_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 4. Remove MFA Device

Remove an MFA device.

**Endpoint**: `DELETE /auth/mfa/devices/{device_id}`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "message": "MFA device removed successfully"
}
```

## User Management Endpoints

### 1. Get Current User

Get current user information.

**Endpoint**: `GET /auth/me`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "user_type": "patient",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "status": "active",
  "email_verified": true,
  "phone_verified": false,
  "mfa_status": "enabled",
  "hipaa_consent_given": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login_at": "2024-01-01T00:00:00Z"
}
```

### 2. Update User Profile

Update user profile information.

**Endpoint**: `PUT /auth/users/profile`

**Headers**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "gender": "male"
}
```

**Response** (200):
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3. Change Password

Change user password.

**Endpoint**: `PUT /auth/users/password`

**Headers**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}
```

**Response** (200):
```json
{
  "message": "Password changed successfully"
}
```

### 4. Get User Profile

Get detailed user profile.

**Endpoint**: `GET /auth/users/profile`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Health enthusiast",
  "location": "New York, NY",
  "timezone": "America/New_York",
  "language": "en",
  "blood_type": "O+",
  "height": 175,
  "weight": 70,
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+1234567890",
  "emergency_contact_relationship": "Spouse",
  "license_number": null,
  "specialization": null,
  "years_of_experience": null,
  "certifications": [],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Role Management Endpoints

### 1. Get User Roles

Get roles assigned to a user.

**Endpoint**: `GET /auth/roles/user/{user_id}`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "roles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440005",
      "role_id": "550e8400-e29b-41d4-a716-446655440006",
      "role_name": "patient",
      "role_description": "Patient user with access to own health data",
      "assigned_at": "2024-01-01T00:00:00Z",
      "expires_at": null,
      "is_active": true
    }
  ]
}
```

### 2. Assign Role

Assign a role to a user.

**Endpoint**: `POST /auth/roles/assign`

**Headers**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role_id": "550e8400-e29b-41d4-a716-446655440006",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Response** (201):
```json
{
  "message": "Role assigned successfully",
  "user_role": {
    "id": "550e8400-e29b-41d4-a716-446655440005",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "role_id": "550e8400-e29b-41d4-a716-446655440006",
    "assigned_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-12-31T23:59:59Z",
    "is_active": true
  }
}
```

### 3. Remove Role

Remove a role from a user.

**Endpoint**: `DELETE /auth/roles/user/{user_id}/role/{role_id}`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "message": "Role removed successfully"
}
```

### 4. Get Available Roles

Get all available roles.

**Endpoint**: `GET /auth/roles`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "roles": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "name": "patient",
      "description": "Patient user with access to own health data",
      "is_system_role": true,
      "hipaa_compliant": true,
      "data_access_level": "limited",
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "name": "doctor",
      "description": "Healthcare provider with access to patient data",
      "is_system_role": true,
      "hipaa_compliant": true,
      "data_access_level": "full",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## Session Management Endpoints

### 1. Get User Sessions

Get all active sessions for a user.

**Endpoint**: `GET /auth/sessions`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "status": "active",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "device_id": "device-123",
      "is_mfa_verified": true,
      "access_token_expires_at": "2024-01-01T00:15:00Z",
      "refresh_token_expires_at": "2024-01-08T00:00:00Z",
      "last_activity_at": "2024-01-01T00:00:00Z",
      "login_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. Revoke Session

Revoke a specific session.

**Endpoint**: `DELETE /auth/sessions/{session_id}`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "message": "Session revoked successfully"
}
```

### 3. Revoke All Sessions

Revoke all sessions except the current one.

**Endpoint**: `DELETE /auth/sessions`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "message": "All sessions revoked successfully",
  "revoked_count": 3
}
```

## Audit Endpoints

### 1. Get Audit Logs

Get audit logs with filtering options.

**Endpoint**: `GET /auth/audit/logs`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `user_id` (optional): Filter by user ID
- `event_type` (optional): Filter by event type
- `start_date` (optional): Start date (ISO format)
- `end_date` (optional): End date (ISO format)
- `severity` (optional): Filter by severity level
- `page` (optional): Page number (default: 1)
- `size` (optional): Page size (default: 20)

**Response** (200):
```json
{
  "logs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440008",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "login_success",
      "event_timestamp": "2024-01-01T00:00:00Z",
      "severity": "low",
      "status": "processed",
      "description": "Successful login for user test@example.com",
      "details": {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "session_id": "550e8400-e29b-41d4-a716-446655440001",
      "risk_score": 0,
      "is_suspicious": false,
      "hipaa_relevant": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "pages": 5
  }
}
```

### 2. Get Security Alerts

Get security alerts.

**Endpoint**: `GET /auth/audit/alerts`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `severity` (optional): Filter by severity
- `status` (optional): Filter by status
- `page` (optional): Page number
- `size` (optional): Page size

**Response** (200):
```json
{
  "alerts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440009",
      "alert_type": "suspicious_login",
      "severity": "high",
      "status": "pending",
      "title": "Suspicious Login Detected",
      "description": "Login from unusual location",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "ip_address": "192.168.1.100",
      "threat_level": "medium",
      "threat_indicators": ["unusual_location", "multiple_failed_attempts"],
      "detected_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 10,
    "pages": 1
  }
}
```

## Consent Management Endpoints

### 1. Get User Consents

Get consent records for a user.

**Endpoint**: `GET /auth/consent/user/{user_id}`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "consents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "consent_type": "hipaa_privacy",
      "consent_scope": "all_data",
      "status": "granted",
      "version": "1.0",
      "title": "HIPAA Privacy Consent",
      "description": "Consent for use of health information",
      "requested_at": "2024-01-01T00:00:00Z",
      "granted_at": "2024-01-01T00:00:00Z",
      "expires_at": "2025-01-01T00:00:00Z",
      "hipaa_authorization": true,
      "hipaa_expiration": "2025-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. Create Consent

Create a new consent record.

**Endpoint**: `POST /auth/consent`

**Headers**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "consent_type": "hipaa_privacy",
  "consent_scope": "all_data",
  "title": "HIPAA Privacy Consent",
  "description": "Consent for use of health information",
  "detailed_terms": "Full terms and conditions...",
  "data_categories": ["vital_signs", "medications", "lab_results"],
  "permissions": {
    "read": true,
    "write": false,
    "share": true
  },
  "third_parties": [
    {
      "name": "Healthcare Provider",
      "id": "provider-123",
      "purposes": ["treatment", "payment"]
    }
  ],
  "hipaa_authorization": true,
  "hipaa_expiration": "2025-01-01T00:00:00Z"
}
```

**Response** (201):
```json
{
  "message": "Consent created successfully",
  "consent": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "consent_type": "hipaa_privacy",
    "status": "pending",
    "version": "1.0",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3. Grant Consent

Grant consent for a user.

**Endpoint**: `PUT /auth/consent/{consent_id}/grant`

**Headers**:
```http
Authorization: Bearer <access_token>
```

**Response** (200):
```json
{
  "message": "Consent granted successfully",
  "consent": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "status": "granted",
    "granted_at": "2024-01-01T00:00:00Z"
  }
}
```

### 4. Withdraw Consent

Withdraw consent.

**Endpoint**: `PUT /auth/consent/{consent_id}/withdraw`

**Headers**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "reason": "Privacy concerns"
}
```

**Response** (200):
```json
{
  "message": "Consent withdrawn successfully",
  "consent": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "status": "withdrawn",
    "withdrawn_at": "2024-01-01T00:00:00Z"
  }
}
```

## Health and Monitoring Endpoints

### 1. Health Check

Check service health.

**Endpoint**: `GET /health`

**Response** (200):
```json
{
  "status": "healthy",
  "service": "auth-service",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "uptime": 3600,
  "database": "connected",
  "redis": "connected"
}
```

### 2. Readiness Check

Check service readiness.

**Endpoint**: `GET /ready`

**Response** (200):
```json
{
  "status": "ready",
  "service": "auth-service",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "database": "ready",
    "redis": "ready",
    "supabase": "ready"
  }
}
```

### 3. Metrics

Get Prometheus metrics.

**Endpoint**: `GET /metrics`

**Response** (200):
```
# HELP auth_login_attempts_total Total login attempts
# TYPE auth_login_attempts_total counter
auth_login_attempts_total{method="password"} 100

# HELP auth_login_success_total Successful logins
# TYPE auth_login_success_total counter
auth_login_success_total{method="password"} 95

# HELP auth_sessions_active Active sessions
# TYPE auth_sessions_active gauge
auth_sessions_active 50
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Login attempts**: 5 per 5 minutes per IP
- **API requests**: 100 per minute per IP
- **MFA attempts**: 5 per 5 minutes per user
- **Registration**: 3 per hour per IP

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## Webhooks

The service can send webhooks for important events:

### Webhook Events

- `user.created`
- `user.updated`
- `user.deleted`
- `session.created`
- `session.revoked`
- `mfa.enabled`
- `mfa.disabled`
- `consent.granted`
- `consent.withdrawn`
- `security.alert`

### Webhook Payload

```json
{
  "event": "user.created",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "user_type": "patient"
  }
}
```

## SDK Examples

### Python SDK

```python
import requests

class AuthClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def login(self, email, password):
        import base64
        credentials = base64.b64encode(f"{email}:{password}".encode()).decode()
        response = requests.post(
            f"{self.base_url}/auth/login",
            headers={"Authorization": f"Basic {credentials}"}
        )
        return response.json()
    
    def get_user(self, token):
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

# Usage
client = AuthClient("http://localhost:8000/api/v1", "your-api-key")
result = client.login("user@example.com", "password")
```

### JavaScript SDK

```javascript
class AuthClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = { Authorization: `Bearer ${apiKey}` };
    }
    
    async login(email, password) {
        const credentials = btoa(`${email}:${password}`);
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: { Authorization: `Basic ${credentials}` }
        });
        return response.json();
    }
    
    async getUser(token) {
        const response = await fetch(`${this.baseUrl}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        return response.json();
    }
}

// Usage
const client = new AuthClient('http://localhost:8000/api/v1', 'your-api-key');
const result = await client.login('user@example.com', 'password');
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_INVALID_CREDENTIALS` | Invalid email or password |
| `AUTH_ACCOUNT_LOCKED` | Account is locked |
| `AUTH_MFA_REQUIRED` | MFA verification required |
| `AUTH_MFA_INVALID_CODE` | Invalid MFA code |
| `AUTH_SESSION_EXPIRED` | Session has expired |
| `AUTH_TOKEN_INVALID` | Invalid or expired token |
| `AUTH_INSUFFICIENT_PERMISSIONS` | Insufficient permissions |
| `AUTH_RATE_LIMITED` | Rate limit exceeded |
| `AUTH_USER_NOT_FOUND` | User not found |
| `AUTH_EMAIL_ALREADY_EXISTS` | Email already registered |
| `AUTH_CONSENT_REQUIRED` | Consent required for operation |
| `AUTH_HIPAA_VIOLATION` | HIPAA compliance violation |

## Support

For API support and questions:

- **Documentation**: This API documentation
- **Issues**: GitHub Issues
- **Email**: api-support@your-domain.com
- **Slack**: #api-support channel 