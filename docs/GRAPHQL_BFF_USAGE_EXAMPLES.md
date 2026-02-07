# 🎯 GraphQL BFF Usage Examples

## **Overview**

The GraphQL BFF (Backend-for-Frontend) provides a unified, type-safe interface for frontend applications to interact with the Personal Physician Assistant (PPA) backend. This document shows practical examples of how to use the GraphQL BFF from different frontend technologies.

## **🎯 GraphQL Endpoint**

```
GraphQL Playground: http://graphql-bff.localhost/graphql
GraphQL Endpoint: http://graphql-bff.localhost/graphql
```

## **🔧 Frontend Integration Examples**

### **1. React/TypeScript with Apollo Client**

```typescript
// hooks/useHealthReasoning.ts
import { useQuery, useMutation, gql } from '@apollo/client';

const REASON_HEALTH = gql`
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
`;

export const useHealthReasoning = (query: string, reasoningType = "symptom_analysis") => {
  return useQuery(REASON_HEALTH, {
    variables: { query, reasoningType, timeWindow: "24h" },
    fetchPolicy: 'cache-and-network'
  });
};

// hooks/useDailySummary.ts
const GET_DAILY_SUMMARY = gql`
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
`;

export const useDailySummary = () => {
  return useQuery(GET_DAILY_SUMMARY, {
    fetchPolicy: 'cache-and-network'
  });
};

// hooks/useDoctorReport.ts
const GET_DOCTOR_REPORT = gql`
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
`;

export const useDoctorReport = (timeWindow = "30d") => {
  return useQuery(GET_DOCTOR_REPORT, {
    variables: { timeWindow },
    fetchPolicy: 'cache-and-network'
  });
};

// hooks/useHealthData.ts
const GET_HEALTH_DATA = gql`
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
`;

export const useHealthData = (timeWindow = "24h", dataTypes?: string[]) => {
  return useQuery(GET_HEALTH_DATA, {
    variables: { timeWindow, dataTypes },
    fetchPolicy: 'cache-and-network'
  });
};

// hooks/useFeedback.ts
const PROVIDE_FEEDBACK = gql`
  mutation ProvideFeedback($insightId: String!, $helpful: Boolean!, $comment: String) {
    provideFeedback(insightId: $insightId, helpful: $helpful, comment: $comment) {
      success
      message
      insightId
      feedbackId
      timestamp
    }
  }
`;

export const useFeedback = () => {
  return useMutation(PROVIDE_FEEDBACK);
};

// hooks/useLogSymptom.ts
const LOG_SYMPTOM = gql`
  mutation LogSymptom($symptom: String!, $severity: String, $duration: String, $notes: String) {
    logSymptom(symptom: $symptom, severity: $severity, duration: $duration, notes: $notes)
  }
`;

export const useLogSymptom = () => {
  return useMutation(LOG_SYMPTOM);
};
```

### **2. React Components Using the Hooks**

