# Personal Health Assistant - Backend API Specification

## Overview
This document provides comprehensive API specifications for all microservices in the Personal Health Assistant platform. Each service is documented with its endpoints, authentication requirements, request/response formats, and integration details.

## Table of Contents
1. [Authentication Service](#authentication-service)
2. [User Profile Service](#user-profile-service)
3. [Health Tracking Service](#health-tracking-service)
4. [Medical Analysis Service](#medical-analysis-service)
5. [Voice Input Service](#voice-input-service)
6. [Device Data Service](#device-data-service)
7. [Medical Records Service](#medical-records-service)
8. [AI Insights Service](#ai-insights-service)
9. [Nutrition Service](#nutrition-service)
10. [Traefik Gateway Configuration](#traefik-gateway-configuration)
11. [Error Handling](#error-handling)
12. [Rate Limiting](#rate-limiting)
13. [WebSocket Endpoints](#websocket-endpoints)

---

## Authentication Service
**Base URL**: `http://localhost:8000`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Authentication Endpoints

#### 1. User Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-01",
  "phone": "+1234567890"
}
```

**Response**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 2. User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "user_id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    }
  }
}
```

#### 3. Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

#### 4. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

#### 5. Verify Token
```http
GET /api/v1/auth/verify
Authorization: Bearer <access_token>
```

---

## User Profile Service
**Base URL**: `http://localhost:8001`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Profile Endpoints

#### 1. Get User Profile
```http
GET /api/v1/profile/{user_id}
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "phone": "+1234567890",
    "emergency_contact": {
      "name": "Jane Doe",
      "phone": "+1234567891",
      "relationship": "Spouse"
    },
    "preferences": {
      "notifications": true,
      "privacy_level": "standard",
      "language": "en"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 2. Update User Profile
```http
PUT /api/v1/profile/{user_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "emergency_contact": {
    "name": "Jane Doe",
    "phone": "+1234567891",
    "relationship": "Spouse"
  },
  "preferences": {
    "notifications": true,
    "privacy_level": "standard",
    "language": "en"
  }
}
```

#### 3. Update Preferences
```http
PATCH /api/v1/profile/{user_id}/preferences
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "notifications": true,
  "privacy_level": "enhanced",
  "language": "en"
}
```

---

## Health Tracking Service
**Base URL**: `http://localhost:8002`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Health Data Endpoints

#### 1. Submit Health Data
```http
POST /api/v1/health/data
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "data_type": "heart_rate",
  "value": 75,
  "unit": "bpm",
  "timestamp": "2024-01-01T12:00:00Z",
  "source": "apple_watch",
  "metadata": {
    "location": "home",
    "activity": "resting"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Health data recorded successfully",
  "data": {
    "data_id": "uuid",
    "user_id": "uuid",
    "data_type": "heart_rate",
    "value": 75,
    "unit": "bpm",
    "timestamp": "2024-01-01T12:00:00Z",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 2. Get Health Data
```http
GET /api/v1/health/data/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - data_type: heart_rate, blood_pressure, steps, sleep, etc.
  - start_date: 2024-01-01
  - end_date: 2024-01-31
  - limit: 100
  - offset: 0
```

#### 3. Get Health Analytics
```http
GET /api/v1/health/analytics/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - period: daily, weekly, monthly
  - data_type: heart_rate, blood_pressure, steps, sleep
```

**Response**:
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "period": "daily",
    "data_type": "heart_rate",
    "analytics": {
      "average": 72.5,
      "min": 65,
      "max": 85,
      "trend": "stable",
      "recommendations": [
        "Your heart rate is within normal range",
        "Consider increasing physical activity"
      ]
    },
    "data_points": [
      {
        "timestamp": "2024-01-01T00:00:00Z",
        "value": 75,
        "unit": "bpm"
      }
    ]
  }
}
```

#### 4. Get Health Alerts
```http
GET /api/v1/health/alerts/{user_id}
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "alert_id": "uuid",
        "type": "high_heart_rate",
        "severity": "medium",
        "message": "Heart rate elevated above normal range",
        "timestamp": "2024-01-01T12:00:00Z",
        "status": "active",
        "recommendations": [
          "Take deep breaths",
          "Consider consulting a doctor if symptoms persist"
        ]
      }
    ]
  }
}
```

---

## Medical Analysis Service
**Base URL**: `http://localhost:8006`  
**Health Check**: `GET /ready`  
**Service Status**: ✅ Running

### Medical Analysis Endpoints

#### 1. Analyze Health Data
```http
POST /api/v1/medical/analyze
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "analysis_type": "health_trends",
  "data": {
    "heart_rate_data": [...],
    "blood_pressure_data": [...],
    "sleep_data": [...]
  },
  "timeframe": "30_days"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "analysis_id": "uuid",
    "user_id": "uuid",
    "analysis_type": "health_trends",
    "results": {
      "overall_health_score": 85,
      "trends": {
        "heart_rate": "improving",
        "blood_pressure": "stable",
        "sleep_quality": "declining"
      },
      "insights": [
        "Your heart rate has improved by 10% over the last month",
        "Sleep quality has decreased, consider improving sleep hygiene"
      ],
      "recommendations": [
        "Continue current exercise routine",
        "Aim for 7-9 hours of sleep per night",
        "Consider stress management techniques"
      ]
    },
    "confidence_score": 0.92,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 2. Get Analysis History
```http
GET /api/v1/medical/analysis/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - analysis_type: health_trends, risk_assessment, etc.
  - limit: 10
  - offset: 0
```

#### 3. Risk Assessment
```http
POST /api/v1/medical/risk-assessment
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "health_data": {
    "age": 35,
    "bmi": 24.5,
    "family_history": ["diabetes", "heart_disease"],
    "lifestyle_factors": {
      "smoking": false,
      "exercise_frequency": "3_times_week",
      "diet": "balanced"
    }
  }
}
```

---

## Voice Input Service
**Base URL**: `http://localhost:8003`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Voice Processing Endpoints

#### 1. Voice Input Processing
```http
POST /api/v1/voice-input/voice-input
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "audio_file": <file>,
  "user_id": "uuid",
  "language": "en",
  "context": "health_symptom"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "request_id": "uuid",
    "transcription": "I've been feeling tired and have a headache",
    "confidence": 0.95,
    "intent": "symptom_report",
    "entities": {
      "symptoms": ["tired", "headache"],
      "duration": "recent",
      "severity": "mild"
    },
    "processing_time": 2.3,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 2. Text-to-Speech
```http
POST /api/v1/voice-input/text-to-speech
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "text": "Your health data has been analyzed successfully",
  "voice": "en-US-Neural2-F",
  "speed": 1.0,
  "pitch": 0.0
}
```

**Response**: Audio file (MP3/WAV)

#### 3. Intent Recognition
```http
POST /api/v1/voice-input/intent
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "text": "I want to check my heart rate",
  "user_id": "uuid",
  "context": "health_query"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "intent": "check_health_data",
    "confidence": 0.98,
    "entities": {
      "health_metric": "heart_rate",
      "timeframe": "current"
    },
    "suggested_action": "fetch_heart_rate_data"
  }
}
```

#### 4. Multi-modal Processing
```http
POST /api/v1/voice-input/multi-modal
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "audio_file": <file>,
  "image_file": <file>,
  "text": "This is what I'm experiencing",
  "user_id": "uuid"
}
```

---

## Device Data Service
**Base URL**: `http://localhost:8004`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Device Integration Endpoints

#### 1. Connect Device
```http
POST /api/v1/device/connect
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "device_type": "apple_watch",
  "device_id": "device_uuid",
  "connection_data": {
    "auth_token": "device_auth_token",
    "sync_frequency": "hourly"
  }
}
```

#### 2. Sync Device Data
```http
POST /api/v1/device/sync/{device_id}
Authorization: Bearer <access_token>
```

#### 3. Get Connected Devices
```http
GET /api/v1/device/connected/{user_id}
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "device_id": "uuid",
        "device_type": "apple_watch",
        "device_name": "John's Apple Watch",
        "connected_at": "2024-01-01T00:00:00Z",
        "last_sync": "2024-01-01T12:00:00Z",
        "status": "connected",
        "capabilities": ["heart_rate", "steps", "sleep", "activity"]
      }
    ]
  }
}
```

#### 4. Disconnect Device
```http
DELETE /api/v1/device/disconnect/{device_id}
Authorization: Bearer <access_token>
```

---

## Medical Records Service
**Base URL**: `http://localhost:8005`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Medical Records Endpoints

#### 1. Upload Medical Document
```http
POST /api/v1/medical-records/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "document_file": <file>,
  "document_type": "lab_report",
  "user_id": "uuid",
  "metadata": {
    "date": "2024-01-01",
    "provider": "City Hospital",
    "description": "Blood test results"
  }
}
```

#### 2. Get Medical Records
```http
GET /api/v1/medical-records/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - document_type: lab_report, prescription, imaging, etc.
  - start_date: 2024-01-01
  - end_date: 2024-12-31
  - limit: 20
  - offset: 0
```

#### 3. Process Medical Document
```http
POST /api/v1/medical-records/process/{document_id}
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "extracted_data": {
      "test_results": {
        "glucose": "95 mg/dL",
        "cholesterol": "180 mg/dL",
        "blood_pressure": "120/80 mmHg"
      },
      "normal_ranges": {
        "glucose": "70-100 mg/dL",
        "cholesterol": "<200 mg/dL"
      },
      "interpretation": "All values within normal range"
    },
    "processing_status": "completed",
    "confidence_score": 0.94
  }
}
```

---

## AI Insights Service
**Base URL**: `http://localhost:8200`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### AI Insights Endpoints

#### 1. Generate Health Insights
```http
POST /api/v1/ai-insights/insights
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "insight_type": "health_patterns",
  "data_sources": ["health_tracking", "medical_records", "device_data"],
  "timeframe": "30_days"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "insight_id": "uuid",
    "user_id": "uuid",
    "insight_type": "health_patterns",
    "insights": [
      {
        "title": "Sleep Quality Impact",
        "description": "Your heart rate is 15% higher on days with less than 6 hours of sleep",
        "confidence": 0.89,
        "recommendations": [
          "Aim for 7-9 hours of sleep per night",
          "Maintain consistent sleep schedule"
        ]
      }
    ],
    "generated_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 2. Get Health Recommendations
```http
GET /api/v1/ai-insights/recommendations/{user_id}
Authorization: Bearer <access_token>
```

#### 3. Calculate Health Score
```http
POST /api/v1/ai-insights/health-scores
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "score_type": "overall_health",
  "factors": ["physical", "mental", "lifestyle"]
}
```

---

## Nutrition Service
**Base URL**: `http://localhost:8007`  
**Health Check**: `GET /health`  
**Service Status**: ✅ Running

### Nutrition Endpoints

#### 1. Analyze Meal
```http
POST /api/v1/nutrition/analyze-meal
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "food_items": [
    {
      "name": "grilled chicken breast",
      "portion": "150g",
      "quantity": 1
    },
    {
      "name": "brown rice",
      "portion": "100g",
      "quantity": 1
    }
  ],
  "meal_type": "lunch",
  "meal_name": "Healthy Lunch",
  "meal_description": "Grilled chicken with brown rice",
  "user_notes": "Felt good after this meal",
  "mood_before": "hungry",
  "mood_after": "satisfied"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "food_items": [
      {
        "name": "grilled chicken breast",
        "portion": "150g",
        "calories": 165,
        "protein": 31,
        "carbs": 0,
        "fat": 3.6,
        "fiber": 0,
        "sugar": 0
      }
    ],
    "totals": {
      "calories": 365,
      "protein": 31,
      "carbs": 23,
      "fat": 3.6,
      "fiber": 1.8,
      "sugar": 0.4
    },
    "recommendations": [
      "Good protein content for muscle maintenance",
      "Consider adding more vegetables for fiber"
    ],
    "user_preferences_used": true
  }
}
```

#### 2. Log Meal
```http
POST /api/v1/nutrition/log-meal
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "food_items": [
    {
      "name": "salmon fillet",
      "portion": "200g",
      "quantity": 1
    }
  ],
  "meal_type": "dinner",
  "meal_name": "Salmon Dinner"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "meal_log_id": "uuid",
    "food_items": [...],
    "totals": {...},
    "recommendations": [...],
    "logged_at": "2024-01-01T18:00:00Z"
  }
}
```

#### 3. Get Daily Nutrition
```http
GET /api/v1/nutrition/daily-nutrition/2024-01-01
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "date": "2024-01-01",
    "meals": [
      {
        "meal_id": "uuid",
        "meal_type": "breakfast",
        "meal_name": "Oatmeal Bowl",
        "food_items": [...],
        "totals": {...}
      }
    ],
    "daily_totals": {
      "calories": 1850,
      "protein": 120,
      "carbs": 180,
      "fat": 65,
      "fiber": 25,
      "sugar": 45
    },
    "goals_progress": {
      "calories": 0.85,
      "protein": 1.2,
      "carbs": 0.9,
      "fat": 0.8
    }
  }
}
```

#### 4. Get Nutrition History
```http
GET /api/v1/nutrition/nutrition-history?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <access_token>
```

#### 5. Get Personalized Recommendations
```http
GET /api/v1/nutrition/personalized-recommendations
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "type": "meal_suggestion",
        "title": "High Protein Breakfast",
        "description": "Consider adding Greek yogurt to your breakfast for extra protein",
        "priority": "high",
        "reasoning": "Your protein intake has been below target for 3 days"
      }
    ],
    "based_on": {
      "user_preferences": true,
      "health_goals": true,
      "recent_intake": true
    }
  }
}
```

#### 6. Get Nutrition Summary
```http
GET /api/v1/nutrition/nutrition-summary?days=7
Authorization: Bearer <access_token>
```

#### 7. Calculate Nutrition
```http
POST /api/v1/nutrition/calculate-nutrition
Authorization: Bearer <access_token>
Content-Type: application/json

[
  {
    "name": "banana",
    "portion": "1 medium",
    "quantity": 1
  }
]
```

#### 8. Get Nutritional Trends
```http
GET /api/v1/nutrition/nutritional-trends/protein?period=7_days
Authorization: Bearer <access_token>
```

#### 9. Get Nutritional Insights
```http
GET /api/v1/nutrition/nutritional-insights?timeframe=week
Authorization: Bearer <access_token>
```

#### 10. Delete Meal
```http
DELETE /api/v1/nutrition/meals/{meal_id}
Authorization: Bearer <access_token>
```

#### 11. Create Food Item
```http
POST /api/v1/nutrition/food-items
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "custom smoothie",
  "calories": 250,
  "protein": 15,
  "carbs": 30,
  "fat": 8,
  "fiber": 5,
  "sugar": 20,
  "category": "beverages"
}
```

#### 12. Get Food Item
```http
GET /api/v1/nutrition/food-items/{food_id}
Authorization: Bearer <access_token>
```

#### 13. Search Foods
```http
GET /api/v1/nutrition/search-foods?query=chicken&category=protein&limit=10
Authorization: Bearer <access_token>
```

### Nutrition Recommendations Endpoints

#### 1. Get Personalized Recommendations
```http
GET /api/v1/nutrition/recommendations/personalized/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - goal_id: Optional goal identifier
  - limit: Maximum number of recommendations (default: 10)
```

#### 2. Create Meal Plan
```http
POST /api/v1/nutrition/recommendations/meal-plan
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Weekly Meal Plan",
  "start_date": "2024-01-01",
  "end_date": "2024-01-07",
  "dietary_restrictions": ["vegetarian"],
  "calorie_target": 2000,
  "preferences": {
    "cuisine_types": ["mediterranean", "asian"],
    "cooking_time": "30_minutes",
    "meal_prep": true
  }
}
```

#### 3. Get Meal Plan
```http
GET /api/v1/nutrition/recommendations/meal-plan/{plan_id}
Authorization: Bearer <access_token>
```

#### 4. Get User Meal Plans
```http
GET /api/v1/nutrition/recommendations/meal-plans/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - limit: Maximum number of results (default: 20)
  - offset: Number of results to skip (default: 0)
```

#### 5. Get Meal Suggestion
```http
POST /api/v1/nutrition/recommendations/meal-suggestion
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "meal_type": "dinner",
  "user_id": "uuid",
  "dietary_restrictions": ["gluten_free", "dairy_free"]
}
```

#### 6. Generate Shopping List
```http
POST /api/v1/nutrition/recommendations/shopping-list
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "meal_plan_id": "uuid"
}
```

#### 7. Get Dietary Restrictions
```http
GET /api/v1/nutrition/recommendations/dietary-restrictions/{user_id}
Authorization: Bearer <access_token>
```

#### 8. Update Dietary Restrictions
```http
PUT /api/v1/nutrition/recommendations/dietary-restrictions/{user_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts", "shellfish"],
  "preferences": {
    "spice_level": "medium",
    "cuisine_preferences": ["mediterranean", "asian"]
  }
}
```

### Nutrition Goals Endpoints

#### 1. Create Nutrition Goal
```http
POST /api/v1/nutrition/goals/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "goal_type": "weight_loss",
  "target_value": 70.0,
  "current_value": 75.0,
  "unit": "kg",
  "target_date": "2024-06-01",
  "description": "Lose 5kg by summer",
  "priority": "high"
}
```

#### 2. Get Nutrition Goal
```http
GET /api/v1/nutrition/goals/{goal_id}
Authorization: Bearer <access_token>
```

#### 3. Get User Goals
```http
GET /api/v1/nutrition/goals/user/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - status_filter: active, completed, paused
  - goal_type: weight_loss, muscle_gain, maintenance
```

#### 4. Update Nutrition Goal
```http
PUT /api/v1/nutrition/goals/{goal_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "target_value": 68.0,
  "description": "Updated goal description"
}
```

#### 5. Delete Nutrition Goal
```http
DELETE /api/v1/nutrition/goals/{goal_id}
Authorization: Bearer <access_token>
```

#### 6. Log Goal Progress
```http
POST /api/v1/nutrition/goals/progress
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "goal_id": "uuid",
  "current_value": 73.5,
  "date": "2024-01-15",
  "notes": "Good progress this week"
}
```

#### 7. Get Goal Progress
```http
GET /api/v1/nutrition/goals/progress/{goal_id}
Authorization: Bearer <access_token>
Query Parameters:
  - start_date: Start date for progress history
  - end_date: End date for progress history
```

#### 8. Get Goal Summary
```http
GET /api/v1/nutrition/goals/summary/{goal_id}
Authorization: Bearer <access_token>
```

#### 9. Get Goal Recommendations
```http
GET /api/v1/nutrition/goals/recommendations/{goal_id}
Authorization: Bearer <access_token>
Query Parameters:
  - limit: Maximum number of recommendations (default: 10)
```

#### 10. Calculate Nutrition Targets
```http
POST /api/v1/nutrition/goals/calculate-targets
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "age": 30,
  "gender": "female",
  "height": 165,
  "current_weight": 70,
  "activity_level": "moderate",
  "goal_type": "weight_loss"
}
```

### Food Recognition Endpoints

#### 1. Recognize Food from Image
```http
POST /api/v1/nutrition/food-recognition/recognize
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "image": <file>,
  "user_id": "uuid",
  "meal_type": "lunch",
  "cuisine_hint": "mediterranean",
  "dietary_restrictions": "vegetarian,gluten_free",
  "preferred_units": "metric",
  "enable_portion_estimation": true,
  "enable_nutrition_lookup": true
}
```

**Response**:
```json
{
  "recognition_id": "uuid",
  "recognized_foods": [
    {
      "name": "grilled salmon",
      "confidence": 0.95,
      "portion_estimate": "150g",
      "nutrition_data": {
        "calories": 280,
        "protein": 34,
        "carbs": 0,
        "fat": 15
      },
      "alternatives": [
        {
          "name": "baked salmon",
          "confidence": 0.85
        }
      ]
    }
  ],
  "processing_time": 2.3,
  "model_used": "google_vision"
}
```

#### 2. Batch Food Recognition
```http
POST /api/v1/nutrition/food-recognition/recognize-batch
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "images": [
    {
      "image_data": "base64_encoded_image",
      "image_format": "jpeg",
      "meal_type": "breakfast"
    }
  ],
  "batch_settings": {
    "enable_portion_estimation": true,
    "enable_nutrition_lookup": true
  }
}
```

#### 3. Correct Food Recognition
```http
POST /api/v1/nutrition/food-recognition/correct-recognition
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "recognition_id": "uuid",
  "corrections": {
    "food_name": "baked salmon instead of grilled",
    "portion_size": "200g instead of 150g"
  }
}
```

#### 4. Get Recognition History
```http
GET /api/v1/nutrition/food-recognition/recognition-history/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - limit: Maximum number of results (default: 20)
  - offset: Number of results to skip (default: 0)
```

#### 5. Get Recognition Statistics
```http
GET /api/v1/nutrition/food-recognition/recognition-stats/{user_id}
Authorization: Bearer <access_token>
Query Parameters:
  - timeframe: Time period for statistics (default: 30_days)
```

#### 6. Estimate Portion Size
```http
POST /api/v1/nutrition/food-recognition/estimate-portion
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "food_name": "apple",
  "image": <file>,
  "reference_object": "hand"
}
```

#### 7. Get Supported Models
```http
GET /api/v1/nutrition/food-recognition/supported-models
Authorization: Bearer <access_token>
```

#### 8. Get Model Performance
```http
GET /api/v1/nutrition/food-recognition/model-performance
Authorization: Bearer <access_token>
```

---

## Traefik Gateway Configuration

### Service URLs (via Traefik)
All services are accessible through Traefik with the following hostnames:

- **Auth Service**: `http://auth.localhost`
- **User Profile**: `http://user-profile.localhost`
- **Health Tracking**: `http://health-tracking.localhost`
- **Medical Analysis**: `http://medical-analysis.localhost`
- **Voice Input**: `http://voice-input.localhost`
- **Device Data**: `http://device-data.localhost`
- **Medical Records**: `http://medical-records.localhost`
- **AI Insights**: `http://ai-insights.localhost`
- **Nutrition**: `http://nutrition.localhost`

### Direct Port Access
- Auth Service: `http://localhost:8000`
- User Profile: `http://localhost:8001`
- Health Tracking: `http://localhost:8002`
- Voice Input: `http://localhost:8003`
- Device Data: `http://localhost:8004`
- Medical Records: `http://localhost:8005`
- Medical Analysis: `http://localhost:8006`
- AI Insights: `http://localhost:8200`
- Nutrition: `http://localhost:8007`

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid"
}
```

### Common Error Codes
- `AUTHENTICATION_ERROR`: Invalid or expired token
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid request data
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Server error

---

## Rate Limiting

### Default Limits
- **Authentication endpoints**: 10 requests/minute
- **Data submission**: 100 requests/minute
- **Data retrieval**: 1000 requests/minute
- **File uploads**: 10 requests/minute

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## WebSocket Endpoints

### Real-time Health Data
```javascript
// Connect to real-time health data stream
const ws = new WebSocket('ws://localhost:8002/ws/health-data/{user_id}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time health data:', data);
};
```

### Voice Processing Stream
```javascript
// Connect to voice processing stream
const ws = new WebSocket('ws://localhost:8003/ws/voice-processing/{user_id}');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Voice processing update:', data);
};
```

---

## Frontend Integration Guide

### 1. Authentication Flow
```javascript
// 1. Register user
const registerResponse = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(registerData)
});

