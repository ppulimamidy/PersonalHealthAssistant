# GraphQL BFF Service - Comprehensive Documentation

## **Service Overview**

The **GraphQL BFF (Backend-for-Frontend) Service** provides a unified, type-safe GraphQL interface for frontend applications to interact with the Personal Physician Assistant (PPA) backend. It aggregates data from multiple microservices and provides efficient, tailored data access patterns for web and mobile applications.

### **Service Purpose**
- **Unified GraphQL Interface**: Single endpoint for all health data access
- **Type-Safe Data Access**: Strong typing with GraphQL schema
- **Efficient Data Fetching**: Request only the data you need
- **Frontend Optimization**: Tailored for frontend application needs
- **Real-time Support**: WebSocket subscriptions for live updates

### **Key Capabilities**
- **GraphQL Schema**: Comprehensive schema for all health data types
- **Data Aggregation**: Combines data from multiple microservices
- **Intelligent Caching**: Redis-based caching for performance
- **Real-time Subscriptions**: WebSocket support for live updates
- **REST Fallbacks**: REST endpoints for non-GraphQL clients

## **Architecture & Design**

### **Service Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    GraphQL BFF Service                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastAPI   │  │   Strawberry│  │   Redis     │        │
│  │   Server    │  │   GraphQL   │  │   Cache     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Data        │  │ Reasoning   │  │ Cache       │        │
│  │ Service     │  │ Service     │  │ Service     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ AI          │  │ Health      │  │ Medical     │        │
│  │ Reasoning   │  │ Tracking    │  │ Records     │        │
│  │ Orchestrator│  │ Service     │  │ Service     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### **Core Components**

#### **1. GraphQL Schema**
- **Purpose**: Defines the complete data model for health information
- **Capabilities**:
  - Type-safe data models
  - Query, mutation, and subscription support
  - Field-level resolvers
  - Input validation
- **Key Types**:
  - `HealthInsight`: Health insights with evidence
  - `ReasoningResult`: AI reasoning results
  - `DailyInsight`: Daily health summaries
  - `DoctorReport`: Comprehensive medical reports
  - `RealTimeInsight`: Live health updates

#### **2. Data Service**
- **Purpose**: Aggregates data from multiple microservices
- **Capabilities**:
  - Parallel data fetching
  - Data transformation and normalization
  - Error handling and fallbacks
  - Data quality assessment
- **Data Sources**:
  - AI Reasoning Orchestrator
  - Health Tracking Service
  - Medical Records Service
  - AI Insights Service

#### **3. Reasoning Service**
- **Purpose**: Handles health reasoning queries through AI Reasoning Orchestrator
- **Capabilities**:
  - Natural language query processing
  - Health reasoning and analysis
  - Doctor report generation
  - Trend analysis and insights
- **Integration**:
  - Direct integration with AI Reasoning Orchestrator
  - Fallback mechanisms for service failures
  - Caching of reasoning results

#### **4. Cache Service**
- **Purpose**: Provides intelligent caching for improved performance
- **Capabilities**:
  - Redis-based caching
  - Cache key generation and management
  - Cache invalidation strategies
  - Cache statistics and monitoring
- **Cache Types**:
  - Reasoning result caching
  - Daily summary caching
  - Health data caching
  - User-specific caching

## **GraphQL Schema**

### **Core Types**

#### **HealthInsight**
```graphql
type HealthInsight {
  id: ID!
  type: String!
  title: String!
  description: String!
  severity: String
  confidence: String!
  evidence: [Evidence!]!
  actionable: Boolean!
  timestamp: DateTime!
}
```

#### **ReasoningResult**
```graphql
type ReasoningResult {
  query: String!
  reasoning: String!
  insights: [HealthInsight!]!
  recommendations: [Recommendation!]!
  evidence: JSON!
  confidence: String!
  processingTime: Float!
  dataSources: [String!]!
  timestamp: DateTime!
}
```

