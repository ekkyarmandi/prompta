#!/usr/bin/env python3
"""
Example usage of Prompta interface objects.

This demonstrates how to use the Project and Prompt classes to interact
with the Prompta API without dealing with HTTP requests directly.
"""

from prompta import Project, Prompt


def main():
    """Demo of the interface objects."""
    print("Prompta Interface Objects Example")
    print("=" * 40)

    try:
        # 1. List all projects
        print("\n1. Listing all projects:")
        projects = Project.list()
        for project in projects:
            print(f"  - {project.name} (ID: {project.id})")
            print(f"    Description: {project.description}")
            print(f"    Tags: {project.tags}")
            print(f"    Public: {project.is_public}")

        # 2. Create a new project
        print("\n2. Creating a new project:")
        new_project = Project.create(
            name="Example Project",
            description="A test project created via interface objects",
            tags=["example", "test"],
            is_public=False,
        )
        print(f"Created project: {new_project.name} (ID: {new_project.id})")

        # 3. Create a prompt in the project
        print("\n3. Creating a prompt in the project:")
        new_prompt = Prompt.create(
            name="Example Prompt",
            content="Please summarize the following text: {text}",
            location="examples/summary.txt",
            description="An example summarization prompt",
            project_id=new_project.id,
            tags=["summary", "example"],
            commit_message="Initial version",
        )
        print(f"Created prompt: {new_prompt.name} (ID: {new_prompt.id})")
        print(f"Content: {new_prompt.content}")

        # 4. Create a new version of the prompt
        print("\n4. Creating a new version:")
        new_version = new_prompt.create_version(
            content="Please provide a detailed summary of the following text: {text}",
            commit_message="Made summary more detailed",
        )
        print(f"Created version {new_version.version_number}")
        print(f"New content: {new_prompt.content}")

        # 5. List prompts in the project
        print("\n5. Listing prompts in the project:")
        project_prompts = new_project.get_prompts()
        for prompt in project_prompts:
            print(f"  - {prompt.name} ({prompt.location})")
            print(f"    Content: {prompt.content[:50]}...")

        # 6. Search for prompts
        print("\n6. Searching for prompts:")
        search_results = Prompt.search("summary")
        for prompt in search_results:
            print(f"  - {prompt.name}: {prompt.description}")

        # 7. Get a specific project and prompt
        print("\n7. Getting specific items:")
        retrieved_project = Project.get(new_project.id)
        print(f"Retrieved project: {retrieved_project.name}")

        retrieved_prompt = Prompt.get(new_prompt.id)
        print(f"Retrieved prompt: {retrieved_prompt.name}")

        # 8. Update the project
        print("\n8. Updating the project:")
        retrieved_project.description = "Updated description"
        retrieved_project.tags.append("updated")
        retrieved_project.save()
        print(f"Updated project description: {retrieved_project.description}")
        print(f"Updated tags: {retrieved_project.tags}")

        print("\n✅ Example completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. A Prompta API server running")
        print("2. PROMPTA_API_KEY environment variable set")
        print("3. Valid API key with proper permissions")


if __name__ == "__main__":
    main()
