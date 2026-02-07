"""
API Gateway Service
Main entry point for the API Gateway that routes requests to microservices.
"""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import httpx
import redis.asyncio as redis

from common.config.settings import settings
from common.middleware.auth import auth_middleware, require_auth
from common.models.base import (
    ErrorResponse, SuccessResponse, create_error_response, create_success_response,
    ErrorCode, ErrorSeverity, BaseServiceException, CircuitBreakerException
)
from common.utils.logging import get_logger
from common.utils.resilience import CircuitBreaker, RetryHandler, TimeoutHandler

logger = get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('api_gateway_active_requests', 'Active requests', ['service'])

# Service registry
SERVICE_REGISTRY = {
    "auth": {
        "url": settings.AUTH_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="auth_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "user_profile": {
        "url": settings.USER_PROFILE_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="user_profile_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "health_tracking": {
        "url": settings.HEALTH_TRACKING_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="health_tracking_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "ai_reasoning_orchestrator": {
        "url": settings.AI_REASONING_ORCHESTRATOR_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="ai_reasoning_orchestrator"),
        "timeout": TimeoutHandler(timeout=60.0),  # Longer timeout for AI reasoning
        "retry": RetryHandler(max_attempts=2)  # Fewer retries for AI services
    },
    "graphql_bff": {
        "url": settings.GRAPHQL_BFF_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="graphql_bff"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "ai_insights": {
        "url": settings.AI_INSIGHTS_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="ai_insights_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "medical_records": {
        "url": settings.MEDICAL_RECORDS_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="medical_records_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "nutrition": {
        "url": settings.NUTRITION_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="nutrition_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    },
    "device_data": {
        "url": settings.DEVICE_DATA_SERVICE_URL,
        "health_check": "/health",
        "circuit_breaker": CircuitBreaker(failure_threshold=5, recovery_timeout=60, name="device_data_service"),
        "timeout": TimeoutHandler(timeout=30.0),
        "retry": RetryHandler(max_attempts=3)
    }
}

# Rate limiting
RATE_LIMIT_STORE = {}
RATE_LIMIT_REQUESTS = settings.RATE_LIMIT_PER_MINUTE
RATE_LIMIT_WINDOW = 60  # seconds

# Redis client for distributed rate limiting
redis_client: Optional[redis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting API Gateway...")
    
    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis client: {e}")
        redis_client = None
    
    # Health check all services
    await health_check_services()
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway...")
    if redis_client:
        await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Personal Health Assistant API Gateway",
    description="API Gateway for Personal Health Assistant microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

class RequestContextMiddleware:
    """Middleware to add request context and metrics"""
    
    async def __call__(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to headers
        request.headers.__dict__["_list"].append(
            (b"x-request-id", request_id.encode())
        )
        
        # Start timing
        start_time = time.time()
        
        # Track active requests
        service = get_service_from_path(request.url.path)
        if service:
            ACTIVE_REQUESTS.labels(service=service).inc()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            # Add request ID to response headers
            response.headers["x-request-id"] = request_id
            
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise
        finally:
            # Decrement active requests
            if service:
                ACTIVE_REQUESTS.labels(service=service).dec()

app.add_middleware(RequestContextMiddleware)

def get_service_from_path(path: str) -> Optional[str]:
    """Determine service from request path"""
    if path.startswith("/auth"):
        return "auth"
    elif path.startswith("/user-profile"):
        return "user_profile"
    elif path.startswith("/health-tracking"):
        return "health_tracking"
    elif path.startswith("/ai-reasoning"):
        return "ai_reasoning_orchestrator"
    elif path.startswith("/graphql"):
        return "graphql_bff"
    elif path.startswith("/ai-insights"):
        return "ai_insights"
    elif path.startswith("/medical-records"):
        return "medical_records"
    elif path.startswith("/nutrition"):
        return "nutrition"
    elif path.startswith("/device-data"):
        return "device_data"
    elif path.startswith("/health"):  # Composite health endpoints
        return "composite"
    return None

async def check_rate_limit(request: Request) -> bool:
    """Check rate limit for the request"""
    # Get client identifier
    client_id = get_client_id(request)
    
    if redis_client:
        # Use Redis for distributed rate limiting
        key = f"rate_limit:{client_id}"
        current = await redis_client.get(key)
        
        if current and int(current) >= RATE_LIMIT_REQUESTS:
            return False
        
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, RATE_LIMIT_WINDOW)
        await pipe.execute()
        return True
    else:
        # Fallback to in-memory rate limiting
        now = time.time()
        if client_id not in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[client_id] = {"count": 0, "reset_time": now + RATE_LIMIT_WINDOW}
        
        client_data = RATE_LIMIT_STORE[client_id]
        
        if now > client_data["reset_time"]:
            client_data["count"] = 0
            client_data["reset_time"] = now + RATE_LIMIT_WINDOW
        
        if client_data["count"] >= RATE_LIMIT_REQUESTS:
            return False
        
        client_data["count"] += 1
        return True

def get_client_id(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Try to get user ID from auth header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            # Extract user ID from JWT token (simplified)
            token = auth_header.split(" ")[1]
            # In a real implementation, you'd decode the JWT to get user ID
            return f"user:{hash(token) % 10000}"
        except:
            pass
    
    # Fall back to IP address
    return f"ip:{request.client.host if request.client else 'unknown'}"

async def health_check_services():
    """Health check all registered services"""
    logger.info("Performing health checks for all services...")
    
    for service_name, service_config in SERVICE_REGISTRY.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_config['url']}{service_config['health_check']}")
                if response.status_code == 200:
                    logger.info(f"Service {service_name} is healthy")
                else:
                    logger.warning(f"Service {service_name} health check failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Service {service_name} health check error: {e}")

async def forward_request(
    request: Request,
    service_name: str,
    path: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> httpx.Response:
    """Forward request to the appropriate service with resilience patterns"""
    service_config = SERVICE_REGISTRY.get(service_name)
    if not service_config:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    # Prepare headers
    forward_headers = {}
    if headers:
        forward_headers.update(headers)
    
    # Forward auth header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        forward_headers["Authorization"] = auth_header
    
    # Forward request ID
    request_id = getattr(request.state, 'request_id', None)
    if request_id:
        forward_headers["x-request-id"] = request_id
    
    # Forward user agent
    user_agent = request.headers.get("User-Agent")
    if user_agent:
        forward_headers["User-Agent"] = user_agent
    
    # Build target URL
    target_url = f"{service_config['url']}{path}"
    
    # Apply resilience patterns
    async def make_request():
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(target_url, headers=forward_headers)
            elif method.upper() == "POST":
                response = await client.post(target_url, json=data, headers=forward_headers)
            elif method.upper() == "PUT":
                response = await client.put(target_url, json=data, headers=forward_headers)
            elif method.upper() == "DELETE":
                response = await client.delete(target_url, headers=forward_headers)
            elif method.upper() == "PATCH":
                response = await client.patch(target_url, json=data, headers=forward_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
    
    # Apply circuit breaker, retry, and timeout
    try:
        response = await service_config["circuit_breaker"].call(
            service_config["retry"].call(
                service_config["timeout"].call(make_request)
            )
        )
        return response
    except Exception as e:
        logger.error(f"Error forwarding request to {service_name}: {e}")
        raise CircuitBreakerException(service_name)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    if not await check_rate_limit(request):
        return JSONResponse(
            status_code=429,
            content=create_error_response(
                error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message="Rate limit exceeded",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    
    return await call_next(request)

@app.middleware("http")
async def auth_middleware_handler(request: Request, call_next):
    """Auth middleware handler"""
    # Skip auth for health checks and public endpoints
    if request.url.path in ["/health", "/ready", "/metrics"]:
        return await call_next(request)
    
    # Check if endpoint requires authentication
    if requires_auth(request.url.path):
        try:
            # Extract token from header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Validate token (simplified - in real implementation, you'd validate with auth service)
            token = auth_header.split(" ")[1]
            # For now, just check if token exists
            if not token:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Add user info to request state (simplified)
            request.state.user = {"id": "user-123", "roles": ["user"]}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    return await call_next(request)

def requires_auth(path: str) -> bool:
    """Check if path requires authentication"""
    # Public endpoints
    public_paths = [
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/health",
        "/ready",
        "/metrics"
    ]
    
    return not any(path.startswith(public_path) for public_path in public_paths)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return create_success_response(
        data={
            "status": "healthy",
            "service": "api-gateway",
            "version": "1.0.0",
            "timestamp": time.time()
        },
        message="API Gateway is healthy"
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Check all services
    service_status = {}
    for service_name, service_config in SERVICE_REGISTRY.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_config['url']}{service_config['health_check']}")
                service_status[service_name] = response.status_code == 200
        except:
            service_status[service_name] = False
    
    all_healthy = all(service_status.values())
    
    return create_success_response(
        data={
            "status": "ready" if all_healthy else "not_ready",
            "services": service_status
        },
        message="API Gateway readiness check completed"
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Composite health endpoints
@app.post("/health/analyze-symptoms")
async def analyze_symptoms_composite(request: Request):
    """
    Composite endpoint for symptom analysis.
    Aggregates data from multiple services and provides AI-powered insights.
    """
    try:
        # Get request data
        data = await request.json()
        symptoms = data.get("symptoms", [])
        include_vitals = data.get("include_vitals", True)
        include_medications = data.get("include_medications", True)
        generate_insights = data.get("generate_insights", True)
        
        user = getattr(request.state, 'user', {})
        user_id = user.get("id", "unknown")
        
        # Use AI Reasoning Orchestrator for comprehensive analysis
        orchestrator_config = SERVICE_REGISTRY.get("ai_reasoning_orchestrator")
        if not orchestrator_config:
            raise HTTPException(status_code=503, detail="AI Reasoning service unavailable")
        
        # Create reasoning request
        reasoning_request = {
            "query": f"Analyze symptoms: {', '.join(symptoms)}",
            "reasoning_type": "symptom_analysis",
            "time_window": "24h",
            "data_types": []
        }
        
        if include_vitals:
            reasoning_request["data_types"].append("vitals")
        if include_medications:
            reasoning_request["data_types"].append("medications")
        
        reasoning_request["data_types"].extend(["symptoms", "nutrition", "sleep"])
        
        # Forward to AI Reasoning Orchestrator
        response = await forward_request(
            request=request,
            service_name="ai_reasoning_orchestrator",
            path="/api/v1/reason",
            method="POST",
            data=reasoning_request
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        logger.error(f"Error in composite symptom analysis: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Error analyzing symptoms",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.get("/health/daily-summary")
async def daily_summary_composite(request: Request):
    """
    Composite endpoint for daily health summary.
    Provides unified daily health insights and recommendations.
    """
    try:
        user = getattr(request.state, 'user', {})
        user_id = user.get("id", "unknown")
        
        # Use AI Reasoning Orchestrator for daily summary
        orchestrator_config = SERVICE_REGISTRY.get("ai_reasoning_orchestrator")
        if not orchestrator_config:
            raise HTTPException(status_code=503, detail="AI Reasoning service unavailable")
        
        # Forward to AI Reasoning Orchestrator
        response = await forward_request(
            request=request,
            service_name="ai_reasoning_orchestrator",
            path="/api/v1/insights/daily-summary",
            method="GET"
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        logger.error(f"Error in composite daily summary: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Error generating daily summary",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.post("/health/doctor-report")
async def doctor_report_composite(request: Request):
    """
    Composite endpoint for doctor mode reports.
    Generates comprehensive reports for healthcare providers.
    """
    try:
        # Get request data
        data = await request.json()
        time_window = data.get("time_window", "30d")
        
        user = getattr(request.state, 'user', {})
        user_id = user.get("id", "unknown")
        
        # Use AI Reasoning Orchestrator for doctor report
        orchestrator_config = SERVICE_REGISTRY.get("ai_reasoning_orchestrator")
        if not orchestrator_config:
            raise HTTPException(status_code=503, detail="AI Reasoning service unavailable")
        
        # Forward to AI Reasoning Orchestrator
        response = await forward_request(
            request=request,
            service_name="ai_reasoning_orchestrator",
            path="/api/v1/doctor-mode/report",
            method="POST",
            data={"time_window": time_window}
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        logger.error(f"Error in composite doctor report: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Error generating doctor report",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.post("/health/query")
async def health_query_composite(request: Request):
    """
    Composite endpoint for natural language health queries.
    Accepts questions like "Why do I feel tired today?" and provides AI-powered answers.
    """
    try:
        # Get request data
        data = await request.json()
        question = data.get("question", "")
        time_window = data.get("time_window", "24h")
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        user = getattr(request.state, 'user', {})
        user_id = user.get("id", "unknown")
        
        # Use AI Reasoning Orchestrator for natural language query
        orchestrator_config = SERVICE_REGISTRY.get("ai_reasoning_orchestrator")
        if not orchestrator_config:
            raise HTTPException(status_code=503, detail="AI Reasoning service unavailable")
        
        # Forward to AI Reasoning Orchestrator
        response = await forward_request(
            request=request,
            service_name="ai_reasoning_orchestrator",
            path="/api/v1/query",
            method="POST",
            data={"question": question, "time_window": time_window}
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        logger.error(f"Error in composite health query: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Error processing health query",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.get("/health/unified-dashboard")
async def unified_dashboard_composite(request: Request):
    """
    Composite endpoint for unified health dashboard data.
    Aggregates data from all health services for dashboard display.
    """
    try:
        user = getattr(request.state, 'user', {})
        user_id = user.get("id", "unknown")
        
        # Use GraphQL BFF for unified data access
        bff_config = SERVICE_REGISTRY.get("graphql_bff")
        if not bff_config:
            raise HTTPException(status_code=503, detail="GraphQL BFF service unavailable")
        
        # Forward to GraphQL BFF
        response = await forward_request(
            request=request,
            service_name="graphql_bff",
            path="/api/v1/health/daily-summary",
            method="GET"
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except Exception as e:
        logger.error(f"Error in unified dashboard: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Error loading dashboard data",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

# New service routes
@app.api_route("/ai-reasoning/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def ai_reasoning_service_route(request: Request, path: str):
    """Route requests to AI Reasoning Orchestrator service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="ai_reasoning_orchestrator",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to AI Reasoning Orchestrator: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/graphql/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def graphql_bff_service_route(request: Request, path: str):
    """Route requests to GraphQL BFF service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="graphql_bff",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to GraphQL BFF: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/ai-insights/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def ai_insights_service_route(request: Request, path: str):
    """Route requests to AI Insights service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="ai_insights",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to AI Insights service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/medical-records/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def medical_records_service_route(request: Request, path: str):
    """Route requests to Medical Records service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="medical_records",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to Medical Records service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/nutrition/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def nutrition_service_route(request: Request, path: str):
    """Route requests to Nutrition service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="nutrition",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to Nutrition service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/device-data/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def device_data_service_route(request: Request, path: str):
    """Route requests to Device Data service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="device_data",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to Device Data service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

# Original service routes
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_service_route(request: Request, path: str):
    """Route requests to auth service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="auth",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to auth service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/user-profile/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def user_profile_service_route(request: Request, path: str):
    """Route requests to user profile service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="user_profile",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to user profile service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.api_route("/health-tracking/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def health_tracking_service_route(request: Request, path: str):
    """Route requests to health tracking service"""
    try:
        # Get request body for POST/PUT/PATCH
        data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                data = await request.json()
            except:
                pass
        
        # Forward request
        response = await forward_request(
            request=request,
            service_name="health_tracking",
            path=f"/{path}",
            method=request.method,
            data=data
        )
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except CircuitBreakerException as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
                message=str(e),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Error routing to health tracking service: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )

@app.exception_handler(BaseServiceException)
async def service_exception_handler(request: Request, exc: BaseServiceException):
    """Handle service exceptions"""
    return JSONResponse(
        status_code=400,
        content=create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            error_details=exc.error_details,
            severity=exc.severity,
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=exc.detail,
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code=ErrorCode.UNKNOWN_ERROR,
            message="An unexpected error occurred",
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 