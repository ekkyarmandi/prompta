#!/usr/bin/env python3
"""
Test script for Prompta API prompt management functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def setup_user_and_get_token():
    """Create a user and get authentication token"""
    print("Setting up test user...")

    # Register user
    user_data = {
        "username": "promptuser",
        "email": "prompt@example.com",
        "password": "testpassword123",
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 201:
        print(f"Registration failed: {response.json()}")
        return None

    # Login to get token
    login_data = {"username": "promptuser", "password": "testpassword123"}

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.json()}")
        return None

    token = response.json()["access_token"]
    print(f"✓ User created and authenticated")
    return token


def test_create_prompt(token):
    """Test creating a new prompt"""
    print("\nTesting prompt creation...")

    headers = {"Authorization": f"Bearer {token}"}
    prompt_data = {
        "name": "cursor-rules",
        "description": "Cursor IDE rules for better coding",
        "location": ".cursorrules",
        "tags": ["cursor", "ide", "rules"],
        "content": "Use TypeScript for all new files.\nPrefer functional components in React.\nUse proper error handling.",
        "commit_message": "Initial cursor rules",
    }

    response = requests.post(f"{BASE_URL}/prompts/", json=prompt_data, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 201:
        prompt = response.json()
        print(f"✓ Prompt created: {prompt['name']} (ID: {prompt['id']})")
        return prompt
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def test_list_prompts(token):
    """Test listing prompts"""
    print("\nTesting prompt listing...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts/", headers=headers)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} prompts")
        for prompt in data["prompts"]:
            print(f"  - {prompt['name']}: {prompt['description']}")
        return data["prompts"]
    else:
        print(f"✗ Failed: {response.json()}")
        return []


def test_get_prompt_by_location(token):
    """Test getting prompt by location"""
    print("\nTesting get prompt by location...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/prompts/by-location?location=.cursorrules", headers=headers
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        prompt = response.json()
        print(f"✓ Found prompt at location: {prompt['name']}")
        return prompt
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def test_create_version(token, prompt_id):
    """Test creating a new version"""
    print("\nTesting version creation...")

    headers = {"Authorization": f"Bearer {token}"}
    version_data = {
        "content": "Use TypeScript for all new files.\nPrefer functional components in React.\nUse proper error handling.\nAdd comprehensive tests for all functions.",
        "commit_message": "Added testing requirements",
    }

    response = requests.post(
        f"{BASE_URL}/prompts/{prompt_id}/versions", json=version_data, headers=headers
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 201:
        version = response.json()
        print(f"✓ Version {version['version_number']} created")
        return version
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def test_list_versions(token, prompt_id):
    """Test listing versions"""
    print("\nTesting version listing...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts/{prompt_id}/versions", headers=headers)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} versions")
        for version in data["versions"]:
            current = "✓" if version["is_current"] else " "
            print(
                f"  {current} Version {version['version_number']}: {version['commit_message']}"
            )
        return data["versions"]
    else:
        print(f"✗ Failed: {response.json()}")
        return []


def test_compare_versions(token, prompt_id):
    """Test version comparison"""
    print("\nTesting version comparison...")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts/{prompt_id}/diff/1/2", headers=headers)

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Diff generated between versions 1 and 2")
        print("Diff preview:")
        print(data["diff"][:200] + "..." if len(data["diff"]) > 200 else data["diff"])
        return data
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def test_restore_version(token, prompt_id):
    """Test version restoration"""
    print("\nTesting version restoration...")

    headers = {"Authorization": f"Bearer {token}"}
    restore_data = {
        "version_number": 1,
        "commit_message": "Restored to version 1 for testing",
    }

    response = requests.post(
        f"{BASE_URL}/prompts/{prompt_id}/restore/1", json=restore_data, headers=headers
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        version = response.json()
        print(
            f"✓ Restored to version 1, created new version {version['version_number']}"
        )
        return version
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def test_search_prompts(token):
    """Test searching prompts"""
    print("\nTesting prompt search...")

    headers = {"Authorization": f"Bearer {token}"}

    # Search by content
    response = requests.get(f"{BASE_URL}/prompts/search?q=TypeScript", headers=headers)
    print(f"Content search status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} prompts containing 'TypeScript'")

    # Search by tags
    response = requests.get(
        f"{BASE_URL}/prompts/?tags=cursor&tags=ide", headers=headers
    )
    print(f"Tag search status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} prompts with tags 'cursor' and 'ide'")


def test_update_prompt(token, prompt_id):
    """Test updating prompt metadata"""
    print("\nTesting prompt update...")

    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "description": "Updated: Cursor IDE rules for better coding with TypeScript",
        "tags": ["cursor", "ide", "rules", "typescript"],
    }

    response = requests.put(
        f"{BASE_URL}/prompts/{prompt_id}", json=update_data, headers=headers
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        prompt = response.json()
        print(f"✓ Prompt updated: {prompt['description']}")
        print(f"  Tags: {prompt['tags']}")
        return prompt
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def main():
    """Run all prompt tests"""
    print("=== Prompta API Prompt Management Tests ===\n")

    # Setup
    token = setup_user_and_get_token()
    if not token:
        print("Failed to setup user, stopping tests")
        return

    # Test prompt creation
    prompt = test_create_prompt(token)
    if not prompt:
        print("Failed to create prompt, stopping tests")
        return

    prompt_id = prompt["id"]

    # Test prompt listing
    test_list_prompts(token)

    # Test get by location
    test_get_prompt_by_location(token)

    # Test version creation
    test_create_version(token, prompt_id)

    # Test version listing
    test_list_versions(token, prompt_id)

    # Test version comparison
    test_compare_versions(token, prompt_id)

    # Test version restoration
    test_restore_version(token, prompt_id)

    # Test search functionality
    test_search_prompts(token)

    # Test prompt update
    test_update_prompt(token, prompt_id)

    print("\n=== All prompt tests completed! ===")


if __name__ == "__main__":
    main()
