import pytest
from unittest.mock import patch, Mock, mock_open
from click.testing import CliRunner
from pathlib import Path

from prompta.commands.export import (
    export_group, project_command, prompt_command, all_command, get_command
)
from prompta.exceptions import NotFoundError, AuthenticationError, PromptaAPIError, ValidationError


class TestExportCommands:
    
    def test_export_group_help(self, cli_runner):
        """Test export group help command."""
        result = cli_runner.invoke(export_group, ['--help'])
        
        assert result.exit_code == 0
        assert "Export and download commands" in result.output
        assert "prompta export project" in result.output
        assert "prompta export prompt" in result.output

    def test_export_group_no_subcommand(self, cli_runner):
        """Test export group without subcommand shows help."""
        result = cli_runner.invoke(export_group)
        
        assert result.exit_code == 0
        assert "Export and download commands" in result.output

    def test_project_command_files_format(self, cli_runner, mock_auth_client):
        """Test project export as files."""
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": [
                {
                    "id": "prompt-1",
                    "name": "Test Prompt",
                    "location": "test.md",
                    "current_version": {
                        "content": "# Test Content\n\nThis is test content."
                    }
                }
            ]
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = cli_runner.invoke(project_command, [
                'Test Project',
                '--format', 'files'
            ])
            
            assert result.exit_code == 0
            assert "Exporting project: Test Project" in result.output
            assert "Exported 1 of 1 prompts" in result.output
            mock_file.assert_called()

    def test_project_command_json_format(self, cli_runner, mock_auth_client):
        """Test project export as JSON."""
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": [
                {
                    "id": "prompt-1",
                    "name": "Test Prompt",
                    "location": "test.md",
                    "description": "A test prompt",
                    "tags": ["test"],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "current_version": {
                        "version_number": 1,
                        "content": "Test content",
                        "commit_message": "Initial version"
                    }
                }
            ]
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            result = cli_runner.invoke(project_command, [
                'Test Project',
                '--format', 'json',
                '--include-metadata'
            ])
            
            assert result.exit_code == 0
            assert "Exported 1 prompts to" in result.output
            mock_json_dump.assert_called_once()

    def test_project_command_no_prompts(self, cli_runner, mock_auth_client):
        """Test project export when no prompts exist."""
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": []
        }
        
        result = cli_runner.invoke(project_command, ['Empty Project'])
        
        assert result.exit_code == 0
        assert "No prompts found in this project" in result.output

    def test_project_command_not_found(self, cli_runner, mock_auth_client):
        """Test project export when project not found."""
        mock_auth_client.download_prompts_by_project.side_effect = NotFoundError("Project not found")
        
        result = cli_runner.invoke(project_command, ['NonExistent'])
        
        assert result.exit_code == 1
        assert "Project not found" in result.output

    def test_prompt_command_success(self, cli_runner, mock_auth_client):
        """Test successful prompt export."""
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
            
            result = cli_runner.invoke(prompt_command, ['Test Prompt'])
            
            assert result.exit_code == 0
            assert "Exported prompt 'Test Prompt'" in result.output
            mock_file.assert_called()

    def test_prompt_command_custom_output(self, cli_runner, mock_auth_client):
        """Test prompt export with custom output path."""
        mock_auth_client.get_prompt.return_value = {
            "name": "Test Prompt",
            "location": "test.md",
            "current_version": {"content": "Content"}
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = cli_runner.invoke(prompt_command, [
                'Test Prompt',
                '--output', 'custom.md'
            ])
            
            assert result.exit_code == 0

    def test_prompt_command_not_found(self, cli_runner, mock_auth_client):
        """Test prompt export when prompt not found."""
        mock_auth_client.get_prompt.side_effect = NotFoundError("Prompt not found")
        
        result = cli_runner.invoke(prompt_command, ['NonExistent'])
        
        assert result.exit_code == 1
        assert "Prompt not found" in result.output

    def test_all_command_files_format(self, cli_runner, mock_auth_client):
        """Test export all prompts as files."""
        mock_auth_client.get_prompts.return_value = [
            {
                "id": "prompt-1",
                "name": "Test Prompt 1",
                "location": "test1.md",
                "current_version": {"content": "Content 1"}
            },
            {
                "id": "prompt-2", 
                "name": "Test Prompt 2",
                "location": "test2.md",
                "current_version": {"content": "Content 2"}
            }
        ]
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = cli_runner.invoke(all_command, [
                '--tags', 'test,sample',
                '--format', 'files'
            ])
            
            assert result.exit_code == 0
            assert "Exporting prompts with tags: test, sample" in result.output
            assert "Exported 2 of 2 prompts" in result.output

    def test_all_command_json_format(self, cli_runner, mock_auth_client):
        """Test export all prompts as JSON."""
        mock_auth_client.get_prompts.return_value = [
            {
                "id": "prompt-1",
                "name": "Test Prompt",
                "location": "test.md",
                "tags": ["test"],
                "current_version": {"content": "Content"}
            }
        ]
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()), \
             patch('json.dump') as mock_json_dump:
            
            result = cli_runner.invoke(all_command, [
                '--query', 'test',
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            mock_json_dump.assert_called_once()

    def test_all_command_with_search_query(self, cli_runner, mock_auth_client):
        """Test export all with search query."""
        mock_auth_client.search_prompts.return_value = [
            {
                "name": "React Component",
                "location": "react.md",
                "tags": ["react"],
                "current_version": {"content": "React content"}
            }
        ]
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = cli_runner.invoke(all_command, [
                '--query', 'react',
                '--tags', 'frontend'
            ])
            
            assert result.exit_code == 0
            mock_auth_client.search_prompts.assert_called_once_with('react')

    def test_all_command_no_prompts(self, cli_runner, mock_auth_client):
        """Test export all when no prompts match criteria."""
        mock_auth_client.get_prompts.return_value = []
        
        result = cli_runner.invoke(all_command, ['--tags', 'nonexistent'])
        
        assert result.exit_code == 0
        assert "No prompts found matching the specified criteria" in result.output

    def test_get_command_project_priority(self, cli_runner, mock_auth_client):
        """Test get command prioritizes project for UUID."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_auth_client.get_project_by_id.return_value = {
            "id": project_id,
            "name": "Test Project"
        }
        
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": []
        }
        
        result = cli_runner.invoke(get_command, [project_id])
        
        assert result.exit_code == 0
        mock_auth_client.get_project_by_id.assert_called_once_with(project_id)

    def test_get_command_prompt_fallback(self, cli_runner, mock_auth_client):
        """Test get command falls back to prompt when project not found."""
        identifier = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_auth_client.get_project_by_id.side_effect = NotFoundError("Project not found")
        mock_auth_client.get_prompt_by_id.return_value = {
            "name": "Test Prompt",
            "location": "test.md",
            "current_version": {"content": "Content"}
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = cli_runner.invoke(get_command, [identifier])
            
            assert result.exit_code == 0
            mock_auth_client.get_prompt_by_id.assert_called_once_with(identifier)

    def test_get_command_name_prompt_priority(self, cli_runner, mock_auth_client):
        """Test get command prioritizes prompt for names."""
        mock_auth_client.get_prompt_by_name.return_value = {
            "name": "Test Prompt",
            "location": "test.md",
            "current_version": {"content": "Content"}
        }
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()):
            
            result = cli_runner.invoke(get_command, ["Test Name"])
            
            assert result.exit_code == 0
            mock_auth_client.get_prompt_by_name.assert_called_once_with("Test Name")

    def test_get_command_project_option(self, cli_runner, mock_auth_client):
        """Test get command with --project option."""
        mock_auth_client.get_project_by_name.return_value = {
            "name": "Test Project"
        }
        
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": []
        }
        
        result = cli_runner.invoke(get_command, ['--project', 'Test Project'])
        
        assert result.exit_code == 0
        mock_auth_client.get_project_by_name.assert_called_once_with('Test Project')

    def test_get_command_conflicting_args(self, cli_runner):
        """Test get command with conflicting arguments."""
        result = cli_runner.invoke(get_command, [
            'identifier',
            '--project', 'project_name'
        ])
        
        assert result.exit_code == 1
        assert "Cannot specify both IDENTIFIER argument and --project option" in result.output

    def test_get_command_missing_args(self, cli_runner):
        """Test get command with missing arguments."""
        result = cli_runner.invoke(get_command)
        
        assert result.exit_code == 1
        assert "You must specify either IDENTIFIER" in result.output

    def test_get_command_not_found(self, cli_runner, mock_auth_client):
        """Test get command when resource not found."""
        mock_auth_client.get_prompt_by_name.side_effect = NotFoundError("Not found")
        mock_auth_client.get_project_by_name.side_effect = NotFoundError("Not found")
        
        result = cli_runner.invoke(get_command, ['NonExistent'])
        
        assert result.exit_code == 1
        assert "No project or prompt found" in result.output


class TestExportHelperFunctions:
    
    def test_normalize_prompt_location(self):
        """Test prompt location normalization."""
        from prompta.commands.export import _normalize_prompt_location
        
        # Test tilde replacement
        assert _normalize_prompt_location("~/docs/prompt.md") == "docs/prompt.md"
        
        # Test ./ prefix removal
        assert _normalize_prompt_location("./src/prompt.md") == "src/prompt.md"
        
        # Test hidden directory preservation
        assert _normalize_prompt_location(".cursor/rules.md") == ".cursor/rules.md"
        
        # Test no change needed
        assert _normalize_prompt_location("src/prompt.md") == "src/prompt.md"

    def test_download_project_prompts_integration(self, cli_runner, mock_auth_client):
        """Test the complete project download flow."""
        from prompta.commands.export import _download_project_prompts
        
        mock_auth_client.download_prompts_by_project.return_value = {
            "prompts": [
                {
                    "name": "Prompt 1",
                    "location": "dir1/prompt1.md",
                    "current_version": {"content": "Content 1"}
                },
                {
                    "name": "Prompt 2", 
                    "location": ".hidden/prompt2.md",
                    "current_version": {"content": "Content 2"}
                }
            ]
        }
        
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', mock_open()) as mock_file:
            
            _download_project_prompts(mock_auth_client, "Test Project", None)
            
            # Verify directories were created
            assert mock_mkdir.call_count >= 2
            
            # Verify files were written
            assert mock_file.call_count == 2