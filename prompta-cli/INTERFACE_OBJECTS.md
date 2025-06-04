# Prompta Interface Objects

The Prompta CLI package now provides interface objects that allow you to interact with your Prompta API directly from Python code without dealing with HTTP requests or connection details.

## Installation

Install the Prompta CLI package:

```bash
pip install prompta
```

## Configuration

The interface objects automatically use your existing Prompta configuration. Set up your API key using any of these methods:

1. **Environment Variable (Recommended)**:

   ```bash
   export PROMPTA_API_KEY="your-api-key-here"
   export PROMPTA_API_URL="http://localhost:8000"  # Optional, defaults to localhost
   ```

2. **`.env` file in your project**:

   ```
   PROMPTA_API_KEY=your-api-key-here
   PROMPTA_API_URL=http://localhost:8000
   ```

3. **Global `~/.prompta` file**:
   ```
   PROMPTA_API_KEY="your-api-key-here"
   PROMPTA_API_URL="http://localhost:8000"
   ```

## Quick Start

```python
from prompta import Project, Prompt, PromptVersion

# Create a new project
project = Project.create(
    name="My AI Project",
    description="Collection of AI prompts for automation",
    tags=["ai", "automation"],
    is_public=False
)

# Create a prompt in the project
prompt = Prompt.create(
    name="Email Generator",
    content="Generate a professional email about: {topic}",
    location="emails/generator.txt",
    description="Generates professional emails",
    project_id=project.id,
    tags=["email", "business"]
)

print(f"Created: {project.name} with prompt: {prompt.name}")
print(f"Prompt content: {prompt.content}")
```

## API Reference

### Project Class

#### Creating Projects

```python
# Create a new project
project = Project.create(
    name="Project Name",
    description="Optional description",
    tags=["tag1", "tag2"],
    is_public=False
)

# Or create an instance and save
project = Project(
    name="Project Name",
    description="My project",
    tags=["ai", "test"]
)
project.save()
```

#### Retrieving Projects

```python
# Get project by ID or name
project = Project.get("project-id-or-name")

# List all projects
projects = Project.list()

# List with filtering
projects = Project.list(
    query="search term",
    tags=["ai"],
    page=1,
    page_size=20
)
```

#### Working with Projects

```python
# Update project
project.description = "Updated description"
project.tags.append("new-tag")
project.save()

# Get prompts in project
prompts = project.get_prompts()

# Delete project
project.delete()
```

### Prompt Class

#### Creating Prompts

```python
# Create a new prompt
prompt = Prompt.create(
    name="Summarizer",
    content="Summarize this text: {text}",
    location="prompts/summarizer.txt",
    description="Text summarization prompt",
    project_id="project-id",  # Optional
    tags=["summary", "text"],
    commit_message="Initial version",
    is_public=False
)
```

#### Retrieving Prompts

```python
# Get prompt by ID or name
prompt = Prompt.get("prompt-id-or-name")

# Get prompt by name with project filter (handles duplicates)
prompt = Prompt.get("prompt-name", project_id="project-id")

# List prompts with filtering
prompts = Prompt.list(
    tags=["ai"],
    location="prompts/",
    project_id="project-id",
    limit=10
)

# Search prompts by content
results = Prompt.search("machine learning")
```

#### Working with Prompts

```python
# Update prompt metadata
prompt.description = "Updated description"
prompt.tags.append("new-tag")
prompt.save()

# Update prompt with new content (creates new version)
prompt.save(
    content="New prompt content: {input}",
    commit_message="Updated for better performance"
)

# Access current content
print(prompt.content)

# Delete prompt
prompt.delete()
```

### Version Management

```python
# Create a new version
new_version = prompt.create_version(
    content="Improved prompt content: {input}",
    commit_message="Performance improvements"
)

# Get all versions
versions = prompt.get_versions()
for version in versions:
    print(f"Version {version.version_number}: {version.commit_message}")

# Get specific version
version = prompt.get_version(2)
print(version.content)

# Restore to previous version
prompt.restore_version(1)
```

### PromptVersion Class

