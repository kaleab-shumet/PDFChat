import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
import structlog

from .config import settings

logger = structlog.get_logger(__name__)

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["result"],  # success, invalid_credentials, invalid_token, etc.
)

database_queries_total = Counter(
    "database_queries_total", "Total database queries", ["operation", "table"]
)

user_registrations_total = Counter(
    "user_registrations_total", "Total user registrations"
)

project_operations_total = Counter(
    "project_operations_total",
    "Total project operations",
    ["operation"],  # create, read, update, delete
)


class MetricsCollector:
    """Centralized metrics collection."""

    @staticmethod
    def record_http_request(
        method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics."""
        http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    @staticmethod
    def record_auth_attempt(result: str):
        """Record authentication attempt."""
        auth_attempts_total.labels(result=result).inc()

    @staticmethod
    def record_database_query(operation: str, table: str):
        """Record database query."""
        database_queries_total.labels(operation=operation, table=table).inc()

    @staticmethod
    def record_user_registration():
        """Record user registration."""
        user_registrations_total.inc()

    @staticmethod
    def record_project_operation(operation: str):
        """Record project operation."""
        project_operations_total.labels(operation=operation).inc()


def setup_metrics_middleware(app: FastAPI) -> None:
    """Set up metrics collection middleware."""

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        if not settings.ENABLE_METRICS:
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Extract endpoint pattern instead of full path for better grouping
            endpoint = request.url.path
            if hasattr(request.state, "route"):
                endpoint = request.state.route.path

            MetricsCollector.record_http_request(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration=duration,
            )

            return response

        except Exception:
            duration = time.time() - start_time

            MetricsCollector.record_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration,
            )

            raise

    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Global metrics collector instance
metrics = MetricsCollector()
