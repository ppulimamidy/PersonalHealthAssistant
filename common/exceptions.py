"""
Common Exceptions

This module contains custom exception classes used throughout the Personal Health Assistant application.
"""

from typing import Optional, Dict, Any


class HealthAssistantException(Exception):
    """Base exception class for all Health Assistant exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(HealthAssistantException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.table = table
        super().__init__(message, details)


class ValidationError(HealthAssistantException):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, details: Optional[Dict[str, Any]] = None):
        self.field = field
        self.value = value
        super().__init__(message, details)


class AuthenticationError(HealthAssistantException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        super().__init__(message, details)


class AuthorizationError(HealthAssistantException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str, user_id: Optional[str] = None, resource: Optional[str] = None, action: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        self.resource = resource
        self.action = action
        super().__init__(message, details)


class NotFoundError(HealthAssistantException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, details)


class ConflictError(HealthAssistantException):
    """Exception raised when there's a conflict with existing data."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, details)


class ConfigurationError(HealthAssistantException):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.config_key = config_key
        super().__init__(message, details)


class ServiceError(HealthAssistantException):
    """Exception raised for service-related errors."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.operation = operation
        super().__init__(message, details)


class ExternalServiceError(HealthAssistantException):
    """Exception raised for external service errors."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.status_code = status_code
        super().__init__(message, details)


class DataIntegrityError(HealthAssistantException):
    """Exception raised for data integrity errors."""
    
    def __init__(self, message: str, constraint: Optional[str] = None, table: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.constraint = constraint
        self.table = table
        super().__init__(message, details)


class PrivacyError(HealthAssistantException):
    """Exception raised for privacy-related errors."""
    
    def __init__(self, message: str, data_type: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.data_type = data_type
        self.user_id = user_id
        super().__init__(message, details)


class ConsentError(HealthAssistantException):
    """Exception raised for consent-related errors."""
    
    def __init__(self, message: str, consent_type: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.consent_type = consent_type
        self.user_id = user_id
        super().__init__(message, details)


class RateLimitError(HealthAssistantException):
    """Exception raised for rate limiting errors."""
    
    def __init__(self, message: str, limit: Optional[int] = None, window: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        self.limit = limit
        self.window = window
        super().__init__(message, details)


class HealthDataError(HealthAssistantException):
    """Exception raised for health data-related errors."""
    
    def __init__(self, message: str, data_type: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.data_type = data_type
        self.user_id = user_id
        super().__init__(message, details)


class NotificationError(HealthAssistantException):
    """Exception raised for notification-related errors."""
    
    def __init__(self, message: str, notification_type: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.notification_type = notification_type
        self.user_id = user_id
        super().__init__(message, details)


class AuditError(HealthAssistantException):
    """Exception raised for audit-related errors."""
    
    def __init__(self, message: str, audit_type: Optional[str] = None, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.audit_type = audit_type
        self.user_id = user_id
        super().__init__(message, details) 