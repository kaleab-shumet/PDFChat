"""
E2E tests for authentication flow.
"""

import pytest
import httpx
import uuid
from tests.e2e.utils import UserSession


@pytest.mark.asyncio
class TestAuthFlow:
    """Test complete authentication workflows."""

    async def test_complete_auth_flow(
        self, api_client: httpx.AsyncClient, user_session: UserSession, health_check
    ):
        """Test complete authentication flow from registration to token usage."""
        # Generate unique test data
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {"email": test_email, "password": "testpassword123"}

        # Step 1: Register user
        register_response = await api_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["success"] is True
        assert register_data["data"]["email"] == test_email
        assert "id" in register_data["data"]
        assert register_data["data"]["is_active"] is True

        # Store user data
        user_session.email = test_email
        user_session.user_id = register_data["data"]["id"]

        # Step 2: Test duplicate registration fails
        duplicate_response = await api_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert duplicate_response.status_code == 400
        duplicate_data = duplicate_response.json()
        assert duplicate_data["success"] is False
        assert duplicate_data["error"]["error_code"] == "USER_EXISTS"

        # Step 3: Login user
        login_response = await api_client.post("/api/v1/auth/login", json=user_data)
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["success"] is True
        assert "access_token" in login_data["data"]
        assert login_data["data"]["token_type"] == "bearer"

        # Store token for next step
        user_session.access_token = login_data["data"]["access_token"]

        # Step 4: Use token to get user info
        profile_response = await api_client.get(
            "/api/v1/auth/me", headers=user_session.headers
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["success"] is True
        assert profile_data["data"]["email"] == test_email
        assert profile_data["data"]["id"] == user_session.user_id
        assert profile_data["data"]["is_active"] is True

    @pytest.mark.parametrize(
        "email,password,expected_error",
        [
            ("nonexistent@example.com", "wrongpassword", "INVALID_CREDENTIALS"),
            (
                "invalid-email",
                "password123",
                "VALIDATION_ERROR",
            ),  # This might fail validation before reaching auth
        ],
    )
    async def test_invalid_login_attempts(
        self,
        api_client: httpx.AsyncClient,
        email: str,
        password: str,
        expected_error: str,
    ):
        """Test various invalid login scenarios."""
        login_data = {"email": email, "password": password}

        response = await api_client.post("/api/v1/auth/login", json=login_data)

        # Either validation error (422) or authentication error (401)
        assert response.status_code in [401, 422]
        if response.status_code == 401:
            data = response.json()
            assert data["success"] is False
            assert expected_error in data["error"]["error_code"]

    async def test_unauthorized_access(self, api_client: httpx.AsyncClient):
        """Test that endpoints require authentication."""
        response = await api_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "MISSING_AUTH"

    async def test_invalid_token_access(self, api_client: httpx.AsyncClient):
        """Test access with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_here"}

        response = await api_client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "INVALID_TOKEN" in data["error"]["error_code"]
