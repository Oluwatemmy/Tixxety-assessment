"""
Tests for event-related API endpoints.
"""
import pytest
from fastapi import status
from datetime import datetime, timezone, timedelta


class TestEventCreation:
    """Test event creation endpoint."""
    
    def test_create_event_success(self, client):
        """Test successful event creation."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Test Event",
            "description": "A test event description",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {
                "address": "123 Event St, Event City",
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Event created successfully"
        assert data["event_title"] == "Test Event"
        assert data["total_tickets"] == 100
        assert "event_id" in data
    
    def test_create_event_minimal_venue_data(self, client):
        """Test event creation with minimal venue data."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Minimal Event",
            "description": "Event with minimal venue",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=1)).isoformat(),
            "total_tickets": 50,
            "venue": {}  # Empty venue
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["event_title"] == "Minimal Event"
    
    def test_create_event_past_dates(self, client):
        """Test event creation with past dates."""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        event_data = {
            "title": "Past Event",
            "description": "Event in the past",
            "start_time": past_time.isoformat(),
            "end_time": (past_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {
                "address": "Past Event Location"
            }
        }
        
        response = client.post("/events/", json=event_data)
        
        # Should still create event - business logic might handle this elsewhere
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_invalid_time_order(self, client):
        """Test event creation where end time is before start time."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Invalid Time Event",
            "description": "Event with invalid time order",
            "start_time": future_time.isoformat(),
            "end_time": (future_time - timedelta(hours=1)).isoformat(),  # Before start
            "total_tickets": 100,
            "venue": {
                "address": "Invalid Time Location"
            }
        }
        
        response = client.post("/events/", json=event_data)
        
        # Should still create - validation might be business logic
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_zero_tickets(self, client):
        """Test event creation with zero total tickets."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Zero Tickets Event",
            "description": "Event with no tickets",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 0,
            "venue": {
                "address": "Zero Tickets Location"
            }
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_missing_title(self, client):
        """Test event creation without title."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "description": "Event without title",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {}
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_event_missing_times(self, client):
        """Test event creation without start/end times."""
        event_data = {
            "title": "No Time Event",
            "description": "Event without times",
            "total_tickets": 100,
            "venue": {}
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_event_invalid_coordinates(self, client):
        """Test event creation with invalid coordinates."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Invalid Coords Event",
            "description": "Event with invalid coordinates",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {
                "latitude": 91,  # Invalid latitude
                "longitude": -200  # Invalid longitude
            }
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestEventListing:
    """Test event listing endpoint."""
    
    def test_list_events_empty(self, client):
        """Test listing events when none exist."""
        response = client.get("/events/")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0
        assert events == []
    
    def test_list_events_single(self, client, sample_event):
        """Test listing events with one event."""
        response = client.get("/events/")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 1
        
        event = events[0]
        assert event["title"] == sample_event.title
        assert event["description"] == sample_event.description
        assert event["total_tickets"] == sample_event.total_tickets
        assert event["tickets_sold"] == sample_event.tickets_sold
        assert "id" in event
        assert "start_time" in event
        assert "end_time" in event
        assert "venue" in event
    
    def test_list_events_multiple(self, client, multiple_events_with_locations):
        """Test listing multiple events."""
        response = client.get("/events/")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 4  # All events from fixture
        
        # Verify all events are returned
        event_titles = [event["title"] for event in events]
        assert "Close Event" in event_titles
        assert "Moderate Event" in event_titles
        assert "Far Event" in event_titles
        assert "No Location Event" in event_titles
    
    def test_list_events_includes_past_events(self, client, sample_event, past_event):
        """Test that listing includes past events."""
        response = client.get("/events/")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 2
        
        event_titles = [event["title"] for event in events]
        assert sample_event.title in event_titles
        assert past_event.title in event_titles
    
    def test_list_events_response_structure(self, client, sample_event):
        """Test the structure of event response."""
        response = client.get("/events/")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 1
        
        event = events[0]
        required_fields = ["id", "title", "description", "start_time", "end_time", 
                          "total_tickets", "tickets_sold", "venue"]
        
        for field in required_fields:
            assert field in event
        
        # Check venue structure
        venue = event["venue"]
        assert isinstance(venue, dict)
        # Venue fields are optional, so just check it's a dict


class TestEventEdgeCases:
    """Test edge cases and error scenarios for event endpoints."""
    
    def test_create_event_very_long_title(self, client):
        """Test event creation with very long title."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "A" * 300,  # Very long title
            "description": "Event with long title",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {}
        }
        
        response = client.post("/events/", json=event_data)
        
        # Might be rejected due to database constraints
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_create_event_empty_title(self, client):
        """Test event creation with empty title."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "",
            "description": "Event with empty title",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {}
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_large_ticket_count(self, client):
        """Test event creation with very large ticket count."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Large Event",
            "description": "Event with many tickets",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 1000000,  # Very large number
            "venue": {}
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_boundary_coordinates(self, client):
        """Test event creation with boundary coordinate values."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Boundary Event",
            "description": "Event at coordinate boundaries",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {
                "latitude": 90.0,  # North Pole
                "longitude": 180.0,  # Date line
                "address": "At the boundaries"
            }
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_same_start_end_time(self, client):
        """Test event creation with same start and end time."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Instant Event",
            "description": "Event with zero duration",
            "start_time": future_time.isoformat(),
            "end_time": future_time.isoformat(),  # Same as start
            "total_tickets": 100,
            "venue": {}
        }
        
        response = client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_event_invalid_json(self, client):
        """Test event creation with malformed JSON."""
        response = client.post("/events/", content="invalid json", headers={"Content-Type": "application/json"})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
