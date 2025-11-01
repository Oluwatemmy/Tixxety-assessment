# Tixxety API

FastAPI service for event and ticket booking management with Celery background tasks.

---

## Assumptions

- **Python 3.11+** installed
- **PostgreSQL** database running locally or via Docker
- **Redis** for Celery task queue and result backend

---

## Setup

1. **Clone the repository:**

```powershell
git clone https://github.com/Oluwatemmy/Tixxety-assessment.git
cd Tixxety-assessment
```

2. **Create virtual environment and install dependencies:**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/tixxety
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
RESULT_EXPIRATION=3600
```

---

## How to Run

### 1. Run the API server

```powershell
uvicorn main:app --reload --port 8000
```

**API Documentation:** http://localhost:8000/docs

### 2. Run Celery worker in another terminal (requires Redis already running)

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
pytest -v
```

Run specific test files:
```powershell
python -m pytest tests/test_users.py -v
python -m pytest tests/test_events.py -v
python -m pytest tests/test_tickets.py -v
```

**Note:** Tests use an isolated test database and mock Celery where needed.

---

## Docker (Optional)
> Note: Make sure you have a .env file with the database and environment variables set as follows:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/tixxety

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
RESULT_EXPIRATION=3600
```

Build and run all services (API, Celery worker, Redis, PostgreSQL):
```powershell
docker compose up --build -d
```

Apply migrations inside the backend container:
```powershell
docker compose exec tixxety-backend python run_migrations.py
```

View logs:
```powershell
docker compose logs -f tixxety-backend
docker compose logs -f tixxety-worker
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
tests/               # Pytest test suite
main.py              # FastAPI application entry point
makemigrations.py    # Script to create new migrations
run_migrations.py    # Script to apply migrations
run_tests.py         # Script to run the test suite
docker-compose.yml   # Docker orchestration
Dockerfile           # Container image definition
.dockerignore        # Docker ignore file
requirements.txt     # Python dependencies
```
---

## API Endpoints

- `GET /` - Health check
- `POST /users/` - Create user
- `GET /users/for-you/` - Get nearby events for a user
- `GET /users/{user_id}/tickets` - Get tickets for a user
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
