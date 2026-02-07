#!/bin/bash

# Vision Analysis Setup Script
# This script helps set up and test the vision analysis feature

set -e

echo "🚀 Setting up Vision Analysis Service"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Check environment variables
check_environment() {
    print_status "Checking environment variables..."
    
    # Check GROQ API key
    if [ -z "$GROQ_API_KEY" ]; then
        print_warning "GROQ_API_KEY is not set"
        print_status "Using default GROQ API key from docker-compose.yml"
    else
        print_success "GROQ_API_KEY is set"
    fi
    
    # Check OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY is not set"
        print_status "You can set it with: export OPENAI_API_KEY=your_key_here"
    else
        print_success "OPENAI_API_KEY is set"
    fi
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        print_success ".env file found"
    else
        print_warning ".env file not found"
        print_status "Creating .env file with default values..."
        cat > .env << EOF
# Vision Analysis Configuration
GROQ_API_KEY=${GROQ_API_KEY:-}
OPENAI_API_KEY=your_openai_api_key_here

# Service Configuration
HOST=0.0.0.0
PORT=8010
DATABASE_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@postgres-health-assistant:5432/health_assistant
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-super-secret-jwt-key-for-development-only

# Vision Analysis Configuration
VISION_MODEL_DEFAULT=llava-3.1-8b-instant
TTS_PROVIDER_DEFAULT=edge_tts
TTS_VOICE_DEFAULT=en-US-JennyNeural
MAX_IMAGE_SIZE=10485760
SUPPORTED_IMAGE_FORMATS=jpeg,jpg,png,webp,tiff,bmp
IMAGE_UPLOAD_DIR=/app/uploads/images
AUDIO_OUTPUT_DIR=/app/outputs/vision_analysis
EOF
        print_success ".env file created"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p uploads/images
    mkdir -p uploads/audio
    mkdir -p outputs/vision_analysis
    mkdir -p logs
    
    print_success "Directories created"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    cd apps/voice_input
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
    
    cd ../..
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Build the voice input service
    docker-compose build voice-input-service
    
    # Start the service
    docker-compose up -d voice-input-service
    
    print_success "Voice input service started"
}

# Wait for service to be ready
wait_for_service() {
    print_status "Waiting for service to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8010/health &> /dev/null; then
            print_success "Service is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - Service not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Service failed to start within expected time"
    return 1
}

# Test the service
test_service() {
    print_status "Testing the service..."
    
    # Test health endpoint
    if curl -f http://localhost:8010/health &> /dev/null; then
        print_success "Health endpoint is working"
    else
        print_error "Health endpoint is not working"
        return 1
    fi
    
    # Test vision analysis endpoints
    if curl -f http://localhost:8010/api/v1/voice-input/vision-analysis/health &> /dev/null; then
        print_success "Vision analysis health endpoint is working"
    else
        print_error "Vision analysis health endpoint is not working"
        return 1
    fi
    
    # Test providers endpoint
    if curl -f http://localhost:8010/api/v1/voice-input/vision-analysis/providers/vision &> /dev/null; then
        print_success "Vision providers endpoint is working"
    else
        print_error "Vision providers endpoint is not working"
        return 1
    fi
    
    print_success "All basic endpoints are working"
}

# Run comprehensive tests
run_tests() {
    print_status "Running comprehensive tests..."
    
    cd apps/voice_input
    
    # Check if virtual environment exists and activate it
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run the test script
    if python test_vision_analysis.py; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        return 1
    fi
    
    cd ../..
}

# Show usage information
show_usage() {
    echo ""
    echo "🎉 Vision Analysis Service Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Service URLs:"
    echo "  - Main Service: http://localhost:8010"
    echo "  - API Documentation: http://localhost:8010/docs"
    echo "  - Health Check: http://localhost:8010/health"
    echo "  - Vision Analysis: http://localhost:8010/api/v1/voice-input/vision-analysis"
    echo ""
    echo "Traefik URLs (if using Traefik):"
    echo "  - Main Service: http://voice-input.localhost"
    echo "  - API Documentation: http://voice-input.localhost/docs"
    echo ""
    echo "Example Usage:"
    echo "  curl -X POST \"http://localhost:8010/api/v1/voice-input/vision-analysis/complete-analysis\" \\"
    echo "    -F \"patient_id=123e4567-e89b-12d3-a456-426614174000\" \\"
    echo "    -F \"image_file=@your_image.jpg\" \\"
    echo "    -F \"text_query=What do you see in this image?\""
    echo ""
    echo "Test Script:"
    echo "  cd apps/voice_input && python test_vision_analysis.py"
    echo ""
    echo "Logs:"
    echo "  docker-compose logs voice-input-service"
    echo ""
    echo "Stop Service:"
    echo "  docker-compose stop voice-input-service"
    echo ""
}

# Main execution
main() {
    echo "Starting Vision Analysis Service setup..."
    echo ""
    
    check_dependencies
    check_environment
    create_directories
    install_dependencies
    start_services
    wait_for_service
    test_service
    
    # Ask if user wants to run comprehensive tests
    echo ""
    read -p "Do you want to run comprehensive tests? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi
    
    show_usage
}

# Handle script arguments
case "${1:-}" in
    "test")
        test_service
        ;;
    "logs")
        docker-compose logs voice-input-service
        ;;
    "stop")
        docker-compose stop voice-input-service
        ;;
    "restart")
        docker-compose restart voice-input-service
        ;;
    "clean")
        docker-compose down
        docker system prune -f
        ;;
    "help"|"-h"|"--help")
        echo "Vision Analysis Setup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Full setup and installation"
        echo "  test       - Test the service endpoints"
        echo "  logs       - Show service logs"
        echo "  stop       - Stop the service"
        echo "  restart    - Restart the service"
        echo "  clean      - Clean up containers and images"
        echo "  help       - Show this help message"
        ;;
    *)
        main
        ;;
esac 