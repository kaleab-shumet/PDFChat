"""
E2E tests for project management flow.
"""

import pytest
import pytest_asyncio
import httpx
import uuid
from datetime import datetime
from typing import Union, Dict, Any, Tuple, List
from tests.e2e.utils import UserSession


@pytest.mark.asyncio
class TestProjectFlow:
    """Test complete project management workflows."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_authenticated_user(
        self, api_client: httpx.AsyncClient, user_session: UserSession, health_check
    ):
        """Set up authenticated user for project tests."""
        # Register user
        test_email = f"project_user_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {"email": test_email, "password": "testpassword123"}

        register_response = await api_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        user_session.email = test_email
        user_session.user_id = register_response.json()["data"]["id"]

        # Login user
        login_response = await api_client.post("/api/v1/auth/login", json=user_data)
        assert login_response.status_code == 200

        user_session.access_token = login_response.json()["data"]["access_token"]

    async def test_create_project(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test project creation."""
        project_data = {
            "name": f"Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "A test project for e2e testing",
        }

        response = await api_client.post(
            "/api/v1/projects/", headers=user_session.headers, json=project_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == project_data["name"]
        assert data["data"]["description"] == project_data["description"]
        assert "id" in data["data"]
        assert "created_at" in data["data"]
        assert "updated_at" in data["data"]

        # Store project for subsequent tests
        user_session.projects.append(data["data"])

    @pytest.mark.parametrize(
        "project_data",
        [
            {"name": "Project with long description", "description": "A" * 1000},
            {
                "name": "Project with special chars !@#$%",
                "description": "Special chars test",
            },
            {
                "name": "Project with unicode 🚀📊",
                "description": "Unicode test project",
            },
        ],
    )
    async def test_create_project_variations(
        self,
        api_client: httpx.AsyncClient,
        user_session: UserSession,
        project_data: dict,
    ):
        """Test project creation with various data."""
        response = await api_client.post(
            "/api/v1/projects/", headers=user_session.headers, json=project_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == project_data["name"]
        assert data["data"]["description"] == project_data["description"]

    async def test_list_projects(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test listing user projects."""
        response = await api_client.get(
            "/api/v1/projects/", headers=user_session.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # Note: Each test runs in isolation, so this user may not have any projects yet
        # This is actually correct behavior - just verify the response structure

        # Verify project structure if any projects exist
        for project in data["data"]:
            assert "id" in project
            assert "name" in project
            assert "description" in project
            assert "created_at" in project
            assert "updated_at" in project

    async def test_get_specific_project(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test retrieving a specific project."""
        # Create a project first
        project_data = {
            "name": f"Get Test Project {uuid.uuid4().hex[:8]}",
            "description": "Project for get test",
        }

        create_response = await api_client.post(
            "/api/v1/projects/", headers=user_session.headers, json=project_data
        )
        assert create_response.status_code == 201
        project = create_response.json()["data"]

        response = await api_client.get(
            f"/api/v1/projects/{project['id']}", headers=user_session.headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == project["id"]
        assert data["data"]["name"] == project["name"]

    async def test_update_project(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test updating project details."""
        # Create a project first
        project_data = {
            "name": f"Update Test Project {uuid.uuid4().hex[:8]}",
            "description": "Project for update test",
        }

        create_response = await api_client.post(
            "/api/v1/projects/", headers=user_session.headers, json=project_data
        )
        assert create_response.status_code == 201
        project = create_response.json()["data"]

        update_data = {
            "name": f"Updated Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Updated description for the project",
        }

        response = await api_client.put(
            f"/api/v1/projects/{project['id']}",
            headers=user_session.headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["description"] == update_data["description"]
        assert data["data"]["id"] == project["id"]

    async def test_project_not_found(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test accessing non-existent project."""
        fake_uuid = str(uuid.uuid4())

        response = await api_client.get(
            f"/api/v1/projects/{fake_uuid}", headers=user_session.headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "PROJECT_NOT_FOUND"

    async def test_delete_project(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test deleting a project."""
        # Create a project first
        project_data = {
            "name": f"Delete Test Project {uuid.uuid4().hex[:8]}",
            "description": "Project for delete test",
        }

        create_response = await api_client.post(
            "/api/v1/projects/", headers=user_session.headers, json=project_data
        )
        assert create_response.status_code == 201
        project = create_response.json()["data"]

        response = await api_client.delete(
            f"/api/v1/projects/{project['id']}", headers=user_session.headers
        )

        assert response.status_code == 204

    async def test_access_deleted_project(
        self, api_client: httpx.AsyncClient, user_session: UserSession
    ):
        """Test that deleted project cannot be accessed."""
        # Create and delete a project
        project_data = {
            "name": f"Access Test Project {uuid.uuid4().hex[:8]}",
            "description": "Project for access after delete test",
        }

        create_response = await api_client.post(
            "/api/v1/projects/", headers=user_session.headers, json=project_data
        )
        assert create_response.status_code == 201
        project = create_response.json()["data"]

        # Delete the project
        delete_response = await api_client.delete(
            f"/api/v1/projects/{project['id']}", headers=user_session.headers
        )
        assert delete_response.status_code == 204

        # Try to access deleted project
        response = await api_client.get(
            f"/api/v1/projects/{project['id']}", headers=user_session.headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "PROJECT_NOT_FOUND"

    async def test_unauthorized_project_access(self, api_client: httpx.AsyncClient):
        """Test project endpoints require authentication."""
        endpoints: List[Union[Tuple[str, str], Tuple[str, str, Dict[str, Any]]]] = [
            ("GET", "/api/v1/projects/"),
            ("POST", "/api/v1/projects/", {"name": "Test", "description": "Test"}),
            ("GET", f"/api/v1/projects/{uuid.uuid4()}"),
            ("PUT", f"/api/v1/projects/{uuid.uuid4()}", {"name": "Test"}),
            ("DELETE", f"/api/v1/projects/{uuid.uuid4()}"),
        ]

        for endpoint_info in endpoints:
            method: str = endpoint_info[0]
            url: str = endpoint_info[1]
            json_data: Union[Dict[str, Any], None] = (
                endpoint_info[2] if len(endpoint_info) > 2 else None
            )

            if method == "GET":
                response = await api_client.get(url)
            elif method == "POST":
                response = await api_client.post(url, json=json_data)
            elif method == "PUT":
                response = await api_client.put(url, json=json_data)
            elif method == "DELETE":
                response = await api_client.delete(url)

            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert data["error"]["error_code"] == "MISSING_AUTH"
