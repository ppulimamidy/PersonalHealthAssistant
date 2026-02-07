# Frontend Integration Guide - Personal Physician Assistant

## **Project Overview**

This guide provides everything needed to build a React-based frontend for the Personal Physician Assistant (PPA) backend. The backend provides unified APIs through an Enhanced API Gateway, GraphQL BFF, and AI Reasoning Orchestrator.

## **Backend Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Microservices │
│   (React App)   │◄──►│   (Enhanced)    │◄──►│   (Backend)     │
│                 │    │                 │    │                 │
│ - Single API    │    │ - Composite     │    │ - AI Reasoning  │
│ - Unified Data  │    │ - Routing       │    │ - Health Data   │
│ - Type Safety   │    │ - Resilience    │    │ - Medical Rec   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## **API Endpoints**

### **Primary API Gateway (Recommended)**
- **Base URL**: `http://api-gateway.localhost`
- **Authentication**: Bearer token in Authorization header
- **Content-Type**: `application/json`

### **Alternative GraphQL BFF**
- **Base URL**: `http://graphql-bff.localhost`
- **GraphQL Endpoint**: `/graphql`
- **Authentication**: Bearer token in Authorization header

## **Core API Endpoints**

### **1. Symptom Analysis**
```http
POST /health/analyze-symptoms
```

**Request:**
```json
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
    "reasoning": "Based on your recent data...",
    "insights": [
      {
        "id": "insight-001",
        "type": "symptom_analysis",
        "title": "Sleep Quality Impact",
        "description": "Your sleep efficiency was 75%...",
        "confidence": "high",
        "actionable": true,
        "evidence": [...]
      }
    ],
    "recommendations": [
      {
        "id": "rec-001",
        "title": "Improve Sleep Hygiene",
        "description": "Consider going to bed 30 minutes earlier...",
        "category": "lifestyle",
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
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "daily-user123-2024-01-15",
    "date": "2024-01-15T00:00:00Z",
    "summary": "Your health is generally good today...",
    "health_score": 0.85,
    "data_quality_score": 0.92,
    "key_insights": [...],
    "recommendations": [...],
    "trends": [...],
    "anomalies": []
  }
}
```

### **3. Natural Language Health Queries**
```http
POST /health/query
```

**Request:**
```json
{
  "question": "Why do I feel tired today?",
  "time_window": "24h"
}
```

### **4. Doctor Mode Report**
```http
POST /health/doctor-report
```

**Request:**
```json
{
  "time_window": "30d"
}
```

### **5. Unified Dashboard**
```http
GET /health/unified-dashboard
```

## **Project Setup**

### **1. Create React Project**
```bash
# Using Create React App with TypeScript
npx create-react-app ppa-frontend --template typescript

# Or using Vite (recommended)
npm create vite@latest ppa-frontend -- --template react-ts

cd ppa-frontend
```

### **2. Install Dependencies**
```bash
# Core dependencies
npm install @apollo/client graphql
npm install react-router-dom
npm install @tanstack/react-query
npm install axios
npm install date-fns
npm install react-hook-form
npm install zod @hookform/resolvers

# UI libraries (choose one)
npm install @mui/material @emotion/react @emotion/styled
# OR
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
# OR
npm install tailwindcss @headlessui/react @heroicons/react

# Development dependencies
npm install -D @types/node
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

### **3. Environment Configuration**
Create `.env` files:

```bash
# .env.development
REACT_APP_API_BASE_URL=http://api-gateway.localhost
REACT_APP_GRAPHQL_URL=http://graphql-bff.localhost/graphql
REACT_APP_ENVIRONMENT=development

