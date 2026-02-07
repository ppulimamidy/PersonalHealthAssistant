# Medical Analysis Service - Traefik Integration Guide

## Overview
This document captures the complete troubleshooting and configuration process for integrating the Medical Analysis Service with Traefik using both Docker provider and file provider configurations, similar to the voice-input service.

## Initial Problem
- Medical Analysis service endpoints were returning 404 errors
- Service was not properly registered in Traefik via Docker provider
- Service was only showing up via file provider
- Health checks were failing

## Root Causes Identified

### 1. Dockerfile Issues
- **Problem**: Dockerfile was hardcoded to use port 8000 instead of 8006
- **Problem**: Dockerfile was copying wrong files, causing service to run incorrectly
- **Problem**: Health check was trying to use `curl` but it wasn't installed in container
- **Problem**: Health check was pointing to `/` instead of `/ready` endpoint

### 2. Traefik Configuration Issues
- **Problem**: Service was only registered via file provider, not Docker provider
- **Problem**: Missing Traefik Docker labels in docker-compose.yml
- **Problem**: File provider config was taking precedence over Docker provider

## Step-by-Step Solution

### Step 1: Fix Dockerfile
**File**: `apps/medical_analysis/Dockerfile`

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (INCLUDE CURL)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code (CORRECT PATHS)
COPY apps/medical_analysis/ ./apps/medical_analysis/
COPY common/ ./common/
COPY apps/__init__.py ./apps/

# Create necessary directories
RUN mkdir -p logs uploads outputs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (CORRECT PORT)
EXPOSE 8006

# Health check (CORRECT ENDPOINT)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8006/ready || exit 1

# Run the application (CORRECT PORT)
CMD ["uvicorn", "apps.medical_analysis.main:app", "--host", "0.0.0.0", "--port", "8006"]
```

### Step 2: Fix docker-compose.yml Configuration
**File**: `docker-compose.yml`

```yaml
medical-analysis-service:
  build:
    context: .
    dockerfile: apps/medical_analysis/Dockerfile
  container_name: personalhealthassistant-medical-analysis-service
  environment:
    - ENVIRONMENT=development
    - LOG_LEVEL=INFO
    - DATABASE_URL=postgresql://postgres:your-super-secret-and-long-postgres-password@postgres-health-assistant:5432/health_assistant
    - REDIS_URL=redis://redis:6379/0
    - JWT_SECRET_KEY=your-super-secret-jwt-key-for-development-only
    - ALLOWED_HOSTS=["localhost", "127.0.0.1", "medical-analysis-service", "medical-analysis.localhost"]
    - CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
    - PROMETHEUS_ENABLED=true
    - GRAFANA_ENABLED=true
    - AUTH_SERVICE_URL=http://auth-service:8000
    - USER_PROFILE_SERVICE_URL=http://user-profile-service:8001
    - HEALTH_TRACKING_SERVICE_URL=http://health-tracking-service:8002
    - MEDICAL_RECORDS_SERVICE_URL=http://medical-records-service:8005
    - GROQ_API_KEY=${GROQ_API_KEY:-}
    - OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key_here}
  ports:
    - "8006:8006"
  volumes:
    - ./logs:/app/logs
  depends_on:
    - postgres-health-assistant
    - redis
    - auth-service
    - user-profile-service
    - health-tracking-service
    - medical-records-service
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8006/ready"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - default
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.medical-analysis.rule=Host(`medical-analysis.localhost`)"
    - "traefik.http.routers.medical-analysis.entrypoints=web"
    - "traefik.http.services.medical-analysis-service.loadbalancer.server.port=8006"
    - "traefik.http.services.medical-analysis-service.loadbalancer.healthcheck.path=/ready"
    - "traefik.http.services.medical-analysis-service.loadbalancer.healthcheck.interval=30s"
    - "traefik.http.services.medical-analysis-service.loadbalancer.healthcheck.timeout=10s"
    - "traefik.http.middlewares.medical-analysis-cors.headers.accessControlAllowOriginList=http://localhost:3000,http://localhost:8080,http://medical-analysis.localhost"
    - "traefik.http.routers.medical-analysis.middlewares=medical-analysis-cors@docker"
  restart: unless-stopped
