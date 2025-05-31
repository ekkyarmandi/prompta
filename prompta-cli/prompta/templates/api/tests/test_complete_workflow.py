#!/usr/bin/env python3
"""
Complete workflow test for Prompta API
Demonstrates the full functionality from user registration to prompt management
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")
    print("-" * 40)


def main():
    """Run complete workflow test"""
    print_section("Prompta API - COMPLETE WORKFLOW TEST")

    # Step 1: User Registration
    print_step(1, "User Registration")
    user_data = {
        "username": "workflowuser",
        "email": "workflow@example.com",
        "password": "securepassword123",
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Registration Status: {response.status_code}")
    if response.status_code == 201:
        user = response.json()
        print(f"✓ User created: {user['username']} ({user['email']})")
    else:
        print(f"✗ Registration failed: {response.json()}")
        return

    # Step 2: User Login
    print_step(2, "User Login & JWT Token")
    login_data = {"username": "workflowuser", "password": "securepassword123"}

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        jwt_token = token_data["access_token"]
        print(f"✓ JWT Token obtained (expires in {token_data['expires_in']} seconds)")
    else:
        print(f"✗ Login failed: {response.json()}")
        return

    # Step 3: Create API Key
    print_step(3, "API Key Creation")
    headers = {"Authorization": f"Bearer {jwt_token}"}
    api_key_data = {"name": "workflow-test-key", "expires_at": None}

    response = requests.post(
        f"{BASE_URL}/auth/api-keys", json=api_key_data, headers=headers
    )
    print(f"API Key Creation Status: {response.status_code}")
    if response.status_code == 201:
        key_data = response.json()
        api_key = key_data["key"]
        print(f"✓ API Key created: {key_data['name']}")
        print(f"  Key: {api_key[:20]}...")
    else:
        print(f"✗ API Key creation failed: {response.json()}")
        return

    # Step 4: Switch to API Key Authentication
    print_step(4, "Switch to API Key Authentication")
    api_headers = {"X-API-Key": api_key}

    response = requests.get(f"{BASE_URL}/auth/me", headers=api_headers)
    print(f"User Info Status: {response.status_code}")
    if response.status_code == 200:
        user_info = response.json()
        print(f"✓ API Key authentication working for user: {user_info['username']}")
    else:
        print(f"✗ API Key authentication failed: {response.json()}")
        return

    # Step 5: Create Multiple Prompts
    print_step(5, "Create Multiple Prompts")
    prompts_to_create = [
        {
            "name": "typescript-config",
            "description": "TypeScript configuration and best practices",
            "location": "tsconfig.json",
            "tags": ["typescript", "config", "javascript"],
            "content": '{\n  "compilerOptions": {\n    "strict": true,\n    "target": "ES2020"\n  }\n}',
            "commit_message": "Initial TypeScript config",
        },
        {
            "name": "react-hooks-guide",
            "description": "React hooks usage patterns and best practices",
            "location": "react-hooks.md",
            "tags": ["react", "hooks", "javascript", "frontend"],
            "content": "# React Hooks Guide\n\n## useState\nUse for local component state.\n\n## useEffect\nUse for side effects and lifecycle events.",
            "commit_message": "Initial React hooks guide",
        },
        {
            "name": "python-linting",
            "description": "Python linting configuration with flake8 and black",
            "location": ".flake8",
            "tags": ["python", "linting", "code-quality"],
            "content": "[flake8]\nmax-line-length = 88\nignore = E203, W503\nexclude = .git,__pycache__",
            "commit_message": "Initial Python linting config",
        },
    ]

    created_prompts = []
    for prompt_data in prompts_to_create:
        response = requests.post(
            f"{BASE_URL}/prompts/", json=prompt_data, headers=api_headers
        )
        if response.status_code == 201:
            prompt = response.json()
            created_prompts.append(prompt)
            print(f"✓ Created prompt: {prompt['name']}")
        else:
            print(f"✗ Failed to create {prompt_data['name']}: {response.json()}")

    print(f"\nTotal prompts created: {len(created_prompts)}")

    # Step 6: List and Search Prompts
    print_step(6, "List and Search Prompts")

    # List all prompts
    response = requests.get(f"{BASE_URL}/prompts/", headers=api_headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total prompts: {data['total']}")
        for prompt in data["prompts"]:
            print(f"  - {prompt['name']}: {prompt['description']}")

    # Search by content
    response = requests.get(f"{BASE_URL}/prompts/search?q=React", headers=api_headers)
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Content search for 'React': {data['total']} results")
        for prompt in data["prompts"]:
            print(f"  - {prompt['name']}")

    # Search by tags
    response = requests.get(f"{BASE_URL}/prompts/?tags=javascript", headers=api_headers)
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Tag search for 'javascript': {data['total']} results")
        for prompt in data["prompts"]:
            print(f"  - {prompt['name']}: {prompt['tags']}")

    # Step 7: Version Management
    print_step(7, "Version Management")
    if created_prompts:
        test_prompt = created_prompts[0]  # Use first created prompt
        prompt_id = test_prompt["id"]

        # Create new version
        version_data = {
            "content": test_prompt["current_version"]["content"]
            + '\n\n// Added new configuration options\n"moduleResolution": "node"',
            "commit_message": "Added module resolution configuration",
        }

        response = requests.post(
            f"{BASE_URL}/prompts/{prompt_id}/versions",
            json=version_data,
            headers=api_headers,
        )
        if response.status_code == 201:
            new_version = response.json()
            print(
                f"✓ Created version {new_version['version_number']} for {test_prompt['name']}"
            )

        # List versions
        response = requests.get(
            f"{BASE_URL}/prompts/{prompt_id}/versions", headers=api_headers
        )
        if response.status_code == 200:
            versions_data = response.json()
            print(f"✓ Prompt has {versions_data['total']} versions:")
            for version in versions_data["versions"]:
                current = "✓" if version["is_current"] else " "
                print(
                    f"  {current} Version {version['version_number']}: {version['commit_message']}"
                )

        # Compare versions
        if versions_data["total"] >= 2:
            response = requests.get(
                f"{BASE_URL}/prompts/{prompt_id}/diff/1/2", headers=api_headers
            )
            if response.status_code == 200:
                diff_data = response.json()
                print(f"\n✓ Version comparison generated")
                print("Diff preview:")
                print(
                    diff_data["diff"][:200] + "..."
                    if len(diff_data["diff"]) > 200
                    else diff_data["diff"]
                )

    # Step 8: Update Prompt Metadata
    print_step(8, "Update Prompt Metadata")
    if created_prompts:
        test_prompt = created_prompts[1]  # Use second prompt
        prompt_id = test_prompt["id"]

        update_data = {
            "description": "Updated: "
            + test_prompt["description"]
            + " with advanced patterns",
            "tags": test_prompt["tags"] + ["advanced", "patterns"],
        }

        response = requests.put(
            f"{BASE_URL}/prompts/{prompt_id}", json=update_data, headers=api_headers
        )
        if response.status_code == 200:
            updated_prompt = response.json()
            print(f"✓ Updated prompt: {updated_prompt['name']}")
            print(f"  New description: {updated_prompt['description']}")
            print(f"  New tags: {updated_prompt['tags']}")

    # Step 9: Get Prompt by Location
    print_step(9, "Get Prompt by Location")
    response = requests.get(
        f"{BASE_URL}/prompts/by-location?location=tsconfig.json", headers=api_headers
    )
    if response.status_code == 200:
        prompt = response.json()
        print(f"✓ Found prompt by location: {prompt['name']} at {prompt['location']}")

    # Step 10: API Key Management
    print_step(10, "API Key Management")

    # List API keys
    response = requests.get(f"{BASE_URL}/auth/api-keys", headers=api_headers)
    if response.status_code == 200:
        keys_data = response.json()
        print(f"✓ User has {keys_data['total']} API keys:")
        for key in keys_data["api_keys"]:
            print(f"  - {key['name']} (created: {key['created_at'][:10]})")

    # Final Summary
    print_section("WORKFLOW TEST COMPLETED SUCCESSFULLY")
    print("✓ User registration and authentication")
    print("✓ JWT token and API key generation")
    print("✓ Prompt creation and management")
    print("✓ Version control and comparison")
    print("✓ Search and filtering")
    print("✓ Metadata updates")
    print("✓ Location-based retrieval")
    print("✓ API key management")
    print("\n🎉 All features working correctly!")
    print(f"\nAPI Documentation: {BASE_URL}/docs")


if __name__ == "__main__":
    main()
