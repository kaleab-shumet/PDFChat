from datetime import datetime

from api.v1.schemas.response import (
    success_response,
    error_response,
    paginated_response,
    user_exists_error,
    invalid_credentials_error,
    project_not_found_error,
)


class TestResponseHelpers:
    """Test response helper functions."""

    def test_success_response(self):
        """Test success response creation."""
        data = {"id": "123", "name": "Test"}
        response = success_response(
            data=data, message="Operation successful", request_id="req_123"
        )

        assert response["success"] is True
        assert response["message"] == "Operation successful"
        assert response["data"] == data
        assert response["error"] is None
        assert response["request_id"] == "req_123"
        assert isinstance(response["timestamp"], str)
        # Check it's a valid ISO format datetime
        datetime.fromisoformat(response["timestamp"])

    def test_success_response_defaults(self):
        """Test success response with defaults."""
        response = success_response()

        assert response["success"] is True
        assert response["message"] == "Success"
        assert response["data"] is None
        assert response["error"] is None
        assert response["request_id"] is None
        assert isinstance(response["timestamp"], str)
        # Check it's a valid ISO format datetime
        datetime.fromisoformat(response["timestamp"])

    def test_error_response(self):
        """Test error response creation."""
        response = error_response(
            error_code="USER_NOT_FOUND", message="User not found", request_id="req_123"
        )

        assert response["success"] is False
        assert response["message"] == "Request failed"
        assert response["data"] is None
        assert response["error"]["error_code"] == "USER_NOT_FOUND"
        assert response["error"]["message"] == "User not found"
        assert response["request_id"] == "req_123"
        assert isinstance(response["timestamp"], str)
        # Check it's a valid ISO format datetime
        datetime.fromisoformat(response["timestamp"])

    def test_paginated_response(self):
        """Test paginated response creation."""
        data = [{"id": "1"}, {"id": "2"}]
        response = paginated_response(
            data=data,
            page=1,
            per_page=10,
            total=25,
            message="Data retrieved",
            request_id="req_123",
        )

        assert response["success"] is True
        assert response["message"] == "Data retrieved"
        assert response["data"] == data
        assert response["error"] is None
        assert response["request_id"] == "req_123"

        # Check pagination metadata
        meta = response["meta"]
        assert meta["page"] == 1
        assert meta["per_page"] == 10
        assert meta["total"] == 25
        assert meta["total_pages"] == 3  # ceil(25/10)
        assert meta["has_next"] is True
        assert meta["has_prev"] is False

    def test_paginated_response_last_page(self):
        """Test paginated response for last page."""
        response = paginated_response(
            data=[{"id": "21"}], page=3, per_page=10, total=21
        )

        meta = response["meta"]
        assert meta["page"] == 3
        assert meta["total_pages"] == 3
        assert meta["has_next"] is False
        assert meta["has_prev"] is True


class TestCommonErrorResponses:
    """Test common error response functions."""

    def test_user_exists_error(self):
        """Test user exists error response."""
        response = user_exists_error("req_123")

        assert response["success"] is False
        assert response["error"]["error_code"] == "USER_EXISTS"
        assert response["error"]["message"] == "Email already registered"
        assert response["request_id"] == "req_123"

    def test_invalid_credentials_error(self):
        """Test invalid credentials error response."""
        response = invalid_credentials_error("req_123")

        assert response["success"] is False
        assert response["error"]["error_code"] == "INVALID_CREDENTIALS"
        assert response["error"]["message"] == "Invalid email or password"
        assert response["request_id"] == "req_123"

    def test_project_not_found_error(self):
        """Test project not found error response."""
        response = project_not_found_error("req_123")

        assert response["success"] is False
        assert response["error"]["error_code"] == "PROJECT_NOT_FOUND"
        assert response["error"]["message"] == "Project not found"
        assert response["request_id"] == "req_123"

    def test_error_responses_without_request_id(self):
        """Test error responses without request ID."""
        response = user_exists_error()

        assert response["success"] is False
        assert response["error"]["error_code"] == "USER_EXISTS"
        assert response["request_id"] is None
