# Same Dockerfile contents as template.

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip uv \
    && uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8000

CMD alembic revision --autogenerate -m "create table" && \
    alembic upgrade head && \
