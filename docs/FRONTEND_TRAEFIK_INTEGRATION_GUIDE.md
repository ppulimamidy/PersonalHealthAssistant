# 🔄 Frontend Integration Guide for Enhanced Traefik Configuration

## **Overview**

With the enhanced Traefik configuration now in place, your frontend UI needs to be updated to use the new service URLs and authentication flow. This guide will help you migrate from direct port access to the centralized Traefik gateway.

## **🚨 Important Changes Required**

### **1. Service URL Changes**

**Before (Direct Port Access):**
```javascript
// Old URLs - Direct port access
const AUTH_URL = "http://localhost:8000";
const HEALTH_TRACKING_URL = "http://localhost:8002";
const NUTRITION_URL = "http://localhost:8007";
const ANALYTICS_URL = "http://localhost:8210";
```

**After (Traefik Gateway):**
```javascript
// New URLs - Through Traefik gateway
const AUTH_URL = "http://auth.localhost";
const HEALTH_TRACKING_URL = "http://health-tracking.localhost";
const NUTRITION_URL = "http://nutrition.localhost";
const ANALYTICS_URL = "http://analytics.localhost";
```

### **2. Authentication Flow Changes**

**Before (Direct Auth):**
```javascript
// Old authentication flow
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return response.json();
};
```

**After (Basic Auth + JWT):**
```javascript
// New authentication flow with Basic Auth
const login = async (email, password) => {
  // Create Basic Auth credentials
  const credentials = btoa(`${email}:${password}`);
  
  const response = await fetch('http://auth.localhost/auth/login', {
    method: 'POST',
    headers: { 
      'Authorization': `Basic ${credentials}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  // Store session token (not access_token)
  if (data.session?.session_token) {
    localStorage.setItem('session_token', data.session.session_token);
    localStorage.setItem('refresh_token', data.session.refresh_token);
    localStorage.setItem('user_id', data.user.id);
  }
  
  return data;
};
```

## **🔧 Required Frontend Updates**

### **1. Update API Configuration**

Create a new API configuration file:

```javascript
// config/api.js
export const API_CONFIG = {
  // Traefik Gateway URLs
  AUTH_SERVICE: "http://auth.localhost",
  HEALTH_TRACKING_SERVICE: "http://health-tracking.localhost",
  NUTRITION_SERVICE: "http://nutrition.localhost",
  ANALYTICS_SERVICE: "http://analytics.localhost",
  MEDICAL_RECORDS_SERVICE: "http://medical-records.localhost",
  VOICE_INPUT_SERVICE: "http://voice-input.localhost",
  AI_INSIGHTS_SERVICE: "http://ai-insights.localhost",
  CONSENT_AUDIT_SERVICE: "http://consent-audit.localhost",
  
  // Fallback URLs (for development)
  FALLBACK_URLS: {
    AUTH_SERVICE: "http://localhost:8000",
    HEALTH_TRACKING_SERVICE: "http://localhost:8002",
    NUTRITION_SERVICE: "http://localhost:8007",
    ANALYTICS_SERVICE: "http://localhost:8210",
  }
};

// Helper function to get service URL with fallback
export const getServiceUrl = (serviceName) => {
  const primaryUrl = API_CONFIG[serviceName];
  const fallbackUrl = API_CONFIG.FALLBACK_URLS[serviceName];
  
  // Try primary URL first, fallback to direct port
  return primaryUrl || fallbackUrl;
};
```

### **2. Update Authentication Service**

```javascript
// services/authService.js
import { getServiceUrl } from '../config/api.js';

class AuthService {
  constructor() {
    this.authUrl = getServiceUrl('AUTH_SERVICE');
  }

