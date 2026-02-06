"""
OpenTelemetry Configuration for Distributed Tracing
Implements distributed tracing across all services as per Implementation Guide.
"""

import os
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
# from opentelemetry.exporter.prometheus import PrometheusExporter  # Removed: use prometheus_client directly
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
# Note: Kafka instrumentation not available in current OpenTelemetry version
# from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.context import Context
from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import Status, StatusCode

from common.config.settings import get_settings


class OpenTelemetryConfig:
    """OpenTelemetry configuration manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        self._tracer = None
        self._meter = None
    
    def configure_tracing(self, service_name: str, service_version: str = "1.0.0"):
        """Configure distributed tracing"""
        if not self.settings.monitoring.enable_tracing:
            return
        
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
            "service.namespace": "health_assistant",
            "deployment.environment": self.settings.development.environment
        })
        
        # Create tracer provider
        self.tracer_provider = TracerProvider(
            resource=resource,
            sampler=TraceIdRatioBased(self.settings.monitoring.trace_sampling_rate)
        )
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=self.settings.monitoring.jaeger_host,
            agent_port=self.settings.monitoring.jaeger_port,
        )
        
        # Add batch span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        self.tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get tracer
        self._tracer = trace.get_tracer(service_name)
        
        return self._tracer
    
    def configure_metrics(self, service_name: str):
        """Configure metrics collection (use prometheus_client for FastAPI metrics endpoint)"""
        if not self.settings.monitoring.enable_metrics:
            return
        
        # Create meter provider
        self.meter_provider = MeterProvider()
        # NOTE: For FastAPI, expose /metrics endpoint using prometheus_client directly.
        # OpenTelemetry PrometheusExporter is not used here due to compatibility issues.
        metrics.set_meter_provider(self.meter_provider)
        self._meter = metrics.get_meter(service_name)
        return self._meter
    
    def instrument_fastapi(self, app, service_name: str):
        """Instrument FastAPI application"""
        if not self.settings.monitoring.enable_tracing:
            return
        
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=self.tracer_provider,
            meter_provider=self.meter_provider
        )
    
    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy engine"""
        if not self.settings.monitoring.enable_tracing:
            return
        
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            tracer_provider=self.tracer_provider
        )
    
    def instrument_httpx(self):
        """Instrument HTTPX client"""
        if not self.settings.monitoring.enable_tracing:
            return
        
        HTTPXClientInstrumentor().instrument(
            tracer_provider=self.tracer_provider
        )
    
    def instrument_redis(self):
        """Instrument Redis client"""
        if not self.settings.monitoring.enable_tracing:
            return
        
        RedisInstrumentor().instrument(
            tracer_provider=self.tracer_provider
        )
    
    def get_tracer(self, service_name: str = None):
        """Get tracer instance"""
        if not self._tracer:
            service_name = service_name or "health_assistant"
            self._tracer = trace.get_tracer(service_name)
        return self._tracer
    
    def get_meter(self, service_name: str = None):
        """Get meter instance"""
        if not self._meter:
            service_name = service_name or "health_assistant"
            self._meter = metrics.get_meter(service_name)
        return self._meter
    
    def create_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL, **kwargs):
        """Create a span for tracing"""
        if not self.settings.monitoring.enable_tracing:
            return None
        
        tracer = self.get_tracer()
        return tracer.start_span(name, kind=kind, **kwargs)
    
    def create_counter(self, name: str, description: str = "", unit: str = ""):
        """Create a counter metric"""
        if not self.settings.monitoring.enable_metrics:
            return None
        
        meter = self.get_meter()
        return meter.create_counter(name, description=description, unit=unit)
    
    def create_histogram(self, name: str, description: str = "", unit: str = ""):
        """Create a histogram metric"""
        if not self.settings.monitoring.enable_metrics:
            return None
        
        meter = self.get_meter()
        return meter.create_histogram(name, description=description, unit=unit)
    
    def create_gauge(self, name: str, description: str = "", unit: str = ""):
        """Create a gauge metric"""
        if not self.settings.monitoring.enable_metrics:
            return None
        
        meter = self.get_meter()
        return meter.create_up_down_counter(name, description=description, unit=unit)


# Global OpenTelemetry configuration instance
ot_config = OpenTelemetryConfig()


def configure_opentelemetry(app, service_name: str, service_version: str = "1.0.0"):
    """Configure OpenTelemetry for a FastAPI application"""
    # Configure tracing
    ot_config.configure_tracing(service_name, service_version)
    
    # Configure metrics
    ot_config.configure_metrics(service_name)
    
    # Instrument FastAPI
    ot_config.instrument_fastapi(app, service_name)
    
    # Instrument other components
    ot_config.instrument_httpx()
    ot_config.instrument_redis()
    
    return ot_config


def get_tracer(service_name: str = None):
    """Get tracer instance"""
    return ot_config.get_tracer(service_name)


def get_meter(service_name: str = None):
    """Get meter instance"""
    return ot_config.get_meter(service_name)


def trace_function(name: str, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to trace function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not ot_config.settings.monitoring.enable_tracing:
                return func(*args, **kwargs)
            
            tracer = get_tracer()
            with tracer.start_as_current_span(name, kind=kind) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_async_function(name: str, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to trace async function execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not ot_config.settings.monitoring.enable_tracing:
                return await func(*args, **kwargs)
            
            tracer = get_tracer()
            with tracer.start_as_current_span(name, kind=kind) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def setup_telemetry():
    """Setup telemetry for the application"""
    # This function is called during application startup
    # The actual configuration is done in configure_opentelemetry
    # This is a placeholder for backward compatibility
    pass 