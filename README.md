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

## API overview (with examples)

- GET `/` — welcome/health
  - Response 200:
    ```json
    { "message": "Welcome to Tixxety API" }
    ```

- Users
  - POST `/users/` — create user
    - Request body:
      ```json
      {
        "name": "John Doe",
        "email": "john@example.com",
        "location_address": "123 Main St",
        "location_latitude": 40.7128,
        "location_longitude": -74.0060
      }
      ```
    - Response 200:
      ```json
      {
        "message": "User created successfully",
        "user_id": 1,
        "user_name": "John Doe",
        "user_email": "john@example.com"
      }
      ```
    - Errors:
      - 400: { "detail": "Email already registered" }
      - 422: validation errors

  - GET `/users/for-you/?user_id=1&max_distance_km=30` — nearby events for a user
    - Response 200 (sorted by distance):
      ```json
      [
        {
          "id": 10,
          "title": "Tech Conference",
          "description": "Annual event",
          "start_time": "2025-11-05T09:00:00+00:00",
          "end_time": "2025-11-05T17:00:00+00:00",
          "total_tickets": 200,
          "tickets_sold": 12,
          "venue": { "address": "NYC", "latitude": 40.75, "longitude": -73.99 }
        }
      ]
      ```
    - Errors:
      - 404: { "detail": "User not found" }
      - 404: { "detail": "User location not set" }

- Events
  - POST `/events/` — create event
    - Request body:
      ```json
      {
        "title": "Tech Conference",
        "description": "Annual event",
        "start_time": "2025-11-05T09:00:00Z",
        "end_time": "2025-11-05T17:00:00Z",
        "total_tickets": 200,
        "venue": { "address": "NYC", "latitude": 40.75, "longitude": -73.99 }
      }
      ```
    - Response 200:
      ```json
      {
        "message": "Event created successfully",
        "event_id": 10,
        "event_title": "Tech Conference",
        "total_tickets": 200
      }
      ```
    - Errors:
      - 422: validation errors

  - GET `/events/` — list events
    - Response 200:
      ```json
      [
        {
          "id": 10,
          "title": "Tech Conference",
          "description": "Annual event",
          "start_time": "2025-11-05T09:00:00+00:00",
          "end_time": "2025-11-05T17:00:00+00:00",
          "total_tickets": 200,
          "tickets_sold": 12,
          "venue": { "address": "NYC", "latitude": 40.75, "longitude": -73.99 }
        }
      ]
      ```

- Tickets
  - POST `/tickets/` — reserve ticket
    - Request body:
      ```json
      { "user_id": 1, "event_id": 10 }
      ```
    - Response 200:
      ```json
      {
        "id": 55,
        "user_id": 1,
        "event_id": 10,
        "status": "reserved",
        "created_at": "2025-10-31T12:00:00+00:00"
      }
      ```
    - Errors:
      - 404: { "detail": "User not found" }
      - 404: { "detail": "Event not found" }
      - 400: { "detail": "Event is sold out" }

  - POST `/tickets/{ticket_id}/pay` — pay for ticket
    - Response 200:
      ```json
      {
        "id": 55,
        "user_id": 1,
        "event_id": 10,
        "status": "paid",
        "created_at": "2025-10-31T12:00:00+00:00"
      }
      ```
    - Errors:
      - 404: { "detail": "Ticket not found" }
      - 400: { "detail": "Ticket already paid or expired" }

Schemas live in `app/schemas/*`.

---

## Project Structure
```
app/
  routers/
    events.py
    tickets.py
    users.py
  models/
    event_models.py
    ticket_models.py
    user_models.py
    __init__.py            # re-exports User, Event, Venue, Ticket, TicketStatus
  schemas/
    event_payload.py
    ticket_payload.py
    user_payload.py
  database.py
  tasks.py                 # Celery task: expire_unpaid_ticket
  celery_worker.py         # Celery app config
alembic/
  env.py
  versions/
main.py                    # FastAPI app entry
Dockerfile
docker-compose.yml
run_migrations.py
makemigrations.py
run_tests.py
tests/
```

---

## Tips
- Use service hostnames inside Docker: `db`, `redis`
- If using SQLite locally, migrations still work the same
- For dev hot-reload in Docker, add a volume and `--reload` to uvicorn

MIT Licensed. Contributions welcome.
