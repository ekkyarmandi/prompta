import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import click.testing

# Set test environment
os.environ["PROMPTA_TEST_MODE"] = "true"

@pytest.fixture
def cli_runner():
    """Create a Click test runner for CLI testing."""
    return click.testing.CliRunner()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.api_url = "http://localhost:8000"
    config.api_key = "test_api_key"
    config.timeout = 30
    return config

@pytest.fixture
def mock_client():
    """Mock Prompta client for testing."""
    client = Mock()
    
    # Mock common responses
    client.get_user_info.return_value = {
        "id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com"
    }
    
    client.get_projects.return_value = {
        "projects": [
            {
                "id": "project-1",
                "name": "Test Project",
                "description": "A test project",
                "tags": ["test"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "is_active": True,
                "is_public": False
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1
    }
    
    client.get_prompts.return_value = [
        {
            "id": "prompt-1",
            "name": "Test Prompt",
            "description": "A test prompt",
            "location": "test.md",
            "tags": ["test"],
            "is_public": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "current_version": {
                "id": "version-1",
                "version_number": 1,
                "content": "This is test content",
                "commit_message": "Initial version",
                "created_at": "2024-01-01T00:00:00Z",
                "is_current": True
            }
        }
    ]
    
    client.search_prompts.return_value = client.get_prompts.return_value
    
    return client

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API testing."""
    with patch('httpx.Client') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        
        mock_instance = Mock()
        mock_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_instance
        
        yield mock_instance

@pytest.fixture
def sample_prompt_file(temp_dir):
    """Create a sample prompt file for testing."""
    prompt_file = temp_dir / "sample_prompt.md"
    prompt_file.write_text("""# Sample Prompt

This is a sample prompt for testing purposes.

## Features
- Test feature 1
- Test feature 2

## Usage
Use this prompt for testing CLI functionality.
""")
    return prompt_file

@pytest.fixture(autouse=True)
def mock_auth_client():
    """Auto-mock authentication for all tests."""
    with patch('prompta.utils.auth.get_authenticated_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def env_vars():
    """Provide clean environment variables for testing."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "PROMPTA_API_URL": "http://localhost:8000",
        "PROMPTA_API_KEY": "test_api_key",
        "PROMPTA_TEST_MODE": "true"
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)