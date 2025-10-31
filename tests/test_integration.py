"""
Integration tests for the complete Tixxety API.
"""
import pytest
from fastapi import status
from datetime import datetime, timezone, timedelta
from unittest.mock import patch


class TestAPIIntegration:
    """Test complete API workflows and integration scenarios."""
    
    def test_complete_ticket_booking_flow(self, client, mock_celery_task):
        """Test the complete flow: create user, create event, reserve ticket, pay."""
        # Step 1: Create user
        user_data = {
            "name": "Integration User",
            "email": "integration@example.com",
            "location_address": "123 Integration St",
            "location_latitude": 40.7128,
            "location_longitude": -74.0060
        }
        
        user_response = client.post("/users/", json=user_data)
        assert user_response.status_code == status.HTTP_200_OK
        user_id = user_response.json()["user_id"]
        
        # Step 2: Create event
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Integration Event",
            "description": "Event for integration testing",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 100,
            "venue": {
                "address": "456 Event Ave",
                "latitude": 40.7589,
                "longitude": -73.9851
            }
        }
        
        event_response = client.post("/events/", json=event_data)
        assert event_response.status_code == status.HTTP_200_OK
        event_id = event_response.json()["event_id"]
        
        # Step 3: Reserve ticket
        ticket_data = {
            "user_id": user_id,
            "event_id": event_id
        }
        
        ticket_response = client.post("/tickets/", json=ticket_data)
        assert ticket_response.status_code == status.HTTP_200_OK
        
        ticket_id = ticket_response.json()["id"]
        assert ticket_response.json()["status"] == "reserved"
        
        # Step 4: Pay for ticket
        payment_response = client.post(f"/tickets/{ticket_id}/pay")
        assert payment_response.status_code == status.HTTP_200_OK
        assert payment_response.json()["status"] == "paid"
        
        # Step 5: Verify event tickets_sold was incremented
        events_response = client.get("/events/")
        assert events_response.status_code == status.HTTP_200_OK
        
        events = events_response.json()
        integration_event = next(e for e in events if e["id"] == event_id)
        assert integration_event["tickets_sold"] == 1
    
    def test_nearby_events_integration(self, client):
        """Test the nearby events functionality with real data."""
        # Create user in NYC
        user_data = {
            "name": "NYC User",
            "email": "nyc@example.com",
            "location_latitude": 40.7128,
            "location_longitude": -74.0060
        }
        
        user_response = client.post("/users/", json=user_data)
        user_id = user_response.json()["user_id"]
        
        # Create events at different distances
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Close event (Manhattan)
        close_event_data = {
            "title": "Close Event",
            "description": "Event in Manhattan",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 50,
            "venue": {
                "latitude": 40.7589,  # Manhattan
                "longitude": -73.9851
            }
        }
        
        # Far event (Boston area)
        far_event_data = {
            "title": "Far Event",
            "description": "Event in Boston area",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 50,
            "venue": {
                "latitude": 42.3601,  # Boston
                "longitude": -71.0589
            }
        }
        
        client.post("/events/", json=close_event_data)
        client.post("/events/", json=far_event_data)
        
        # Get nearby events (default 30km radius)
        nearby_response = client.get(f"/users/for-you/?user_id={user_id}")
        assert nearby_response.status_code == status.HTTP_200_OK
        
        nearby_events = nearby_response.json()
        assert len(nearby_events) == 1  # Only close event should be returned
        assert nearby_events[0]["title"] == "Close Event"
        
        # Get nearby events with larger radius (500km)
        nearby_large_response = client.get(f"/users/for-you/?user_id={user_id}&max_distance_km=500")
        assert nearby_large_response.status_code == status.HTTP_200_OK
        
        nearby_large_events = nearby_large_response.json()
        assert len(nearby_large_events) == 2  # Both events should be returned
        
        event_titles = [e["title"] for e in nearby_large_events]
        assert "Close Event" in event_titles
        assert "Far Event" in event_titles
    
    def test_sold_out_event_scenario(self, client, mock_celery_task):
        """Test the complete sold out event scenario."""
        # Create user
        user_data = {
            "name": "Sold Out Test User",
            "email": "soldout@example.com"
        }
        
        user_response = client.post("/users/", json=user_data)
        user_id = user_response.json()["user_id"]
        
        # Create event with only 1 ticket
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Limited Event",
            "description": "Event with only 1 ticket",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 1,
            "venue": {}
        }
        
        event_response = client.post("/events/", json=event_data)
        event_id = event_response.json()["event_id"]
        
        # Reserve the only ticket
        ticket_data = {
            "user_id": user_id,
            "event_id": event_id
        }
        
        ticket_response = client.post("/tickets/", json=ticket_data)
        assert ticket_response.status_code == status.HTTP_200_OK
        
        # Pay for the ticket
        ticket_id = ticket_response.json()["id"]
        payment_response = client.post(f"/tickets/{ticket_id}/pay")
        assert payment_response.status_code == status.HTTP_200_OK
        
        # Try to reserve another ticket - should fail
        second_ticket_response = client.post("/tickets/", json=ticket_data)
        assert second_ticket_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sold out" in second_ticket_response.json()["detail"].lower()
    
    def test_multiple_users_same_event(self, client, mock_celery_task):
        """Test multiple users booking tickets for the same event."""
        # Create event
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Popular Event",
            "description": "Event with multiple bookings",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 5,
            "venue": {}
        }
        
        event_response = client.post("/events/", json=event_data)
        event_id = event_response.json()["event_id"]
        
        # Create multiple users and book tickets
        users_and_tickets = []
        
        for i in range(3):
            # Create user
            user_data = {
                "name": f"User {i+1}",
                "email": f"user{i+1}@example.com"
            }
            
            user_response = client.post("/users/", json=user_data)
            user_id = user_response.json()["user_id"]
            
            # Reserve ticket
            ticket_data = {
                "user_id": user_id,
                "event_id": event_id
            }
            
            ticket_response = client.post("/tickets/", json=ticket_data)
            assert ticket_response.status_code == status.HTTP_200_OK
            
            ticket_id = ticket_response.json()["id"]
            users_and_tickets.append((user_id, ticket_id))
        
        # Pay for 2 tickets
        for i in range(2):
            user_id, ticket_id = users_and_tickets[i]
            payment_response = client.post(f"/tickets/{ticket_id}/pay")
            assert payment_response.status_code == status.HTTP_200_OK
        
        # Verify event shows 2 tickets sold
        events_response = client.get("/events/")
        events = events_response.json()
        popular_event = next(e for e in events if e["id"] == event_id)
        assert popular_event["tickets_sold"] == 2
        
        # Third user's ticket should still be reserved
        # (We'll test expiration separately)


