# Prompta CLI

Prompta is a powerful command-line tool for creating and managing self-hosted prompt management systems.

## Configuration

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

## Project Management

Create and manage Prompta API server projects:

- **`prompta init`** - Create a new Prompta API server project

## Prompt Management

- Create, edit and organise prompt files locally
- Push and pull prompts to a Prompta server
- Inspect and test prompts from the terminal

## Flexibility

The prompta commands are convenience wrappers that make common tasks easier. You can always use the underlying tools directly:

- Use **`alembic`** commands directly for advanced migration management
- Use **`uvicorn app.main:app`** directly for custom server configurations
- All standard FastAPI, SQLAlchemy, and Alembic workflows are fully supported

```shell
$ prompta --help
```

For full documentation see the project's main README in the repository root or visit the project website.

Prompta is written in Python 3.8+ and distributed under the MIT licence.
