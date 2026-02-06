"""
Base Models for Personal Health Assistant
Common models and base classes used across all services.
"""

from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, validator, ConfigDict
from sqlalchemy import Column, DateTime, String, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.sql import func
from enum import Enum
import traceback

# SQLAlchemy Base
Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields to SQLAlchemy models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    """Mixin for adding UUID primary key to SQLAlchemy models"""
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class MetadataMixin:
    """Mixin for adding metadata field to SQLAlchemy models"""
    model_metadata = Column(JSONB, nullable=True)


# Pydantic Base Models
class BasePydanticModel(BaseModel):
    """Base Pydantic model with common configuration"""
    
    model_config = ConfigDict(
        # Use UUID for id fields
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        },
        # Allow population by field name
        populate_by_name=True,
        # Validate assignment
        validate_assignment=True,
        # Use enum values
        use_enum_values=True,
        # Allow extra fields
        extra="ignore"
    )


class TimestampModel(BasePydanticModel):
    """Base model with timestamp fields"""
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_timestamps(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return v
        return v


class UUIDModel(BasePydanticModel):
    """Base model with UUID primary key"""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")


class BaseEntityModel(UUIDModel, TimestampModel):
    """Base model for all entities"""
    pass


class SoftDeleteModel(BasePydanticModel):
    """Base model with soft delete functionality"""
    is_deleted: bool = Field(False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")


class MetadataModel(BasePydanticModel):
    """Base model with extra_metadata field"""
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Response Models
class ResponseModel(BasePydanticModel):
    """Base response model"""
    success: bool = Field(True, description="Success flag")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Any] = Field(None, description="Response data")


class PaginatedResponseModel(BasePydanticModel):
    """Paginated response model"""
    items: List[Any] = Field(default_factory=list, description="List of items")
    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page number")
    size: int = Field(20, description="Page size")
    pages: int = Field(0, description="Total number of pages")
    has_next: bool = Field(False, description="Has next page")
    has_prev: bool = Field(False, description="Has previous page")


class ErrorResponseModel(BasePydanticModel):
    """Error response model"""
    success: bool = Field(False, description="Success flag")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


# Request Models
class PaginationModel(BasePydanticModel):
    """Pagination request model"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        if v > 100:
            return 100
        return v


class SortModel(BasePydanticModel):
    """Sorting request model"""
    field: str = Field(..., description="Field to sort by")
    order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class FilterModel(BasePydanticModel):
    """Filter request model"""
    field: str = Field(..., description="Field to filter by")
    operator: str = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")


class SearchModel(BasePydanticModel):
    """Search request model"""
    query: str = Field(..., description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")
    fuzzy: bool = Field(False, description="Enable fuzzy search")


# Health and Status Models
class HealthCheckModel(BasePydanticModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime in seconds")
    checks: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Health checks")


class ServiceStatusModel(BasePydanticModel):
    """Service status model"""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime")
    last_check: datetime = Field(..., description="Last health check")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


# Event Models
class EventModel(BasePydanticModel):
    """Base event model"""
    event_id: UUID = Field(default_factory=uuid4, description="Event ID")
    event_type: str = Field(..., description="Event type")
    event_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(..., description="Event source")
    user_id: Optional[UUID] = Field(None, description="User ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Event metadata")


class EventLogModel(EventModel):
    """Event log model for database storage"""
    id: UUID = Field(default_factory=uuid4, description="Log entry ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Audit Models
class AuditLogModel(BasePydanticModel):
    """Audit log model"""
    id: UUID = Field(default_factory=uuid4, description="Audit log ID")
    user_id: Optional[UUID] = Field(None, description="User ID")
    action_type: str = Field(..., description="Action type")
    resource_type: str = Field(..., description="Resource type")
    resource_id: Optional[UUID] = Field(None, description="Resource ID")
    action_data: Optional[Dict[str, Any]] = Field(None, description="Action data")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Notification Models
class NotificationModel(BasePydanticModel):
    """Notification model"""
    id: UUID = Field(default_factory=uuid4, description="Notification ID")
    user_id: UUID = Field(..., description="User ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$", description="Notification priority")
    is_read: bool = Field(False, description="Read status")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = Field(None, description="Read timestamp")


# File Models
class FileModel(BasePydanticModel):
    """File model"""
    id: UUID = Field(default_factory=uuid4, description="File ID")
    filename: str = Field(..., description="File name")
    original_filename: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    file_path: str = Field(..., description="File path")
    url: Optional[str] = Field(None, description="File URL")
    checksum: Optional[str] = Field(None, description="File checksum")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="File metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Validation Models
class ValidationErrorModel(BasePydanticModel):
    """Validation error model"""
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Validation message")
    code: Optional[str] = Field(None, description="Error code")


class ValidationResultModel(BasePydanticModel):
    """Validation result model"""
    is_valid: bool = Field(..., description="Validation result")
    errors: List[ValidationErrorModel] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationErrorModel] = Field(default_factory=list, description="Validation warnings")


# Utility Models
class IDListModel(BasePydanticModel):
    """Model for list of IDs"""
    ids: List[UUID] = Field(..., description="List of IDs")


class CountModel(BasePydanticModel):
    """Model for count responses"""
    count: int = Field(..., description="Count value")


class StatusModel(BasePydanticModel):
    """Model for status responses"""
    status: str = Field(..., description="Status value")
    message: Optional[str] = Field(None, description="Status message")


# Time Range Models
class TimeRangeModel(BasePydanticModel):
    """Time range model"""
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v


class DateRangeModel(BasePydanticModel):
    """Date range model"""
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


# Export/Import Models
class ExportModel(BasePydanticModel):
    """Export model"""
    format: str = Field(..., pattern="^(json|csv|xml|pdf)$", description="Export format")
    filters: Optional[Dict[str, Any]] = Field(None, description="Export filters")
    fields: Optional[List[str]] = Field(None, description="Fields to export")
    include_metadata: bool = Field(True, description="Include metadata")


class ImportModel(BasePydanticModel):
    """Import model"""
    format: str = Field(..., pattern="^(json|csv|xml)$", description="Import format")
    data: Any = Field(..., description="Import data")
    options: Optional[Dict[str, Any]] = Field(None, description="Import options")
    validate_only: bool = Field(False, description="Validate only, don't import")


# Cache Models
class CacheEntryModel(BasePydanticModel):
    """Cache entry model"""
    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Cache value")
    ttl: int = Field(300, description="Time to live in seconds")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


# Rate Limiting Models
class RateLimitModel(BasePydanticModel):
    """Rate limit model"""
    key: str = Field(..., description="Rate limit key")
    limit: int = Field(..., description="Request limit")
    window: int = Field(..., description="Time window in seconds")
    current: int = Field(0, description="Current request count")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="Reset time")


# Metrics Models
class MetricModel(BasePydanticModel):
    """Metric model"""
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Metric unit")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Metric metadata")


class MetricSummaryModel(BasePydanticModel):
    """Metric summary model"""
    name: str = Field(..., description="Metric name")
    count: int = Field(..., description="Number of measurements")
    min_value: float = Field(..., description="Minimum value")
    max_value: float = Field(..., description="Maximum value")
    avg_value: float = Field(..., description="Average value")
    sum_value: float = Field(..., description="Sum of values")
    unit: Optional[str] = Field(None, description="Metric unit")
    time_range: Optional[TimeRangeModel] = Field(None, description="Time range")


class ErrorCode(str, Enum):
    """Standardized error codes for all services"""
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    
    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Circuit breaker
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    
    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BaseResponseModel(BaseModel):
    """Base response model for all API responses"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class SuccessResponse(BaseResponseModel):
    """Standard success response"""
    success: bool = True
    data: Optional[Any] = Field(None, description="Response data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": "123", "name": "example"},
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req-123"
            }
        }
    )

