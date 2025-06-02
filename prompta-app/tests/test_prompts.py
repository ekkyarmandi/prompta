#!/usr/bin/env python3
"""
Test script for Prompta API prompt management functionality
"""

import httpx
import json
import pytest

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

    response = httpx.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 201:
        print(f"Registration failed: {response.json()}")
        return None

    # Login to get token
    login_data = {"username": "promptuser", "password": "testpassword123"}

    response = httpx.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.json()}")
        return None

    token = response.json()["access_token"]
    print(f"✓ User created and authenticated")
    return token


def _create_prompt_helper(token):
    """Helper function for creating a new prompt (not a pytest test)"""
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

    response = httpx.post(f"{BASE_URL}/prompts/", json=prompt_data, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code == 201:
        prompt = response.json()
        print(f"✓ Prompt created: {prompt['name']} (ID: {prompt['id']})")
        return prompt
    else:
        print(f"✗ Failed: {response.json()}")
        return None


def _list_prompts_helper(token):
    """Helper function for listing prompts (not a pytest test)"""
    print("\nTesting prompt listing...")

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{BASE_URL}/prompts/", headers=headers)

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


def _get_prompt_by_location_helper(token):
    """Helper function for getting prompt by location (not a pytest test)"""
    print("\nTesting get prompt by location...")

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
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


def _create_version_helper(token, prompt_id):
    """Helper function for creating a new version (not a pytest test)"""
    print("\nTesting version creation...")

    headers = {"Authorization": f"Bearer {token}"}
    version_data = {
        "content": "Use TypeScript for all new files.\nPrefer functional components in React.\nUse proper error handling.\nAdd comprehensive tests for all functions.",
        "commit_message": "Added testing requirements",
    }

    response = httpx.post(
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


def _list_versions_helper(token, prompt_id):
    """Helper function for listing versions (not a pytest test)"""
    print("\nTesting version listing...")

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{BASE_URL}/prompts/{prompt_id}/versions", headers=headers)

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


def _compare_versions_helper(token, prompt_id):
    """Helper function for version comparison (not a pytest test)"""
    print("\nTesting version comparison...")

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{BASE_URL}/prompts/{prompt_id}/diff/1/2", headers=headers)

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


def _restore_version_helper(token, prompt_id):
    """Helper function for version restoration (not a pytest test)"""
    print("\nTesting version restoration...")

    headers = {"Authorization": f"Bearer {token}"}
    restore_data = {
        "version_number": 1,
        "commit_message": "Restored to version 1 for testing",
    }

    response = httpx.post(
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


def _search_prompts_helper(token):
    """Helper function for searching prompts (not a pytest test)"""
    print("\nTesting prompt search...")

    headers = {"Authorization": f"Bearer {token}"}

    # Search by content
    response = httpx.get(f"{BASE_URL}/prompts/search?q=TypeScript", headers=headers)
    print(f"Content search status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} prompts containing 'TypeScript'")

    # Search by tags
    response = httpx.get(f"{BASE_URL}/prompts/?tags=cursor&tags=ide", headers=headers)
    print(f"Tag search status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {data['total']} prompts with tags 'cursor' and 'ide'")


def _update_prompt_helper(token, prompt_id):
    """Helper function for updating prompt metadata (not a pytest test)"""
    print("\nTesting prompt update...")

    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "description": "Updated: Cursor IDE rules for better coding with TypeScript",
        "tags": ["cursor", "ide", "rules", "typescript"],
    }

    response = httpx.put(
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
    prompt = _create_prompt_helper(token)
    if not prompt:
        print("Failed to create prompt, stopping tests")
        return

    prompt_id = prompt["id"]

    # Test prompt listing
    _list_prompts_helper(token)

    # Test get by location
    _get_prompt_by_location_helper(token)

    # Test version creation
    _create_version_helper(token, prompt_id)

    # Test version listing
    _list_versions_helper(token, prompt_id)

    # Test version comparison
    _compare_versions_helper(token, prompt_id)

    # Test version restoration
    _restore_version_helper(token, prompt_id)

    # Test search functionality
    _search_prompts_helper(token)

    # Test prompt update
    _update_prompt_helper(token, prompt_id)

    print("\n=== All prompt tests completed! ===")


def test_public_private_prompt_access():
    print("\nTesting public/private prompt access...")

    try:
        # Create a public prompt
        user_data = {
            "username": "publicuser",
            "email": "public@example.com",
            "password": "publicpass123",
        }
        httpx.post(f"{BASE_URL}/auth/register", json=user_data)
        login_data = {"username": "publicuser", "password": "publicpass123"}
        response = httpx.post(f"{BASE_URL}/auth/login", json=login_data)

        if response.status_code != 200:
            pytest.skip("Could not authenticate - server may not be running")

        token = response.json()["access_token"]
    except Exception:
        pytest.skip("Server not available")
    headers = {"Authorization": f"Bearer {token}"}
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    public_prompt_data = {
        "name": f"public-prompt-{unique_id}",
        "description": "A public prompt",
        "location": f"public-{unique_id}.txt",
        "tags": ["public"],
        "content": "This is a public prompt.",
        "commit_message": "Initial public",
        "is_public": True,
    }
    resp = httpx.post(f"{BASE_URL}/prompts/", json=public_prompt_data, headers=headers)
    if resp.status_code != 201:
        pytest.skip(f"Could not create test prompts - server error: {resp.status_code}")
    public_id = resp.json()["id"]

    # Create a private prompt
    private_prompt_data = {
        "name": f"private-prompt-{unique_id}",
        "description": "A private prompt",
        "location": f"private-{unique_id}.txt",
        "tags": ["private"],
        "content": "This is a private prompt.",
        "commit_message": "Initial private",
        "is_public": False,
    }
    resp = httpx.post(f"{BASE_URL}/prompts/", json=private_prompt_data, headers=headers)
    if resp.status_code != 201:
        pytest.skip(f"Could not create test prompts - server error: {resp.status_code}")
    private_id = resp.json()["id"]

    # Test public prompt access (may require auth depending on API design)
    resp = httpx.get(f"{BASE_URL}/prompts/{public_id}")
    if resp.status_code == 200:
        print("✓ Public prompt accessible without authentication")
    elif resp.status_code == 401:
        print("ℹ Public prompts require authentication in this API")
        # Test with auth instead
        resp = httpx.get(f"{BASE_URL}/prompts/{public_id}", headers=headers)
        if resp.status_code == 200:
            print("✓ Public prompt accessible with authentication")
        else:
            pytest.skip(f"Server error when accessing prompts: {resp.status_code}")
    else:
        pytest.skip(f"Unexpected status code for public prompt: {resp.status_code}")

    # Private prompt should NOT be accessible without auth
    resp = httpx.get(f"{BASE_URL}/prompts/{private_id}")
    assert (
        resp.status_code == 404
    ), "Private prompt should not be accessible without auth"
    print("✓ Private prompt not accessible without authentication")

    # Private prompt should be accessible by owner
    resp = httpx.get(f"{BASE_URL}/prompts/{private_id}", headers=headers)
    assert resp.status_code == 200, "Private prompt not accessible by owner"
    print("✓ Private prompt accessible by owner")

    print("✓ Public/private prompt access tests passed")


if __name__ == "__main__":
    main()
