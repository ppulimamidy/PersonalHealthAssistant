"""
OpenTelemetry Configuration for Distributed Tracing
Implements distributed tracing across all services as per Implementation Guide.
"""

import os
from typing import Optional


def configure_opentelemetry(app, service_name: str):
    """Configure OpenTelemetry tracing for a FastAPI service."""
    from common.config.settings import get_settings

    settings = get_settings()

    if not getattr(settings, "TRACING_ENABLED", False):
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create(
            {"service.name": service_name, "service.version": "1.0.0"}
        )
        provider = TracerProvider(resource=resource)

        jaeger_endpoint = getattr(settings, "JAEGER_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=jaeger_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)

        # Optional instrumentations
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument()
        except Exception:
            pass
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            HTTPXClientInstrumentor().instrument()
        except Exception:
            pass
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor

            RedisInstrumentor().instrument()
        except Exception:
            pass
    except ImportError:
        pass  # OpenTelemetry not installed


# ---------------------------------------------------------------------------
# Legacy helpers kept for backward compatibility
# ---------------------------------------------------------------------------


class OpenTelemetryConfig:
    """OpenTelemetry configuration manager (legacy)"""

    def __init__(self):
        from common.config.settings import get_settings

        self.settings = get_settings()
        self.tracer_provider: Optional[object] = None
        self.meter_provider: Optional[object] = None
        self._tracer = None
        self._meter = None

    def configure_tracing(self, service_name: str, service_version: str = "1.0.0"):
        """Configure distributed tracing"""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            resource = Resource.create(
                {
                    "service.name": service_name,
                    "service.version": service_version,
                    "service.namespace": "health_assistant",
                }
            )

            self.tracer_provider = TracerProvider(resource=resource)

            jaeger_endpoint = getattr(
                self.settings, "JAEGER_ENDPOINT", "http://localhost:4317"
            )
            exporter = OTLPSpanExporter(endpoint=jaeger_endpoint)
            self.tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(self.tracer_provider)

            self._tracer = trace.get_tracer(service_name)
            return self._tracer
        except ImportError:
            return None

    def configure_metrics(self, service_name: str):
        """Configure metrics collection"""
        try:
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider

            self.meter_provider = MeterProvider()
            metrics.set_meter_provider(self.meter_provider)
            self._meter = metrics.get_meter(service_name)
            return self._meter
        except ImportError:
            return None

    def instrument_fastapi(self, app, service_name: str):
        """Instrument FastAPI application"""
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=self.tracer_provider,
                meter_provider=self.meter_provider,
            )
        except ImportError:
            pass

    def instrument_sqlalchemy(self, engine=None):
        """Instrument SQLAlchemy engine"""
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            kwargs = {"tracer_provider": self.tracer_provider}
            if engine is not None:
                kwargs["engine"] = engine
            SQLAlchemyInstrumentor().instrument(**kwargs)
        except ImportError:
            pass

    def instrument_httpx(self):
        """Instrument HTTPX client"""
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            HTTPXClientInstrumentor().instrument(tracer_provider=self.tracer_provider)
        except ImportError:
            pass

    def instrument_redis(self):
        """Instrument Redis client"""
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor

            RedisInstrumentor().instrument(tracer_provider=self.tracer_provider)
        except ImportError:
            pass

    def get_tracer(self, service_name: str = None):
        """Get tracer instance"""
        if not self._tracer:
            try:
                from opentelemetry import trace

                service_name = service_name or "health_assistant"
                self._tracer = trace.get_tracer(service_name)
            except ImportError:
                return None
        return self._tracer

    def get_meter(self, service_name: str = None):
        """Get meter instance"""
        if not self._meter:
            try:
                from opentelemetry import metrics

                service_name = service_name or "health_assistant"
                self._meter = metrics.get_meter(service_name)
            except ImportError:
                return None
        return self._meter

    def create_span(self, name: str, kind=None, **kwargs):
        """Create a span for tracing"""
        tracer = self.get_tracer()
        if tracer is None:
            return None
        return tracer.start_span(name, kind=kind, **kwargs)

    def create_counter(self, name: str, description: str = "", unit: str = ""):
        """Create a counter metric"""
        meter = self.get_meter()
        if meter is None:
            return None
        return meter.create_counter(name, description=description, unit=unit)

    def create_histogram(self, name: str, description: str = "", unit: str = ""):
        """Create a histogram metric"""
        meter = self.get_meter()
        if meter is None:
            return None
        return meter.create_histogram(name, description=description, unit=unit)

    def create_gauge(self, name: str, description: str = "", unit: str = ""):
        """Create a gauge metric"""
        meter = self.get_meter()
        if meter is None:
            return None
        return meter.create_up_down_counter(name, description=description, unit=unit)


# Global OpenTelemetry configuration instance
ot_config = OpenTelemetryConfig()


def get_tracer(service_name: str = None):
    """Get tracer instance"""
    return ot_config.get_tracer(service_name)


def get_meter(service_name: str = None):
    """Get meter instance"""
    return ot_config.get_meter(service_name)


def trace_function(name: str, kind=None):
    """Decorator to trace function execution"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)
            with tracer.start_as_current_span(name, kind=kind) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def trace_async_function(name: str, kind=None):
    """Decorator to trace async function execution"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer is None:
                return await func(*args, **kwargs)
            with tracer.start_as_current_span(name, kind=kind) as span:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def setup_telemetry():
    """Setup telemetry for the application (backward compatibility placeholder)"""
    pass
