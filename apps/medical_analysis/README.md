# Medical Analysis Service

A comprehensive medical analysis service that provides diagnosis, prognosis, and literature insights for the Personal Health Assistant platform.

## Overview

The Medical Analysis Service is designed to provide AI-powered medical analysis capabilities including:

- **Medical Diagnosis**: AI-powered diagnosis based on symptoms, medical history, and data
- **Medical Prognosis**: Disease progression and outcome prediction
- **Literature Insights**: Medical literature and research-based insights
- **Comprehensive Reports**: Complete medical analysis reports with recommendations

## Features

### 🏥 Medical Diagnosis
- AI-powered condition identification
- Differential diagnosis generation
- Confidence scoring and severity assessment
- ICD-10/11 code mapping
- Supporting evidence analysis

### 📊 Medical Prognosis
- Disease progression prediction
- Risk factor assessment
- Protective factor identification
- Survival rate estimation
- Quality of life impact analysis

### 📚 Literature Insights
- Research findings analysis
- Clinical guidelines integration
- Treatment evidence evaluation
- Recent studies and meta-analyses
- Expert opinions and consensus

### 📋 Comprehensive Reports
- Executive summaries
- Key findings extraction
- Risk assessment
- Treatment recommendations
- Monitoring plans

## API Endpoints

### Medical Analysis
- `POST /api/v1/medical-analysis/analyze` - Perform medical analysis based on type
- `POST /api/v1/medical-analysis/diagnosis` - Medical diagnosis analysis
- `POST /api/v1/medical-analysis/prognosis` - Medical prognosis analysis
- `POST /api/v1/medical-analysis/literature` - Medical literature analysis
- `POST /api/v1/medical-analysis/comprehensive` - Comprehensive analysis
- `POST /api/v1/medical-analysis/report` - Generate comprehensive report

### Service Information
- `GET /api/v1/medical-analysis/capabilities` - Get service capabilities
- `GET /api/v1/medical-analysis/health` - Health check

## Usage Examples

### Medical Diagnosis
```bash
curl -X POST "http://localhost:8006/api/v1/medical-analysis/diagnosis" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "symptoms": ["chest pain", "shortness of breath", "fatigue"],
    "medical_history": {"hypertension": true, "diabetes": false},
    "age": 45,
    "gender": "male",
    "urgency_level": 3
  }'
```

### Medical Prognosis
```bash
curl -X POST "http://localhost:8006/api/v1/medical-analysis/prognosis" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "symptoms": ["chest pain", "shortness of breath"],
    "medical_history": {"previous_heart_attack": true},
    "lab_results": {"troponin": "elevated"},
    "age": 45,
    "gender": "male"
  }'
```

### Literature Analysis
```bash
curl -X POST "http://localhost:8006/api/v1/medical-analysis/literature" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "symptoms": ["skin rash", "itching"],
    "medical_history": {"allergies": true},
    "domain": "dermatology"
  }'
```

### Comprehensive Analysis
```bash
curl -X POST "http://localhost:8006/api/v1/medical-analysis/comprehensive" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "symptoms": ["chest pain", "shortness of breath", "fatigue"],
    "medical_history": {"hypertension": true, "diabetes": false},
    "vital_signs": {"blood_pressure": "140/90", "heart_rate": 95},
    "lab_results": {"troponin": "normal", "cholesterol": "elevated"},
    "age": 45,
    "gender": "male",
    "urgency_level": 3
  }'
```

## Integration with Voice Input Service

The Medical Analysis Service integrates with the Voice Input Service to provide medical analysis for voice queries:

### Voice Input Integration Endpoints
- `POST /api/v1/voice-input/medical-analysis/analyze-query` - Analyze medical query from voice
- `POST /api/v1/voice-input/medical-analysis/analyze-vision` - Analyze medical query with vision data
- `POST /api/v1/voice-input/medical-analysis/generate-report` - Generate comprehensive report

### Example Voice Query Analysis
```bash
curl -X POST "http://localhost:8003/api/v1/voice-input/medical-analysis/analyze-query" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "query_text": "I have chest pain and shortness of breath",
    "symptoms": ["chest pain", "shortness of breath"],
    "medical_history": {"hypertension": true},
    "analysis_type": "comprehensive"
  }'
```

## Medical Domains

The service supports analysis across multiple medical domains:

- **Cardiology**: Heart conditions, cardiovascular health
- **Dermatology**: Skin conditions, lesions, rashes
- **Neurology**: Brain and nervous system conditions
- **Oncology**: Cancer and tumor analysis
- **Endocrinology**: Hormonal and metabolic conditions
- **Gastroenterology**: Digestive system conditions
- **Respiratory**: Lung and breathing conditions
- **General**: General health assessment

## AI Models

The service uses multiple AI models for analysis:

- **OpenAI GPT-4**: High-quality medical analysis
- **GROQ LLaMA**: Fast inference for real-time analysis
- **Medical Knowledge Base**: Domain-specific medical knowledge
- **Pattern-based Analysis**: Fallback analysis when AI models are unavailable

## Safety Features

- **Medical Disclaimers**: Automatic inclusion of appropriate medical disclaimers
- **Confidence Scoring**: Transparent confidence levels for all analyses
- **Professional Consultation**: Always recommends professional medical consultation
- **Emergency Detection**: Automatic detection of emergency situations
- **Educational Purpose**: Designed for educational purposes only

## Configuration

### Environment Variables
```bash
# Service Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
SERVICE_PORT=8006

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/health_assistant

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key

# AI APIs
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key

# CORS
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## Development

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- OpenAI API key
- GROQ API key

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd PersonalHealthAssistant

# Install dependencies
pip install -r apps/medical_analysis/requirements.txt

# Set up environment variables
export OPENAI_API_KEY=your-openai-api-key
export GROQ_API_KEY=your-groq-api-key

# Run the service
cd apps/medical_analysis
python main.py
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose up medical-analysis-service

# Or build individually
docker build -f apps/medical_analysis/Dockerfile -t medical-analysis-service .
docker run -p 8006:8006 medical-analysis-service
```

## Testing

### Health Check
```bash
curl http://localhost:8006/health
```

### Capabilities Check
```bash
curl http://localhost:8006/api/v1/medical-analysis/capabilities
```

### Test Medical Analysis
```bash
# Test diagnosis
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

## Monitoring

The service includes comprehensive monitoring:

- **Health Checks**: Automatic health monitoring
- **Prometheus Metrics**: Performance and usage metrics
- **Grafana Dashboards**: Visualization of service metrics
- **Logging**: Structured logging for debugging

## Security

- **JWT Authentication**: Secure authentication with JWT tokens
- **CORS Protection**: Cross-origin resource sharing protection
- **Input Validation**: Comprehensive input validation
- **Error Handling**: Secure error handling without information leakage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This service is designed for educational purposes only and should not replace professional medical advice. Always consult with qualified healthcare professionals for medical diagnosis and treatment. 