#!/bin/bash

# Nutrition Service Integration Setup Script

echo "🚀 Setting up Nutrition Service Integration..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ../../.env ]; then
    echo "📝 Creating .env file with placeholder values..."
    cat > ../../.env << EOF
# Nutrition Service Integration Environment Variables
# Fill in your actual API keys below

# External API Keys (optional - service will work with mock data if not provided)
NUTRITIONIX_API_KEY=your_nutritionix_api_key_here
NUTRITIONIX_APP_ID=your_nutritionix_app_id_here
USDA_API_KEY=your_usda_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here
AZURE_VISION_API_KEY=your_azure_vision_api_key_here

# Service URLs
USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
AUTH_SERVICE_URL=http://auth-service:8000

# Database
DATABASE_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@postgres:5432/health_assistant
REDIS_URL=redis://redis:6379

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-for-development-only
JWT_ALGORITHM=HS256

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created at ../../.env"
    echo "⚠️  Please edit the .env file and add your actual API keys if you have them."
else
    echo "✅ .env file already exists"
fi

# Check if required directories exist
echo "🔍 Checking required directories..."
if [ ! -d "../../common" ]; then
    echo "❌ Common directory not found. Please run this script from the correct location."
    exit 1
fi

if [ ! -d "../../apps/auth" ]; then
    echo "❌ Auth service directory not found. Please run this script from the correct location."
    exit 1
fi

if [ ! -d "../../apps/user_profile" ]; then
    echo "❌ User profile service directory not found. Please run this script from the correct location."
    exit 1
fi

echo "✅ All required directories found"

# Build and start services
echo "🐳 Building and starting services..."
cd ../..
docker-compose -f docker-compose.nutrition-integration.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
services=(
    "http://localhost:5432"  # PostgreSQL
    "http://localhost:8000"  # Auth Service
    "http://localhost:8001"  # User Profile Service
    "http://localhost:8007"  # Nutrition Service
)

for service in "${services[@]}"; do
    if curl -f "$service/health" > /dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "⚠️  $service health check failed (this might be normal for PostgreSQL)"
    fi
done

echo ""
echo "🎉 Nutrition Service Integration Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit ../../.env and add your API keys if you have them"
echo "2. Run the integration tests: python test_auth_integration.py"
echo "3. Access the services:"
echo "   - Auth Service: http://localhost:8000"
echo "   - User Profile Service: http://localhost:8001"
echo "   - Nutrition Service: http://localhost:8007"
echo "   - Traefik Dashboard: http://localhost:8080"
echo "   - Through Traefik: http://nutrition.localhost"
echo ""
echo "📚 For more information, see INTEGRATION_GUIDE.md" 