# Epic FHIR Integration

This document provides comprehensive information about the Epic FHIR integration in the Personal Health Assistant system.

## Overview

The Epic FHIR integration allows the Personal Health Assistant to connect to Epic EHR systems and retrieve patient data using the FHIR (Fast Healthcare Interoperability Resources) standard. This integration supports both the Epic test sandbox and production environments.

## Features

- **Test Sandbox Support**: Connect to Epic's test sandbox with pre-configured test patients
- **SMART on FHIR**: Support for SMART on FHIR launch sequences
- **Multiple Authentication Flows**: Client credentials, authorization code, and SMART on FHIR
- **Comprehensive FHIR Resources**: Patient, Observation, DiagnosticReport, DocumentReference, ImagingStudy, and more
- **Test Patient Access**: Easy access to Epic's test patients (Anna, Henry, John, Omar, Kyle)
- **Connection Testing**: Built-in connection and patient access testing

## Prerequisites

1. **Epic Developer Account**: Sign up at [https://fhir.epic.com/](https://fhir.epic.com/)
2. **Epic FHIR App Registration**: Create an app in the Epic developer portal
3. **Client Credentials**: Obtain Client ID and Client Secret from Epic
4. **Python Environment**: Python 3.8+ with required dependencies

## Quick Setup

### 1. Set Up JWT Configuration

First, set up JWT validation required by Epic:

```bash
cd /path/to/PersonalHealthAssistant
python scripts/setup_epic_jwt.py
```

This script will:
- Generate RSA key pair for JWT signing
- Create JSON Web Key Set (JWKS)
- Provide JWK Set URL and public key for Epic registration
- Test JWT functionality

### 2. Register Your App in Epic Developer Portal

Use the information from the JWT setup script to register your app:

1. Go to https://fhir.epic.com/
2. Sign in to your Epic developer account
3. Create a new app or edit an existing one
4. Configure the following:
   - **Non-Production JWK Set URL**: Use the URL provided by the setup script
   - **Public Key**: Copy the public key shown by the setup script
   - **Redirect URI**: `http://localhost:8080/api/v1/medical-records/epic-fhir/callback`

### 3. Run the Epic FHIR Setup Script

```bash
python scripts/setup_epic_fhir.py
```

The setup script will guide you through:
- Environment selection (Sandbox/Production/Staging)
- Client credentials configuration (from Epic developer portal)
- Scope selection
- Connection testing
- Patient access validation

### 2. Manual Configuration

If you prefer manual setup, add the following environment variables to your `.env` file:

```bash
# Epic FHIR Configuration
EPIC_FHIR_ENVIRONMENT=sandbox
EPIC_FHIR_CLIENT_ID=your_client_id_here
EPIC_FHIR_CLIENT_SECRET=your_client_secret_here
EPIC_FHIR_LAUNCH_URL=your_launch_url_here
EPIC_FHIR_REDIRECT_URI=http://localhost:8080/callback
```

### 3. Start the Medical Records Service

```bash
cd apps/medical_records
python main.py
```

## API Endpoints

### Connection Management

#### Test Connection
```http
GET /api/v1/medical-records/epic-fhir/test-connection
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "status": "connected",
  "environment": "sandbox",
  "fhir_version": "4.0.1",
  "server_name": "Epic FHIR Server",
  "server_version": "2023.1",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Get Configuration
```http
GET /api/v1/medical-records/epic-fhir/config
Authorization: Bearer <your_jwt_token>
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
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Test Patients

#### Get Available Test Patients
```http
GET /api/v1/medical-records/epic-fhir/test-patients
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
[
  {
    "name": "anna",
    "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "display_name": "Anna Clin Doc",
    "gender": "female",
    "birth_date": "1980-01-01"
  },
  {
    "name": "henry",
    "patient_id": "a1",
    "display_name": "Henry Grand Central",
    "gender": "male",
    "birth_date": "1975-05-15"
  }
]
```

#### Get Specific Test Patient
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}
Authorization: Bearer <your_jwt_token>
```

**Example:**
```http
GET /api/v1/medical-records/epic-fhir/test-patients/anna
```

**Response:**
```json
{
  "patient_name": "anna",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "resource_type": "Patient",
  "data": {
    "resourceType": "Patient",
    "id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "name": [
      {
        "text": "Anna Clin Doc",
        "family": "Clin Doc",
        "given": ["Anna"]
      }
    ],
    "gender": "female",
    "birthDate": "1980-01-01"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Patient Data

#### Get Patient Observations
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/observations
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `category`: Observation category

**Example:**
```http
GET /api/v1/medical-records/epic-fhir/test-patients/anna/observations?category=laboratory
```

#### Get Patient Diagnostic Reports
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/diagnostic-reports
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `category`: Report category

#### Get Patient Documents
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/documents
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `doc_type`: Document type

#### Get Patient Imaging Studies
```http
GET /api/v1/medical-records/epic-fhir/test-patients/{patient_name}/imaging-studies
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `date_from`: Start date (ISO format)
- `date_to`: End date (ISO format)
- `modality`: Imaging modality (CT, MRI, X-RAY, etc.)

### JWT and JWK Endpoints

#### Get JSON Web Key Set
```http
GET /api/v1/medical-records/epic-fhir/.well-known/jwks.json
```

**Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "epic-fhir-abc123def456",
      "use": "sig",
      "alg": "RS256",
      "n": "base64url_encoded_modulus",
      "e": "base64url_encoded_exponent",
      "x5c": ["base64_encoded_certificate"],
      "x5t": "base64url_encoded_thumbprint"
    }
  ]
}
```

#### Get Public Key
```http
GET /api/v1/medical-records/epic-fhir/public-key
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "key_id": "epic-fhir-abc123def456",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
  "algorithm": "RS256",
  "key_type": "RSA",
  "key_size": 2048,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Generate JWT Token
```http
POST /api/v1/medical-records/epic-fhir/generate-jwt
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "sub": "user123",
  "scope": "patient/*.read",
  "custom_claim": "value"
}
```

**Response:**
```json
{
  "jwt": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImVwaWMtZmhpci1hYmMxMjNkZWY0NTYifQ...",
  "key_id": "epic-fhir-abc123def456",
  "algorithm": "RS256",
  "expires_in": 3600,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### SMART on FHIR Launch

#### Create Launch URL
```http
POST /api/v1/medical-records/epic-fhir/launch
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "patient_name": "anna",
  "encounter_id": "optional_encounter_id",
  "user_id": "optional_user_id",
  "app_context": "optional_app_context",
  "redirect_uri": "http://localhost:8080/callback"
}
```

**Response:**
```json
{
  "launch_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize?response_type=code&client_id=...",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "state": "random_state_123",
  "scope": "launch/patient patient/*.read",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Test Patients

Epic provides the following test patients in the sandbox:

| Name | Patient ID | Description |
|------|------------|-------------|
| Anna | `Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB` | Main test patient with comprehensive data |
| Henry | `a1` | Test patient for various scenarios |
| John | `a2` | Test patient for specific use cases |
| Omar | `a3` | Test patient for additional testing |
| Kyle | `a4` | Test patient for edge cases |

## Authentication Flows

### 1. Client Credentials Flow
Used for system-level access without user context.

```python
from apps.medical_records.services.epic_fhir_client import EpicFHIRClient, EpicFHIRClientConfig

config = EpicFHIRClientConfig(
    client_id="your_client_id",
    client_secret="your_client_secret",
    scope="system/*.read"
)

client = EpicFHIRClient(config)
await client._authenticate_client_credentials()
```

### 2. SMART on FHIR Launch
Used for patient-specific access with user context.

```python
from apps.medical_records.services.epic_fhir_client import EpicFHIRLaunchContext, EpicFHIRLaunchType

launch_context = EpicFHIRLaunchContext(
    launch_type=EpicFHIRLaunchType.SMART_ON_FHIR,
    patient_id="patient_id",
    launch_url="launch_url_from_epic"
)

await client.authenticate_with_launch_context(launch_context)
```

### 3. Authorization Code Flow
Used for user-initiated authorization.

```python
launch_context = EpicFHIRLaunchContext(
    launch_type=EpicFHIRLaunchType.AUTHORIZATION_CODE,
    patient_id="patient_id",
    redirect_uri="http://localhost:8080/callback"
)

await client.authenticate_with_launch_context(launch_context)
```

## Error Handling

The Epic FHIR integration includes comprehensive error handling:

### Common Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `invalid_token` | Invalid or expired access token | Re-authenticate |
| `insufficient_scope` | Insufficient scope for requested resource | Update app scopes in Epic portal |
| `patient_not_found` | Patient not found or access denied | Check patient ID and permissions |
| `resource_not_found` | Requested resource not found | Verify resource exists |
| `invalid_request` | Invalid request format or parameters | Check request format |
| `server_error` | Internal server error | Contact Epic support |
| `rate_limit_exceeded` | Rate limit exceeded | Implement rate limiting |

### Error Response Format

```json
{
  "detail": "Epic FHIR request failed: 401 - Invalid token",
  "status_code": 500,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EPIC_FHIR_ENVIRONMENT` | Epic environment (sandbox/production/staging) | `sandbox` | Yes |
| `EPIC_FHIR_CLIENT_ID` | Epic FHIR client ID | - | Yes |
| `EPIC_FHIR_CLIENT_SECRET` | Epic FHIR client secret | - | Yes |
| `EPIC_FHIR_LAUNCH_URL` | SMART on FHIR launch URL | - | No |
| `EPIC_FHIR_REDIRECT_URI` | OAuth2 redirect URI | `http://localhost:8080/callback` | No |
| `EPIC_FHIR_PRIVATE_KEY` | RSA private key for JWT signing | Auto-generated | No |
| `EPIC_FHIR_PUBLIC_KEY` | RSA public key for JWT validation | Auto-generated | No |
| `EPIC_FHIR_KEY_ID` | Key ID for JWT tokens | Auto-generated | No |

### JWT Configuration

The Epic FHIR integration uses RSA key pairs for JWT signing and validation:

#### Key Generation
Keys are automatically generated when the service starts, or you can use the setup script:

```bash
python scripts/setup_epic_jwt.py
```

#### JWK Set URL
The JWK Set URL is automatically available at:
```
http://localhost:8080/api/v1/medical-records/epic-fhir/.well-known/jwks.json
```

#### Public Key Format
The public key is provided in PEM format for Epic registration:
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
```

### FHIR Scopes

| Scope | Description | Use Case |
|-------|-------------|----------|
| `launch/patient patient/*.read` | Patient read access | Basic patient data retrieval |
| `launch/patient patient/*.read patient/*.write` | Patient read/write access | Full patient data management |
| `system/*.read` | System read access | System-level data access |
| `system/*.read system/*.write` | System read/write access | Full system access |

## Development

### Running Tests

```bash
cd apps/medical_records
python -m pytest tests/test_epic_fhir.py -v
```

### Debugging

Enable debug logging by setting the log level:

```python
import logging
logging.getLogger("apps.medical_records.services.epic_fhir_client").setLevel(logging.DEBUG)
```

### Local Development

For local development, you can use the test sandbox without real Epic credentials:

```python
# Use test configuration
config = EpicFHIRClientConfig(
    client_id="test_client_id",
    client_secret="test_client_secret",
    epic_environment=EpicEnvironment.SANDBOX
)
```

## Troubleshooting

### Connection Issues

1. **Check Network Connectivity**
   ```bash
   curl -I https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/metadata
   ```

2. **Verify Client Credentials**
   - Check your Epic developer portal
   - Ensure credentials are correctly copied
   - Verify app is approved and active

3. **Check Environment Selection**
   - Use `sandbox` for testing
   - Use `production` for live data
   - Verify environment matches your app configuration

### Authentication Issues

1. **Invalid Token Errors**
   - Tokens expire after a certain time
   - Re-authenticate automatically handled by the client
   - Check token expiration settings

2. **Scope Issues**
   - Verify app has correct scopes in Epic portal
   - Check requested scopes match app configuration
   - Update app scopes if needed

### Patient Access Issues

1. **Patient Not Found**
   - Verify patient ID is correct
   - Check patient exists in the environment
   - Ensure app has access to the patient

2. **Permission Denied**
   - Check app permissions in Epic portal
   - Verify user has access to patient data
   - Contact Epic support if needed

## Security Considerations

1. **Credential Management**
   - Store credentials securely (use environment variables)
   - Rotate credentials regularly
   - Never commit credentials to version control

2. **Token Security**
   - Tokens are automatically managed by the client
   - Tokens are stored in memory only
   - Implement proper session management

3. **Data Privacy**
   - Follow HIPAA guidelines
   - Implement proper access controls
   - Log access appropriately
   - Secure data transmission (HTTPS)

## Support

### Epic FHIR Documentation
- [Epic FHIR Documentation](https://fhir.epic.com/)
- [Test Sandbox Guide](https://fhir.epic.com/Documentation?docId=testpatients)
- [SMART on FHIR Guide](https://docs.smarthealthit.org/)

### Contact
- Epic Developer Support: [Epic Developer Portal](https://fhir.epic.com/)
- Personal Health Assistant Issues: Create an issue in the project repository

## Changelog

### Version 1.0.0
- Initial Epic FHIR integration
- Test sandbox support
- SMART on FHIR launch
- Comprehensive patient data access
- Connection testing and validation 