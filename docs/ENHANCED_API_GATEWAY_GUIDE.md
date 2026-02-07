# 🚀 Enhanced API Gateway Guide

## **Overview**

The Enhanced API Gateway provides a unified entry point for all Personal Physician Assistant (PPA) services, featuring composite endpoints that aggregate functionality from multiple microservices and provide intelligent routing with resilience patterns.

## **🎯 Key Features**

### **1. Composite Health Endpoints**
- **Unified Health Analysis**: Single endpoints that combine data from multiple services
- **AI-Powered Insights**: Integration with AI Reasoning Orchestrator for intelligent analysis
- **Reduced Latency**: Fewer round trips to backend services
- **Better UX**: Simplified frontend integration

### **2. Service Registry & Routing**
- **Dynamic Service Discovery**: Automatic routing to appropriate microservices
- **Circuit Breakers**: Resilience patterns for service failures
- **Retry Logic**: Automatic retry with exponential backoff
- **Timeout Handling**: Configurable timeouts per service

### **3. Performance & Monitoring**
- **Request Tracking**: Unique request IDs for tracing
- **Metrics Collection**: Prometheus metrics for monitoring
- **Rate Limiting**: Per-user and global rate limiting
- **Caching**: Redis-based caching for frequently accessed data

## **🔧 Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Microservices │
│   (React/RN)    │◄──►│   (Enhanced)    │◄──►│   (Backend)     │
│                 │    │                 │    │                 │
│ - Single API    │    │ - Composite     │    │ - AI Reasoning  │
│ - Unified Data  │    │ - Routing       │    │ - Health Data   │
│ - Type Safety   │    │ - Resilience    │    │ - Medical Rec   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## **🎯 Composite Endpoints**

### **1. Symptom Analysis**
```http
POST /health/analyze-symptoms
Content-Type: application/json
Authorization: Bearer <token>

{
  "symptoms": ["fatigue", "headache"],
  "include_vitals": true,
  "include_medications": true,
  "generate_insights": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "Analyze symptoms: fatigue, headache",
    "reasoning": "Based on your recent data, your fatigue appears to be related to...",
    "insights": [
      {
        "type": "symptom_analysis",
        "title": "Sleep Quality Impact",
        "description": "Your sleep efficiency was 75% last night...",
        "confidence": "high",
        "actionable": true
      }
    ],
    "recommendations": [
      {
        "title": "Improve Sleep Hygiene",
        "description": "Consider going to bed 30 minutes earlier...",
        "priority": "high",
        "actionable": true
      }
    ],
    "confidence": "medium",
    "data_sources": ["health_tracking", "medical_records", "knowledge_graph"]
  }
}
```

### **2. Daily Health Summary**
```http
GET /health/daily-summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "daily-user123-2024-01-15",
    "date": "2024-01-15T00:00:00Z",
    "summary": "Your health is generally good today. Key observations include...",
    "health_score": 0.85,
    "data_quality_score": 0.92,
    "key_insights": [...],
    "recommendations": [...],
    "trends": [...],
    "anomalies": [...]
  }
}
```

### **3. Doctor Mode Report**
```http
POST /health/doctor-report
Content-Type: application/json
Authorization: Bearer <token>

{
  "time_window": "30d"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "patient_id": "user123",
    "report_date": "2024-01-15T10:30:00Z",
    "time_period": "30d",
    "summary": "Executive summary for healthcare provider...",
    "key_insights": [...],
    "recommendations": [...],
    "trends": [...],
    "anomalies": [...],
    "confidence_score": 0.88,
    "next_steps": [
      "Schedule follow-up appointment",
      "Monitor blood pressure trends",
      "Review medication effectiveness"
    ]
  }
}
```

### **4. Natural Language Health Queries**
```http
POST /health/query
Content-Type: application/json
Authorization: Bearer <token>

{
  "question": "Why do I feel tired today?",
  "time_window": "24h"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "Why do I feel tired today?",
    "reasoning": "Based on your recent data, your fatigue appears to be related to...",
    "insights": [...],
    "recommendations": [...],
    "confidence": "high",
    "processing_time": 2.3,
    "data_sources": ["health_tracking", "medical_records", "knowledge_graph"]
  }
}
```

