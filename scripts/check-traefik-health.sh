#!/bin/bash

# Traefik Health Check Script
# This script checks the health of Traefik and its services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if Traefik container is running
print_status "Checking Traefik container status..."
if docker ps | grep -q "traefik-gateway"; then
    print_success "Traefik container is running"
else
    print_error "Traefik container is not running"
    exit 1
fi

# Check Traefik API
print_status "Checking Traefik API..."
if curl -s -f http://localhost:8081/api/overview > /dev/null; then
    print_success "Traefik API is accessible"
else
    print_error "Traefik API is not accessible"
    exit 1
fi

# Check Traefik dashboard
print_status "Checking Traefik dashboard..."
if curl -s -f http://localhost:8081/dashboard/ > /dev/null; then
    print_success "Traefik dashboard is accessible"
else
    print_warning "Traefik dashboard is not accessible"
fi

# Check services
services=("auth-service" "analytics-service" "user-profile" "health-tracking" "medical-records" "device-data" "ai-insights" "voice-input" "medical-analysis" "nutrition" "health-analysis" "consent-audit")

print_status "Checking service health..."
for service in "${services[@]}"; do
    if docker ps | grep -q "$service"; then
        print_success "$service is running"
    else
        print_warning "$service is not running"
    fi
done

print_success "Health check completed"
