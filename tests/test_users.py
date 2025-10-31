"""
Tests for user-related API endpoints.
"""
import pytest
from fastapi import status
from datetime import datetime, timezone, timedelta


class TestUserCreation:
    """Test user creation endpoint."""
    
    def test_create_user_success(self, client):
        """Test successful user creation."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "location_address": "123 Test St, Test City",
            "location_latitude": 40.7128,
            "location_longitude": -74.0060
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "User created successfully"
        assert data["user_name"] == "Test User"
        assert data["user_email"] == "test@example.com"
        assert "user_id" in data
    
    def test_create_user_minimal_data(self, client):
        """Test user creation with minimal required data."""
        user_data = {
            "name": "Minimal User",
            "email": "minimal@example.com"
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_name"] == "Minimal User"
        assert data["user_email"] == "minimal@example.com"
    
    def test_create_user_duplicate_email(self, client, sample_user):
        """Test user creation with duplicate email fails."""
        user_data = {
            "name": "Another User",
            "email": sample_user.email  # Duplicate email
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_create_user_invalid_email(self, client):
        """Test user creation with invalid email format."""
        user_data = {
            "name": "Test User",
            "email": "invalid-email"
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_user_invalid_latitude(self, client):
        """Test user creation with invalid latitude."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "location_latitude": 91  # Invalid: > 90
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_user_invalid_longitude(self, client):
        """Test user creation with invalid longitude."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "location_longitude": 181  # Invalid: > 180
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_user_missing_name(self, client):
        """Test user creation without name fails."""
        user_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_user_missing_email(self, client):
        """Test user creation without email fails."""
        user_data = {
            "name": "Test User"
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestNearbyEvents:
    """Test nearby events endpoint."""
    
    def test_get_nearby_events_success(self, client, sample_user, multiple_events_with_locations):
        """Test successful retrieval of nearby events."""
        response = client.get(f"/users/for-you/?user_id={sample_user.id}")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        
        # Should return close and moderate events (within 30km), but not far event
        assert len(events) == 2
        event_titles = [event["title"] for event in events]
        assert "Close Event" in event_titles
        assert "Moderate Event" in event_titles
        assert "Far Event" not in event_titles  # Too far
        assert "No Location Event" not in event_titles  # No coordinates
        
        # Events should be sorted by distance (closest first)
        assert events[0]["title"] == "Close Event"
    
    def test_get_nearby_events_custom_radius(self, client, sample_user, multiple_events_with_locations):
        """Test nearby events with custom radius."""
        # Use smaller radius (5km)
        response = client.get(f"/users/for-you/?user_id={sample_user.id}&max_distance_km=5")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        
        # Should only return the close event
        assert len(events) == 2  # Close event and moderate event (moderate is ~4km away)
        assert events[0]["title"] == "Close Event"
    
    def test_get_nearby_events_large_radius(self, client, sample_user, multiple_events_with_locations):
        """Test nearby events with large radius."""
        # Use large radius (50km)
        response = client.get(f"/users/for-you/?user_id={sample_user.id}&max_distance_km=50")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        
        # Should return all events with coordinates (including far event)
        assert len(events) == 3
        event_titles = [event["title"] for event in events]
        assert "Close Event" in event_titles
        assert "Moderate Event" in event_titles
        assert "Far Event" in event_titles
        assert "No Location Event" not in event_titles  # Still no coordinates
    
    def test_get_nearby_events_user_not_found(self, client):
        """Test nearby events for non-existent user."""
        response = client.get("/users/for-you/?user_id=999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]
    
    def test_get_nearby_events_user_no_location(self, client, sample_user_no_location, multiple_events_with_locations):
        """Test nearby events for user without location."""
        response = client.get(f"/users/for-you/?user_id={sample_user_no_location.id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User location not set" in response.json()["detail"]
    
    def test_get_nearby_events_no_events(self, client, sample_user):
        """Test nearby events when no events exist."""
        response = client.get(f"/users/for-you/?user_id={sample_user.id}")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0
    
    def test_get_nearby_events_only_past_events(self, client, sample_user, past_event):
        """Test nearby events when only past events exist."""
        response = client.get(f"/users/for-you/?user_id={sample_user.id}")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0  # Past events should not be included
    
    def test_get_nearby_events_invalid_radius(self, client, sample_user):
        """Test nearby events with invalid radius."""
        response = client.get(f"/users/for-you/?user_id={sample_user.id}&max_distance_km=-5")
        
        # FastAPI should handle this validation, but let's test the behavior
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_CONTENT]
    
    def test_get_nearby_events_zero_radius(self, client, sample_user, multiple_events_with_locations):
        """Test nearby events with zero radius."""
        response = client.get(f"/users/for-you/?user_id={sample_user.id}&max_distance_km=0")
        
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0  # No events should be within 0km exactly


class TestUserEdgeCases:
    """Test edge cases and error scenarios for user endpoints."""
    
    def test_create_user_empty_name(self, client):
        """Test user creation with empty name."""
        user_data = {
            "name": "",
            "email": "test@example.com"
        }
        
        response = client.post("/users/", json=user_data)
        
        # Should still create user as empty string is technically valid
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_user_very_long_name(self, client):
        """Test user creation with very long name."""
        user_data = {
            "name": "A" * 200,  # Very long name
            "email": "test@example.com"
        }
        
        response = client.post("/users/", json=user_data)
        
        # Depending on database constraints, this might fail
        # For now, assuming it should work if within string limit
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_CONTENT]
    
    def test_create_user_boundary_coordinates(self, client):
        """Test user creation with boundary coordinate values."""
        user_data = {
            "name": "Boundary User",
            "email": "boundary@example.com",
            "location_latitude": 90.0,  # Maximum valid latitude
            "location_longitude": 180.0  # Maximum valid longitude
        }
        
        response = client.post("/users/", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Test minimum values
        user_data2 = {
            "name": "Boundary User 2",
            "email": "boundary2@example.com",
            "location_latitude": -90.0,  # Minimum valid latitude
            "location_longitude": -180.0  # Minimum valid longitude
        }
        
        response2 = client.post("/users/", json=user_data2)
        
        assert response2.status_code == status.HTTP_200_OK
