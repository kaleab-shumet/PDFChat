from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from fastapi import FastAPI
import structlog

from .config import settings

logger = structlog.get_logger(__name__)


def setup_tracing(app: FastAPI) -> None:
    """Set up OpenTelemetry tracing."""

    # Disable tracing in test environments to avoid logging errors on shutdown
    import os
    import sys

    if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in " ".join(sys.argv):
        logger.info("Tracing disabled in test environment")
        return

    if not settings.ENABLE_TRACING:
        logger.info("Tracing disabled")
        return

    # Set up the tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()

    # Set up console exporter for development
    # In production, you'd use OTLP exporter to send to Jaeger/Zipkin
    console_exporter = ConsoleSpanExporter()
    span_processor = BatchSpanProcessor(console_exporter)
    tracer_provider.add_span_processor(span_processor)  # type: ignore[attr-defined]

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()

    logger.info("Tracing configured with console exporter")


def get_tracer(name: str):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def trace_function(operation_name: str):
    """Decorator to trace function calls."""

    def decorator(func):
        import functools
        import asyncio

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = get_tracer(__name__)
                with tracer.start_as_current_span(operation_name) as span:
                    # Add function name as attribute
                    span.set_attribute("function.name", func.__name__)

                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("function.result", "success")
                        return result
                    except Exception as exc:
                        span.set_attribute("function.result", "error")
                        span.set_attribute("function.error", str(exc))
                        raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = get_tracer(__name__)
                with tracer.start_as_current_span(operation_name) as span:
                    span.set_attribute("function.name", func.__name__)

                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("function.result", "success")
                        return result
                    except Exception as exc:
                        span.set_attribute("function.result", "error")
                        span.set_attribute("function.error", str(exc))
                        raise

            return sync_wrapper

    return decorator
