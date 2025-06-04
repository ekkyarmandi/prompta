#!/usr/bin/env python3
"""Test the new Prompta interface objects."""

from prompta import Project, Prompt, PromptVersion

# Test basic imports and object creation
print("Testing Prompta interface objects...")

# Test creating objects without API calls
project = Project(name="Test Project", description="A test project")
print(f"Created project object: {project}")

prompt = Prompt(name="Test Prompt", location="test.txt")
print(f"Created prompt object: {prompt}")

version = PromptVersion(version_number=1, content="Test content")
print(f"Created version object: {version}")

print("✅ Interface objects imported and created successfully!")
