# Health Analysis Service - API Endpoints Documentation

## 🏥 Overview

The Health Analysis Service provides comprehensive medical analysis using hybrid AI models (OpenAI Vision + BioGPT + PubMedGPT). All endpoints require authentication and return structured medical data.

**Base URL**: `/api/v1/health-analysis`

---

## 📋 Health Analysis Endpoints

### 1. **POST** `/api/v1/health-analysis/analyze`

**Description**: Analyze a health-related image and provide comprehensive medical insights.

**Request**:
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Authentication**: Required

**Parameters**:
```json
{
  "image": "file (required) - Health-related image to analyze",
  "user_query": "string (optional) - User's specific health question or concern",
  "body_part": "string (optional) - Body part affected (e.g., arm, leg, face)",
  "symptoms": "string (optional) - Additional symptoms description",
  "urgency_level": "string (optional) - Urgency level: low, normal, high, emergency"
}
```

**Response**:
```json
{
  "id": "uuid",
  "user_id": "string",
  "detected_conditions": [
    {
      "id": "uuid",
      "name": "string",
      "confidence": 0.85,
      "category": "skin|injury|eye|dental|respiratory|gastrointestinal|cardiac|neurological",
      "severity": "mild|moderate|severe",
      "urgency": "low|normal|high|emergency",
      "symptoms": ["string"],
      "model_used": "biogpt|pubmedgpt|openai_vision",
      "processing_time": 2.5,
      "description": "string",
      "differential_diagnosis": ["string"],
      "timestamp": "datetime"
    }
  ],
  "medical_insights": [...],
  "overall_severity": "string",
  "urgency_level": "string",
  "triage_level": "string",
  "treatment_recommendations": [...],
  "immediate_actions": ["string"],
  "medical_advice": "string",
  "when_to_seek_care": "string",
  "risk_assessment": {...},
  "processing_time": 5.2,
  "models_used": ["biogpt", "pubmedgpt", "openai_vision"],
  "confidence_score": 0.87,
  "warnings": ["string"],
  "disclaimers": ["string"],
  "timestamp": "datetime"
}
```

**Supported Conditions**:
- Skin conditions (rashes, burns, bites, infections)
- Injuries (cuts, bruises, broken bones)
- Eye problems
- Dental issues
- Respiratory issues
- Gastrointestinal problems
- Cardiac conditions
- Neurological issues

---

### 2. **POST** `/api/v1/health-analysis/detect-condition`

**Description**: Detect specific medical conditions from images.

**Request**:
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Authentication**: Required

**Parameters**:
```json
{
  "image": "file (required) - Image to analyze for condition detection",
  "condition_type": "string (required) - Type of condition to detect"
}
```

**Supported Condition Types**:
- `skin`: rashes, burns, bites, infections, moles, acne
- `injury`: cuts, bruises, fractures, sprains
- `eye`: redness, swelling, discharge, vision issues
- `dental`: cavities, gum disease, tooth damage
- `respiratory`: breathing issues, chest problems
- `gastrointestinal`: abdominal issues, digestive problems
- `cardiac`: heart-related conditions
- `neurological`: brain and nerve conditions

**Response**:
```json
{
  "id": "uuid",
  "user_id": "string",
  "detected_conditions": [...],
  "primary_condition": {...},
  "differential_diagnosis": ["string"],
  "confidence_analysis": {
    "biogpt": 0.89,
    "pubmedgpt": 0.91
  },
  "processing_time": 3.1,
  "model_used": "string",
  "timestamp": "datetime"
}
```

---

### 3. **POST** `/api/v1/health-analysis/medical-query`

**Description**: Process medical queries with or without images.

**Request**:
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: Required

**Request Body**:
```json
{
  "query": "string (required) - Medical query text",
  "image_data": "bytes (optional) - Optional image data",
  "image_format": "string (optional) - Image format if provided",
  "query_type": "string (required) - symptom|treatment|medication|diagnosis|general",
  "urgency_level": "string (optional) - low|normal|high|emergency",
  "age": "integer (optional) - User age",
  "gender": "string (optional) - User gender",
  "medical_history": ["string (optional) - Medical history"],
  "current_medications": ["string (optional) - Current medications"]
}
```

**Response**:
```json
{
  "id": "uuid",
  "user_id": "string",
  "query_analysis": "string",
  "key_findings": ["string"],
  "medical_information": "string",
  "relevant_conditions": ["string"],
  "recommendations": ["string"],
  "next_steps": ["string"],
  "resources": ["string"],
  "references": ["string"],
  "processing_time": 2.8,
  "confidence": 0.85,
  "timestamp": "datetime"
}
```

---

### 4. **GET** `/api/v1/health-analysis/history`

