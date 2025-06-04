# Prompta

Prompta is a self-hosted prompt management system that allows users to create, manage, and version control their prompts. The CLI tool enables users to retrieve their prompts from the Prompta API and provides powerful Python interfaces for external integration.

## Installation

### From PyPI (Recommended)

```bash
pip install prompta
```

### From Source

```bash
git clone https://github.com/ekkyarmandi/prompta.git
cd prompta/prompta-cli
pip install -e .
```

## Quick Start

### 1. Configuration

Configure the CLI using environment variables or a `.env` file in your project:

```bash
PROMPTA_API_KEY=your-api-key-here
PROMPTA_API_URL=http://localhost:8000
```

Some commands require a valid API key through one of these methods:

1. `PROMPTA_API_KEY` environment variable
2. `PROMPTA_API_KEY` in project's `.env` file
3. `PROMPTA_API_KEY` in global variable `~/.prompta` file
4. `--api-key` flag with individual commands

### 2. CLI Basic Usage

```bash
# Check version
prompta --version

# List all available projects
prompta projects

# List prompts with search and filtering
prompta list --query "authentication"

# Download a project by name or ID
prompta get my-project-name
prompta get --project "My Project"

# Download individual prompts
prompta get prompt-name
prompta get {prompt-id}

# View prompt content in terminal
prompta show my-prompt

# Get detailed information about API server status and API_KEY validity
prompta info
```

## Available Commands

- **`prompta projects`** - List and search projects with filtering options
- **`prompta get`** - Download prompts or entire projects
- **`prompta list`** - List prompts with search and filtering capabilities
- **`prompta show`** - Display prompt content in the terminal with syntax highlighting
- **`prompta info`** - Get detailed information about the system

## Python Library Interface

Prompta provides comprehensive Python interfaces for external use, offering three main approaches:

### 1. Interface Objects (Basic CRUD)

Clean, simple objects for basic operations without handling API complexity:

```python
from prompta import Project, Prompt, PromptVersion

# Create a new project
project = Project.create(
    name="My AI Project",
    description="Collection of AI prompts",
    tags=["ai", "automation"],
    is_public=False
)

# Create a prompt in the project
prompt = Prompt.create(
    name="Summary Generator",
    content="Please summarize the following text: {text}",
    location="prompts/summary.txt",
    project_id=project.id,
    description="Generates concise summaries",
    tags=["summary", "text-processing"]
)

# Update prompt with new version
prompt.create_version(
    content="Please provide a detailed summary of: {text}",
    commit_message="Made summary more detailed"
)

# List and search
projects = Project.list(tags=["ai"])
results = Prompt.search("summary")

# Get specific items
my_project = Project.get("My AI Project")
my_prompt = Prompt.get("Summary Generator")
```

### 2. Auto-Tracking with Context Detection

Advanced tracking that automatically detects context and manages versions:

```python
from prompta import TrackedPrompt, tracked_prompt

def generate_email():
    # Auto-detects context: file, function, line number
    prompt = TrackedPrompt(
        name="email_generator",
        content="Generate a professional email about {topic}"
    )
    # Creates: your_file_generate_email_email_generator

    return use_prompt(prompt.content)

def different_function():
    # Same name, different context = different tracking
    prompt = TrackedPrompt(
        name="email_generator",
        content="Generate a casual email about {topic}"
    )
    # Creates: your_file_different_function_email_generator

    return use_prompt(prompt.content)

# Convenience function
def quick_tracking():
    prompt = tracked_prompt(
        name="assistant",
        content="You are a helpful assistant"
    )
    return prompt.content
```

### 3. File-Based Management

Seamless integration between file system and API with automatic synchronization:

```python
from prompta import TrackedPrompt

def file_based_workflow():
    # Read from file, sync to API
    prompt = TrackedPrompt(
        name="assistant_instruction",
        location="prompts/assistant.txt"
    )
    # Reads content from file, creates API version

    # Update content and sync to file
    prompt.update_content("You are a specialized assistant")
    # Automatically writes to prompts/assistant.txt

    # Reload from file
    prompt.reload_from_file()
    # Reads latest content from file, creates new version if changed

def hybrid_approach():
    # Provide content and file location
    prompt = TrackedPrompt(
        name="assistant_instruction",
        content="You are a helpful assistant",
        location="prompts/assistant.txt"
    )
    # Uses provided content, writes to file, syncs to API
```

### 4. Version-Specific Loading

Load and work with specific versions for A/B testing, rollbacks, and comparison:

