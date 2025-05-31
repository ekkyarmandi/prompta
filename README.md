# Prompta API

A FastAPI-based authentication and prompt management API with JWT and API key support.

## Features

- **User Authentication**: Registration, login with JWT tokens
- **API Key Management**: Create, list, update, and delete API keys
- **Prompt Management**: Full CRUD operations for prompts with version control
- **Version Control**: Track changes, compare versions, restore previous versions
- **Search & Filtering**: Search by content, tags, location with pagination
- **Dual Authentication**: Support for both JWT tokens and API keys
- **SQLite Database**: Local development with SQLite, production-ready for PostgreSQL
- **Security**: Password hashing with bcrypt, secure API key generation
- **Auto-generated Documentation**: OpenAPI/Swagger docs (in debug mode)

## Quick Start

### Prerequisites

- Python 3.10+
- uv (for package management)

### Installation

1. Install dependencies:

```bash
uv pip install -r requirements.txt
```

2. Start the development server:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Environment Configuration

Create a `.env` file in the api directory:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production-at-least-32-characters-long
DATABASE_URL=sqlite:///./sqlite.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_EXPIRE_DAYS=365
ALLOWED_ORIGINS=*
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## API Endpoints

### Health Check

- `GET /health` - Health check endpoint

### Authentication

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info (JWT or API key)
- `PUT /auth/me` - Update current user (JWT only)

### API Key Management

- `POST /auth/api-keys` - Create new API key (JWT only)
- `GET /auth/api-keys` - List user's API keys (JWT or API key)
- `GET /auth/api-keys/{key_id}` - Get specific API key (JWT or API key)
- `PUT /auth/api-keys/{key_id}` - Update API key (JWT or API key)
- `DELETE /auth/api-keys/{key_id}` - Delete API key (JWT or API key)

### Prompt Management

- `POST /prompts/` - Create new prompt with initial version
- `GET /prompts/` - List prompts with search and pagination
- `GET /prompts/search` - Search prompts by content
- `GET /prompts/by-location` - Get prompt by file location
- `GET /prompts/{prompt_id}` - Get specific prompt
- `PUT /prompts/{prompt_id}` - Update prompt metadata
- `DELETE /prompts/{prompt_id}` - Delete prompt and all versions

### Version Management

- `POST /prompts/{prompt_id}/versions` - Create new version
- `GET /prompts/{prompt_id}/versions` - List all versions
- `GET /prompts/{prompt_id}/versions/{version_number}` - Get specific version
- `PUT /prompts/{prompt_id}/versions/{version_number}` - Update version commit message
- `POST /prompts/{prompt_id}/restore/{version_number}` - Restore to specific version
- `GET /prompts/{prompt_id}/diff/{v1}/{v2}` - Compare two versions

## Authentication Methods

### JWT Token Authentication

Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### API Key Authentication

Include the API key in the X-API-Key header:

```
X-API-Key: <your-api-key>
```

## Usage Examples

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
```

### 3. Create API Key

```bash
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-api-key"
  }'
```

### 4. Create a Prompt

```bash
curl -X POST "http://localhost:8000/prompts/" \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cursor-rules",
    "description": "Cursor IDE rules for better coding",
    "location": ".cursorrules",
    "tags": ["cursor", "ide", "rules"],
    "content": "Use TypeScript for all new files.\nPrefer functional components in React.",
    "commit_message": "Initial cursor rules"
  }'
```

### 5. Search Prompts

```bash
# Search by content
curl -X GET "http://localhost:8000/prompts/search?q=TypeScript" \
  -H "X-API-Key: <your-api-key>"

# Search by tags
curl -X GET "http://localhost:8000/prompts/?tags=cursor&tags=ide" \
  -H "X-API-Key: <your-api-key>"

# Combined search
curl -X GET "http://localhost:8000/prompts/?query=component&tags=react" \
  -H "X-API-Key: <your-api-key>"
```

### 6. Create New Version

```bash
curl -X POST "http://localhost:8000/prompts/{prompt_id}/versions" \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content with new rules...",
    "commit_message": "Added new coding standards"
  }'
```

### 7. Compare Versions

```bash
curl -X GET "http://localhost:8000/prompts/{prompt_id}/diff/1/2" \
  -H "X-API-Key: <your-api-key>"
