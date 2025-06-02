# Prompta CLI

Prompta is a powerful command-line tool for creating and managing self-hosted prompt management systems. Organize, version, and sync prompt files across multiple projects with a simple command-line interface.

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

### Using uv (Development)

```bash
git clone https://github.com/ekkyarmandi/prompta.git
cd prompta/prompta-cli
uv pip install -e .
```

## Quick Start

### 1. Configuration

Configure the CLI using environment variables or a `.env` file in your project:

```bash
# Required: API key for authentication
PROMPTA_API_KEY=your-api-key-here

# Optional: API server URL (defaults to localhost:8000)
PROMPTA_API_URL=http://localhost:8000
```

All prompt commands require a valid API key through one of these methods:

1. `PROMPTA_API_KEY` environment variable
2. `PROMPTA_API_KEY` in project's `.env` file
3. `--api-key` flag with individual commands

### 2. Basic Usage

```bash
# Check version
prompta --version

# List all available projects
prompta projects

# List prompts with search and filtering
prompta list --query "authentication" --tags "security,auth"

# Download a project by name or ID
prompta get my-project-name
prompta get --project "My Project"

# Download individual prompts
prompta get prompt-name
prompta get {prompt-id}

# View prompt content in terminal
prompta show my-prompt

# Get detailed information about prompts/projects
prompta info
```

## Usage Examples

### Project Management

```bash
# Search projects by query
prompta projects --query "authentication"

# Filter projects by tags
prompta projects --tags "api,security"

# Download entire project
prompta get --project "My API Project" --output ./my-project/

# Download project by ID
prompta get a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Prompt Management

```bash
# List all prompts
prompta list

# Search prompts by name or description
prompta list --query "system prompt"

# Filter prompts by location
prompta list --location "rules/"

# Show prompt content with syntax highlighting
prompta show my-system-prompt

# Show specific version of a prompt
prompta show my-prompt --version 2

# Download prompt to specific location
prompta get my-prompt --output ./prompts/system.md
```

### Advanced Usage

```bash
# Pagination for large result sets
prompta list --page 2 --page-size 50
prompta projects --page 1 --page-size 10

# Multiple tags filtering
prompta list --tags "system,rules,security"

# Using custom API key for specific commands
prompta list --api-key your-specific-api-key
```

## Configuration

Configure the CLI using environment variables or a `.env` file in your project:

```bash
# Required: API key for authentication
PROMPTA_API_KEY=your-api-key-here

# Optional: API server URL (defaults to localhost:8000)
PROMPTA_API_URL=http://localhost:8000
```

## Available Commands

- **`prompta projects`** - List and search projects with filtering options
- **`prompta get`** - Download prompts or entire projects
- **`prompta list`** - List prompts with search and filtering capabilities
- **`prompta show`** - Display prompt content in the terminal with syntax highlighting
- **`prompta info`** - Get detailed information about the system

## Flexibility

The prompta commands are convenience wrappers that make common tasks easier. You can always use the underlying tools directly:

- Use **`alembic`** commands directly for advanced migration management
- Use **`uvicorn app.main:app`** directly for custom server configurations
- All standard FastAPI, SQLAlchemy, and Alembic workflows are fully supported

## Help and Documentation

```bash
# Get general help
prompta --help

# Get help for specific commands
prompta projects --help
prompta list --help
prompta get --help
prompta show --help
```

## Repository

**GitHub**: [https://github.com/ekkyarmandi/prompta](https://github.com/ekkyarmandi/prompta)

## Contributing

We welcome contributions to the Prompta CLI! Here's how you can help:

### Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/your-username/prompta.git
   cd prompta/prompta-cli
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

4. **Code formatting and linting**
   ```bash
   black prompta/
   isort prompta/
   flake8 prompta/
   mypy prompta/
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