```

### Step 3: Create File Provider Configuration
**File**: `traefik/medical-analysis.yml`

```yaml
# Medical Analysis Service Traefik Configuration

http:
  routers:
    medical-analysis:
      rule: "Host(`medical-analysis.localhost`)"
      service: medical-analysis-service
      entryPoints:
        - web
      middlewares:
        - medical-analysis-cors
      tls: {}

  services:
    medical-analysis-service:
      loadBalancer:
        servers:
          - url: "http://medical-analysis-service:8006"
        healthCheck:
          path: "/ready"
          interval: "30s"
          timeout: "10s"

  middlewares:
    medical-analysis-cors:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        accessControlAllowOriginList:
          - "http://localhost:3000"
          - "http://localhost:8080"
          - "http://medical-analysis.localhost"
        accessControlAllowHeaders:
          - "*"
        accessControlAllowCredentials: true
        accessControlMaxAge: 86400
```

### Step 4: Fix FastAPI Router Import Paths
**File**: `apps/medical_analysis/main.py`

Ensure correct import paths:
```python
from apps.medical_analysis.api.medical_analysis import medical_analysis_router
```

### Step 5: Build and Deploy Process

1. **Rebuild the service with curl support**:
   ```bash
   docker-compose build medical-analysis-service
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d medical-analysis-service
   ```

3. **Restart Traefik to pick up file provider config**:
   ```bash
   docker-compose restart traefik
   ```

## Verification Commands

### Check Container Health
```bash
docker ps | grep medical-analysis
```

### Check Health Check Endpoint
```bash
curl -s http://localhost:8006/ready
```

### Check Traefik Services (Both Providers)
```bash
curl -s http://localhost:8081/api/http/services | jq '.[] | select(.name | contains("medical"))'
```

### Check Traefik Routers (Both Providers)
```bash
curl -s http://localhost:8081/api/http/routers | jq '.[] | select(.name | contains("medical"))'
```

### Test End-to-End Routing
```bash
curl -s -H "Host: medical-analysis.localhost" http://localhost/ready
```

## Expected Results

### Traefik Dashboard Should Show:
1. **Docker Provider**:
   - Service: `medical-analysis-service@docker`
   - Router: `medical-analysis@docker`
   - Status: UP

2. **File Provider**:
   - Service: `medical-analysis-service@file`
   - Router: `medical-analysis@file`
   - Status: UP

### API Response:
```json
{
  "service": "medical_analysis",
  "status": "ready",
  "version": "1.0.0"
}
```

## Key Lessons Learned

1. **Docker Health Checks**: Always ensure required tools (curl) are installed in the container
2. **Port Consistency**: Ensure Dockerfile, docker-compose.yml, and application code all use the same port
3. **Traefik Labels**: Docker provider requires specific labels in docker-compose.yml
4. **File Provider**: Provides additional configuration flexibility and redundancy
5. **Dual Registration**: Services can be registered with both providers simultaneously
6. **Health Check Endpoints**: Use dedicated health check endpoints (`/ready`) instead of root (`/`)

## Troubleshooting Checklist

- [ ] Container is running and healthy
- [ ] Health check endpoint responds correctly
- [ ] Traefik Docker labels are present and correct
- [ ] File provider config exists and is valid
- [ ] Both providers show the service as UP
- [ ] End-to-end routing works through Traefik
- [ ] CORS headers are properly configured
- [ ] Service is accessible via `medical-analysis.localhost`

## Next Service Integration Template

When integrating the next service, follow this template:

1. **Dockerfile**: Include curl, correct port, proper health check
2. **docker-compose.yml**: Add Traefik labels for Docker provider
3. **traefik/[service-name].yml**: Create file provider config
4. **Build and deploy**: Rebuild service, restart Traefik
5. **Verify**: Check both providers, test end-to-end routing

This ensures consistent integration across all services in the Personal Health Assistant platform. 