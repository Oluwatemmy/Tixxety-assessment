"""
Test configuration and fixtures for Tixxety API tests.
"""
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
import os
from unittest.mock import patch, MagicMock

from app.database import Base, get_db
from main import app
from app import tasks
from app.models import User, Event, Ticket, TicketStatus, Venue
from datetime import datetime, timezone, timedelta


# Create SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tixxety.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# ✅ Enable foreign key enforcement for SQLite
@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    with patch('app.tasks.SessionLocal', return_value=db):
        yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Patch SessionLocal in tasks module to use test session
    with patch('app.tasks.SessionLocal') as mock_session:
        mock_session.return_value = db_session
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        name="John Doe",
        email="john@example.com",
        location_address="123 Main St, City, Country",
        location_latitude=40.7128,
        location_longitude=-74.0060
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user_no_location(db_session):
    """Create a sample user without location for testing."""
    user = User(
        name="Jane Smith",
        email="jane@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_event(db_session):
    """Create a sample event for testing."""
    future_time = datetime.now(timezone.utc) + timedelta(days=7)
    event = Event(
        title="Test Event",
        description="A test event",
        start_time=future_time,
        end_time=future_time + timedelta(hours=2),
        total_tickets=100,
        tickets_sold=0,
        address="456 Event Ave, City, Country",
        latitude=40.7589,
        longitude=-73.9851
    )
    db_session.add(event)
    try:
        db_session.commit()
        db_session.refresh(event)
    except IntegrityError as e:
        db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event creation failed due to invalid data or constraint validation.")
    return event


@pytest.fixture
def past_event(db_session):
    """Create a past event for testing."""
    past_time = datetime.now(timezone.utc) - timedelta(days=7)
    event = Event(
        title="Past Event",
        description="A past event",
        start_time=past_time - timedelta(hours=2),
        end_time=past_time,
        total_tickets=50,
        tickets_sold=10,
        address="789 Past St, City, Country",
        latitude=40.7589,
        longitude=-73.9851
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def sold_out_event(db_session):
    """Create a sold out event for testing."""
    future_time = datetime.now(timezone.utc) + timedelta(days=7)
    event = Event(
        title="Sold Out Event",
        description="A sold out event",
        start_time=future_time,
        end_time=future_time + timedelta(hours=2),
        total_tickets=5,
        tickets_sold=5,
        address="999 Sold Out Blvd, City, Country",
        latitude=40.7589,
        longitude=-73.9851
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def sample_ticket(db_session, sample_user, sample_event):
    """Create a sample ticket for testing."""
    ticket = Ticket(
        user_id=sample_user.id,
        event_id=sample_event.id,
        status=TicketStatus.RESERVED,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.fixture
def paid_ticket(db_session, sample_user, sample_event):
    """Create a paid ticket for testing."""
    ticket = Ticket(
        user_id=sample_user.id,
        event_id=sample_event.id,
        status=TicketStatus.PAID,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.fixture
def expired_ticket(db_session, sample_user, sample_event):
    """Create an expired ticket for testing."""
    ticket = Ticket(
        user_id=sample_user.id,
        event_id=sample_event.id,
        status=TicketStatus.EXPIRED,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


@pytest.fixture
def mock_celery_task():
    """Mock celery task for testing."""
    with patch('app.tasks.expire_unpaid_ticket.apply_async') as mock_task:
        mock_task.return_value = MagicMock()
        yield mock_task


@pytest.fixture
def multiple_events_with_locations(db_session):
    """Create multiple events with different locations for testing nearby events."""
    future_time = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Event very close to user (NYC coordinates: 40.7128, -74.0060)
    close_event = Event(
        title="Close Event",
        description="Very close event",
        start_time=future_time,
        end_time=future_time + timedelta(hours=2),
        total_tickets=50,
        tickets_sold=0,
        address="Close Location",
        latitude=40.7130,  # Very close
        longitude=-74.0058
    )
    
    # Event moderately close (within 30km)
    moderate_event = Event(
        title="Moderate Event",
        description="Moderately close event",
        start_time=future_time + timedelta(hours=1),
        end_time=future_time + timedelta(hours=3),
        total_tickets=75,
        tickets_sold=0,
        address="Moderate Location",
        latitude=40.7500,  # ~4km away
        longitude=-74.0000
    )
    
    # Event far away (beyond 30km)
    far_event = Event(
        title="Far Event",
        description="Far away event",
        start_time=future_time + timedelta(hours=2),
        end_time=future_time + timedelta(hours=4),
        total_tickets=100,
        tickets_sold=0,
        address="Far Location",
        latitude=41.0000,  # ~32km away
        longitude=-74.0000
    )
    
    # Event without location
    no_location_event = Event(
        title="No Location Event",
        description="Event without coordinates",
        start_time=future_time + timedelta(hours=3),
        end_time=future_time + timedelta(hours=5),
        total_tickets=25,
        tickets_sold=0,
        address="No Coordinates Location"
        # No latitude/longitude
    )
    
    db_session.add_all([close_event, moderate_event, far_event, no_location_event])
    db_session.commit()
    
    return {
        'close': close_event,
        'moderate': moderate_event,
        'far': far_event,
        'no_location': no_location_event
    }
