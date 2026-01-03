"""
E2E test configuration and fixtures.
"""

import pytest_asyncio
import pytest
import httpx
from tests.e2e.utils import UserSession


@pytest_asyncio.fixture
async def api_client():
    """Create an HTTP client for API testing."""
    async with httpx.AsyncClient(
        base_url="http://localhost:8000", timeout=30.0
    ) as client:
        yield client


@pytest_asyncio.fixture
async def health_check(api_client):
    """Ensure API is healthy before running tests."""
    response = await api_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"


@pytest.fixture
def user_session() -> UserSession:
    """Create a fresh user session for each test."""
    return UserSession()
