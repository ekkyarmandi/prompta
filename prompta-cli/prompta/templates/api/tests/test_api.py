#!/usr/bin/env python3
"""
Simple test script to verify the Prompta API authentication functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_user_registration():
    """Test user registration"""
    print("Testing user registration...")
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpassword123",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json() if response.status_code == 201 else None


def test_user_login(username, password):
    """Test user login"""
    print("Testing user login...")
    login_data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json()["access_token"] if response.status_code == 200 else None


def test_get_user_info(token=None, api_key=None):
    """Test getting user info with JWT or API key"""
    print("Testing get user info...")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key:
        headers["X-API-Key"] = api_key

    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_create_api_key(token):
    """Test creating an API key"""
    print("Testing API key creation...")
    headers = {"Authorization": f"Bearer {token}"}
    api_key_data = {"name": "test-cli-key"}

    response = requests.post(
        f"{BASE_URL}/auth/api-keys", json=api_key_data, headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    return response.json()["key"] if response.status_code == 201 else None


def test_list_api_keys(token=None, api_key=None):
    """Test listing API keys"""
    print("Testing API key listing...")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key:
        headers["X-API-Key"] = api_key

    response = requests.get(f"{BASE_URL}/auth/api-keys", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def main():
    """Run all tests"""
    print("=== Prompta API Authentication Tests ===\n")

    # Test health
    test_health()

    # Test user registration
    user = test_user_registration()
    if not user:
        print("User registration failed, stopping tests")
        return

    # Test login
    token = test_user_login("testuser2", "testpassword123")
    if not token:
        print("Login failed, stopping tests")
        return

    # Test getting user info with JWT
    test_get_user_info(token=token)

    # Test creating API key
    api_key = test_create_api_key(token)
    if not api_key:
        print("API key creation failed")
        return

    # Test getting user info with API key
    test_get_user_info(api_key=api_key)

    # Test listing API keys with JWT
    test_list_api_keys(token=token)

    # Test listing API keys with API key
    test_list_api_keys(api_key=api_key)

    print("=== All tests completed! ===")


if __name__ == "__main__":
    main()
