# ---------- Base Image ----------
FROM python:3.11-slim AS base

# Prevent Python from buffering stdout and creating .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir  -r requirements.txt


COPY . .

# ---------- FastAPI App ----------
FROM base AS api
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4"]

# ---------- Celery Worker ----------
FROM base AS worker
CMD ["celery", "-A", "app.celery_worker.celery_app", "worker", "--loglevel=info"]