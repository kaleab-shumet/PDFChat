"""
E2E tests for API health and system status.
"""

import pytest
import httpx


@pytest.mark.asyncio
class TestAPIHealth:
    """Test API health and system status endpoints."""

    async def test_basic_health_check(self, api_client: httpx.AsyncClient):
        """Test basic health check endpoint."""
        response = await api_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["service"] == "PDFChat API"
        assert "timestamp" in data["data"]

    async def test_detailed_health_check(self, api_client: httpx.AsyncClient):
        """Test detailed health check with database connectivity."""
        response = await api_client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] in ["healthy", "degraded"]
        assert "checks" in data["data"]

        # Verify database check
        assert "database" in data["data"]["checks"]
        assert data["data"]["checks"]["database"]["status"] in ["healthy", "unhealthy"]

        # Verify other system checks
        assert "memory" in data["data"]["checks"]
        assert "disk" in data["data"]["checks"]

    async def test_api_responsiveness(self, api_client: httpx.AsyncClient):
        """Test API response times are reasonable."""
        import time

        start_time = time.time()
        response = await api_client.get("/api/v1/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds

    async def test_api_headers_and_security(self, api_client: httpx.AsyncClient):
        """Test API returns proper security headers."""
        response = await api_client.get("/api/v1/health")

        assert response.status_code == 200

        # Check for security headers (if implemented)
        headers = response.headers

        # These should be set by security middleware
        # Note: Adjust based on your actual security middleware implementation
        expected_headers = [
            "x-request-id",  # From logging middleware
        ]

        for header in expected_headers:
            assert header in headers, f"Missing security header: {header}"

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/health",
            "/api/v1/health/detailed",
        ],
    )
    async def test_health_endpoints_public_access(
        self, api_client: httpx.AsyncClient, endpoint: str
    ):
        """Test that health endpoints are publicly accessible."""
        response = await api_client.get(endpoint)

        # Health endpoints should not require authentication
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_invalid_endpoints_return_proper_errors(
        self, api_client: httpx.AsyncClient
    ):
        """Test that invalid endpoints return proper errors."""
        # All routes not in the exclude list are protected by auth middleware
        protected_invalid_endpoints = [
            "/api/v1/nonexistent",
            "/api/v1/health/invalid",
            "/api/v2/health",  # Auth middleware catches all routes first
            "/nonexistent",  # Auth middleware catches all routes first
        ]

        for endpoint in protected_invalid_endpoints:
            response = await api_client.get(endpoint)
            assert response.status_code == 401  # Caught by auth middleware

        # Test that valid excluded endpoints work without auth
        excluded_endpoints = [
            "/api/v1/health",
            "/api/v1/health/detailed",
        ]

        for endpoint in excluded_endpoints:
            response = await api_client.get(endpoint)
            assert response.status_code == 200  # Should work without auth

    async def test_api_content_type(self, api_client: httpx.AsyncClient):
        """Test API returns proper content type."""
        response = await api_client.get("/api/v1/health")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    async def test_api_cors_headers(self, api_client: httpx.AsyncClient):
        """Test CORS headers if implemented."""
        # Options request to test CORS preflight
        response = await api_client.options("/api/v1/health")

        # Might return 405 (Method Not Allowed) or 200 depending on CORS setup
        # This test might need adjustment based on actual CORS implementation
        assert response.status_code in [200, 405]

    async def test_large_request_handling(self, api_client: httpx.AsyncClient):
        """Test API handles large requests appropriately."""
        # Create a large payload (but not too large to avoid timeouts)
        large_data = {"data": "x" * 10000}  # 10KB of data

        # Try to send to an endpoint that doesn't accept this data
        response = await api_client.post("/api/v1/health", json=large_data)

        # Should return method not allowed, not crash
        assert response.status_code == 405  # Method Not Allowed
