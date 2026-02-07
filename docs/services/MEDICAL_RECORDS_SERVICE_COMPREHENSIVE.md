# Medical Records Service - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [API Endpoints](#api-endpoints)
6. [Data Models](#data-models)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Monitoring & Logging](#monitoring--logging)
11. [Troubleshooting](#troubleshooting)

## Overview

The Medical Records Service manages comprehensive electronic health records (EHR), medical documents, and clinical data for the Personal Health Assistant platform. It provides secure storage, retrieval, and management of medical information while ensuring compliance with healthcare regulations and standards.

### Key Responsibilities
- Electronic Health Records (EHR) management
- Medical document storage and retrieval
- FHIR/HL7 standards compliance
- Epic EHR integration
- Clinical data management
- Medical imaging storage
- Audit trails and compliance

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Healthcare    │    │   API Gateway   │    │ Medical Records │
│   Systems       │    │   (Traefik)     │    │   Service       │
│                 │    │                 │    │                 │
│ - Epic EHR      │───▶│ - Rate Limiting │───▶│ - EHR Mgmt      │
│ - Hospital      │    │ - SSL/TLS       │    │ - FHIR/HL7      │
│   Systems       │    │ - Auth          │    │ - Document      │
│ - Lab Systems   │    │                 │    │   Storage       │
│ - Imaging       │    │                 │    │ - Compliance    │
│   Systems       │    │                 │    │ - Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Patient Data  │
                                              │ - Medical       │
                                              │   Records       │
                                              │ - Documents     │
                                              │ - Audit Logs    │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   File Storage  │
                                              │                 │
                                              │ - Medical       │
                                              │   Images        │
                                              │ - Documents     │
                                              │ - Reports       │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with medical data extensions
- **File Storage**: Secure file storage for medical documents
- **FHIR/HL7**: Healthcare standards compliance
- **Integration**: Epic EHR and other healthcare systems
- **Security**: HIPAA-compliant security measures

## Features

### 1. Electronic Health Records (EHR)
- **Patient Demographics**: Complete patient information management
- **Medical History**: Comprehensive medical history tracking
- **Medications**: Current and historical medication management
- **Allergies**: Allergy and adverse reaction tracking
- **Immunizations**: Vaccination history and schedules
- **Vital Signs**: Blood pressure, temperature, pulse, etc.
- **Lab Results**: Laboratory test results and interpretations
- **Diagnoses**: Medical diagnoses and conditions

### 2. Medical Documents
- **Document Storage**: Secure storage of medical documents
- **Document Types**: Support for various medical document formats
- **Version Control**: Document versioning and history
- **Document Search**: Full-text search capabilities
- **Document Sharing**: Secure document sharing with healthcare providers
- **Document Templates**: Standardized medical document templates

### 3. FHIR/HL7 Compliance
- **FHIR Resources**: Support for FHIR resource types
- **HL7 Messages**: HL7 message processing
- **Interoperability**: Standard healthcare data exchange
- **Resource Validation**: FHIR resource validation
- **Bundle Support**: FHIR bundle processing
- **Extensions**: Custom FHIR extensions

### 4. Epic EHR Integration
- **Epic FHIR API**: Integration with Epic's FHIR API
- **OAuth2 Authentication**: Secure Epic authentication
- **Data Synchronization**: Bidirectional data sync
- **Real-time Updates**: Real-time data updates
- **Error Handling**: Robust error handling and retry logic
- **Audit Logging**: Comprehensive integration audit logs

### 5. Medical Imaging
- **Image Storage**: Secure medical image storage
- **DICOM Support**: DICOM image format support
- **Image Processing**: Basic image processing capabilities
- **Image Viewing**: Web-based image viewing
- **Image Sharing**: Secure image sharing
- **Image Metadata**: Medical image metadata management

### 6. Clinical Decision Support
- **Clinical Rules**: Clinical decision support rules
- **Alerts**: Clinical alerts and notifications
- **Recommendations**: Evidence-based recommendations
- **Drug Interactions**: Drug interaction checking
- **Allergy Alerts**: Allergy and contraindication alerts
- **Clinical Guidelines**: Integration with clinical guidelines

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and session management

### Healthcare Standards
- **FHIR**: Fast Healthcare Interoperability Resources
- **HL7**: Health Level 7 messaging
- **DICOM**: Digital Imaging and Communications in Medicine
- **LOINC**: Logical Observation Identifiers Names and Codes
- **SNOMED CT**: Systematized Nomenclature of Medicine

### Additional Libraries
- **fhirclient**: FHIR client library
- **pydicom**: DICOM image processing
- **pandas**: Data manipulation
- **pydantic**: Data validation
- **cryptography**: Data encryption

## API Endpoints

### Patient Management

#### GET /api/v1/patients
Get patient list.

**Query Parameters:**
- `name`: Patient name filter
- `date_of_birth`: Date of birth filter
- `limit`: Number of patients to return
- `offset`: Pagination offset

**Response:**
```json
{
  "patients": [
    {
      "id": "uuid",
      "identifier": [
        {
          "system": "https://hospital.com/patients",
          "value": "MRN123456"
        }
      ],
      "name": {
        "use": "official",
        "family": "Doe",
        "given": ["John"]
      },
      "gender": "male",
      "birthDate": "1990-01-01",
      "address": [
        {
          "use": "home",
          "type": "physical",
          "line": ["123 Main St"],
          "city": "New York",
          "state": "NY",
          "postalCode": "10001"
        }
      ],
      "contact": [
        {
          "system": "phone",
          "value": "+1234567890",
          "use": "mobile"
        }
      ]
    }
  ],
  "total": 100,
  "offset": 0,
  "limit": 10
}
```

#### GET /api/v1/patients/{patient_id}
Get specific patient details.

#### POST /api/v1/patients
Create new patient record.

#### PUT /api/v1/patients/{patient_id}
Update patient information.

#### DELETE /api/v1/patients/{patient_id}
Delete patient record (soft delete).

### Medical Records

#### GET /api/v1/patients/{patient_id}/records
Get patient's medical records.

**Query Parameters:**
- `record_type`: Type of medical record
- `start_date`: Start date for filtering
- `end_date`: End date for filtering
- `limit`: Number of records to return

#### POST /api/v1/patients/{patient_id}/records
Create new medical record.

**Request Body:**
```json
{
  "resourceType": "Observation",
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
        "code": "85354-9",
        "display": "Blood pressure panel with all children optional"
      }
    ]
  },
  "subject": {
    "reference": "Patient/uuid"
  },
  "effectiveDateTime": "2023-12-01T12:00:00Z",
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 120,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    },
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8462-4",
            "display": "Diastolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 80,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    }
  ]
}
```

#### GET /api/v1/patients/{patient_id}/records/{record_id}
Get specific medical record.

#### PUT /api/v1/patients/{patient_id}/records/{record_id}
Update medical record.

#### DELETE /api/v1/patients/{patient_id}/records/{record_id}
Delete medical record.

### Medications

#### GET /api/v1/patients/{patient_id}/medications
Get patient's medications.

#### POST /api/v1/patients/{patient_id}/medications
Add medication to patient record.

**Request Body:**
```json
{
  "resourceType": "MedicationRequest",
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "197361",
        "display": "Lisinopril 10 MG Oral Tablet"
      }
    ]
  },
  "subject": {
    "reference": "Patient/uuid"
  },
  "authoredOn": "2023-12-01T12:00:00Z",
  "requester": {
    "reference": "Practitioner/uuid"
  },
  "dosageInstruction": [
    {
      "text": "Take 1 tablet daily",
      "timing": {
        "repeat": {
          "frequency": 1,
          "period": 1,
          "periodUnit": "d"
        }
      },
      "route": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "26643006",
            "display": "Oral route"
          }
        ]
      },
      "doseAndRate": [
        {
          "type": {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                "code": "ordered",
                "display": "Ordered"
              }
            ]
          },
          "doseQuantity": {
            "value": 1,
            "unit": "tablet",
            "system": "http://unitsofmeasure.org",
            "code": "{tbl}"
          }
        }
      ]
    }
  ]
}
```

### Allergies

#### GET /api/v1/patients/{patient_id}/allergies
Get patient's allergies.

#### POST /api/v1/patients/{patient_id}/allergies
Add allergy to patient record.

### Lab Results

#### GET /api/v1/patients/{patient_id}/lab-results
Get patient's lab results.

#### POST /api/v1/patients/{patient_id}/lab-results
Add lab result to patient record.

### Medical Documents

#### POST /api/v1/patients/{patient_id}/documents
Upload medical document.

**Request:**
```
Content-Type: multipart/form-data
document: <file>
document_type: "progress_note"
title: "Progress Note"
description: "Follow-up visit notes"
```

#### GET /api/v1/patients/{patient_id}/documents
Get patient's medical documents.

#### GET /api/v1/patients/{patient_id}/documents/{document_id}
Get specific medical document.

#### DELETE /api/v1/patients/{patient_id}/documents/{document_id}
Delete medical document.

### Epic Integration

#### GET /api/v1/epic/patients
Get patients from Epic EHR.

#### POST /api/v1/epic/sync
Trigger Epic data synchronization.

#### GET /api/v1/epic/sync/status
Get Epic sync status.

### FHIR Resources

#### GET /api/v1/fhir/{resource_type}
Get FHIR resources.

#### POST /api/v1/fhir/{resource_type}
Create FHIR resource.

#### GET /api/v1/fhir/{resource_type}/{resource_id}
Get specific FHIR resource.

#### PUT /api/v1/fhir/{resource_type}/{resource_id}
Update FHIR resource.

#### DELETE /api/v1/fhir/{resource_type}/{resource_id}
Delete FHIR resource.

### Search

#### GET /api/v1/search
Search medical records.

**Query Parameters:**
- `q`: Search query
- `resource_type`: FHIR resource type
- `patient_id`: Patient ID filter
- `date_range`: Date range filter

## Data Models

### Patient Model
```python
class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {'schema': 'medical_records'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Patient identifiers
    mrn = Column(String(50), unique=True)  # Medical Record Number
    epic_patient_id = Column(String(50), unique=True)
    
    # Demographics
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10))
    
    # Contact information
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(JSON)
    
    # Medical information
    blood_type = Column(String(5))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    
    # Emergency contact
    emergency_contact = Column(JSON)
    
    # Insurance information
    insurance = Column(JSON)
    
    # FHIR data
    fhir_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Medical Record Model
```python
class MedicalRecord(Base):
    __tablename__ = "medical_records"
    __table_args__ = {'schema': 'medical_records'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.patients.id"), nullable=False)
    
    # Record information
    record_type = Column(String(50), nullable=False)  # observation, medication, allergy, etc.
    fhir_resource_type = Column(String(50), nullable=False)
    fhir_resource_id = Column(String(100))
    
    # Record data
    fhir_data = Column(JSON, nullable=False)
    
    # Metadata
    recorded_date = Column(DateTime, nullable=False)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    source_system = Column(String(50))  # epic, manual, device, etc.
    
    # Status
    status = Column(String(20), default="active")
    verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    verified_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Medical Document Model
```python
class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    __table_args__ = {'schema': 'medical_records'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.patients.id"), nullable=False)
    
    # Document information
    title = Column(String(200), nullable=False)
    document_type = Column(String(50), nullable=False)
    description = Column(Text)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))
    
    # Metadata
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    uploaded_date = Column(DateTime, default=datetime.utcnow)
    
    # FHIR document reference
    fhir_document_reference = Column(JSON)
    
    # Access control
    access_level = Column(String(20), default="private")
    shared_with = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Epic Integration Model
```python
class EpicIntegration(Base):
    __tablename__ = "epic_integrations"
    __table_args__ = {'schema': 'medical_records'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.patients.id"), nullable=False)
    
    # Epic information
    epic_patient_id = Column(String(50), nullable=False)
    epic_access_token = Column(Text)
    epic_refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Sync information
    last_sync = Column(DateTime)
    sync_status = Column(String(20), default="pending")
    sync_errors = Column(JSON, default=list)
    
    # Configuration
    sync_enabled = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=60)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=medical-records-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# File Storage Configuration
UPLOAD_DIR=/app/uploads/medical
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_FILE_TYPES=["pdf", "doc", "docx", "jpg", "png", "dcm"]

# Epic Integration Configuration
EPIC_FHIR_BASE_URL=https://fhir.epic.com/api/FHIR/R4
EPIC_CLIENT_ID=your-epic-client-id
EPIC_CLIENT_SECRET=your-epic-client-secret
EPIC_REDIRECT_URI=http://localhost:8005/api/v1/epic/callback

# FHIR Configuration
FHIR_BASE_URL=http://localhost:8005/api/v1/fhir
FHIR_VERSION=R4
VALIDATE_FHIR_RESOURCES=true

# Security Configuration
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key
HIPAA_COMPLIANCE_ENABLED=true

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8002

# Sync Configuration
SYNC_INTERVAL_MINUTES=60
MAX_SYNC_RETRIES=3
SYNC_TIMEOUT_SECONDS=300
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads/medical

EXPOSE 8005

CMD ["uvicorn", "apps.medical_records.main:app", "--host", "0.0.0.0", "--port", "8005"]
```

### Docker Compose
```yaml
medical-records-service:
  build:
    context: .
    dockerfile: apps/medical_records/Dockerfile
  ports:
    - "8005:8005"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
  volumes:
    - ./uploads:/app/uploads
  depends_on:
    - postgres
    - redis
    - auth-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_patients.py
import pytest
from fastapi.testclient import TestClient
from apps.medical_records.main import app

client = TestClient(app)

def test_create_patient():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "mrn": "MRN123456"
    }
    response = client.post("/api/v1/patients", json=data, headers=headers)
    assert response.status_code == 201
    assert "id" in response.json()

def test_get_patients():
    headers = {"Authorization": "Bearer test-token"}
    response = client.get("/api/v1/patients", headers=headers)
    assert response.status_code == 200
    assert "patients" in response.json()
```

### Integration Tests
```python
# tests/integration/test_epic_integration.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_epic_sync_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Trigger Epic sync
        response = await ac.post("/api/v1/epic/sync")
        assert response.status_code == 202
        
        # Check sync status
        response = await ac.get("/api/v1/epic/sync/status")
        assert response.status_code == 200
        assert "status" in response.json()
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "medical-records-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "epic_integration": "connected"
    }
```

### Metrics
- **Patient Records**: Number of patient records
- **Medical Records**: Number of medical records by type
- **Document Storage**: File storage usage
- **Epic Sync**: Epic integration performance
- **API Performance**: Response times and error rates

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/patients")
async def create_patient(patient: PatientCreate, current_user: User = Depends(get_current_user)):
    logger.info(f"Patient creation requested by user: {current_user.id}")
    # ... patient creation logic
    logger.info(f"Patient created successfully: {patient_id}")
```

## Troubleshooting

### Common Issues

#### 1. Epic Integration Failures
**Symptoms**: Epic sync failures
**Solution**: Check Epic credentials and API access

#### 2. FHIR Validation Errors
**Symptoms**: FHIR resource validation failures
**Solution**: Verify FHIR resource structure and required fields

#### 3. File Upload Issues
**Symptoms**: Document upload failures
**Solution**: Check file size limits and storage permissions

#### 4. Performance Issues
**Symptoms**: Slow API responses
**Solution**: Optimize database queries and implement caching

### Performance Optimization
- **Database Indexing**: Optimize queries for patient and record lookups
- **Caching Strategy**: Cache frequently accessed patient data
- **File Compression**: Compress medical documents for storage
- **Batch Processing**: Process large datasets in batches

### Security Considerations
1. **HIPAA Compliance**: Ensure all data handling meets HIPAA requirements
2. **Data Encryption**: Encrypt sensitive medical data
3. **Access Control**: Implement strict role-based access control
4. **Audit Logging**: Comprehensive audit trails for all data access
5. **Data Retention**: Implement medical data retention policies

---

## Conclusion

The Medical Records Service provides comprehensive electronic health record management with full FHIR/HL7 compliance and Epic EHR integration. With secure document storage, clinical decision support, and robust audit trails, it ensures reliable and compliant medical data management for the Personal Health Assistant platform.

For additional support or questions, please refer to the platform documentation or contact the development team. 