#### **DailyInsight**
```graphql
type DailyInsight {
  id: ID!
  date: DateTime!
  summary: String!
  keyInsights: [HealthInsight!]!
  recommendations: [Recommendation!]!
  healthScore: Float!
  dataQualityScore: Float!
  trends: [JSON!]!
  anomalies: [JSON!]!
}
```

#### **DoctorReport**
```graphql
type DoctorReport {
  id: ID!
  patientId: String!
  reportDate: DateTime!
  timePeriod: String!
  summary: String!
  keyInsights: [HealthInsight!]!
  recommendations: [Recommendation!]!
  trends: [JSON!]!
  anomalies: [JSON!]!
  dataQuality: JSON!
  confidenceScore: Float!
  nextSteps: [String!]!
}
```

#### **RealTimeInsight**
```graphql
type RealTimeInsight {
  id: ID!
  type: String!
  message: String!
  priority: String!
  timestamp: DateTime!
  actionable: Boolean!
  dataSource: String!
}
```

### **Queries**

#### **Health Reasoning**
```graphql
query ReasonHealth($query: String!, $reasoningType: String, $timeWindow: String) {
  reason(query: $query, reasoningType: $reasoningType, timeWindow: $timeWindow) {
    query
    reasoning
    insights {
      id
      type
      title
      description
      confidence
      actionable
      evidence {
        source
        description
        confidence
      }
    }
    recommendations {
      id
      title
      description
      category
      priority
      actionable
    }
    confidence
    processingTime
    dataSources
  }
}
```

#### **Daily Summary**
```graphql
query GetDailySummary {
  dailySummary {
    id
    date
    summary
    healthScore
    dataQualityScore
    keyInsights {
      id
      title
      description
      confidence
      actionable
    }
    recommendations {
      id
      title
      description
      priority
      actionable
    }
    trends
    anomalies
  }
}
```

#### **Doctor Report**
```graphql
query GetDoctorReport($timeWindow: String!) {
  doctorReport(timeWindow: $timeWindow) {
    id
    reportDate
    timePeriod
    summary
    keyInsights {
      id
      title
      description
      confidence
    }
    recommendations {
      id
      title
      description
      priority
    }
    confidenceScore
    nextSteps
  }
}
```

#### **Health Data**
```graphql
query GetHealthData($timeWindow: String!, $dataTypes: [String!]) {
  healthData(timeWindow: $timeWindow, dataTypes: $dataTypes) {
    userId
    timeWindow
    vitals
    symptoms {
      id
      name
      severity
      timestamp
    }
    medications {
      id
      name
      dosage
      frequency
    }
    nutrition {
      id
      meal
      calories
      timestamp
    }
    summary {
      totalRecords
      dataQualityScore
      dataTypesAvailable
    }
  }
}
```

### **Mutations**

#### **Provide Feedback**
```graphql
mutation ProvideFeedback($insightId: String!, $helpful: Boolean!, $comment: String) {
  provideFeedback(insightId: $insightId, helpful: $helpful, comment: $comment) {
    success
    message
    insightId
    feedbackId
    timestamp
  }
}
```

#### **Log Symptom**
```graphql
mutation LogSymptom($symptom: String!, $severity: String, $duration: String, $notes: String) {
  logSymptom(symptom: $symptom, severity: $severity, duration: $duration, notes: $notes)
}
```

#### **Log Vital**
```graphql
mutation LogVital($vitalType: String!, $value: Float!, $unit: String!, $timestamp: DateTime) {
  logVital(vitalType: $vitalType, value: $value, unit: $unit, timestamp: $timestamp)
}
```

### **Subscriptions**

#### **Real-time Health Insights**
```graphql
subscription HealthInsights {
  healthInsights {
    id
    type
    message
    priority
    timestamp
    actionable
    dataSource
  }
}
```

## **REST Fallback Endpoints**

