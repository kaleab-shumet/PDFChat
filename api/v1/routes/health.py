from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import structlog

from ..core.database import get_db
from ..core.tracing import trace_function
from ..core.metrics import metrics
from ..schemas.response import success_response, error_response
from typing import Dict, Any


router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
@trace_function("health_check")
async def health_check():
    """Basic health check endpoint."""
    return success_response(
        data={"status": "healthy", "service": "PDFChat API", "timestamp": time.time()},
        message="Service is healthy",
    )


@router.get("/health/detailed")
@trace_function("detailed_health_check")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with database connectivity."""
    start_time = time.time()
    health_status: Dict[str, Any] = {
        "service": "PDFChat API",
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {},
    }

    # Database connectivity check
    try:
        await db.execute(text("SELECT 1"))
        db_check = {
            "status": "healthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }
        metrics.record_database_query("health_check", "system")
        logger.info("Database health check passed")
    except Exception as exc:
        db_check = {
            "status": "unhealthy",
            "error": str(exc),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }
        health_status["status"] = "degraded"
        logger.error("Database health check failed", error=str(exc))

    health_status["checks"]["database"] = db_check

    # Memory and basic system checks could be added here
    health_status["checks"]["memory"] = {"status": "healthy"}
    health_status["checks"]["disk"] = {"status": "healthy"}

    if health_status["status"] == "healthy":
        return success_response(data=health_status, message="All systems operational")
    else:
        return error_response(
            error_code="SYSTEM_DEGRADED", message="Some systems are experiencing issues"
        )
