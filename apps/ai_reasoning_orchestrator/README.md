# AI Reasoning Orchestrator Service

Central intelligence layer for Personal Physician Assistant (PPA) that orchestrates data from all microservices to provide unified, explainable health insights.

## Quick Start

### Prerequisites
- Python 3.11+
- Redis server running
- Environment variables configured (see below)

### Running the Service

#### Option 1: Using the startup script (Recommended)
```bash
cd apps/ai_reasoning_orchestrator
./start.sh
```

#### Option 2: Using Python directly
```bash
cd /path/to/PersonalHealthAssistant
PYTHONPATH=/path/to/PersonalHealthAssistant python -m uvicorn apps.ai_reasoning_orchestrator.main:app --host 0.0.0.0 --port 8300 --reload
```

#### Option 3: Using Docker
```bash
docker build -t ai-reasoning-orchestrator .
docker run -p 8300:8300 ai-reasoning-orchestrator
```

## Environment Variables

Make sure these environment variables are set:

```bash
# Redis
REDIS_URL=redis://localhost:6379

# Service URLs
HEALTH_TRACKING_SERVICE_URL=http://localhost:8001
MEDICAL_RECORDS_SERVICE_URL=http://localhost:8002
AI_INSIGHTS_SERVICE_URL=http://localhost:8003
KNOWLEDGE_GRAPH_SERVICE_URL=http://localhost:8004
NUTRITION_SERVICE_URL=http://localhost:8005
DEVICE_DATA_SERVICE_URL=http://localhost:8006

# OpenAI (for AI insights)
OPENAI_API_KEY=your_openai_api_key_here
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/reason` - Main reasoning endpoint
- `POST /api/v1/query` - Natural language query endpoint
- `GET /api/v1/insights/daily-summary` - Daily insights summary
- `POST /health/analyze-symptoms` - Symptom analysis endpoint
- `POST /health/query` - Health query endpoint
- `POST /health/doctor-report` - Doctor report generation
- `GET /health/unified-dashboard` - Unified dashboard data

## Issue Fix

The main issue was with Python path configuration. The service imports from the `common` module which is located at the project root, but when running the service directly from the `apps/ai_reasoning_orchestrator` directory, Python couldn't find the `common` module.

**Solution**: Set the `PYTHONPATH` environment variable to point to the project root directory before starting the service.

## Development

The service is now properly configured to run both locally and in Docker. The startup scripts handle the Python path configuration automatically.

## Health Check

Test if the service is running:
```bash
curl http://localhost:8300/health
```

Expected response:
```json
{
  "success": true,
  "message": "AI Reasoning Orchestrator is healthy",
  "timestamp": "2025-08-09T01:28:56.415732",
  "data": {
    "status": "healthy",
    "service": "ai-reasoning-orchestrator",
    "version": "1.0.0"
  }
}
```
