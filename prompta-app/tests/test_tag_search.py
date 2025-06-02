#!/usr/bin/env python3
import httpx
import pytest

BASE_URL = "http://localhost:8000"


def get_auth_token():
    """Get authentication token for testing"""
    try:
        token_resp = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"username": "promptuser", "password": "testpassword123"},
        )
        if token_resp.status_code == 200:
            data = token_resp.json()
            return data.get("access_token")
        else:
            return None
    except Exception:
        return None


def test_tag_search_python():
    """Test tag search for python"""
    token = get_auth_token()
    if not token:
        pytest.skip("Could not authenticate - server may not be running")

    headers = {"Authorization": f"Bearer {token}"}

    print("Testing tag search for python:")
    resp = httpx.get(f"{BASE_URL}/prompts/?tags=python", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f'Found {data["total"]} prompts')
        for prompt in data["prompts"]:
            print(f'  - {prompt["name"]}: {prompt["tags"]}')
    else:
        print(f"Error: {resp.json()}")


def test_tag_search_react():
    """Test tag search for react"""
    token = get_auth_token()
    if not token:
        pytest.skip("Could not authenticate - server may not be running")

    headers = {"Authorization": f"Bearer {token}"}

    print("\nTesting tag search for react:")
    resp = httpx.get(f"{BASE_URL}/prompts/?tags=react", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f'Found {data["total"]} prompts')
        for prompt in data["prompts"]:
            print(f'  - {prompt["name"]}: {prompt["tags"]}')
    else:
        print(f"Error: {resp.json()}")


if __name__ == "__main__":
    # Legacy script mode for backwards compatibility
    token = get_auth_token()
    if token:
        headers = {"Authorization": f"Bearer {token}"}

        print("Testing tag search for python:")
        resp = httpx.get(f"{BASE_URL}/prompts/?tags=python", headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f'Found {data["total"]} prompts')
            for prompt in data["prompts"]:
                print(f'  - {prompt["name"]}: {prompt["tags"]}')
        else:
            print(f"Error: {resp.json()}")

        print("\nTesting tag search for react:")
        resp = httpx.get(f"{BASE_URL}/prompts/?tags=react", headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f'Found {data["total"]} prompts')
            for prompt in data["prompts"]:
                print(f'  - {prompt["name"]}: {prompt["tags"]}')
        else:
            print(f"Error: {resp.json()}")
    else:
        print("Could not authenticate - server may not be running")
