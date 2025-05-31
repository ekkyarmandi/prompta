#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000"

# Get token
token_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "promptuser", "password": "testpassword123"},
)
token = token_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Testing tag search for python:")
resp = requests.get(f"{BASE_URL}/prompts/?tags=python", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f'Found {data["total"]} prompts')
    for prompt in data["prompts"]:
        print(f'  - {prompt["name"]}: {prompt["tags"]}')
else:
    print(f"Error: {resp.json()}")

print("\nTesting tag search for react:")
resp = requests.get(f"{BASE_URL}/prompts/?tags=react", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f'Found {data["total"]} prompts')
    for prompt in data["prompts"]:
        print(f'  - {prompt["name"]}: {prompt["tags"]}')
else:
    print(f"Error: {resp.json()}")