```python
# Access version properties
version = prompt.current_version
print(f"Version: {version.version_number}")
print(f"Content: {version.content}")
print(f"Message: {version.commit_message}")
print(f"Created: {version.created_at}")
print(f"Is Current: {version.is_current}")
```

## Advanced Usage

### Custom Client Configuration

```python
from prompta import Project, Prompt, PromptaClient
from prompta.config import Config

# Custom configuration
config = Config()
config.api_url = "https://my-prompta-server.com"
config.api_timeout = 60

# Custom client
client = PromptaClient("your-api-key", config)

# Use with interface objects
project = Project.create("My Project", client=client)
prompt = Prompt.get("my-prompt", client=client)
```

### Error Handling

```python
from prompta import Project, Prompt
from prompta.exceptions import NotFoundError, ValidationError, AuthenticationError

try:
    project = Project.get("non-existent-project")
except NotFoundError:
    print("Project not found")
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Batch Operations

```python
# Create multiple prompts
prompts_data = [
    {
        "name": "Prompt 1",
        "content": "Content 1: {input}",
        "location": "prompts/prompt1.txt"
    },
    {
        "name": "Prompt 2",
        "content": "Content 2: {input}",
        "location": "prompts/prompt2.txt"
    }
]

created_prompts = []
for data in prompts_data:
    prompt = Prompt.create(
        name=data["name"],
        content=data["content"],
        location=data["location"],
        project_id=project.id
    )
    created_prompts.append(prompt)

print(f"Created {len(created_prompts)} prompts")
```

## Integration Examples

### With FastAPI

```python
from fastapi import FastAPI
from prompta import Prompt

app = FastAPI()

@app.get("/prompts/{prompt_name}")
async def get_prompt_content(prompt_name: str):
    try:
        prompt = Prompt.get(prompt_name)
        return {
            "name": prompt.name,
            "content": prompt.content,
            "description": prompt.description,
            "tags": prompt.tags
        }
    except NotFoundError:
        return {"error": "Prompt not found"}, 404
```

### With Django

```python
# In your Django views.py
from django.http import JsonResponse
from prompta import Project, Prompt

def get_project_prompts(request, project_name):
    try:
        project = Project.get(project_name)
        prompts = project.get_prompts()

        return JsonResponse({
            "project": project.name,
            "prompts": [
                {
                    "name": p.name,
                    "content": p.content,
                    "location": p.location
                }
                for p in prompts
            ]
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
```

### With Flask

```python
from flask import Flask, jsonify
from prompta import Prompt

app = Flask(__name__)

@app.route('/search/<query>')
def search_prompts(query):
    try:
        results = Prompt.search(query)
        return jsonify([
            {
                "name": p.name,
                "description": p.description,
                "content": p.content[:100] + "..."
            }
            for p in results
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 400
```

## Best Practices

1. **Error Handling**: Always wrap API calls in try-catch blocks
2. **Configuration**: Use environment variables for API keys in production
3. **Caching**: Store frequently used prompts locally to reduce API calls
4. **Version Control**: Use meaningful commit messages when creating versions
5. **Testing**: Create test projects/prompts for development

## Troubleshooting

### Common Issues

1. **"API key not found"**:

   - Set `PROMPTA_API_KEY` environment variable
   - Check your `.env` file or `~/.prompta` configuration

2. **"Connection refused"**:

   - Ensure your Prompta API server is running
   - Check `PROMPTA_API_URL` configuration

3. **"Authentication failed"**:

   - Verify your API key is correct and active
   - Check API key permissions

4. **"Multiple prompts found"**:
   - Use `project_id` parameter when getting prompts by name
   - Or use the full prompt ID instead

### Debug Mode

```python
from prompta.config import Config

config = Config()
config.verbose = True  # Enable verbose logging

# Or set environment variable
import os
os.environ["PROMPTA_VERBOSE"] = "true"
```

## Contributing

The interface objects are part of the Prompta CLI package. To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

For issues or questions, please visit the [Prompta repository](https://github.com/ekkyarmandi/prompta).
