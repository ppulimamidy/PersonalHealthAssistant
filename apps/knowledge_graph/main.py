"""
Knowledge Graph Service Main Application

FastAPI application for the Personal Health Assistant Knowledge Graph Service.
Provides comprehensive medical knowledge graph functionality with Neo4j and Qdrant integration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from apps.knowledge_graph.api.knowledge import router as knowledge_router
from common.middleware.auth import AuthMiddleware
from common.middleware.error_handling import (
    ErrorHandlingMiddleware,
    setup_error_handlers,
)
from common.utils.logging import get_logger
from common.models.registry import register_model
from common.config.settings import get_settings
from common.middleware.prometheus_metrics import setup_prometheus_metrics

# Import all models that are referenced in relationships
from .models.knowledge_models import (
    MedicalEntityResponse,
    RelationshipResponse,
    KnowledgeGraphResponse,
    MedicalRecommendation,
    OntologyImportResponse,
    KnowledgeGraphStats,
    HealthInsight,
)

# Global logger
logger = get_logger("knowledge_graph.main")

# Global service instance
knowledge_graph_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global knowledge_graph_service

    # Startup
    logger.info("🚀 Starting Knowledge Graph Service...")

    # Register models in the global registry
    try:
        register_model("MedicalEntityResponse", MedicalEntityResponse)
        register_model("RelationshipResponse", RelationshipResponse)
        register_model("KnowledgeGraphResponse", KnowledgeGraphResponse)
        register_model("MedicalRecommendation", MedicalRecommendation)
        register_model("OntologyImportResponse", OntologyImportResponse)
        register_model("KnowledgeGraphStats", KnowledgeGraphStats)
        register_model("HealthInsight", HealthInsight)
        logger.info("Knowledge Graph models registered in global registry")
    except Exception as e:
        logger.warning(f"Failed to register Knowledge Graph models: {e}")

    # Initialize knowledge graph service
    try:
        from .services.knowledge_graph_service import KnowledgeGraphService

        knowledge_graph_service = KnowledgeGraphService()
        await knowledge_graph_service.initialize()
        logger.info("Knowledge Graph Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Knowledge Graph Service: {e}")
        # Don't raise here to allow the service to start with limited functionality

    logger.info("✅ Knowledge Graph Service started successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Knowledge Graph Service...")

    if knowledge_graph_service:
        try:
            await knowledge_graph_service.cleanup()
            logger.info("Knowledge Graph Service cleaned up")
        except Exception as e:
            logger.error(f"Error during Knowledge Graph Service cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title="Knowledge Graph Service",
    description="Medical Knowledge Graph Service for Personal Health Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Setup error handlers
setup_error_handlers(app)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="knowledge-graph-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "knowledge-graph-service")
except ImportError:
    pass

# Add routers
app.include_router(
    knowledge_router, prefix="/api/v1/knowledge-graph", tags=["Knowledge Graph"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint for the Knowledge Graph Service."""
    return {
        "service": "Knowledge Graph Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "description": "Medical Knowledge Graph Service for Personal Health Assistant",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if knowledge_graph_service:
            health_status = await knowledge_graph_service.health_check()
            return health_status
        else:
            return {
                "service": "knowledge-graph-service",
                "status": "initializing",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "service": "knowledge-graph-service",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }


# Readiness check endpoint
@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        if knowledge_graph_service:
            health_status = await knowledge_graph_service.health_check()
            if health_status["status"] == "healthy":
                return {
                    "status": "ready",
                    "service": "knowledge-graph-service",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "status": "not_ready",
                    "service": "knowledge-graph-service",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        else:
            return {
                "status": "not_ready",
                "service": "knowledge-graph-service",
                "reason": "Service not initialized",
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "service": "knowledge-graph-service",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Service information endpoint
@app.get("/info")
async def service_info():
    """Get service information."""
    return {
        "service": "Knowledge Graph Service",
        "version": "1.0.0",
        "description": "Medical Knowledge Graph Service for Personal Health Assistant",
        "features": [
            "Medical entity management",
            "Relationship management",
            "Semantic search and queries",
            "Path finding",
            "Recommendations",
            "Statistics and analytics",
            "Ontology integration",
            "Health insights",
        ],
        "databases": ["Neo4j (Graph Database)", "Qdrant (Vector Database)"],
        "ontologies": [
            "SNOMED CT",
            "ICD-10",
            "ICD-11",
            "LOINC",
            "RxNorm",
            "UMLS",
            "MESH",
            "DOID",
            "HP (Human Phenotype Ontology)",
            "CHEBI",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True, log_level="info")
