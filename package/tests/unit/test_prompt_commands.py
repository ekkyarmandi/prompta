import pytest
from unittest.mock import patch, Mock, mock_open
from click.testing import CliRunner
from pathlib import Path

from prompta.commands.prompts import (
    prompt_group, list_command, show_command, get_command, 
    save_command, delete_command, info_command, search_command,
    version_group, list_versions_command, show_version_command,
    create_version_command, restore_version_command, diff_command
)
from prompta.exceptions import NotFoundError, AuthenticationError, PromptaAPIError, ValidationError


class TestPromptCommands:
    
    def test_prompt_group_help(self, cli_runner):
        """Test prompt group help command."""
        result = cli_runner.invoke(prompt_group, ['--help'])
        
        assert result.exit_code == 0
        assert "Prompt management commands" in result.output
        assert "prompta prompt list" in result.output
        assert "prompta prompt show" in result.output

    def test_prompt_group_no_subcommand(self, cli_runner):
        """Test prompt group without subcommand shows help."""
        result = cli_runner.invoke(prompt_group)
        
        assert result.exit_code == 0
        assert "Prompt management commands" in result.output

    def test_list_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt listing."""
        mock_auth_client.get_prompts.return_value = [
            {
                "id": "prompt-1",
                "name": "Test Prompt",
                "description": "A test prompt",
                "location": "test.md",
                "tags": ["test"],
                "current_version": {
                    "version_number": 1,
                    "content": "Test content"
                }
            }
        ]
        
        result = cli_runner.invoke(list_command)
        
        assert result.exit_code == 0
        assert "Test Prompt" in result.output
        assert "test.md" in result.output
        mock_auth_client.get_prompts.assert_called_once()

    def test_list_command_with_query(self, cli_runner, mock_auth_client):
        """Test prompt listing with search query."""
        mock_auth_client.search_prompts.return_value = [
            {
                "id": "prompt-1",
                "name": "React Component",
                "location": "components.md",
                "tags": ["react"],
                "current_version": {"version_number": 1}
            }
        ]
        
        result = cli_runner.invoke(list_command, ['--query', 'react'])
        
        assert result.exit_code == 0
        assert "React Component" in result.output
        mock_auth_client.search_prompts.assert_called_once_with('react')

    def test_list_command_with_filters(self, cli_runner, mock_auth_client):
        """Test prompt listing with filters."""
        mock_auth_client.get_prompts.return_value = []
        
        result = cli_runner.invoke(list_command, [
            '--tags', 'python,ai',
            '--location', 'src/',
            '--page', '2',
            '--page-size', '10'
        ])
        
        assert result.exit_code == 0
        mock_auth_client.get_prompts.assert_called_once_with(
            tags=['python', 'ai'],
            location='src/',
            limit=10,
            offset=10
        )

    def test_list_command_no_prompts(self, cli_runner, mock_auth_client):
        """Test prompt listing when no prompts exist."""
        mock_auth_client.get_prompts.return_value = []
        
        result = cli_runner.invoke(list_command)
        
        assert result.exit_code == 0
        assert "No prompts found" in result.output

    def test_show_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt display."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt",
            "description": "A test prompt",
            "location": "test.md",
            "tags": ["test"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "current_version": {
                "version_number": 1,
                "content": "# Test Content\n\nThis is test content."
            }
        }
        
        with patch('rich.console.Console'):
            result = cli_runner.invoke(show_command, ['Test Prompt'])
            
            assert result.exit_code == 0
            mock_auth_client.get_prompt.assert_called_once_with('Test Prompt', None)

    def test_show_command_with_version(self, cli_runner, mock_auth_client):
        """Test showing specific version of prompt."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt",
            "location": "test.md",
            "current_version": {"version_number": 2}
        }
        
        mock_auth_client.get_versions.return_value = [
            {
                "version_number": 1,
                "content": "Old content"
            }
        ]
        
        with patch('rich.console.Console'):
            result = cli_runner.invoke(show_command, ['Test Prompt', '--version', '1'])
            
            assert result.exit_code == 0
            mock_auth_client.get_versions.assert_called_once_with('prompt-1')

    def test_show_command_not_found(self, cli_runner, mock_auth_client):
        """Test showing prompt when not found."""
        mock_auth_client.get_prompt.side_effect = NotFoundError("Prompt not found")
        
        result = cli_runner.invoke(show_command, ['NonExistent'])
        
        assert result.exit_code == 1
        assert "Prompt not found" in result.output

    def test_get_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt download."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt",
            "location": "test.md",
            "current_version": {
                "content": "# Test Content"
            }
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = cli_runner.invoke(get_command, ['Test Prompt'])
            
            assert result.exit_code == 0
            assert "Downloaded 'Test Prompt'" in result.output
            mock_file.assert_called_once()

    def test_get_command_with_output(self, cli_runner, mock_auth_client):
        """Test prompt download with custom output path."""
        mock_auth_client.get_prompt.return_value = {
            "name": "Test Prompt",
            "location": "test.md",
            "current_version": {"content": "Content"}
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = cli_runner.invoke(get_command, ['Test Prompt', '--output', 'custom.md'])
            
            assert result.exit_code == 0

    def test_create_command_success(self, cli_runner, mock_auth_client, sample_prompt_file):
        """Test successful prompt creation."""
        mock_auth_client.create_prompt.return_value = {
            "id": "new-prompt-id",
            "name": "New Prompt"
        }
        
        result = cli_runner.invoke(save_command, [
            str(sample_prompt_file),
            '--name', 'New Prompt',
            '--description', 'A new test prompt',
            '--tags', 'test,sample',
            '--message', 'Initial creation'
        ])
        
        assert result.exit_code == 0
        assert "Created prompt 'New Prompt' successfully" in result.output
        mock_auth_client.create_prompt.assert_called_once()

    def test_create_command_file_not_found(self, cli_runner):
        """Test prompt creation when file doesn't exist."""
        result = cli_runner.invoke(save_command, ['nonexistent.md'])
        
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_delete_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt deletion."""
        mock_auth_client.get_prompt_by_name.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt"
        }
        
        with patch('click.confirm', return_value=True):
            result = cli_runner.invoke(delete_command, ['Test Prompt'])
            
            assert result.exit_code == 0
            assert "Deleted 'Test Prompt' successfully" in result.output
            mock_auth_client.delete_prompt.assert_called_once_with('prompt-1')

    def test_delete_command_cancelled(self, cli_runner, mock_auth_client):
        """Test prompt deletion when user cancels."""
        mock_auth_client.get_prompt_by_name.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt"
        }
        
        with patch('click.confirm', return_value=False):
            result = cli_runner.invoke(delete_command, ['Test Prompt'])
            
            assert result.exit_code == 0
            assert "Cancelled" in result.output
            mock_auth_client.delete_prompt.assert_not_called()

    def test_info_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt info display."""
        mock_auth_client.get_prompt_by_name.return_value = {
            "name": "Test Prompt",
            "description": "A test prompt",
            "location": "test.md",
            "tags": ["test", "sample"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "current_version": {
                "version_number": 2,
                "created_at": "2024-01-01T01:00:00Z"
            }
        }
        
        result = cli_runner.invoke(info_command, ['Test Prompt'])
        
        assert result.exit_code == 0
        assert "Name: Test Prompt" in result.output
        assert "Description: A test prompt" in result.output
        assert "Current Version: 2" in result.output

    def test_search_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt search."""
        mock_auth_client.search_prompts.return_value = [
            {
                "name": "React Component",
                "description": "Component prompt",
                "location": "components.md",
                "tags": ["react", "frontend"]
            }
        ]
        
        result = cli_runner.invoke(search_command, ['react'])
        
        assert result.exit_code == 0
        assert "Found 1 prompt(s)" in result.output
        assert "React Component" in result.output
        mock_auth_client.search_prompts.assert_called_once_with('react')

    def test_search_command_no_results(self, cli_runner, mock_auth_client):
        """Test prompt search with no results."""
        mock_auth_client.search_prompts.return_value = []
        
        result = cli_runner.invoke(search_command, ['nonexistent'])
        
        assert result.exit_code == 0
        assert "No prompts found matching your search" in result.output


class TestVersionCommands:
    
    def test_list_versions_command_success(self, cli_runner, mock_auth_client):
        """Test successful version listing."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt"
        }
        
        mock_auth_client.get_versions.return_value = [
            {
                "version_number": 2,
                "created_at": "2024-01-01T01:00:00Z",
                "commit_message": "Updated content",
                "is_current": True
            },
            {
                "version_number": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "commit_message": "Initial version",
                "is_current": False
            }
        ]
        
        result = cli_runner.invoke(list_versions_command, ['Test Prompt'])
        
        assert result.exit_code == 0
        assert "Versions for prompt 'Test Prompt'" in result.output
        assert "✓ Version 2" in result.output
        assert "  Version 1" in result.output

    def test_show_version_command_success(self, cli_runner, mock_auth_client):
        """Test successful version display."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt",
            "location": "test.md"
        }
        
        mock_auth_client.get_versions.return_value = [
            {
                "version_number": 1,
                "content": "Version 1 content",
                "commit_message": "Initial version",
                "created_at": "2024-01-01T00:00:00Z",
                "is_current": False
            }
        ]
        
        with patch('rich.console.Console'):
            result = cli_runner.invoke(show_version_command, ['Test Prompt', '1'])
            
            assert result.exit_code == 0

    def test_create_version_command_success(self, cli_runner, mock_auth_client, sample_prompt_file):
        """Test successful version creation."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt"
        }
        
        mock_auth_client.create_version.return_value = {
            "version_number": 2
        }
        
        result = cli_runner.invoke(create_version_command, [
            'Test Prompt',
            str(sample_prompt_file),
            '--message', 'Updated version'
        ])
        
        assert result.exit_code == 0
        assert "Created version 2 for 'Test Prompt'" in result.output

    def test_restore_version_command_success(self, cli_runner, mock_auth_client):
        """Test successful version restoration."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt"
        }
        
        mock_auth_client.restore_version.return_value = {
            "version_number": 3
        }
        
        with patch('click.confirm', return_value=True):
            result = cli_runner.invoke(restore_version_command, [
                'Test Prompt', '1',
                '--message', 'Restored to version 1'
            ])
            
            assert result.exit_code == 0
            assert "Restored 'Test Prompt' to version 1" in result.output
            assert "Created new version 3" in result.output

    def test_diff_command_success(self, cli_runner, mock_auth_client):
        """Test successful version comparison."""
        mock_auth_client.get_prompt.return_value = {
            "id": "prompt-1",
            "name": "Test Prompt"
        }
        
        mock_auth_client.compare_versions.return_value = "--- Version 1\n+++ Version 2\n@@ -1,1 +1,1 @@\n-Old content\n+New content"
        
        result = cli_runner.invoke(diff_command, ['Test Prompt', '1', '2'])
        
        assert result.exit_code == 0
        assert "Diff for 'Test Prompt' (v1 → v2)" in result.output
        assert "Old content" in result.output
        assert "New content" in result.output


class TestPromptHelperFunctions:
    
    def test_normalize_prompt_location(self):
        """Test prompt location normalization."""
        from prompta.commands.prompts import _normalize_prompt_location
        
        # Test tilde replacement
        assert _normalize_prompt_location("~/docs/prompt.md") == "docs/prompt.md"
        
        # Test ./ prefix removal
        assert _normalize_prompt_location("./src/prompt.md") == "src/prompt.md"
        
        # Test hidden directory preservation
        assert _normalize_prompt_location(".cursor/rules.md") == ".cursor/rules.md"
        
        # Test no change needed
        assert _normalize_prompt_location("src/prompt.md") == "src/prompt.md"