### **Health Query Endpoint**
```http
POST /api/v1/health/query
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "Why do I feel tired today?",
  "reasoningType": "symptom_analysis",
  "timeWindow": "24h"
}
```

### **Daily Summary Endpoint**
```http
GET /api/v1/health/daily-summary
Authorization: Bearer <token>
```

### **Doctor Report Endpoint**
```http
POST /api/v1/health/doctor-report
Content-Type: application/json
Authorization: Bearer <token>

{
  "timeWindow": "30d"
}
```

## **Configuration**

### **Environment Variables**
```bash
# Service URLs
AI_REASONING_ORCHESTRATOR_URL=http://ai-reasoning-orchestrator:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8000
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8000
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8000
KNOWLEDGE_GRAPH_SERVICE_URL=http://knowledge-graph-service:8000

# Redis Configuration
REDIS_URL=redis://redis:6379

# Service Configuration
SERVICE_PORT=8400
HOST=0.0.0.0
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# Security
ALLOWED_HOSTS=["localhost", "127.0.0.1", "graphql-bff.localhost"]
```

### **Service Dependencies**
```yaml
# docker-compose.yml
graphql-bff:
  build: ./apps/graphql_bff
  ports:
    - "8400:8000"
  environment:
    - REDIS_URL=redis://redis:6379
    - AI_REASONING_ORCHESTRATOR_URL=http://ai-reasoning-orchestrator:8000
    - HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8000
    - MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8000
    - AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8000
    - KNOWLEDGE_GRAPH_SERVICE_URL=http://knowledge-graph-service:8000
  depends_on:
    - redis
    - ai-reasoning-orchestrator
    - health-tracking-service
    - medical-records-service
    - ai-insights-service
    - knowledge-graph-service
```

## **Deployment & Operations**

### **Docker Deployment**
```bash
# Build the service
docker build -t graphql-bff ./apps/graphql_bff

# Run the service
docker run -d \
  --name graphql-bff \
  -p 8400:8000 \
  -e REDIS_URL=redis://redis:6379 \
  -e AI_REASONING_ORCHESTRATOR_URL=http://ai-reasoning-orchestrator:8000 \
  graphql-bff
```

### **Kubernetes Deployment**
```yaml
# kubernetes/graphql-bff.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphql-bff
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graphql-bff
  template:
    metadata:
      labels:
        app: graphql-bff
    spec:
      containers:
      - name: graphql-bff
        image: graphql-bff:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: AI_REASONING_ORCHESTRATOR_URL
          value: "http://ai-reasoning-orchestrator:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### **Health Checks**
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "graphql-bff",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## **Frontend Integration**

### **React/TypeScript with Apollo Client**
```typescript
// Apollo Client Configuration
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: 'http://graphql-bff.localhost/graphql',
});

const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('authToken');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : "",
    }
  }
});

const client = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache()
});

// React Hook for Health Reasoning
import { useQuery, gql } from '@apollo/client';

const REASON_HEALTH = gql`
  query ReasonHealth($query: String!, $reasoningType: String) {
    reason(query: $query, reasoningType: $reasoningType) {
      query
      reasoning
      insights {
        id
        title
        description
        confidence
        actionable
      }
      recommendations {
        id
        title
        description
        priority
        actionable
      }
      confidence
      processingTime
    }
  }
`;

export const useHealthReasoning = (query: string, reasoningType = "symptom_analysis") => {
  return useQuery(REASON_HEALTH, {
    variables: { query, reasoningType },
    fetchPolicy: 'cache-and-network'
  });
};
```

### **React Native Integration**
```typescript
// React Native with Apollo Client
import { ApolloClient, InMemoryCache, gql, useQuery } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://graphql-bff.localhost/graphql',
  cache: new InMemoryCache(),
});

const GET_DAILY_SUMMARY = gql`
  query GetDailySummary {
    dailySummary {
      id
      date
      summary
      healthScore
      keyInsights {
        id
        title
        description
      }
    }
  }
`;

