#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Prompta API tests
"""

import os
import sys
import pytest
import httpx

# Add the project root directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up test environment
os.environ.setdefault("TESTING", "True")
os.environ.setdefault("APP_NAME", "Prompta API Test")
os.environ.setdefault("APP_VERSION", "1.0.0")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("API_KEY_EXPIRE_DAYS", "365")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("RATE_LIMIT_REQUESTS", "100")
os.environ.setdefault("RATE_LIMIT_WINDOW", "60")

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the API"""
    return BASE_URL


@pytest.fixture(scope="session")
def test_user_credentials():
    """Test user credentials"""
    return {
        "username": "pytestuser",
        "email": "pytest@example.com",
        "password": "pytestpass123",
    }


@pytest.fixture(scope="session")
def auth_token(test_user_credentials):
    """Get authentication token for testing"""
    try:
        # Try to register user (might already exist)
        httpx.post(f"{BASE_URL}/auth/register", json=test_user_credentials)

        # Login to get token
        login_data = {
            "username": test_user_credentials["username"],
            "password": test_user_credentials["password"],
        }
        response = httpx.post(f"{BASE_URL}/auth/login", json=login_data)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            pytest.skip(f"Could not authenticate: {response.status_code}")
    except Exception as e:
        pytest.skip(f"Server not available: {e}")


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers for API requests"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_prompt_data():
    """Sample prompt data for testing"""
    return {
        "name": "pytest-test-prompt",
        "description": "A test prompt created by pytest",
        "location": "pytest_test.md",
        "tags": ["pytest", "test", "automation"],
        "content": "This is a test prompt created by pytest automation.",
        "commit_message": "Initial pytest test prompt",
    }


@pytest.fixture
def created_prompt(auth_headers, test_prompt_data):
    """Create a test prompt and return its data"""
    try:
        response = httpx.post(
            f"{BASE_URL}/prompts/", json=test_prompt_data, headers=auth_headers
        )
        if response.status_code == 201:
            prompt = response.json()
            yield prompt
            # Cleanup: delete the prompt after test
            try:
                httpx.delete(f"{BASE_URL}/prompts/{prompt['id']}", headers=auth_headers)
            except:
                pass  # Ignore cleanup errors
        else:
            pytest.skip(f"Could not create test prompt: {response.status_code}")
    except Exception as e:
        pytest.skip(f"Server not available: {e}")


@pytest.fixture
def prompt_id(created_prompt):
    """Get the ID of a created test prompt"""
    return created_prompt["id"]


# Add pytest-asyncio plugin support
pytest_plugins = ["pytest_asyncio"]


# Mock database session fixture
@pytest.fixture
def mock_db():
    """Create a mock database session for unit tests"""
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    return mock_session


# Mock user fixture
@pytest.fixture
def mock_user():
    """Create a mock user for unit tests"""
    from unittest.mock import MagicMock

    mock_user = MagicMock()
    mock_user.id = "00000000-0000-0000-0000-000000000000"
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    return mock_user
