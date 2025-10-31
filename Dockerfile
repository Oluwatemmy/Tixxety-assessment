# ---------- Base Image ----------
FROM python:3.11-slim AS base

# Prevent Python from buffering stdout and creating .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ---------- FastAPI App ----------
FROM base AS api
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------- Celery Worker ----------
FROM base AS worker
CMD ["celery", "-A", "app.celery_worker.celery_app", "worker", "--loglevel=info"]