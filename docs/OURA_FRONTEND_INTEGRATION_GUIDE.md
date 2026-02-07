# 🏥 Oura Ring Frontend Integration Guide

## Overview

This guide explains how to integrate Oura Ring into your ReactJS frontend application for the POC version, using the Oura sandbox for testing with proper user management.

## 🎯 Key Features

- ✅ **User-specific sandbox data** - Each user gets their own mock data
- ✅ **JWT authentication** - Secure user context
- ✅ **Device ownership validation** - Users can only access their own devices
- ✅ **Sandbox mode** - No real Oura API tokens needed for testing

---

## 🔧 Backend Setup

### 1. Environment Configuration

Set these environment variables in your backend:

```bash
# Enable Oura sandbox mode
export OURA_USE_SANDBOX=true

# Optional: Custom sandbox API URL
export OURA_SANDBOX_API_BASE_URL=http://localhost:8000/api/v1/device-data/oura-sandbox
```

### 2. Verify Backend is Running

```bash
# Test health endpoint
curl http://device-data.localhost/health

# Test supported integrations (should include Oura Ring)
curl http://device-data.localhost/api/v1/device-data/integrations/supported
```

---

## 🚀 Frontend Integration Steps

### Step 1: Authentication Setup

Ensure your frontend has JWT authentication working:

```javascript
// Example: Login and get JWT token
const login = async (email, password) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  localStorage.setItem('jwt_token', data.token);
  return data.token;
};

// Helper function to get auth headers
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
  'Content-Type': 'application/json'
});
```

### Step 2: Create Oura Ring Device

```javascript
// Create a new Oura Ring device for the user
const createOuraDevice = async () => {
  const deviceData = {
    name: "Oura Ring Gen 3",
    device_type: "SMART_RING",
    manufacturer: "Oura",
    model: "Gen 3",
    connection_type: "api",
    serial_number: `OURA-${Date.now()}`, // Generate unique serial
    metadata: {
      source: "oura_ring",
      sandbox: true // Enable sandbox mode
    }
  };

  const response = await fetch('http://device-data.localhost/api/v1/device-data/devices/', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(deviceData)
  });

  const device = await response.json();
  console.log('Created Oura device:', device);
  return device;
};
```

### Step 3: Connect Oura Device

```javascript
// Connect the Oura device (this will use sandbox mode)
const connectOuraDevice = async (deviceId) => {
  const connectionData = {
    connection_type: "api",
    connection_id: "sandbox-connection",
    api_key: null, // No real token needed in sandbox
    metadata: {
      sandbox: true
    }
  };

  const response = await fetch(`http://device-data.localhost/api/v1/device-data/devices/${deviceId}/connect`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(connectionData)
  });

  const result = await response.json();
  console.log('Device connected:', result);
  return result;
};
```

### Step 4: Sync Oura Data

```javascript
// Sync data from Oura Ring (sandbox will generate user-specific mock data)
const syncOuraData = async (deviceId) => {
  const syncData = {
    start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
    end_date: new Date().toISOString(),
    data_types: ["sleep", "activity", "readiness", "heart_rate"]
  };

  const response = await fetch(`http://device-data.localhost/api/v1/device-data/devices/${deviceId}/sync`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(syncData)
  });

  const result = await response.json();
  console.log('Data synced:', result);
  return result;
};
```

### Step 5: Retrieve Synced Data

```javascript
// Get synced data points
const getOuraData = async (deviceId, dataType = 'sleep') => {
  const response = await fetch(
    `http://device-data.localhost/api/v1/device-data/data/?device_id=${deviceId}&data_type=${dataType}&limit=100`,
    {
      headers: getAuthHeaders()
    }
  );

  const data = await response.json();
  console.log(`${dataType} data:`, data);
  return data;
};
```

---

## 📱 Complete React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const OuraIntegration = () => {
  const [device, setDevice] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Step 1: Create device
  const handleCreateDevice = async () => {
    setLoading(true);
    try {
      const newDevice = await createOuraDevice();
      setDevice(newDevice);
      alert('Oura device created successfully!');
    } catch (error) {
      console.error('Error creating device:', error);
      alert('Failed to create device');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Connect device
  const handleConnectDevice = async () => {
    if (!device) {
      alert('Please create a device first');
      return;
    }

    setLoading(true);
    try {
      await connectOuraDevice(device.id);
      setIsConnected(true);
      alert('Device connected successfully!');
    } catch (error) {
      console.error('Error connecting device:', error);
      alert('Failed to connect device');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Sync data
  const handleSyncData = async () => {
    if (!device || !isConnected) {
      alert('Please create and connect a device first');
      return;
    }

    setLoading(true);
    try {
      const syncResult = await syncOuraData(device.id);
      alert(`Synced ${syncResult.data_points_count} data points!`);
      
      // Fetch the synced data
      const sleepData = await getOuraData(device.id, 'sleep');
      setData(sleepData);
    } catch (error) {
      console.error('Error syncing data:', error);
      alert('Failed to sync data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="oura-integration">
      <h2>Oura Ring Integration (Sandbox Mode)</h2>
      
      <div className="actions">
        <button 
          onClick={handleCreateDevice} 
          disabled={loading || device}
          className="btn btn-primary"
        >
          {loading ? 'Creating...' : 'Create Oura Device'}
        </button>

        <button 
          onClick={handleConnectDevice} 
          disabled={loading || !device || isConnected}
          className="btn btn-secondary"
        >
          {loading ? 'Connecting...' : 'Connect Device'}
        </button>

        <button 
          onClick={handleSyncData} 
          disabled={loading || !isConnected}
          className="btn btn-success"
        >
          {loading ? 'Syncing...' : 'Sync Data'}
        </button>
      </div>

      {device && (
        <div className="device-info">
          <h3>Device Information</h3>
          <p><strong>ID:</strong> {device.id}</p>
          <p><strong>Name:</strong> {device.name}</p>
          <p><strong>Status:</strong> {device.status}</p>
          <p><strong>Connected:</strong> {isConnected ? 'Yes' : 'No'}</p>
        </div>
      )}

      {data && (
        <div className="data-display">
          <h3>Synced Data</h3>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default OuraIntegration;
```

