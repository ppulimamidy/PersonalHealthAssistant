#!/bin/bash

# Personal Health Assistant - Prerequisites Setup Script
set -e

echo "🚀 Setting up Personal Health Assistant development environment..."

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "🍺 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install required packages
    echo "📦 Installing required packages..."
    brew install python@3.11 git docker docker-compose make jq
    
    # Install Python dependencies
    echo "🐍 Setting up Python environment..."
    python3 -m pip install --upgrade pip
    python3 -m pip install virtualenv
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux"
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    echo "📦 Installing required packages..."
    sudo apt-get install -y python3.11 python3.11-venv python3-pip git docker.io docker-compose make jq curl
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "🐳 Starting Docker..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a Docker
        echo "⏳ Waiting for Docker to start..."
        sleep 30
    else
        sudo systemctl start docker
    fi
fi

# Create project directories
echo "📁 Creating project structure..."
mkdir -p analytics
mkdir -p logs
mkdir -p data
mkdir -p docs/api
mkdir -p docs/architecture
mkdir -p docs/deployment

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install development tools
echo "🔧 Installing development tools..."
pip install pre-commit black flake8 mypy isort pytest pytest-cov pytest-asyncio

# Set up pre-commit hooks
echo "🔒 Setting up pre-commit hooks..."
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/health_assistant
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
QDRANT_URL=http://localhost:6333
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379

# AI/ML Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# File Storage
STORAGE_BUCKET=health-assistant-storage
STORAGE_REGION=us-east-1

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# Development
DEBUG=true
ENVIRONMENT=development
EOF
    echo "⚠️  Please update .env file with your actual API keys and configuration"
fi

# Set up Git hooks
echo "🔧 Setting up Git hooks..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run pre-commit hooks
pre-commit run --all-files
EOF

chmod +x .git/hooks/pre-commit

# Create Makefile for common commands
echo "📝 Creating Makefile..."
cat > Makefile << 'EOF'
.PHONY: help setup start stop test clean logs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Set up the development environment
	@echo "Setting up development environment..."
	./scripts/setup_prerequisites.sh

start: ## Start all services
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	sleep 30
	@echo "Services started successfully!"

stop: ## Stop all services
	@echo "Stopping all services..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting all services..."
	docker-compose restart

test: ## Run tests
	@echo "Running tests..."
	python -m pytest tests/ -v --cov=apps --cov-report=html

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	@echo "Running end-to-end tests..."
	python -m pytest tests/e2e/ -v

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f

logs: ## Show logs for all services
	@echo "Showing logs..."
	docker-compose logs -f

logs-postgres: ## Show PostgreSQL logs
	@echo "Showing PostgreSQL logs..."
	docker-compose logs -f postgres

logs-kafka: ## Show Kafka logs
	@echo "Showing Kafka logs..."
	docker-compose logs -f kafka

logs-qdrant: ## Show Qdrant logs
	@echo "Showing Qdrant logs..."
	docker-compose logs -f qdrant

db-setup: ## Set up database schema
	@echo "Setting up database schema..."
	python scripts/setup/db_setup.py

db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	python scripts/migration/migrate.py

db-backup: ## Create database backup
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres health_assistant > backup_$(date +%Y%m%d_%H%M%S).sql

format: ## Format code with black and isort
	@echo "Formatting code..."
	black apps/ tests/ scripts/
	isort apps/ tests/ scripts/

lint: ## Run linting checks
	@echo "Running linting checks..."
	flake8 apps/ tests/ scripts/
	mypy apps/ tests/ scripts/

security: ## Run security checks
	@echo "Running security checks..."
	safety check
	bandit -r apps/ -f json -o security-report.json

docs: ## Generate API documentation
	@echo "Generating API documentation..."
	python scripts/generate_docs.py

monitor: ## Open monitoring dashboard
	@echo "Opening monitoring dashboard..."
	open http://localhost:3000

health: ## Check service health
	@echo "Checking service health..."
	curl -f http://localhost:8000/health || echo "API not ready"
	curl -f http://localhost:6333/collections || echo "Qdrant not ready"
	docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092 || echo "Kafka not ready"
EOF

echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run 'make start' to start all services"
echo "3. Run 'make db-setup' to initialize the database"
echo "4. Run 'make test' to verify everything works"
echo ""
echo "🔧 Available commands:"
echo "  make help     - Show all available commands"
echo "  make start    - Start all services"
echo "  make stop     - Stop all services"
echo "  make test     - Run all tests"
echo "  make logs     - Show service logs"
echo ""
echo "🚀 Happy coding!" 