```typescript
// components/HealthInsightCard.tsx
import React from 'react';
import { useHealthReasoning } from '../hooks/useHealthReasoning';

interface HealthInsightCardProps {
  query: string;
  reasoningType?: string;
}

export const HealthInsightCard: React.FC<HealthInsightCardProps> = ({ 
  query, 
  reasoningType = "symptom_analysis" 
}) => {
  const { loading, error, data } = useHealthReasoning(query, reasoningType);

  if (loading) return <div>Analyzing your health data...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const result = data?.reason;

  return (
    <div className="health-insight-card">
      <h3>Health Analysis</h3>
      <p className="query">"{result?.query}"</p>
      
      <div className="reasoning">
        <h4>Analysis</h4>
        <p>{result?.reasoning}</p>
      </div>

      <div className="insights">
        <h4>Key Insights</h4>
        {result?.insights.map((insight: any) => (
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
        {result?.recommendations.map((rec: any) => (
          <div key={rec.id} className="recommendation">
            <h5>{rec.title}</h5>
            <p>{rec.description}</p>
            <span className={`priority priority-${rec.priority}`}>
              {rec.priority} priority
            </span>
          </div>
        ))}
      </div>

      <div className="metadata">
        <p>Processing time: {result?.processingTime}s</p>
        <p>Data sources: {result?.dataSources.join(', ')}</p>
        <p>Overall confidence: {result?.confidence}</p>
      </div>
    </div>
  );
};

// components/DailySummary.tsx
import React from 'react';
import { useDailySummary } from '../hooks/useDailySummary';

export const DailySummary: React.FC = () => {
  const { loading, error, data } = useDailySummary();

  if (loading) return <div>Loading daily summary...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const summary = data?.dailySummary;

  return (
    <div className="daily-summary">
      <h2>Daily Health Summary</h2>
      <p className="date">{new Date(summary?.date).toLocaleDateString()}</p>
      
      <div className="summary-text">
        <p>{summary?.summary}</p>
      </div>

      <div className="health-score">
        <h3>Health Score</h3>
        <div className="score-circle">
          <span>{Math.round(summary?.healthScore * 100)}%</span>
        </div>
      </div>

      <div className="key-insights">
        <h3>Key Insights</h3>
        {summary?.keyInsights.map((insight: any) => (
          <div key={insight.id} className="insight">
            <h4>{insight.title}</h4>
            <p>{insight.description}</p>
          </div>
        ))}
      </div>

      <div className="recommendations">
        <h3>Today's Recommendations</h3>
        {summary?.recommendations.map((rec: any) => (
          <div key={rec.id} className="recommendation">
            <h4>{rec.title}</h4>
            <p>{rec.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// components/DoctorReport.tsx
import React from 'react';
import { useDoctorReport } from '../hooks/useDoctorReport';

export const DoctorReport: React.FC = () => {
  const { loading, error, data } = useDoctorReport("30d");

  if (loading) return <div>Generating doctor report...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const report = data?.doctorReport;

  return (
    <div className="doctor-report">
      <h2>Doctor Mode Report</h2>
      <p className="period">Period: {report?.timePeriod}</p>
      
      <div className="summary">
        <h3>Executive Summary</h3>
        <p>{report?.summary}</p>
      </div>

      <div className="insights">
        <h3>Key Clinical Insights</h3>
        {report?.keyInsights.map((insight: any) => (
          <div key={insight.id} className="clinical-insight">
            <h4>{insight.title}</h4>
            <p>{insight.description}</p>
            <span className="confidence">{insight.confidence} confidence</span>
          </div>
        ))}
      </div>

      <div className="recommendations">
        <h3>Treatment Recommendations</h3>
        {report?.recommendations.map((rec: any) => (
          <div key={rec.id} className="treatment-rec">
            <h4>{rec.title}</h4>
            <p>{rec.description}</p>
            <span className="priority">{rec.priority} priority</span>
          </div>
        ))}
      </div>

      <div className="next-steps">
        <h3>Next Steps</h3>
        <ul>
          {report?.nextSteps.map((step: string, index: number) => (
            <li key={index}>{step}</li>
          ))}
        </ul>
      </div>

      <button className="download-pdf">Download PDF Report</button>
    </div>
  );
};
```

### **3. React Native Example**

```typescript
// React Native with Apollo Client
import { ApolloClient, InMemoryCache, ApolloProvider, gql, useQuery } from '@apollo/client';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';

const client = new ApolloClient({
  uri: 'http://graphql-bff.localhost/graphql',
  cache: new InMemoryCache(),
});

const GET_HEALTH_DATA = gql`
  query GetHealthData($timeWindow: String!) {
    healthData(timeWindow: $timeWindow) {
      userId
      timeWindow
      vitals
      symptoms {
        id
        name
        severity
        timestamp
      }
      summary {
        totalRecords
        dataQualityScore
      }
    }
  }
`;

const HealthDataScreen: React.FC = () => {
  const { loading, error, data } = useQuery(GET_HEALTH_DATA, {
    variables: { timeWindow: "24h" }
  });

  if (loading) return <Text>Loading health data...</Text>;
  if (error) return <Text>Error: {error.message}</Text>;

  const healthData = data?.healthData;

  return (
    <ScrollView>
      <View style={{ padding: 16 }}>
        <Text style={{ fontSize: 24, fontWeight: 'bold' }}>Health Data</Text>
        
        <View style={{ marginTop: 16 }}>
          <Text style={{ fontSize: 18 }}>Data Quality: {Math.round(healthData?.summary?.dataQualityScore * 100)}%</Text>
          <Text>Total Records: {healthData?.summary?.totalRecords}</Text>
        </View>

        <View style={{ marginTop: 16 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold' }}>Recent Symptoms</Text>
          {healthData?.symptoms.map((symptom: any) => (
            <View key={symptom.id} style={{ marginTop: 8, padding: 12, backgroundColor: '#f5f5f5' }}>
              <Text style={{ fontWeight: 'bold' }}>{symptom.name}</Text>
              <Text>Severity: {symptom.severity}</Text>
              <Text>Time: {new Date(symptom.timestamp).toLocaleString()}</Text>
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );
};

export default HealthDataScreen;
```

### **4. Vanilla JavaScript Example**

