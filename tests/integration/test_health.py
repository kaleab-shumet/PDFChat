import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_basic_health_check(self, async_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await async_client.get("/api/v1/health")

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Service is healthy"
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert data["data"]["service"] == "PDFChat API"
        assert "timestamp" in data["data"]

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, async_client: AsyncClient):
        """Test detailed health check endpoint."""
        response = await async_client.get("/api/v1/health/detailed")

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        health_data = data["data"]
        assert health_data["service"] == "PDFChat API"
        assert health_data["status"] == "healthy"
        assert "checks" in health_data

        # Check that database check is present
        checks = health_data["checks"]
        assert "database" in checks
        assert checks["database"]["status"] == "healthy"
        assert "response_time_ms" in checks["database"]

        # Other system checks
        assert "memory" in checks
        assert "disk" in checks

    @pytest.mark.asyncio
    async def test_health_endpoints_no_auth_required(self, async_client: AsyncClient):
        """Test that health endpoints don't require authentication."""
        # Test without any headers
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

        response = await async_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