# .env.production
REACT_APP_API_BASE_URL=https://api.ppa.yourdomain.com
REACT_APP_GRAPHQL_URL=https://graphql.ppa.yourdomain.com/graphql
REACT_APP_ENVIRONMENT=production
```

## **Core API Client**

### **1. API Client Setup**
```typescript
// src/lib/api-client.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('authToken', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('authToken');
  }

  private async request<T>(config: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client(config);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || error.message);
    }
  }

  // Health API methods
  async analyzeSymptoms(symptoms: string[], options: any = {}) {
    return this.request({
      method: 'POST',
      url: '/health/analyze-symptoms',
      data: {
        symptoms,
        include_vitals: options.includeVitals ?? true,
        include_medications: options.includeMedications ?? true,
        generate_insights: options.generateInsights ?? true,
      },
    });
  }

  async getDailySummary() {
    return this.request({
      method: 'GET',
      url: '/health/daily-summary',
    });
  }

  async queryHealth(question: string, timeWindow: string = '24h') {
    return this.request({
      method: 'POST',
      url: '/health/query',
      data: { question, time_window: timeWindow },
    });
  }

  async generateDoctorReport(timeWindow: string = '30d') {
    return this.request({
      method: 'POST',
      url: '/health/doctor-report',
      data: { time_window: timeWindow },
    });
  }

  async getUnifiedDashboard() {
    return this.request({
      method: 'GET',
      url: '/health/unified-dashboard',
    });
  }
}

// Create singleton instance
export const apiClient = new ApiClient(process.env.REACT_APP_API_BASE_URL!);
```

### **2. React Query Setup**
```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});
```

### **3. Custom Hooks**
```typescript
// src/hooks/useHealthAPI.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';

// Query keys
export const healthKeys = {
  all: ['health'] as const,
  dailySummary: () => [...healthKeys.all, 'daily-summary'] as const,
  symptoms: () => [...healthKeys.all, 'symptoms'] as const,
  dashboard: () => [...healthKeys.all, 'dashboard'] as const,
};

// Daily Summary Hook
export const useDailySummary = () => {
  return useQuery({
    queryKey: healthKeys.dailySummary(),
    queryFn: () => apiClient.getDailySummary(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Symptom Analysis Hook
export const useSymptomAnalysis = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ symptoms, options }: { symptoms: string[]; options?: any }) =>
      apiClient.analyzeSymptoms(symptoms, options),
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: healthKeys.symptoms() });
    },
  });
};

// Health Query Hook
export const useHealthQuery = () => {
  return useMutation({
    mutationFn: ({ question, timeWindow }: { question: string; timeWindow?: string }) =>
      apiClient.queryHealth(question, timeWindow),
  });
};

// Doctor Report Hook
export const useDoctorReport = () => {
  return useMutation({
    mutationFn: ({ timeWindow }: { timeWindow?: string }) =>
      apiClient.generateDoctorReport(timeWindow),
  });
};

