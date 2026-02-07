# Frontend Quick Reference Card

## 🚀 Service URLs & Ports

| Service | Port | Health Check | Status |
|---------|------|--------------|--------|
| **Auth** | 8000 | `/health` | ✅ Running |
| **User Profile** | 8001 | `/health` | ✅ Running |
| **Health Tracking** | 8002 | `/health` | ✅ Running |
| **Voice Input** | 8003 | `/health` | ✅ Running |
| **Device Data** | 8004 | `/health` | ✅ Running |
| **Medical Records** | 8005 | `/health` | ✅ Running |
| **Medical Analysis** | 8006 | `/ready` | ✅ Running |
| **AI Insights** | 8200 | `/health` | ✅ Running |

## 🔐 Authentication Flow

```javascript
// 1. Register
const register = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
    first_name: 'John',
    last_name: 'Doe'
  })
});

// 2. Login
const login = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access_token } = await login.json();

// 3. Use token
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};
```

## 📊 Key Endpoints

### Health Data
```javascript
// Submit health data
POST http://localhost:8002/api/v1/health/data
{
  "user_id": "uuid",
  "data_type": "heart_rate",
  "value": 75,
  "unit": "bpm",
  "timestamp": "2024-01-01T12:00:00Z"
}

// Get health data
GET http://localhost:8002/api/v1/health/data/{user_id}?data_type=heart_rate&start_date=2024-01-01

// Get analytics
GET http://localhost:8002/api/v1/health/analytics/{user_id}?period=daily&data_type=heart_rate
```

### User Profile
```javascript
// Get profile
GET http://localhost:8001/api/v1/profile/{user_id}

// Update profile
PUT http://localhost:8001/api/v1/profile/{user_id}
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

### Voice Input
```javascript
// Process voice
const formData = new FormData();
formData.append('audio_file', audioBlob);
formData.append('user_id', 'uuid');

POST http://localhost:8003/api/v1/voice-input/voice-input
```

### Medical Analysis
```javascript
// Analyze health data
POST http://localhost:8006/api/v1/medical/analyze
{
  "user_id": "uuid",
  "analysis_type": "health_trends",
  "timeframe": "30_days"
}
```

## 🔄 Common Patterns

### API Call Helper
```javascript
async function apiCall(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    },
    ...options
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error?.message || 'API request failed');
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

### Error Handling
```javascript
try {
  const data = await apiCall('http://localhost:8002/api/v1/health/data/user123');
  console.log('Success:', data);
} catch (error) {
  if (error.message.includes('AUTHENTICATION_ERROR')) {
    // Redirect to login
    window.location.href = '/login';
  } else {
    // Show error message
    showError(error.message);
  }
}
```

## 📡 WebSocket Connections

```javascript
// Real-time health data
const healthWs = new WebSocket('ws://localhost:8002/ws/health-data/user123');
healthWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateHealthDashboard(data);
};

// Voice processing updates
const voiceWs = new WebSocket('ws://localhost:8003/ws/voice-processing/user123');
voiceWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateVoiceStatus(data);
};
```

## 🎯 Quick Test Commands

```bash
# Test all services are running
curl http://localhost:8000/health  # Auth
curl http://localhost:8001/health  # User Profile
curl http://localhost:8002/health  # Health Tracking
curl http://localhost:8003/health  # Voice Input
curl http://localhost:8004/health  # Device Data
curl http://localhost:8005/health  # Medical Records
curl http://localhost:8006/ready   # Medical Analysis
curl http://localhost:8200/health  # AI Insights

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","first_name":"Test","last_name":"User"}'
```

## 🚨 Important Notes

- **All endpoints require authentication** except registration and login
- **Token expires in 1 hour** - implement refresh logic
- **Rate limits**: 10/min for auth, 100/min for data submission
- **File uploads**: Use `multipart/form-data` for audio/images
- **Error responses**: Always check `success` field in response
- **CORS**: Configured for `localhost:3000` and `localhost:8080`

## 📚 Full Documentation

For complete API documentation, see: `docs/BACKEND_API_SPECIFICATION.md` 