# ----------------------------------------------------------------------------
# Dockerfile – Production image for a Prompta FastAPI service
# ----------------------------------------------------------------------------
# • Uses the official Python 3.11 slim image
# • Installs dependencies with "uv" (https://github.com/astral-sh/uv) which is
#   significantly faster than the traditional "pip" resolver/installer.
# • Applies Alembic migrations automatically on start-up before launching the
#   Uvicorn server.
# ----------------------------------------------------------------------------

FROM python:3.11-slim AS runtime

# ---------------------------------------------------------------------------
# Runtime environment configuration
# ---------------------------------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---------------------------------------------------------------------------
# System-level dependencies required by common Python wheels (psycopg2, etc.)
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Install "uv" and project dependencies
#   1. We first copy only the requirements file(s) so Docker can leverage layer
#      caching when source code changes but dependencies do not.
#   2. Install uv via pip (it is a self-contained binary wheel so very quick).
#   3. Use `uv pip install --system` to install requirements directly into the
#      system site-packages (no virtualenv in Docker image necessary).
# ---------------------------------------------------------------------------

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip uv \
    && uv pip install --system -r requirements.txt

# ---------------------------------------------------------------------------
# Copy the rest of the application source tree
# ---------------------------------------------------------------------------
COPY . .

# Application will listen on port 8000 inside the container
EXPOSE 8000

# ---------------------------------------------------------------------------
# Entrypoint
#   1. Run Alembic migrations (idempotent) so the DB schema is always up-to-date.
#   2. Start the ASGI server.
# ---------------------------------------------------------------------------

CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
