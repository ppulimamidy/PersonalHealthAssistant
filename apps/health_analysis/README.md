# Health Analysis Service

A comprehensive medical AI service for analyzing health-related images and providing detailed medical insights, diagnoses, and recommendations.

## 🏥 Features

### Core Capabilities
- **Medical Image Analysis**: Analyze images for various health conditions using BioGPT and PubMedGPT
- **Condition Detection**: Detect specific medical conditions (skin, injury, eye, dental, etc.)
- **Emergency Triage**: Assess emergency situations and provide immediate guidance
- **Medical Insights**: Generate detailed medical analysis and recommendations
- **Treatment Recommendations**: Provide personalized treatment options
- **Risk Assessment**: Evaluate health risks and potential complications

### Medical AI Integration
- **BioGPT**: Microsoft's biomedical language model for clinical analysis
- **PubMedGPT**: Stanford's medical research model for evidence-based insights
- **Medical Specialization**: Models specifically trained on biomedical literature
- **Evidence-Based**: Responses backed by medical research and clinical guidelines

### Hybrid AI Models Integration
- **BioGPT + PubMedGPT + OpenAI Vision**: Combined analysis for maximum accuracy
- **OpenAI Vision**: Image-specific visual analysis and feature detection
- **BioGPT**: Biomedical insights and clinical terminology
- **PubMedGPT**: Medical research and evidence-based recommendations
- **Google Vision API**: Additional fallback option
- **Azure Vision**: Additional fallback option
- **Custom Medical Models**: Specialized medical AI models

### Supported Medical Conditions
- **Skin Conditions**: Rashes, burns, bites, infections, moles, acne
- **Injuries**: Cuts, bruises, fractures, sprains
- **Eye Problems**: Redness, swelling, discharge, vision issues
- **Dental Issues**: Cavities, gum disease, tooth damage
- **Respiratory**: Breathing issues, chest problems
- **Gastrointestinal**: Abdominal issues, digestive problems
- **Cardiac**: Heart-related symptoms
- **Neurological**: Brain and nervous system issues
- **Pediatric**: Child-specific medical concerns

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- OpenAI API Key (for GPT-4 Vision - fallback)
- Google Vision API Key (optional)
- Azure Vision API Key (optional)
- **Medical AI Models**: BioGPT and PubMedGPT (automatically downloaded)

### Environment Variables
```bash
# Required (for fallback)
OPENAI_API_KEY=your_openai_api_key_here

# Optional
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here
AZURE_VISION_API_KEY=your_azure_vision_api_key_here
AZURE_VISION_ENDPOINT=your_azure_vision_endpoint_here

# Medical AI Models (automatically configured)
# BioGPT and PubMedGPT will be downloaded automatically
```

### Running with Docker Compose
```bash
# Build and start the service
docker compose up -d health-analysis-service

# Check service health
curl http://health-analysis.localhost/health

# Access API documentation
open http://health-analysis.localhost/docs
```

### Running Locally
```bash
# Install dependencies
pip install -r apps/health_analysis/requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_openai_api_key_here

# Run the service
cd apps/health_analysis
python main.py
```

## 📋 API Endpoints

### Health Analysis
- `POST /api/v1/health-analysis/analyze` - Analyze health images
- `POST /api/v1/health-analysis/detect-condition` - Detect specific conditions
- `POST /api/v1/health-analysis/medical-query` - Process medical queries
- `GET /api/v1/health-analysis/history` - Get analysis history
- `GET /api/v1/health-analysis/statistics` - Get analysis statistics
- `GET /api/v1/health-analysis/supported-conditions` - Get supported conditions
- `GET /api/v1/health-analysis/model-performance` - Get model performance

### Medical Insights
- `POST /api/v1/medical-insights/analyze-symptoms` - Analyze symptoms
- `POST /api/v1/medical-insights/treatment-recommendations` - Get treatment recommendations
- `POST /api/v1/medical-insights/risk-assessment` - Assess health risks
- `GET /api/v1/medical-insights/medical-literature` - Search medical literature
- `GET /api/v1/medical-insights/drug-interactions` - Check drug interactions
- `GET /api/v1/medical-insights/medical-guidelines` - Get medical guidelines
- `POST /api/v1/medical-insights/second-opinion` - Get second medical opinion

