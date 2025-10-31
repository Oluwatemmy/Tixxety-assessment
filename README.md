# Tixxety API

FastAPI service for managing events and ticket bookings with Celery-based background tasks and SQLAlchemy persistence. Comes with full test coverage (unit + integration), Alembic migrations, and Docker setup.

## Features
- Users: create and locate nearby events (Haversine)
- Events: create, list, geo metadata (address/lat/lng)
- Tickets: reserve, pay, automatic expiration via Celery
- SQLAlchemy models + Alembic migrations
- Comprehensive pytest suite and fixtures
Prereqs: Python 3.11+, Redis (optional for local tests), Postgres or SQLite
1) Create venv and install deps
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2) Environment
- For Postgres (recommended):
```
DATABASE_URL=postgresql+psycopg2://USER:PASS@localhost:5432/tixxety
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
RESULT_EXPIRATION=3600
```
- Or fallback to SQLite (no DB service needed):
```
DATABASE_URL=sqlite:///./app/tixxety.db
```

3) Run API
```powershell
uvicorn main:app --reload --port 8000
```
4) Start Celery in another terminal (Redis must be running)
```powershell
celery -A app.celery_worker.celery_app worker --loglevel=info --pool=solo
```

API docs: http://localhost:8000/docs

---


Local:
```powershell
python makemigrations.py    # autogenerate revision
```

Docker (container):
```powershell
docker compose exec backend python run_migrations.py
```

---

## Running Tests

All tests:
```powershell
python run_tests.py
```

Single file / test:
```powershell
python -m pytest tests/test_users.py -v
python -m pytest tests/test_tasks.py::TestExpireUnpaidTicketTask::test_expire_reserved_ticket -v
```

Notes:
- Tests use an isolated SQLite DB.
- Celery calls are mocked for unit-level tests where appropriate.

---

## Docker
Build & run:
```powershell
docker compose build
```

Services (docker-compose.yml):
- backend (FastAPI): exposes 8000
- redis: broker/result backend
- db: Postgres 15

Required .env for Docker (example):
```
DB_USER=postgres
DB_NAME=tixxety
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
RESULT_EXPIRATION=3600
```

Logs & status:
```powershell
docker compose logs -f backend
docker compose logs -f worker
```

Stop & clean:
```powershell
docker compose down -v
```

---

## API Overview

- GET `/` — health/welcome
- Users
  - POST `/users/` — create user
  - GET `/users/for-you/?user_id=...&max_distance_km=30` — nearby events
- Events
  - GET `/events/` — list events
- Tickets
Schemas: see `app/schemas/*`

---

## Project Structure
```
app/
  routers/        # FastAPI routers (users, events, tickets)
  models.py       # SQLAlchemy models (User, Event, Ticket, Venue)
  database.py     # DB engine & session
  tasks.py        # Celery tasks (expire_unpaid_ticket)
  celery_worker.py# Celery app config
alembic/          # Alembic migrations
main.py           # FastAPI app factory & routes
tests/            # Pytest suite (unit + integration)
```

---

## Tips
- Use service hostnames inside Docker: `db`, `redis`
- If using SQLite locally, migrations still work the same
- For dev hot-reload in Docker, add a volume and `--reload` to uvicorn

MIT Licensed. Contributions welcome.
