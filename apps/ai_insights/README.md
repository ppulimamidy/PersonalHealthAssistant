# AI Insights Service

Advanced AI-powered health insights and recommendations for the VitaSense Personal Health Assistant platform.

## Overview

The AI Insights Service provides intelligent analysis of health data to generate meaningful insights, detect patterns, and provide personalized recommendations. It uses advanced machine learning algorithms and AI agents to process various health metrics and deliver actionable health intelligence.

## Features

### 🤖 AI Agents
- **Insight Generator Agent**: Analyzes health data to generate meaningful insights
- **Pattern Detection Agent**: Identifies temporal and behavioral patterns in health data
- **Trend Analysis Agent**: Detects trends and changes in health metrics
- **Risk Assessment Agent**: Evaluates health risks and provides risk scores
- **Recommendation Engine Agent**: Generates personalized health recommendations
- **Health Scoring Agent**: Calculates comprehensive health scores
- **Anomaly Detection Agent**: Identifies unusual patterns and anomalies
- **Predictive Analytics Agent**: Provides predictive health insights
- **Behavioral Analysis Agent**: Analyzes behavioral patterns and habits
- **Wellness Assessment Agent**: Evaluates overall wellness and lifestyle

### 📊 Data Models
- **Health Insights**: Comprehensive insight data with confidence scoring
- **Health Patterns**: Temporal and behavioral pattern detection
- **Health Scores**: Multi-dimensional health scoring system
- **Risk Assessments**: Risk evaluation and mitigation strategies
- **Recommendations**: Personalized health recommendations
- **Wellness Indices**: Multi-dimensional wellness assessment

### 🔍 Analysis Capabilities
- **Temporal Pattern Detection**: Daily, weekly, monthly, and seasonal patterns
- **Behavioral Analysis**: Activity, sleep, nutrition, and lifestyle patterns
- **Trend Analysis**: Statistical trend detection and forecasting
- **Correlation Analysis**: Multi-metric correlation discovery
- **Anomaly Detection**: Statistical and ML-based anomaly identification
- **Risk Assessment**: Comprehensive health risk evaluation
- **Predictive Modeling**: Future health outcome prediction

## Architecture

```
AI Insights Service
├── agents/                 # AI agents for analysis
│   ├── base_insight_agent.py
│   ├── insight_generator_agent.py
│   ├── pattern_detection_agent.py
│   └── ...
├── api/                   # REST API endpoints
│   ├── insights.py
│   ├── recommendations.py
│   ├── health_scores.py
│   └── ...
├── models/                # Data models
│   ├── insight_models.py
│   ├── recommendation_models.py
│   └── health_score_models.py
├── services/              # Business logic services
│   ├── insight_service.py
│   ├── recommendation_service.py
│   └── ...
└── main.py               # FastAPI application
```

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   cd apps/ai_insights
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the service**
   ```bash
   python main.py
   ```

The service will be available at `http://localhost:8003`

## API Documentation

### Base URL
```
http://localhost:8003/api/v1/ai-insights
```

### Health Check
```bash
GET /health
```

### Insights API

#### Generate Insights
```bash
POST /insights/generate
Content-Type: application/json

{
  "patient_id": "uuid",
  "data": {
    "vital_signs": [...],
    "activity_data": [...],
    "sleep_data": [...],
    "nutrition_data": [...]
  }
}
```

#### Get Insights
```bash
GET /insights?patient_id=uuid&insight_type=trend_analysis&limit=50
```

#### Get Insight by ID
```bash
GET /insights/{insight_id}?patient_id=uuid
```

#### Create Insight
```bash
POST /insights
Content-Type: application/json

{
  "patient_id": "uuid",
  "insight_type": "trend_analysis",
  "category": "health_metrics",
  "title": "Heart Rate Trend",
  "description": "Your heart rate shows a declining trend...",
  "confidence_score": 0.85,
  "relevance_score": 0.75
}
```

#### Update Insight
```bash
PUT /insights/{insight_id}?patient_id=uuid
Content-Type: application/json

{
  "title": "Updated Heart Rate Trend",
  "confidence_score": 0.90
}
```

#### Delete Insight
```bash
DELETE /insights/{insight_id}?patient_id=uuid
```

#### Get Insights Summary
```bash
GET /insights/summary/{patient_id}
```

#### Search Insights
```bash
GET /insights/search/{patient_id}?search_term=heart&limit=20
```