```javascript
// Vanilla JavaScript with fetch
class HealthAPI {
  constructor(baseURL = 'http://graphql-bff.localhost/graphql') {
    this.baseURL = baseURL;
  }

  async query(query, variables = {}) {
    const response = await fetch(this.baseURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
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

  getAuthToken() {
    // Get auth token from localStorage or other storage
    return localStorage.getItem('authToken');
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

  async logSymptom(symptom, severity, notes) {
    const graphqlQuery = `
      mutation LogSymptom($symptom: String!, $severity: String, $notes: String) {
        logSymptom(symptom: $symptom, severity: $severity, notes: $notes)
      }
    `;

    return this.query(graphqlQuery, { symptom, severity, notes });
  }
}

// Usage example
const healthAPI = new HealthAPI();

// Reason about health
healthAPI.reasonHealth("Why do I feel tired today?")
  .then(data => {
    console.log('Health reasoning:', data.reason);
    
    // Display insights
    data.reason.insights.forEach(insight => {
      console.log(`Insight: ${insight.title} - ${insight.description}`);
    });
    
    // Display recommendations
    data.reason.recommendations.forEach(rec => {
      console.log(`Recommendation: ${rec.title} - ${rec.description}`);
    });
  })
  .catch(error => {
    console.error('Error reasoning about health:', error);
  });

// Get daily summary
healthAPI.getDailySummary()
  .then(data => {
    console.log('Daily summary:', data.dailySummary);
  })
  .catch(error => {
    console.error('Error getting daily summary:', error);
  });

// Log a symptom
healthAPI.logSymptom("headache", "moderate", "Started after lunch")
  .then(result => {
    console.log('Symptom logged:', result.logSymptom);
  })
  .catch(error => {
    console.error('Error logging symptom:', error);
  });
```

### **5. Python Client Example**

```python
# Python client using requests
import requests
import json
from typing import Dict, Any, Optional

class HealthGraphQLClient:
    def __init__(self, base_url: str = "http://graphql-bff.localhost/graphql", auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    def query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result["data"]
    
    def reason_health(self, query: str, reasoning_type: str = "symptom_analysis") -> Dict[str, Any]:
        """Reason about health using natural language query"""
        graphql_query = """
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
                    category
                    priority
                    actionable
                }
                confidence
                processingTime
                dataSources
            }
        }
        """
        
        return self.query(graphql_query, {
            "query": query,
            "reasoningType": reasoning_type
        })
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily health summary"""
        graphql_query = """
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
                }
                recommendations {
                    id
                    title
                    description
                    priority
                }
            }
        }
        """
        
        return self.query(graphql_query)
    
    def get_health_data(self, time_window: str = "24h", data_types: Optional[list] = None) -> Dict[str, Any]:
        """Get aggregated health data"""
        graphql_query = """
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
                }
                summary {
                    totalRecords
                    dataQualityScore
                    dataTypesAvailable
                }
            }
        }
        """
        
        return self.query(graphql_query, {
            "timeWindow": time_window,
            "dataTypes": data_types
        })
    
    def log_symptom(self, symptom: str, severity: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Log a new symptom"""
        graphql_query = """
        mutation LogSymptom($symptom: String!, $severity: String, $notes: String) {
            logSymptom(symptom: $symptom, severity: $severity, notes: $notes)
        }
        """
        
        result = self.query(graphql_query, {
            "symptom": symptom,
            "severity": severity,
            "notes": notes
        })
        
        return result["logSymptom"]

# Usage example
if __name__ == "__main__":
    client = HealthGraphQLClient(auth_token="your-auth-token")
    
    try:
        # Reason about health
        result = client.reason_health("Why do I feel fatigued today?")
        print("Health reasoning result:")
        print(f"Query: {result['reason']['query']}")
        print(f"Reasoning: {result['reason']['reasoning']}")
        print(f"Confidence: {result['reason']['confidence']}")
        
        # Get daily summary
        summary = client.get_daily_summary()
        print(f"\nDaily summary: {summary['dailySummary']['summary']}")
        print(f"Health score: {summary['dailySummary']['healthScore']}")
        
        # Log a symptom
        success = client.log_symptom("headache", "moderate", "Started after lunch")
        print(f"\nSymptom logged: {success}")
        
    except Exception as e:
        print(f"Error: {e}")
```

## **🎯 Benefits of Using GraphQL BFF**

### **1. Type Safety**
- **Strong Typing**: GraphQL provides compile-time type checking
- **IntelliSense**: Better IDE support with autocomplete
- **Runtime Validation**: Automatic validation of queries and responses

### **2. Efficient Data Fetching**
- **Single Request**: Get all needed data in one request
- **No Over-fetching**: Request only the fields you need
- **No Under-fetching**: Get all related data in one go

### **3. Unified Interface**
- **Single Endpoint**: All health data through one GraphQL endpoint
- **Consistent Schema**: Unified data model across all health features
- **Versioning**: GraphQL schema evolution without breaking changes

### **4. Performance**
- **Caching**: Built-in caching with Redis
- **Batching**: Multiple queries can be batched
- **Optimization**: Query optimization and field-level caching

### **5. Developer Experience**
- **GraphQL Playground**: Interactive API explorer
- **Documentation**: Self-documenting schema
- **Real-time**: Subscriptions for live updates

## **🎯 Next Steps**

1. **Set up Apollo Client** in your frontend application
2. **Configure authentication** headers for GraphQL requests
3. **Implement error handling** for GraphQL errors
4. **Add caching strategies** for optimal performance
5. **Create reusable hooks** for common health queries

The GraphQL BFF provides a powerful, type-safe interface that makes it easy to build rich health applications while maintaining excellent performance and developer experience! 🚀
