# Personal Health Assistant - API Endpoints Documentation

## Base URLs
- **Health Analysis Service**: `http://health-analysis.localhost`
- **Health Tracking Service**: `http://health-tracking.localhost`
- **Nutrition Service**: `http://nutrition.localhost`
- **Auth Service**: `http://auth.localhost`
- **User Profile Service**: `http://user-profile.localhost`
- **Medical Records Service**: `http://medical-records.localhost`
- **Medical Analysis Service**: `http://medical-analysis.localhost`

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

---

## 🔬 Health Analysis Service
**Base URL**: `http://health-analysis.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check if the service is healthy
**Response**: Service status and AI model availability

#### 2. Supported Medical Conditions
```http
GET /api/v1/health-analysis/supported-conditions
```
**Description**: Get all supported medical condition categories and conditions
**Response**: Array of 18 categories with 470 total conditions
**Example Response**:
```json
[
  {
    "type": "skin",
    "conditions": ["rash", "burn", "dermatitis", "eczema", ...]
  },
  {
    "type": "injury", 
    "conditions": ["cut", "wound", "bruise", "fracture", ...]
  }
  // ... 16 more categories
]
```

#### 3. Analyze Health Image
```http
POST /api/v1/health-analysis/analyze
```
**Description**: Analyze medical images for conditions
**Content-Type**: `multipart/form-data`
**Body**:
- `image`: Image file (JPEG, PNG, WebP, HEIC)
- `description` (optional): Text description of symptoms
**Response**: Medical analysis with conditions, severity, and recommendations

#### 4. Detect Specific Condition
```http
POST /api/v1/health-analysis/detect-condition
```
**Description**: Detect specific medical conditions from image
**Content-Type**: `multipart/form-data`
**Body**:
- `image`: Image file
- `condition_type`: Category to focus on (e.g., "skin", "injury")
**Response**: Condition detection with confidence scores

#### 5. Medical Query
```http
POST /api/v1/health-analysis/medical-query
```
**Description**: Ask medical questions and get AI-powered responses
**Content-Type**: `application/json`
**Body**:
```json
{
  "query": "What are the symptoms of diabetes?",
  "context": "Patient has family history"
}
```

### Emergency Triage Endpoints

#### 6. Emergency Assessment
```http
POST /api/v1/emergency-triage/assess-emergency
```
**Description**: Assess if symptoms require emergency care
**Content-Type**: `application/json`
**Body**:
```json
{
  "symptoms": ["chest pain", "shortness of breath"],
  "severity": "high"
}
```

#### 7. Emergency Alert
```http
POST /api/v1/emergency-triage/emergency-alert
```
**Description**: Send emergency alert with location
**Content-Type**: `application/json`
**Body**:
```json
{
  "emergency_type": "cardiac",
  "location": "123 Main St, City",
  "contact": "+1234567890"
}
```

#### 8. Emergency Contacts
```http
GET /api/v1/emergency-triage/emergency-contacts
```
**Description**: Get user's emergency contacts

#### 9. Nearest Emergency Facilities
```http
GET /api/v1/emergency-triage/nearest-emergency-facilities
```
**Query Parameters**:
- `latitude`: User's latitude
- `longitude`: User's longitude
- `radius`: Search radius in km (default: 10)

### Medical Insights Endpoints

#### 10. Analyze Symptoms
```http
POST /api/v1/medical-insights/analyze-symptoms
```
**Description**: Analyze symptoms and provide insights
**Content-Type**: `application/json`
**Body**:
```json
{
  "symptoms": ["fever", "cough", "fatigue"],
  "duration": "3 days",
  "severity": "moderate"
}
```

#### 11. Drug Interactions
```http
POST /api/v1/medical-insights/drug-interactions
```
**Description**: Check for drug interactions
**Content-Type**: `application/json`
**Body**:
```json
{
  "medications": ["aspirin", "ibuprofen"],
  "new_medication": "warfarin"
}
```

#### 12. Treatment Recommendations
```http
POST /api/v1/medical-insights/treatment-recommendations
```
**Description**: Get treatment recommendations for conditions
**Content-Type**: `application/json`
**Body**:
```json
{
  "condition": "hypertension",
  "severity": "mild",
  "patient_age": 45
}
```

---

## 📊 Health Tracking Service
**Base URL**: `http://health-tracking.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check service health