// 2. Login user
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(loginData)
});

const { access_token } = await loginResponse.json();

// 3. Use token for authenticated requests
const profileResponse = await fetch('http://localhost:8001/api/v1/profile/{user_id}', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### 2. Health Data Submission
```javascript
// Submit health data
const healthData = {
  user_id: 'user_uuid',
  data_type: 'heart_rate',
  value: 75,
  unit: 'bpm',
  timestamp: new Date().toISOString(),
  source: 'manual_entry'
};

const response = await fetch('http://localhost:8002/api/v1/health/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify(healthData)
});
```

### 3. Voice Input Processing
```javascript
// Process voice input
const formData = new FormData();
formData.append('audio_file', audioBlob);
formData.append('user_id', 'user_uuid');
formData.append('language', 'en');

const response = await fetch('http://localhost:8003/api/v1/voice-input/voice-input', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
});
```

### 4. Nutrition Data Management
```javascript
// Analyze and log a meal
const mealData = {
  food_items: [
    {
      name: "grilled chicken breast",
      portion: "150g",
      quantity: 1
    },
    {
      name: "brown rice",
      portion: "100g",
      quantity: 1
    }
  ],
  meal_type: "lunch",
  meal_name: "Healthy Lunch",
  user_notes: "Felt good after this meal"
};

const response = await fetch('http://localhost:8007/api/v1/nutrition/log-meal', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify(mealData)
});

// Get daily nutrition summary
const dailyResponse = await fetch('http://localhost:8007/api/v1/nutrition/daily-nutrition/2024-01-01', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

// Get personalized recommendations
const recommendationsResponse = await fetch('http://localhost:8007/api/v1/nutrition/personalized-recommendations', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### 5. Food Recognition
```javascript
// Recognize food from image
const formData = new FormData();
formData.append('image', imageFile);
formData.append('user_id', 'user_uuid');
formData.append('meal_type', 'lunch');
formData.append('dietary_restrictions', 'vegetarian,gluten_free');

const recognitionResponse = await fetch('http://localhost:8007/api/v1/nutrition/food-recognition/recognize', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
});
```

### 6. Error Handling
```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
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

