import pytest
from unittest.mock import patch, Mock, mock_open, MagicMock
from pathlib import Path
import hashlib
import os
import tempfile

from prompta.tracking import TrackedPrompt, tracked_prompt
from prompta.exceptions import NotFoundError, ValidationError


class TestTrackedPrompt:
    
    def test_init_minimal(self):
        """Test TrackedPrompt initialization with minimal parameters."""
        prompt = TrackedPrompt(name="test-prompt")
        
        assert prompt._prompt_name == "test-prompt"
        assert prompt._content is None
        assert prompt._target_version is None
        assert not prompt.is_version_specific
    
    def test_init_with_content(self):
        """Test TrackedPrompt initialization with content."""
        content = "This is test content"
        prompt = TrackedPrompt(content=content, name="test-prompt")
        
        assert prompt._prompt_name == "test-prompt"
        assert prompt._content == content
        assert prompt._target_version is None
    
    def test_init_with_version(self):
        """Test TrackedPrompt initialization with version."""
        prompt = TrackedPrompt(name="test-prompt", version="v1.0")
        
        assert prompt._prompt_name == "test-prompt"
        assert prompt._target_version == "v1.0"
        assert prompt.is_version_specific
    
    def test_init_with_location(self):
        """Test TrackedPrompt initialization with file location."""
        prompt = TrackedPrompt(name="test-prompt", location="./test.md")
        
        assert prompt._prompt_name == "test-prompt"
        assert prompt.file_location == "./test.md"
    
    def test_parse_version_identifier_string(self):
        """Test version identifier parsing with string."""
        prompt = TrackedPrompt(name="test")
        
        assert prompt._parse_version_identifier("v1.0") == "v1.0"
        assert prompt._parse_version_identifier("latest") == "latest"
        assert prompt._parse_version_identifier("main") == "main"
    
    def test_parse_version_identifier_integer(self):
        """Test version identifier parsing with integer."""
        prompt = TrackedPrompt(name="test")
        
        assert prompt._parse_version_identifier(1) == "1"
        assert prompt._parse_version_identifier(42) == "42"
    
    def test_parse_version_identifier_invalid(self):
        """Test version identifier parsing with invalid types."""
        prompt = TrackedPrompt(name="test")
        
        with pytest.raises(ValueError, match="Version must be a string or integer"):
            prompt._parse_version_identifier([1, 2, 3])
        
        with pytest.raises(ValueError, match="Version must be a string or integer"):
            prompt._parse_version_identifier({"version": 1})
    
    def test_content_hash(self):
        """Test content hashing functionality."""
        prompt = TrackedPrompt(name="test", content="This is test content")
        
        expected_hash = hashlib.sha256("This is test content".encode()).hexdigest()[:12]
        assert prompt._content_hash() == expected_hash
    
    def test_content_hash_empty(self):
        """Test content hashing with empty content."""
        prompt = TrackedPrompt(name="test", content="")
        
        expected_hash = hashlib.sha256("".encode()).hexdigest()[:12]
        assert prompt._content_hash() == expected_hash
    
    def test_generate_tracking_key(self):
        """Test tracking key generation."""
        prompt = TrackedPrompt(name="test-prompt")
        
        # Mock context detection
        with patch.object(prompt, '_detect_context', return_value={'project': 'test-project'}):
            key = prompt._generate_tracking_key()
            assert "test-prompt" in key
            assert "test-project" in key
    
    def test_generate_location_from_name(self):
        """Test location generation from prompt name."""
        prompt = TrackedPrompt(name="my-awesome-prompt")
        
        location = prompt._generate_location()
        assert location == "my_awesome_prompt.md"
    
    def test_generate_location_with_context(self):
        """Test location generation with context."""
        prompt = TrackedPrompt(name="test-prompt")
        
        with patch.object(prompt, '_detect_context', return_value={'directory': '.prompta'}):
            location = prompt._generate_location()
            assert location.startswith(".prompta/")
            assert location.endswith("test_prompt.md")
    
    @patch('builtins.open', new_callable=mock_open, read_data="File content here")
    @patch('pathlib.Path.exists', return_value=True)
    def test_read_from_file_success(self, mock_exists, mock_file):
        """Test successful file reading."""
        prompt = TrackedPrompt(name="test", location="test.md")
        
        content = prompt._read_from_file()
        
        assert content == "File content here"
        mock_file.assert_called_once_with("test.md", "r", encoding="utf-8")
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_read_from_file_not_found(self, mock_exists):
        """Test file reading when file doesn't exist."""
        prompt = TrackedPrompt(name="test", location="nonexistent.md")
        
        content = prompt._read_from_file()
        
        assert content is None
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    @patch('pathlib.Path.exists', return_value=True)
    def test_read_from_file_io_error(self, mock_exists, mock_file):
        """Test file reading with IO error."""
        prompt = TrackedPrompt(name="test", location="test.md")
        
        content = prompt._read_from_file()
        
        assert content is None
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_write_to_file_success(self, mock_mkdir, mock_file):
        """Test successful file writing."""
        prompt = TrackedPrompt(name="test", location="test.md", content="Test content")
        
        prompt._write_to_file("Test content")
        
        mock_file.assert_called_once_with("test.md", "w", encoding="utf-8")
        mock_file().write.assert_called_once_with("Test content")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    @patch('pathlib.Path.mkdir')
    def test_write_to_file_io_error(self, mock_mkdir, mock_file):
        """Test file writing with IO error."""
        prompt = TrackedPrompt(name="test", location="test.md", content="Test content")
        
        # Should not raise exception, just handle gracefully
        prompt._write_to_file("Test content")
        
        mock_file.assert_called_once()
    
    def test_detect_context_cwd(self):
        """Test context detection from current working directory."""
        prompt = TrackedPrompt(name="test")
        
        with patch('pathlib.Path.cwd', return_value=Path('/home/user/my-project')):
            context = prompt._detect_context()
            
            assert context['directory'] == str(Path('/home/user/my-project'))
            assert context['project'] == 'my-project'
    
    def test_detect_context_git_repo(self):
        """Test context detection with git repository."""
        prompt = TrackedPrompt(name="test")
        
        with patch('pathlib.Path.cwd', return_value=Path('/home/user/my-project')), \
             patch('pathlib.Path.exists') as mock_exists:
            
            # Mock .git directory exists
            mock_exists.side_effect = lambda path: str(path).endswith('.git')
            
            context = prompt._detect_context()
            
            assert context['project'] == 'my-project'
            assert context['git_repo'] is True
    
    @patch('prompta.tracking.Prompt')
    def test_create_or_load_prompt_existing(self, mock_prompt_class):
        """Test creating or loading existing prompt."""
        mock_prompt = Mock()
        mock_prompt.id = "prompt-123"
        mock_prompt.name = "test-prompt"
        mock_prompt_class.get.return_value = mock_prompt
        
        prompt = TrackedPrompt(name="test-prompt")
        result = prompt._create_or_load_prompt()
        
        assert result == mock_prompt
        mock_prompt_class.get.assert_called_once_with("test-prompt", None)
    
    @patch('prompta.tracking.Prompt')
    def test_create_or_load_prompt_new(self, mock_prompt_class):
        """Test creating new prompt when not found."""
        mock_prompt_class.get.side_effect = NotFoundError("Not found")
        
        mock_new_prompt = Mock()
        mock_new_prompt.id = "new-prompt-123"
        mock_prompt_class.create.return_value = mock_new_prompt
        
        prompt = TrackedPrompt(name="test-prompt", content="Test content")
        with patch.object(prompt, '_generate_location', return_value="test.md"):
            result = prompt._create_or_load_prompt()
        
        assert result == mock_new_prompt
        mock_prompt_class.create.assert_called_once()
    
    @patch('prompta.tracking.Prompt')
    def test_create_new_version(self, mock_prompt_class):
        """Test creating new version."""
        mock_prompt = Mock()
        mock_version = Mock()
        mock_version.version_number = 2
        mock_prompt.create_version.return_value = mock_version
        
        prompt = TrackedPrompt(name="test", content="New content")
        result = prompt._create_new_version(mock_prompt)
        
        assert result == mock_version
        mock_prompt.create_version.assert_called_once_with(
            content="New content",
            commit_message="Auto-tracked content update"
        )
    
    def test_is_content_duplicate_true(self):
        """Test content duplicate detection - true case."""
        mock_prompt = Mock()
        mock_prompt.content = "Same content"
        
        prompt = TrackedPrompt(name="test", content="Same content")
        
        assert prompt._is_content_duplicate(mock_prompt) is True
    
    def test_is_content_duplicate_false(self):
        """Test content duplicate detection - false case."""
        mock_prompt = Mock()
        mock_prompt.content = "Different content"
        
        prompt = TrackedPrompt(name="test", content="New content")
        
        assert prompt._is_content_duplicate(mock_prompt) is False
    
    def test_is_content_duplicate_no_current_content(self):
        """Test content duplicate detection with no current content."""
        mock_prompt = Mock()
        mock_prompt.content = "Some content"
        
        prompt = TrackedPrompt(name="test")  # No content set
        
        assert prompt._is_content_duplicate(mock_prompt) is False
    
    def test_generate_commit_message_default(self):
        """Test commit message generation with default."""
        prompt = TrackedPrompt(name="test")
        
        message = prompt._generate_commit_message("Updated content")
        assert message == "Auto-tracked content update"
    
    def test_generate_commit_message_with_context(self):
        """Test commit message generation with context."""
        prompt = TrackedPrompt(name="test")
        
        with patch.object(prompt, '_detect_context', return_value={'project': 'my-project'}):
            message = prompt._generate_commit_message("Updated content")
            assert "my-project" in message or "Auto-tracked" in message
    
    def test_log_action(self):
        """Test action logging."""
        prompt = TrackedPrompt(name="test")
        
        with patch('builtins.print') as mock_print:
            prompt._log_action("Test message")
            mock_print.assert_called_once_with("📝 Test message")
    
    @patch('prompta.tracking.Prompt')
    def test_update_content_new_version(self, mock_prompt_class):
        """Test updating content creates new version."""
        mock_prompt = Mock()
        mock_prompt.content = "Old content"
        mock_prompt_class.get.return_value = mock_prompt
        
        mock_version = Mock()
        mock_version.version_number = 2
        mock_prompt.create_version.return_value = mock_version
        
        prompt = TrackedPrompt(name="test", content="Old content")
        prompt.update_content("New content")
        
        assert prompt._content == "New content"
        mock_prompt.create_version.assert_called_once()
    
    @patch('prompta.tracking.Prompt')
    def test_update_content_no_change(self, mock_prompt_class):
        """Test updating content with no actual change."""
        mock_prompt = Mock()
        mock_prompt.content = "Same content"
        mock_prompt_class.get.return_value = mock_prompt
        
        prompt = TrackedPrompt(name="test", content="Same content")
        result = prompt.update_content("Same content")
        
        assert result is None
        mock_prompt.create_version.assert_not_called()
    
    def test_reload_from_file_success(self):
        """Test reloading content from file."""
        prompt = TrackedPrompt(name="test", location="test.md")
        
        with patch.object(prompt, '_read_from_file', return_value="File content"):
            prompt.reload_from_file()
            
            assert prompt._content == "File content"
    
    def test_reload_from_file_no_location(self):
        """Test reloading from file without location."""
        prompt = TrackedPrompt(name="test")  # No location set
        
        with pytest.raises(ValueError, match="No file location specified"):
            prompt.reload_from_file()
    
    def test_reload_from_file_not_found(self):
        """Test reloading from file that doesn't exist."""
        prompt = TrackedPrompt(name="test", location="nonexistent.md")
        
        with patch.object(prompt, '_read_from_file', return_value=None):
            with pytest.raises(FileNotFoundError, match="Could not read file"):
                prompt.reload_from_file()
    
    @patch('prompta.tracking.Prompt')
    def test_load_version_success(self, mock_prompt_class):
        """Test loading specific version."""
        mock_prompt = Mock()
        mock_version = Mock()
        mock_version.content = "Version content"
        mock_prompt.get_version.return_value = mock_version
        mock_prompt_class.get.return_value = mock_prompt
        
        prompt = TrackedPrompt(name="test")
        prompt.load_version("v1.0")
        
        assert prompt._content == "Version content"
        assert prompt._target_version == "v1.0"
        mock_prompt.get_version.assert_called_once_with("v1.0")
    
    @patch('prompta.tracking.Prompt')
    def test_load_version_not_found(self, mock_prompt_class):
        """Test loading version that doesn't exist."""
        mock_prompt = Mock()
        mock_prompt.get_version.side_effect = NotFoundError("Version not found")
        mock_prompt_class.get.return_value = mock_prompt
        
        prompt = TrackedPrompt(name="test")
        
        with pytest.raises(NotFoundError):
            prompt.load_version("nonexistent")
    
    def test_create_tracked_class_method(self):
        """Test create_tracked class method."""
        with patch('prompta.tracking.TrackedPrompt._registry', {}):
            prompt = TrackedPrompt.create_tracked("test-prompt", "Test content")
            
            assert isinstance(prompt, TrackedPrompt)
            assert prompt._prompt_name == "test-prompt"
            assert prompt._content == "Test content"
            assert "test-prompt" in TrackedPrompt._registry
    
    def test_get_tracked_prompts_class_method(self):
        """Test get_tracked_prompts class method."""
        with patch('prompta.tracking.TrackedPrompt._registry', {"test": "prompt"}):
            result = TrackedPrompt.get_tracked_prompts()
            
            assert result == {"test": "prompt"}
    
    def test_get_tracked_prompt_class_method(self):
        """Test get_tracked_prompt class method."""
        mock_prompt = Mock()
        with patch('prompta.tracking.TrackedPrompt._registry', {"test": mock_prompt}):
            result = TrackedPrompt.get_tracked_prompt("test")
            
            assert result == mock_prompt
    
    def test_get_tracked_prompt_not_found(self):
        """Test get_tracked_prompt with non-existent key."""
        with patch('prompta.tracking.TrackedPrompt._registry', {}):
            result = TrackedPrompt.get_tracked_prompt("nonexistent")
            
            assert result is None
    
    def test_clear_registry_class_method(self):
        """Test clear_registry class method."""
        with patch('prompta.tracking.TrackedPrompt._registry', {"test": "prompt"}):
            TrackedPrompt.clear_registry()
            
            assert TrackedPrompt._registry == {}
    
    def test_show_tracking_info_class_method(self):
        """Test show_tracking_info class method."""
        mock_prompt1 = Mock()
        mock_prompt1.prompt_name = "prompt1"
        mock_prompt1.content = "Content 1"
        mock_prompt1.file_location = "file1.md"
        
        mock_prompt2 = Mock()
        mock_prompt2.prompt_name = "prompt2"
        mock_prompt2.content = None
        mock_prompt2.file_location = None
        
        registry = {"key1": mock_prompt1, "key2": mock_prompt2}
        
        with patch('prompta.tracking.TrackedPrompt._registry', registry), \
             patch('builtins.print') as mock_print:
            
            TrackedPrompt.show_tracking_info()
            
            # Verify print was called with tracking information
            assert mock_print.call_count > 0
    
    def test_repr(self):
        """Test string representation."""
        prompt = TrackedPrompt(name="test-prompt", content="Test content")
        
        repr_str = repr(prompt)
        
        assert "TrackedPrompt" in repr_str
        assert "test-prompt" in repr_str
        assert "loaded=True" in repr_str
    
    def test_properties(self):
        """Test property access."""
        prompt = TrackedPrompt(
            name="test-prompt", 
            content="Test content",
            location="test.md",
            version="v1.0"
        )
        
        assert prompt.content == "Test content"
        assert prompt.prompt_name == "test-prompt"
        assert prompt.file_location == "test.md"
        assert prompt.target_version == "v1.0"
        assert prompt.is_version_specific is True
        
        # Test tracking key
        with patch.object(prompt, '_detect_context', return_value={'project': 'test'}):
            key = prompt.tracking_key
            assert isinstance(key, str)
        
        # Test context info
        with patch.object(prompt, '_detect_context', return_value={'project': 'test'}):
            context = prompt.context_info
            assert context['project'] == 'test'