class ErrorResponse(BaseResponseModel):
    """Standard error response"""
    success: bool = False
    error_code: ErrorCode = Field(..., description="Error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    severity: ErrorSeverity = Field(ErrorSeverity.MEDIUM, description="Error severity level")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "Resource not found",
                "error_code": "RESOURCE_NOT_FOUND",
                "error_details": {"resource_type": "user", "resource_id": "123"},
                "severity": "medium",
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req-123",
                "trace_id": "trace-456"
            }
        }
    )

class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(0, description="Total number of pages")
    has_next: bool = Field(False, description="Whether there is a next page")
    has_prev: bool = Field(False, description="Whether there is a previous page")

    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        if 'total' in values and 'size' in values:
            return (values['total'] + values['size'] - 1) // values['size']
        return v
    
    @validator('has_next', always=True)
    def calculate_has_next(cls, v, values):
        if 'page' in values and 'pages' in values:
            return values['page'] < values['pages']
        return v
    
    @validator('has_prev', always=True)
    def calculate_has_prev(cls, v, values):
        if 'page' in values:
            return values['page'] > 1
        return v

class PaginatedResponse(SuccessResponse):
    """Paginated response with data and pagination info"""
    data: List[Any] = Field(..., description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Data retrieved successfully",
                "data": [{"id": "1", "name": "item1"}, {"id": "2", "name": "item2"}],
                "pagination": {
                    "page": 1,
                    "size": 10,
                    "total": 25,
                    "pages": 3,
                    "has_next": True,
                    "has_prev": False
                },
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req-123"
            }
        }
    )

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    checks: Dict[str, bool] = Field(..., description="Health check results")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "auth-service",
                "version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z",
                "checks": {
                    "database": True,
                    "redis": True,
                    "external_api": True
                },
                "uptime": 3600.5
            }
        }
    )