  // Login with Basic Authentication
  async login(email, password) {
    try {
      const credentials = btoa(`${email}:${password}`);
      
      const response = await fetch(`${this.authUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${credentials}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Login failed: ${response.status}`);
      }

      const data = await response.json();
      
      // Store session information
      if (data.session?.session_token) {
        localStorage.setItem('session_token', data.session.session_token);
        localStorage.setItem('refresh_token', data.session.refresh_token);
        localStorage.setItem('user_id', data.user.id);
        localStorage.setItem('user_email', data.user.email);
        localStorage.setItem('user_type', data.user.user_type);
      }

      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  // Get current session token
  getSessionToken() {
    return localStorage.getItem('session_token');
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getSessionToken();
  }

  // Logout
  async logout() {
    try {
      const token = this.getSessionToken();
      if (token) {
        await fetch(`${this.authUrl}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('session_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_id');
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_type');
    }
  }

  // Refresh token
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${this.authUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      if (data.access_token) {
        localStorage.setItem('session_token', data.access_token);
        return data.access_token;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      // Redirect to login if refresh fails
      this.logout();
      window.location.href = '/login';
    }
  }
}

export default new AuthService();
```

### **3. Update API Client**

```javascript
// services/apiClient.js
import { getServiceUrl } from '../config/api.js';
import authService from './authService.js';

class ApiClient {
  constructor() {
    this.baseHeaders = {
      'Content-Type': 'application/json'
    };
  }

  // Add authentication header
  getAuthHeaders() {
    const token = authService.getSessionToken();
    return {
      ...this.baseHeaders,
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  // Generic API call with authentication
  async apiCall(serviceName, endpoint, options = {}) {
    const baseUrl = getServiceUrl(serviceName);
    const url = `${baseUrl}${endpoint}`;
    
    const config = {
      headers: this.getAuthHeaders(),
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      // Handle 401 Unauthorized
      if (response.status === 401) {
        // Try to refresh token
        await authService.refreshToken();
        
        // Retry with new token
        const newToken = authService.getSessionToken();
        if (newToken) {
          config.headers['Authorization'] = `Bearer ${newToken}`;
          const retryResponse = await fetch(url, config);
          return this.handleResponse(retryResponse);
        } else {
          // Redirect to login
          authService.logout();
          window.location.href = '/login';
          return;
        }
      }
      
      return this.handleResponse(response);
    } catch (error) {
      console.error('API call error:', error);
      throw error;
    }
  }

  handleResponse(response) {
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // Health Tracking API calls
  async getHealthData(userId, params = {}) {
    return this.apiCall('HEALTH_TRACKING_SERVICE', `/api/v1/health-tracking/data/${userId}`, {
      method: 'GET',
      params
    });
  }

  async submitHealthData(data) {
    return this.apiCall('HEALTH_TRACKING_SERVICE', '/api/v1/health-tracking/data', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // Nutrition API calls
  async recognizeFood(imageFile, options = {}) {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    Object.entries(options).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const baseUrl = getServiceUrl('NUTRITION_SERVICE');
    const token = authService.getSessionToken();
    
    const response = await fetch(`${baseUrl}/api/v1/nutrition/food-recognition/recognize`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    return this.handleResponse(response);
  }

  // Analytics API calls
  async getAnalyticsCapabilities() {
    return this.apiCall('ANALYTICS_SERVICE', '/api/v1/analytics/capabilities', {
      method: 'GET'
    });
  }

  async getPatientHealthAnalytics(patientId, timeRange = '1_month') {
    return this.apiCall('ANALYTICS_SERVICE', `/api/v1/analytics/patient/${patientId}/health`, {
      method: 'POST',
      body: JSON.stringify({ time_range: timeRange })
    });
  }
}

export default new ApiClient();
```

### **4. Update Login Component**

```javascript
// components/Login.jsx
import React, { useState } from 'react';
import authService from '../services/authService.js';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await authService.login(email, password);
      
      if (result.session?.session_token) {
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } catch (error) {
      setError(error.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleLogin}>
        <h2>Login to Personal Health Assistant</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default Login;
```

### **5. Update Dashboard Component**

```javascript
// components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import apiClient from '../services/apiClient.js';
import authService from '../services/authService.js';

const Dashboard = () => {
  const [userData, setUserData] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const userId = localStorage.getItem('user_id');
        
        // Load user data
        const userResponse = await apiClient.apiCall(
          'USER_PROFILE_SERVICE', 
          `/api/v1/profile/${userId}`
        );
        setUserData(userResponse);

        // Load health data
        const healthResponse = await apiClient.getHealthData(userId);
        setHealthData(healthResponse);
        
      } catch (error) {
        console.error('Dashboard loading error:', error);
      } finally {
        setLoading(false);
      }
    };

    if (authService.isAuthenticated()) {
      loadDashboardData();
    } else {
      window.location.href = '/login';
    }
  }, []);

  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  if (loading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <header>
        <h1>Personal Health Assistant Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      
      {userData && (
        <div className="user-info">
          <h2>Welcome, {userData.first_name} {userData.last_name}</h2>
          <p>Email: {userData.email}</p>
          <p>User Type: {userData.user_type}</p>
        </div>
      )}
      
      {healthData && (
        <div className="health-data">
          <h3>Recent Health Data</h3>
          {/* Display health data */}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
```

## **🔍 Testing Your Frontend Integration**

### **1. Test Authentication Flow**

```javascript
// Test script for frontend integration
const testFrontendIntegration = async () => {
  try {
    // Test login
    const loginResult = await authService.login('test@example.com', 'password123');
    console.log('Login successful:', loginResult);
    
    // Test API call
    const capabilities = await apiClient.getAnalyticsCapabilities();
    console.log('Analytics capabilities:', capabilities);
    
    // Test health data
    const userId = localStorage.getItem('user_id');
    const healthData = await apiClient.getHealthData(userId);
    console.log('Health data:', healthData);
    
  } catch (error) {
    console.error('Integration test failed:', error);
  }
};
```

### **2. Check Network Tab**

1. Open browser DevTools
2. Go to Network tab
3. Perform login and API calls
4. Verify requests are going to `.localhost` URLs
5. Check for proper Authorization headers

### **3. Common Issues and Solutions**

| Issue | Cause | Solution |
|-------|-------|----------|
| CORS errors | Frontend origin not allowed | Add `http://localhost:5173` to CORS origins |
| 401 Unauthorized | Wrong token format | Use `session_token` instead of `access_token` |
| 404 Not Found | Wrong service URL | Use `.localhost` URLs instead of direct ports |
| Network errors | Service not running | Check `docker-compose ps` for service status |

## **🚀 Migration Checklist**

- [ ] Update all service URLs to use `.localhost` domains
- [ ] Implement Basic Authentication for login
- [ ] Update token storage to use `session_token`
- [ ] Add token refresh logic
- [ ] Update API client to handle 401 responses
- [ ] Test authentication flow end-to-end
- [ ] Test all API endpoints through Traefik
- [ ] Update error handling for new response formats
- [ ] Test CORS and security headers
- [ ] Verify rate limiting behavior

## **📊 Benefits of the New Configuration**

1. **Centralized Authentication**: All requests go through Traefik with forward auth
2. **Better Security**: JWT tokens validated centrally
3. **Rate Limiting**: Automatic rate limiting per user
4. **Security Headers**: Consistent security headers across all services
5. **Monitoring**: Centralized logging and monitoring
6. **Scalability**: Easy to add new services and load balancing

## **🔗 Useful URLs**

- **Frontend**: http://localhost:5173
- **Traefik Dashboard**: http://localhost:8081 (admin/admin)
- **Auth Service**: http://auth.localhost
- **Analytics Service**: http://analytics.localhost
- **Health Tracking**: http://health-tracking.localhost
- **Nutrition Service**: http://nutrition.localhost

## **📞 Support**

If you encounter issues during migration:

1. Check Traefik logs: `docker-compose logs -f traefik`
2. Check auth service logs: `docker-compose logs -f auth-service`
3. Verify service health: `docker-compose ps`
4. Test endpoints manually with curl
5. Check browser network tab for request details

The enhanced Traefik configuration provides a more robust, secure, and scalable architecture for your Personal Health Assistant platform! 