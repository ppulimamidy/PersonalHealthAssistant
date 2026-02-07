# Epic FHIR Complete Integration Guide

## 🎯 **Overview**

This guide provides a complete solution for integrating Epic FHIR data into the PersonalHealthAssistant app. The solution includes:

1. **OAuth2 Authentication Flow** - Secure user authentication with Epic FHIR
2. **Data Capture & Storage** - Automatic capture and local storage of Epic FHIR data
3. **Data Retrieval & Display** - APIs for retrieving and displaying stored data
4. **Frontend Integration** - Complete UI integration examples

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │ Medical Records  │    │   Epic FHIR     │
│                 │    │     Service      │    │    Sandbox      │
│ • OAuth2 Flow   │◄──►│ • OAuth2 Handler │◄──►│ • Patient Data  │
│ • Data Display  │    │ • Data Storage   │    │ • Observations  │
│ • Sync Status   │    │ • Local Database │    │ • Reports       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 **Database Schema**

### **Epic FHIR Data Tables**

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `epic_fhir_connections` | Store OAuth2 connections | `user_id`, `access_token`, `patient_id` |
| `epic_fhir_observations` | Store patient observations | `fhir_id`, `category`, `value_quantity`, `effective_datetime` |
| `epic_fhir_diagnostic_reports` | Store diagnostic reports | `fhir_id`, `category`, `conclusion`, `issued` |
| `epic_fhir_documents` | Store medical documents | `fhir_id`, `type`, `content_url`, `date` |
| `epic_fhir_imaging_studies` | Store imaging studies | `fhir_id`, `modality`, `procedure_code`, `started` |
| `epic_fhir_sync_logs` | Track sync operations | `connection_id`, `sync_type`, `records_synced` |

## 🔐 **OAuth2 Authentication Flow**

### **Step 1: Initiate OAuth2 Flow**

```javascript
// Frontend: Start OAuth2 flow
const startEpicFHIRAuth = async (patientName = 'anna') => {
  try {
    const response = await fetch('/api/v1/medical-records/epic-fhir/authorize', {
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    // Redirect user to Epic FHIR authorization URL
    window.location.href = `${data.authorization_url}&patient_name=${patientName}`;
    
  } catch (error) {
    console.error('Failed to start OAuth2 flow:', error);
  }
};
```

### **Step 2: Handle OAuth2 Callback**

The callback URL (`http://localhost:8005/api/v1/medical-records/epic-fhir/callback`) will:

1. **Exchange authorization code for access token**
2. **Create connection record** in local database
3. **Automatically sync patient data** from Epic FHIR
4. **Return sync results** to frontend

```javascript
// Frontend: Handle callback response
const handleOAuthCallback = async (code, state, patientName) => {
  try {
    const response = await fetch(`/api/v1/medical-records/epic-fhir/callback?code=${code}&state=${state}&patient_name=${patientName}`, {
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      console.log('OAuth2 successful!');
      console.log('Connection ID:', result.connection_id);
      console.log('Sync Results:', result.sync_results);
      
      // Update UI to show connected state
      updateConnectionStatus('connected', result);
      
      // Refresh data display
      loadStoredData();
    }
    
  } catch (error) {
    console.error('OAuth2 callback failed:', error);
  }
};
```

## 📊 **Data Retrieval APIs**

### **1. Get Stored Observations**

```javascript
// Get all observations for the user
const getMyObservations = async (filters = {}) => {
  const params = new URLSearchParams({
    limit: filters.limit || 100,
    offset: filters.offset || 0,
    ...(filters.category && { category: filters.category }),
    ...(filters.dateFrom && { date_from: filters.dateFrom }),
    ...(filters.dateTo && { date_to: filters.dateTo })
  });
  
  const response = await fetch(`/api/v1/medical-records/epic-fhir/my/observations?${params}`, {
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};

// Example usage
const observations = await getMyObservations({
  category: 'vital-signs',
  dateFrom: '2024-01-01',
  dateTo: '2024-12-31',
  limit: 50
});

console.log('Observations:', observations.observations);
console.log('Total count:', observations.total_count);
```

### **2. Get Diagnostic Reports**

