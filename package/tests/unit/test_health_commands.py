import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner
import httpx

from prompta.commands.health import health_group, ping_command, _check_api_status, _check_api_key_status, _get_config_sources


class TestHealthCommands:
    
    def test_health_group_basic(self, cli_runner):
        """Test basic health command execution."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._check_api_key_status') as mock_key_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "http://localhost:8000", "source": "Default value"},
                "api_key": {"value": "test_key", "source": "Test"}
            }
            mock_api_status.return_value = (True, "API is responding (HTTP 200)")
            mock_key_status.return_value = (True, "API key is valid")
            
            result = cli_runner.invoke(health_group)
            
            assert result.exit_code == 0
            assert "Prompta CLI Status" in result.output
            assert "Server Connection:" in result.output
            assert "API Authentication:" in result.output
            assert "✅" in result.output

    def test_health_group_with_custom_api_key(self, cli_runner):
        """Test health command with custom API key."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._check_api_key_status') as mock_key_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "http://localhost:8000", "source": "Default value"},
                "api_key": {"value": "custom_key", "source": "CLI flag (--api-key)"}
            }
            mock_api_status.return_value = (True, "API is responding (HTTP 200)")
            mock_key_status.return_value = (True, "API key is valid")
            
            result = cli_runner.invoke(health_group, ['--api-key', 'custom_key'])
            
            assert result.exit_code == 0
            assert "CLI flag (--api-key)" in result.output

    def test_health_group_server_down(self, cli_runner):
        """Test health command when server is down."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "http://localhost:8000", "source": "Default value"},
                "api_key": {"value": "test_key", "source": "Test"}
            }
            mock_api_status.return_value = (False, "Connection failed: Connection refused")
            
            result = cli_runner.invoke(health_group)
            
            assert result.exit_code == 0
            assert "❌" in result.output
            assert "Connection failed" in result.output
            assert "Quick Setup:" in result.output

    def test_health_group_no_api_key(self, cli_runner):
        """Test health command when no API key is configured."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "http://localhost:8000", "source": "Default value"},
                "api_key": {"value": None, "source": None}
            }
            mock_api_status.return_value = (True, "API is responding (HTTP 200)")
            
            result = cli_runner.invoke(health_group)
            
            assert result.exit_code == 0
            assert "No API key configured" in result.output
            assert "Set your API key:" in result.output

    def test_ping_command_success(self, cli_runner):
        """Test ping command when server responds."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "http://localhost:8000", "source": "Default value"},
                "api_key": {"value": None, "source": None}
            }
            mock_api_status.return_value = (True, "API is responding (HTTP 200)")
            
            result = cli_runner.invoke(ping_command)
            
            assert result.exit_code == 0
            assert "🏓 Pinging http://localhost:8000..." in result.output
            assert "✅ API is responding" in result.output

    def test_ping_command_failure(self, cli_runner):
        """Test ping command when server doesn't respond."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "http://localhost:8000", "source": "Default value"},
                "api_key": {"value": None, "source": None}
            }
            mock_api_status.return_value = (False, "Connection failed")
            
            result = cli_runner.invoke(ping_command)
            
            assert result.exit_code == 1
            assert "❌ Connection failed" in result.output

    def test_ping_command_custom_url(self, cli_runner):
        """Test ping command with custom API URL."""
        with patch('prompta.commands.health._check_api_status') as mock_api_status, \
             patch('prompta.commands.health._get_config_sources') as mock_config:
            
            mock_config.return_value = {
                "api_url": {"value": "https://custom-api.com", "source": "CLI flag (--api-url)"},
                "api_key": {"value": None, "source": None}
            }
            mock_api_status.return_value = (True, "API is responding (HTTP 200)")
            
            result = cli_runner.invoke(ping_command, ['--api-url', 'https://custom-api.com'])
            
            assert result.exit_code == 0
            assert "🏓 Pinging https://custom-api.com..." in result.output