const DailySummaryScreen: React.FC = () => {
  const { loading, error, data } = useQuery(GET_DAILY_SUMMARY);

  if (loading) return <Text>Loading daily summary...</Text>;
  if (error) return <Text>Error: {error.message}</Text>;

  const summary = data?.dailySummary;

  return (
    <View>
      <Text>Daily Health Summary</Text>
      <Text>Health Score: {Math.round(summary?.healthScore * 100)}%</Text>
      <Text>{summary?.summary}</Text>
    </View>
  );
};
```

### **Vanilla JavaScript Integration**
```javascript
// Vanilla JavaScript with fetch
class GraphQLClient {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async query(query, variables = {}) {
    const response = await fetch(this.baseURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        query,
        variables
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    if (result.errors) {
      throw new Error(result.errors[0].message);
    }

    return result.data;
  }

  async reasonHealth(query, reasoningType = 'symptom_analysis') {
    const graphqlQuery = `
      query ReasonHealth($query: String!, $reasoningType: String) {
        reason(query: $query, reasoningType: $reasoningType) {
          query
          reasoning
          insights {
            id
            title
            description
            confidence
          }
          recommendations {
            id
            title
            description
            priority
          }
          confidence
        }
      }
    `;

    return this.query(graphqlQuery, { query, reasoningType });
  }

