# Epic FHIR Integration Guide

## 🏥 Overview

This guide covers the Epic FHIR integration for the Personal Health Assistant medical records service. The integration provides comprehensive access to Epic EHR data through FHIR R4 APIs, including SMART on FHIR authentication, test patient data access, and JWT-based authentication.

## 🚀 Current Status

### ✅ **Successfully Implemented:**

1. **JWK Set URL Generation** - Fixed and working correctly
2. **JWT Token Generation** - RSA256 signed tokens for Epic authentication
3. **Epic FHIR Client Management** - Multi-client support for sandbox and production
4. **SMART on FHIR Launch** - OAuth2.0 flow for patient context
5. **Test Patient Data Access** - Sandbox patient data retrieval
6. **FHIR Resource Endpoints** - Observations, Diagnostic Reports, Documents, Imaging
7. **Service Integration** - Authentication and authorization middleware

### 🔧 **Technical Implementation:**

- **Service Port**: `8005` (Medical Records Service)
- **JWK Set URL**: `http://localhost:8005/api/v1/medical-records/epic-fhir/.well-known/jwks.json`
- **Authentication**: JWT Bearer tokens with RSA256 signing
- **FHIR Version**: R4
- **Environment**: Sandbox (Epic test environment)

## 📋 API Endpoints

### 🔐 Authentication & Configuration

#### 1. Get Epic FHIR Configuration
```http
GET /api/v1/medical-records/epic-fhir/config
Authorization: Bearer <token>
```

**Response:**
```json
{
  "environment": "sandbox",
  "base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
  "oauth_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2",
  "fhir_version": "R4",
  "test_patients": ["anna", "henry", "john", "omar", "kyle"],
  "test_mychart_users": ["derrick", "camilla", "desiree", "olivia"],
  "scopes": {
    "patient_read": "launch/patient patient/*.read",
    "patient_write": "launch/patient patient/*.read patient/*.write",
    "system_read": "system/*.read",
    "system_write": "system/*.read system/*.write"
  },
  "jwk_set_url": "http://localhost:8005/api/v1/medical-records/epic-fhir/.well-known/jwks.json",
  "key_id": "epic-fhir-78b78e2d7f70415f",
  "timestamp": "2025-07-28T23:20:21.386632"
}
```

#### 2. Get JWK Set (Public Key)
```http
GET /api/v1/medical-records/epic-fhir/.well-known/jwks.json
```

**Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "epic-fhir-78b78e2d7f70415f",
      "use": "sig",
      "alg": "RS256",
      "n": "tIKpY2EXoe9et2MDW4zd_0q4OwDjXefU-pWI-LpHiSp960s6PpOlD62kgsKadWa5ziqy-XrznKY04JkKUdLwMhVZ83g5yHNhxxFORagtfzWo-awU-Ze7fllkpAdfq2D3JrG17Kg0-l6u5z0ugL9BZLSK_kKKPMhBPytLh_xXkfExdlG0fqNoRB9tCY7LzrnUrxSWx1Tl470GPwEmKsogoKwOMMDN6LMPmqyIhgqj555HGaeo9vGqtxH8rHrfUfRehaaYZrK9dAG2ptgUnjYgWxCHBnvI64InSu8xN-aAUI5B0FX9aFJEUDPspK04oNNpcTd6YXTwQrP7srTTe4huHw",
      "e": "AQAB",
      "x5c": ["cGxhY2Vob2xkZXItY2VydGlmaWNhdGU="],
      "x5t": "cGxhY2Vob2xkZXItdGh1bWJwcmludA"
    }
  ]
}
```

#### 3. Get Public Key (PEM Format)
```http
GET /api/v1/medical-records/epic-fhir/public-key
```

**Response:**
```json
{
  "key_id": "epic-fhir-78b78e2d7f70415f",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...",
  "algorithm": "RS256",
  "key_type": "RSA"
}
```

#### 4. Generate JWT Token
```http
POST /api/v1/medical-records/epic-fhir/generate-jwt
Authorization: Bearer <token>
Content-Type: application/json

{
  "sub": "test-user",
  "aud": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
}
```

**Response:**
```json
{
  "jwt": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImVwaWMtZmhpci03OGI3OGUyZDdmNzA0MTVmIiwidHlwIjoiSldUIn0...",
  "key_id": "epic-fhir-78b78e2d7f70415f",
  "algorithm": "RS256",
  "expires_in": 3600,
  "timestamp": "2025-07-28T23:21:00.770565"
}
```

### 🏥 Patient Data Access

#### 5. Get Available Test Patients
```http
GET /api/v1/medical-records/epic-fhir/test-patients
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "name": "anna",
    "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "display_name": "Anna Smith",
    "gender": "female",
    "birth_date": "1990-01-01"
  },
  {
    "name": "henry",
    "patient_id": "a1",
    "display_name": "Henry Johnson",
    "gender": "male",
    "birth_date": "1985-05-15"
  }
]
```

#### 6. Get Test Patient Details
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}
Authorization: Bearer <token>
```

#### 7. Get Patient Observations
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/observations
Authorization: Bearer <token>
```

**Query Parameters:**
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `category`: Observation category (vital-signs, laboratory, etc.)

#### 8. Get Patient Diagnostic Reports
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/diagnostic-reports
Authorization: Bearer <token>
```

#### 9. Get Patient Documents
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/documents
Authorization: Bearer <token>
```

#### 10. Get Patient Imaging Studies
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/imaging-studies
Authorization: Bearer <token>
```

### 🔗 SMART on FHIR Launch

#### 11. Create SMART on FHIR Launch
```http
POST /api/v1/medical-records/epic-fhir/launch
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_name": "anna",
  "encounter_id": "optional-encounter-id",
  "user_id": "optional-user-id",
  "app_context": "optional-app-context",
  "redirect_uri": "http://localhost:8080/callback"
}
```

