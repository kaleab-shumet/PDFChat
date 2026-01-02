from pydantic import BaseModel, field_serializer
from typing import Generic, TypeVar, Optional, Any, Dict, List
from datetime import datetime, timezone

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper for all endpoints."""

    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[Dict[str, str]] = None
    timestamp: datetime
    request_id: Optional[str] = None

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    success: bool = True
    message: str
    data: List[T]
    meta: PaginationMeta
    error: Optional[Dict[str, str]] = None
    timestamp: datetime
    request_id: Optional[str] = None


# Helper functions to create standardized responses
def success_response(
    data: Any = None, message: str = "Success", request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }


def error_response(
    error_code: str, message: str, request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create an error response."""
    return {
        "success": False,
        "message": "Request failed",
        "data": None,
        "error": {"error_code": error_code, "message": message},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }


def paginated_response(
    data: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: str = "Success",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a paginated response."""
    total_pages = (total + per_page - 1) // per_page

    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }


# Common error responses
def user_exists_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response("USER_EXISTS", "Email already registered", request_id)


def invalid_credentials_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response(
        "INVALID_CREDENTIALS", "Invalid email or password", request_id
    )


def user_inactive_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response("USER_INACTIVE", "User account is inactive", request_id)


def project_not_found_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response("PROJECT_NOT_FOUND", "Project not found", request_id)


def missing_auth_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response("MISSING_AUTH", "Missing Authorization header", request_id)


def invalid_auth_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response(
        "INVALID_AUTH", "Invalid Authorization header format", request_id
    )


def invalid_token_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response("INVALID_TOKEN", "Invalid or expired token", request_id)


def not_authenticated_error(request_id: Optional[str] = None) -> Dict[str, Any]:
    return error_response("NOT_AUTHENTICATED", "Authentication required", request_id)
