#!/bin/bash

# Personal Physician Assistant Backend Startup Script
# This script starts all required backend services for frontend development

set -e

echo "🚀 Starting Personal Physician Assistant Backend Services..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 1
    else
        return 0
    fi
}

# Function to start service
start_service() {
    local service_name=$1
    local port=$2
    local command=$3
    
    echo -e "${BLUE}Starting $service_name on port $port...${NC}"
    
    if check_port $port; then
        cd "$command"
        nohup python -m uvicorn main:app --host 0.0.0.0 --port $port --reload > /tmp/ppa-$service_name.log 2>&1 &
        echo -e "${GREEN}✅ $service_name started on http://localhost:$port${NC}"
        sleep 2
    else
        echo -e "${RED}❌ Failed to start $service_name - port $port is busy${NC}"
    fi
}

# Check if we're in the right directory
if [ ! -f "apps/api_gateway/main.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the PersonalHealthAssistant root directory${NC}"
    exit 1
fi

# Start Redis and PostgreSQL if using Docker
echo -e "${BLUE}Starting infrastructure services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d redis postgres 2>/dev/null || echo -e "${YELLOW}⚠️  Docker services already running or not available${NC}"
else
    echo -e "${YELLOW}⚠️  docker-compose not found, skipping infrastructure services${NC}"
fi

# Start API Gateway (Enhanced)
start_service "API Gateway" 8000 "apps/api_gateway"

# Start AI Reasoning Orchestrator
start_service "AI Reasoning Orchestrator" 8300 "apps/ai_reasoning_orchestrator"

# Start GraphQL BFF
start_service "GraphQL BFF" 8400 "apps/graphql_bff"

# Start Health Tracking Service
start_service "Health Tracking Service" 8100 "apps/health_tracking"

# Start Medical Records Service
start_service "Medical Records Service" 8200 "apps/medical_records"

# Start AI Insights Service
start_service "AI Insights Service" 8201 "apps/ai_insights"

# Start Nutrition Service
start_service "Nutrition Service" 8202 "apps/nutrition"

# Start Device Data Service
start_service "Device Data Service" 8203 "apps/device_data"

echo ""
echo -e "${GREEN}🎉 All backend services started!${NC}"
echo "=================================================="
echo -e "${BLUE}Services running:${NC}"
echo -e "  • API Gateway: ${GREEN}http://localhost:8000${NC}"
echo -e "  • AI Reasoning Orchestrator: ${GREEN}http://localhost:8300${NC}"
echo -e "  • GraphQL BFF: ${GREEN}http://localhost:8400${NC}"
echo -e "  • Health Tracking: ${GREEN}http://localhost:8100${NC}"
echo -e "  • Medical Records: ${GREEN}http://localhost:8200${NC}"
echo -e "  • AI Insights: ${GREEN}http://localhost:8201${NC}"
echo -e "  • Nutrition: ${GREEN}http://localhost:8202${NC}"
echo -e "  • Device Data: ${GREEN}http://localhost:8203${NC}"
echo ""
echo -e "${YELLOW}📝 Frontend Configuration:${NC}"
echo "Update your frontend .env.development file:"
echo "REACT_APP_API_BASE_URL=http://localhost:8000"
echo "REACT_APP_GRAPHQL_URL=http://localhost:8400/graphql"
echo ""
echo -e "${YELLOW}🔍 Health Checks:${NC}"
echo "Test the API Gateway: curl http://localhost:8000/health"
echo "Test GraphQL BFF: curl http://localhost:8400/health"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo "Service logs are available in /tmp/ppa-*.log"
echo ""
echo -e "${GREEN}✨ Your frontend can now connect to the backend!${NC}"
