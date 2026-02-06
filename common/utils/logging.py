"""
Logging Infrastructure
Provides structured logging with different handlers and formatters.
"""

import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
import structlog
from structlog.stdlib import LoggerFactory
import os

from common.config.settings import get_settings

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
            
        user_id = user_id_var.get()
        if user_id:
            log_entry["user_id"] = user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage", "exc_info", 
                          "exc_text", "stack_info"]:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class HealthCheckFilter(logging.Filter):
    """Filter to exclude health check logs from certain handlers"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out health check logs"""
        return not (
            record.name == "uvicorn.access" and 
            "health" in record.getMessage().lower()
        )


class DatabaseFilter(logging.Filter):
    """Filter to handle database-specific logs"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter database logs"""
        return not (
            record.name.startswith("sqlalchemy") and 
            record.levelno < logging.WARNING
        )


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Setup logging configuration"""
    
    settings = get_settings()
    
    # Use provided log level or default from settings
    level = log_level or settings.LOG_LEVEL
    log_level_num = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    # Use environment variable LOGS_DIR or default to ./logs
    logs_dir_str = os.environ.get("LOGS_DIR", "./logs")
    logs_dir = Path(logs_dir_str)
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        # If we can't create the logs directory, disable file logging
        print(f"Warning: Could not create logs directory {logs_dir}: {e}")
        enable_file = False
        logs_dir = Path("./logs")  # Fallback to local directory
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if enable_json else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_num)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_num)
        
        if enable_json:
            console_formatter = StructuredFormatter()
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(HealthCheckFilter())
        root_logger.addHandler(console_handler)
    
    # File handler
    if enable_file:
        if log_file is None:
            log_file = logs_dir / "health_assistant.log"
        
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level_num)
            
            if enable_json:
                file_formatter = StructuredFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create log file {log_file}: {e}")
            enable_file = False
    
    # Error file handler
    if enable_file:
        try:
            error_log_file = logs_dir / "health_assistant_error.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(error_handler)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create error log file: {e}")
    
    # Database handler (separate file for database logs)
    if enable_file:
        try:
            db_log_file = logs_dir / "database.log"
            db_handler = logging.handlers.RotatingFileHandler(
                db_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            db_handler.setLevel(logging.DEBUG)
            db_handler.setFormatter(StructuredFormatter())
            db_handler.addFilter(DatabaseFilter())
            
            # Add database handler to SQLAlchemy logger
            db_logger = logging.getLogger("sqlalchemy")
            db_logger.addHandler(db_handler)
            db_logger.setLevel(logging.DEBUG)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create database log file: {e}")
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


def log_request(
    request_id: str,
    method: str,
    url: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log HTTP request details"""
    logger = get_logger("http.request")
    
    log_data = {
        "request_id": request_id,
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        "user_id": user_id,
        **kwargs
    }
    
    if status_code >= 400:
        logger.warning("HTTP request", **log_data)
    else:
        logger.info("HTTP request", **log_data)


def log_database_operation(
    operation: str,
    table: str,
    duration: float,
    rows_affected: Optional[int] = None,
    **kwargs
) -> None:
    """Log database operation details"""
    logger = get_logger("database.operation")
    
    log_data = {
        "operation": operation,
        "table": table,
        "duration_ms": round(duration * 1000, 2),
        "rows_affected": rows_affected,
        **kwargs
    }
    
    logger.info("Database operation", **log_data)


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Log security-related events"""
    logger = get_logger("security.event")
    
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {},
        **kwargs
    }
    
    logger.warning("Security event", **log_data)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
    **kwargs
) -> None:
    """Log performance metrics"""
    logger = get_logger("performance.metric")
    
    log_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "labels": labels or {},
        **kwargs
    }
    
    logger.info("Performance metric", **log_data)


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log error with context"""
    logger = get_logger("error")
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
        "user_id": user_id,
        "traceback": traceback.format_exc(),
        **kwargs
    }
    
    logger.error("Application error", **log_data)


def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Set request context for logging"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)


# Initialize logging on module import
setup_logging() 