```python
from prompta import TrackedPrompt

# Load specific versions
v1_prompt = TrackedPrompt(name="assistant", version="v1")
v2_prompt = TrackedPrompt(name="assistant", version=2)
latest_prompt = TrackedPrompt(name="assistant", version="latest")

# A/B Testing
def run_ab_test():
    prompt_a = TrackedPrompt(name="email_gen", version="v1")
    prompt_b = TrackedPrompt(name="email_gen", version="v2")

    result_a = test_agent(prompt_a.content)
    result_b = test_agent(prompt_b.content)

    return compare_results(result_a, result_b)

# Rollback to previous version
def emergency_rollback():
    stable_version = TrackedPrompt(name="production_assistant", version="v3")

    # Deploy stable version as new current
    TrackedPrompt(
        name="production_assistant",
        content=stable_version.content
    )

# Environment-specific versions
def get_prompt_for_env(environment):
    version_map = {
        "production": "stable",
        "staging": "latest",
        "development": "dev"
    }

    return TrackedPrompt(
        name="assistant",
        version=version_map.get(environment, "latest")
    )

# Version comparison
def compare_versions():
    versions = [1, 2, 3, "latest"]

    for version in versions:
        prompt = TrackedPrompt(name="summarizer", version=version)
        print(f"Version {version}: {len(prompt.content)} chars")
```

## Key Features

### Interface Objects

- **Clean Interface**: No need to handle HTTP requests or API keys directly
- **Automatic Configuration**: Uses existing config system
- **Type Hints**: Full type annotation for better IDE support
- **Error Handling**: Uses existing exception classes
- **Version Management**: Built-in support for prompt versioning
- **Search & Filter**: Easy methods for finding projects and prompts

### Auto-Tracking

- **Context Detection**: Automatically detects calling file, function, and line
- **Explicit Naming**: Require explicit prompt names for clear identification
- **Cross-Invocation Tracking**: Maintains prompt state across different program runs
- **Version Management**: Automatic versioning when content changes
- **Duplicate Prevention**: Avoids creating duplicate versions

### File-Based Management

- **Seamless Sync**: Automatic synchronization between files and API
- **File Operations**: Read from and write to files with UTF-8 encoding
- **Directory Creation**: Automatically creates parent directories
- **Content Resolution**: Smart content resolution from multiple sources

### Version-Specific Loading

- **Multiple Formats**: Support for `1`, `"v1"`, `"latest"`, `"current"`
- **Read-Only Access**: Version-specific prompts prevent accidental modifications
- **A/B Testing**: Easy comparison of different prompt versions
- **Rollback Capability**: Restore previous stable versions
- **Environment Management**: Use appropriate versions per environment

## Advanced Usage Examples

### Cross-Feature Integration

```python
from prompta import TrackedPrompt

# File + Version Loading
def load_with_fallback():
    try:
        # Try to load specific version
        prompt = TrackedPrompt(name="assistant", version="v1")
    except NotFoundError:
        # Fallback to file if version doesn't exist
        prompt = TrackedPrompt(name="assistant", location="backup.txt")

    return prompt.content

# Tracking + File Management
def development_workflow():
    # During development: work with files
    prompt = TrackedPrompt(
        name="dev_assistant",
        location="dev_prompts/assistant.txt",
        content="You are a development assistant"
    )

    # File automatically updated, versions tracked
    prompt.update_content("You are an improved development assistant")

    # Later: load specific version for testing
    test_prompt = TrackedPrompt(name="dev_assistant", version=1)
    return test_prompt.content

# Complete Lifecycle Management
def production_workflow():
    # Development
    dev_prompt = TrackedPrompt(
        name="production_assistant",
        content="Development version",
        location="prompts/assistant.txt"
    )

    # Testing - load specific version
    test_version = TrackedPrompt(name="production_assistant", version=1)

    # Production - use latest stable
    prod_prompt = TrackedPrompt(name="production_assistant", version="stable")

    return prod_prompt.content
```

### Tracking Registry

Monitor and manage tracked prompts:

```python
from prompta import TrackedPrompt

# View all tracked prompts
TrackedPrompt.show_tracking_info()

# Get specific tracked prompt
tracked = TrackedPrompt.get_tracked_prompt("my_tracking_key")

# Clear registry (useful for testing)
TrackedPrompt.clear_registry()
```

## Repository

**GitHub**: [https://github.com/ekkyarmandi/prompta](https://github.com/ekkyarmandi/prompta)

## Contributing

We welcome contributions to the Prompta! Here's how you can help:

### Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/your-username/prompta.git
   cd prompta
   ```

2. **Set up development environment**

   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install in development mode
   uv pip install -e ".[dev]"
   ```

3. **Run tests**

   ```bash
   pytest
   pytest --cov=prompta --cov-report=html  # With coverage
   ```

### Contributing Guidelines

- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/ekkyarmandi/prompta/issues)
- **Pull Requests**: Submit PRs against the `main` branch
- **Code Style**: Follow Black formatting and include type hints
- **Testing**: Add tests for new features and ensure existing tests pass
- **Documentation**: Update documentation for new features

### Commit Messages

Follow conventional commit format:

- `feat: add new command for bulk operations`
- `fix: resolve authentication error handling`
- `docs: update installation instructions`
- `test: add unit tests for prompt commands`

## Requirements

- **Python**: 3.8+
- **Dependencies**: click, httpx, rich, python-dotenv, tqdm, pydantic

## License

Prompta is distributed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

For full documentation and server setup instructions, see the project's main README in the repository root or visit the [project website](https://github.com/ekkyarmandi/prompta).