#### 2. Track Health Data
```http
POST /api/v1/health-tracking/track
```
**Description**: Track health metrics
**Content-Type**: `application/json`
**Body**:
```json
{
  "user_id": "user123",
  "metric_type": "heart_rate",
  "value": 75,
  "timestamp": "2025-07-20T10:00:00Z",
  "unit": "bpm"
}
```

#### 3. Get Health History
```http
GET /api/v1/health-tracking/history
```
**Query Parameters**:
- `user_id`: User identifier
- `metric_type`: Type of metric (heart_rate, blood_pressure, etc.)
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)

#### 4. Health Analytics
```http
GET /api/v1/health-tracking/analytics
```
**Query Parameters**:
- `user_id`: User identifier
- `metric_type`: Type of metric
- `period`: Time period (day, week, month, year)

#### 5. Health Insights
```http
GET /api/v1/health-tracking/insights
```
**Query Parameters**:
- `user_id`: User identifier
- `insight_type`: Type of insight (trends, anomalies, recommendations)

---

## 🍎 Nutrition Service
**Base URL**: `http://nutrition.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check service health

#### 2. Analyze Food Image
```http
POST /api/v1/nutrition/analyze-food
```
**Description**: Analyze food from image
**Content-Type**: `multipart/form-data`
**Body**:
- `image`: Food image
- `meal_type` (optional): breakfast, lunch, dinner, snack

#### 3. Get Nutrition Info
```http
GET /api/v1/nutrition/food-info
```
**Query Parameters**:
- `food_name`: Name of the food
- `quantity`: Amount (optional)
- `unit`: Unit of measurement (optional)

#### 4. Calculate Nutrition
```http
POST /api/v1/nutrition/calculate
```
**Description**: Calculate nutrition for meal
**Content-Type**: `application/json`
**Body**:
```json
{
  "foods": [
    {"name": "apple", "quantity": 1, "unit": "medium"},
    {"name": "chicken breast", "quantity": 100, "unit": "grams"}
  ]
}
```

#### 5. Nutrition Recommendations
```http
GET /api/v1/nutrition/recommendations
```
**Query Parameters**:
- `user_id`: User identifier
- `goal`: Nutrition goal (weight_loss, muscle_gain, maintenance)
- `dietary_restrictions`: Array of restrictions (vegetarian, gluten_free, etc.)

---

## 🔐 Authentication Service
**Base URL**: `http://auth.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check service health

#### 2. User Registration
```http
POST /auth/register
```
**Description**: Register new user
**Content-Type**: `application/json`
**Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### 3. User Login
```http
POST /auth/login
```
**Description**: Login user
**Content-Type**: `application/json`
**Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### 4. Get Current User
```http
GET /auth/me
```
**Description**: Get current user information
**Headers**: `Authorization: Bearer <token>`

#### 5. Refresh Token
```http
POST /auth/refresh
```
**Description**: Refresh access token
**Content-Type**: `application/json`
**Body**:
```json
{
  "refresh_token": "your_refresh_token"
}
```

#### 6. Logout
```http
POST /auth/logout
```
**Description**: Logout user
**Headers**: `Authorization: Bearer <token>`

---

## 👤 User Profile Service
**Base URL**: `http://user-profile.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check service health

#### 2. Get User Profile
```http
GET /api/v1/user-profile/profile
```
**Description**: Get user profile
**Headers**: `Authorization: Bearer <token>`

#### 3. Update User Profile
```http
PUT /api/v1/user-profile/profile
```
**Description**: Update user profile
**Headers**: `Authorization: Bearer <token>`
**Content-Type**: `application/json`
**Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "height": 175,
  "weight": 70,
  "medical_history": ["diabetes", "hypertension"]
}
```

#### 4. Get Health Goals
```http
GET /api/v1/user-profile/health-goals
```
**Description**: Get user's health goals
**Headers**: `Authorization: Bearer <token>`

