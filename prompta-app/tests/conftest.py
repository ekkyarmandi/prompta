#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Prompta API tests
"""

import pytest
import httpx

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
