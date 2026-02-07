# Medical Analysis Service - Complete Endpoint Guide

## Overview

The Personal Health Assistant now includes a comprehensive Medical Analysis Service that provides diagnosis, prognosis, and literature insights. This service integrates with the Voice Input Service to provide medical analysis for multi-modal queries (voice, text, images).

## Service Architecture

```
Voice Input Service (Port 8003)
├── Multi-modal Processing
├── Voice Processing
├── Vision Analysis
└── Medical Analysis Integration
    └── Medical Analysis Service (Port 8006)
        ├── Diagnosis Service
        ├── Prognosis Service
        └── Literature Service
```

## Medical Analysis Service Endpoints (Port 8006)

### 1. Core Analysis Endpoints

#### `POST /api/v1/medical-analysis/analyze`
**Description**: Perform medical analysis based on request type
**Request Body**:
```json
{
  "patient_id": "uuid",
  "session_id": "string (optional)",
  "analysis_type": "diagnosis|prognosis|literature|comprehensive",
  "symptoms": ["symptom1", "symptom2"],
  "medical_history": {},
  "current_medications": [],
  "vital_signs": {},
  "lab_results": {},
  "imaging_results": {},
  "age": 45,
  "gender": "male",
  "family_history": [],
  "lifestyle_factors": {},
  "domain": "cardiology|dermatology|neurology|general",
  "urgency_level": 1-5
}
```

#### `POST /api/v1/medical-analysis/diagnosis`
**Description**: Medical diagnosis analysis
**Response**:
```json
{
  "analysis_id": "uuid",
  "patient_id": "uuid",
  "analysis_type": "diagnosis",
  "diagnosis": {
    "condition_name": "Angina",
    "icd_code": "I20.9",
    "confidence": 0.85,
    "confidence_level": "high",
    "differential_diagnoses": ["Myocardial infarction", "Pericarditis"],
    "supporting_evidence": ["Chest pain", "Shortness of breath"],
    "severity": "moderate",
    "urgency_level": 3
  },
  "confidence_score": 0.85,
  "processing_time": 2.5,
  "recommendations": ["Schedule appointment with cardiologist"],
  "next_steps": ["Consult healthcare provider"]
}
```

#### `POST /api/v1/medical-analysis/prognosis`
**Description**: Medical prognosis analysis
**Response**:
```json
{
  "analysis_id": "uuid",
  "patient_id": "uuid",
  "analysis_type": "prognosis",
  "prognosis": {
    "condition_name": "Angina",
    "prognosis_type": "short-term",
    "predicted_outcome": "Stable with medication management",
    "time_frame": "3-6 months",
    "confidence": 0.8,
    "risk_factors": ["age", "hypertension"],
    "protective_factors": ["medication_compliance"],
    "survival_rate": 0.95,
    "quality_of_life_impact": "Moderate impact"
  },
  "confidence_score": 0.8,
  "processing_time": 2.1
}
```

#### `POST /api/v1/medical-analysis/literature`
**Description**: Medical literature analysis
**Response**:
```json
{
  "analysis_id": "uuid",
  "patient_id": "uuid",
  "analysis_type": "literature",
  "literature_insights": {
    "topic": "Angina treatment",
    "research_findings": ["Beta-blockers reduce symptoms by 30-40%"],
    "clinical_guidelines": ["ACC/AHA guidelines recommend beta-blockers"],
    "treatment_evidence": ["Level A evidence for beta-blocker therapy"],
    "recent_studies": [{"title": "Recent study", "findings": "Promising results"}],
    "relevance_score": 0.9,
    "evidence_level": "A"
  },
  "confidence_score": 0.9,
  "processing_time": 3.2
}
```