  async getDailySummary() {
    const graphqlQuery = `
      query GetDailySummary {
        dailySummary {
          id
          date
          summary
          healthScore
          keyInsights {
            id
            title
            description
          }
        }
      }
    `;

    return this.query(graphqlQuery);
  }
}

// Usage
const client = new GraphQLClient('http://graphql-bff.localhost/graphql', 'your-token');

client.reasonHealth("Why do I feel tired today?")
  .then(data => {
    console.log('Health reasoning:', data.reason);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## **Monitoring & Observability**

### **Metrics**
- **Query Count**: Total GraphQL queries executed
- **Query Duration**: Average query processing time
- **Cache Hit Rate**: Redis cache hit rate
- **Error Rate**: GraphQL error rate
- **Subscription Count**: Active WebSocket subscriptions

### **Logging**
```python
# Structured logging with correlation IDs
logger.info("GraphQL query executed", extra={
    "query": query,
    "variables": variables,
    "user_id": user_id,
    "request_id": request_id,
    "processing_time": processing_time
})
```

### **Tracing**
- **Query Tracing**: Full GraphQL query/response tracing
- **Resolver Performance**: Monitor resolver performance
- **Cache Performance**: Monitor cache hit/miss rates
- **Error Tracking**: Track and alert on GraphQL errors

## **Security Considerations**

### **Authentication & Authorization**
- **JWT Token Validation**: Validate user tokens
- **GraphQL Context**: Pass user context to resolvers
- **Field-Level Security**: Implement field-level access control
- **Query Depth Limiting**: Prevent deeply nested queries

### **Input Validation**
- **GraphQL Schema Validation**: Automatic schema validation
- **Query Complexity Analysis**: Analyze query complexity
- **Rate Limiting**: Implement query rate limiting
- **Query Whitelisting**: Whitelist allowed queries

### **Data Privacy**
- **HIPAA Compliance**: Ensure health data privacy
- **Data Encryption**: Encrypt sensitive health data
- **Audit Logging**: Log all GraphQL queries
- **Data Masking**: Mask sensitive data in logs

## **Performance Optimization**

### **Caching Strategy**
- **Redis Caching**: Cache query results
- **Field-Level Caching**: Cache individual fields
- **Query Result Caching**: Cache similar query results
- **Cache Invalidation**: Smart cache invalidation

### **Query Optimization**
- **Query Batching**: Batch multiple queries
- **Field Selection**: Only request needed fields
- **Query Complexity Analysis**: Monitor query complexity
- **Resolver Optimization**: Optimize resolver performance

### **Resource Management**
- **Connection Pooling**: Pool connections to services
- **Memory Management**: Efficient memory usage
- **CPU Optimization**: Optimize CPU usage for queries

## **Error Handling & Resilience**

### **GraphQL Errors**
```json
{
  "errors": [
    {
      "message": "Unable to fetch health data",
      "locations": [{"line": 2, "column": 3}],
      "path": ["dailySummary"],
      "extensions": {
        "code": "HEALTH_DATA_UNAVAILABLE",
        "service": "health-tracking-service"
      }
    }
  ],
  "data": {
    "dailySummary": null
  }
}
```

### **Circuit Breakers**
- **Service Dependencies**: Circuit breakers for dependent services
- **Fallback Mechanisms**: Graceful degradation when services are unavailable
- **Retry Logic**: Exponential backoff for transient failures

### **Graceful Degradation**
- **Partial Data**: Return partial data when possible
- **Cached Results**: Return cached results when services are unavailable
- **Error Boundaries**: Implement error boundaries in resolvers

## **Testing Strategy**

### **Unit Tests**
```python
# tests/test_graphql_schema.py
def test_health_reasoning_query():
    schema = strawberry.Schema(query=Query)
    query = """
    query ReasonHealth($query: String!) {
        reason(query: $query) {
            query
            reasoning
            insights {
                id
                title
            }
        }
    }
    """
    result = schema.execute_sync(query, variable_values={"query": "Why am I tired?"})
    assert result.errors is None
    assert result.data["reason"]["query"] == "Why am I tired?"
```

### **Integration Tests**
- **Service Integration**: Test integration with dependent services
- **End-to-End Tests**: Test complete GraphQL workflows
- **Performance Tests**: Test GraphQL performance under load

### **Load Testing**
- **Concurrent Queries**: Test handling of multiple concurrent queries
- **Complex Queries**: Test complex GraphQL queries
- **Subscription Testing**: Test WebSocket subscription performance

## **Future Enhancements**

### **Advanced GraphQL Features**
- **GraphQL Federation**: Implement GraphQL federation
- **Real-time Subscriptions**: Enhanced real-time features
- **Query Persistence**: Persist and replay queries
- **GraphQL Analytics**: Advanced query analytics

### **Performance Improvements**
- **Query Optimization**: Advanced query optimization
- **Caching Improvements**: Advanced caching strategies
- **CDN Integration**: CDN integration for static queries
- **Edge Computing**: Edge computing for global performance

### **Developer Experience**
- **GraphQL Playground**: Enhanced GraphQL playground
- **Query Builder**: Visual query builder
- **Schema Documentation**: Enhanced schema documentation
- **Code Generation**: Generate TypeScript types from schema

## **API Documentation**

### **GraphQL Playground**
- **Interactive Documentation**: Available at `/graphql`
- **Query Builder**: Visual query builder
- **Schema Explorer**: Interactive schema explorer
- **Query History**: Query execution history

### **OpenAPI/Swagger**
- **REST Endpoints**: Documentation for REST fallback endpoints
- **Interactive Documentation**: Available at `/docs`
- **Request/Response Examples**: Detailed examples for all endpoints

### **Postman Collection**
- **Complete Collection**: Postman collection for all endpoints
- **Environment Variables**: Pre-configured environment variables
- **Test Scripts**: Automated test scripts for API validation

## **Support & Maintenance**

### **Troubleshooting**
- **Common Issues**: Documentation of common issues and solutions
- **Debug Mode**: Enable debug mode for detailed logging
- **Health Checks**: Regular health check monitoring

### **Updates & Maintenance**
- **Schema Evolution**: GraphQL schema evolution strategies
- **Breaking Changes**: Handle breaking changes gracefully
- **Performance Monitoring**: Continuous performance monitoring

---

**The GraphQL BFF Service provides a powerful, type-safe interface that makes it easy for frontend applications to access and manipulate health data efficiently, while maintaining excellent performance and developer experience.**
