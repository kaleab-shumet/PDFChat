import pytest
from httpx import AsyncClient

from api.v1.models.user import User


class TestUserRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, async_client: AsyncClient, valid_user_data: dict
    ):
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register", json=valid_user_data
        )

        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["message"] == "User registered successfully"

        user_data = data["data"]
        assert user_data["email"] == valid_user_data["email"]
        assert user_data["is_active"] is True
        assert "id" in user_data
        assert "created_at" in user_data
        # Password should not be returned
        assert "password" not in user_data
        assert "hashed_password" not in user_data

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test registration with existing email."""
        user_data = {
            "email": test_user.email,  # Use existing user's email
            "password": "newpassword",
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "USER_EXISTS"
        assert "already registered" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email."""
        user_data = {"email": "not-an-email", "password": "password123"}

        response = await async_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_user_missing_fields(self, async_client: AsyncClient):
        """Test registration with missing fields."""
        response = await async_client.post("/api/v1/auth/register", json={})

        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, async_client: AsyncClient, test_user: User, valid_login_data: dict
    ):
        """Test successful login."""
        response = await async_client.post("/api/v1/auth/login", json=valid_login_data)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Login successful"

        token_data = data["data"]
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert isinstance(token_data["access_token"], str)
        assert len(token_data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}

        response = await async_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test login with wrong password."""
        login_data = {"email": test_user.email, "password": "wrongpassword"}

        response = await async_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, async_client: AsyncClient, test_inactive_user: User
    ):
        """Test login with inactive user."""
        login_data = {"email": test_inactive_user.email, "password": "testpassword"}

        response = await async_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "USER_INACTIVE"

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, async_client: AsyncClient):
        """Test login with missing fields."""
        response = await async_client.post("/api/v1/auth/login", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, async_client: AsyncClient):
        """Test login with invalid email format."""
        login_data = {"email": "not-an-email", "password": "password"}

        response = await async_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 422


class TestAuthenticationFlow:
    """Test end-to-end authentication flow."""

    @pytest.mark.asyncio
    async def test_register_then_login_flow(self, async_client: AsyncClient):
        """Test complete registration and login flow."""
        # Register a new user
        user_data = {"email": "flowtest@example.com", "password": "flowpassword123"}

        register_response = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        # Login with the same credentials
        login_response = await async_client.post("/api/v1/auth/login", json=user_data)
        assert login_response.status_code == 200

        login_data = login_response.json()
        assert "access_token" in login_data["data"]

        # Verify token works (when we implement protected endpoints)
        token = login_data["data"]["access_token"]
        # This would test a protected endpoint once we have one
        # headers = {"Authorization": f"Bearer {token}"}
        # For now, just verify the token structure is correct
        assert len(token.split(".")) == 3  # JWT has 3 parts
