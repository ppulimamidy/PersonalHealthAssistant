#!/bin/bash

# Personal Health Assistant - One-Command Setup
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Personal Health Assistant - One-Command Setup"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if virtual environment is active
check_venv_active() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_success "Activated virtual environment: $VIRTUAL_ENV"
        return 0
    else
        print_error "Virtual environment not found"
        return 1
    fi
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

print_success "All prerequisites are installed"

# Step 2: Set up Python environment
print_status "Setting up Python environment..."

# Check if virtual environment already exists
if [ -d "venv" ]; then
    print_success "Virtual environment already exists"
    
    # Check if it's already activated
    if check_venv_active; then
        print_success "Virtual environment is already active"
    else
        # Activate the existing virtual environment
        if activate_venv; then
            print_success "Activated existing virtual environment"
        else
            print_error "Failed to activate virtual environment"
            exit 1
        fi
    fi
else
    # Create new virtual environment
    print_status "Creating new virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        print_success "Created virtual environment"
        
        # Activate the new virtual environment
        if activate_venv; then
            print_success "Activated new virtual environment"
        else
            print_error "Failed to activate virtual environment"
            exit 1
        fi
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Verify virtual environment is active
if ! check_venv_active; then
    print_error "Virtual environment is not active. Please activate it manually:"
    echo "source venv/bin/activate"
    exit 1
fi

# Upgrade pip in the virtual environment
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements if they exist
if [ -f "requirements.txt" ]; then
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Installed Python dependencies"
    else
        print_error "Failed to install Python dependencies"
        exit 1
    fi
else
    print_warning "requirements.txt not found, skipping dependency installation"
fi

# Step 3: Install missing dependencies
print_status "Installing missing dependencies..."

# Run the dependency installation script
if [ -f "scripts/install_missing_dependencies.py" ]; then
    python scripts/install_missing_dependencies.py
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_warning "Some dependencies may not have been installed properly"
    fi
else
    print_warning "Dependency installation script not found, skipping..."
fi

# Step 4: Start Docker services
print_status "Starting Docker services..."

# Stop any existing services
docker-compose down 2>/dev/null || true

# Start services
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Step 5: Verify services are running
print_status "Verifying services..."

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "Docker services are running"
else
    print_error "Docker services failed to start"
    docker-compose logs
    exit 1
fi

# Step 6: Run database setup
print_status "Setting up database..."

if [ -f "scripts/setup/db_setup.py" ]; then
    python scripts/setup/db_setup.py
    if [ $? -eq 0 ]; then
        print_success "Database setup completed"
    else
        print_error "Database setup failed"
        exit 1
    fi
else
    print_warning "Database setup script not found, skipping..."
fi

# Step 7: Run tests
print_status "Running tests..."

if [ -f "scripts/test_setup.py" ]; then
    python scripts/test_setup.py
    if [ $? -eq 0 ]; then
        print_success "Tests passed"
    else
        print_warning "Some tests failed, but setup may still be functional"
    fi
else
    print_warning "Test script not found, skipping..."
fi

# Step 8: Final validation
print_status "Running final validation..."

if [ -f "scripts/validate_requirements.py" ]; then
    python scripts/validate_requirements.py
    if [ $? -eq 0 ]; then
        print_success "All requirements validated successfully"
    else
        print_warning "Some requirements may not be met"
    fi
else
    print_warning "Validation script not found, skipping..."
fi

# Success message
echo ""
echo "🎉 SETUP COMPLETED!"
echo "=================="
echo ""
echo "Your Personal Health Assistant is now ready!"
echo ""
echo "Virtual Environment Status:"
if check_venv_active; then
    echo "✅ Virtual environment is ACTIVE: $VIRTUAL_ENV"
    echo "   To deactivate: deactivate"
else
    echo "⚠️  Virtual environment is NOT active"
    echo "   To activate: source venv/bin/activate"
fi
echo ""
echo "Next steps:"
echo "1. Update your .env file with actual API keys"
echo "2. Start the application: python main.py"
echo "3. Access the API documentation: http://localhost:8000/docs"
echo "4. Access Supabase Studio: http://localhost:3001"
echo ""
echo "Useful commands:"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart"
echo "- Run tests: python scripts/test_setup.py"
echo "- Validate environment: python scripts/validate_requirements.py"
echo ""
echo "Happy coding! 🚀" 