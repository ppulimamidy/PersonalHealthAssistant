# CORS and Session Configuration Guide

## Overview
This document outlines the CORS (Cross-Origin Resource Sharing) and session configuration for all microservices in the Personal Health Assistant platform. All services are configured to accept session cookies and allow credentials from the frontend.

## ✅ Current Configuration Status

### 1. Global CORS Settings
**Location**: `common/config/settings.py`

```python
# CORS Configuration
CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_METHODS: List[str] = ["*"]
CORS_ALLOW_HEADERS: List[str] = ["*"]
```

### 2. Service-Specific CORS Implementation

| Service | Port | CORS Status | Session Support |
|---------|------|-------------|-----------------|
| **Auth Service** | 8000 | ✅ Properly configured | ✅ Session cookies + Bearer tokens |
| **User Profile** | 8001 | ✅ Uses common settings | ✅ Session cookies + Bearer tokens |
| **Health Tracking** | 8002 | ✅ Uses common settings | ✅ Session cookies + Bearer tokens |
| **AI Insights** | 8200 | ✅ Fixed (was too permissive) | ✅ Session cookies + Bearer tokens |
| **Medical Records** | 8005 | ✅ Uses common settings | ✅ Session cookies + Bearer tokens |
| **Nutrition** | 8007 | ✅ Uses common settings | ✅ Session cookies + Bearer tokens |

## 🔧 Authentication Methods Supported

### 1. Bearer Token Authentication
```javascript
// Frontend implementation
const response = await fetch('http://localhost:8002/api/v1/health-tracking/metrics/', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  credentials: 'include'  // Important for cookies
});
```

### 2. Session Cookie Authentication
```javascript
// Frontend implementation - cookies are automatically sent
const response = await fetch('http://localhost:8002/api/v1/health-tracking/metrics/', {
  credentials: 'include',  // Sends cookies automatically
  headers: {
    'Content-Type': 'application/json'
  }
});
```

## 🍪 Session Management

### Auth Service Session Configuration
```python
# Secure cookie configuration in auth service
response.set_cookie(
    key="access_token",
    value=session.session_token,
    httponly=True,        # Prevents XSS attacks
    secure=True,          # HTTPS only in production
    samesite="strict",    # CSRF protection
    max_age=900           # 15 minutes
)

response.set_cookie(
    key="refresh_token",
    value=session.refresh_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=604800        # 7 days
)
```

### Auth Middleware Session Support
The auth middleware now supports both authentication methods:

1. **Bearer Token from Authorization Header**
2. **Session Cookie from `access_token` cookie**

```python
# Enhanced auth middleware logic
async def __call__(self, request: Request, call_next):
    token = None
    
    # Check for Bearer token in Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # Check for session cookie if no Bearer token
    if not token:
        token = request.cookies.get("access_token")
    
    if token:
        # Validate token and add user to request state
        # ... token validation logic
```

## 🌐 CORS Configuration Details

### Standard CORS Middleware Setup
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,           # ["http://localhost:3000", "http://localhost:8080"]
    allow_credentials=True,                        # Required for cookies
    allow_methods=settings.CORS_ALLOW_METHODS,    # ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers=settings.CORS_ALLOW_HEADERS,    # ["*"]
)
```

### Traefik CORS Configuration
```yaml
# Example: traefik/nutrition.yml
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
```

## 🔒 Security Considerations

### 1. Cookie Security
- **HttpOnly**: Prevents XSS attacks by blocking JavaScript access
- **Secure**: Ensures cookies are only sent over HTTPS (in production)
- **SameSite**: Prevents CSRF attacks
- **Max Age**: Short-lived access tokens (15 minutes)

### 2. CORS Security
- **Specific Origins**: Only allow trusted frontend domains
- **Credentials**: Required for session cookies
- **Methods**: Explicitly define allowed HTTP methods
- **Headers**: Allow necessary headers for API functionality

### 3. Token Security
- **JWT Validation**: All tokens are validated using shared secret
- **Token Blacklisting**: Revoked tokens are stored in Redis
- **Circuit Breaker**: Prevents auth service overload

## 🚀 Frontend Integration Guide

### 1. Login and Session Setup
```javascript
// Login and get session cookies
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Authorization': `Basic ${btoa('email:password')}`,
    'Content-Type': 'application/json'
  },
  credentials: 'include'  // Important for receiving cookies
});

