#!/bin/bash
# Start Development Environment for Personal Health Assistant
# This script starts both the backend API and frontend development servers

set -e

echo "=========================================="
echo "Starting Personal Health Assistant Dev Environment"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    echo -e "${YELLOW}Killing process on port $port...${NC}"
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 1
}

# Check and clean up ports
echo -e "\n${BLUE}1. Checking ports...${NC}"
if check_port 8080; then
    echo "Port 8080 is in use"
    kill_port 8080
fi

if check_port 3000; then
    echo "Port 3000 is in use"
    read -p "Frontend is already running. Kill and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill_port 3000
    fi
fi

# Start backend API
echo -e "\n${BLUE}2. Starting Backend API (Port 8080)...${NC}"
cd apps/mvp_api

# Check if virtual environment exists
if [ ! -d "../../venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    cd ../..
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd apps/mvp_api
else
    source ../../venv/bin/activate
fi

# Start API server in background
echo "Starting FastAPI server on http://localhost:8080"
uvicorn main:app --host 0.0.0.0 --port 8080 --reload > ../../logs/api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✓ Backend API started (PID: $API_PID)${NC}"

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}Warning: API health check timed out${NC}"
    fi
done

cd ../..

# Start frontend
echo -e "\n${BLUE}3. Starting Frontend (Port 3000)...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Start frontend in background
echo "Starting Next.js on http://localhost:3000"
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

cd ..

# Summary
echo -e "\n=========================================="
echo -e "${GREEN}✓ Development environment is running!${NC}"
echo "=========================================="
echo -e "Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "Backend:   ${BLUE}http://localhost:8080${NC}"
echo -e "API Docs:  ${BLUE}http://localhost:8080/docs${NC}"
echo ""
echo -e "Logs:"
echo -e "  API:      tail -f logs/api.log"
echo -e "  Frontend: tail -f logs/frontend.log"
echo ""
echo -e "To stop:"
echo -e "  kill $API_PID $FRONTEND_PID"
echo -e "  or run: ./stop-dev.sh"
echo "=========================================="

# Keep script running and monitor processes
trap "echo 'Stopping servers...'; kill $API_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Follow logs (optional - comment out if you don't want this)
# tail -f logs/api.log logs/frontend.log
