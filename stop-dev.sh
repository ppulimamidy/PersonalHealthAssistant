#!/bin/bash
# Stop Development Environment

echo "Stopping Personal Health Assistant Dev Environment..."

# Kill processes on ports
kill_port() {
    local port=$1
    local name=$2
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "Stopping $name on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        echo "✓ $name stopped"
    else
        echo "✓ $name not running"
    fi
}

kill_port 8080 "Backend API"
kill_port 3000 "Frontend"

echo "✓ All services stopped"