### **5. Unified Dashboard**
```http
GET /health/unified-dashboard
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "daily_summary": {...},
    "recent_insights": [...],
    "health_metrics": {
      "vitals": {...},
      "symptoms": [...],
      "medications": [...],
      "nutrition": [...],
      "activity": {...}
    },
    "recommendations": [...],
    "alerts": [...]
  }
}
```

## **🎯 Service Routes**

### **AI Reasoning Orchestrator**
```http
POST /ai-reasoning/api/v1/reason
GET /ai-reasoning/api/v1/insights/daily-summary
POST /ai-reasoning/api/v1/doctor-mode/report
POST /ai-reasoning/api/v1/query
```

### **GraphQL BFF**
```http
POST /graphql/graphql
GET /graphql/api/v1/health/daily-summary
POST /graphql/api/v1/health/query
POST /graphql/api/v1/health/doctor-report
```

### **AI Insights**
```http
GET /ai-insights/api/v1/ai-insights/insights
GET /ai-insights/api/v1/ai-insights/recommendations
GET /ai-insights/api/v1/ai-insights/patterns
```

### **Medical Records**
```http
GET /medical-records/api/v1/medical-records/records
POST /medical-records/api/v1/medical-records/records
GET /medical-records/api/v1/medical-records/medications
```

### **Nutrition**
```http
GET /nutrition/api/v1/nutrition/meals
POST /nutrition/api/v1/nutrition/meals
GET /nutrition/api/v1/nutrition/analysis
```

### **Device Data**
```http
GET /device-data/api/v1/device-data/vitals
POST /device-data/api/v1/device-data/vitals
GET /device-data/api/v1/device-data/activity
```

## **🔧 Frontend Integration Examples**

### **React/TypeScript Example**
```typescript
// hooks/useHealthAPI.ts
class HealthAPI {
  private baseURL: string;
  private token: string;

  constructor(baseURL: string, token: string) {
    this.baseURL = baseURL;
    this.token = token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async analyzeSymptoms(symptoms: string[], options: any = {}) {
    return this.request('/health/analyze-symptoms', {
      method: 'POST',
      body: JSON.stringify({
        symptoms,
        include_vitals: options.includeVitals ?? true,
        include_medications: options.includeMedications ?? true,
        generate_insights: options.generateInsights ?? true,
      }),
    });
  }

  async getDailySummary() {
    return this.request('/health/daily-summary');
  }

  async generateDoctorReport(timeWindow: string = '30d') {
    return this.request('/health/doctor-report', {
      method: 'POST',
      body: JSON.stringify({ time_window: timeWindow }),
    });
  }

  async queryHealth(question: string, timeWindow: string = '24h') {
    return this.request('/health/query', {
      method: 'POST',
      body: JSON.stringify({ question, time_window: timeWindow }),
    });
  }

  async getUnifiedDashboard() {
    return this.request('/health/unified-dashboard');
  }
}

// React hook
export const useHealthAPI = () => {
  const [token] = useState(() => localStorage.getItem('authToken'));
  const [api] = useState(() => new HealthAPI('http://api-gateway.localhost', token!));

  return {
    analyzeSymptoms: api.analyzeSymptoms.bind(api),
    getDailySummary: api.getDailySummary.bind(api),
    generateDoctorReport: api.generateDoctorReport.bind(api),
    queryHealth: api.queryHealth.bind(api),
    getUnifiedDashboard: api.getUnifiedDashboard.bind(api),
  };
};
```

