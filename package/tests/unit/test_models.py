import pytest
from unittest.mock import patch, Mock, MagicMock
import json
from datetime import datetime

from prompta.models import BaseModel, Project, Prompt, PromptVersion, _get_api_key
from prompta.exceptions import NotFoundError, ValidationError, AuthenticationError


class TestGetApiKey:
    
    @patch.dict('os.environ', {'PROMPTA_API_KEY': 'env_key'})
    def test_get_api_key_from_env(self):
        """Test getting API key from environment variable."""
        api_key = _get_api_key()
        assert api_key == 'env_key'
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('prompta.models.dotenv_values', return_value={'PROMPTA_API_KEY': 'dotenv_key'})
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_api_key_from_dotenv(self, mock_exists, mock_dotenv):
        """Test getting API key from .env file."""
        api_key = _get_api_key()
        assert api_key == 'dotenv_key'
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('prompta.models.dotenv_values', return_value={})
    @patch('pathlib.Path.exists', return_value=False)
    def test_get_api_key_none(self, mock_exists, mock_dotenv):
        """Test getting API key when not configured."""
        api_key = _get_api_key()
        assert api_key is None


class TestBaseModel:
    
    @patch('prompta.models.PromptaClient')
    def test_init_minimal(self, mock_client_class):
        """Test BaseModel initialization with minimal parameters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            model = BaseModel()
        
        assert model._client == mock_client
    
    @patch('prompta.models.PromptaClient')
    def test_init_with_client(self, mock_client_class):
        """Test BaseModel initialization with provided client."""
        mock_client = Mock()
        
        model = BaseModel(client=mock_client)
        
        assert model._client == mock_client
    
    @patch('prompta.models.PromptaClient')
    def test_from_dict(self, mock_client_class):
        """Test creating BaseModel from dictionary."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        data = {
            "id": "test-id",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z",
            "extra_field": "value"
        }
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            model = BaseModel._from_dict(data)
        
        assert model.id == "test-id"
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)
        assert model.extra_field == "value"
    
    @patch('prompta.models.PromptaClient')
    def test_from_dict_missing_fields(self, mock_client_class):
        """Test creating BaseModel from dictionary with missing fields."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        data = {"id": "test-id"}
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            model = BaseModel._from_dict(data)
        
        assert model.id == "test-id"


class TestProject:
    
    @patch('prompta.models.PromptaClient')
    def test_init_minimal(self, mock_client_class):
        """Test Project initialization with minimal parameters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(name="test-project")
        
        assert project.name == "test-project"
        assert project.description is None
        assert project.tags == []
        assert project.is_public is False
    
    @patch('prompta.models.PromptaClient')
    def test_init_full(self, mock_client_class):
        """Test Project initialization with all parameters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(
                id="proj-123",
                name="test-project",
                description="A test project",
                tags=["test", "sample"],
                is_public=True,
                is_active=True
            )
        
        assert project.id == "proj-123"
        assert project.name == "test-project"
        assert project.description == "A test project"
        assert project.tags == ["test", "sample"]
        assert project.is_public is True
        assert project.is_active is True
    
    @patch('prompta.models.PromptaClient')
    def test_save_new_project(self, mock_client_class):
        """Test saving a new project."""
        mock_client = Mock()
        mock_client.create_project.return_value = {
            "id": "new-proj-123",
            "name": "test-project",
            "description": "A test project",
            "tags": ["test"],
            "is_public": False,
            "is_active": True,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(name="test-project", description="A test project", tags=["test"])
            result = project.save()
        
        assert result.id == "new-proj-123"
        assert result.name == "test-project"
        mock_client.create_project.assert_called_once()
    
    @patch('prompta.models.PromptaClient')
    def test_save_existing_project(self, mock_client_class):
        """Test saving an existing project."""
        mock_client = Mock()
        mock_client.update_project.return_value = {
            "id": "proj-123",
            "name": "updated-project",
            "description": "Updated description",
            "tags": ["updated"],
            "is_public": True,
            "is_active": True,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-02T12:00:00Z"
        }
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(id="proj-123", name="updated-project")
            result = project.save()
        
        assert result.id == "proj-123"
        assert result.name == "updated-project"
        mock_client.update_project.assert_called_once_with("proj-123", {
            "name": "updated-project",
            "description": None,
            "tags": [],
            "is_public": False
        })
    
    @patch('prompta.models.PromptaClient')
    def test_delete(self, mock_client_class):
        """Test deleting a project."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(id="proj-123", name="test-project")
            project.delete()
        
        mock_client.delete_project.assert_called_once_with("proj-123")
    
    @patch('prompta.models.PromptaClient')
    def test_delete_no_id(self, mock_client_class):
        """Test deleting project without ID."""
        mock_client_class.return_value = Mock()
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(name="test-project")
        
            with pytest.raises(ValueError, match="Cannot delete project without ID"):
                project.delete()
    
    @patch('prompta.models.PromptaClient')
    def test_get_prompts(self, mock_client_class):
        """Test getting prompts from project."""
        mock_client = Mock()
        mock_client.get_prompts.return_value = [
            {
                "id": "prompt-1",
                "name": "Test Prompt",
                "description": "A test prompt",
                "location": "test.md",
                "tags": ["test"],
                "is_public": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "current_version": {
                    "id": "version-1",
                    "version_number": 1,
                    "content": "Test content",
                    "commit_message": "Initial version",
                    "created_at": "2024-01-01T12:00:00Z",
                    "is_current": True
                }
            }
        ]
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(id="proj-123", name="test-project")
            prompts = project.get_prompts()
        
        assert len(prompts) == 1
        assert isinstance(prompts[0], Prompt)
        assert prompts[0].name == "Test Prompt"
        mock_client.get_prompts.assert_called_once_with(project_id="proj-123")
    
    @patch('prompta.models.PromptaClient')
    def test_create_class_method(self, mock_client_class):
        """Test Project.create class method."""
        mock_client = Mock()
        mock_client.create_project.return_value = {
            "id": "new-proj-123",
            "name": "New Project",
            "description": "A new project",
            "tags": ["new"],
            "is_public": False,
            "is_active": True,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project.create(
                name="New Project",
                description="A new project",
                tags=["new"]
            )
        
        assert isinstance(project, Project)
        assert project.id == "new-proj-123"
        assert project.name == "New Project"
        mock_client.create_project.assert_called_once()
    
    @patch('prompta.models.PromptaClient')
    def test_get_class_method(self, mock_client_class):
        """Test Project.get class method."""
        mock_client = Mock()
        mock_client.get_project_by_id.return_value = {
            "id": "proj-123",
            "name": "Test Project",
            "description": "A test project",
            "tags": ["test"],
            "is_public": False,
            "is_active": True,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project.get("proj-123")
        
        assert isinstance(project, Project)
        assert project.id == "proj-123"
        assert project.name == "Test Project"
        mock_client.get_project_by_id.assert_called_once_with("proj-123")
    
    @patch('prompta.models.PromptaClient')
    def test_get_by_name(self, mock_client_class):
        """Test Project.get with name instead of ID."""
        mock_client = Mock()
        mock_client.get_project_by_id.side_effect = NotFoundError("Not found by ID")
        mock_client.get_project_by_name.return_value = {
            "id": "proj-123",
            "name": "Test Project",
            "description": "A test project",
            "tags": ["test"],
            "is_public": False,
            "is_active": True,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project.get("Test Project")
        
        assert isinstance(project, Project)
        assert project.id == "proj-123"
        assert project.name == "Test Project"
        mock_client.get_project_by_name.assert_called_once_with("Test Project")
    
    @patch('prompta.models.PromptaClient')
    def test_list_class_method(self, mock_client_class):
        """Test Project.list class method."""
        mock_client = Mock()
        mock_client.get_projects.return_value = {
            "projects": [
                {
                    "id": "proj-1",
                    "name": "Project 1",
                    "description": "First project",
                    "tags": ["test"],
                    "is_public": False,
                    "is_active": True,
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z"
                },
                {
                    "id": "proj-2",
                    "name": "Project 2",
                    "description": "Second project",
                    "tags": ["sample"],
                    "is_public": True,
                    "is_active": True,
                    "created_at": "2024-01-02T12:00:00Z",
                    "updated_at": "2024-01-02T12:00:00Z"
                }
            ],
            "total": 2,
            "page": 1,
            "page_size": 20,
            "total_pages": 1
        }
        mock_client_class.return_value = mock_client
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            projects = Project.list(query="test", page=1, page_size=20)
        
        assert len(projects) == 2
        assert all(isinstance(p, Project) for p in projects)
        assert projects[0].name == "Project 1"
        assert projects[1].name == "Project 2"
        mock_client.get_projects.assert_called_once_with(
            query="test",
            tags=None,
            page=1,
            page_size=20
        )
    
    @patch('prompta.models.PromptaClient')
    def test_repr(self, mock_client_class):
        """Test Project string representation."""
        mock_client_class.return_value = Mock()
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            project = Project(id="proj-123", name="Test Project")
        
            repr_str = repr(project)
        
            assert "Project" in repr_str
            assert "proj-123" in repr_str
            assert "Test Project" in repr_str


class TestPromptVersion:
    
    def test_init(self):
        """Test PromptVersion initialization."""
        version = PromptVersion(
            id="version-123",
            version_number=1,
            content="Test content",
            commit_message="Initial version",
            is_current=True
        )
        
        assert version.id == "version-123"
        assert version.version_number == 1
        assert version.content == "Test content"
        assert version.commit_message == "Initial version"
        assert version.is_current is True
    
    def test_from_dict(self):
        """Test creating PromptVersion from dictionary."""
        data = {
            "id": "version-123",
            "version_number": 1,
            "content": "Test content",
            "commit_message": "Initial version",
            "created_at": "2024-01-01T12:00:00Z",
            "is_current": True
        }
        
        version = PromptVersion._from_dict(data)
        
        assert version.id == "version-123"
        assert version.version_number == 1
        assert version.content == "Test content"
        assert version.commit_message == "Initial version"
        assert version.is_current is True
        assert isinstance(version.created_at, datetime)
    
    def test_repr(self):
        """Test PromptVersion string representation."""
        version = PromptVersion(id="version-123", version_number=1)
        
        repr_str = repr(version)
        
        assert "PromptVersion" in repr_str
        assert "version-123" in repr_str
        assert "v1" in repr_str


class TestPrompt:
    
    @patch('prompta.models.PromptaClient')
    def test_init_minimal(self, mock_client_class):
        """Test Prompt initialization with minimal parameters."""
        mock_client_class.return_value = Mock()
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            prompt = Prompt(name="test-prompt", location="test.md")
        
        assert prompt.name == "test-prompt"
        assert prompt.location == "test.md"
        assert prompt.description is None
        assert prompt.tags == []
        assert prompt.is_public is False
        assert prompt.project_id is None
    
    @patch('prompta.models.PromptaClient')
    def test_init_full(self, mock_client_class):
        """Test Prompt initialization with all parameters."""
        mock_client_class.return_value = Mock()
        
        current_version = PromptVersion(
            id="version-123",
            version_number=1,
            content="Test content",
            commit_message="Initial version",
            is_current=True
        )
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            prompt = Prompt(
                id="prompt-123",
                name="test-prompt",
                description="A test prompt",
                location="test.md",
                tags=["test", "sample"],
                is_public=True,
                project_id="proj-123",
                current_version=current_version
            )
        
        assert prompt.id == "prompt-123"
        assert prompt.name == "test-prompt"
        assert prompt.description == "A test prompt"
        assert prompt.location == "test.md"
        assert prompt.tags == ["test", "sample"]
        assert prompt.is_public is True
        assert prompt.project_id == "proj-123"
        assert prompt.current_version == current_version
    
    @patch('prompta.models.PromptaClient')
    def test_content_property_with_version(self, mock_client_class):
        """Test content property with current version."""
        mock_client_class.return_value = Mock()
        
        current_version = PromptVersion(
            id="version-123",
            version_number=1,
            content="Version content",
            is_current=True
        )
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            prompt = Prompt(name="test", location="test.md", current_version=current_version)
        
        assert prompt.content == "Version content"
    
    @patch('prompta.models.PromptaClient')
    def test_content_property_no_version(self, mock_client_class):
        """Test content property without current version."""
        mock_client_class.return_value = Mock()
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            prompt = Prompt(name="test", location="test.md")
        
        assert prompt.content is None
    
    @patch('prompta.models.PromptaClient')
    def test_repr(self, mock_client_class):
        """Test Prompt string representation."""
        mock_client_class.return_value = Mock()
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            prompt = Prompt(id="prompt-123", name="Test Prompt", location="test.md")
        
            repr_str = repr(prompt)
        
            assert "Prompt" in repr_str
            assert "prompt-123" in repr_str
            assert "Test Prompt" in repr_str


class TestModelsIntegration:
    
    @patch('prompta.models.PromptaClient')
    def test_datetime_parsing_edge_cases(self, mock_client_class):
        """Test datetime parsing with various formats."""
        mock_client_class.return_value = Mock()
        
        with patch('prompta.models._get_api_key', return_value='test_key'):
            # Test with different datetime formats
            data_iso = {
                "id": "test-1",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T13:30:45.123Z"
            }
            
            model = BaseModel._from_dict(data_iso)
            assert isinstance(model.created_at, datetime)
            assert isinstance(model.updated_at, datetime)
            
            # Test with None values
            data_none = {
                "id": "test-2",
                "created_at": None,
                "updated_at": None
            }
            
            model = BaseModel._from_dict(data_none)
            assert model.created_at is None
            assert model.updated_at is None
            
            # Test with missing fields
            data_minimal = {"id": "test-3"}
            
            model = BaseModel._from_dict(data_minimal)
            assert hasattr(model, 'id')
            assert model.id == "test-3"