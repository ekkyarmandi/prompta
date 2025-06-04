import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prompts.routes import router
from prompts.schemas import PromptCreate, PromptUpdate, PromptVersionCreate
from auth.models import User
from app.database import get_db
from auth.dependencies import get_current_user_optional, get_current_user_flexible


# Create test app with dependency overrides
app = FastAPI()
app.include_router(router, prefix="/api/v1")

# Test data
test_user = Mock(spec=User)
test_user.id = "user123"
test_user.username = "testuser"
test_user.email = "test@example.com"
test_user.is_active = True

test_db = Mock()

# Dependency overrides
app.dependency_overrides[get_db] = lambda: test_db
app.dependency_overrides[get_current_user_flexible] = lambda: test_user
app.dependency_overrides[get_current_user_optional] = lambda: (test_user, True)

client = TestClient(app)


@pytest.fixture
def sample_prompt_create():
    """Sample prompt creation data"""
    return PromptCreate(
        name="test-prompt",
        description="A test prompt",
        location="test.md",
        tags=["test", "sample"],
        content="This is test content",
        commit_message="Initial version",
    )


@pytest.fixture
def sample_prompt_response():
    """Sample prompt response"""
    return {
        "id": "prompt123",
        "name": "test-prompt",
        "description": "A test prompt",
        "location": "test.md",
        "project_id": None,
        "project": None,
        "tags": ["test", "sample"],
        "is_public": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "current_version": {
            "id": "version123",
            "version_number": 1,
            "content": "This is test content",
            "commit_message": "Initial version",
            "is_current": True,
            "created_at": "2024-01-01T00:00:00",
        },
    }


@pytest.fixture
def sample_version_response():
    """Sample version response"""
    return {
        "id": "version456",
        "version_number": 2,
        "content": "Updated content",
        "commit_message": "Second version",
        "is_current": True,
        "created_at": "2024-01-01T01:00:00",
    }