```javascript
const getMyDiagnosticReports = async (filters = {}) => {
  const params = new URLSearchParams({
    limit: filters.limit || 100,
    offset: filters.offset || 0,
    ...(filters.category && { category: filters.category }),
    ...(filters.dateFrom && { date_from: filters.dateFrom }),
    ...(filters.dateTo && { date_to: filters.dateTo })
  });
  
  const response = await fetch(`/api/v1/medical-records/epic-fhir/my/diagnostic-reports?${params}`, {
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};
```

### **3. Get Sync Logs**

```javascript
const getMySyncLogs = async (limit = 50, offset = 0) => {
  const response = await fetch(`/api/v1/medical-records/epic-fhir/my/sync-logs?limit=${limit}&offset=${offset}`, {
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};
```

### **4. Get Connection Status**

```javascript
const getMyConnection = async () => {
  const response = await fetch('/api/v1/medical-records/epic-fhir/my/connection', {
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};
```

## 🔄 **Data Synchronization**

### **Manual Sync**

```javascript
const syncMyData = async (options = {}) => {
  const params = new URLSearchParams({
    ...(options.resourceTypes && { resource_types: options.resourceTypes.join(',') }),
    ...(options.dateFrom && { date_from: options.dateFrom }),
    ...(options.dateTo && { date_to: options.dateTo })
  });
  
  const response = await fetch(`/api/v1/medical-records/epic-fhir/my/sync?${params}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};

// Example: Sync all data types
const syncAll = await syncMyData();

