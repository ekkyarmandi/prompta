# Prompta CLI

Prompta is a powerful command-line tool for creating and managing self-hosted prompt management systems.

## Project Management

Create and manage Prompta API server projects:

- **`prompta createproject <name>`** - Create a new Prompta API server project
- **`prompta migrate`** - Run database migrations (convenience wrapper around Alembic)
- **`prompta runserver`** - Start development server (convenience wrapper around Uvicorn)
- **`prompta createsuperuser`** - Create admin users interactively

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
