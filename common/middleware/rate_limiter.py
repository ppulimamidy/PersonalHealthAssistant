"""
Rate Limiting Middleware
Implements rate limiting with Redis backend as per Implementation Guide.
"""

import time
import hashlib
from typing import Optional, Dict, Any, Callable
from functools import wraps
import redis.asyncio as redis
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram

from common.config.settings import get_settings
from common.utils.logging import get_logger


logger = get_logger(__name__)
settings = get_settings()


class RateLimiterMetrics:
    """Metrics for rate limiting"""
    
    def __init__(self):
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Total rate limit hits',
            ['endpoint', 'client_id']
        )
        
        self.rate_limit_requests = Counter(
            'rate_limit_requests_total',
            'Total requests processed by rate limiter',
            ['endpoint', 'client_id']
        )
        
        self.rate_limit_duration = Histogram(
            'rate_limit_duration_seconds',
            'Rate limiting check duration',
            ['endpoint']
        )


class RateLimiter:
    """Rate limiter with Redis backend"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.external_services.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.metrics = RateLimiterMetrics()
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
    
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True,
                max_connections=20
            )
        return self.redis_client
    
    def register_rate_limit(
        self,
        endpoint: str,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        burst_size: int = 10
    ):
        """Register a rate limit for an endpoint"""
        self._rate_limits[endpoint] = {
            "requests_per_minute": requests_per_minute,
            "requests_per_hour": requests_per_hour,
            "requests_per_day": requests_per_day,
            "burst_size": burst_size
        }
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get from X-Forwarded-For header first
        client_ip = request.headers.get("X-Forwarded-For")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        
        # If user is authenticated, use user ID
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Otherwise use IP address
        return f"ip:{client_ip}"
    
    async def check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        start_time = time.time()
        
        try:
            redis_client = await self.get_redis_client()
            
            # Get rate limit configuration
            rate_limit_config = self._rate_limits.get(endpoint, {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "burst_size": 10
            })
            
            # Create keys for different time windows
            current_time = int(time.time())
            minute_key = f"rate_limit:{client_id}:{endpoint}:minute:{current_time // 60}"
            hour_key = f"rate_limit:{client_id}:{endpoint}:hour:{current_time // 3600}"
            day_key = f"rate_limit:{client_id}:{endpoint}:day:{current_time // 86400}"
            
            # Use pipeline for atomic operations
            async with redis_client.pipeline() as pipe:
                # Increment counters
                await pipe.incr(minute_key)
                await pipe.incr(hour_key)
                await pipe.incr(day_key)
                
                # Set expiration for keys
                await pipe.expire(minute_key, 60)
                await pipe.expire(hour_key, 3600)
                await pipe.expire(day_key, 86400)
                
                # Execute pipeline
                results = await pipe.execute()
                
                minute_count, hour_count, day_count = results[:3]
            
            # Check limits
            is_allowed = (
                minute_count <= rate_limit_config["requests_per_minute"] and
                hour_count <= rate_limit_config["requests_per_hour"] and
                day_count <= rate_limit_config["requests_per_day"]
            )
            
            # Update metrics
            duration = time.time() - start_time
            self.metrics.rate_limit_duration.labels(endpoint=endpoint).observe(duration)
            self.metrics.rate_limit_requests.labels(
                endpoint=endpoint, client_id=client_id
            ).inc()
            
            if not is_allowed:
                self.metrics.rate_limit_hits.labels(
                    endpoint=endpoint, client_id=client_id
                ).inc()
            
            return {
                "allowed": is_allowed,
                "minute_count": minute_count,
                "hour_count": hour_count,
                "day_count": day_count,
                "minute_limit": rate_limit_config["requests_per_minute"],
                "hour_limit": rate_limit_config["requests_per_hour"],
                "day_limit": rate_limit_config["requests_per_day"],
                "reset_time": {
                    "minute": (current_time // 60 + 1) * 60,
                    "hour": (current_time // 3600 + 1) * 3600,
                    "day": (current_time // 86400 + 1) * 86400
                }
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request if rate limiting fails
            return {
                "allowed": True,
                "error": "Rate limiting temporarily unavailable"
            }
    
    async def rate_limit_middleware(self, request: Request, call_next):
        """FastAPI middleware for rate limiting"""
        endpoint = request.url.path
        client_id = self.get_client_id(request)
        
        # Check if endpoint has rate limiting configured
        if endpoint not in self._rate_limits:
            return await call_next(request)
        
        # Check rate limit
        rate_limit_result = await self.check_rate_limit(client_id, endpoint)
        
        if not rate_limit_result["allowed"]:
            # Return rate limit exceeded response
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "endpoint": endpoint,
                        "limits": {
                            "minute": rate_limit_result["minute_limit"],
                            "hour": rate_limit_result["hour_limit"],
                            "day": rate_limit_result["day_limit"]
                        },
                        "current_usage": {
                            "minute": rate_limit_result["minute_count"],
                            "hour": rate_limit_result["hour_count"],
                            "day": rate_limit_result["day_count"]
                        },
                        "reset_times": rate_limit_result["reset_time"]
                    }
                }
            )
        
        # Add rate limit info to request state
        request.state.rate_limit_info = rate_limit_result
        
        # Continue with request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Minute-Limit"] = str(rate_limit_result["minute_limit"])
        response.headers["X-RateLimit-Minute-Remaining"] = str(
            max(0, rate_limit_result["minute_limit"] - rate_limit_result["minute_count"])
        )
        response.headers["X-RateLimit-Minute-Reset"] = str(rate_limit_result["reset_time"]["minute"])
        
        response.headers["X-RateLimit-Hour-Limit"] = str(rate_limit_result["hour_limit"])
        response.headers["X-RateLimit-Hour-Remaining"] = str(
            max(0, rate_limit_result["hour_limit"] - rate_limit_result["hour_count"])
        )
        response.headers["X-RateLimit-Hour-Reset"] = str(rate_limit_result["reset_time"]["hour"])
        
        return response


class RateLimitDependency:
    """Dependency for rate limiting specific endpoints"""
    
    def __init__(self, rate_limiter: RateLimiter, endpoint: str):
        self.rate_limiter = rate_limiter
        self.endpoint = endpoint
    
    async def __call__(self, request: Request):
        client_id = self.rate_limiter.get_client_id(request)
        rate_limit_result = await self.rate_limiter.check_rate_limit(
            client_id, self.endpoint
        )
        
        if not rate_limit_result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": rate_limit_result
                }
            )
        
        return rate_limit_result


# Global rate limiter instance
rate_limiter = RateLimiter()


def setup_rate_limiting(app):
    """Setup rate limiting for FastAPI app"""
    # Register default rate limits
    rate_limiter.register_rate_limit("/api/auth/login", requests_per_minute=5)
    rate_limiter.register_rate_limit("/api/auth/register", requests_per_minute=3)
    rate_limiter.register_rate_limit("/api/users", requests_per_minute=30)
    rate_limiter.register_rate_limit("/api/health", requests_per_minute=60)
    
    # Add middleware
    app.middleware("http")(rate_limiter.rate_limit_middleware)
    
    return rate_limiter


def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    requests_per_day: int = 10000
):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        endpoint = f"{func.__module__}.{func.__name__}"
        
        # Register rate limit
        rate_limiter.register_rate_limit(
            endpoint,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day
        )
        
        # Create dependency
        dependency = RateLimitDependency(rate_limiter, endpoint)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be used as a dependency in FastAPI
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Convenience functions for common rate limits
def login_rate_limit():
    """Rate limit for login endpoints"""
    return RateLimitDependency(rate_limiter, "/api/auth/login")


def registration_rate_limit():
    """Rate limit for registration endpoints"""
    return RateLimitDependency(rate_limiter, "/api/auth/register")


def api_rate_limit():
    """General API rate limit"""
    return RateLimitDependency(rate_limiter, "/api")


def health_check_rate_limit():
    """Rate limit for health check endpoints"""
    return RateLimitDependency(rate_limiter, "/api/health")


# Example usage in FastAPI
"""
from fastapi import Depends

@app.post("/auth/login")
async def login(
    credentials: UserLogin,
    rate_limit: dict = Depends(login_rate_limit())
):
    # Rate limiting is automatically applied
    return {"message": "Login successful"}

@app.get("/api/users")
async def get_users(
    rate_limit: dict = Depends(api_rate_limit())
):
    # Rate limiting is automatically applied
    return {"users": []}
"""

class RateLimitingMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app):
        self.app = app
        self.rate_limiter = RateLimiter()
        # Register default rate limits
        self.rate_limiter.register_rate_limit("/api/v1/auth/login", requests_per_minute=5, requests_per_hour=20)
        self.rate_limiter.register_rate_limit("/api/v1/auth/register", requests_per_minute=3, requests_per_hour=10)
        self.rate_limiter.register_rate_limit("/api/v1/auth/", requests_per_minute=60, requests_per_hour=1000)
        self.rate_limiter.register_rate_limit("/health", requests_per_minute=120, requests_per_hour=10000)
        self.rate_limiter.register_rate_limit("/metrics", requests_per_minute=60, requests_per_hour=1000)
    
    async def __call__(self, request: Request, call_next):
        """Process request through rate limiting middleware"""
        return await self.rate_limiter.rate_limit_middleware(request, call_next) 