#### `POST /api/v1/medical-analysis/comprehensive`
**Description**: Comprehensive analysis (diagnosis + prognosis + literature)
**Response**:
```json
{
  "analysis_id": "uuid",
  "patient_id": "uuid",
  "analysis_type": "comprehensive",
  "diagnosis": {...},
  "prognosis": {...},
  "literature_insights": {...},
  "treatment_recommendations": [...],
  "confidence_score": 0.85,
  "processing_time": 8.5,
  "recommendations": ["Schedule comprehensive consultation"],
  "next_steps": ["Consult healthcare team"]
}
```

#### `POST /api/v1/medical-analysis/report`
**Description**: Generate comprehensive medical report
**Response**:
```json
{
  "report_id": "uuid",
  "patient_id": "uuid",
  "executive_summary": "Patient presents with chest pain...",
  "key_findings": ["Angina diagnosis", "Moderate risk factors"],
  "critical_alerts": [],
  "diagnosis_summary": {...},
  "prognosis_summary": {...},
  "literature_summary": {...},
  "treatment_plan": [...],
  "risk_factors": ["age", "hypertension"],
  "protective_factors": ["medication_compliance"],
  "risk_score": 0.6,
  "immediate_actions": ["Schedule cardiologist appointment"],
  "short_term_goals": ["Begin beta-blocker therapy"],
  "long_term_goals": ["Achieve optimal cardiovascular health"],
  "monitoring_plan": ["Regular follow-up appointments"],
  "overall_confidence": 0.85,
  "data_quality_score": 0.8
}
```

### 2. Service Information Endpoints

#### `GET /api/v1/medical-analysis/capabilities`
**Description**: Get service capabilities
**Response**:
```json
{
  "service": "medical_analysis",
  "capabilities": {
    "analysis_types": [...],
    "medical_domains": [...],
    "data_sources": [...],
    "ai_models": [...],
    "output_formats": [...]
  }
}
```

#### `GET /api/v1/medical-analysis/health`
**Description**: Health check
**Response**:
```json
{
  "service": "medical_analysis",
  "status": "healthy",
  "version": "1.0.0",
  "endpoints": {...}
}
```

## Voice Input Service Integration (Port 8003)

### Medical Analysis Integration Endpoints

#### `POST /api/v1/voice-input/medical-analysis/analyze-query`
**Description**: Analyze medical query from voice input
**Request Body**:
```json
{
  "patient_id": "uuid",
  "session_id": "string (optional)",
  "query_text": "I have chest pain and shortness of breath",
  "symptoms": ["chest pain", "shortness of breath"],
  "medical_history": {"hypertension": true},
  "analysis_type": "comprehensive"
}
```

#### `POST /api/v1/voice-input/medical-analysis/analyze-vision`
**Description**: Analyze medical query with vision data
**Request Body**:
```json
{
  "patient_id": "uuid",
  "session_id": "string (optional)",
  "vision_response": {
    "response": "Skin rash analysis...",
    "medical_domain": "dermatology",
    "medical_confidence": 0.85
  },
  "query_text": "What's wrong with this skin rash?"
}
```

#### `POST /api/v1/voice-input/medical-analysis/generate-report`
**Description**: Generate comprehensive medical report from multi-modal input
**Request Body**: MultiModalResult object

### Enhanced Multi-modal Endpoints

#### `POST /api/v1/voice-input/multi-modal/process`
**Description**: Process multi-modal input with medical analysis
**Features**:
- Automatic medical intent detection
- Medical analysis integration
- Comprehensive health insights

**Response**:
```json
{
  "input_id": "uuid",
  "processing_successful": true,
  "combined_text": "Patient reports chest pain...",
  "primary_intent": "symptom_report",
  "confidence_score": 0.85,
  "medical_analysis_result": {
    "diagnosis": {...},
    "prognosis": {...},
    "literature_insights": {...}
  },
  "recommendations": ["Schedule cardiologist appointment"],
  "next_steps": ["Consult healthcare provider"]
}
```

## Complete Workflow Examples

### 1. Voice Query with Medical Analysis

