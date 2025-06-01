#!/usr/bin/env python3
"""
Script to create additional test prompts for search functionality
"""

import requests

BASE_URL = "http://localhost:8000"


def get_token():
    """Login and get token"""
    login_data = {"username": "promptuser", "password": "testpassword123"}

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def create_sample_prompts(token):
    """Create several sample prompts"""
    headers = {"Authorization": f"Bearer {token}"}

    prompts = [
        {
            "name": "python-best-practices",
            "description": "Python coding best practices and conventions",
            "location": "python_rules.md",
            "tags": ["python", "best-practices", "coding"],
            "content": "Use type hints for all function parameters and return values.\nFollow PEP 8 style guidelines.\nWrite docstrings for all functions and classes.\nUse list comprehensions when appropriate.",
            "commit_message": "Initial Python best practices",
        },
        {
            "name": "react-component-guide",
            "description": "Guidelines for creating React components",
            "location": "react_guide.md",
            "tags": ["react", "javascript", "frontend", "components"],
            "content": "Use functional components with hooks.\nImplement proper prop validation with PropTypes.\nKeep components small and focused.\nUse meaningful component names.",
            "commit_message": "Initial React component guidelines",
        },
        {
            "name": "api-design-principles",
            "description": "RESTful API design principles and standards",
            "location": "api_standards.md",
            "tags": ["api", "rest", "backend", "design"],
            "content": "Use proper HTTP status codes.\nImplement consistent error handling.\nVersion your APIs properly.\nUse meaningful resource names.",
            "commit_message": "Initial API design principles",
        },
        {
            "name": "git-workflow",
            "description": "Git workflow and commit message conventions",
            "location": "git_workflow.md",
            "tags": ["git", "workflow", "version-control"],
            "content": "Use conventional commit messages.\nCreate feature branches for new work.\nRebase before merging to main.\nWrite descriptive commit messages.",
            "commit_message": "Initial Git workflow guide",
        },
    ]

    created_prompts = []
    for prompt_data in prompts:
        response = requests.post(
            f"{BASE_URL}/prompts/", json=prompt_data, headers=headers
        )
        if response.status_code == 201:
            prompt = response.json()
            print(f"✓ Created: {prompt['name']}")
            created_prompts.append(prompt)
        else:
            print(f"✗ Failed to create {prompt_data['name']}: {response.json()}")

    return created_prompts


def test_advanced_search(token):
    """Test various search scenarios"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== Testing Advanced Search ===")

    # Search by content
    print("\n1. Content search for 'function':")
    response = requests.get(f"{BASE_URL}/prompts/search?q=function", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} prompts")
        for prompt in data["prompts"]:
            print(f"   - {prompt['name']}")

    # Search by tags
    print("\n2. Tag search for 'python':")
    response = requests.get(f"{BASE_URL}/prompts/?tags=python", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} prompts")
        for prompt in data["prompts"]:
            print(f"   - {prompt['name']}: {prompt['tags']}")

    # Search by location pattern
    print("\n3. Location search for '.md':")
    response = requests.get(f"{BASE_URL}/prompts/?location=.md", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} prompts")
        for prompt in data["prompts"]:
            print(f"   - {prompt['name']}: {prompt['location']}")

    # Combined search
    print("\n4. Combined search (query + tags):")
    response = requests.get(
        f"{BASE_URL}/prompts/?query=component&tags=react", headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} prompts")
        for prompt in data["prompts"]:
            print(f"   - {prompt['name']}")


def main():
    """Create sample prompts and test search"""
    print("=== Creating Additional Test Prompts ===")

    token = get_token()
    if not token:
        print("Failed to get authentication token")
        return

    # Create sample prompts
    created_prompts = create_sample_prompts(token)
    print(f"\nCreated {len(created_prompts)} additional prompts")

    # Test search functionality
    test_advanced_search(token)

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