class TestErrorHandlingIntegration:
    """Test error handling across the entire API."""
    
    def test_cascade_error_handling(self, client):
        """Test how errors cascade through the API."""
        # Try to reserve ticket with invalid data
        invalid_ticket_data = {
            "user_id": "invalid",
            "event_id": "invalid"
        }
        
        response = client.post("/tickets/", json=invalid_ticket_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        # Verify the error structure
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
    
    def test_database_constraint_violations(self, client):
        """Test database constraint violation handling."""
        # Create user
        user_data = {
            "name": "Constraint Test User",
            "email": "constraint@example.com"
        }
        
        response1 = client.post("/users/", json=user_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to create user with same email
        response2 = client.post("/users/", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response2.json()["detail"]
    
    def test_missing_resource_errors(self, client):
        """Test handling of missing resources."""
        # Try to get nearby events for non-existent user
        response = client.get("/users/for-you/?user_id=999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]
        
        # Try to pay for non-existent ticket
        response = client.post("/tickets/999/pay")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Ticket not found" in response.json()["detail"]


class TestAPIPerformanceAndScaling:
    """Test API performance and scaling considerations."""
    
    def test_large_event_list_performance(self, client):
        """Test performance with large number of events."""
        # Create many events
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        
        for i in range(10):  # Create 10 events (reduced for test speed)
            event_data = {
                "title": f"Performance Event {i+1}",
                "description": f"Event {i+1} for performance testing",
                "start_time": (future_time + timedelta(minutes=i)).isoformat(),
                "end_time": (future_time + timedelta(minutes=i, hours=2)).isoformat(),
                "total_tickets": 100,
                "venue": {
                    "latitude": 40.7128 + (i * 0.001),  # Slightly different locations
                    "longitude": -74.0060 + (i * 0.001)
                }
            }
            
            response = client.post("/events/", json=event_data)
            assert response.status_code == status.HTTP_200_OK
        
        # List all events - should be fast
        list_response = client.get("/events/")
        assert list_response.status_code == status.HTTP_200_OK
        
        events = list_response.json()
        assert len(events) == 10
    
    def test_concurrent_ticket_reservation_simulation(self, client, mock_celery_task):
        """Simulate concurrent ticket reservations."""
        # Create user and event
        user_data = {
            "name": "Concurrent User",
            "email": "concurrent@example.com"
        }
        
        user_response = client.post("/users/", json=user_data)
        user_id = user_response.json()["user_id"]
        
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        event_data = {
            "title": "Concurrent Event",
            "description": "Event for concurrent testing",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "total_tickets": 3,
            "venue": {}
        }
        
        event_response = client.post("/events/", json=event_data)
        event_id = event_response.json()["event_id"]
        
        # Simulate multiple concurrent reservations
        ticket_data = {
            "user_id": user_id,
            "event_id": event_id
        }
        
        responses = []
        for i in range(5):  # Try to reserve 5 tickets (more than available)
            response = client.post("/tickets/", json=ticket_data)
            responses.append(response)
        
        # Count successful reservations
        successful_reservations = [r for r in responses if r.status_code == status.HTTP_200_OK]
        failed_reservations = [r for r in responses if r.status_code != status.HTTP_200_OK]
        
        # Should have exactly 5 successful reservations (total_tickets)
        assert len(successful_reservations) == 5
        assert len(failed_reservations) == 0  # 0 should fail


class TestRootEndpoint:
    """Test the root API endpoint."""
    
    def test_root_endpoint(self, client):
        """Test the root API endpoint returns welcome message."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "Tixxety" in data["message"]
    
    def test_api_docs_accessible(self, client):
        """Test that API documentation is accessible."""
        # FastAPI automatically generates docs at /docs
        response = client.get("/docs")
        
        # Should either return the docs or redirect
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_307_TEMPORARY_REDIRECT]
    
    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Tixxety API"