```bash
# 1. Upload voice file
curl -X POST "http://localhost:8003/api/v1/voice-input/voice-input" \
  -F "audio_file=@symptoms.wav" \
  -F "patient_id=123e4567-e89b-12d3-a456-426614174000"

# 2. Get transcription
curl -X POST "http://localhost:8003/api/v1/voice-input/transcription" \
  -F "audio_file=@symptoms.wav" \
  -F "language=en"

# 3. Analyze medical query
curl -X POST "http://localhost:8003/api/v1/voice-input/medical-analysis/analyze-query" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "query_text": "I have chest pain and shortness of breath",
    "symptoms": ["chest pain", "shortness of breath"],
    "analysis_type": "comprehensive"
  }'
```

### 2. Vision + Voice Medical Analysis

```bash
# 1. Complete vision voice analysis
curl -X POST "http://localhost:8003/api/v1/voice-input/vision-analysis/complete-analysis" \
  -F "patient_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "image_file=@skin_rash.jpg" \
  -F "voice_file=@query.wav" \
  -F "query=What's wrong with this skin rash?"

# 2. Medical analysis with vision data
curl -X POST "http://localhost:8003/api/v1/voice-input/medical-analysis/analyze-vision" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "vision_response": {
      "response": "Eczematous rash with erythema...",
      "medical_domain": "dermatology",
      "medical_confidence": 0.85
    },
    "query_text": "What treatment should I use?"
  }'
```

### 3. Multi-modal Medical Analysis

```bash
# Process multi-modal input with medical analysis
curl -X POST "http://localhost:8003/api/v1/voice-input/multi-modal/process" \
  -F "patient_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "text_input=I have chest pain and shortness of breath" \
  -F "voice_file=@symptoms.wav" \
  -F "image_file=@ecg.jpg" \
  -F "sensor_data=[{\"sensor_type\":\"heart_rate\",\"sensor_value\":95,\"unit\":\"bpm\"}]"
```

## Medical Domains Supported

1. **Cardiology**: Heart conditions, cardiovascular health
2. **Dermatology**: Skin conditions, lesions, rashes
3. **Neurology**: Brain and nervous system conditions
4. **Oncology**: Cancer and tumor analysis
5. **Endocrinology**: Hormonal and metabolic conditions
6. **Gastroenterology**: Digestive system conditions
7. **Respiratory**: Lung and breathing conditions
8. **General**: General health assessment

## AI Models Used

- **OpenAI GPT-4**: High-quality medical analysis
- **GROQ LLaMA**: Fast inference for real-time analysis
- **Medical Knowledge Base**: Domain-specific medical knowledge
- **Pattern-based Analysis**: Fallback analysis

## Safety Features

- **Medical Disclaimers**: Automatic inclusion of appropriate disclaimers
- **Confidence Scoring**: Transparent confidence levels
- **Professional Consultation**: Always recommends professional medical consultation
- **Emergency Detection**: Automatic detection of emergency situations
- **Educational Purpose**: Designed for educational purposes only

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `500`: Internal server error
- `503`: Service unavailable

## Rate Limiting

- Medical Analysis Service: 100 requests/minute
- Voice Input Service: 50 requests/minute
- Comprehensive Analysis: 20 requests/minute

## Monitoring

- Health checks available at `/health` endpoints
- Prometheus metrics for performance monitoring
- Structured logging for debugging
- Grafana dashboards for visualization

## Security

- JWT authentication required for all endpoints
- CORS protection enabled
- Input validation and sanitization
- Secure error handling

## Getting Started

1. **Start the services**:
```bash
docker-compose up medical-analysis-service voice-input-service
```

2. **Test health**:
```bash
curl http://localhost:8006/health
curl http://localhost:8003/health
```

3. **Test medical analysis**:
```bash
curl -X POST "http://localhost:8006/api/v1/medical-analysis/diagnosis" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "symptoms": ["headache", "nausea"],
    "medical_history": {},
    "age": 30,
    "gender": "female"
  }'
```

## Disclaimer

This service is designed for educational purposes only and should not replace professional medical advice. Always consult with qualified healthcare professionals for medical diagnosis and treatment. 