---

## Testing Endpoints

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health  # Auth
curl http://localhost:8001/health  # User Profile
curl http://localhost:8002/health  # Health Tracking
curl http://localhost:8003/health  # Voice Input
curl http://localhost:8004/health  # Device Data
curl http://localhost:8005/health  # Medical Records
curl http://localhost:8006/ready   # Medical Analysis
curl http://localhost:8007/health  # Nutrition
curl http://localhost:8200/health  # AI Insights
```

### Authentication Test
```bash
# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","first_name":"Test","last_name":"User"}'

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

---

## Security Considerations

### 1. Authentication
- All endpoints require valid JWT tokens (except public endpoints)
- Tokens expire after 1 hour
- Refresh tokens valid for 7 days

### 2. Data Privacy
- All health data is encrypted at rest
- API communications use HTTPS in production
- User data is anonymized for analytics

### 3. Rate Limiting
- Implemented to prevent abuse
- Different limits for different endpoint types
- IP-based and user-based limiting

### 4. Input Validation
- All inputs are validated and sanitized
- File uploads are scanned for malware
- SQL injection protection implemented

---

## Monitoring and Logging

### Health Monitoring
- All services expose `/health` endpoints
- Prometheus metrics available at `/metrics`
- Grafana dashboards for visualization

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking and alerting

---

This API specification provides all the information needed for frontend integration. Each service is documented with its endpoints, authentication requirements, and example usage patterns. 