from fastapi import FastAPI
import uvicorn

from api.v1.router import router as v1_router
from api.v1.core.config import settings
from api.v1.core.logging import configure_logging
from api.v1.core.metrics import setup_metrics_middleware
from api.v1.core.tracing import setup_tracing
from api.v1.middlewares.logging import setup_logging_middleware
from api.v1.middlewares.security import setup_security_middleware
from api.v1.middlewares.auth import setup_auth

# Configure observability
configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Set up tracing
setup_tracing(app)

# Security middleware
setup_security_middleware(app)

# Metrics middleware
setup_metrics_middleware(app)

# Logging middleware
setup_logging_middleware(app)

# Authentication middleware (exclude health checks, auth endpoints, and metrics)
setup_auth(
    app,
    exclude_from_auth=[
        "/api/v1/health",
        "/api/v1/health/detailed",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
    ],
)

# Include routers
app.include_router(v1_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