### Emergency Triage
- `POST /api/v1/emergency-triage/assess-emergency` - Assess emergency situations
- `POST /api/v1/emergency-triage/triage` - Perform medical triage
- `POST /api/v1/emergency-triage/emergency-recommendations` - Get emergency recommendations
- `GET /api/v1/emergency-triage/emergency-symptoms` - Get emergency symptoms
- `GET /api/v1/emergency-triage/nearest-emergency-facilities` - Find emergency facilities
- `POST /api/v1/emergency-triage/emergency-contact` - Manage emergency contacts
- `GET /api/v1/emergency-triage/emergency-contacts` - Get emergency contacts
- `POST /api/v1/emergency-triage/emergency-alert` - Send emergency alerts

## 🔧 Usage Examples

### Analyze Health Image
```bash
curl -X POST "http://health-analysis.localhost/api/v1/health-analysis/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@path/to/medical_image.jpg" \
  -F "user_query=I have this rash on my arm" \
  -F "body_part=arm" \
  -F "symptoms=itching and redness" \
  -F "urgency_level=normal"
```

### Emergency Assessment
```bash
curl -X POST "http://health-analysis.localhost/api/v1/emergency-triage/assess-emergency" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@path/to/injury_image.jpg" \
  -F "symptoms=severe pain and swelling" \
  -F "body_part=ankle" \
  -F "pain_level=8" \
  -F "duration=2 hours"
```

### Medical Query
```bash
curl -X POST "http://health-analysis.localhost/api/v1/health-analysis/medical-query" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What could cause persistent headaches?",
    "query_type": "symptom",
    "urgency_level": "normal",
    "age": 35,
    "gender": "female"
  }'
```

## 🏗️ Architecture

### Service Components
- **FastAPI Application**: Main web framework
- **Health Analysis Service**: Core medical analysis logic
- **Medical AI Service**: BioGPT and PubMedGPT integration
- **AI Models**: BioGPT, PubMedGPT, OpenAI Vision, Google Vision, Azure Vision
- **Database**: PostgreSQL for storing analysis results
- **Redis**: Caching and session management
- **Authentication**: JWT-based authentication middleware

### Data Flow
1. **Image Upload**: User uploads medical image
2. **Hybrid Analysis**: 
   - OpenAI Vision analyzes visual features and conditions
   - BioGPT and PubMedGPT provide clinical insights and medical context
3. **Result Enhancement**: Combine and enhance results from all models
4. **Condition Merging**: Merge duplicate conditions and enhance with multi-model insights
5. **Medical Processing**: Generate medical insights and recommendations
6. **Risk Assessment**: Evaluate urgency and risk levels
7. **Response**: Return comprehensive medical analysis

## 🔒 Security & Privacy

### Data Protection
- All medical data is encrypted in transit and at rest
- HIPAA-compliant data handling practices
- Secure authentication and authorization
- Audit logging for all medical interactions

### Privacy Features
- User data isolation
- Secure image processing
- No data retention beyond required periods
- Compliance with medical privacy regulations

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest apps/health_analysis/tests/unit/

# Integration tests
pytest apps/health_analysis/tests/integration/

# End-to-end tests
pytest apps/health_analysis/tests/e2e/
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=apps/health_analysis --cov-report=html
```

## 📊 Monitoring

### Health Checks
- Service health: `GET /health`
- Readiness check: `GET /ready`
- Model status: Available through health endpoint

### Metrics
- Request latency
- Error rates
- AI model performance
- Processing times

### Logging
- Structured logging with correlation IDs
- Medical event logging
- Error tracking and alerting

## 🚨 Emergency Features

### Triage Levels
- **Level 1 (Immediate)**: Life-threatening, call 911 immediately
- **Level 2 (Emergent)**: Urgent care needed within 1 hour
- **Level 3 (Urgent)**: Care needed within 4 hours
- **Level 4 (Less Urgent)**: Care needed within 24 hours
- **Level 5 (Non-Urgent)**: Can wait for regular appointment

### Emergency Alerts
- Automatic emergency detection
- Contact notification system
- Location-based facility finding
- Real-time emergency guidance

## 📚 Medical Disclaimers

⚠️ **Important Medical Disclaimer**

This service provides AI-powered medical analysis for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for:

- Proper medical diagnosis
- Treatment recommendations
- Emergency medical situations
- Medication decisions

The service should be used as a supplementary tool to support healthcare decisions, not as a replacement for professional medical care.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

For medical emergencies:
- Call 911 immediately
- Contact your healthcare provider
- Visit the nearest emergency room 