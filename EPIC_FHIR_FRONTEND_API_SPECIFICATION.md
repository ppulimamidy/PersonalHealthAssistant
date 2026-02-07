# Epic FHIR Frontend API Specification

## Overview
This document provides the complete API specification for integrating with the Epic FHIR (Fast Healthcare Interoperability Resources) functionality to load patient vital records, observations, and other EHR data from the Epic sandbox environment.

## Base URL
```
http://localhost:8005/api/v1/medical-records/epic-fhir
```

## Authentication
All endpoints require Bearer token authentication. The token should be obtained from the auth service.

```javascript
// Example authentication header
const headers = {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
};
```

## OAuth2 Flow for Epic FHIR

### 1. Start OAuth2 Authorization Flow
**Endpoint:** `GET /authorize`

**Description:** Initiates the Epic FHIR OAuth2 authorization code flow. This is the first step in the authentication process.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "authorization_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize?response_type=code&client_id=${EPIC_FHIR_CLIENT_ID:-}&redirect_uri=http://localhost:8005/api/v1/medical-records/epic-fhir/callback&scope=launch/patient patient/*.read&state=...&aud=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
  "client_id": "${EPIC_FHIR_CLIENT_ID:-}",
  "redirect_uri": "http://localhost:8005/api/v1/medical-records/epic-fhir/callback",
  "scope": "launch/patient patient/*.read",
  "state": "epic_fhir_auth",
  "timestamp": "2025-07-29T01:22:19.632328"
}
```

**Frontend Implementation:**
```javascript
// 1. Call the authorize endpoint
const response = await fetch('/api/v1/medical-records/epic-fhir/authorize', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const authData = await response.json();

// 2. Redirect user to Epic authorization URL
window.location.href = authData.authorization_url;
```

### 2. Handle OAuth2 Callback
**Endpoint:** `GET /callback`

**Description:** Handles the redirect from Epic after user authorization. This endpoint exchanges the authorization code for an access token.

**Query Parameters:**
- `code` (required): Authorization code from Epic
- `state` (required): State parameter for security
- `error` (optional): Error from Epic
- `error_description` (optional): Error description from Epic

**Response:**
```json
{
  "status": "success",
  "message": "Epic FHIR OAuth2 authentication successful",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "launch/patient patient/*.read",
  "timestamp": "2025-07-29T01:25:30.123456"
}
```

**Frontend Implementation:**
```javascript
// This is typically handled by the backend, but you can check the status
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');

if (code && state) {
  // The backend will handle the token exchange automatically
  // You can redirect to your main application or show success message
  console.log('OAuth2 authorization successful');
}
```

## Patient Data Retrieval

### 3. Get Available Test Patients
**Endpoint:** `GET /test-patients`

**Description:** Retrieves a list of available test patients in the Epic sandbox.

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
[
  {
    "name": "anna",
    "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "display_name": "Anna Test",
    "gender": "female",
    "birth_date": "1990-01-01"
  },
  {
    "name": "henry",
    "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
    "display_name": "Henry Test",
    "gender": "male",
    "birth_date": "1985-05-15"
  }
]
```

**Frontend Implementation:**
```javascript
const response = await fetch('/api/v1/medical-records/epic-fhir/test-patients', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const patients = await response.json();

// Display patient selection dropdown
patients.forEach(patient => {
  console.log(`${patient.display_name} (${patient.name})`);
});
```

### 4. Get Patient Observations (Vital Signs)
**Endpoint:** `GET /test-patients/{patient_name}/observations-with-auth`

**Description:** Retrieves patient observations (vital signs, lab results, etc.) using OAuth2 authentication.

**Path Parameters:**
- `patient_name` (required): Test patient name (anna, henry, john, omar, kyle)

**Query Parameters:**
- `date_from` (optional): Start date in ISO format (YYYY-MM-DD)
- `date_to` (optional): End date in ISO format (YYYY-MM-DD)
- `category` (optional): Observation category (vital-signs, laboratory, etc.)

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "patient_name": "anna",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "resource_type": "Observation",
  "data": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 25,
    "entry": [
      {
        "resource": {
          "resourceType": "Observation",
          "id": "obs-001",
          "status": "final",
          "category": [
            {
              "coding": [
                {
                  "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                  "code": "vital-signs",
                  "display": "Vital Signs"
                }
              ]
            }
          ],
          "code": {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "8302-2",
                "display": "Body height"
              }
            ]
          },
          "subject": {
            "reference": "Patient/Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
          },
          "effectiveDateTime": "2025-07-28T10:30:00Z",
          "valueQuantity": {
            "value": 165.1,
            "unit": "cm",
            "system": "http://unitsofmeasure.org",
            "code": "cm"
          }
        }
      }
    ]
  },
  "timestamp": "2025-07-29T01:30:45.123456"
}
```

**Frontend Implementation:**
```javascript
// Get patient observations
const getPatientObservations = async (patientName, dateFrom = null, dateTo = null, category = null) => {
  const params = new URLSearchParams();
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  if (category) params.append('category', category);

  const response = await fetch(
    `/api/v1/medical-records/epic-fhir/test-patients/${patientName}/observations-with-auth?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  const data = await response.json();
  return data;
};

// Example usage
const observations = await getPatientObservations('anna', '2025-07-01', '2025-07-28', 'vital-signs');
console.log('Patient observations:', observations);
```

### 5. Get Patient Diagnostic Reports
**Endpoint:** `GET /test-patients/{patient_name}/diagnostic-reports`

**Description:** Retrieves patient diagnostic reports (lab reports, imaging reports, etc.).

**Path Parameters:**
- `patient_name` (required): Test patient name

**Query Parameters:**
- `date_from` (optional): Start date
- `date_to` (optional): End date
- `category` (optional): Report category

**Response:**
```json
{
  "patient_name": "anna",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "resource_type": "DiagnosticReport",
  "data": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 5,
    "entry": [
      {
        "resource": {
          "resourceType": "DiagnosticReport",
          "id": "dr-001",
          "status": "final",
          "code": {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "58410-2",
                "display": "CBC panel"
              }
            ]
          },
          "subject": {
            "reference": "Patient/Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
          },
          "effectiveDateTime": "2025-07-25T14:00:00Z",
          "issued": "2025-07-25T16:30:00Z"
        }
      }
    ]
  },
  "timestamp": "2025-07-29T01:30:45.123456"
}
```

### 6. Get Patient Documents
**Endpoint:** `GET /test-patients/{patient_name}/documents`

**Description:** Retrieves patient documents (clinical notes, discharge summaries, etc.).

**Path Parameters:**
- `patient_name` (required): Test patient name

**Query Parameters:**
- `date_from` (optional): Start date
- `date_to` (optional): End date
- `doc_type` (optional): Document type

**Response:**
```json
{
  "patient_name": "anna",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "resource_type": "DocumentReference",
  "data": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 3,
    "entry": [
      {
        "resource": {
          "resourceType": "DocumentReference",
          "id": "doc-001",
          "status": "current",
          "type": {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "11506-3",
                "display": "Progress note"
              }
            ]
          },
          "subject": {
            "reference": "Patient/Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
          },
          "date": "2025-07-26T09:00:00Z"
        }
      }
    ]
  },
  "timestamp": "2025-07-29T01:30:45.123456"
}
```

### 7. Get Patient Imaging Studies
**Endpoint:** `GET /test-patients/{patient_name}/imaging-studies`

**Description:** Retrieves patient imaging studies (X-rays, MRIs, CT scans, etc.).

**Path Parameters:**
- `patient_name` (required): Test patient name

**Query Parameters:**
- `date_from` (optional): Start date
- `date_to` (optional): End date
- `modality` (optional): Imaging modality (CT, MRI, XR, etc.)

**Response:**
```json
{
  "patient_name": "anna",
  "patient_id": "Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB",
  "resource_type": "ImagingStudy",
  "data": {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 2,
    "entry": [
      {
        "resource": {
          "resourceType": "ImagingStudy",
          "id": "img-001",
          "status": "available",
          "modality": [
            {
              "system": "http://dicom.nema.org/resources/ontology/DCM",
              "code": "CT",
              "display": "Computed Tomography"
            }
          ],
          "subject": {
            "reference": "Patient/Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB"
          },
          "started": "2025-07-24T10:00:00Z",
          "numberOfSeries": 1,
          "numberOfInstances": 50
        }
      }
    ]
  },
  "timestamp": "2025-07-29T01:30:45.123456"
}
```

## Configuration and Status Endpoints

### 8. Get Epic FHIR Configuration
**Endpoint:** `GET /config`

**Description:** Retrieves current Epic FHIR configuration settings.

**Response:**
```json
{
  "client_id": "${EPIC_FHIR_CLIENT_ID:-}",
  "environment": "sandbox",
  "base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
  "oauth_url": "https://fhir.epic.com/interconnect-fhir-oauth/oauth2",
  "scope": "launch/patient patient/*.read",
  "redirect_uri": "http://localhost:8005/api/v1/medical-records/epic-fhir/callback",
  "jwk_set_url": "http://localhost:8005/api/v1/medical-records/epic-fhir/.well-known/jwks.json"
}
```

### 9. Test Epic FHIR Connection
**Endpoint:** `GET /test-connection`

**Description:** Tests the connection to Epic FHIR server.

**Response:**
```json
{
  "status": "connected",
  "environment": "sandbox",
  "fhir_version": "R4",
  "server_name": "Epic FHIR Server",
  "server_version": "1.0.0",
  "timestamp": "2025-07-29T01:30:45.123456"
}
```

### 10. Get Epic FHIR Metadata
**Endpoint:** `GET /metadata`

**Description:** Retrieves Epic FHIR server metadata and capabilities.

**Response:**
```json
{
  "resourceType": "CapabilityStatement",
  "status": "active",
  "date": "2025-07-29T01:30:45.123456",
  "publisher": "Epic Systems Corporation",
  "kind": "instance",
  "software": {
    "name": "Epic FHIR Server",
    "version": "1.0.0"
  },
  "implementation": {
    "description": "Epic FHIR Server Implementation"
  },
  "rest": [
    {
      "mode": "server",
      "resource": [
        {
          "type": "Patient",
          "interaction": [
            {
              "code": "read"
            },
            {
              "code": "search-type"
            }
          ]
        },
        {
          "type": "Observation",
          "interaction": [
            {
              "code": "read"
            },
            {
              "code": "search-type"
            }
          ]
        }
      ]
    }
  ]
}
```

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden:**
```json
{
  "detail": "Insufficient permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Patient not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Epic FHIR server error: Connection failed"
}
```

## Frontend Integration Examples

### Complete Integration Example

```javascript
class EpicFHIRService {
  constructor(baseUrl = 'http://localhost:8005/api/v1/medical-records/epic-fhir') {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Start OAuth2 flow
  async startAuthorization() {
    const data = await this.makeRequest('/authorize');
    return data.authorization_url;
  }

  // Get available patients
  async getPatients() {
    return await this.makeRequest('/test-patients');
  }

  // Get patient observations
  async getPatientObservations(patientName, filters = {}) {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    if (filters.category) params.append('category', filters.category);

    const endpoint = `/test-patients/${patientName}/observations-with-auth`;
    const url = params.toString() ? `${endpoint}?${params}` : endpoint;
    
    return await this.makeRequest(url);
  }

  // Get patient diagnostic reports
  async getPatientReports(patientName, filters = {}) {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    if (filters.category) params.append('category', filters.category);

    const endpoint = `/test-patients/${patientName}/diagnostic-reports`;
    const url = params.toString() ? `${endpoint}?${params}` : endpoint;
    
    return await this.makeRequest(url);
  }

  // Get patient documents
  async getPatientDocuments(patientName, filters = {}) {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    if (filters.docType) params.append('doc_type', filters.docType);

    const endpoint = `/test-patients/${patientName}/documents`;
    const url = params.toString() ? `${endpoint}?${params}` : endpoint;
    
    return await this.makeRequest(url);
  }

  // Get patient imaging studies
  async getPatientImaging(patientName, filters = {}) {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    if (filters.modality) params.append('modality', filters.modality);

    const endpoint = `/test-patients/${patientName}/imaging-studies`;
    const url = params.toString() ? `${endpoint}?${params}` : endpoint;
    
    return await this.makeRequest(url);
  }

  // Test connection
  async testConnection() {
    return await this.makeRequest('/test-connection');
  }

  // Get configuration
  async getConfig() {
    return await this.makeRequest('/config');
  }
}

// Usage example
const epicService = new EpicFHIRService();
epicService.setToken('your-jwt-token');

// Get patients
const patients = await epicService.getPatients();

// Get patient observations
const observations = await epicService.getPatientObservations('anna', {
  dateFrom: '2025-07-01',
  dateTo: '2025-07-28',
  category: 'vital-signs'
});

// Get patient reports
const reports = await epicService.getPatientReports('anna', {
  dateFrom: '2025-07-01',
  dateTo: '2025-07-28'
});
```

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const EpicFHIRIntegration = ({ token }) => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [observations, setObservations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const epicService = new EpicFHIRService();
  epicService.setToken(token);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const patientList = await epicService.getPatients();
      setPatients(patientList);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPatientObservations = async (patientName) => {
    try {
      setLoading(true);
      const data = await epicService.getPatientObservations(patientName, {
        dateFrom: '2025-07-01',
        dateTo: '2025-07-28',
        category: 'vital-signs'
      });
      setObservations(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePatientSelect = (patientName) => {
    setSelectedPatient(patientName);
    loadPatientObservations(patientName);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Epic FHIR Patient Data</h2>
      
      <div>
        <h3>Select Patient:</h3>
        <select onChange={(e) => handlePatientSelect(e.target.value)}>
          <option value="">Choose a patient...</option>
          {patients.map(patient => (
            <option key={patient.name} value={patient.name}>
              {patient.display_name}
            </option>
          ))}
        </select>
      </div>

      {observations && (
        <div>
          <h3>Patient Observations for {selectedPatient}</h3>
          <div>
            <strong>Total Observations:</strong> {observations.data.total}
          </div>
          <div>
            {observations.data.entry?.map((entry, index) => (
              <div key={index} style={{ border: '1px solid #ccc', margin: '10px 0', padding: '10px' }}>
                <strong>Type:</strong> {entry.resource.code?.coding?.[0]?.display}<br/>
                <strong>Value:</strong> {entry.resource.valueQuantity?.value} {entry.resource.valueQuantity?.unit}<br/>
                <strong>Date:</strong> {new Date(entry.resource.effectiveDateTime).toLocaleDateString()}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EpicFHIRIntegration;
```

## Important Notes

1. **OAuth2 Flow**: The Epic FHIR integration requires OAuth2 authentication. The frontend must initiate the authorization flow before accessing patient data.

2. **Test Patients**: The sandbox environment provides test patients (anna, henry, john, omar, kyle) for development and testing.

3. **Data Categories**: Common observation categories include:
   - `vital-signs`: Blood pressure, heart rate, temperature, etc.
   - `laboratory`: Lab test results
   - `survey`: Patient surveys and assessments
   - `imaging`: Imaging results

4. **Date Format**: All dates should be in ISO format (YYYY-MM-DD).

5. **Error Handling**: Always implement proper error handling for network requests and API responses.

6. **Security**: Never expose the JWT token in client-side code. Use secure token storage and transmission methods.

## Testing Checklist

- [ ] OAuth2 authorization flow works correctly
- [ ] Patient list loads successfully
- [ ] Patient observations retrieve correctly
- [ ] Date filtering works as expected
- [ ] Category filtering works as expected
- [ ] Error handling works for invalid requests
- [ ] Loading states display correctly
- [ ] Data displays in appropriate format for users

This specification provides everything needed to integrate Epic FHIR functionality into your frontend application for loading patient vital records and other EHR data. 