**Description**: Get user's analysis history.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "limit": "integer (optional, default: 20) - Number of records to return (1-100)",
  "offset": "integer (optional, default: 0) - Number of records to skip"
}
```

**Response**:
```json
[
  {
    "id": "uuid",
    "user_id": "string",
    "analysis_type": "string",
    "primary_condition": "string",
    "urgency_level": "string",
    "confidence_score": 0.87,
    "processing_time": 3.2,
    "timestamp": "datetime"
  }
]
```

---

### 5. **GET** `/api/v1/health-analysis/statistics`

**Description**: Get analysis statistics for the user.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "timeframe": "string (optional, default: 30_days) - Timeframe for statistics"
}
```

**Response**:
```json
{
  "total_analyses": 45,
  "conditions_detected": 23,
  "average_confidence": 0.84,
  "most_common_conditions": [
    {"condition": "skin_rash", "count": 8},
    {"condition": "minor_injury", "count": 5}
  ],
  "urgency_distribution": {
    "low": 15,
    "normal": 20,
    "high": 8,
    "emergency": 2
  },
  "timeframe": "30_days"
}
```

---

### 6. **GET** `/api/v1/health-analysis/supported-conditions`

**Description**: Get list of supported medical conditions.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Response**:
```json
{
  "categories": {
    "skin": ["rash", "burn", "dermatitis", "eczema", "psoriasis", "acne", "mole", "lesion"],
    "injury": ["cut", "wound", "bruise", "fracture", "sprain", "strain", "dislocation"],
    "eye": ["conjunctivitis", "stye", "cataract", "glaucoma", "macular_degeneration"],
    "dental": ["cavity", "gum_disease", "gingivitis", "periodontitis", "tooth_abscess"],
    "respiratory": ["pneumonia", "bronchitis", "asthma", "copd", "pulmonary_embolism"],
    "gastrointestinal": ["gastritis", "ulcer", "appendicitis", "cholecystitis", "pancreatitis"],
    "cardiac": ["myocardial_infarction", "angina", "heart_failure", "arrhythmia"],
    "neurological": ["stroke", "migraine", "epilepsy", "meningitis", "encephalitis"]
  },
  "total_conditions": 85
}
```

---

### 7. **GET** `/api/v1/health-analysis/model-performance`

**Description**: Get performance metrics for AI models.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Response**:
```json
{
  "models": {
    "biogpt": {
      "available": true,
      "model": "microsoft/BioGPT",
      "device": "cuda",
      "accuracy": 0.89,
      "speed_ms": 3000,
      "medical_specialized": true,
      "strengths": ["biomedical_text", "clinical_terminology", "medical_literature"],
      "limitations": ["vision_analysis", "real_time_processing"]
    },
    "pubmedgpt": {
      "available": true,
      "model": "stanford-crfm/BioMedLM",
      "device": "cuda",
      "accuracy": 0.91,
      "speed_ms": 3500,
      "medical_specialized": true,
      "strengths": ["medical_research", "evidence_based", "clinical_guidelines"],
      "limitations": ["vision_analysis", "real_time_processing"]
    },
    "openai_vision": {
      "available": true,
      "model": "gpt-4-vision-preview",
      "accuracy": 0.87,
      "speed_ms": 2000,
      "strengths": ["vision_analysis", "image_understanding"],
      "limitations": ["medical_specialization", "cost"]
    }
  },
  "hybrid_accuracy": 0.93,
  "average_processing_time": 2.8
}
```

---

## 🔬 Medical Insights Endpoints

### 8. **POST** `/api/v1/medical-insights/analyze-symptoms`

**Description**: Analyze symptoms and provide detailed medical insights.

**Request**:
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: Required

**Request Body**:
```json
{
  "symptoms": ["string (required) - List of symptoms"],
  "conditions": ["string (optional) - Known conditions"],
  "age": "integer (optional) - User age",
  "gender": "string (optional) - User gender",
  "medical_history": ["string (optional) - Medical history"],
  "current_medications": ["string (optional) - Current medications"]
}
```

**Response**:
```json
{
  "id": "uuid",
  "primary_symptoms": ["string"],
  "secondary_symptoms": ["string"],
  "symptom_severity": "string",
  "symptom_duration": "string",
  "possible_causes": ["string"],
  "most_likely_cause": "string",
  "differential_diagnosis": ["string"],
  "risk_level": "string",
  "emergency_indicators": ["string"],
  "immediate_actions": ["string"],
  "monitoring_advice": "string",
  "follow_up_timeline": "string",
  "specialist_referral": "string"
}
```

---

### 9. **POST** `/api/v1/medical-insights/treatment-recommendations`