#### 5. Set Health Goals
```http
POST /api/v1/user-profile/health-goals
```
**Description**: Set health goals
**Headers**: `Authorization: Bearer <token>`
**Content-Type**: `application/json`
**Body**:
```json
{
  "weight_goal": 65,
  "fitness_goal": "run_5k",
  "nutrition_goal": "balanced_diet"
}
```

---

## 📋 Medical Records Service
**Base URL**: `http://medical-records.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check service health

#### 2. Get Medical Records
```http
GET /api/v1/medical-records/records
```
**Description**: Get user's medical records
**Headers**: `Authorization: Bearer <token>`

#### 3. Add Medical Record
```http
POST /api/v1/medical-records/records
```
**Description**: Add new medical record
**Headers**: `Authorization: Bearer <token>`
**Content-Type**: `application/json`
**Body**:
```json
{
  "record_type": "diagnosis",
  "condition": "hypertension",
  "date": "2025-07-20",
  "doctor": "Dr. Smith",
  "notes": "Patient diagnosed with mild hypertension"
}
```

#### 4. Update Medical Record
```http
PUT /api/v1/medical-records/records/{record_id}
```
**Description**: Update medical record
**Headers**: `Authorization: Bearer <token>`

#### 5. Delete Medical Record
```http
DELETE /api/v1/medical-records/records/{record_id}
```
**Description**: Delete medical record
**Headers**: `Authorization: Bearer <token>`

---

## 🔬 Medical Analysis Service
**Base URL**: `http://medical-analysis.localhost`

### Core Endpoints

#### 1. Health Check
```http
GET /health
```
**Description**: Check service health

#### 2. Analyze Medical Data
```http
POST /api/v1/medical-analysis/analyze
```
**Description**: Analyze medical data
**Content-Type**: `application/json`
**Body**:
```json
{
  "data_type": "lab_results",
  "data": {
    "glucose": 120,
    "cholesterol": 200,
    "blood_pressure": "140/90"
  }
}
```

#### 3. Get Analysis History
```http
GET /api/v1/medical-analysis/history
```
**Description**: Get analysis history
**Headers**: `Authorization: Bearer <token>`

---

## 🚀 React Frontend Integration Examples

### Example: Health Analysis with Image Upload
```javascript
// Upload and analyze health image
const analyzeHealthImage = async (imageFile, description = '') => {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (description) {
    formData.append('description', description);
  }

  const response = await fetch('http://health-analysis.localhost/api/v1/health-analysis/analyze', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData
  });

  return await response.json();
};
```

### Example: Get Supported Conditions
```javascript
// Get all supported medical conditions
const getSupportedConditions = async () => {
  const response = await fetch('http://health-analysis.localhost/api/v1/health-analysis/supported-conditions', {
    headers: {
      'Authorization': `Bearer ${token}`,
    }
  });

  return await response.json();
};
```

### Example: Track Health Data
```javascript
// Track health metrics
const trackHealthData = async (metricType, value, unit) => {
  const response = await fetch('http://health-tracking.localhost/api/v1/health-tracking/track', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      metric_type: metricType,
      value: value,
      unit: unit,
      timestamp: new Date().toISOString()
    })
  });

  return await response.json();
};
```

### Example: User Authentication
```javascript
// Login user
const loginUser = async (email, password) => {
  const response = await fetch('http://auth.localhost/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();
  if (data.access_token) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }

  return data;
};
```

---

## 📝 Notes for Frontend Development

1. **CORS**: All services support CORS for localhost development
2. **Authentication**: Use JWT tokens for protected endpoints
3. **Error Handling**: All endpoints return consistent error formats
4. **File Uploads**: Use FormData for image uploads
5. **Pagination**: Some endpoints support pagination with `page` and `limit` parameters
6. **Rate Limiting**: Be aware of rate limits on API calls
7. **Health Checks**: Always check service health before making requests

## 🔧 Development Setup

For local development, you can use these URLs:
- Health Analysis: `http://localhost:8008`
- Health Tracking: `http://localhost:8002`
- Nutrition: `http://localhost:8007`
- Auth: `http://localhost:8000`
- User Profile: `http://localhost:8001`
- Medical Records: `http://localhost:8005`
- Medical Analysis: `http://localhost:8006`

Or use the Traefik routes with `.localhost` domains for automatic routing. 