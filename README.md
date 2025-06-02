# Prompta: Self-Hosted Prompt Management System

Prompta is a comprehensive, self-hosted system for managing, versioning, and utilizing AI prompts. It consists of a powerful FastAPI-based API server (`prompta-app`) and a user-friendly command-line interface (`prompta-cli`).

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Components](#components)
  - [Prompta App (API Server)](#prompta-app-api-server)
  - [Prompta CLI (Command-Line Interface)](#prompta-cli-command-line-interface)
- [Getting Started](#getting-started)
  - [Running Prompta App (API Server)](#running-prompta-app-api-server)
  - [Installing Prompta CLI](#installing-prompta-cli)
- [Quick Usage](#quick-usage)
  - [Prompta API](#prompta-api)
  - [Prompta CLI](#prompta-cli)
- [Configuration](#configuration)
  - [Prompta App](#prompta-app)
  - [Prompta CLI](#prompta-cli-1)
- [Repository Structure](#repository-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

Prompta empowers individuals and teams to take control of their AI prompt engineering workflow. It provides a centralized server to store and manage prompts with version control, and a CLI tool to easily interact with these prompts from your local development environment.

## Features

**Prompta System:**

- **Self-Hosted:** Full control over your data and infrastructure.
- **Centralized Prompt Management:** Store, organize, and manage all your prompts in one place.
- **Version Control:** Track changes to prompts, view history, and restore previous versions.
- **Secure Access:** Authentication using JWT for users and API keys for applications/CLI.

**Prompta App (API Server):**

- Built with FastAPI for high performance.
- Supports SQLite (for development) and PostgreSQL (for production).
- Dockerized for easy deployment.
- Comprehensive API for user, API key, prompt, and version management.
- Auto-generated OpenAPI/Swagger documentation.

**Prompta CLI:**

- Intuitive command-line interface for interacting with the Prompta API.
- Retrieve and display prompts.
- List projects and prompts with search and filtering.
- Easy installation via PyPI.

## Components

### Prompta App (API Server)

The `prompta-app` is the backend API server that handles:

- User authentication (registration, login with JWT).
- API key management.
- CRUD operations for prompts and their versions.
- Search and filtering capabilities.

For detailed information, see the [`prompta-app/README.md`](prompta-app/README.md).

### Prompta CLI (Command-Line Interface)

The `prompta-cli` is a command-line tool that allows users to:

- Interact with the Prompta API from the terminal.
- List available projects and prompts.
- Fetch and display prompt content.
- Configure API endpoint and authentication.

Prompta CLI is designed to be a lightweight and efficient way to integrate your managed prompts into your local workflows.

For detailed information, see the [`prompta-cli/README.md`](prompta-cli/README.md).

## Getting Started

### Running Prompta App (API Server)

**Using Docker (Recommended for Production):**

1. Ensure Docker and Docker Compose are installed.
2. In the `prompta-app` directory (or project root if `docker-compose.yml` is there):
   ```bash
   docker compose up --build
   ```
   The API will typically be available at `http://localhost:8000`.

**Local Development (without Docker):**

1. Navigate to the `prompta-app` directory.
2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```
   (Ensure `requirements.txt` is in `prompta-app`)
3. Create a `.env` file (see [Prompta App Configuration](#prompta-app)).
4. Run Alembic migrations if necessary.
5. Start the development server:
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Installing Prompta CLI

**From PyPI (Recommended):**

```bash
pip install prompta
```

**From Source (for development):**

```bash
git clone https://github.com/ekkyarmandi/prompta.git
cd prompta/prompta-cli
# For editable install
uv pip install -e .
# Or, for regular install using local files
pip install .
```

## Quick Usage

### Prompta API

Once the `prompta-app` is running, you can interact with it via HTTP requests. Key initial steps:

1.  **Register a user:** `POST /auth/register`
2.  **Login:** `POST /auth/login` to get a JWT token.
3.  **Create an API Key:** `POST /auth/api-keys` (using JWT token) for CLI or other services.

Refer to `prompta-app/README.md` for detailed API endpoints and `curl` examples.

### Prompta CLI

1.  **Configure API Key and URL:** (See [Prompta CLI Configuration](#prompta-cli-1))
    Typically, create a `.env` file in your project or set environment variables:

    ```bash
    PROMPTA_API_KEY=your-api-key-here
    PROMPTA_API_URL=http://localhost:8000
    ```

2.  **Basic Commands:**

    ```bash
    # Check version
    prompta --version

    # Check API server status and API key validity
    prompta info

    # List all available projects
    prompta projects

    # List prompts (e.g., search by query)
    prompta list --query "authentication"

    # Download a project by name or ID
    prompta get my-project-name
    # or
    prompta get --project "My Project Name"

    # View prompt content
    prompta show my-prompt-name
    ```

## Configuration

### Prompta App

Configuration for `prompta-app` is managed via a `.env` file in the `prompta-app` directory. Key variables:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./sqlite.db # For local dev; use postgresql for prod
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_EXPIRE_DAYS=365
ALLOWED_ORIGINS=* # Adjust for production
# Add other necessary variables like RATE_LIMIT_REQUESTS, etc.
```

See `prompta-app/README.md` or `prompta-app/env.example` for more details.

### Prompta CLI

Prompta CLI can be configured via:

1.  **Environment Variables:**
    - `PROMPTA_API_KEY`: Your API key.
    - `PROMPTA_API_URL`: The URL of your Prompta API server (defaults to `http://localhost:8000`).
2.  **`.env` file:** In the current project directory.
    ```
    PROMPTA_API_KEY=your-api-key-here
    PROMPTA_API_URL=http://your.prompta.server
    ```
3.  **Global `~/.prompta` file:** (Less common, ensure CLI supports this if documented)
    ```
    PROMPTA_API_KEY=your-global-api-key
    ```
4.  **Command-line flags:** e.g., `--api-key` with individual commands.

## Repository Structure

```
Prompta/
├── prompta-app/            # FastAPI Server application
│   ├── app/                # Core application logic
│   ├── auth/               # Authentication logic
│   ├── models/             # Database models
│   ├── migrations/         # Alembic database migrations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── README.md           # Detailed app documentation
├── prompta-cli/            # Command Line Interface
│   ├── prompta/            # CLI source code
│   ├── pyproject.toml      # Packaging and dependencies
│   ├── README.md           # Detailed CLI documentation
│   └── ...
├── .gitignore
├── LICENSE
└── README.md               # This file (Project overview)
```

## Contributing

Contributions are welcome! Please follow these general guidelines:

1.  **Fork the repository.**
2.  **Create a new branch** for your feature or bug fix.
3.  **Develop your changes:**
    - For `prompta-app` specific changes, refer to `prompta-app/README.md`.
    - For `prompta-cli` specific changes, refer to `prompta-cli/README.md`.
4.  **Ensure tests pass** for the component you are working on.
5.  **Update documentation** if necessary.
6.  **Follow conventional commit messages.** (e.g., `feat: add new feature`, `fix: resolve bug`)
7.  **Submit a Pull Request** to the `main` branch.

Please check the README files within `prompta-app` and `prompta-cli` for more specific development and contribution instructions, including setting up development environments and running tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