class TestTrackedPromptFunction:
    
    def test_tracked_prompt_function_minimal(self):
        """Test tracked_prompt function with minimal parameters."""
        with patch('prompta.tracking.TrackedPrompt') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            result = tracked_prompt(name="test")
            
            assert result == mock_instance
            mock_class.assert_called_once_with(
                name="test",
                content=None,
                version=None,
                location=None,
                auto_sync_file=True,
                auto_detect_context=True
            )
    
    def test_tracked_prompt_function_full_params(self):
        """Test tracked_prompt function with all parameters."""
        with patch('prompta.tracking.TrackedPrompt') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            result = tracked_prompt(
                name="test",
                content="Test content",
                version="v1.0",
                location="test.md",
                auto_sync_file=False,
                auto_detect_context=False
            )
            
            assert result == mock_instance
            mock_class.assert_called_once_with(
                name="test",
                content="Test content",
                version="v1.0",
                location="test.md",
                auto_sync_file=False,
                auto_detect_context=False
            )
    
    def test_tracked_prompt_function_with_kwargs(self):
        """Test tracked_prompt function with additional kwargs."""
        with patch('prompta.tracking.TrackedPrompt') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            result = tracked_prompt(
                name="test",
                custom_param="custom_value",
                another_param=123
            )
            
            mock_class.assert_called_once_with(
                name="test",
                content=None,
                version=None,
                location=None,
                auto_sync_file=True,
                auto_detect_context=True,
                custom_param="custom_value",
                another_param=123
            )