```

## Testing

Run the comprehensive test suites:

```bash
# Test authentication
uv run python test_api.py

# Test prompt management
uv run python test_prompts.py

# Test additional prompts and search
uv run python test_more_prompts.py
```

This will test:

- User registration and login
- JWT and API key authentication
- Prompt CRUD operations
- Version management
- Search and filtering
- Version comparison and restoration

## Database Schema

### Users Table

- `id` (String): Unique user identifier
- `username` (String): Unique username
- `email` (String): Unique email address
- `password_hash` (String): Bcrypt hashed password
- `created_at` (DateTime): Account creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `is_active` (Boolean): Account status

### API Keys Table

- `id` (String): Unique API key identifier
- `user_id` (String): Foreign key to users table
- `key_hash` (String): SHA-256 hashed API key
- `name` (String): Human-readable key name
- `created_at` (DateTime): Key creation timestamp
- `last_used_at` (DateTime): Last usage timestamp
- `expires_at` (DateTime): Optional expiration date
- `is_active` (Boolean): Key status

### Prompts Table

- `id` (String): Unique prompt identifier
- `user_id` (String): Foreign key to users table
- `name` (String): Prompt name (unique per user)
- `description` (Text): Optional description
- `location` (String): File path/location
- `tags` (JSON): Array of tags
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp
- `current_version_id` (String): Foreign key to current version

### Prompt Versions Table

- `id` (String): Unique version identifier
- `prompt_id` (String): Foreign key to prompts table
- `version_number` (Integer): Sequential version number
- `content` (Text): Version content
- `commit_message` (Text): Optional commit message
- `created_at` (DateTime): Version creation timestamp
- `is_current` (Boolean): Whether this is the current version

## Security Features

- **Password Hashing**: Bcrypt with salt rounds
- **JWT Tokens**: HS256 algorithm with configurable expiration
- **API Key Hashing**: SHA-256 hashed storage
- **Secure Key Generation**: Cryptographically secure random tokens
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

## Development

### Project Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration management
│   └── database.py      # Database setup
├── auth/
│   ├── __init__.py
│   ├── models.py        # User and APIKey models
│   ├── schemas.py       # Pydantic schemas
│   ├── routes.py        # Authentication routes
│   ├── security.py      # Security utilities
│   └── dependencies.py  # FastAPI dependencies
├── prompts/
│   ├── __init__.py
│   ├── models.py        # Prompt and PromptVersion models
│   ├── schemas.py       # Pydantic schemas
│   ├── routes.py        # Prompt management routes
│   ├── services.py      # Business logic
│   └── utils.py         # Utility functions
├── migrations/          # Alembic migrations
├── requirements.txt     # Python dependencies
├── test_*.py           # Test suites
└── README.md           # This file
```

### Key Features Implemented

1. **Complete Authentication System**

   - User registration and login
   - JWT token generation and validation
   - API key creation and management
   - Flexible authentication (JWT or API key)

2. **Comprehensive Prompt Management**

   - CRUD operations for prompts
   - Version control with full history
   - Search by content, tags, and location
   - Pagination and filtering

3. **Version Control Features**

   - Automatic version numbering
   - Commit messages for changes
   - Version comparison with diff
   - Restore to previous versions

4. **Advanced Search Capabilities**

   - Full-text search in prompt content
   - Tag-based filtering
   - Location pattern matching
   - Combined search criteria

5. **Production-Ready Features**
   - Proper error handling
   - Input validation
   - Security best practices
   - Comprehensive test coverage

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment
2. Use a strong `SECRET_KEY` (32+ characters)
3. Configure PostgreSQL database URL
4. Set up proper CORS origins
5. Configure rate limiting
6. Use HTTPS/TLS
7. Set up monitoring and logging

## Next Steps

This API is ready for:

- CLI integration for local file management
- Web interface development
- Advanced search features (full-text search)
- Collaboration features (shared prompts)
- Export/import functionality
- Integration with external tools

The flexible authentication system supports both JWT tokens (for web interfaces) and API keys (for CLI tools), making it perfect for the complete Ruru prompt management ecosystem.