class TestCreatePrompt:
    """Test cases for create_prompt endpoint"""

    @patch("prompts.routes.PromptService.create_prompt")
    def test_create_prompt_success(
        self, mock_create_prompt, sample_prompt_create, sample_prompt_response
    ):
        """Test successful prompt creation"""
        mock_create_prompt.return_value = sample_prompt_response

        response = client.post("/prompts/", json=sample_prompt_create.model_dump())

        assert response.status_code == 201
        assert response.json() == sample_prompt_response
        mock_create_prompt.assert_called_once_with(
            test_db, test_user, sample_prompt_create
        )

    @patch("prompts.routes.PromptService.create_prompt")
    def test_create_prompt_value_error(self, mock_create_prompt, sample_prompt_create):
        """Test prompt creation with validation error"""
        mock_create_prompt.side_effect = ValueError("Prompt name already exists")

        response = client.post("/prompts/", json=sample_prompt_create.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Prompt name already exists"

    @patch("prompts.routes.PromptService.create_prompt")
    def test_create_prompt_without_trailing_slash(
        self, mock_create_prompt, sample_prompt_create, sample_prompt_response
    ):
        """Test create prompt endpoint without trailing slash"""
        mock_create_prompt.return_value = sample_prompt_response

        response = client.post("/prompts", json=sample_prompt_create.model_dump())

        assert response.status_code == 201
        assert response.json() == sample_prompt_response


class TestListPrompts:
    """Test cases for list_prompts endpoint"""

    @patch("prompts.routes.PromptService.list_prompts")
    def test_list_prompts_success(self, mock_list_prompts, sample_prompt_response):
        """Test successful prompt listing"""
        mock_list_prompts.return_value = ([sample_prompt_response], 1)

        response = client.get("/prompts/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 1
        assert len(data["prompts"]) == 1
        assert data["prompts"][0] == sample_prompt_response

    @patch("prompts.routes.PromptService.list_prompts")
    def test_list_prompts_with_search_params(self, mock_list_prompts):
        """Test prompt listing with search parameters"""
        mock_list_prompts.return_value = ([], 0)

        response = client.get(
            "/prompts/?query=test&tags=python&tags=ai&location=src/&page=2&page_size=10"
        )

        assert response.status_code == 200
        mock_list_prompts.assert_called_once()
        # Check that search params were created properly
        call_args = mock_list_prompts.call_args
        assert call_args[0][0] == test_db  # db
        assert call_args[0][1] == test_user  # user
        search_params = call_args[0][2]  # search_params
        assert search_params.query == "test"
        assert search_params.tags == ["python", "ai"]
        assert search_params.location == "src/"
        assert search_params.page == 2
        assert search_params.page_size == 10

    @patch("prompts.routes.PromptService.list_prompts")
    def test_list_prompts_empty_result(self, mock_list_prompts):
        """Test prompt listing with no results"""
        mock_list_prompts.return_value = ([], 0)

        response = client.get("/prompts/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["total_pages"] == 0
        assert len(data["prompts"]) == 0


class TestSearchPrompts:
    """Test cases for search_prompts_by_content endpoint"""

    @patch("prompts.routes.PromptService.search_prompts_by_content")
    def test_search_prompts_success(self, mock_search_prompts, sample_prompt_response):
        """Test successful prompt content search"""
        mock_search_prompts.return_value = ([sample_prompt_response], 1)

        response = client.get("/prompts/search?q=test%20content&page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["prompts"]) == 1
        mock_search_prompts.assert_called_once_with(
            test_db, test_user, "test content", 1, 10, True
        )


class TestGetPrompt:
    """Test cases for get_prompt endpoint"""

    @patch("prompts.routes.PromptService.get_prompt_public_or_private")
    def test_get_prompt_success(self, mock_get_prompt, sample_prompt_response):
        """Test successful prompt retrieval by ID"""
        mock_get_prompt.return_value = sample_prompt_response

        response = client.get("/prompts/prompt123")

        assert response.status_code == 200
        assert response.json() == sample_prompt_response
        mock_get_prompt.assert_called_once_with(test_db, "prompt123", test_user)

    @patch("prompts.routes.PromptService.get_prompt_public_or_private")
    def test_get_prompt_not_found(self, mock_get_prompt):
        """Test prompt retrieval when not found"""
        mock_get_prompt.return_value = None

        response = client.get("/prompts/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found or not accessible"


class TestUpdatePrompt:
    """Test cases for update_prompt endpoint"""

    @patch("prompts.routes.PromptService.update_prompt")
    def test_update_prompt_success(self, mock_update_prompt, sample_prompt_response):
        """Test successful prompt update"""
        mock_update_prompt.return_value = sample_prompt_response

        update_data = PromptUpdate(
            name="updated-prompt", description="Updated description"
        )
        response = client.put("/prompts/prompt123", json=update_data.model_dump())

        assert response.status_code == 200
        assert response.json() == sample_prompt_response
        mock_update_prompt.assert_called_once_with(
            test_db, test_user, "prompt123", update_data
        )

    @patch("prompts.routes.PromptService.update_prompt")
    def test_update_prompt_not_found(self, mock_update_prompt):
        """Test prompt update when not found"""
        mock_update_prompt.return_value = None

        update_data = PromptUpdate(name="updated-prompt")
        response = client.put("/prompts/nonexistent", json=update_data.model_dump())

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found"

    @patch("prompts.routes.PromptService.update_prompt")
    def test_update_prompt_value_error(self, mock_update_prompt):
        """Test prompt update with validation error"""
        mock_update_prompt.side_effect = ValueError("Invalid prompt data")

        update_data = PromptUpdate(name="updated-prompt")
        response = client.put("/prompts/prompt123", json=update_data.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid prompt data"


class TestDeletePrompt:
    """Test cases for delete_prompt endpoint"""

    @patch("prompts.routes.PromptService.delete_prompt")
    def test_delete_prompt_success(self, mock_delete_prompt):
        """Test successful prompt deletion"""
        mock_delete_prompt.return_value = True

        response = client.delete("/prompts/prompt123")

        assert response.status_code == 204
        mock_delete_prompt.assert_called_once_with(test_db, test_user, "prompt123")

    @patch("prompts.routes.PromptService.delete_prompt")
    def test_delete_prompt_not_found(self, mock_delete_prompt):
        """Test prompt deletion when not found"""
        mock_delete_prompt.return_value = False

        response = client.delete("/prompts/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Prompt not found"


class TestVersionManagement:
    """Test cases for version management endpoints"""

    @patch("prompts.routes.PromptService.create_version")
    def test_create_version_success(self, mock_create_version, sample_version_response):
        """Test successful version creation"""
        mock_create_version.return_value = sample_version_response

        version_data = PromptVersionCreate(
            content="Updated content", commit_message="Second version"
        )
        response = client.post(
            "/prompts/prompt123/versions", json=version_data.model_dump()
        )

        assert response.status_code == 201
        assert response.json() == sample_version_response
        mock_create_version.assert_called_once_with(
            test_db, test_user, "prompt123", version_data
        )

    @patch("prompts.routes.PromptService.list_versions")
    def test_list_versions_success(self, mock_list_versions, sample_version_response):
        """Test successful version listing"""
        mock_list_versions.return_value = [sample_version_response]

        response = client.get("/prompts/prompt123/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["versions"]) == 1
        assert data["versions"][0] == sample_version_response

    @patch("prompts.routes.PromptService.get_version")
    def test_get_version_success(self, mock_get_version, sample_version_response):
        """Test successful version retrieval"""
        mock_get_version.return_value = sample_version_response

        response = client.get("/prompts/prompt123/versions/2")

        assert response.status_code == 200
        assert response.json() == sample_version_response
        mock_get_version.assert_called_once_with(test_db, test_user, "prompt123", 2)


class TestDownloadEndpoints:
    """Test cases for download endpoints - testing route functions directly"""

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_json_success(
        self, mock_download_prompts, sample_prompt_response
    ):
        """Test successful prompt download in JSON format"""
        from prompts.routes import download_prompts
        from prompts.schemas import PromptDownloadParams

        mock_download_prompts.return_value = (
            [sample_prompt_response],
            1,
            {"project_name": "test"},
        )

        # Call the route function directly
        result = await download_prompts(
            project_name="test",
            directory=None,
            tags=None,
            include_content=True,
            format="json",
            user_auth=(test_user, True),
            db=test_db,
        )

        assert result.total == 1
        assert result.download_format == "json"
        assert result.filters_applied == {"project_name": "test"}
        assert len(result.prompts) == 1

        mock_download_prompts.assert_called_once()
        call_args = mock_download_prompts.call_args
        assert call_args[0][0] == test_db  # db
        assert call_args[0][1] == test_user  # user
        download_params = call_args[0][2]  # download_params
        assert download_params.project_name == "test"
        assert download_params.format == "json"

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_with_filters(
        self, mock_download_prompts, sample_prompt_response
    ):
        """Test prompt download with multiple filters"""
        from prompts.routes import download_prompts

        filters_applied = {"tags": ["python"]}
        mock_download_prompts.return_value = (
            [sample_prompt_response],
            1,
            filters_applied,
        )

        result = await download_prompts(
            project_name=None,
            directory=None,
            tags=["python"],
            include_content=True,
            format="json",
            user_auth=(test_user, True),
            db=test_db,
        )

        assert result.total == 1
        assert result.download_format == "json"
        assert result.filters_applied == filters_applied

        mock_download_prompts.assert_called_once()
        call_args = mock_download_prompts.call_args
        download_params = call_args[0][2]  # third argument
        assert download_params.tags == ["python"]
        assert download_params.include_content == True

    @pytest.mark.asyncio
    async def test_download_prompts_zip_redirect(self):
        """Test that zip format returns error directing to zip endpoint"""
        from prompts.routes import download_prompts
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await download_prompts(
                project_name=None,
                directory=None,
                tags=None,
                include_content=True,
                format="zip",
                user_auth=(test_user, True),
                db=test_db,
            )

        assert exc_info.value.status_code == 400
        assert "zip endpoint" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_value_error(self, mock_download_prompts):
        """Test download prompts with service value error"""
        from prompts.routes import download_prompts
        from fastapi import HTTPException

        mock_download_prompts.side_effect = ValueError("Invalid filter parameters")

        with pytest.raises(HTTPException) as exc_info:
            await download_prompts(
                project_name="invalid",
                directory=None,
                tags=None,
                include_content=True,
                format="json",
                user_auth=(test_user, True),
                db=test_db,
            )

        assert exc_info.value.status_code == 400
        assert str(exc_info.value.detail) == "Invalid filter parameters"

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_by_project_success(
        self, mock_download_prompts, sample_prompt_response
    ):
        """Test successful download by project"""
        from prompts.routes import download_prompts_by_project

        filters_applied = {"project_name": "test-project"}
        mock_download_prompts.return_value = (
            [sample_prompt_response],
            1,
            filters_applied,
        )

        result = await download_prompts_by_project(
            project_name="test-project",
            include_content=True,
            user_auth=(test_user, True),
            db=test_db,
        )

        assert result.total == 1
        assert result.download_format == "json"
        assert result.filters_applied == filters_applied

        mock_download_prompts.assert_called_once()
        call_args = mock_download_prompts.call_args
        download_params = call_args[0][2]  # download_params
        assert download_params.project_name == "test-project"
        assert download_params.format == "json"

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_by_project_exclude_content(
        self, mock_download_prompts, sample_prompt_response
    ):
        """Test download by project excluding content"""
        from prompts.routes import download_prompts_by_project

        filters_applied = {"project_name": "test-project"}
        mock_download_prompts.return_value = (
            [sample_prompt_response],
            1,
            filters_applied,
        )

        result = await download_prompts_by_project(
            project_name="test-project",
            include_content=False,
            user_auth=(test_user, True),
            db=test_db,
        )

        mock_download_prompts.assert_called_once()
        call_args = mock_download_prompts.call_args
        download_params = call_args[0][2]  # third argument
        assert download_params.include_content == False
        assert download_params.project_name == "test-project"

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_by_project_value_error(self, mock_download_prompts):
        """Test download by project with service value error"""
        from prompts.routes import download_prompts_by_project
        from fastapi import HTTPException

        mock_download_prompts.side_effect = ValueError("Project not found")

        with pytest.raises(HTTPException) as exc_info:
            await download_prompts_by_project(
                project_name="nonexistent",
                include_content=True,
                user_auth=(test_user, True),
                db=test_db,
            )

        assert exc_info.value.status_code == 400
        assert str(exc_info.value.detail) == "Project not found"

    @pytest.mark.asyncio
    @patch("prompts.routes.PromptService.download_prompts")
    async def test_download_prompts_empty_result(self, mock_download_prompts):
        """Test download with no results"""
        from prompts.routes import download_prompts

        mock_download_prompts.return_value = ([], 0, {})

        result = await download_prompts(
            project_name=None,
            directory=None,
            tags=None,
            include_content=True,
            format="json",
            user_auth=(test_user, True),
            db=test_db,
        )

        assert result.total == 0
        assert len(result.prompts) == 0
        mock_download_prompts.assert_called_once()