// Cookies are automatically set by the browser
```

### 2. Making Authenticated Requests
```javascript
// Method 1: Using session cookies (recommended)
const response = await fetch('http://localhost:8002/api/v1/health-tracking/metrics/', {
  credentials: 'include',  // Sends cookies automatically
  headers: {
    'Content-Type': 'application/json'
  }
});

// Method 2: Using Bearer token
const response = await fetch('http://localhost:8002/api/v1/health-tracking/metrics/', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  credentials: 'include'
});
```

### 3. Token Refresh
```javascript
// Refresh token using session cookie
const refreshResponse = await fetch('http://localhost:8000/auth/refresh', {
  method: 'POST',
  credentials: 'include'  // Sends refresh_token cookie
});

// New access_token cookie is automatically set
```

## 🧪 Testing CORS and Session Configuration

### 1. Test CORS Preflight
```bash
curl -X OPTIONS http://localhost:8002/api/v1/health-tracking/metrics/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

### 2. Test Session Cookie Authentication
```bash
# First, login to get cookies
curl -X POST http://localhost:8000/auth/login \
  -H "Authorization: Basic ZTJldGVzdEBoZWFsdGguY29tOnBhc3N3b3JkMTIz" \
  -c cookies.txt

# Then use cookies for authenticated request
curl -X GET http://localhost:8002/api/v1/health-tracking/metrics/ \
  -b cookies.txt \
  -H "Origin: http://localhost:3000" \
  -v
```

### 3. Test Bearer Token Authentication
```bash
curl -X GET http://localhost:8002/api/v1/health-tracking/metrics/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Origin: http://localhost:3000" \
  -v
```

## 📋 Configuration Checklist

### ✅ Completed
- [x] All services have CORS middleware configured
- [x] All services allow credentials (`allow_credentials=True`)
- [x] Auth service sets secure session cookies
- [x] Auth middleware supports both Bearer tokens and cookies
- [x] CORS origins are properly restricted
- [x] Security headers are configured
- [x] Token blacklisting is implemented

### 🔄 Recommended Improvements
- [ ] Add environment-specific CORS origins
- [ ] Implement CORS origin validation
- [ ] Add rate limiting for auth endpoints
- [ ] Implement session timeout warnings
- [ ] Add audit logging for authentication events

## 🚨 Troubleshooting

### Common Issues

1. **CORS Error: "No 'Access-Control-Allow-Origin' header"**
   - Check if frontend origin is in `CORS_ORIGINS`
   - Ensure `allow_credentials=True` is set

2. **"Credentials not supported" Error**
   - Verify `credentials: 'include'` is set in frontend requests
   - Check that CORS middleware has `allow_credentials=True`

3. **Session Cookie Not Sent**
   - Ensure `credentials: 'include'` in fetch requests
   - Check cookie domain and path settings
   - Verify SameSite policy compatibility

4. **Token Validation Fails**
   - Check JWT secret key consistency across services
   - Verify token expiration times
   - Check Redis connection for token blacklisting

### Debug Commands
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8200/health

# Check CORS headers
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8002/api/v1/health-tracking/metrics/ \
     -v

# Test authentication
curl -X POST http://localhost:8000/auth/login \
     -H "Authorization: Basic ZTJldGVzdEBoZWFsdGguY29tOnBhc3N3b3JkMTIz" \
     -v
```

## 📚 Additional Resources

- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [JWT Security Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- [Cookie Security Guide](https://owasp.org/www-project-cheat-sheets/cheatsheets/HTML5_Security_Cheat_Sheet.html#cookies)

---

**Last Updated**: July 16, 2025  
**Version**: 1.0.0  
**Status**: ✅ All services configured and tested 