### **React Component Example**
```typescript
// components/SymptomAnalyzer.tsx
import React, { useState } from 'react';
import { useHealthAPI } from '../hooks/useHealthAPI';

export const SymptomAnalyzer: React.FC = () => {
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const { analyzeSymptoms } = useHealthAPI();

  const handleAnalyze = async () => {
    if (symptoms.length === 0) return;

    setLoading(true);
    try {
      const result = await analyzeSymptoms(symptoms);
      setAnalysis(result.data);
    } catch (error) {
      console.error('Error analyzing symptoms:', error);
    } finally {
      setLoading(false);
    }
  };

  const addSymptom = (symptom: string) => {
    if (!symptoms.includes(symptom)) {
      setSymptoms([...symptoms, symptom]);
    }
  };

  return (
    <div className="symptom-analyzer">
      <h2>Analyze Your Symptoms</h2>
      
      <div className="symptom-input">
        <input
          type="text"
          placeholder="Enter a symptom..."
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value) {
              addSymptom(e.currentTarget.value);
              e.currentTarget.value = '';
            }
          }}
        />
      </div>

      <div className="symptoms-list">
        {symptoms.map((symptom, index) => (
          <span key={index} className="symptom-tag">
            {symptom}
            <button onClick={() => setSymptoms(symptoms.filter((_, i) => i !== index))}>
              ×
            </button>
          </span>
        ))}
      </div>

      <button 
        onClick={handleAnalyze} 
        disabled={symptoms.length === 0 || loading}
        className="analyze-button"
      >
        {loading ? 'Analyzing...' : 'Analyze Symptoms'}
      </button>

      {analysis && (
        <div className="analysis-results">
          <h3>Analysis Results</h3>
          
          <div className="reasoning">
            <h4>Analysis</h4>
            <p>{analysis.reasoning}</p>
          </div>

          <div className="insights">
            <h4>Key Insights</h4>
            {analysis.insights.map((insight: any) => (
              <div key={insight.id} className="insight">
                <h5>{insight.title}</h5>
                <p>{insight.description}</p>
                <span className={`confidence confidence-${insight.confidence}`}>
                  {insight.confidence} confidence
                </span>
              </div>
            ))}
          </div>

          <div className="recommendations">
            <h4>Recommendations</h4>
            {analysis.recommendations.map((rec: any) => (
              <div key={rec.id} className="recommendation">
                <h5>{rec.title}</h5>
                <p>{rec.description}</p>
                <span className={`priority priority-${rec.priority}`}>
                  {rec.priority} priority
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

## **🎯 Benefits of Enhanced API Gateway**

### **1. Simplified Frontend Integration**
- **Single Entry Point**: All health data through one API
- **Unified Response Format**: Consistent data structure
- **Type Safety**: Strong typing with OpenAPI/Swagger
- **Error Handling**: Standardized error responses

### **2. Performance Optimization**
- **Reduced Latency**: Fewer round trips to backend
- **Intelligent Caching**: Cache frequently accessed data
- **Parallel Processing**: Aggregate data from multiple services
- **Load Balancing**: Distribute requests across services

### **3. Resilience & Reliability**
- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Handle temporary service failures
- **Fallback Mechanisms**: Graceful degradation
- **Health Monitoring**: Proactive service health checks

### **4. Security & Compliance**
- **Centralized Auth**: Single authentication point
- **Rate Limiting**: Prevent abuse and ensure fair usage
- **Request Tracing**: Full request/response tracing
- **Audit Logging**: Comprehensive audit trail

## **🎯 Monitoring & Observability**

### **Metrics Available**
- **Request Count**: Total requests by endpoint and status
- **Request Duration**: Response times by endpoint
- **Active Requests**: Current active requests by service
- **Circuit Breaker Status**: Open/closed state per service
- **Rate Limit Usage**: Rate limit consumption per user

### **Health Checks**
```http
GET /health          # Gateway health
GET /ready           # Readiness check (all services)
GET /metrics         # Prometheus metrics
```

### **Request Tracing**
Every request includes:
- **Request ID**: Unique identifier for tracing
- **User Context**: Authenticated user information
- **Service Routing**: Which service handled the request
- **Timing Information**: Request duration and timing

## **🎯 Configuration**

### **Environment Variables**
```bash
# Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
USER_PROFILE_SERVICE_URL=http://user-profile-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8000
AI_REASONING_ORCHESTRATOR_URL=http://ai-reasoning-orchestrator:8000
GRAPHQL_BFF_URL=http://graphql-bff:8000
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8000
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8000
NUTRITION_SERVICE_URL=http://nutrition-service:8000
DEVICE_DATA_SERVICE_URL=http://device-data-service:8000

# Redis Configuration
REDIS_URL=redis://redis:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## **🎯 Next Steps**

1. **Deploy Enhanced Gateway**: Deploy the enhanced API Gateway with new services
2. **Update Frontend**: Integrate frontend applications with composite endpoints
3. **Monitor Performance**: Set up monitoring and alerting for the new endpoints
4. **Optimize Caching**: Configure Redis caching strategies for optimal performance
5. **Add Real-time Features**: Implement WebSocket support for real-time updates

The Enhanced API Gateway transforms your microservices architecture into a cohesive, high-performance system that provides excellent developer experience and user satisfaction! 🚀
