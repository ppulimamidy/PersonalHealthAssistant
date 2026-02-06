#!/bin/bash

# Comprehensive Health Tracking Service Test Runner
# This script starts the service and runs all tests to verify production readiness

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_PORT=8002
SERVICE_HOST="localhost"
BASE_URL="http://${SERVICE_HOST}:${SERVICE_PORT}"
SERVICE_NAME="health-tracking-service"

echo -e "${BLUE}🏥 Health Tracking Service - Production Readiness Test${NC}"
echo -e "${BLUE}==================================================${NC}"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$SERVICE_PORT -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $SERVICE_PORT is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    echo -e "${BLUE}⏳ Waiting for service to be ready...${NC}"
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is ready!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - Service not ready yet...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Service failed to start within expected time${NC}"
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    if [ ! -z "$SERVICE_PID" ]; then
        echo -e "${YELLOW}🛑 Stopping service (PID: $SERVICE_PID)${NC}"
        kill $SERVICE_PID 2>/dev/null || true
        wait $SERVICE_PID 2>/dev/null || true
    fi
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found. Please run this script from the health_tracking directory.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "../venv" ] && [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
    source ../venv/bin/activate
fi

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if port is available
if ! check_port; then
    echo -e "${RED}❌ Port $SERVICE_PORT is already in use. Please stop the existing service first.${NC}"
    exit 1
fi

# Start the service
echo -e "${BLUE}🚀 Starting Health Tracking Service...${NC}"
echo -e "${BLUE}   Port: $SERVICE_PORT${NC}"
echo -e "${BLUE}   URL: $BASE_URL${NC}"

# Start service in background
python main.py &
SERVICE_PID=$!

# Wait for service to be ready
if ! wait_for_service; then
    echo -e "${RED}❌ Failed to start service${NC}"
    exit 1
fi

# Run basic health check
echo -e "${BLUE}🔍 Running basic health check...${NC}"
if curl -s -f "${BASE_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ Basic health check passed${NC}"
else
    echo -e "${RED}❌ Basic health check failed${NC}"
    exit 1
fi

# Run comprehensive tests
echo -e "${BLUE}🧪 Running comprehensive endpoint tests...${NC}"
echo -e "${BLUE}   This will test all endpoints, authentication, error handling, and performance${NC}"

# Run the comprehensive test suite
python comprehensive_endpoint_test.py "$BASE_URL"
TEST_EXIT_CODE=$?

# Check test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Health Tracking Service is PRODUCTION READY!${NC}"
    echo -e "${GREEN}✅ Service is robust and ready for frontend consumption${NC}"
    
    # Display service information
    echo -e "${BLUE}📋 Service Information:${NC}"
    echo -e "${BLUE}   URL: $BASE_URL${NC}"
    echo -e "${BLUE}   Documentation: ${BASE_URL}/docs${NC}"
    echo -e "${BLUE}   Health Check: ${BASE_URL}/health${NC}"
    echo -e "${BLUE}   Metrics: ${BASE_URL}/metrics${NC}"
    
    # Show recent test results
    if [ -f "health_tracking_test_results_*.json" ]; then
        echo -e "${BLUE}📄 Test results saved to: health_tracking_test_results_*.json${NC}"
    fi
    
else
    echo -e "${RED}💥 Some tests failed. Service needs attention before production deployment.${NC}"
    echo -e "${YELLOW}⚠️  Check the test results above for details${NC}"
fi

# Keep service running for manual testing if requested
if [ "$1" = "--keep-running" ]; then
    echo -e "${BLUE}🔄 Keeping service running for manual testing...${NC}"
    echo -e "${BLUE}   Press Ctrl+C to stop${NC}"
    wait $SERVICE_PID
else
    echo -e "${BLUE}✅ Test completed. Service will be stopped.${NC}"
fi

exit $TEST_EXIT_CODE 