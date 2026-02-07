"""
Device Data Service
Main FastAPI application for device data management and analytics.
"""

import os
import sys
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from common.config.settings import get_settings
from common.middleware.error_handling import setup_error_handlers
# from common.middleware.security import setup_security  # Temporarily disabled for development
from common.middleware.auth import auth_middleware
from common.utils.logging import setup_logging, get_logger
from common.utils.opentelemetry_config import configure_opentelemetry
from common.middleware.rate_limiter import setup_rate_limiting

from apps.device_data.api import devices, data
from apps.device_data.api import integrations
from apps.device_data.agents.agent_orchestrator import get_device_agent_orchestrator
from apps.device_data.services.event_consumer import get_event_consumer, start_event_consumer, stop_event_consumer
from apps.device_data.services.event_producer import get_event_producer

# Configure logging
setup_logging()
logger = get_logger("device_data_service")

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Device Data Service starting up...")
    
    # Initialize agent orchestrator
    try:
        orchestrator = await get_device_agent_orchestrator()
        logger.info("✅ Device Data Agent Orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent orchestrator: {e}")
    
    # Start Kafka event consumer
    try:
        app.state.consumer_task = asyncio.create_task(start_event_consumer())
        logger.info("✅ Kafka event consumer started")
    except Exception as e:
        logger.error(f"❌ Failed to start Kafka event consumer: {e}")
    
    # Health check
    logger.info("✅ Device Data Service is healthy and ready to serve requests")
    
    yield
    
    # Shutdown
    logger.info("🛑 Device Data Service shutting down...")
    
    # Cleanup agent orchestrator
    try:
        orchestrator = await get_device_agent_orchestrator()
        await orchestrator.cleanup()
        logger.info("✅ Device Data Agent Orchestrator cleaned up")
    except Exception as e:
        logger.error(f"❌ Failed to cleanup agent orchestrator: {e}")
    
    # Stop Kafka event consumer
    try:
        await stop_event_consumer()
        logger.info("✅ Kafka event consumer stopped")
    except Exception as e:
        logger.error(f"❌ Failed to stop Kafka event consumer: {e}")


# Create FastAPI app
app = FastAPI(
    title="Device Data Service",
    description="Service for managing health devices and data collection with autonomous agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure OpenTelemetry
configure_opentelemetry(app, service_name="device-data-service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add trusted host middleware
if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Add security middleware (temporarily disabled for development)
# setup_security(app)

# Add error handling
setup_error_handlers(app)

# Add rate limiting (temporarily disabled for development)
# setup_rate_limiting(app)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "device-data-service",
        "version": "1.0.0",
        "environment": "development",
        "agents_enabled": True
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Device Data Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "agents": "/api/v1/device-data/agents",
        "features": [
            "Device Management",
            "Data Collection",
            "Integration Management",
            "Autonomous Agents",
            "Data Quality Monitoring",
            "Anomaly Detection",
            "Calibration Monitoring",
            "Sync Optimization"
        ]
    }


# Agent endpoints
@app.get("/api/v1/device-data/agents/health")
async def get_agents_health():
    """Get health status of all agents"""
    try:
        orchestrator = await get_device_agent_orchestrator()
        health_status = await orchestrator.get_agent_health()
        return health_status
    except Exception as e:
        logger.error(f"Failed to get agent health: {e}")
        return {"error": "Failed to get agent health status"}


@app.post("/api/v1/device-data/agents/analyze")
async def run_comprehensive_analysis(
    background_tasks: BackgroundTasks,
    user_id: str,
    device_id: str = None
):
    """
    Run comprehensive device analysis using all agents.
    
    Args:
        user_id: User ID to analyze
        device_id: Optional specific device ID
        background_tasks: FastAPI background tasks
    """
    try:
        orchestrator = await get_device_agent_orchestrator()
        
        # Run analysis in background
        background_tasks.add_task(
            orchestrator.run_comprehensive_analysis,
            user_id,
            None,  # db session will be created in background task
            device_id
        )
        
        return {
            "message": "Comprehensive analysis started",
            "user_id": user_id,
            "device_id": device_id,
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        return {"error": "Failed to start analysis"}


@app.post("/api/v1/device-data/agents/{agent_name}/analyze")
async def run_specific_agent(
    agent_name: str,
    user_id: str,
    device_id: str = None
):
    """
    Run a specific agent for targeted analysis.
    
    Args:
        agent_name: Name of the agent to run
        user_id: User ID to analyze
        device_id: Optional specific device ID
    """
    try:
        orchestrator = await get_device_agent_orchestrator()
        result = await orchestrator.run_specific_agent(agent_name, user_id, None, device_id)
        
        return {
            "agent_name": agent_name,
            "user_id": user_id,
            "device_id": device_id,
            "result": {
                "success": result.success,
                "data": result.data,
                "insights": result.insights,
                "alerts": result.alerts,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "error": result.error
            }
        }
    except Exception as e:
        logger.error(f"Failed to run agent {agent_name}: {e}")
        return {"error": f"Failed to run agent {agent_name}"}


@app.get("/api/v1/device-data/agents")
async def list_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "name": "data_quality",
                "description": "Monitors data quality and flags issues",
                "capabilities": [
                    "Missing data detection",
                    "Inconsistent readings analysis",
                    "Data quality distribution monitoring"
                ]
            },
            {
                "name": "device_anomaly",
                "description": "Detects anomalies in device behavior",
                "capabilities": [
                    "Connection stability monitoring",
                    "Battery behavior analysis",
                    "Data volume pattern detection",
                    "Sync behavior analysis"
                ]
            },
            {
                "name": "calibration",
                "description": "Monitors device accuracy and suggests calibration",
                "capabilities": [
                    "Measurement drift detection",
                    "Consistency analysis",
                    "Accuracy assessment",
                    "Calibration recommendations"
                ]
            },
            {
                "name": "sync_monitor",
                "description": "Optimizes device synchronization patterns",
                "capabilities": [
                    "Sync frequency optimization",
                    "Reliability monitoring",
                    "Data completeness checking",
                    "Sync latency analysis"
                ]
            }
        ],
        "total_agents": 4
    }


