# Prompta API Server (`prompta-app`)

A FastAPI-based authentication and prompt management API with JWT and API key support, serving as the backend for the Prompta ecosystem.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Running the API Server](#running-the-api-server)
  - [Using Docker (Recommended)](#using-docker-recommended)
  - [Local Development](#local-development)
- [Environment Configuration](#environment-configuration)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [Authentication](#authentication)
  - [API Key Management](#api-key-management)
  - [Prompt Management](#prompt-management)
  - [Version Management](#version-management)
- [Authentication Methods](#authentication-methods)
  - [JWT Token Authentication](#jwt-token-authentication)
  - [API Key Authentication](#api-key-authentication)
- [Usage Examples (cURL)](#usage-examples-curl)
  - [1. Register a User](#1-register-a-user)
  - [2. Login](#2-login)
  - [3. Create API Key](#3-create-api-key)
  - [4. Create a Prompt](#4-create-a-prompt)
  - [5. Search Prompts](#5-search-prompts)
  - [6. Create New Version](#6-create-new-version)
  - [7. Compare Versions](#7-compare-versions)
- [Testing](#testing)
- [Database Schema](#database-schema)
  - [Users Table](#users-table)
  - [API Keys Table](#api-keys-table)
  - [Prompts Table](#prompts-table)
  - [Prompt Versions Table](#prompt-versions-table)
- [Security Features](#security-features)
- [Development](#development)
  - [Project Structure](#project-structure)
- [Production Deployment](#production-deployment)

## Features

- **User Authentication**: Registration, login with JWT tokens.
- **API Key Management**: Create, list, update, and delete API keys.
- **Prompt Management**: Full CRUD operations for prompts with version control.
- **Version Control**: Track changes, compare versions, restore previous versions.
- **Search & Filtering**: Search by content, tags, location with pagination.
- **Dual Authentication**: Support for both JWT tokens and API keys.
- **Database Support**: SQLite for local development, production-ready for PostgreSQL.
- **Security**: Password hashing with bcrypt, secure API key generation.
- **Auto-generated Documentation**: OpenAPI/Swagger docs available at `/docs` (when `DEBUG=True`).

## Prerequisites

- Python 3.10+
- `uv` (for package management, optional but recommended)
- Docker and Docker Compose (for Docker-based deployment)

## Running the API Server

### Using Docker (Recommended)

If you have Docker and Docker Compose installed, you can spin up a fully-featured stack (FastAPI application + PostgreSQL database) with a single command from the `prompta-app` directory (or the root directory if `docker-compose.yml` is located there and paths are adjusted):

```bash
# Ensure docker-compose.yml is configured for prompta-app
docker compose up --build
```

The first time this runs, Docker will:

1. Build an image for the FastAPI application using `prompta-app/Dockerfile`.
2. Start a PostgreSQL container (if configured in `docker-compose.yml`).
3. Apply Alembic migrations automatically on container start-up.

After the stack is ready, the API is typically available at `http://localhost:8000`.

### Local Development

1.  Navigate to the `prompta-app` directory.
2.  Install dependencies:
    ```bash
    uv pip install -r requirements.txt
    ```
3.  Set up your `.env` file (see [Environment Configuration](#environment-configuration)).
4.  Initialize the database and run migrations (if not using Docker which handles this):
    ```bash
    # Example commands, adjust as per your Alembic setup
    # alembic upgrade head
    ```
5.  Start the development server:
    `bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
`
    The API will be available at `http://localhost:8000`.

## Environment Configuration

Create a `.env` file in the `prompta-app` directory. Refer to `env.example` for a full list of options.
Key variables:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production-at-least-32-characters-long
DATABASE_URL=sqlite:///./sqlite.db  # For SQLite
# DATABASE_URL=postgresql://user:password@host:port/dbname # For PostgreSQL
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_EXPIRE_DAYS=365
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"] # Example for a frontend
# For allowing all origins (less secure, for development):
# ALLOWED_ORIGINS=["*"]
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60 # in seconds
```

**Important:**

- Change `SECRET_KEY` to a strong, unique value for production.
- Configure `DATABASE_URL` for your chosen database (SQLite for local, PostgreSQL for production is recommended).
- Set `DEBUG=False` in production.
- Adjust `ALLOWED_ORIGINS` for your frontend applications in production.

## API Endpoints

Base URL: `http://localhost:8000` (or your configured host/port)

### Health Check

- `GET /health` - Health check endpoint.

### Authentication

- `POST /auth/register` - Register a new user.
- `POST /auth/login` - Login and get JWT token.
- `GET /auth/me` - Get current user info (requires JWT or API key).
- `PUT /auth/me` - Update current user (requires JWT).

### API Key Management

(Most require JWT authentication for the user managing their keys)

- `POST /auth/api-keys` - Create new API key.
- `GET /auth/api-keys` - List user's API keys.
- `GET /auth/api-keys/{key_id}` - Get specific API key.
- `PUT /auth/api-keys/{key_id}` - Update API key (e.g., name, active status).
- `DELETE /auth/api-keys/{key_id}` - Delete API key.

### Prompt Management

(Requires JWT or API key authentication)

- `POST /prompts/` - Create new prompt with initial version.
- `GET /prompts/` - List prompts with search, filtering, and pagination.
- `GET /prompts/search` - (If implemented separately) Search prompts by content.
- `GET /prompts/by-location` - Get prompt by file location.
- `GET /prompts/{prompt_id}` - Get specific prompt details.
- `PUT /prompts/{prompt_id}` - Update prompt metadata (name, description, tags, location).
- `DELETE /prompts/{prompt_id}` - Delete prompt and all its versions.

### Version Management

(Requires JWT or API key authentication)

- `POST /prompts/{prompt_id}/versions` - Create a new version for a prompt.
- `GET /prompts/{prompt_id}/versions` - List all versions of a prompt.
- `GET /prompts/{prompt_id}/versions/{version_number}` - Get specific version of a prompt.
- `PUT /prompts/{prompt_id}/versions/{version_number}` - Update version metadata (e.g., commit message).
- `POST /prompts/{prompt_id}/restore/{version_number}` - Set a specific version as the current one.
- `GET /prompts/{prompt_id}/diff/{v1_number}/{v2_number}` - Compare two versions of a prompt.

## Authentication Methods

### JWT Token Authentication

Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

Used primarily for user-facing operations (e.g., web dashboard).

### API Key Authentication

Include the API key in the `X-API-Key` header:

```
X-API-Key: <your-api-key>
```

Used primarily for programmatic access (e.g., CLI, other services).

## Usage Examples (cURL)

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword123"
  }'
# This will return an access_token (JWT)
```

### 3. Create API Key

(Requires JWT token from login)

```bash
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-cli-key"
  }'
# This will return the API key string. Save it securely.
```

### 4. Create a Prompt

(Requires API key or JWT token)

```bash
curl -X POST "http://localhost:8000/prompts/" \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Sample Prompt",
    "description": "A prompt for testing purposes.",
    "location": "samples/my_prompt.md",
    "tags": ["sample", "test"],
    "content": "This is the initial content of the prompt.",
    "commit_message": "Initial version"
  }'
```

### 5. Search Prompts

(Requires API key or JWT token)

```bash
# Search by query in name/description
curl -X GET "http://localhost:8000/prompts/?query=sample" \
  -H "X-API-Key: <your-api-key>"

# Search by tags (can often be repeated for AND, or comma-separated for OR, check API spec)
curl -X GET "http://localhost:8000/prompts/?tags=sample&tags=test" \
  -H "X-API-Key: <your-api-key>"
```

### 6. Create New Version

(Requires API key or JWT token and `prompt_id`)

```bash
PROMPT_ID="your-prompt-id-here"
curl -X POST "http://localhost:8000/prompts/${PROMPT_ID}/versions" \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content for version 2.",
    "commit_message": "Second version with updates"
  }'
```

### 7. Compare Versions

(Requires API key or JWT token, `prompt_id`, and version numbers)

```bash
PROMPT_ID="your-prompt-id-here"
curl -X GET "http://localhost:8000/prompts/${PROMPT_ID}/diff/1/2" \
  -H "X-API-Key: <your-api-key>"
```

## Testing

Run tests using your preferred test runner (e.g., `pytest`). Ensure your test environment is configured (e.g., a separate test database).

```bash
# Example assuming pytest and tests are in a 'tests' directory within prompta-app
# Ensure your PYTHONPATH is set up if needed
# May require specific env vars for testing (e.g., TEST_DATABASE_URL)
uv run pytest
```

Refer to specific test files (e.g., `test_auth.py`, `test_prompts.py`) for details on what is covered.

## Database Schema

(Simplified overview, refer to `models.py` for exact definitions and relationships)

### Users Table

- `id` (String/UUID): Primary Key.
- `username` (String): Unique.
- `email` (String): Unique.
- `password_hash` (String).
- `created_at`, `updated_at` (DateTime).
- `is_active` (Boolean).

### API Keys Table

- `id` (String/UUID): Primary Key.
- `user_id` (String/UUID): Foreign Key to Users.
- `key_hash` (String): Hashed API key for storage.
- `name` (String): Human-readable name.
- `created_at`, `last_used_at`, `expires_at` (DateTime).
- `is_active` (Boolean).

### Prompts Table

- `id` (String/UUID): Primary Key.
- `user_id` (String/UUID): Foreign Key to Users.
- `name` (String): Unique per user.
- `description` (Text).
- `location` (String).
- `tags` (JSON/Array).
- `created_at`, `updated_at` (DateTime).
- `current_version_id` (String/UUID): Foreign Key to PromptVersions.

### Prompt Versions Table

- `id` (String/UUID): Primary Key.
- `prompt_id` (String/UUID): Foreign Key to Prompts.
- `version_number` (Integer): Sequential, unique per prompt.
- `content` (Text).
- `commit_message` (Text).
- `created_at` (DateTime).
- `is_current` (Boolean).

## Security Features

- **Password Hashing**: Bcrypt used for storing user passwords.
- **JWT Tokens**: HS256 algorithm for secure session management.
- **API Key Hashing**: API keys are hashed (e.g., SHA-256) before storing.
- **Secure Key Generation**: Cryptographically secure methods for generating API keys.
- **Input Validation**: Pydantic schemas for request and response validation.
- **SQL Injection Prevention**: Use of ORM (SQLAlchemy) with parameterized queries.
- **CORS Configuration**: Control which origins can access the API.
- **Rate Limiting**: To prevent abuse.

## Development

### Project Structure (inside `prompta-app`)

```
prompta-app/
├── app/                  # Core application module
│   ├── __init__.py
│   ├── main.py           # FastAPI application instance and main router
│   ├── config.py         # Configuration loading (e.g., from .env)
│   └── database.py       # Database session and engine setup
├── auth/                 # Authentication related module
│   ├── __init__.py
│   ├── models.py         # User and APIKey SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas for auth
│   ├── routes.py         # API routes for /auth
│   ├── security.py       # Password hashing, JWT handling, API key functions
│   └── dependencies.py   # FastAPI dependencies for auth (e.g., get_current_user)
├── prompts/              # Prompts and versions module
│   ├── __init__.py
│   ├── models.py         # Prompt and PromptVersion SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas for prompts
│   ├── routes.py         # API routes for /prompts
│   └── services.py       # Business logic for prompts (optional, can be in routes)
├── migrations/           # Alembic database migrations
│   └── versions/
│   └── env.py
│   └── script.py.mako
├── tests/                # Test suite
├── .env.example          # Example environment file
├── alembic.ini           # Alembic configuration
├── Dockerfile
├── docker-compose.yml    # (If app-specific or linked from root)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Production Deployment

For production:

1.  Set `DEBUG=False` in your environment or `.env` file.
2.  Use a strong, unique `SECRET_KEY`.
3.  Configure a robust production database (e.g., PostgreSQL) via `DATABASE_URL`.
4.  Set up `ALLOWED_ORIGINS` carefully to only include your frontend domains.
5.  Implement proper HTTPS/TLS (e.g., via a reverse proxy like Nginx or Traefik).
6.  Consider a production-grade ASGI server like Gunicorn with Uvicorn workers.
    Example with Gunicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`
7.  Set up robust monitoring, logging, and alerting.
8.  Ensure database backups are in place.