// Example: Sync only observations from last 30 days
const syncRecent = await syncMyData({
  resourceTypes: ['Observation'],
  dateFrom: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  dateTo: new Date().toISOString()
});
```

### **Disconnect Connection**

```javascript
const disconnectConnection = async () => {
  const response = await fetch('/api/v1/medical-records/epic-fhir/my/connection', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${userToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  return await response.json();
};
```

## 🎨 **Frontend UI Integration**

### **React Component Example**

```jsx
import React, { useState, useEffect } from 'react';

const EpicFHIRIntegration = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [observations, setObservations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncResults, setSyncResults] = useState(null);

  // Check connection status on component mount
  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const connection = await getMyConnection();
      setConnectionStatus(connection.status);
      
      if (connection.status === 'connected') {
        loadObservations();
      }
    } catch (error) {
      console.error('Failed to check connection:', error);
    }
  };

  const startOAuthFlow = async (patientName = 'anna') => {
    setLoading(true);
    try {
      await startEpicFHIRAuth(patientName);
    } catch (error) {
      console.error('OAuth flow failed:', error);
      setLoading(false);
    }
  };

  const loadObservations = async () => {
    try {
      const data = await getMyObservations({
        limit: 50,
        category: 'vital-signs'
      });
      setObservations(data.observations);
    } catch (error) {
      console.error('Failed to load observations:', error);
    }
  };

  const handleManualSync = async () => {
    setLoading(true);
    try {
      const results = await syncMyData();
      setSyncResults(results);
      await loadObservations(); // Refresh data
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const disconnect = async () => {
    try {
      await disconnectConnection();
      setConnectionStatus('disconnected');
      setObservations([]);
      setSyncResults(null);
    } catch (error) {
      console.error('Disconnect failed:', error);
    }
  };

  return (
    <div className="epic-fhir-integration">
      <h2>Epic FHIR Integration</h2>
      
      {/* Connection Status */}
      <div className="connection-status">
        <h3>Connection Status: {connectionStatus}</h3>
        
        {connectionStatus === 'disconnected' && (
          <div>
            <p>Connect to Epic FHIR to access your medical data</p>
            <button 
              onClick={() => startOAuthFlow('anna')}
              disabled={loading}
            >
              {loading ? 'Connecting...' : 'Connect to Epic FHIR'}
            </button>
          </div>
        )}
        
        {connectionStatus === 'connected' && (
          <div>
            <button onClick={handleManualSync} disabled={loading}>
              {loading ? 'Syncing...' : 'Sync Data'}
            </button>
            <button onClick={disconnect} className="disconnect-btn">
              Disconnect
            </button>
          </div>
        )}
      </div>

      {/* Sync Results */}
      {syncResults && (
        <div className="sync-results">
          <h4>Last Sync Results</h4>
          <pre>{JSON.stringify(syncResults, null, 2)}</pre>
        </div>
      )}

      {/* Observations Display */}
      {observations.length > 0 && (
        <div className="observations">
          <h3>Recent Observations ({observations.length})</h3>
          <div className="observations-grid">
            {observations.map(obs => (
              <div key={obs.id} className="observation-card">
                <h4>{obs.code_display || obs.code}</h4>
                <p>Category: {obs.category}</p>
                {obs.value_quantity && (
                  <p>Value: {obs.value_quantity} {obs.value_unit}</p>
                )}
                {obs.effective_datetime && (
                  <p>Date: {new Date(obs.effective_datetime).toLocaleDateString()}</p>
                )}
                {obs.interpretation && (
                  <p>Interpretation: {obs.interpretation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EpicFHIRIntegration;
```

### **CSS Styling**

```css
.epic-fhir-integration {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.connection-status {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.connection-status button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

.connection-status button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.disconnect-btn {
  background: #dc3545 !important;
}

.sync-results {
  background: #e9ecef;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.sync-results pre {
  background: white;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.observations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.observation-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.observation-card h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.observation-card p {
  margin: 5px 0;
  color: #666;
}
```

## 🚀 **Implementation Steps**

### **Phase 1: Database Setup**

1. **Create Epic FHIR tables:**
   ```bash
   cd apps/medical_records
   python create_epic_fhir_tables.py create
   ```

2. **Verify tables created:**
   ```bash
   python create_epic_fhir_tables.py check
   ```

### **Phase 2: Backend Deployment**

1. **Rebuild medical records service:**
   ```bash
   docker-compose build medical-records-service
   docker-compose up -d medical-records-service
   ```

2. **Test OAuth2 flow:**
   ```bash
   curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/authorize" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### **Phase 3: Frontend Integration**

1. **Add Epic FHIR component to your React app**
2. **Implement OAuth2 flow handling**
3. **Add data display components**
4. **Test complete flow**

## 📝 **API Endpoints Summary**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/authorize` | GET | Start OAuth2 flow |
| `/callback` | GET | Handle OAuth2 callback + data sync |
| `/my/connection` | GET | Get connection status |
| `/my/connection` | DELETE | Disconnect |
| `/my/observations` | GET | Get stored observations |
| `/my/diagnostic-reports` | GET | Get stored reports |
| `/my/sync-logs` | GET | Get sync history |
| `/my/sync` | POST | Manual data sync |

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Epic FHIR Configuration
EPIC_FHIR_CLIENT_ID=${EPIC_FHIR_CLIENT_ID:-}
EPIC_FHIR_CLIENT_SECRET=***REMOVED***
EPIC_FHIR_ENVIRONMENT=SANDBOX
EPIC_FHIR_REDIRECT_URI=http://localhost:8005/api/v1/medical-records/epic-fhir/callback
```

### **Test Patients**

Available test patients in Epic FHIR sandbox:
- `anna` - Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB
- `henry` - a1
- `john` - a2
- `omar` - a3
- `kyle` - a4

## 🎉 **Complete Flow Example**

1. **User clicks "Connect to Epic FHIR"**
2. **Frontend calls `/authorize` endpoint**
3. **User redirected to Epic FHIR login**
4. **User logs in with sandbox credentials (FHIR/EpicFhir11!)**
5. **Epic redirects to `/callback` with authorization code**
6. **Backend exchanges code for token**
7. **Backend creates connection record**
8. **Backend automatically syncs patient data**
9. **Frontend displays stored data**
10. **User can view, filter, and refresh data**

## 🔍 **Troubleshooting**

### **Common Issues**

1. **OAuth2 callback fails:**
   - Check redirect URI matches exactly
   - Verify client ID and secret are correct
   - Ensure user has proper permissions

2. **Data sync fails:**
   - Check Epic FHIR token is valid
   - Verify patient ID exists in sandbox
   - Check database connection

3. **Frontend can't connect:**
   - Verify medical records service is running
   - Check CORS configuration
   - Ensure authentication token is valid

### **Debug Commands**

```bash
# Check service status
docker-compose logs medical-records-service

# Test OAuth2 flow
curl -X GET "http://localhost:8005/api/v1/medical-records/epic-fhir/authorize" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check database tables
python apps/medical_records/create_epic_fhir_tables.py check
```

This complete integration provides a robust solution for capturing, storing, and displaying Epic FHIR data in your PersonalHealthAssistant app! 🚀 