#!/bin/bash

# AI Reasoning Orchestrator Service Startup Script

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT"
export PYTHONUNBUFFERED=1

echo "🚀 Starting AI Reasoning Orchestrator Service..."
echo "📁 Project root: $PROJECT_ROOT"
echo "🐍 Python path: $PYTHONPATH"

# Change to the project root directory
cd "$PROJECT_ROOT"

# Start the service
python -m uvicorn apps.ai_reasoning_orchestrator.main:app --host 0.0.0.0 --port 8300 --reload
