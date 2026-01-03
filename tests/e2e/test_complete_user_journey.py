"""
E2E tests for complete user journeys.
"""

import pytest
import httpx
import uuid
from datetime import datetime


@pytest.mark.asyncio
class TestCompleteUserJourney:
    """Test complete end-to-end user workflows."""

    async def test_complete_user_workflow(
        self, api_client: httpx.AsyncClient, health_check
    ):
        """Test complete user workflow from registration to project deletion."""
        # Step 1: Register new user
        test_email = f"journey_user_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {"email": test_email, "password": "journeypassword123"}

        register_response = await api_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201
        user_info = register_response.json()["data"]

        # Step 2: Login user
        login_response = await api_client.post("/api/v1/auth/login", json=user_data)
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 3: Verify user profile
        profile_response = await api_client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()["data"]
        assert profile_data["email"] == test_email
        assert profile_data["id"] == user_info["id"]

        # Step 4: Create multiple projects
        projects = []
        for i in range(3):
            project_data = {
                "name": f"Journey Project {i+1} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": f"Project {i+1} created during user journey test",
            }

            create_response = await api_client.post(
                "/api/v1/projects/", headers=headers, json=project_data
            )
            assert create_response.status_code == 201
            projects.append(create_response.json()["data"])

        # Step 5: List all projects and verify count
        list_response = await api_client.get("/api/v1/projects/", headers=headers)
        assert list_response.status_code == 200
        all_projects = list_response.json()["data"]
        assert len(all_projects) >= 3  # At least the 3 we created

        # Step 6: Update one project
        project_to_update = projects[0]
        update_data = {
            "name": f"Updated {project_to_update['name']}",
            "description": "Updated during journey test",
        }

        update_response = await api_client.put(
            f"/api/v1/projects/{project_to_update['id']}",
            headers=headers,
            json=update_data,
        )
        assert update_response.status_code == 200
        updated_project = update_response.json()["data"]
        assert updated_project["name"] == update_data["name"]

        # Step 7: Get specific project details
        detail_response = await api_client.get(
            f"/api/v1/projects/{project_to_update['id']}", headers=headers
        )
        assert detail_response.status_code == 200
        project_detail = detail_response.json()["data"]
        assert project_detail["name"] == update_data["name"]

        # Step 8: Delete one project
        project_to_delete = projects[1]
        delete_response = await api_client.delete(
            f"/api/v1/projects/{project_to_delete['id']}", headers=headers
        )
        assert delete_response.status_code == 204

        # Step 9: Verify project was deleted
        deleted_check_response = await api_client.get(
            f"/api/v1/projects/{project_to_delete['id']}", headers=headers
        )
        assert deleted_check_response.status_code == 404

        # Step 10: Verify remaining projects still exist
        final_list_response = await api_client.get("/api/v1/projects/", headers=headers)
        assert final_list_response.status_code == 200
        final_projects = final_list_response.json()["data"]

        # Should have one less project now
        assert len(final_projects) == len(all_projects) - 1

        # Verify deleted project is not in the list
        project_ids = [p["id"] for p in final_projects]
        assert project_to_delete["id"] not in project_ids

        # But other projects should still be there
        assert project_to_update["id"] in project_ids
        assert projects[2]["id"] in project_ids

    async def test_multiple_users_isolation(
        self, api_client: httpx.AsyncClient, health_check
    ):
        """Test that different users can't access each other's projects."""
        # Create first user
        user1_email = f"user1_{uuid.uuid4().hex[:8]}@example.com"
        user1_data = {"email": user1_email, "password": "password123"}

        await api_client.post("/api/v1/auth/register", json=user1_data)
        login1_response = await api_client.post("/api/v1/auth/login", json=user1_data)
        user1_token = login1_response.json()["data"]["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Create second user
        user2_email = f"user2_{uuid.uuid4().hex[:8]}@example.com"
        user2_data = {"email": user2_email, "password": "password123"}

        await api_client.post("/api/v1/auth/register", json=user2_data)
        login2_response = await api_client.post("/api/v1/auth/login", json=user2_data)
        user2_token = login2_response.json()["data"]["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # User 1 creates a project
        project_data = {
            "name": f"User 1 Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Private project for user 1",
        }

        create_response = await api_client.post(
            "/api/v1/projects/", headers=user1_headers, json=project_data
        )
        assert create_response.status_code == 201
        user1_project = create_response.json()["data"]

        # User 2 should not see User 1's projects
        user2_list_response = await api_client.get(
            "/api/v1/projects/", headers=user2_headers
        )
        assert user2_list_response.status_code == 200
        user2_projects = user2_list_response.json()["data"]

        # User 2 should have no projects or projects that don't include user 1's project
        user2_project_ids = [p["id"] for p in user2_projects]
        assert user1_project["id"] not in user2_project_ids

        # User 2 should not be able to access User 1's project directly
        # Note: This test assumes proper authorization is implemented
        # If not implemented yet, this might return 404 instead of 403
        direct_access_response = await api_client.get(
            f"/api/v1/projects/{user1_project['id']}", headers=user2_headers
        )
        assert direct_access_response.status_code in [
            403,
            404,
        ]  # Either forbidden or not found

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"email": "invalid-email", "password": "password123"},
            {"email": "test@example.com", "password": "short"},
            {"email": "", "password": "password123"},
            {"email": "test@example.com", "password": ""},
        ],
    )
    async def test_registration_validation(
        self, api_client: httpx.AsyncClient, invalid_data: dict, health_check
    ):
        """Test registration input validation."""
        response = await api_client.post("/api/v1/auth/register", json=invalid_data)

        # Should return validation error (could be 400 or 422 depending on validation type)
        assert response.status_code in [400, 422]
        data = response.json()
        # Check for either FastAPI validation format or our custom error format
        assert "detail" in data or ("success" in data and not data["success"])

    async def test_concurrent_project_operations(
        self, api_client: httpx.AsyncClient, health_check
    ):
        """Test concurrent project operations don't interfere."""
        # Setup authenticated user
        test_email = f"concurrent_user_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {"email": test_email, "password": "password123"}

        await api_client.post("/api/v1/auth/register", json=user_data)
        login_response = await api_client.post("/api/v1/auth/login", json=user_data)
        access_token = login_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create multiple projects concurrently
        import asyncio

        async def create_project(index):
            project_data = {
                "name": f"Concurrent Project {index}",
                "description": f"Project created concurrently #{index}",
            }
            return await api_client.post(
                "/api/v1/projects/", headers=headers, json=project_data
            )

        # Create 5 projects concurrently
        responses = await asyncio.gather(*[create_project(i) for i in range(5)])

        # All should succeed
        for response in responses:
            assert response.status_code == 201

        # Verify all projects were created
        list_response = await api_client.get("/api/v1/projects/", headers=headers)
        assert list_response.status_code == 200
        projects = list_response.json()["data"]
        assert len(projects) >= 5