// Unified Dashboard Hook
export const useUnifiedDashboard = () => {
  return useQuery({
    queryKey: healthKeys.dashboard(),
    queryFn: () => apiClient.getUnifiedDashboard(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};
```

## **Core Components**

### **1. Symptom Analyzer Component**
```typescript
// src/components/SymptomAnalyzer.tsx
import React, { useState } from 'react';
import { useSymptomAnalysis } from '../hooks/useHealthAPI';

interface SymptomAnalyzerProps {
  onAnalysisComplete?: (data: any) => void;
}

export const SymptomAnalyzer: React.FC<SymptomAnalyzerProps> = ({ 
  onAnalysisComplete 
}) => {
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const symptomAnalysis = useSymptomAnalysis();

  const addSymptom = (symptom: string) => {
    if (symptom.trim() && !symptoms.includes(symptom.trim())) {
      setSymptoms([...symptoms, symptom.trim()]);
      setInputValue('');
    }
  };

  const removeSymptom = (index: number) => {
    setSymptoms(symptoms.filter((_, i) => i !== index));
  };

  const handleAnalyze = async () => {
    if (symptoms.length === 0) return;

    try {
      const result = await symptomAnalysis.mutateAsync({ 
        symptoms,
        options: {
          includeVitals: true,
          includeMedications: true,
          generateInsights: true,
        }
      });
      
      onAnalysisComplete?.(result.data);
    } catch (error) {
      console.error('Error analyzing symptoms:', error);
    }
  };

  return (
    <div className="symptom-analyzer">
      <h2 className="text-2xl font-bold mb-4">Analyze Your Symptoms</h2>
      
      <div className="mb-4">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              addSymptom(inputValue);
            }
          }}
          placeholder="Enter a symptom and press Enter..."
          className="w-full p-3 border border-gray-300 rounded-lg"
        />
      </div>

      {symptoms.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">Symptoms to Analyze:</h3>
          <div className="flex flex-wrap gap-2">
            {symptoms.map((symptom, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
              >
                {symptom}
                <button
                  onClick={() => removeSymptom(index)}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={symptoms.length === 0 || symptomAnalysis.isPending}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
      >
        {symptomAnalysis.isPending ? 'Analyzing...' : 'Analyze Symptoms'}
      </button>

      {symptomAnalysis.isError && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg">
          Error: {symptomAnalysis.error?.message}
        </div>
      )}
    </div>
  );
};
```

### **2. Analysis Results Component**
```typescript
// src/components/AnalysisResults.tsx
import React from 'react';

interface AnalysisData {
  query: string;
  reasoning: string;
  insights: Array<{
    id: string;
    title: string;
    description: string;
    confidence: string;
    actionable: boolean;
  }>;
  recommendations: Array<{
    id: string;
    title: string;
    description: string;
    priority: string;
    actionable: boolean;
  }>;
  confidence: string;
}

interface AnalysisResultsProps {
  data: AnalysisData;
}

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({ data }) => {
  return (
    <div className="analysis-results">
      <h3 className="text-xl font-bold mb-4">Analysis Results</h3>
      
      <div className="mb-6">
        <h4 className="text-lg font-semibold mb-2">Analysis</h4>
        <p className="text-gray-700 leading-relaxed">{data.reasoning}</p>
      </div>

      <div className="mb-6">
        <h4 className="text-lg font-semibold mb-3">Key Insights</h4>
        <div className="space-y-3">
          {data.insights.map((insight) => (
            <div key={insight.id} className="p-4 bg-blue-50 rounded-lg">
              <h5 className="font-semibold text-blue-900">{insight.title}</h5>
              <p className="text-blue-800 mt-1">{insight.description}</p>
              <div className="flex items-center mt-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  insight.confidence === 'high' ? 'bg-green-100 text-green-800' :
                  insight.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {insight.confidence} confidence
                </span>
                {insight.actionable && (
                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                    Actionable
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h4 className="text-lg font-semibold mb-3">Recommendations</h4>
        <div className="space-y-3">
          {data.recommendations.map((rec) => (
            <div key={rec.id} className="p-4 bg-green-50 rounded-lg">
              <h5 className="font-semibold text-green-900">{rec.title}</h5>
              <p className="text-green-800 mt-1">{rec.description}</p>
              <div className="flex items-center mt-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                  rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {rec.priority} priority
                </span>
                {rec.actionable && (
                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                    Actionable
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="text-sm text-gray-600">
        Overall confidence: <span className="font-medium">{data.confidence}</span>
      </div>
    </div>
  );
};
```

### **3. Daily Summary Component**
```typescript
// src/components/DailySummary.tsx
import React from 'react';
import { useDailySummary } from '../hooks/useHealthAPI';

export const DailySummary: React.FC = () => {
  const { data, isLoading, error } = useDailySummary();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading daily summary...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded-lg">
        Error loading daily summary: {error.message}
      </div>
    );
  }

  if (!data?.data) {
    return <div>No data available</div>;
  }

  const summary = data.data;

  return (
    <div className="daily-summary">
      <h2 className="text-2xl font-bold mb-4">Daily Health Summary</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900">Health Score</h3>
          <p className="text-2xl font-bold text-blue-600">
            {Math.round(summary.health_score * 100)}%
          </p>
        </div>
        
        <div className="p-4 bg-green-50 rounded-lg">
          <h3 className="font-semibold text-green-900">Data Quality</h3>
          <p className="text-2xl font-bold text-green-600">
            {Math.round(summary.data_quality_score * 100)}%
          </p>
        </div>
        
        <div className="p-4 bg-purple-50 rounded-lg">
          <h3 className="font-semibold text-purple-900">Date</h3>
          <p className="text-lg font-medium text-purple-600">
            {new Date(summary.date).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Summary</h3>
        <p className="text-gray-700 leading-relaxed">{summary.summary}</p>
      </div>

      {summary.key_insights && summary.key_insights.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Key Insights</h3>
          <div className="space-y-2">
            {summary.key_insights.map((insight: any) => (
              <div key={insight.id} className="p-3 bg-yellow-50 rounded-lg">
                <h4 className="font-medium text-yellow-900">{insight.title}</h4>
                <p className="text-yellow-800 text-sm">{insight.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary.recommendations && summary.recommendations.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Recommendations</h3>
          <div className="space-y-2">
            {summary.recommendations.map((rec: any) => (
              <div key={rec.id} className="p-3 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900">{rec.title}</h4>
                <p className="text-green-800 text-sm">{rec.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

### **4. Health Query Component**
```typescript
// src/components/HealthQuery.tsx
import React, { useState } from 'react';
import { useHealthQuery } from '../hooks/useHealthAPI';

export const HealthQuery: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [timeWindow, setTimeWindow] = useState('24h');
  const [result, setResult] = useState<any>(null);
  
  const healthQuery = useHealthQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    try {
      const response = await healthQuery.mutateAsync({ 
        question: question.trim(), 
        timeWindow 
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error querying health:', error);
    }
  };

  return (
    <div className="health-query">
      <h2 className="text-2xl font-bold mb-4">Ask About Your Health</h2>
      
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Question
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g., Why do I feel tired today? What's causing my headache?"
            className="w-full p-3 border border-gray-300 rounded-lg resize-none"
            rows={3}
            required
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Time Window
          </label>
          <select
            value={timeWindow}
            onChange={(e) => setTimeWindow(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg"
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
        
        <button
          type="submit"
          disabled={!question.trim() || healthQuery.isPending}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          {healthQuery.isPending ? 'Analyzing...' : 'Ask Question'}
        </button>
      </form>

      {healthQuery.isError && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
          Error: {healthQuery.error?.message}
        </div>
      )}

      {result && (
        <div className="result-section">
          <h3 className="text-lg font-semibold mb-3">Analysis Result</h3>
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Question: {result.query}</h4>
            <p className="text-gray-700 mb-4">{result.reasoning}</p>
            
            {result.insights && result.insights.length > 0 && (
              <div className="mb-4">
                <h5 className="font-medium mb-2">Insights:</h5>
                <ul className="list-disc list-inside space-y-1">
                  {result.insights.map((insight: any) => (
                    <li key={insight.id} className="text-sm text-gray-600">
                      {insight.title}: {insight.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {result.recommendations && result.recommendations.length > 0 && (
              <div>
                <h5 className="font-medium mb-2">Recommendations:</h5>
                <ul className="list-disc list-inside space-y-1">
                  {result.recommendations.map((rec: any) => (
                    <li key={rec.id} className="text-sm text-gray-600">
                      {rec.title}: {rec.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
```

## **App Structure**

### **1. Main App Component**
```typescript
// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/query-client';
import { Navigation } from './components/Navigation';
import { Dashboard } from './pages/Dashboard';
import { SymptomAnalysis } from './pages/SymptomAnalysis';
import { HealthQuery } from './pages/HealthQuery';
import { DoctorMode } from './pages/DoctorMode';
import { Login } from './pages/Login';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Navigation />
            <main className="container mx-auto px-4 py-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/symptoms" element={<SymptomAnalysis />} />
                <Route path="/query" element={<HealthQuery />} />
                <Route path="/doctor-mode" element={<DoctorMode />} />
                <Route path="/login" element={<Login />} />
              </Routes>
            </main>
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
```

### **2. Authentication Context**
```typescript
// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../lib/api-client';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('authToken');
    if (token) {
      apiClient.setToken(token);
      setIsAuthenticated(true);
      // You might want to validate the token here
    }
  }, []);

  const login = (token: string) => {
    apiClient.setToken(token);
    setIsAuthenticated(true);
    // You might want to fetch user data here
  };

  const logout = () => {
    apiClient.clearToken();
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

## **Page Components**

### **1. Dashboard Page**
```typescript
// src/pages/Dashboard.tsx
import React from 'react';
import { DailySummary } from '../components/DailySummary';
import { useUnifiedDashboard } from '../hooks/useHealthAPI';

export const Dashboard: React.FC = () => {
  const { data: dashboardData, isLoading, error } = useUnifiedDashboard();

  return (
    <div className="dashboard">
      <h1 className="text-3xl font-bold mb-6">Health Dashboard</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <DailySummary />
        </div>
        
        <div>
          <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
          {isLoading && <div>Loading dashboard data...</div>}
          {error && <div>Error loading dashboard data</div>}
          {dashboardData?.data && (
            <div className="space-y-4">
              {/* Render dashboard data */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
```

### **2. Symptom Analysis Page**
```typescript
// src/pages/SymptomAnalysis.tsx
import React, { useState } from 'react';
import { SymptomAnalyzer } from '../components/SymptomAnalyzer';
import { AnalysisResults } from '../components/AnalysisResults';

export const SymptomAnalysis: React.FC = () => {
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  return (
    <div className="symptom-analysis">
      <h1 className="text-3xl font-bold mb-6">Symptom Analysis</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <SymptomAnalyzer onAnalysisComplete={setAnalysisResult} />
        </div>
        
        <div>
          {analysisResult && (
            <AnalysisResults data={analysisResult} />
          )}
        </div>
      </div>
    </div>
  );
};
```

## **Styling and UI**

### **1. Tailwind CSS Setup**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
```

### **2. Global Styles**
```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
  
  .input-field {
    @apply w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent;
  }
}
```

## **Testing Setup**

### **1. Testing Dependencies**
```bash
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

### **2. Test Example**
```typescript
// src/components/__tests__/SymptomAnalyzer.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SymptomAnalyzer } from '../SymptomAnalyzer';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

test('renders symptom analyzer', () => {
  render(<SymptomAnalyzer />, { wrapper });
  
  expect(screen.getByText('Analyze Your Symptoms')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('Enter a symptom and press Enter...')).toBeInTheDocument();
});

test('can add and remove symptoms', () => {
  render(<SymptomAnalyzer />, { wrapper });
  
  const input = screen.getByPlaceholderText('Enter a symptom and press Enter...');
  
  fireEvent.change(input, { target: { value: 'fatigue' } });
  fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });
  
  expect(screen.getByText('fatigue')).toBeInTheDocument();
  
  const removeButton = screen.getByText('×');
  fireEvent.click(removeButton);
  
  expect(screen.queryByText('fatigue')).not.toBeInTheDocument();
});
```

## **Deployment**

### **1. Build Configuration**
```json
// package.json scripts
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
```

### **2. Docker Configuration**
```dockerfile
# Dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## **Troubleshooting & Backend Setup**

### **CORS Issues and Backend Setup**

If you're getting CORS errors when calling `http://api-gateway.localhost`, follow these steps:

#### **1. Backend Services Setup**

First, ensure all backend services are running. The frontend depends on these services:

```bash
# Navigate to your backend project root
cd /path/to/PersonalHealthAssistant

# Start the core services using Docker Compose
docker-compose up -d redis postgres

# Start the API Gateway (Enhanced)
cd apps/api_gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start the AI Reasoning Orchestrator
cd ../ai_reasoning_orchestrator
python -m uvicorn main:app --host 0.0.0.0 --port 8300 --reload

# Start the GraphQL BFF
cd ../graphql_bff
python -m uvicorn main:app --host 0.0.0.0 --port 8400 --reload

# Start other required services
cd ../health_tracking
python -m uvicorn main:app --host 0.0.0.0 --port 8100 --reload

cd ../medical_records
python -m uvicorn main:app --host 0.0.0.0 --port 8200 --reload
```

#### **2. Environment Configuration**

Update your frontend environment variables to use the correct backend URLs:

```bash
# .env.development
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_GRAPHQL_URL=http://localhost:8400/graphql
REACT_APP_ENVIRONMENT=development
```

#### **3. CORS Configuration**

The backend services are already configured with CORS, but if you're still having issues, check:

**API Gateway CORS Settings** (already configured):
```python
# apps/api_gateway/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
```

#### **4. Alternative: Use Localhost Instead of api-gateway.localhost**

If you're having DNS resolution issues, update your frontend configuration:

```typescript
// src/lib/api-client.ts
// Change from:
export const apiClient = new ApiClient('http://api-gateway.localhost');

// To:
export const apiClient = new ApiClient('http://localhost:8000');
```

#### **5. Quick Backend Test**

Test if your backend is running correctly:

```bash
# Test API Gateway
curl http://localhost:8000/health

# Test AI Reasoning Orchestrator
curl http://localhost:8300/health

# Test GraphQL BFF
curl http://localhost:8400/health
```

#### **6. Development Proxy Setup (Alternative)**

If you prefer to use a proxy, add this to your `vite.config.ts`:

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/graphql': {
        target: 'http://localhost:8400',
        changeOrigin: true
      }
    }
  }
})
```

Then update your API client:

```typescript
// src/lib/api-client.ts
export const apiClient = new ApiClient('/api'); // This will proxy to localhost:8000
```

#### **7. Common Issues and Solutions**

**Issue**: "Network Error" or "Failed to fetch"
- **Solution**: Ensure backend services are running on the correct ports
- **Check**: Run `netstat -tulpn | grep :8000` to verify ports are in use

**Issue**: "CORS policy: No 'Access-Control-Allow-Origin' header"
- **Solution**: Verify CORS configuration in backend services
- **Check**: Ensure your frontend URL is in the `allow_origins` list

**Issue**: "401 Unauthorized"
- **Solution**: Set up authentication or use a test token
- **Temporary Fix**: Add a test token to bypass auth during development

```typescript
// Temporary development setup
const apiClient = new ApiClient('http://localhost:8000');
apiClient.setToken('test-token-for-development');
```

#### **8. Development Environment Checklist**

- [ ] Backend services are running on correct ports
- [ ] Frontend environment variables are set correctly
- [ ] CORS is configured for your frontend URL
- [ ] Network connectivity between frontend and backend
- [ ] Authentication is set up (or bypassed for development)

#### **9. Quick Start Script**

Create a `start-backend.sh` script for easy backend startup:

```bash
#!/bin/bash
# start-backend.sh

echo "Starting Personal Physician Assistant Backend Services..."

# Start Redis and PostgreSQL
docker-compose up -d redis postgres

# Start API Gateway
cd apps/api_gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
echo "API Gateway started on http://localhost:8000"

# Start AI Reasoning Orchestrator
cd ../ai_reasoning_orchestrator
python -m uvicorn main:app --host 0.0.0.0 --port 8300 --reload &
echo "AI Reasoning Orchestrator started on http://localhost:8300"

# Start GraphQL BFF
cd ../graphql_bff
python -m uvicorn main:app --host 0.0.0.0 --port 8400 --reload &
echo "GraphQL BFF started on http://localhost:8400"

# Start Health Tracking Service
cd ../health_tracking
python -m uvicorn main:app --host 0.0.0.0 --port 8100 --reload &
echo "Health Tracking Service started on http://localhost:8100"

echo "All backend services started!"
echo "Frontend can now connect to http://localhost:8000"
```

Make it executable and run:
```bash
chmod +x start-backend.sh
./start-backend.sh
```

## **Next Steps**

1. **Set up the project structure** as outlined above
2. **Configure authentication** with your backend
3. **Implement the core components** and pages
4. **Add error handling** and loading states
5. **Style the components** using your preferred UI library
6. **Add tests** for critical functionality
7. **Deploy** to your hosting platform

This guide provides a solid foundation for building a comprehensive frontend for the Personal Physician Assistant. The modular structure allows for easy expansion and maintenance as the application grows.

## Enhanced User Flow: Health Query → Symptom Analysis

### 🎯 **Smart User Journey Design**

The backend now provides an intelligent routing system that guides users through the optimal health assessment flow:

#### **Phase 1: Health Query (Educational)**
- **Purpose**: Provide educational health information
- **User Input**: Natural language health questions
- **Response**: Educational content + smart redirect suggestions
- **Example**: "What are the symptoms of diabetes?"

#### **Phase 2: Symptom Analysis (Clinical)**
- **Purpose**: Comprehensive clinical assessment
- **Trigger**: User accepts redirect suggestion
- **Response**: Clinical workflow with follow-up questions
- **Example**: "I have a headache" → Detailed assessment

### 🔄 **Recommended Frontend Flow**

```javascript
// Enhanced Health Query Flow
const handleHealthQuery = async (userQuery) => {
  try {
    // Step 1: Send to Health Query endpoint
    const response = await healthQueryAPI({
      query: userQuery,
      context: "User health inquiry",
      user_id: currentUser.id
    });

    // Step 2: Analyze response and determine next action
    if (response.should_redirect_to_symptoms) {
      // Show educational content + redirect suggestion
      showEducationalContent(response.educational_content);
      showRedirectSuggestion(response.redirect_reason);
      
      // Step 3: If user accepts, proceed to symptom analysis
      if (await userAcceptsRedirect()) {
        const symptomResponse = await symptomAnalysisAPI({
          symptoms: [response.query],
          include_vitals: true,
          include_medications: true,
          generate_insights: true
        });
        
        // Step 4: Show clinical assessment workflow
        showClinicalAssessment(symptomResponse);
      }
    } else {
      // Show educational content only
      showEducationalContent(response.educational_content);
    }
  } catch (error) {
    handleError(error);
  }
};
```

### 🎨 **UI/UX Components**

#### **1. Health Query Interface**
```jsx
const HealthQueryInterface = () => {
  return (
    <div className="health-query-container">
      {/* Natural language input */}
      <ChatInput 
        placeholder="Ask me anything about your health..."
        onSubmit={handleHealthQuery}
      />
      
      {/* Educational response */}
      <EducationalResponse 
        content={response.educational_content}
        queryAnalysis={response.query_analysis}
      />
      
      {/* Redirect suggestion (if applicable) */}
      {response.should_redirect_to_symptoms && (
        <RedirectSuggestion 
          reason={response.redirect_reason}
          onAccept={() => proceedToSymptomAnalysis()}
          onDecline={() => continueWithEducation()}
        />
      )}
    </div>
  );
};
```

#### **2. Symptom Analysis Interface**
```jsx
const SymptomAnalysisInterface = () => {
  return (
    <div className="symptom-analysis-container">
      {/* Clinical assessment header */}
      <ClinicalHeader 
        urgency={response.urgency_level}
        reasoning={response.urgency_reasoning}
      />
      
      {/* Follow-up questions */}
      <FollowUpQuestions 
        questions={response.follow_up_questions}
        onAnswer={handleQuestionAnswer}
        sessionId={response.session_id}
      />
      
      {/* Medical insights */}
      <MedicalInsights 
        insights={response.key_insights}
        possibleCauses={response.possible_causes}
        medicalContext={response.medical_context}
      />
      
      {/* Personalized recommendations */}
      <Recommendations 
        recommendations={response.recommendations}
        nextSteps={response.next_steps}
      />
    </div>
  );
};
```

### 🎯 **Key UI/UX Principles**

#### **1. Progressive Disclosure**
- Start with simple educational content
- Gradually reveal more detailed clinical information
- Don't overwhelm users with too much information at once

#### **2. Clear Visual Hierarchy**
```css
/* Educational content styling */
.educational-content {
  background: #f8f9fa;
  border-left: 4px solid #007bff;
  padding: 1rem;
  margin: 1rem 0;
}

/* Clinical assessment styling */
.clinical-assessment {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 1rem;
  margin: 1rem 0;
}

/* Urgency indicators */
.urgency-high {
  background: #f8d7da;
  border-left: 4px solid #dc3545;
}

.urgency-medium {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
}

.urgency-low {
  background: #d1ecf1;
  border-left: 4px solid #17a2b8;
}
```

#### **3. Interactive Elements**
```jsx
// Follow-up question component
const FollowUpQuestion = ({ question, onAnswer }) => {
  return (
    <div className="follow-up-question">
      <h4>{question.question}</h4>
      {question.type === 'multiple_choice' ? (
        <div className="options">
          {question.options.map(option => (
            <button 
              key={option}
              onClick={() => onAnswer(question.id, option)}
              className="option-button"
            >
              {option}
            </button>
          ))}
        </div>
      ) : (
        <input 
          type="text"
          placeholder="Your answer..."
          onBlur={(e) => onAnswer(question.id, e.target.value)}
        />
      )}
    </div>
  );
};
```

### 🔄 **State Management**

#### **1. Session Management**
```javascript
// Track conversation state
const [conversationState, setConversationState] = useState({
  currentPhase: 'query', // 'query' | 'assessment' | 'complete'
  sessionId: null,
  userAnswers: {},
  medicalContext: {},
  recommendations: []
});

// Update state based on responses
const updateConversationState = (response) => {
  setConversationState(prev => ({
    ...prev,
    sessionId: response.session_id,
    medicalContext: response.medical_context,
    recommendations: response.recommendations
  }));
};
```

#### **2. Answer Tracking**
```javascript
// Track user answers for follow-up questions
const [userAnswers, setUserAnswers] = useState({});

const handleQuestionAnswer = (questionId, answer) => {
  setUserAnswers(prev => ({
    ...prev,
    [questionId]: {
      answer,
      timestamp: new Date().toISOString()
    }
  }));
  
  // Send answers to backend for enhanced analysis
  updateSymptomAnalysis(questionId, answer);
};
```

### 🎨 **Visual Design Guidelines**

#### **1. Color Coding**
- **Educational Content**: Blue (#007bff) - Informational, trustworthy
- **Clinical Assessment**: Yellow (#ffc107) - Attention, assessment
- **High Urgency**: Red (#dc3545) - Warning, immediate action
- **Medium Urgency**: Orange (#fd7e14) - Caution, monitor
- **Low Urgency**: Green (#28a745) - Normal, continue monitoring

#### **2. Typography Hierarchy**
```css
.health-query-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #007bff;
}

.clinical-assessment-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffc107;
}

.urgency-high-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #dc3545;
}

.question-text {
  font-size: 1.1rem;
  font-weight: 500;
  color: #495057;
}

.medical-insight {
  font-size: 1rem;
  color: #6c757d;
  font-style: italic;
}
```

#### **3. Animation & Transitions**
```css
/* Smooth transitions between phases */
.phase-transition {
  transition: all 0.3s ease-in-out;
  opacity: 0;
  transform: translateY(20px);
}

.phase-transition.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Question appearance animation */
.follow-up-question {
  animation: slideInFromRight 0.4s ease-out;
}

@keyframes slideInFromRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

### 📊 **User Experience Flow**

#### **1. Initial Query**
```
User types: "I have a headache"
↓
System analyzes: symptom_inquiry
↓
Shows: Educational content about headaches
↓
Suggests: "Would you like a detailed assessment?"
```

#### **2. User Accepts Redirect**
```
User clicks: "Yes, assess my symptoms"
↓
System calls: Symptom Analysis API
↓
Shows: Clinical assessment interface
↓
Presents: Follow-up questions
```

#### **3. Interactive Assessment**
```
System asks: "How long have you been experiencing these symptoms?"
↓
User answers: "2-3 days"
↓
System asks: "Where is the headache located?"
↓
User answers: "Front of head"
↓
System provides: Personalized insights and recommendations
```

### 🎯 **Benefits of This Approach**

1. **User-Friendly**: Natural conversation flow
2. **Educational First**: Builds health literacy
3. **Progressive**: Gradually increases complexity
4. **Trust Building**: Educational content builds confidence
5. **Comprehensive**: Covers both education and clinical assessment
6. **Scalable**: Easy to add more query types and educational content

### 🚀 **Implementation Checklist**

- [ ] Implement Health Query interface with educational content display
- [ ] Add redirect suggestion modal/component
- [ ] Create Symptom Analysis interface with follow-up questions
- [ ] Implement session management and answer tracking
- [ ] Add urgency level indicators and styling
- [ ] Create smooth transitions between phases
- [ ] Add error handling and loading states
- [ ] Implement responsive design for mobile devices
- [ ] Add accessibility features (ARIA labels, keyboard navigation)
- [ ] Test user flow with various query types

This enhanced user flow creates a seamless, educational, and clinically comprehensive health assessment experience that guides users naturally from general health questions to detailed symptom analysis when appropriate.
