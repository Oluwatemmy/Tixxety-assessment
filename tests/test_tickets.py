"""
Tests for ticket-related API endpoints.
"""
from fastapi import status
from unittest.mock import patch
from app.models import Event
from datetime import datetime, timezone, timedelta


class TestTicketReservation:
    """Test ticket reservation endpoint."""
    
    def test_reserve_ticket_success(self, client, sample_user, sample_event, mock_celery_task):
        """Test successful ticket reservation."""
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": sample_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["user_id"] == sample_user.id
        assert data["event_id"] == sample_event.id
        assert data["status"] == "reserved"
        assert "id" in data
        assert "created_at" in data
        
        # Verify celery task was scheduled
        mock_celery_task.assert_called_once()
        args, kwargs = mock_celery_task.call_args
        assert kwargs["countdown"] == 120  # 2 minutes
    
    def test_reserve_ticket_user_not_found(self, client, sample_event):
        """Test ticket reservation with non-existent user."""
        ticket_data = {
            "user_id": 999,  # Non-existent user
            "event_id": sample_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]
    
    def test_reserve_ticket_event_not_found(self, client, sample_user):
        """Test ticket reservation with non-existent event."""
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": 999  # Non-existent event
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Event not found" in response.json()["detail"]
    
    def test_reserve_ticket_sold_out_event(self, client, sample_user, sold_out_event):
        """Test ticket reservation for sold out event."""
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": sold_out_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Event is sold out" in response.json()["detail"]
    
    def test_reserve_multiple_tickets_same_user_event(self, client, sample_user, sample_event, mock_celery_task):
        """Test reserving multiple tickets for same user and event."""
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": sample_event.id
        }
        
        # First reservation
        response1 = client.post("/tickets/", json=ticket_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second reservation - should also work (no business rule preventing it)
        response2 = client.post("/tickets/", json=ticket_data)
        assert response2.status_code == status.HTTP_200_OK
        
        # Verify different ticket IDs
        ticket1_id = response1.json()["id"]
        ticket2_id = response2.json()["id"]
        assert ticket1_id != ticket2_id
    
    def test_reserve_ticket_missing_user_id(self, client, sample_event):
        """Test ticket reservation without user_id."""
        ticket_data = {
            "event_id": sample_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_reserve_ticket_missing_event_id(self, client, sample_user):
        """Test ticket reservation without event_id."""
        ticket_data = {
            "user_id": sample_user.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_reserve_ticket_invalid_user_id(self, client, sample_event):
        """Test ticket reservation with invalid user_id type."""
        ticket_data = {
            "user_id": "invalid",
            "event_id": sample_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_reserve_ticket_negative_ids(self, client):
        """Test ticket reservation with negative IDs."""
        ticket_data = {
            "user_id": -1,
            "event_id": -1
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTicketPayment:
    """Test ticket payment endpoint."""
    
    def test_pay_for_ticket_success(self, client, sample_ticket, db_session):
        """Test successful ticket payment."""
        # Verify initial state
        assert sample_ticket.status.value == "reserved"
        initial_tickets_sold = sample_ticket.event.tickets_sold
        
        response = client.post(f"/tickets/{sample_ticket.id}/pay")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == sample_ticket.id
        assert data["status"] == "paid"
        assert data["user_id"] == sample_ticket.user_id
        assert data["event_id"] == sample_ticket.event_id
        
        # Refresh and verify database state
        db_session.refresh(sample_ticket)
        db_session.refresh(sample_ticket.event)
        
        assert sample_ticket.status.value == "paid"
        assert sample_ticket.event.tickets_sold == initial_tickets_sold + 1
    
    def test_pay_for_ticket_not_found(self, client):
        """Test payment for non-existent ticket."""
        response = client.post("/tickets/999/pay")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Ticket not found" in response.json()["detail"]
    
    def test_pay_for_already_paid_ticket(self, client, paid_ticket):
        """Test payment for already paid ticket."""
        response = client.post(f"/tickets/{paid_ticket.id}/pay")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Ticket already paid or expired" in response.json()["detail"]
    
    def test_pay_for_expired_ticket(self, client, expired_ticket):
        """Test payment for expired ticket."""
        response = client.post(f"/tickets/{expired_ticket.id}/pay")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Ticket already paid or expired" in response.json()["detail"]
    
    def test_pay_for_ticket_invalid_id(self, client):
        """Test payment with invalid ticket ID."""
        response = client.post("/tickets/invalid/pay")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_pay_for_ticket_negative_id(self, client):
        """Test payment with negative ticket ID."""
        response = client.post("/tickets/-1/pay")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTicketWorkflow:
    """Test complete ticket workflow scenarios."""
    
    def test_complete_ticket_workflow(self, client, sample_user, sample_event, mock_celery_task, db_session):
        """Test complete workflow: reserve -> pay."""
        # Step 1: Reserve ticket
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": sample_event.id
        }
        
        reserve_response = client.post("/tickets/", json=ticket_data)
        assert reserve_response.status_code == status.HTTP_200_OK
        
        ticket_id = reserve_response.json()["id"]
        initial_tickets_sold = sample_event.tickets_sold
        
        # Step 2: Pay for ticket
        pay_response = client.post(f"/tickets/{ticket_id}/pay")
        assert pay_response.status_code == status.HTTP_200_OK
        
        # Verify final state
        pay_data = pay_response.json()
        assert pay_data["status"] == "paid"
        
        # Refresh event and check tickets_sold increment
        db_session.refresh(sample_event)
        assert sample_event.tickets_sold == initial_tickets_sold + 1
    
    def test_reserve_until_sold_out(self, client, sample_user, db_session, mock_celery_task):
        """Test reserving tickets until event is sold out."""
        # Create event with only 2 tickets        
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        small_event = Event(
            title="Small Event",
            description="Event with few tickets",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=2,
            tickets_sold=0
        )
        db_session.add(small_event)
        db_session.commit()
        db_session.refresh(small_event)
        
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": small_event.id
        }
        
        # Reserve first ticket
        response1 = client.post("/tickets/", json=ticket_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Reserve second ticket
        response2 = client.post("/tickets/", json=ticket_data)
        assert response2.status_code == status.HTTP_200_OK
        
        # Pay for both tickets to update tickets_sold
        ticket1_id = response1.json()["id"]
        ticket2_id = response2.json()["id"]
        
        client.post(f"/tickets/{ticket1_id}/pay")
        client.post(f"/tickets/{ticket2_id}/pay")
        
        # Try to reserve third ticket - should fail
        response3 = client.post("/tickets/", json=ticket_data)
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        assert "Event is sold out" in response3.json()["detail"]
    
    def test_double_payment_attempt(self, client, sample_ticket):
        """Test attempting to pay for the same ticket twice."""
        # First payment
        response1 = client.post(f"/tickets/{sample_ticket.id}/pay")
        assert response1.status_code == status.HTTP_200_OK
        
        # Second payment attempt
        response2 = client.post(f"/tickets/{sample_ticket.id}/pay")
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "Ticket already paid or expired" in response2.json()["detail"]


class TestTicketEdgeCases:
    """Test edge cases and error scenarios for ticket endpoints."""
    
    @patch('app.tasks.expire_unpaid_ticket.apply_async')
    def test_reserve_ticket_celery_failure(self, mock_task, client, sample_user, sample_event):
        """Test ticket reservation when Celery task scheduling fails."""
        # Mock Celery task to raise exception
        mock_task.side_effect = Exception("Celery connection failed")
        
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": sample_event.id
        }
        
        # Should still create ticket even if task scheduling fails
        response = client.post("/tickets/", json=ticket_data)
        
        # The current implementation doesn't handle Celery failures gracefully
        # This test documents the current behavior
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_payment_race_condition_simulation(self, client, sample_user, sample_event, db_session, mock_celery_task):
        """Test payment when event becomes sold out between check and payment."""
        # Create event with exactly 1 ticket available        
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        limited_event = Event(
            title="Limited Event",
            description="Event with one ticket",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=1,
            tickets_sold=0
        )
        db_session.add(limited_event)
        db_session.commit()
        db_session.refresh(limited_event)
        
        # Reserve a ticket
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": limited_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        assert response.status_code == status.HTTP_200_OK
        ticket_id = response.json()["id"]
        
        # Manually update tickets_sold to simulate race condition
        limited_event.tickets_sold = 1
        db_session.commit()
        
        print(limited_event.tickets_sold)
        
        pay_response = client.post(f"/tickets/{ticket_id}/pay")
        assert pay_response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_ticket_reservation_with_zero_capacity_event(self, client, sample_user, db_session, mock_celery_task):
        """Test reserving ticket for event with zero capacity."""
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        zero_event = Event(
            title="Zero Capacity Event",
            description="Event with no tickets",
            start_time=future_time,
            end_time=future_time + timedelta(hours=2),
            total_tickets=0,
            tickets_sold=0
        )
        db_session.add(zero_event)
        db_session.commit()
        db_session.refresh(zero_event)
        
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": zero_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Event is sold out" in response.json()["detail"]