# Include API routers
app.include_router(devices.router, prefix="/api/v1/device-data")
app.include_router(data.router, prefix="/api/v1/device-data")
app.include_router(integrations.router, prefix="/api/v1/device-data")

# Include OAuth router
try:
    from apps.device_data.api import oauth
    app.include_router(oauth.router, prefix="/api/v1/device-data")
    logger.info("✅ OAuth API router included")
except ImportError as e:
    logger.warning(f"⚠️ OAuth API router not available: {e}")

# Import and include additional routers
try:
    from apps.device_data.api import agents
    app.include_router(agents.router, prefix="/api/v1/device-data")
    logger.info("✅ Additional API router (agents) included")
except ImportError as e:
    logger.warning(f"⚠️ Agents API router not available: {e}")

try:
    from apps.device_data.api import apple_health
    if hasattr(apple_health, 'router'):
        app.include_router(apple_health.router, prefix="/api/v1/device-data")
        logger.info("✅ Apple Health API router included")
    else:
        logger.warning("⚠️ Apple Health API router not available (no router attribute)")
except ImportError as e:
    logger.warning(f"⚠️ Apple Health API router not available: {e}")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


@app.get("/api/v1/device-data/kafka/producer/status")
async def get_kafka_producer_status():
    """Get Kafka producer status and metrics"""
    try:
        producer = await get_event_producer()
        metrics = producer.get_metrics()
        return {
            "status": "success",
            "producer_metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get producer status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/v1/device-data/kafka/consumer/status")
async def get_kafka_consumer_status():
    """Get Kafka consumer status and metrics"""
    try:
        consumer = await get_event_consumer()
        status = consumer.get_consumer_status()
        return {
            "status": "success",
            "consumer_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get consumer status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.post("/api/v1/device-data/kafka/test-event")
async def test_kafka_event(
    event_type: str = "test",
    device_id: str = "test-device-001",
    message: str = "Test event from device data service"
):
    """Test Kafka event publishing"""
    try:
        producer = await get_event_producer()
        
        test_event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "message": message,
            "test": True
        }
        
        # Publish to test topic
        success = await producer.publish_batch_events([test_event], "device-data-raw")
        
        return {
            "status": "success" if success else "failed",
            "event": test_event,
            "published": success,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to test Kafka event: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,  # Device data service port
        reload=True,
        log_level="info"
    ) 