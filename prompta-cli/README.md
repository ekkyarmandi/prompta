# Prompta CLI

Prompta is a self-hosted prompt management system that allows users to create, manage, and version control their prompts. The CLI tool enables users to retrieve their prompts from the Prompta API.

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
PROMPTA_API_KEY=your-api-key-here
PROMPTA_API_URL=http://localhost:8000
```

Some commands require a valid API key through one of these methods:

1. `PROMPTA_API_KEY` environment variable
2. `PROMPTA_API_KEY` in project's `.env` file
3. `PROMPTA_API_KEY` in global variable `~/.prompta` file
4. `--api-key` flag with individual commands

### 2. Basic Usage

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

## Repository

**GitHub**: [https://github.com/ekkyarmandi/prompta](https://github.com/ekkyarmandi/prompta)

## Contributing

We welcome contributions to the Prompta CLI! Here's how you can help:

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