---

## 🔍 Testing the Integration

### 1. Test User-Specific Data

Each user will get different mock data:

```javascript
// User A logs in and syncs data
const userA = await login('userA@example.com', 'password');
const deviceA = await createOuraDevice();
await syncOuraData(deviceA.id);

// User B logs in and syncs data  
const userB = await login('userB@example.com', 'password');
const deviceB = await createOuraDevice();
await syncOuraData(deviceB.id);

// Each user will get different mock data based on their user_id
```

### 2. Verify Data Ownership

```javascript
// This will only return data for the authenticated user
const myData = await getOuraData(deviceId, 'sleep');
console.log('My sleep data:', myData);
```

### 3. Test Error Handling

```javascript
// Test with invalid device ID (should fail)
try {
  await syncOuraData('invalid-device-id');
} catch (error) {
  console.log('Expected error:', error.message);
}
```

---

## 🎨 UI/UX Recommendations

### 1. Loading States
- Show loading spinners during API calls
- Disable buttons while operations are in progress
- Provide clear feedback for each step

### 2. Error Handling
- Display user-friendly error messages
- Retry mechanisms for failed operations
- Graceful degradation when services are unavailable

### 3. Data Visualization
- Use charts to display sleep, activity, and readiness data
- Show trends over time
- Highlight important metrics

### 4. User Feedback
- Success notifications for completed operations
- Progress indicators for long-running operations
- Clear status indicators for device connection state

---

## 🔒 Security Considerations

### 1. JWT Token Management
- Store tokens securely (httpOnly cookies recommended)
- Implement token refresh logic
- Clear tokens on logout

### 2. CORS Configuration
- Ensure your backend allows requests from your frontend domain
- Configure proper CORS headers

### 3. Input Validation
- Validate all user inputs on both frontend and backend
- Sanitize data before sending to API

---

## 🚀 Production Considerations

When moving from POC to production:

### 1. Real Oura API Integration
```javascript
// Disable sandbox mode
export OURA_USE_SANDBOX=false

// Use real Oura access tokens
const realOuraToken = await getOuraAccessToken(userId);
```

### 2. Enhanced Error Handling
- Handle Oura API rate limits
- Implement retry logic for failed requests
- Monitor API usage and costs

### 3. Data Persistence
- Store synced data in your database
- Implement data versioning
- Handle data conflicts

### 4. User Experience
- Implement background sync
- Add data freshness indicators
- Provide data export functionality

---

## 📞 Support

For issues or questions:
1. Check the backend logs for detailed error messages
2. Verify JWT token validity
3. Ensure device ownership matches authenticated user
4. Test with the provided sandbox mode first

---

## 🎉 Success Metrics

Your integration is working correctly when:
- ✅ Users can create Oura devices
- ✅ Devices connect successfully in sandbox mode
- ✅ Each user gets unique mock data
- ✅ Data sync operations complete without errors
- ✅ Retrieved data is associated with the correct user 