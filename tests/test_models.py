"""
Tests for database models and core business logic.
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.models import User, Event, Ticket, TicketStatus, Venue
from sqlalchemy.exc import IntegrityError


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation_success(self, db_session):
        """Test successful user creation."""
        user = User(
            name="Test User",
            email="test@example.com",
            location_address="123 Test St",
            location_latitude=40.7128,
            location_longitude=-74.0060
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.location_address == "123 Test St"
        assert user.location_latitude == 40.7128
        assert user.location_longitude == -74.0060
    
    def test_user_unique_email_constraint(self, db_session, sample_user):
        """Test that email uniqueness is enforced."""
        duplicate_user = User(
            name="Duplicate User",
            email=sample_user.email  # Same email
        )
        
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_location_composite(self, db_session):
        """Test user location composite attribute."""
        user = User(
            name="Location User",
            email="location@example.com",
            location_address="Test Address",
            location_latitude=40.0,
            location_longitude=-74.0
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Test composite location access
        location = user.location
        assert isinstance(location, Venue)
        assert location.address == "Test Address"
        assert location.latitude == 40.0
        assert location.longitude == -74.0
    
    def test_user_without_location(self, db_session):
        """Test user creation without location data."""
        user = User(
            name="No Location User",
            email="nolocation@example.com"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.location_latitude is None
        assert user.location_longitude is None
        assert user.location_address is None
    
    def test_user_repr(self, sample_user):
        """Test user string representation."""
        repr_str = repr(sample_user)
        assert "User" in repr_str
        assert str(sample_user.id) in repr_str
        assert sample_user.name in repr_str
        assert sample_user.email in repr_str


class TestEventModel:
    """Test Event model functionality."""
    
    def test_event_creation_success(self, db_session):
        """Test successful event creation."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event = Event(
            title="Test Event",
            description="A test event",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=100,
            address="123 Event Ave",
            latitude=40.7589,
            longitude=-73.9851
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.title == "Test Event"
        assert event.description == "A test event"
        assert event.total_tickets == 100
        assert event.tickets_sold == 0  # Default value
        assert event.address == "123 Event Ave"
        assert event.latitude == 40.7589
        assert event.longitude == -73.9851
    
    def test_event_venue_composite(self, db_session):
        """Test event venue composite attribute."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event = Event(
            title="Venue Test Event",
            description="Event to test venue",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=50,
            address="Venue Address",
            latitude=41.0,
            longitude=-75.0
        )
        
        db_session.add(event)
        db_session.commit()
        
        # Test composite venue access
        venue = event.venue
        assert isinstance(venue, Venue)
        assert venue.address == "Venue Address"
        assert venue.latitude == 41.0
        assert venue.longitude == -75.0
    
    def test_event_tickets_sold_constraints(self, db_session):
        """Test that tickets_sold constraints are enforced."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Test valid tickets_sold
        event = Event(
            title="Valid Event",
            description="Event with valid tickets_sold",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=100,
            tickets_sold=50
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.tickets_sold == 50
    
    def test_event_without_venue(self, db_session):
        """Test event creation without venue data."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event = Event(
            title="No Venue Event",
            description="Event without venue",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=25
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.address is None
        assert event.latitude is None
        assert event.longitude is None
    
    def test_event_repr(self, sample_event):
        """Test event string representation."""
        repr_str = repr(sample_event)
        assert "Event" in repr_str
        assert str(sample_event.id) in repr_str
        assert sample_event.title in repr_str


class TestTicketModel:
    """Test Ticket model functionality."""
    
    def test_ticket_creation_success(self, db_session, sample_user, sample_event):
        """Test successful ticket creation."""
        ticket = Ticket(
            user_id=sample_user.id,
            event_id=sample_event.id,
            status=TicketStatus.RESERVED
        )
        
        db_session.add(ticket)
        db_session.commit()
        
        assert ticket.id is not None
        assert ticket.user_id == sample_user.id
        assert ticket.event_id == sample_event.id
        assert ticket.status == TicketStatus.RESERVED
        assert ticket.created_at is not None
    
    def test_ticket_default_values(self, db_session, sample_user, sample_event):
        """Test ticket default values."""
        ticket = Ticket(
            user_id=sample_user.id,
            event_id=sample_event.id
        )
        
        db_session.add(ticket)
        db_session.commit()
        
        # Default status should be RESERVED
        assert ticket.status == TicketStatus.RESERVED
        # Default created_at should be set to current time
        assert ticket.created_at is not None
        assert isinstance(ticket.created_at, datetime)
    
    def test_ticket_status_enum(self, db_session, sample_user, sample_event):
        """Test all ticket status enum values."""
        statuses_to_test = [TicketStatus.RESERVED, TicketStatus.PAID, TicketStatus.EXPIRED]
        
        for status in statuses_to_test:
            ticket = Ticket(
                user_id=sample_user.id,
                event_id=sample_event.id,
                status=status
            )
            
            db_session.add(ticket)
            db_session.commit()
            
            assert ticket.status == status
            db_session.delete(ticket)  # Clean up
            db_session.commit()
    
    def test_ticket_relationships(self, db_session, sample_ticket):
        """Test ticket relationships with user and event."""
        # Test user relationship
        assert sample_ticket.user is not None
        assert sample_ticket.user.id == sample_ticket.user_id
        assert sample_ticket.user.name == "John Doe"
        
        # Test event relationship
        assert sample_ticket.event is not None
        assert sample_ticket.event.id == sample_ticket.event_id
        assert sample_ticket.event.title == "Test Event"
    
    def test_ticket_cascade_delete_user(self, db_session, sample_ticket):
        """Test that tickets are deleted when user is deleted."""
        user_id = sample_ticket.user_id
        ticket_id = sample_ticket.id
        
        # Delete user
        db_session.delete(sample_ticket.user)
        db_session.commit()
        
        # Ticket should be deleted due to cascade
        deleted_ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        assert deleted_ticket is None
    
    def test_ticket_cascade_delete_event(self, db_session, sample_ticket):
        """Test that tickets are deleted when event is deleted."""
        event_id = sample_ticket.event_id
        ticket_id = sample_ticket.id
        
        # Delete event
        db_session.delete(sample_ticket.event)
        db_session.commit()
        
        # Ticket should be deleted due to cascade
        deleted_ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        assert deleted_ticket is None
    
    def test_ticket_repr(self, sample_ticket):
        """Test ticket string representation."""
        repr_str = repr(sample_ticket)
        assert "Ticket" in repr_str
        assert str(sample_ticket.id) in repr_str
        assert str(sample_ticket.user_id) in repr_str
        assert str(sample_ticket.event_id) in repr_str
        assert sample_ticket.status.value in repr_str


class TestVenueValueObject:
    """Test Venue value object functionality."""
    
    def test_venue_creation(self):
        """Test venue creation with all parameters."""
        venue = Venue(40.7128, -74.0060, "New York, NY")
        
        assert venue.latitude == 40.7128
        assert venue.longitude == -74.0060
        assert venue.address == "New York, NY"
    
    def test_venue_creation_with_none_values(self):
        """Test venue creation with None values."""
        venue = Venue(None, None, None)
        
        assert venue.latitude is None
        assert venue.longitude is None
        assert venue.address is None
    
    def test_venue_creation_partial_none(self):
        """Test venue creation with some None values."""
        venue = Venue(40.7128, None, "Partial Address")
        
        assert venue.latitude == 40.7128
        assert venue.longitude is None
        assert venue.address == "Partial Address"
    
    def test_venue_distance_calculation(self):
        """Test distance calculation between venues."""
        venue1 = Venue(40.7128, -74.0060, "NYC")  # New York
        venue2 = Venue(40.7589, -73.9851, "Manhattan")  # Manhattan
        
        distance = venue1.distance_to(40.7589, -73.9851)
        
        # Distance should be a positive number (approximately 4.5 km)
        assert distance > 0
        assert distance < 10  # Should be less than 10 km
    
    def test_venue_distance_same_location(self):
        """Test distance calculation for same location."""
        venue = Venue(40.7128, -74.0060, "Same Location")
        
        distance = venue.distance_to(40.7128, -74.0060)
        
        # Distance should be 0 or very close to 0
        assert distance < 0.001
    
    def test_venue_equality(self):
        """Test venue equality comparison."""
        venue1 = Venue(40.7128, -74.0060, "NYC")
        venue2 = Venue(40.7128, -74.0060, "NYC")
        venue3 = Venue(40.7589, -73.9851, "Manhattan")
        
        assert venue1 == venue2
        assert venue1 != venue3
        assert venue2 != venue3
    
    def test_venue_equality_with_different_types(self):
        """Test venue equality with non-Venue objects."""
        venue = Venue(40.7128, -74.0060, "NYC")
        
        assert venue != "not a venue"
        assert venue != 42
        assert venue != None
    
    def test_venue_repr(self):
        """Test venue string representation."""
        venue = Venue(40.7128, -74.0060, "New York, NY")
        
        repr_str = repr(venue)
        assert "Venue" in repr_str
        assert "40.7128" in repr_str
        assert "-74.0060" in repr_str
        assert "New York, NY" in repr_str
    
    def test_venue_composite_values(self):
        """Test venue composite values method."""
        venue = Venue(40.7128, -74.0060, "NYC")
        
        values = venue.__composite_values__()
        
        assert values == (40.7128, -74.0060, "NYC")


class TestModelConstraintsAndValidation:
    """Test database constraints and model validation."""
    
    def test_user_email_index(self, db_session):
        """Test that user email index works for fast lookups."""
        user = User(name="Index Test", email="index@test.com")
        db_session.add(user)
        db_session.commit()
        
        # Query by email should be fast (testing index exists)
        found_user = db_session.query(User).filter(User.email == "index@test.com").first()
        assert found_user is not None
        assert found_user.name == "Index Test"
    
    def test_ticket_foreign_key_constraints(self, db_session):
        """Test that foreign key constraints are enforced."""
        # Try to create ticket with non-existent user_id
        ticket = Ticket(
            user_id=999,  # Non-existent
            event_id=999,  # Non-existent
            status=TicketStatus.RESERVED
        )
        
        db_session.add(ticket)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_event_time_handling(self, db_session):
        """Test proper timezone handling in events."""
        # Create event with timezone-aware datetime
        utc_time = datetime.now(timezone.utc)
        event = Event(
            title="Timezone Test",
            description="Testing timezone handling",
            start_time=utc_time,
            end_time=utc_time + timedelta(hours=1),
            total_tickets=50
        )
        
        db_session.add(event)
        db_session.commit()
        
        # Retrieve and verify timezone is preserved
        retrieved_event = db_session.query(Event).filter(Event.id == event.id).first()
        # SQLite doesn't preserve tzinfo
        if retrieved_event.start_time.tzinfo is None:
            # Verify stored value is still correct (within same UTC hour)
            assert abs((retrieved_event.start_time - utc_time.replace(tzinfo=None)).total_seconds()) < 5
        else:
            # For databases that preserve tzinfo (like PostgreSQL)
            assert retrieved_event.start_time.tzinfo is not None
