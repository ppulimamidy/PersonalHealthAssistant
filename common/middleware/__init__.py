"""
Middleware module for Personal Health Assistant
"""

from .auth import (
    AuthMiddleware,
    get_optional_user,
    get_current_user,
    require_auth,
    require_roles,
    require_permissions
)

from .error_handling import (
    ErrorHandlingMiddleware,
    SecurityErrorMiddleware,
    PerformanceMonitoringMiddleware,
    setup_error_handlers,
    create_error_response,
    log_and_raise_error
)

__all__ = [
    # Auth middleware
    "AuthMiddleware",
    "get_optional_user",
    "get_current_user",
    "require_auth",
    "require_roles",
    "require_permissions",
    # Error handling middleware
    "ErrorHandlingMiddleware",
    "SecurityErrorMiddleware", 
    "PerformanceMonitoringMiddleware",
    "setup_error_handlers",
    "create_error_response",
    "log_and_raise_error"
] 