"""
Error Handling Middleware
Provides centralized error handling and consistent error responses.
"""

import traceback
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from jose import JWTError
from pydantic import ValidationError

from common.utils.logging import get_logger, log_error, log_security_event
from common.models.base import ErrorResponseModel
from common.services.base import ServiceError, NotFoundError, ValidationError as ServiceValidationError, DuplicateError

logger = get_logger(__name__)


class ErrorHandlingMiddleware:
    """Centralized error handling middleware"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, scope, receive, send):
        """FastAPI middleware call method"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object from scope
        request = Request(scope, receive)
        
        try:
            # Create a call_next function that works with the new signature
            async def call_next(req):
                # This is a simplified approach - in practice, we'd need to handle the response properly
                await self.app(scope, receive, send)
                return None  # Placeholder response
            
            response = await call_next(request)
            if response:
                await response(scope, receive, send)
        except Exception as exc:
            error_response = await self.handle_exception(request, exc)
            await error_response(scope, receive, send)
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of exceptions"""
        
        # Get request context
        request_id = getattr(request.state, 'request_id', 'unknown')
        user_id = getattr(request.state, 'user_id', None)
        
        # Log the error
        log_error(
            error=exc,
            context={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_id": str(user_id) if user_id else None,
                "client_ip": request.client.host if request.client else None
            },
            user_id=str(user_id) if user_id else None
        )
        
        # Handle different exception types
        if isinstance(exc, HTTPException):
            return self._handle_http_exception(exc, request_id)
        elif isinstance(exc, RequestValidationError):
            return self._handle_validation_error(exc, request_id)
        elif isinstance(exc, ServiceError):
            return self._handle_service_error(exc, request_id)
        elif isinstance(exc, SQLAlchemyError):
            return self._handle_database_error(exc, request_id)
        elif isinstance(exc, JWTError):
            return self._handle_jwt_error(exc, request_id)
        elif isinstance(exc, ValidationError):
            return self._handle_pydantic_error(exc, request_id)
        else:
            return self._handle_generic_error(exc, request_id)
    
    def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle HTTP exceptions"""
        error_response = ErrorResponseModel(
            success=False,
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
            headers=exc.headers
        )
    
    def _handle_validation_error(self, exc: RequestValidationError, request_id: str) -> JSONResponse:
        """Handle request validation errors"""
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = ErrorResponseModel(
            success=False,
            error="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={
                "request_id": request_id,
                "validation_errors": error_details
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    def _handle_service_error(self, exc: ServiceError, request_id: str) -> JSONResponse:
        """Handle service layer errors"""
        status_code = self._get_status_code_for_service_error(exc)
        
        error_response = ErrorResponseModel(
            success=False,
            error=exc.message,
            error_code=exc.error_code,
            details={
                "request_id": request_id,
                **exc.details
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )
    
    def _handle_database_error(self, exc: SQLAlchemyError, request_id: str) -> JSONResponse:
        """Handle database errors"""
        if isinstance(exc, IntegrityError):
            error_message = "Database integrity constraint violated"
            error_code = "DATABASE_INTEGRITY_ERROR"
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, OperationalError):
            error_message = "Database operation failed"
            error_code = "DATABASE_OPERATIONAL_ERROR"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            error_message = "Database error occurred"
            error_code = "DATABASE_ERROR"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        error_response = ErrorResponseModel(
            success=False,
            error=error_message,
            error_code=error_code,
            details={
                "request_id": request_id,
                "database_error": str(exc)
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )
    
    def _handle_jwt_error(self, exc: JWTError, request_id: str) -> JSONResponse:
        """Handle JWT errors"""
        error_response = ErrorResponseModel(
            success=False,
            error="Invalid authentication token",
            error_code="JWT_ERROR",
            details={
                "request_id": request_id,
                "jwt_error": str(exc)
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.model_dump(),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    def _handle_pydantic_error(self, exc: ValidationError, request_id: str) -> JSONResponse:
        """Handle Pydantic validation errors"""
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = ErrorResponseModel(
            success=False,
            error="Data validation failed",
            error_code="VALIDATION_ERROR",
            details={
                "request_id": request_id,
                "validation_errors": error_details
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )
    
    def _handle_generic_error(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle generic/unexpected errors"""
        # Log security event for unexpected errors
        log_security_event(
            event_type="unexpected_error",
            details={
                "request_id": request_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc()
            }
        )
        
        error_response = ErrorResponseModel(
            success=False,
            error="An unexpected error occurred",
            error_code="INTERNAL_ERROR",
            details={
                "request_id": request_id,
                "error_type": type(exc).__name__
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
    
    def _get_status_code_for_service_error(self, exc: ServiceError) -> int:
        """Get appropriate HTTP status code for service error"""
        if isinstance(exc, NotFoundError):
            return status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ServiceValidationError):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exc, DuplicateError):
            return status.HTTP_409_CONFLICT
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR


class SecurityErrorMiddleware:
    """Middleware to handle security-related errors"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            
            # Log security events for certain response codes
            if response.status_code in [401, 403, 429]:
                user_id = getattr(request.state, 'user_id', None)
                log_security_event(
                    event_type="security_response",
                    user_id=str(user_id) if user_id else None,
                    ip_address=request.client.host if request.client else None,
                    details={
                        "method": request.method,
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "request_id": getattr(request.state, 'request_id', 'unknown')
                    }
                )
            
            return response
        except Exception as exc:
            # Re-raise to be handled by main error handling middleware
            raise


class PerformanceMonitoringMiddleware:
    """Middleware to monitor request performance"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        import time
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                user_id = getattr(request.state, 'user_id', None)
                self.logger.warning(
                    "Slow request detected",
                    duration=duration,
                    method=request.method,
                    url=str(request.url),
                    user_id=str(user_id) if user_id else None,
                    request_id=getattr(request.state, 'request_id', 'unknown')
                )
            
            # Add performance headers
            response.headers["X-Request-Duration"] = str(duration)
            
            return response
        except Exception as exc:
            duration = time.time() - start_time
            
            # Log failed requests
            user_id = getattr(request.state, 'user_id', None)
            self.logger.error(
                "Request failed",
                duration=duration,
                method=request.method,
                url=str(request.url),
                user_id=str(user_id) if user_id else None,
                error=str(exc),
                request_id=getattr(request.state, 'request_id', 'unknown')
            )
            
            raise


# Global middleware instances - removed to prevent import errors
# These should be instantiated when adding to FastAPI app
# error_handling_middleware = ErrorHandlingMiddleware()
# security_error_middleware = SecurityErrorMiddleware()
# performance_monitoring_middleware = PerformanceMonitoringMiddleware()


def setup_error_handlers(app):
    """Setup error handlers for FastAPI app"""
    
    # Create a temporary instance for error handling
    error_handler = ErrorHandlingMiddleware(app)
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return await error_handler.handle_exception(request, exc)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await error_handler.handle_exception(request, exc)
    
    @app.exception_handler(ServiceError)
    async def service_exception_handler(request: Request, exc: ServiceError):
        return await error_handler.handle_exception(request, exc)
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        return await error_handler.handle_exception(request, exc)
    
    @app.exception_handler(JWTError)
    async def jwt_exception_handler(request: Request, exc: JWTError):
        return await error_handler.handle_exception(request, exc)
    
    @app.exception_handler(ValidationError)
    async def pydantic_exception_handler(request: Request, exc: ValidationError):
        return await error_handler.handle_exception(request, exc)
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return await error_handler.handle_exception(request, exc)


# Utility functions for error handling
def create_error_response(
    message: str,
    error_code: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response"""
    error_response = ErrorResponseModel(
        success=False,
        error=message,
        error_code=error_code,
        details=details or {}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


def log_and_raise_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
):
    """Log an error and raise it"""
    log_error(error, context, user_id)
    raise error 