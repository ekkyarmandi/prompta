import pytest
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner

from prompta.commands.projects import list_command, _normalize_prompt_location


class TestProjectCommandsSimple:
    
    def test_normalize_prompt_location_tilde(self):
        """Test location normalization with tilde prefix."""
        result = _normalize_prompt_location("~/documents/prompt.md")
        assert result == "documents/prompt.md"

    def test_normalize_prompt_location_dot_slash(self):
        """Test location normalization with ./ prefix."""
        result = _normalize_prompt_location("./src/prompt.md")
        assert result == "src/prompt.md"

    def test_normalize_prompt_location_hidden_dir(self):
        """Test location normalization preserves hidden directories."""
        result = _normalize_prompt_location(".cursor/rules/prompt.md")
        assert result == ".cursor/rules/prompt.md"

    def test_normalize_prompt_location_no_change(self):
        """Test location normalization when no change needed."""
        result = _normalize_prompt_location("src/prompt.md")
        assert result == "src/prompt.md"

    @patch('prompta.utils.auth.get_authenticated_client')
    def test_list_command_with_mocked_client(self, mock_get_client):
        """Test list command with properly mocked client."""
        # Setup mock client
        mock_client = Mock()
        mock_client.get_projects.return_value = {
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
        mock_get_client.return_value = mock_client
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(list_command, [])
        
        # Verify
        assert result.exit_code == 0
        assert "Test Project" in result.output
        mock_client.get_projects.assert_called_once()

    @patch('prompta.utils.auth.get_authenticated_client')
    def test_list_command_no_projects(self, mock_get_client):
        """Test list command when no projects exist."""
        # Setup mock client
        mock_client = Mock()
        mock_client.get_projects.return_value = {
            "projects": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0
        }
        mock_get_client.return_value = mock_client
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(list_command, [])
        
        # Verify
        assert result.exit_code == 0
        assert "No projects found" in result.output
        mock_client.get_projects.assert_called_once()

    @patch('prompta.utils.auth.get_authenticated_client')
    def test_list_command_with_filters(self, mock_get_client):
        """Test list command with filters."""
        # Setup mock client
        mock_client = Mock()
        mock_client.get_projects.return_value = {
            "projects": [],
            "total": 0,
            "page": 2,
            "page_size": 10,
            "total_pages": 0
        }
        mock_get_client.return_value = mock_client
        
        # Run command with filters
        runner = CliRunner()
        result = runner.invoke(list_command, [
            '--query', 'test',
            '--tags', 'frontend,react',
            '--page', '2',
            '--page-size', '10'
        ])
        
        # Verify
        assert result.exit_code == 0
        mock_client.get_projects.assert_called_once_with(
            query='test',
            tags=['frontend', 'react'],
            page=2,
            page_size=10
        )