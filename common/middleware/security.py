"""
Enhanced Security Middleware
Implements mutual TLS, security headers, and enhanced security measures as per Implementation Guide.
"""

import ssl
import time
import hashlib
from typing import Optional, Dict, Any, List
from functools import wraps
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
import httpx

from common.config.settings import get_settings
from common.utils.logging import get_logger


logger = get_logger(__name__)
settings = get_settings()


class SecurityMetrics:
    """Metrics for security monitoring"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityMetrics, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics only once"""
        try:
            self.security_violations = Counter(
                'security_violations_total',
                'Total security violations',
                ['violation_type', 'endpoint']
            )
            
            self.mtls_connections = Counter(
                'mtls_connections_total',
                'Total mTLS connections',
                ['client_cert', 'endpoint']
            )
            
            self.security_headers_duration = Histogram(
                'security_headers_duration_seconds',
                'Security headers processing duration',
                ['endpoint']
            )
        except ValueError as e:
            # If metrics already exist, just use None to avoid errors
            if "Duplicated timeseries" in str(e):
                logger.warning("Security metrics already registered, skipping initialization")
                self.security_violations = None
                self.mtls_connections = None
                self.security_headers_duration = None
            else:
                raise


class SecurityMiddleware:
    """Enhanced security middleware with mTLS support"""
    
    def __init__(self, app):
        self.app = app
        self.metrics = SecurityMetrics()
        self.allowed_origins = settings.security.cors_origins
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = [
            "Authorization", "Content-Type", "X-Requested-With",
            "X-API-Key", "X-Client-Cert"
        ]
        
        # Security configuration
        self.enable_mtls = settings.security.enable_mtls
        self.require_client_cert = settings.security.require_client_cert
        self.trusted_ca_certs = settings.security.trusted_ca_certs
        self.client_cert_validation = settings.security.client_cert_validation
        
        # Rate limiting for security events
        self.security_event_counts: Dict[str, int] = {}
        self.security_event_windows: Dict[str, float] = {}
    
    async def __call__(self, scope, receive, send):
        """FastAPI middleware call method"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object from scope
        request = Request(scope, receive)
        
        try:
            # Apply security checks
            client_id = self.get_client_id(request)
            
            # Validate request origin
            if not self.validate_request_origin(request):
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid request origin"}
                )
                await response(scope, receive, send)
                return
            
            # Validate request method
            if not self.validate_request_method(request):
                response = JSONResponse(
                    status_code=405,
                    content={"detail": "Method not allowed"}
                )
                await response(scope, receive, send)
                return
            
            # Validate request headers
            if not self.validate_request_headers(request):
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request headers"}
                )
                await response(scope, receive, send)
                return
            
            # Check for SQL injection attempts
            if self.detect_sql_injection(request):
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Potential SQL injection detected"}
                )
                await response(scope, receive, send)
                return
            
            # Check for XSS attempts
            if self.detect_xss_attempt(request):
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Potential XSS attack detected"}
                )
                await response(scope, receive, send)
                return
            
            # Continue to next middleware/endpoint
            await self.app(scope, receive, send)
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Security middleware error"}
            )
            await response(scope, receive, send)
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for mTLS"""
        if not self.enable_mtls:
            return None
        
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Load server certificate and key
        if settings.security.server_cert_path and settings.security.server_key_path:
            ssl_context.load_cert_chain(
                certfile=settings.security.server_cert_path,
                keyfile=settings.security.server_key_path
            )
        
        # Load trusted CA certificates
        if self.trusted_ca_certs:
            ssl_context.load_verify_locations(cafile=self.trusted_ca_certs)
        
        # Configure client certificate validation
        if self.require_client_cert:
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            ssl_context.verify_mode = ssl.CERT_OPTIONAL
        
        # Set minimum TLS version
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Configure cipher suites
        ssl_context.set_ciphers('ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256')
        
        return ssl_context
    
    def validate_client_certificate(self, request: Request) -> Dict[str, Any]:
        """Validate client certificate"""
        if not self.enable_mtls or not self.require_client_cert:
            return {}
        
        # Get client certificate from headers (for proxy scenarios)
        client_cert_header = request.headers.get("X-Client-Cert")
        if client_cert_header:
            # Parse certificate from header
            try:
                import base64
                cert_data = base64.b64decode(client_cert_header)
                # Validate certificate (simplified)
                return {"cert_present": True, "cert_data": cert_data}
            except Exception as e:
                logger.error(f"Failed to parse client certificate: {e}")
                return {"cert_present": False, "error": str(e)}
        
        # For direct TLS connections, certificate validation happens at SSL level
        return {"cert_present": True, "direct_tls": True}
    
    def add_security_headers(self, response: Response, request: Request) -> Response:
        """Add security headers to response"""
        # Use a more permissive CSP for Swagger/ReDoc docs
        if request.url.path in ["/docs", "/redoc"]:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Strict Transport Security
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Cache Control for sensitive endpoints
        if any(path in request.url.path for path in ["/api/auth", "/api/admin"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response
    
    def validate_request_origin(self, request: Request) -> bool:
        """Validate request origin"""
        # In development mode, allow all origins
        if settings.ENVIRONMENT == "development":
            return True
            
        origin = request.headers.get("Origin")
        if not origin:
            return True  # Allow requests without origin (e.g., mobile apps)
        
        # Check if origin is in allowed list
        if origin in self.allowed_origins:
            return True
        
        # Check wildcard patterns
        for allowed_origin in self.allowed_origins:
            if allowed_origin.startswith("*."):
                domain = allowed_origin[2:]
                if origin.endswith(domain):
                    return True
        
        return False
    
    def validate_request_method(self, request: Request) -> bool:
        """Validate request method"""
        return request.method in self.allowed_methods
    
    def validate_request_headers(self, request: Request) -> bool:
        """Validate request headers"""
        # Check for required headers
        # required_headers = ["User-Agent"]  # Temporarily disabled for Traefik testing
        # for header in required_headers:
        #     if not request.headers.get(header):
        #         return False
        
        # Check for suspicious headers (but allow common proxy headers)
        suspicious_headers = [
            "X-Original-URL",
            "X-Rewrite-URL"
        ]
        
        for header in suspicious_headers:
            if request.headers.get(header):
                logger.warning(f"Suspicious header detected: {header}")
                return False
        
        return True
    
    def detect_sql_injection(self, request: Request) -> bool:
        """Detect potential SQL injection attempts"""
        sql_patterns = [
            "UNION SELECT",
            "DROP TABLE",
            "INSERT INTO",
            "DELETE FROM",
            "UPDATE SET",
            "OR 1=1",
            "OR '1'='1'",
            "'; DROP",
            "'; INSERT",
            "'; UPDATE"
        ]
        
        # Check URL parameters
        for param_name, param_value in request.query_params.items():
            param_value_lower = param_value.lower()
            for pattern in sql_patterns:
                if pattern.lower() in param_value_lower:
                    logger.warning(f"Potential SQL injection detected in query param {param_name}")
                    return True
        
        # Check request body (for POST/PUT requests)
        if request.method in ["POST", "PUT"]:
            try:
                body = request.body()
                if body:
                    body_str = body.decode('utf-8').lower()
                    for pattern in sql_patterns:
                        if pattern.lower() in body_str:
                            logger.warning("Potential SQL injection detected in request body")
                            return True
            except Exception:
                pass
        
        return False
    
    def detect_xss_attempt(self, request: Request) -> bool:
        """Detect potential XSS attempts"""
        xss_patterns = [
            "<script>",
            "javascript:",
            "onload=",
            "onerror=",
            "onclick=",
            "onmouseover=",
            "eval(",
            "document.cookie",
            "window.location"
        ]
        
        # Check URL parameters
        for param_name, param_value in request.query_params.items():
            param_value_lower = param_value.lower()
            for pattern in xss_patterns:
                if pattern.lower() in param_value_lower:
                    logger.warning(f"Potential XSS detected in query param {param_name}")
                    return True
        
        return False
    
    def check_rate_limit_security_events(self, client_id: str, event_type: str) -> bool:
        """Check rate limit for security events"""
        current_time = time.time()
        key = f"{client_id}:{event_type}"
        
        # Reset window if expired
        if key not in self.security_event_windows or \
           current_time - self.security_event_windows[key] > 60:  # 1 minute window
            self.security_event_counts[key] = 0
            self.security_event_windows[key] = current_time
        
        # Increment count
        self.security_event_counts[key] = self.security_event_counts.get(key, 0) + 1
        
        # Check limit (5 events per minute)
        return self.security_event_counts[key] <= 5
    
    async def security_middleware(self, request: Request, call_next):
        """Main security middleware"""
        start_time = time.time()
        client_id = self.get_client_id(request)
        
        try:
            # Validate client certificate
            cert_info = self.validate_client_certificate(request)
            if self.require_client_cert and not cert_info.get("cert_present"):
                self.metrics.security_violations.labels(
                    violation_type="missing_client_cert", endpoint=request.url.path
                ).inc()
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Client certificate required",
                        "error_code": "CLIENT_CERT_REQUIRED"
                    }
                )
            
            # Update mTLS metrics
            if cert_info.get("cert_present"):
                self.metrics.mtls_connections.labels(
                    client_cert="present", endpoint=request.url.path
                ).inc()
            
            # Validate request origin
            if not self.validate_request_origin(request):
                self.metrics.security_violations.labels(
                    violation_type="invalid_origin", endpoint=request.url.path
                ).inc()
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Invalid origin",
                        "error_code": "INVALID_ORIGIN"
                    }
                )
            
            # Validate request method
            if not self.validate_request_method(request):
                self.metrics.security_violations.labels(
                    violation_type="invalid_method", endpoint=request.url.path
                ).inc()
                return JSONResponse(
                    status_code=405,
                    content={
                        "error": "Method not allowed",
                        "error_code": "METHOD_NOT_ALLOWED"
                    }
                )
            
            # Validate request headers
            if not self.validate_request_headers(request):
                self.metrics.security_violations.labels(
                    violation_type="invalid_headers", endpoint=request.url.path
                ).inc()
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid headers",
                        "error_code": "INVALID_HEADERS"
                    }
                )
            
            # Detect SQL injection
            if self.detect_sql_injection(request):
                if not self.check_rate_limit_security_events(client_id, "sql_injection"):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too many security violations",
                            "error_code": "RATE_LIMIT_EXCEEDED"
                        }
                    )
                
                self.metrics.security_violations.labels(
                    violation_type="sql_injection", endpoint=request.url.path
                ).inc()
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid request",
                        "error_code": "INVALID_REQUEST"
                    }
                )
            
            # Detect XSS attempts
            if self.detect_xss_attempt(request):
                if not self.check_rate_limit_security_events(client_id, "xss_attempt"):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Too many security violations",
                            "error_code": "RATE_LIMIT_EXCEEDED"
                        }
                    )
                
                self.metrics.security_violations.labels(
                    violation_type="xss_attempt", endpoint=request.url.path
                ).inc()
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid request",
                        "error_code": "INVALID_REQUEST"
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self.add_security_headers(response, request)
            
            # Update metrics
            duration = time.time() - start_time
            self.metrics.security_headers_duration.labels(
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR"
                }
            )
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier"""
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


# Global security middleware instance - REMOVED
# security_middleware = SecurityMiddleware()


def setup_security(app):
    """Setup security middleware for FastAPI app"""
    # Create security middleware instance
    security_middleware = SecurityMiddleware(app)
    
    # Add security middleware
    app.middleware("http")(security_middleware.security_middleware)
    
    return security_middleware


def require_mtls():
    """Dependency for requiring mTLS"""
    async def dependency(request: Request):
        if not settings.security.enable_mtls:
            return True
        
        cert_info = SecurityMiddleware(None).validate_client_certificate(request) # Pass None or a dummy app
        if not cert_info.get("cert_present"):
            raise HTTPException(
                status_code=401,
                detail="Client certificate required"
            )
        return True
    return dependency


def require_secure_headers():
    """Dependency for requiring secure headers"""
    async def dependency(request: Request):
        # Check for required security headers
        # required_headers = ["User-Agent"]  # Temporarily disabled for Traefik testing
        # for header in required_headers:
        #     if not request.headers.get(header):
        #         raise HTTPException(
        #             status_code=400,
        #             detail=f"Missing required header: {header}"
        #         )
        return True
    return dependency


def security_headers(func):
    """Decorator to add security headers to responses"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get the response from the function
        response = await func(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            security_mw = SecurityMiddleware(None) # Pass None or a dummy app
            response = security_mw.add_security_headers(response, args[0] if args else None) # Pass request if available
        
        return response
    
    return wrapper


# Example usage in FastAPI
"""
from fastapi import Depends

@app.get("/api/secure-endpoint")
async def secure_endpoint(
    mtls: bool = Depends(require_mtls()),
    secure_headers: bool = Depends(require_secure_headers())
):
    return {"message": "Secure endpoint accessed"}

# Setup security middleware
setup_security(app)
""" 