**Description**: Get personalized treatment recommendations.

**Request**:
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: Required

**Response**:
```json
[
  {
    "id": "uuid",
    "condition_id": "string",
    "treatment_type": "home_care|medication|procedure",
    "name": "string",
    "description": "string",
    "instructions": ["string"],
    "medications": ["string"],
    "dosages": ["string"],
    "duration": "string",
    "precautions": ["string"],
    "side_effects": ["string"],
    "contraindications": ["string"],
    "warnings": ["string"],
    "effectiveness": "string",
    "time_to_improvement": "string",
    "cost_estimate": "string",
    "availability": "otc|prescription|procedure",
    "evidence_level": "string",
    "source": "string",
    "when_to_stop": "string",
    "follow_up": "string"
  }
]
```

---

### 10. **POST** `/api/v1/medical-insights/risk-assessment`

**Description**: Assess health risks based on symptoms and conditions.

**Request**:
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: Required

**Response**:
```json
{
  "id": "uuid",
  "overall_risk": "string",
  "immediate_risk": "string",
  "long_term_risk": "string",
  "identified_risks": ["string"],
  "risk_score": 6.5,
  "potential_complications": ["string"],
  "complication_probability": {
    "condition": 0.25
  },
  "emergency_indicators": ["string"],
  "emergency_probability": 0.15,
  "preventive_measures": ["string"],
  "lifestyle_recommendations": ["string"],
  "monitoring_requirements": ["string"],
  "follow_up_schedule": "string"
}
```

---

### 11. **GET** `/api/v1/medical-insights/medical-literature`

**Description**: Search medical literature and research.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "query": "string (required) - Medical search query",
  "condition_type": "string (optional) - Type of medical condition",
  "limit": "integer (optional, default: 10) - Number of results (1-50)"
}
```

**Response**:
```json
{
  "results": [
    {
      "title": "string",
      "authors": ["string"],
      "journal": "string",
      "year": 2023,
      "abstract": "string",
      "url": "string",
      "relevance_score": 0.92
    }
  ],
  "total_results": 45,
  "search_query": "string"
}
```

---

### 12. **GET** `/api/v1/medical-insights/drug-interactions`

**Description**: Check for potential drug interactions.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "medications": ["string (required) - List of medications to check"]
}
```

**Response**:
```json
{
  "interactions": [
    {
      "medication1": "string",
      "medication2": "string",
      "severity": "major|moderate|minor",
      "description": "string",
      "risk_factors": ["string"],
      "recommendations": ["string"],
      "alternative_medications": ["string"]
    }
  ],
  "risk_summary": {
    "major_interactions": 2,
    "moderate_interactions": 5,
    "minor_interactions": 3
  }
}
```

---

### 13. **GET** `/api/v1/medical-insights/medical-guidelines`

**Description**: Get medical guidelines for specific conditions.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "condition": "string (required) - Medical condition",
  "specialty": "string (optional) - Medical specialty"
}
```

**Response**:
```json
{
  "condition": "string",
  "guidelines": [
    {
      "title": "string",
      "organization": "string",
      "year": 2023,
      "recommendations": ["string"],
      "evidence_level": "string",
      "url": "string"
    }
  ],
  "treatment_protocols": ["string"],
  "monitoring_guidelines": ["string"]
}
```

---

## 🚨 Emergency Triage Endpoints

### 14. **POST** `/api/v1/emergency-triage/assess-emergency`

**Description**: Assess emergency medical situations and provide immediate guidance.

**Request**:
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Authentication**: Required

**Parameters**:
```json
{
  "image": "file (optional) - Image of the emergency situation",
  "symptoms": "string (required) - Description of symptoms and situation",
  "body_part": "string (optional) - Affected body part",
  "pain_level": "integer (required) - Pain level (1-10)",
  "duration": "string (optional) - How long the condition has been present"
}
```

**Response**:
```json
{
  "id": "uuid",
  "user_id": "string",
  "triage_level": "immediate|emergent|urgent|less_urgent|non_urgent",
  "urgency_level": "low|normal|high|emergency",
  "severity_score": 8.5,
  "is_emergency": true,
  "call_911": true,
  "seek_immediate_care": true,
  "primary_concern": "string",
  "detected_conditions": [...],
  "immediate_actions": ["string"],
  "do_not_do": ["string"],
  "care_level": "string",
  "facility_type": "string",
  "time_to_care": "string",
  "signs_to_watch": ["string"],
  "when_to_escalate": "string",
  "processing_time": 1.2,
  "models_used": ["string"],
  "timestamp": "datetime"
}
```

---

### 15. **POST** `/api/v1/emergency-triage/triage`

**Description**: Perform medical triage to determine urgency and care level needed.

**Request**:
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: Required

**Request Body**:
```json
{
  "symptoms": "string (required) - Description of symptoms",
  "body_part": "string (optional) - Affected body part",
  "pain_level": "integer (required) - Pain level (1-10)",
  "duration": "string (optional) - Duration of symptoms",
  "image_data": "bytes (optional) - Optional image data",
  "age": "integer (optional) - User age",
  "medical_history": ["string (optional) - Medical history"],
  "current_medications": ["string (optional) - Current medications"]
}
```

**Response**:
```json
{
  "id": "uuid",
  "user_id": "string",
  "triage_level": "immediate|emergent|urgent|less_urgent|non_urgent",
  "triage_score": 3.5,
  "urgency_level": "low|normal|high|emergency",
  "wait_time": "string",
  "care_recommendation": "string",
  "facility_recommendation": "string",
  "vital_signs_concern": true,
  "pain_level": 7,
  "risk_factors": ["string"],
  "comorbidities": ["string"],
  "processing_time": 1.8,
  "confidence": 0.92,
  "timestamp": "datetime"
}
```

---

### 16. **GET** `/api/v1/emergency-triage/emergency-symptoms`

**Description**: Get list of emergency symptoms and warning signs.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "category": "string (optional) - Symptom category"
}
```

