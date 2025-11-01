# Tixxety API

FastAPI service for event and ticket booking management with Celery background tasks.

---

## Assumptions

- **Python 3.11+** installed
- **SQLite** used by default (no database setup needed)
- **Optional**: Redis for Celery tasks, PostgreSQL for production

---

## Setup

1. **Create virtual environment and install dependencies:**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Environment variables (optional):**

For PostgreSQL + Redis (production):
```env
DATABASE_URL=postgresql+psycopg2://USER:PASS@localhost:5432/tixxety
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
RESULT_EXPIRATION=3600
```

For SQLite (default - no setup needed):
```env
DATABASE_URL=sqlite:///./app/tixxety.db
```

---

## How to Run

### 1. Run the API server

```powershell
uvicorn main:app --reload --port 8000
```

**API Documentation:** http://localhost:8000/docs

### 2. Run Celery worker (optional, requires Redis)

```powershell
celery -A app.celery_worker.celery_app worker --loglevel=info --pool=solo
```

### 3. Apply database migrations

```powershell
python run_migrations.py
```

To auto-generate a new migration:
```powershell
python makemigrations.py
```

---

## Running Tests

Run all tests:
```powershell
python run_tests.py
```

Or with pytest directly:
```powershell
python -m pytest tests/ -v
```

Run specific test files:
```powershell
python -m pytest tests/test_users.py -v
python -m pytest tests/test_events.py -v
python -m pytest tests/test_tickets.py -v
```

**Note:** Tests use an isolated SQLite database and mock Celery where needed.

---

## Docker (Optional)

Build and run all services (API, Celery worker, Redis, PostgreSQL):

```powershell
docker compose up --build -d
```

View logs:
```powershell
docker compose logs -f backend
docker compose logs -f worker
```

Stop services:
```powershell
docker compose down -v
```

**Note:** Docker uses service hostnames (`db`, `redis`) defined in `docker-compose.yml`.

---

## Project Structure

```
app/
  routers/           # API endpoints (users, events, tickets)
  models/            # SQLAlchemy models (User, Event, Ticket)
  schemas/           # Pydantic request/response models
  database.py        # Database configuration
  tasks.py           # Celery background tasks
  celery_worker.py   # Celery app configuration
alembic/             # Database migration scripts
main.py              # FastAPI application entry point
tests/               # Pytest test suite
docker-compose.yml   # Docker orchestration
Dockerfile           # Container image definition
requirements.txt     # Python dependencies
```

---

## API Endpoints

- `GET /` - Health check
- `POST /users/` - Create user
- `GET /users/for-you/` - Get nearby events for a user
- `POST /events/` - Create event
- `GET /events/` - List all events
- `POST /tickets/` - Reserve ticket
- `POST /tickets/{ticket_id}/pay` - Pay for reserved ticket

Interactive API docs: http://localhost:8000/docs

---

## Features

- **User Management**: Create users with location data
- **Event Management**: Create and list events with venue information
- **Ticket Booking**: Reserve tickets with automatic expiration (2 minutes)
- **Payment Processing**: Pay for reserved tickets before expiration
- **Nearby Events**: Find events within specified distance using Haversine formula
- **Background Tasks**: Celery-based ticket expiration
- **Full Test Coverage**: Unit and integration tests for all features

---

MIT Licensed.
