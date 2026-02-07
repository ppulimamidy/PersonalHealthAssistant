# Health Analysis Service - Comprehensive Overview

## 🏥 Service Overview

The Health Analysis Service is a comprehensive medical AI service that provides advanced health image analysis, condition detection, emergency triage, and medical insights. It's designed to help users analyze medical images, get preliminary diagnoses, and receive appropriate medical guidance.

## 🚀 Service Status

- **Status**: ✅ **FULLY OPERATIONAL**
- **Port**: 8008
- **Health Check**: ✅ Healthy
- **AI Models**: ✅ All models available (OpenAI Vision, Google Vision, Azure Vision)
- **Authentication**: ✅ Working with JWT tokens

## 📋 Available Endpoints

### Core Health Analysis Endpoints

#### 1. **Health Image Analysis** - `/api/v1/health-analysis/analyze`
- **Method**: POST
- **Purpose**: Comprehensive analysis of health-related images
- **Features**:
  - Detects multiple medical conditions
  - Provides severity assessment
  - Generates treatment recommendations
  - Offers medical advice and warnings
  - Risk assessment and triage level determination

**Example Request**:
```bash
curl -X POST \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "image=@medical_image.jpg" \
  -F "user_query=Please analyze this skin rash" \
  -F "body_part=skin" \
  -F "symptoms=redness and itching" \
  -F "urgency_level=normal" \
  http://localhost:8008/api/v1/health-analysis/analyze
```

**Example Response**:
```json
{
  "id": "fc48a262-66bb-446a-af47-fb28eeeb624f",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "detected_conditions": [
    {
      "id": "c54c311c-9e7a-4d15-9862-620da9bb558e",
      "name": "skin rash",
      "confidence": 0.85,
      "category": "skin",
      "severity": "mild",
      "urgency": "normal",
      "symptoms": ["redness", "itching", "irritation"],
      "model_used": "openai_vision",
      "description": "Appears to be a mild skin rash",
      "differential_diagnosis": [
        "contact dermatitis",
        "allergic reaction",
        "eczema"
      ]
    }
  ],
  "medical_insights": [...],
  "overall_severity": "mild",
  "urgency_level": "normal",
  "triage_level": "less_urgent",
  "treatment_recommendations": [...],
  "immediate_actions": [
    "Keep area clean",
    "Monitor for changes",
    "Follow up with healthcare provider if needed"
  ],
  "medical_advice": "This appears to be a manageable condition...",
  "when_to_seek_care": "Within 24-48 hours",
  "risk_assessment": {...},
  "processing_time": 0.542799,
  "models_used": ["openai_vision"],
  "confidence_score": 0.85,
  "warnings": ["This analysis is for informational purposes only..."],
  "disclaimers": ["Always consult with a healthcare professional..."]
}
```

#### 2. **Condition Detection** - `/api/v1/health-analysis/detect-condition`
- **Method**: POST
- **Purpose**: Detect specific medical conditions from images
- **Supported Conditions**:
  - **Skin**: rash, burn, bite, infection, mole, acne
  - **Injury**: cut, bruise, fracture, sprain
  - **Eye**: redness, swelling, discharge
  - **Dental**: cavity, gum_disease, tooth_damage

#### 3. **Medical Query Processing** - `/api/v1/health-analysis/medical-query`
- **Method**: POST
- **Purpose**: Process text-based medical queries
- **Features**:
  - Symptom analysis
  - Treatment recommendations
  - Medication information
  - Medical guidance

#### 4. **Analysis History** - `/api/v1/health-analysis/history`
- **Method**: GET
- **Purpose**: Retrieve user's health analysis history

#### 5. **Analysis Statistics** - `/api/v1/health-analysis/statistics`
- **Method**: GET
- **Purpose**: Get health analysis statistics for the user

#### 6. **Supported Conditions** - `/api/v1/health-analysis/supported-conditions`
- **Method**: GET
- **Purpose**: Get list of supported medical conditions

#### 7. **Model Performance** - `/api/v1/health-analysis/model-performance`
- **Method**: GET
- **Purpose**: Get performance metrics for health analysis models

### Emergency Triage Endpoints

#### 1. **Emergency Assessment** - `/api/v1/emergency-triage/assess-emergency`
- **Method**: POST
- **Purpose**: Assess emergency medical situations
- **Features**:
  - Emergency severity assessment
  - Immediate action recommendations
  - 911 call guidance
  - Urgent care vs emergency room guidance

#### 2. **Medical Triage** - `/api/v1/emergency-triage/triage`
- **Method**: POST
- **Purpose**: Perform medical triage
- **Triage Levels**:
  - Level 1 (Immediate): Life-threatening, call 911 immediately
  - Level 2 (Emergent): Urgent care needed within 1 hour
  - Level 3 (Urgent): Care needed within 4 hours
  - Level 4 (Less Urgent): Care needed within 24 hours
  - Level 5 (Non-Urgent): Can wait for regular appointment

#### 3. **Emergency Recommendations** - `/api/v1/emergency-triage/emergency-recommendations`
- **Method**: POST
- **Purpose**: Get immediate emergency recommendations

#### 4. **Emergency Symptoms** - `/api/v1/emergency-triage/emergency-symptoms`
- **Method**: GET
- **Purpose**: Get list of emergency symptoms and warning signs

#### 5. **Nearest Emergency Facilities** - `/api/v1/emergency-triage/nearest-emergency-facilities`
- **Method**: GET
- **Purpose**: Find nearest emergency medical facilities

#### 6. **Emergency Contacts** - `/api/v1/emergency-triage/emergency-contacts`
- **Method**: GET
- **Purpose**: Manage emergency contacts

#### 7. **Emergency Alert** - `/api/v1/emergency-triage/emergency-alert`
- **Method**: POST
- **Purpose**: Send emergency alerts