class TestHealthHelperFunctions:
    
    def test_check_api_status_success(self):
        """Test API status check when server responds."""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_instance = Mock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_instance
            
            is_live, message = _check_api_status("http://localhost:8000")
            
            assert is_live is True
            assert "API is responding" in message
            assert "HTTP 200" in message

    def test_check_api_status_connection_error(self):
        """Test API status check when connection fails."""
        with patch('httpx.Client') as mock_client:
            mock_instance = Mock()
            mock_instance.get.side_effect = httpx.RequestError("Connection refused")
            mock_client.return_value.__enter__.return_value = mock_instance
            
            is_live, message = _check_api_status("http://localhost:8000")
            
            assert is_live is False
            assert "Connection failed" in message

    def test_check_api_status_server_error(self):
        """Test API status check when server returns error."""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            
            mock_instance = Mock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_instance
            
            is_live, message = _check_api_status("http://localhost:8000")
            
            assert is_live is True  # Still considered "live" even with 500
            assert "HTTP 500" in message

    def test_check_api_key_status_no_key(self):
        """Test API key status check when no key is provided."""
        is_valid, message = _check_api_key_status(None, "http://localhost:8000")
        
        assert is_valid is False
        assert "No API key found" in message

    def test_check_api_key_status_valid(self):
        """Test API key status check with valid key."""
        with patch('prompta.commands.health.ConfigManager') as mock_config_manager, \
             patch('prompta.commands.health.PromptaClient') as mock_client_class:
            
            mock_config = Mock()
            mock_config_manager.return_value.config = mock_config
            
            mock_client = Mock()
            mock_client.get_user_info.return_value = {"username": "testuser"}
            mock_client_class.return_value = mock_client
            
            is_valid, message = _check_api_key_status("valid_key", "http://localhost:8000")
            
            assert is_valid is True
            assert "testuser" in message

    def test_check_api_key_status_invalid(self):
        """Test API key status check with invalid key."""
        with patch('prompta.commands.health.ConfigManager') as mock_config_manager, \
             patch('prompta.commands.health.PromptaClient') as mock_client_class:
            
            mock_config = Mock()
            mock_config_manager.return_value.config = mock_config
            
            mock_client = Mock()
            mock_client.get_user_info.side_effect = Exception("401 Unauthorized")
            mock_client.get_prompts.side_effect = Exception("401 Unauthorized")
            mock_client_class.return_value = mock_client
            
            is_valid, message = _check_api_key_status("invalid_key", "http://localhost:8000")
            
            assert is_valid is False
            assert "authentication failed" in message.lower()

    def test_get_config_sources_priority(self):
        """Test configuration source priority."""
        with patch('os.getenv') as mock_getenv, \
             patch('prompta.commands.health.dotenv_values') as mock_dotenv, \
             patch('prompta.commands.health._load_prompta') as mock_load_prompta, \
             patch('pathlib.Path.exists') as mock_exists:
            
            # Setup mocks
            mock_getenv.side_effect = lambda key: {
                'PROMPTA_API_KEY': 'env_key',
                'PROMPTA_API_URL': 'env_url'
            }.get(key)
            
            mock_dotenv.return_value = {
                'PROMPTA_API_KEY': 'dotenv_key',
                'PROMPTA_API_URL': 'dotenv_url'
            }
            
            mock_load_prompta.return_value = {
                'PROMPTA_API_KEY': 'prompta_key',
                'PROMPTA_API_URL': 'prompta_url'
            }
            
            mock_exists.return_value = True
            
            # Test CLI flags have highest priority
            sources = _get_config_sources('cli_key', 'cli_url')
            
            assert sources['api_key']['value'] == 'cli_key'
            assert sources['api_key']['source'] == 'CLI flag (--api-key)'
            assert sources['api_url']['value'] == 'cli_url'
            assert sources['api_url']['source'] == 'CLI flag (--api-url)'
            
            # Test environment variables have second priority
            sources = _get_config_sources(None, None)
            
            assert sources['api_key']['value'] == 'env_key'
            assert sources['api_key']['source'] == 'Environment variable (PROMPTA_API_KEY)'
            assert sources['api_url']['value'] == 'env_url'
            assert sources['api_url']['source'] == 'Environment variable (PROMPTA_API_URL)'

    def test_get_config_sources_defaults(self):
        """Test configuration defaults when nothing is configured."""
        with patch('os.getenv', return_value=None), \
             patch('prompta.commands.health.dotenv_values', return_value={}), \
             patch('prompta.commands.health._load_prompta', return_value={}), \
             patch('pathlib.Path.exists', return_value=False):
            
            sources = _get_config_sources(None, None)
            
            assert sources['api_url']['value'] == 'http://localhost:8000'
            assert sources['api_url']['source'] == ''
            assert sources['api_key']['value'] is None