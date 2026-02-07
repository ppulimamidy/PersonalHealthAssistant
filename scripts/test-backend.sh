#!/bin/bash

# Personal Physician Assistant Backend Test Script
# This script tests if all backend services are running correctly

set -e

echo "🧪 Testing Personal Physician Assistant Backend Services..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test service
test_service() {
    local service_name=$1
    local url=$2
    local endpoint=$3
    
    echo -e "${BLUE}Testing $service_name...${NC}"
    
    if curl -s -f "$url$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running at $url${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not responding at $url${NC}"
        return 1
    fi
}

# Test all services
services=(
    "API Gateway|http://localhost:8000|/health"
    "AI Reasoning Orchestrator|http://localhost:8300|/health"
    "GraphQL BFF|http://localhost:8400|/health"
    "Health Tracking Service|http://localhost:8100|/health"
    "Medical Records Service|http://localhost:8200|/health"
    "AI Insights Service|http://localhost:8201|/health"
    "Nutrition Service|http://localhost:8202|/health"
    "Device Data Service|http://localhost:8203|/health"
)

failed_services=()

for service in "${services[@]}"; do
    IFS='|' read -r name url endpoint <<< "$service"
    if ! test_service "$name" "$url" "$endpoint"; then
        failed_services+=("$name")
    fi
    echo ""
done

# Summary
echo "=================================================="
if [ ${#failed_services[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 All backend services are running correctly!${NC}"
    echo ""
    echo -e "${BLUE}Frontend Configuration:${NC}"
    echo "Your frontend can now connect using:"
    echo "• API Gateway: http://localhost:8000"
    echo "• GraphQL BFF: http://localhost:8400"
    echo ""
    echo -e "${GREEN}✨ Ready for frontend development!${NC}"
else
    echo -e "${RED}❌ Some services failed:${NC}"
    for service in "${failed_services[@]}"; do
        echo -e "${RED}  • $service${NC}"
    done
    echo ""
    echo -e "${YELLOW}💡 To start missing services, run:${NC}"
    echo "  ./scripts/start-backend.sh"
    echo ""
    echo -e "${YELLOW}🔍 To check service logs:${NC}"
    echo "  tail -f /tmp/ppa-*.log"
    exit 1
fi
