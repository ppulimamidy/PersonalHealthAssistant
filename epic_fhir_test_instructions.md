# Epic FHIR OAuth2 Testing Guide

## 🏥 Epic FHIR Sandbox OAuth2 Flow Testing

### **Step 1: Epic FHIR Authorization URL**

**Copy and paste this URL into your browser:**

```
https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize?response_type=code&client_id=0f7c15aa-0f82-4166-8bed-71b398fadcb7&redirect_uri=http://localhost:8005/api/v1/medical-records/epic-fhir/callback&scope=launch/patient%20patient/*.read&state=test_oauth2_flow&aud=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
```

### **Step 2: Epic FHIR Sandbox Login**

When the page loads, you'll see the Epic FHIR sandbox login page. Use these credentials:

- **Username:** `FHIR`
- **Password:** `EpicFhir11!`

### **Step 3: Authorization Process**

1. Enter the credentials above
2. Click "Login" or "Sign In"
3. You may see a consent/authorization page
4. Click "Allow" or "Authorize" to grant access
5. The browser will redirect to: `http://localhost:8005/api/v1/medical-records/epic-fhir/callback?code=AUTHORIZATION_CODE&state=test_oauth2_flow`

### **Step 4: Extract Authorization Code**

From the redirect URL, copy the `code` parameter value. It will look something like:
```
http://localhost:8005/api/v1/medical-records/epic-fhir/callback?code=abc123def456&state=test_oauth2_flow
```

The authorization code is: `abc123def456` (your actual code will be different)

### **Step 5: Test Authorization Code Exchange**

Once you have the authorization code, test the exchange:

```bash
# Replace YOUR_AUTHORIZATION_CODE with the actual code you received
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/callback?code=YOUR_AUTHORIZATION_CODE&state=test_oauth2_flow"
```

### **Step 6: Test Patient Observations**

After successful authorization code exchange, test getting patient observations:

```bash
# Get session token first
SESSION_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -u 'e2etest@health.com:password123' | jq -r '.session.session_token')

# Test patient observations
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/test-patients/anna/observations-with-auth" \
  -H "Authorization: Bearer $SESSION_TOKEN"
```

## 🔧 **Alternative Testing Methods**

### **Method 1: Direct Epic FHIR Access Test**

Test direct access to Epic FHIR metadata:

```bash
curl -X GET "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/metadata" \
  -H "Accept: application/fhir+json" \
  -H "Content-Type: application/fhir+json"
```

### **Method 2: OAuth2 Token Endpoint Test**

Test the OAuth2 token endpoint directly:

```bash
curl -X POST "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=0f7c15aa-0f82-4166-8bed-71b398fadcb7&client_secret=&scope=launch/patient patient/*.read"
```

### **Method 3: Patient Data Test (After OAuth2)**

Once you have an access token, test patient data:

```bash
# Replace YOUR_ACCESS_TOKEN with the actual token
curl -X GET "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/Observation?patient=Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB" \
  -H "Accept: application/fhir+json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📋 **Expected Results**

### **Successful OAuth2 Flow:**
1. ✅ Authorization URL opens Epic FHIR login page
2. ✅ Login with `FHIR` / `EpicFhir11!` works
3. ✅ Authorization consent page appears
4. ✅ Redirect to callback URL with authorization code
5. ✅ Authorization code exchange returns access token
6. ✅ Patient observations retrieved successfully

### **Expected Response Formats:**

**Authorization Code Exchange Response:**
```json
{
  "status": "success",
  "message": "Epic FHIR OAuth2 authentication successful",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "launch/patient patient/*.read"
}
```

**Patient Observations Response:**
```json
{
  "patient_name": "anna",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "resource_type": "Observation",
  "data": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 10,
    "entry": [...]
  }
}
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **"Invalid client" error**: Check that client ID is correct
2. **"Invalid redirect_uri"**: Ensure redirect URI matches exactly
3. **"Invalid scope"**: Verify scope format is correct
4. **"Authorization code expired"**: Codes expire quickly, use immediately
5. **"Access denied"**: Check Epic FHIR sandbox credentials

### **Debug Commands:**

```bash
# Check service health
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/test-alive"

# Check configuration
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/config" \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/auth/login -u 'e2etest@health.com:password123' | jq -r '.session.session_token')"

# Test connection
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/test-connection" \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/auth/login -u 'e2etest@health.com:password123' | jq -r '.session.session_token')"
```

## 🎯 **Success Criteria**

The Epic FHIR OAuth2 flow is successful when:
- ✅ Authorization URL opens correctly
- ✅ Epic FHIR login works with provided credentials
- ✅ Authorization code is received
- ✅ Access token is obtained
- ✅ Patient observations are retrieved

This completes the full OAuth2 authorization code flow for Epic FHIR sandbox integration! 