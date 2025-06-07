import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner

from prompta.commands.projects import project_group, list_command, download_command, create_command, show_command
from prompta.exceptions import NotFoundError, AuthenticationError, PromptaAPIError, ValidationError


class TestProjectCommands:
    
    def test_project_group_help(self, cli_runner):
        """Test project group help command."""
        result = cli_runner.invoke(project_group, ['--help'])
        
        assert result.exit_code == 0
        assert "Project management commands" in result.output
        assert "prompta project list" in result.output
        assert "prompta project show" in result.output

    def test_project_group_no_subcommand(self, cli_runner):
        """Test project group without subcommand shows help."""
        result = cli_runner.invoke(project_group)
        
        assert result.exit_code == 0
        assert "Project management commands" in result.output

    def test_list_command_success(self, cli_runner, mock_auth_client):
        """Test successful project listing."""
        mock_auth_client.get_projects.return_value = {
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
        
        result = cli_runner.invoke(list_command)
        
        assert result.exit_code == 0
        assert "Test Project" in result.output
        assert "project-1" in result.output
        mock_auth_client.get_projects.assert_called_once()

    def test_list_command_with_filters(self, cli_runner, mock_auth_client):
        """Test project listing with filters."""
        mock_auth_client.get_projects.return_value = {
            "projects": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "total_pages": 0
        }
        
        result = cli_runner.invoke(list_command, [
            '--query', 'test',
            '--tags', 'frontend,react',
            '--page', '2',
            '--page-size', '10'
        ])
        
        assert result.exit_code == 0
        mock_auth_client.get_projects.assert_called_once_with(
            query='test',
            tags=['frontend', 'react'],
            page=2,
            page_size=10
        )

    def test_list_command_no_projects(self, cli_runner, mock_auth_client):
        """Test project listing when no projects exist."""
        mock_auth_client.get_projects.return_value = {
            "projects": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0
        }
        
        result = cli_runner.invoke(list_command)
        
        assert result.exit_code == 0
        assert "No projects found" in result.output

    def test_list_command_auth_error(self, cli_runner, mock_auth_client):
        """Test project listing with authentication error."""
        mock_auth_client.get_projects.side_effect = AuthenticationError("Invalid API key")
        
        result = cli_runner.invoke(list_command)
        
        assert result.exit_code == 1
        assert "Authentication failed" in result.output

    def test_download_command_by_id(self, cli_runner, mock_auth_client):
        """Test project download by ID."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_auth_client.get_project_by_id.return_value = {
            "id": project_id,
            "name": "Test Project"
        }
        
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": [
                {
                    "id": "prompt-1",
                    "name": "Test Prompt",
                    "location": "test.md",
                    "current_version": {
                        "content": "# Test Content"
                    }
                }
            ]
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open_func("# Test Content")):
            
            result = cli_runner.invoke(download_command, [project_id])
            
            assert result.exit_code == 0
            assert "Downloading project: Test Project" in result.output
            assert "Downloaded 1 of 1 prompts" in result.output

    def test_download_command_by_name(self, cli_runner, mock_auth_client):
        """Test project download by name."""
        mock_auth_client.get_project_by_name.return_value = {
            "id": "project-1",
            "name": "Test Project"
        }
        
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": []
        }
        
        result = cli_runner.invoke(download_command, ["Test Project"])
        
        assert result.exit_code == 0
        assert "No prompts found in this project" in result.output

    def test_download_command_not_found(self, cli_runner, mock_auth_client):
        """Test project download when project not found."""
        mock_auth_client.get_project_by_name.side_effect = NotFoundError("Project not found")
        
        result = cli_runner.invoke(download_command, ["NonExistent"])
        
        assert result.exit_code == 1
        assert "No project found with name 'NonExistent'" in result.output

    def test_download_command_multiple_projects_error(self, cli_runner, mock_auth_client):
        """Test project download when multiple projects have same name."""
        mock_auth_client.get_project_by_name.side_effect = ValidationError("Multiple projects found")
        
        result = cli_runner.invoke(download_command, ["Duplicate Name"])
        
        assert result.exit_code == 1
        assert "Multiple projects found with the same name" in result.output

    def test_create_command_success(self, cli_runner, mock_auth_client):
        """Test successful project creation."""
        mock_auth_client.create_project.return_value = {
            "id": "new-project-id",
            "name": "New Project"
        }
        
        result = cli_runner.invoke(create_command, [
            '--name', 'New Project',
            '--description', 'A new test project',
            '--tags', 'test,cli',
            '--public'
        ])
        
        assert result.exit_code == 0
        assert "Created project 'New Project'" in result.output
        assert "new-project-id" in result.output
        
        mock_auth_client.create_project.assert_called_once_with({
            "name": "New Project",
            "description": "A new test project",
            "tags": ["test", "cli"],
            "is_public": True
        })

    def test_create_command_minimal(self, cli_runner, mock_auth_client):
        """Test project creation with minimal parameters."""
        mock_auth_client.create_project.return_value = {
            "id": "minimal-project-id",
            "name": "Minimal Project"
        }
        
        result = cli_runner.invoke(create_command, ['--name', 'Minimal Project'])
        
        assert result.exit_code == 0
        mock_auth_client.create_project.assert_called_once_with({
            "name": "Minimal Project",
            "description": None,
            "tags": [],
            "is_public": False
        })

    def test_create_command_validation_error(self, cli_runner, mock_auth_client):
        """Test project creation with validation error."""
        mock_auth_client.create_project.side_effect = ValidationError("Project name already exists")
        
        result = cli_runner.invoke(create_command, ['--name', 'Existing Project'])
        
        assert result.exit_code == 1
        assert "Project creation failed" in result.output

    def test_show_command_by_id(self, cli_runner, mock_auth_client):
        """Test showing project details by ID."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_auth_client.get_project_by_id.return_value = {
            "id": project_id,
            "name": "Test Project",
            "description": "A test project",
            "tags": ["test", "demo"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "is_active": True,
            "is_public": False
        }
        
        result = cli_runner.invoke(show_command, [project_id])
        
        assert result.exit_code == 0
        assert "Project: Test Project" in result.output
        assert f"ID: {project_id}" in result.output
        assert "Description: A test project" in result.output
        assert "Tags: test, demo" in result.output
        assert "Active: Yes" in result.output
        assert "Public: No" in result.output

    def test_show_command_by_name(self, cli_runner, mock_auth_client):
        """Test showing project details by name."""
        mock_auth_client.get_project_by_id.side_effect = NotFoundError("Not found by ID")
        mock_auth_client.get_project_by_name.return_value = {
            "id": "project-1",
            "name": "Test Project",
            "description": None,
            "tags": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "is_active": True,
            "is_public": True
        }
        
        result = cli_runner.invoke(show_command, ["Test Project"])
        
        assert result.exit_code == 0
        assert "Project: Test Project" in result.output
        assert "Public: Yes" in result.output

    def test_show_command_not_found(self, cli_runner, mock_auth_client):
        """Test showing project when not found."""
        mock_auth_client.get_project_by_name.side_effect = NotFoundError("Project not found")
        
        result = cli_runner.invoke(show_command, ["NonExistent"])
        
        assert result.exit_code == 1
        assert "Project not found" in result.output


class TestProjectHelperFunctions:
    
    def test_normalize_prompt_location_tilde(self):
        """Test location normalization with tilde prefix."""
        from prompta.commands.projects import _normalize_prompt_location
        
        result = _normalize_prompt_location("~/documents/prompt.md")
        assert result == "documents/prompt.md"

    def test_normalize_prompt_location_dot_slash(self):
        """Test location normalization with ./ prefix."""
        from prompta.commands.projects import _normalize_prompt_location
        
        result = _normalize_prompt_location("./src/prompt.md")
        assert result == "src/prompt.md"

    def test_normalize_prompt_location_hidden_dir(self):
        """Test location normalization preserves hidden directories."""
        from prompta.commands.projects import _normalize_prompt_location
        
        result = _normalize_prompt_location(".cursor/rules/prompt.md")
        assert result == ".cursor/rules/prompt.md"

    def test_normalize_prompt_location_no_change(self):
        """Test location normalization when no change needed."""
        from prompta.commands.projects import _normalize_prompt_location
        
        result = _normalize_prompt_location("src/prompt.md")
        assert result == "src/prompt.md"


def mock_open_func(content):
    """Helper function to create mock open for file writing tests."""
    from unittest.mock import mock_open
    return mock_open()