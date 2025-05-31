# Prompta Project

A self-hosted prompt management system built with FastAPI.

## Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Copy environment configuration:**

   ```bash
   cp .env.example .env
   ```

3. **Run database migrations:**

   ```bash
   prompta migrate
   # or use alembic directly: alembic upgrade head
   ```

4. **Create a superuser:**

   ```bash
   prompta createsuperuser
   ```

5. **Start the development server:**
   ```bash
   prompta runserver
   # or use uvicorn directly: uvicorn app.main:app --reload
   ```

The API will be available at http://127.0.0.1:8000

## API Documentation

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Secret key for JWT tokens (auto-generated)
- `DATABASE_URL`: Database connection string
- `DEBUG`: Enable debug mode

## Commands

### Prompta Commands (Convenience Wrappers)

- `prompta migrate` - Run database migrations
- `prompta runserver` - Start development server
- `prompta createsuperuser` - Create admin users

### Using Underlying Tools Directly

You can also use the standard tools directly for more control:

```bash
# Database migrations with Alembic
alembic upgrade head                    # Apply all migrations
alembic revision --autogenerate -m "description"  # Create new migration
alembic downgrade -1                    # Rollback one migration

# Development server with Uvicorn
uvicorn app.main:app --reload           # Start with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8080  # Custom host/port
```

## Project Structure

- `app/` - FastAPI application
- `auth/` - Authentication and user management
- `prompts/` - Prompt management
- `models/` - Database models
- `migrations/` - Database migrations
- `tests/` - Test suite