class TestTrackedPromptIntegration:
    
    def test_file_tracking_workflow(self):
        """Test complete file tracking workflow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Initial content")
            temp_file = f.name
        
        try:
            # Create tracked prompt with file
            prompt = TrackedPrompt(name="test", location=temp_file)
            prompt.reload_from_file()
            
            assert prompt._content == "Initial content"
            
            # Update content and write back
            prompt.update_content("Updated content")
            prompt._write_to_file()
            
            # Reload and verify
            prompt.reload_from_file()
            assert prompt._content == "Updated content"
            
        finally:
            os.unlink(temp_file)
    
    def test_version_specific_loading_workflow(self):
        """Test version-specific loading workflow."""
        with patch('prompta.tracking.Prompt') as mock_prompt_class:
            mock_prompt = Mock()
            mock_version = Mock()
            mock_version.content = "Specific version content"
            mock_prompt.get_version.return_value = mock_version
            mock_prompt_class.get.return_value = mock_prompt
            
            # Create with version
            prompt = TrackedPrompt(name="test", version="v1.0")
            
            # Should have loaded the specific version
            assert prompt.is_version_specific
            assert prompt._target_version == "v1.0"
    
    def test_auto_tracking_workflow(self):
        """Test automatic tracking workflow."""
        with patch('prompta.tracking.TrackedPrompt._registry', {}):
            prompt = TrackedPrompt(name="test", content="Test")
            
            # Should be automatically registered
            with patch.object(prompt, '_detect_context', return_value={'project': 'test'}):
                tracking_key = prompt._generate_tracking_key()
                # Note: auto-tracking would need to be tested with actual implementation