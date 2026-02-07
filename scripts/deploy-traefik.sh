#!/bin/bash

# Traefik Deployment Script
# This script deploys the enhanced Traefik configuration

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

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
fi

# Stop existing services
print_status "Stopping existing services..."
docker-compose down

# Build and start services
print_status "Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
./scripts/check-traefik-health.sh

print_success "Deployment completed successfully"
print_status "Traefik dashboard: http://traefik.localhost:8081"
print_status "Auth service: https://auth.localhost"
print_status "Analytics service: https://analytics.localhost"
