"""
Shared Prometheus Metrics Middleware for all PersonalHealthAssistant services.

Usage in any service's main.py:
    from common.middleware.prometheus_metrics import setup_prometheus_metrics
    setup_prometheus_metrics(app, service_name="my-service")

This will:
1. Add request count, duration, and active request metrics
2. Add a /metrics endpoint
3. Track errors and exceptions
"""

import time
from typing import Optional

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)

from common.utils.logging import get_logger

logger = get_logger(__name__)

# Registry to track which services have been registered (avoid duplicates)
_registered_services = set()


def _get_or_create_metric(metric_class, name, description, labelnames=None):
    """Get existing metric or create a new one (handles re-registration)."""
    try:
        return metric_class(name, description, labelnames or [])
    except ValueError:
        # Already registered - find and return it
        for collector in REGISTRY._names_to_collectors.values():
            if hasattr(collector, "_name") and collector._name == name:
                return collector
        # Fallback: create with a unique suffix
        return metric_class(name, description, labelnames or [])


def setup_prometheus_metrics(
    app: FastAPI, service_name: str, prefix: Optional[str] = None
) -> dict:
    """
    Setup Prometheus metrics for a FastAPI service.

    Args:
        app: FastAPI application instance
        service_name: Name of the service (e.g., "auth-service")
        prefix: Optional prefix for metric names (defaults to service_name with hyphens replaced)

    Returns:
        dict with metric objects for custom use
    """
    if service_name in _registered_services:
        logger.warning(f"Prometheus metrics already registered for {service_name}")
        return {}

    metric_prefix = prefix or service_name.replace("-", "_").replace(" ", "_")

    # Standard metrics
    request_count = _get_or_create_metric(
        Counter,
        f"{metric_prefix}_requests_total",
        f"Total HTTP requests for {service_name}",
        ["method", "endpoint", "status_code"],
    )

    request_duration = _get_or_create_metric(
        Histogram,
        f"{metric_prefix}_request_duration_seconds",
        f"HTTP request duration in seconds for {service_name}",
        ["method", "endpoint"],
    )

    active_requests = _get_or_create_metric(
        Gauge,
        f"{metric_prefix}_active_requests",
        f"Number of active requests for {service_name}",
    )

    error_count = _get_or_create_metric(
        Counter,
        f"{metric_prefix}_errors_total",
        f"Total errors for {service_name}",
        ["error_type"],
    )

    # Service info metric
    try:
        service_info = Info(
            f"{metric_prefix}_service", f"Service information for {service_name}"
        )
        service_info.info(
            {
                "service_name": service_name,
                "version": getattr(app, "version", "1.0.0"),
            }
        )
    except ValueError:
        pass  # Already registered

    # Middleware to track metrics
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        active_requests.inc()
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Normalize path to avoid high cardinality
            path = request.url.path
            # Collapse UUID-like segments
            import re

            path = re.sub(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                "{id}",
                path,
            )
            # Collapse numeric segments
            path = re.sub(r"/\d+(?=/|$)", "/{id}", path)

            request_count.labels(
                method=request.method,
                endpoint=path,
                status_code=str(response.status_code),
            ).inc()

            request_duration.labels(method=request.method, endpoint=path).observe(
                duration
            )

            return response

        except Exception as e:
            error_count.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            active_requests.dec()

    # Add /metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        """Expose Prometheus metrics."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    _registered_services.add(service_name)

    logger.info(f"Prometheus metrics configured for {service_name}")

    return {
        "request_count": request_count,
        "request_duration": request_duration,
        "active_requests": active_requests,
        "error_count": error_count,
    }