class MetricsResponse(BaseModel):
    """Metrics response for monitoring"""
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    metrics: Dict[str, Any] = Field(..., description="Service metrics")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service": "auth-service",
                "timestamp": "2024-01-01T00:00:00Z",
                "metrics": {
                    "requests_total": 1000,
                    "requests_per_second": 10.5,
                    "error_rate": 0.02,
                    "response_time_avg": 0.15
                }
            }
        }
    )

class BaseEntity(BaseModel):
    """Base entity model with common fields"""
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the entity is active")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class BaseCreateModel(BaseModel):
    """Base model for creation requests"""
    pass

class BaseUpdateModel(BaseModel):
    """Base model for update requests"""
    pass

class BaseFilterModel(BaseModel):
    """Base model for filtering requests"""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Field(None, description="Search term")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v and v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()

class BaseSortModel(BaseModel):
    """Base model for sorting"""
    field: str = Field(..., description="Field to sort by")
    order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

class BaseSearchModel(BaseModel):
    """Base model for search"""
    query: str = Field(..., description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")
    fuzzy: bool = Field(default=False, description="Whether to use fuzzy search")

# Error handling utilities
def create_error_response(
    error_code: ErrorCode,
    message: str,
    error_details: Optional[Dict[str, Any]] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None
) -> dict:
    """Create a standardized error response as a dict"""
    return ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        error_details=error_details,
        severity=severity,
        request_id=request_id,
        trace_id=trace_id
    ).model_dump()

def create_success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    request_id: Optional[str] = None
) -> SuccessResponse:
    """Create a standardized success response"""
    return SuccessResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id
    )

def create_paginated_response(
    data: List[Any],
    page: int,
    size: int,
    total: int,
    message: str = "Data retrieved successfully",
    request_id: Optional[str] = None
) -> PaginatedResponse:
    """Create a standardized paginated response"""
    pagination = PaginationInfo(
        page=page,
        size=size,
        total=total
    )
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        pagination=pagination,
        request_id=request_id
    )

# Exception classes
class BaseServiceException(Exception):
    """Base exception for all service exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        error_details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ):
        self.message = message
        self.error_code = error_code
        self.error_details = error_details or {}
        self.severity = severity
        super().__init__(message)

class ValidationException(BaseServiceException):
    """Exception for validation errors"""
    def __init__(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            error_details=error_details,
            severity=ErrorSeverity.MEDIUM
        )

class ResourceNotFoundException(BaseServiceException):
    """Exception for resource not found errors"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id {resource_id} not found",
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            error_details={"resource_type": resource_type, "resource_id": resource_id},
            severity=ErrorSeverity.MEDIUM
        )

class AuthenticationException(BaseServiceException):
    """Exception for authentication errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            severity=ErrorSeverity.HIGH
        )

class AuthorizationException(BaseServiceException):
    """Exception for authorization errors"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            severity=ErrorSeverity.HIGH
        )

class DatabaseException(BaseServiceException):
    """Exception for database errors"""
    def __init__(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            error_details=error_details,
            severity=ErrorSeverity.HIGH
        )

class ExternalServiceException(BaseServiceException):
    """Exception for external service errors"""
    def __init__(self, service_name: str, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"External service {service_name} error: {message}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            error_details={"service_name": service_name, **error_details} if error_details else {"service_name": service_name},
            severity=ErrorSeverity.HIGH
        )

class RateLimitException(BaseServiceException):
    """Exception for rate limiting errors"""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="Rate limit exceeded",
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            error_details={"retry_after": retry_after} if retry_after else None,
            severity=ErrorSeverity.MEDIUM
        )

class CircuitBreakerException(BaseServiceException):
    """Exception for circuit breaker errors"""
    def __init__(self, service_name: str):
        super().__init__(
            message=f"Circuit breaker is open for {service_name}",
            error_code=ErrorCode.CIRCUIT_BREAKER_OPEN,
            error_details={"service_name": service_name},
            severity=ErrorSeverity.HIGH
        ) 