#### Get Insights Timeline
```bash
GET /insights/timeline/{patient_id}?start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

### Patterns API

#### Get Health Patterns
```bash
GET /patterns?patient_id=uuid&pattern_type=temporal&limit=50
```

### Health Scores API

#### Get Health Scores
```bash
GET /health-scores?patient_id=uuid&score_type=overall_health&limit=50
```

### Agents API

#### Get Agent Status
```bash
GET /agents/status
```

## Data Models

### Insight Types
- `trend_analysis`: Trend detection and analysis
- `pattern_detection`: Pattern identification
- `anomaly_detection`: Anomaly detection
- `risk_assessment`: Risk evaluation
- `predictive_analysis`: Predictive insights
- `behavioral_insight`: Behavioral analysis
- `clinical_insight`: Clinical insights
- `lifestyle_insight`: Lifestyle analysis
- `nutrition_insight`: Nutrition analysis
- `fitness_insight`: Fitness analysis
- `sleep_insight`: Sleep analysis
- `stress_insight`: Stress analysis
- `medication_insight`: Medication analysis
- `vital_sign_insight`: Vital signs analysis
- `lab_result_insight`: Lab results analysis

### Insight Categories
- `health_metrics`: Health metric insights
- `behavior`: Behavioral insights
- `lifestyle`: Lifestyle insights
- `clinical`: Clinical insights
- `preventive`: Preventive care insights
- `diagnostic`: Diagnostic insights
- `prognostic`: Prognostic insights
- `therapeutic`: Therapeutic insights

### Severity Levels
- `low`: Low priority insights
- `medium`: Medium priority insights
- `high`: High priority insights
- `critical`: Critical insights requiring immediate attention

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio
from uuid import uuid4

async def generate_insights():
    async with httpx.AsyncClient() as client:
        # Sample health data
        health_data = {
            "patient_id": str(uuid4()),
            "vital_signs": [
                {
                    "metric": "heart_rate",
                    "value": 75,
                    "timestamp": "2024-01-15T10:00:00Z",
                    "unit": "bpm"
                }
            ],
            "activity_data": [
                {
                    "date": "2024-01-15",
                    "steps": 8500,
                    "calories": 2100,
                    "active_minutes": 35
                }
            ]
        }
        
        # Generate insights
        response = await client.post(
            "http://localhost:8003/api/v1/ai-insights/insights/generate",
            json=health_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Generated {result['data']['metadata']['total_insights']} insights")
            return result
        else:
            print(f"Error: {response.status_code}")

# Run the example
asyncio.run(generate_insights())
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function generateInsights() {
    const healthData = {
        patient_id: "123e4567-e89b-12d3-a456-426614174000",
        vital_signs: [
            {
                metric: "heart_rate",
                value: 75,
                timestamp: "2024-01-15T10:00:00Z",
                unit: "bpm"
            }
        ],
        activity_data: [
            {
                date: "2024-01-15",
                steps: 8500,
                calories: 2100,
                active_minutes: 35
            }
        ]
    };

    try {
        const response = await axios.post(
            'http://localhost:8003/api/v1/ai-insights/insights/generate',
            healthData
        );
        
        console.log(`Generated ${response.data.data.metadata.total_insights} insights`);
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

generateInsights();
```

## Testing

### Run Tests
```bash
python test_ai_insights_service.py
```

### Test Coverage
The test suite covers:
- Service health checks
- API endpoint functionality
- AI agent initialization and execution
- Data model validation
- Insight generation with sample data
- Pattern detection algorithms

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/ai_insights

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Service
SERVICE_PORT=8003
SERVICE_HOST=0.0.0.0
```

### AI Model Configuration

The service supports various AI models and algorithms:

```python
# Example configuration
AI_MODELS = {
    "trend_analyzer": {
        "type": "statistical_trend",
        "algorithms": ["linear_regression", "moving_average"],
        "parameters": {
            "window_size": 7,
            "confidence_level": 0.95
        }
    },
    "pattern_detector": {
        "type": "pattern_recognition",
        "algorithms": ["fourier_analysis", "wavelet_analysis"],
        "parameters": {
            "pattern_types": ["cyclic", "seasonal", "trending"],
            "min_pattern_length": 3
        }
    }
}
```

## Monitoring and Observability

### Health Checks
- `/health`: Service health status
- `/ready`: Service readiness status
- `/api/v1/ai-insights/insights/health`: Insights API health
- `/api/v1/ai-insights/patterns/health`: Patterns API health

### Metrics
The service exposes Prometheus metrics for:
- Request counts and durations
- AI agent execution times
- Insight generation success rates
- Database query performance

### Logging
Structured logging with correlation IDs for request tracing.

## Deployment

### Docker
```bash
docker build -t ai-insights-service .
docker run -p 8003:8003 ai-insights-service
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-insights-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-insights-service
  template:
    metadata:
      labels:
        app: ai-insights-service
    spec:
      containers:
      - name: ai-insights-service
        image: ai-insights-service:latest
        ports:
        - containerPort: 8003
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-insights-secrets
              key: database-url
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Roadmap

- [ ] Advanced predictive models
- [ ] Real-time streaming insights
- [ ] Integration with external health APIs
- [ ] Mobile SDK
- [ ] Advanced visualization capabilities
- [ ] Multi-language support
- [ ] Enhanced security features 