**Response:**
```json
{
  "launch_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize?...",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "state": "random-state-value",
  "scope": "launch/patient patient/*.read",
  "timestamp": "2025-07-28T23:21:00.770565"
}
```

#### 12. OAuth Callback
```http
GET /api/v1/medical-records/epic-fhir/callback?code={authorization_code}&state={state}
Authorization: Bearer <token>
```

### 🔍 Connection Testing

#### 13. Test Epic FHIR Connection
```http
GET /api/v1/medical-records/epic-fhir/test-connection
Authorization: Bearer <token>
```

#### 14. Get Epic FHIR Metadata
```http
GET /api/v1/medical-records/epic-fhir/metadata
Authorization: Bearer <token>
```

## 🔧 Configuration

### Environment Variables

```bash
# Epic FHIR Configuration
EPIC_FHIR_CLIENT_ID=your_epic_client_id
EPIC_FHIR_CLIENT_SECRET=your_epic_client_secret
EPIC_FHIR_ENVIRONMENT=sandbox  # or production
MEDICAL_RECORDS_SERVICE_URL=http://localhost:8005

# JWT Configuration (auto-generated if not provided)
EPIC_FHIR_PRIVATE_KEY=your_private_key_pem
EPIC_FHIR_PUBLIC_KEY=your_public_key_pem
EPIC_FHIR_KEY_ID=your_key_id
EPIC_FHIR_CERTIFICATE=your_x509_certificate
```

### Test Patients Available

| Name | Patient ID | Description |
|------|------------|-------------|
| anna | Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB | Female patient with comprehensive data |
| henry | a1 | Male patient with various conditions |
| john | a2 | Adult patient with lab results |
| omar | a3 | Patient with imaging studies |
| kyle | a4 | Patient with documents and reports |

## 🚀 Getting Started

### 1. Service Setup

The medical records service is already running on port 8005. Verify it's accessible:

```bash
curl http://localhost:8005/api/v1/medical-records/epic-fhir/test-alive
```

### 2. Authentication

Get an authentication token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -u 'e2etest@health.com:password123' | jq -r '.session.session_token')
```

### 3. Test Configuration

Check the Epic FHIR configuration:

```bash
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/config" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Generate JWT for Epic

Create a JWT token for Epic FHIR authentication:

```bash
curl -X POST "http://localhost:8005/api/v1/medical-records/epic-fhir/generate-jwt" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sub": "your-user-id",
    "aud": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
  }'
```

### 5. Access Patient Data

Get available test patients:

```bash
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/test-patients" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔒 Security Considerations

### JWT Token Security

1. **Key Management**: RSA keys are automatically generated and stored securely
2. **Token Expiration**: JWT tokens expire after 1 hour (3600 seconds)
3. **Audience Validation**: Tokens are validated against Epic's token endpoint
4. **Key Rotation**: New keys are generated on service restart

### Authentication Flow

1. **Service Authentication**: All endpoints require valid service JWT tokens
2. **Epic Authentication**: Epic FHIR endpoints use client credentials or SMART on FHIR
3. **Patient Context**: Patient data access requires proper launch context

## 🐛 Troubleshooting

### Common Issues

1. **JWK Set URL Not Accessible**
   - Verify the service is running on port 8005
   - Check the JWK set endpoint: `/api/v1/medical-records/epic-fhir/.well-known/jwks.json`

2. **Authentication Failures**
   - Ensure valid Epic FHIR client credentials are configured
   - Check that the JWT token is properly signed with the correct key ID

3. **Patient Data Not Available**
   - Verify the patient name is one of the available test patients
   - Check that the Epic FHIR client is properly initialized

4. **Connection Errors**
   - Ensure the Epic FHIR sandbox is accessible
   - Verify network connectivity to Epic's servers

### Debug Endpoints

```bash
# Test service health
curl http://localhost:8005/api/v1/medical-records/epic-fhir/test-alive

# Check JWK set
curl http://localhost:8005/api/v1/medical-records/epic-fhir/.well-known/jwks.json

# Verify public key
curl http://localhost:8005/api/v1/medical-records/epic-fhir/public-key
```

## 📚 Next Steps

### For Production Deployment

1. **Obtain Epic FHIR Production Credentials**
   - Register your application with Epic
   - Get production client ID and secret
   - Configure production environment

2. **Certificate Management**
   - Replace placeholder certificates with real X.509 certificates
   - Implement proper key rotation
   - Store keys securely (not in environment variables)

3. **Patient Data Integration**
   - Implement real patient context from your application
   - Add patient consent management
   - Implement data caching and synchronization

4. **Error Handling**
   - Add comprehensive error handling for Epic API failures
   - Implement retry logic with exponential backoff
   - Add circuit breaker patterns for resilience

### For Frontend Integration

1. **SMART on FHIR Launch**
   - Implement the launch flow in your frontend
   - Handle OAuth callbacks
   - Manage patient context

2. **Data Display**
   - Create components for displaying FHIR resources
   - Implement data visualization for observations
   - Add document and imaging viewers

3. **Real-time Updates**
   - Implement WebSocket connections for real-time data
   - Add data synchronization mechanisms
   - Handle data conflicts and merging

## 🎯 Success Metrics

- ✅ JWK Set URL accessible and properly configured
- ✅ JWT tokens generated successfully with RSA256 signing
- ✅ Epic FHIR client manager initialized with sandbox client
- ✅ All API endpoints responding correctly
- ✅ Authentication and authorization working
- ✅ Test patient data structure defined

The Epic FHIR integration is now ready for development and testing with the sandbox environment! 