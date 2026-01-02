from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog
import uuid

from ..core.auth import verify_token

logger = structlog.get_logger(__name__)


def setup_auth(app: FastAPI, exclude_from_auth=[]) -> None:
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Skip authentication for excluded paths
        if request.url.path in exclude_from_auth:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        request_id = getattr(request.state, "request_id", None)

        if not auth_header:
            logger.warning("Missing Authorization header", path=request.url.path)
            from ..schemas.response import missing_auth_error

            return JSONResponse(
                status_code=401,
                content=missing_auth_error(request_id),
            )

        # Extract token from "Bearer <token>" format
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid auth scheme")
        except ValueError:
            logger.warning("Invalid Authorization header format", path=request.url.path)
            from ..schemas.response import invalid_auth_error

            return JSONResponse(
                status_code=401,
                content=invalid_auth_error(request_id),
            )

        # Verify token
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid or expired token", path=request.url.path)
            from ..schemas.response import invalid_token_error

            return JSONResponse(
                status_code=401,
                content=invalid_token_error(request_id),
            )

        # Add user info to request state
        request.state.user_id = uuid.UUID(payload.get("sub"))
        request.state.user_email = payload.get("email")

        logger.info(
            "User authenticated", user_id=request.state.user_id, path=request.url.path
        )

        return await call_next(request)
