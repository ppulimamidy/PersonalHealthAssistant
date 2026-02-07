#!/bin/bash

# Voice Input Service Startup Script

set -e

echo "🎤 Starting Voice Input Service..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model if not present
echo "📚 Checking spaCy model..."
python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    echo "📥 Downloading spaCy model..."
    python3 -m spacy download en_core_web_sm
}

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads/audio uploads/images logs temp

# Set environment variables if not set
export ENVIRONMENT=${ENVIRONMENT:-development}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export DATABASE_URL=${DATABASE_URL:-postgresql://postgres:password@localhost:5432/voice_input}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-secret-key-for-development}

# Run database migrations (if using Alembic)
if [ -f "alembic.ini" ]; then
    echo "🗄️  Running database migrations..."
    alembic upgrade head
fi

# Start the service
echo "🚀 Starting Voice Input Service on port 8004..."
echo "📖 API Documentation: http://localhost:8004/docs"
echo "🔍 Health Check: http://localhost:8004/health"

exec python3 main.py 