### Medical Insights Endpoints

#### 1. **Symptom Analysis** - `/api/v1/medical-insights/analyze-symptoms`
- **Method**: POST
- **Purpose**: Analyze symptoms and provide insights

#### 2. **Treatment Recommendations** - `/api/v1/medical-insights/treatment-recommendations`
- **Method**: POST
- **Purpose**: Get treatment recommendations

#### 3. **Risk Assessment** - `/api/v1/medical-insights/risk-assessment`
- **Method**: POST
- **Purpose**: Assess health risks

#### 4. **Drug Interactions** - `/api/v1/medical-insights/drug-interactions`
- **Method**: POST
- **Purpose**: Check drug interactions

#### 5. **Medical Guidelines** - `/api/v1/medical-insights/medical-guidelines`
- **Method**: POST
- **Purpose**: Get medical guidelines

#### 6. **Medical Literature** - `/api/v1/medical-insights/medical-literature`
- **Method**: POST
- **Purpose**: Search medical literature

#### 7. **Second Opinion** - `/api/v1/medical-insights/second-opinion`
- **Method**: POST
- **Purpose**: Get second medical opinion

## 🔧 Technical Features

### AI Models Integration
- **OpenAI Vision**: Primary model for medical image analysis
- **Google Vision API**: Fallback for image analysis
- **Azure Vision**: Additional fallback option
- **Custom Medical Models**: Specialized medical AI models

### Image Processing
- **Supported Formats**: JPEG, JPG, PNG, WEBP, HEIC
- **Max Size**: 10MB
- **Processing**: Real-time analysis with confidence scores

### Security & Authentication
- **JWT Authentication**: Bearer token authentication
- **CORS Support**: Configured for frontend integration
- **Rate Limiting**: Built-in protection against abuse
- **Data Privacy**: Secure handling of medical images

### Database Integration
- **PostgreSQL**: Primary database
- **Analysis History**: Stores user analysis results
- **User Data**: Secure storage of medical queries and results

## 🎯 Use Cases

### 1. **Skin Condition Analysis**
- Rashes, burns, bites, infections
- Mole analysis and skin cancer screening
- Acne and dermatological conditions

### 2. **Injury Assessment**
- Cuts, bruises, and wounds
- Fracture detection
- Sprain and strain assessment

### 3. **Eye Problems**
- Redness and irritation
- Swelling and discharge
- Vision-related issues

### 4. **Dental Issues**
- Cavity detection
- Gum disease assessment
- Tooth damage evaluation

### 5. **Emergency Situations**
- Chest pain and cardiac symptoms
- Breathing difficulties
- Severe injuries and bleeding
- Allergic reactions

### 6. **General Health Queries**
- Symptom analysis
- Treatment recommendations
- Medication information
- Preventive care guidance

## 📊 Service Performance

### Health Check Results
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
      "openai_vision": true,
      "google_vision": true,
      "azure_vision": true
    },
    "emergency_triage": "healthy"
  }
}
```

### Readiness Check Results
```json
{
  "status": "ready",
  "models": {
    "openai_vision": {
      "available": true,
      "model": "gpt-4o"
    },
    "google_vision": {
      "available": true,
      "model": "vision-api"
    },
    "azure_vision": {
      "available": true,
      "model": "computer-vision"
    }
  }
}
```

## 🔗 Integration Points

### Frontend Integration
- **CORS Configuration**: Supports `http://localhost:5173` (Vite dev server)
- **Authentication**: JWT token-based authentication
- **File Upload**: Multipart form data for image uploads
- **Real-time Processing**: Fast response times for medical analysis

### Backend Services
- **Auth Service**: User authentication and authorization
- **User Profile Service**: User context and preferences
- **Health Tracking Service**: Integration with health metrics
- **Medical Records Service**: Medical history integration

### External APIs
- **OpenAI API**: Advanced medical image analysis
- **Google Vision API**: Image recognition and analysis
- **Azure Vision API**: Computer vision capabilities

## 🚀 Getting Started

### 1. **Service Access**
```bash
# Health check
curl http://localhost:8008/health

# Readiness check
curl http://localhost:8008/ready
```

### 2. **Authentication**
```bash
# Generate JWT token
python generate_valid_jwt.py

# Use token for authenticated requests
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  http://localhost:8008/api/v1/health-analysis/supported-conditions
```

### 3. **Image Analysis**
```bash
# Upload and analyze medical image
curl -X POST \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "image=@medical_image.jpg" \
  -F "user_query=Please analyze this condition" \
  -F "body_part=skin" \
  -F "symptoms=redness and itching" \
  -F "urgency_level=normal" \
  http://localhost:8008/api/v1/health-analysis/analyze
```

## ⚠️ Important Disclaimers

1. **Not a Replacement**: This service is for informational purposes only and should not replace professional medical advice.

2. **Consult Healthcare Professionals**: Always consult with qualified healthcare professionals for proper diagnosis and treatment.

3. **Emergency Situations**: In emergency situations, call 911 or seek immediate medical attention.

4. **Data Privacy**: Medical images and data are processed securely but should be handled with appropriate privacy considerations.

## 🎉 Conclusion

The Health Analysis Service provides a comprehensive, AI-powered medical analysis platform that can:

- ✅ Analyze medical images for various conditions
- ✅ Provide preliminary diagnoses and severity assessments
- ✅ Offer treatment recommendations and medical advice
- ✅ Perform emergency triage and urgent care guidance
- ✅ Generate medical insights and risk assessments
- ✅ Support emergency situations with immediate guidance

The service is fully operational, well-integrated with the Personal Health Assistant platform, and ready for production use with appropriate medical disclaimers and professional oversight. 