**Supported Categories**:
- `cardiac`: heart attack, chest pain
- `respiratory`: breathing difficulties
- `neurological`: stroke, seizures
- `trauma`: injuries, bleeding
- `pediatric`: child-specific emergencies

**Response**:
```json
{
  "category": "string",
  "symptoms": [
    {
      "name": "string",
      "description": "string",
      "urgency": "string",
      "warning_signs": ["string"],
      "immediate_actions": ["string"]
    }
  ]
}
```

---

### 17. **GET** `/api/v1/emergency-triage/nearest-emergency-facilities`

**Description**: Find nearest emergency medical facilities.

**Request**:
- **Method**: `GET`
- **Authentication**: Required

**Query Parameters**:
```json
{
  "latitude": "float (required) - User's latitude",
  "longitude": "float (required) - User's longitude",
  "radius": "float (optional, default: 10.0) - Search radius in miles",
  "facility_type": "string (optional, default: all) - Type of facility"
}
```

**Response**:
```json
{
  "facilities": [
    {
      "name": "string",
      "type": "emergency_room|urgent_care|hospital",
      "address": "string",
      "phone": "string",
      "distance_miles": 2.5,
      "travel_time_minutes": 8,
      "services": ["string"],
      "hours": "string",
      "rating": 4.5
    }
  ],
  "user_location": {
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "search_radius": 10.0
}
```

---

## 🔧 Utility Endpoints

### 18. **GET** `/health`

**Description**: Health check endpoint.

**Request**:
- **Method**: `GET`
- **Authentication**: Not required

**Response**:
```json
{
  "service": "health-analysis",
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "database": "healthy",
    "health_analysis": "healthy",
    "ai_models": {
      "biogpt": "available",
      "pubmedgpt": "available",
      "openai_vision": "available"
    },
    "emergency_triage": "healthy"
  }
}
```

---

### 19. **GET** `/ready`

**Description**: Readiness check endpoint.

**Request**:
- **Method**: `GET`
- **Authentication**: Not required

**Response**:
```json
{
  "status": "ready",
  "models": {
    "biogpt": {
      "available": true,
      "model": "microsoft/BioGPT",
      "device": "cuda"
    },
    "pubmedgpt": {
      "available": true,
      "model": "stanford-crfm/BioMedLM",
      "device": "cuda"
    }
  }
}
```

---

## 🔐 Authentication

All endpoints (except `/health` and `/ready`) require authentication using JWT tokens.

**Header**: `Authorization: Bearer <jwt_token>`

---

## 📊 Response Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## ⚠️ Important Notes

1. **Medical Disclaimer**: All analysis results are for informational purposes only and should not replace professional medical advice.

2. **Emergency Situations**: For life-threatening emergencies, call 911 immediately.

3. **Data Privacy**: All medical data is handled according to HIPAA guidelines.

4. **Rate Limiting**: API calls are rate-limited to prevent abuse.

5. **Model Availability**: AI model availability depends on system resources and configuration.

---

## 🚀 Getting Started

1. **Authentication**: Obtain JWT token from auth service
2. **Upload Image**: Use `/analyze` endpoint for image analysis
3. **Get Insights**: Use medical insights endpoints for detailed analysis
4. **Emergency**: Use emergency triage endpoints for urgent situations

The Health Analysis Service provides comprehensive medical analysis using state-of-the-art AI models specifically designed for medical applications. 