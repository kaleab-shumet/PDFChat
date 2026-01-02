import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.models.user import User
from api.v1.models.project import Project


class TestProjectEndpoints:
    """Test project management endpoints."""

    @pytest.mark.asyncio
    async def test_create_project_success(
        self, async_client: AsyncClient, auth_headers: dict, valid_project_data: dict
    ):
        """Test successful project creation."""
        response = await async_client.post(
            "/api/v1/projects/", json=valid_project_data, headers=auth_headers
        )

        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Project created successfully"

        project_data = data["data"]
        assert project_data["name"] == valid_project_data["name"]
        assert project_data["description"] == valid_project_data["description"]
        assert "id" in project_data
        assert "created_at" in project_data

    @pytest.mark.asyncio
    async def test_create_project_unauthorized(
        self, async_client: AsyncClient, valid_project_data: dict
    ):
        """Test project creation without authentication."""
        response = await async_client.post("/api/v1/projects/", json=valid_project_data)

        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "MISSING_AUTH"

    @pytest.mark.asyncio
    async def test_create_project_invalid_token(
        self, async_client: AsyncClient, valid_project_data: dict
    ):
        """Test project creation with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}

        response = await async_client.post(
            "/api/v1/projects/", json=valid_project_data, headers=headers
        )

        assert response.status_code == 401

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_create_project_missing_name(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test project creation with missing name."""
        project_data = {"description": "Project without name"}

        response = await async_client.post(
            "/api/v1/projects/", json=project_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_projects_success(
        self, async_client: AsyncClient, auth_headers: dict, test_project: Project
    ):
        """Test listing user's projects."""
        response = await async_client.get("/api/v1/projects/", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        projects = data["data"]
        assert isinstance(projects, list)
        assert len(projects) >= 1

        # Check that our test project is in the list
        project_ids = [p["id"] for p in projects]
        assert str(test_project.id) in project_ids

    @pytest.mark.asyncio
    async def test_list_projects_unauthorized(self, async_client: AsyncClient):
        """Test listing projects without authentication."""
        response = await async_client.get("/api/v1/projects/")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_project_success(
        self, async_client: AsyncClient, auth_headers: dict, test_project: Project
    ):
        """Test getting a specific project."""
        response = await async_client.get(
            f"/api/v1/projects/{test_project.id}", headers=auth_headers
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        project_data = data["data"]
        assert project_data["id"] == str(test_project.id)
        assert project_data["name"] == test_project.name
        assert project_data["description"] == test_project.description

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test getting a non-existent project."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await async_client.get(
            f"/api/v1/projects/{fake_uuid}", headers=auth_headers
        )

        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert data["error"]["error_code"] == "PROJECT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_project_unauthorized(
        self, async_client: AsyncClient, test_project: Project
    ):
        """Test getting a project without authentication."""
        response = await async_client.get(f"/api/v1/projects/{test_project.id}")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_project_success(
        self, async_client: AsyncClient, auth_headers: dict, test_project: Project
    ):
        """Test updating a project."""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
        }

        response = await async_client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        project_data = data["data"]
        assert project_data["name"] == update_data["name"]
        assert project_data["description"] == update_data["description"]
        assert project_data["id"] == str(test_project.id)

    @pytest.mark.asyncio
    async def test_update_project_partial(
        self, async_client: AsyncClient, auth_headers: dict, test_project: Project
    ):
        """Test partial update of a project."""
        update_data = {"name": "Partially Updated Name"}

        response = await async_client.put(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        project_data = data["data"]
        assert project_data["name"] == update_data["name"]
        # Description should remain unchanged
        assert project_data["description"] == test_project.description

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_db: AsyncSession,
        test_user: User,
    ):
        """Test deleting a project."""
        # Create a project specifically for deletion
        from api.v1.models.project import Project
        import uuid

        project = Project(
            id=uuid.uuid4(), name="Project to Delete", owner_user_id=test_user.id
        )
        test_db.add(project)
        await test_db.commit()
        await test_db.refresh(project)

        response = await async_client.delete(
            f"/api/v1/projects/{project.id}", headers=auth_headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_project_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test deleting a non-existent project."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await async_client.delete(
            f"/api/v1/projects/{fake_uuid}", headers=auth_headers
        )

        assert response.status_code == 404


class TestProjectAuthorization:
    """Test project authorization and access control."""

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_users_projects(
        self, async_client: AsyncClient, test_db: AsyncSession
    ):
        """Test that users can only access their own projects."""
        from api.v1.models.user import User
        from api.v1.models.project import Project
        from api.v1.core.auth import get_password_hash, create_access_token
        import uuid

        # Create a second user
        user2 = User(
            id=uuid.uuid4(),
            email="user2@example.com",
            hashed_password=get_password_hash("password"),
            is_active=True,
        )
        test_db.add(user2)
        await test_db.commit()
        await test_db.refresh(user2)

        # Create a project for user2
        project2 = Project(
            id=uuid.uuid4(), name="User2's Project", owner_user_id=user2.id
        )
        test_db.add(project2)
        await test_db.commit()
        await test_db.refresh(project2)

        # Create user1
        user1 = User(
            id=uuid.uuid4(),
            email="user1@example.com",
            hashed_password=get_password_hash("password"),
            is_active=True,
        )
        test_db.add(user1)
        await test_db.commit()
        await test_db.refresh(user1)

        # Create token for user1
        user1_token = create_access_token(
            {"sub": str(user1.id), "email": "user1@example.com"}
        )
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # User1 should not be able to access user2's project
        response = await async_client.get(
            f"/api/v1/projects/{project2.id}", headers=user1_headers
        )

        assert response.status_code == 404  # Should appear as not found for security
