# Nutrition Service - Comprehensive Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [API Endpoints](#api-endpoints)
6. [Data Models](#data-models)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Monitoring & Logging](#monitoring--logging)
11. [Troubleshooting](#troubleshooting)

## Overview

The Nutrition Service provides comprehensive nutrition management, meal planning, dietary analysis, and personalized nutrition recommendations for the Personal Health Assistant platform. It helps users track their nutrition, plan healthy meals, and achieve their dietary goals while considering health conditions and preferences.

### Key Responsibilities
- Nutrition tracking and analysis
- Meal planning and recipe management
- Dietary recommendations and goal setting
- Food database and nutritional information
- Integration with health tracking and medical records
- Personalized nutrition coaching
- Dietary compliance monitoring

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │   Nutrition     │
│                 │    │   (Traefik)     │    │   Service       │
│ - Web App       │───▶│                 │───▶│                 │
│ - Mobile App    │    │ - Rate Limiting │    │ - Meal Planning │
│ - Smart Devices │    │ - SSL/TLS       │    │ - Tracking      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │                 │
                                              │ - Nutrition     │
                                              │   Data          │
                                              │ - Meal Plans    │
                                              │ - Recipes       │
                                              │ - Goals         │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │     Redis       │
                                              │                 │
                                              │ - Caching       │
                                              │ - Real-time     │
                                              │   Updates       │
                                              └─────────────────┘
```

### Service Architecture
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL for nutrition data and meal plans
- **Caching**: Redis for real-time updates and caching
- **Food Database**: Comprehensive nutritional database
- **Recipe Management**: Recipe storage and meal planning
- **Integration**: Health tracking, medical records, and AI insights

## Features

### 1. Nutrition Tracking
- **Food Logging**: Track daily food intake and meals
- **Nutrient Analysis**: Analyze macronutrients and micronutrients
- **Calorie Tracking**: Monitor daily calorie intake
- **Portion Control**: Track portion sizes and servings
- **Barcode Scanning**: Scan food barcodes for quick logging
- **Custom Foods**: Add custom foods and recipes

### 2. Meal Planning
- **Meal Plan Creation**: Create personalized meal plans
- **Recipe Management**: Store and manage recipes
- **Shopping Lists**: Generate shopping lists from meal plans
- **Meal Scheduling**: Schedule meals throughout the day
- **Dietary Restrictions**: Accommodate dietary restrictions
- **Nutritional Goals**: Align meals with nutritional goals

### 3. Dietary Recommendations
- **Personalized Recommendations**: AI-powered nutrition advice
- **Goal-Based Planning**: Plan nutrition around health goals
- **Condition-Specific Diets**: Support for medical conditions
- **Allergy Management**: Manage food allergies and intolerances
- **Supplement Recommendations**: Suggest dietary supplements
- **Hydration Tracking**: Monitor water and fluid intake

### 4. Food Database
- **Comprehensive Database**: Extensive food and nutrition database
- **Nutritional Information**: Detailed nutritional profiles
- **Brand Information**: Brand-specific nutritional data
- **Restaurant Menus**: Restaurant menu nutritional information
- **Seasonal Foods**: Seasonal and local food information
- **Organic/Conventional**: Distinguish between food types

### 5. Recipe Management
- **Recipe Storage**: Store personal and favorite recipes
- **Recipe Sharing**: Share recipes with other users
- **Recipe Scaling**: Scale recipes for different serving sizes
- **Nutritional Calculation**: Calculate recipe nutritional content
- **Cooking Instructions**: Step-by-step cooking instructions
- **Recipe Categories**: Organize recipes by categories

### 6. Progress Monitoring
- **Nutritional Goals**: Set and track nutritional goals
- **Progress Reports**: Generate nutrition progress reports
- **Trend Analysis**: Analyze nutrition trends over time
- **Goal Achievement**: Monitor goal achievement progress
- **Compliance Tracking**: Track dietary compliance
- **Performance Metrics**: Nutrition performance metrics

## Technology Stack

### Core Technologies
- **Python 3.11**: Modern Python with async support
- **FastAPI**: High-performance web framework
- **SQLAlchemy 2.0**: Modern ORM with async support
- **PostgreSQL 15**: Primary database
- **Redis 7**: Caching and real-time updates

### Data Analysis & Machine Learning
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning for recommendations
- **Matplotlib/Seaborn**: Data visualization
- **Plotly**: Interactive nutrition charts

### Food Database & APIs
- **USDA Food Database**: Official nutritional database
- **Open Food Facts**: Open-source food database
- **Nutritionix API**: Restaurant nutrition data
- **Edamam API**: Recipe and nutrition API

### Additional Libraries
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **httpx**: Async HTTP client
- **PyYAML**: Configuration management
- **python-dateutil**: Date and time utilities

## API Endpoints

### Nutrition Tracking

#### POST /api/v1/nutrition/log
Log food intake.

**Request Body:**
```json
{
  "user_id": "uuid",
  "meal_type": "breakfast",
  "foods": [
    {
      "food_id": "uuid",
      "quantity": 1.5,
      "unit": "cup",
      "meal_time": "2023-12-01T08:00:00Z"
    }
  ],
  "notes": "Added berries to oatmeal"
}
```

**Response:**
```json
{
  "log_id": "uuid",
  "user_id": "uuid",
  "meal_type": "breakfast",
  "total_calories": 320,
  "macronutrients": {
    "protein": 12.5,
    "carbohydrates": 45.2,
    "fat": 8.1
  },
  "logged_at": "2023-12-01T08:30:00Z"
}
```

#### GET /api/v1/nutrition/logs
Get nutrition logs with filtering.

#### GET /api/v1/nutrition/logs/{log_id}
Get specific nutrition log.

#### PUT /api/v1/nutrition/logs/{log_id}
Update nutrition log.

#### DELETE /api/v1/nutrition/logs/{log_id}
Delete nutrition log.

### Meal Planning

#### POST /api/v1/meals/plans
Create meal plan.

**Request Body:**
```json
{
  "user_id": "uuid",
  "plan_name": "Weekly Healthy Plan",
  "start_date": "2023-12-01",
  "end_date": "2023-12-07",
  "dietary_restrictions": ["gluten_free", "dairy_free"],
  "nutritional_goals": {
    "calories": 2000,
    "protein": 150,
    "carbohydrates": 200,
    "fat": 65
  },
  "meals": [
    {
      "day": "monday",
      "meal_type": "breakfast",
      "recipe_id": "uuid",
      "servings": 1
    }
  ]
}
```

#### GET /api/v1/meals/plans
Get user's meal plans.

#### GET /api/v1/meals/plans/{plan_id}
Get specific meal plan.

#### PUT /api/v1/meals/plans/{plan_id}
Update meal plan.

#### DELETE /api/v1/meals/plans/{plan_id}
Delete meal plan.

### Recipe Management

#### POST /api/v1/recipes
Create new recipe.

**Request Body:**
```json
{
  "user_id": "uuid",
  "name": "Quinoa Buddha Bowl",
  "description": "Healthy vegetarian bowl with quinoa and vegetables",
  "ingredients": [
    {
      "food_id": "uuid",
      "quantity": 1,
      "unit": "cup",
      "notes": "cooked"
    }
  ],
  "instructions": [
    "Cook quinoa according to package instructions",
    "Chop vegetables",
    "Assemble bowl with quinoa base"
  ],
  "prep_time": 15,
  "cook_time": 20,
  "servings": 4,
  "tags": ["vegetarian", "gluten_free", "healthy"]
}
```

#### GET /api/v1/recipes
Get recipes with filtering.

#### GET /api/v1/recipes/{recipe_id}
Get specific recipe.

#### PUT /api/v1/recipes/{recipe_id}
Update recipe.

#### DELETE /api/v1/recipes/{recipe_id}
Delete recipe.

### Food Database

#### GET /api/v1/foods/search
Search food database.

**Query Parameters:**
- `query`: Search term
- `category`: Food category
- `brand`: Brand name
- `limit`: Number of results

#### GET /api/v1/foods/{food_id}
Get food nutritional information.

#### POST /api/v1/foods/custom
Add custom food.

#### GET /api/v1/foods/categories
Get food categories.

### Dietary Recommendations

#### POST /api/v1/recommendations/generate
Generate nutrition recommendations.

**Request Body:**
```json
{
  "user_id": "uuid",
  "goals": ["weight_loss", "muscle_gain"],
  "restrictions": ["gluten_free"],
  "preferences": ["vegetarian"],
  "health_conditions": ["diabetes"]
}
```

#### GET /api/v1/recommendations
Get user recommendations.

#### PUT /api/v1/recommendations/{recommendation_id}
Update recommendation status.

### Progress Tracking

#### GET /api/v1/progress/summary
Get nutrition progress summary.

#### GET /api/v1/progress/trends
Get nutrition trends over time.

#### POST /api/v1/progress/goals
Set nutrition goals.

#### GET /api/v1/progress/goals
Get nutrition goals.

### Shopping Lists

#### POST /api/v1/shopping/generate
Generate shopping list from meal plan.

#### GET /api/v1/shopping/lists
Get shopping lists.

#### PUT /api/v1/shopping/lists/{list_id}
Update shopping list.

### Hydration Tracking

#### POST /api/v1/hydration/log
Log water intake.

#### GET /api/v1/hydration/summary
Get hydration summary.

## Data Models

### Nutrition Log Model
```python
class NutritionLog(Base):
    __tablename__ = "nutrition_logs"
    __table_args__ = {'schema': 'nutrition'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    meal_type = Column(String(50), nullable=False)
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbohydrates = Column(Float)
    total_fat = Column(Float)
    
    notes = Column(Text)
    logged_at = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Food Item Model
```python
class FoodItem(Base):
    __tablename__ = "food_items"
    __table_args__ = {'schema': 'nutrition'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_id = Column(UUID(as_uuid=True), ForeignKey("nutrition_logs.id"), nullable=False)
    
    food_id = Column(UUID(as_uuid=True), ForeignKey("foods.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    
    calories = Column(Float)
    protein = Column(Float)
    carbohydrates = Column(Float)
    fat = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Meal Plan Model
```python
class MealPlan(Base):
    __tablename__ = "meal_plans"
    __table_args__ = {'schema': 'nutrition'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    plan_name = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    dietary_restrictions = Column(JSON, default=list)
    nutritional_goals = Column(JSON, default=dict)
    
    status = Column(String(20), default="active")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Recipe Model
```python
class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = {'schema': 'nutrition'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    instructions = Column(JSON, default=list)
    
    prep_time = Column(Integer)
    cook_time = Column(Integer)
    servings = Column(Integer)
    
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_carbohydrates = Column(Float)
    total_fat = Column(Float)
    
    tags = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Food Database Model
```python
class Food(Base):
    __tablename__ = "foods"
    __table_args__ = {'schema': 'nutrition'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(500), nullable=False)
    brand = Column(String(200))
    category = Column(String(100))
    
    serving_size = Column(Float)
    serving_unit = Column(String(20))
    
    calories_per_serving = Column(Float)
    protein_per_serving = Column(Float)
    carbohydrates_per_serving = Column(Float)
    fat_per_serving = Column(Float)
    
    fiber = Column(Float)
    sugar = Column(Float)
    sodium = Column(Float)
    
    barcode = Column(String(50))
    external_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Configuration

### Environment Variables
```bash
# Service Configuration
SERVICE_NAME=nutrition-service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
REDIS_URL=redis://localhost:6379

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8005
MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002
AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200

# Food Database APIs
USDA_API_KEY=your-usda-api-key
NUTRITIONIX_APP_ID=your-nutritionix-app-id
NUTRITIONIX_APP_KEY=your-nutritionix-app-key
EDAMAM_APP_ID=your-edamam-app-id
EDAMAM_APP_KEY=your-edamam-app-key

# Analysis Configuration
ANALYSIS_WORKERS=4
MAX_ANALYSIS_TIME_HOURS=1
CACHE_TTL_HOURS=24

# Nutrition Configuration
DEFAULT_CALORIE_GOAL=2000
DEFAULT_PROTEIN_GOAL=150
DEFAULT_CARB_GOAL=200
DEFAULT_FAT_GOAL=65

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8010

CMD ["uvicorn", "apps.nutrition.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

### Docker Compose
```yaml
nutrition-service:
  build:
    context: .
    dockerfile: apps/nutrition/Dockerfile
  ports:
    - "8010:8010"
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/health_assistant
    - REDIS_URL=redis://redis:6379
    - AUTH_SERVICE_URL=http://auth-service:8000
    - HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8005
    - MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8002
    - AI_INSIGHTS_SERVICE_URL=http://ai-insights-service:8200
    - USDA_API_KEY=your-usda-api-key
    - NUTRITIONIX_APP_ID=your-nutritionix-app-id
    - NUTRITIONIX_APP_KEY=your-nutritionix-app-key
  depends_on:
    - postgres
    - redis
    - auth-service
    - health-tracking-service
    - medical-records-service
    - ai-insights-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8010/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

## Testing

### Unit Tests
```python
# tests/unit/test_nutrition.py
import pytest
from fastapi.testclient import TestClient
from apps.nutrition.main import app

client = TestClient(app)

def test_log_nutrition():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "meal_type": "breakfast",
        "foods": [
            {
                "food_id": "test-food-id",
                "quantity": 1.0,
                "unit": "cup"
            }
        ]
    }
    response = client.post("/api/v1/nutrition/log", json=data, headers=headers)
    assert response.status_code == 201
    assert "log_id" in response.json()

def test_create_meal_plan():
    headers = {"Authorization": "Bearer test-token"}
    data = {
        "user_id": "test-user-id",
        "plan_name": "Test Plan",
        "start_date": "2023-12-01",
        "end_date": "2023-12-07"
    }
    response = client.post("/api/v1/meals/plans", json=data, headers=headers)
    assert response.status_code == 201
    assert "plan_id" in response.json()
```

### Integration Tests
```python
# tests/integration/test_recipe_management.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_recipe_management_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create recipe
        recipe_data = {
            "user_id": "test-user-id",
            "name": "Test Recipe",
            "description": "Test recipe description",
            "ingredients": [],
            "instructions": ["Step 1", "Step 2"]
        }
        response = await ac.post("/api/v1/recipes", json=recipe_data)
        assert response.status_code == 201
        
        # Get recipes
        response = await ac.get("/api/v1/recipes")
        assert response.status_code == 200
        assert len(response.json()) > 0
```

## Monitoring & Logging

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "nutrition-service",
        "version": "1.0.0",
        "database": "connected",
        "redis": "connected",
        "food_database": "connected"
    }
```

### Metrics
- **Nutrition Logs**: Number of nutrition logs created
- **Meal Plans**: Meal plan creation and usage
- **Recipe Management**: Recipe creation and sharing
- **Food Searches**: Food database search volume
- **API Performance**: Response times and error rates

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@app.post("/api/v1/nutrition/log")
async def log_nutrition(request: NutritionLogRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Nutrition log created by user: {current_user.id}")
    # ... logging logic
    logger.info(f"Nutrition log completed: {log_id}")
```

## Troubleshooting

### Common Issues

#### 1. Food Database API Failures
**Symptoms**: Food search failures
**Solution**: Check API keys and external service connectivity

#### 2. Nutritional Calculation Errors
**Symptoms**: Incorrect nutritional calculations
**Solution**: Validate food database and calculation logic

#### 3. Meal Plan Generation Issues
**Symptoms**: Meal plan generation failures
**Solution**: Check recipe database and planning algorithms

#### 4. Data Synchronization Issues
**Symptoms**: Inconsistent nutrition data
**Solution**: Implement data synchronization mechanisms

### Performance Optimization
- **Caching Strategy**: Cache frequently accessed food data
- **Database Indexing**: Optimize database indexes for nutrition queries
- **API Rate Limiting**: Implement rate limiting for external APIs
- **Batch Processing**: Process nutrition logs in batches

### Security Considerations
1. **Data Privacy**: Ensure nutrition data privacy and security
2. **Access Control**: Implement role-based access to nutrition data
3. **Audit Logging**: Log all nutrition data access and modifications
4. **Data Validation**: Validate all nutrition input data
5. **Compliance**: Ensure compliance with healthcare regulations

---

## Conclusion

The Nutrition Service provides comprehensive nutrition management and meal planning capabilities for the Personal Health Assistant platform. With advanced food tracking, meal planning, and personalized recommendations, it helps users achieve their nutrition goals and maintain healthy eating habits.

For additional support or questions, please refer to the platform documentation or contact the development team. 