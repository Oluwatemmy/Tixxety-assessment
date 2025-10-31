"""
Tests for Celery tasks and background processing.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.tasks import expire_unpaid_ticket
from app.models import Ticket, TicketStatus
from datetime import datetime, timezone


class TestExpireUnpaidTicketTask:
    """Test the expire_unpaid_ticket Celery task."""
    
    def test_expire_reserved_ticket(self, db_session, sample_ticket):
        """Test expiring a reserved ticket."""
        # Verify ticket is initially reserved
        assert sample_ticket.status == TicketStatus.RESERVED
        
        # Execute the task
        result = expire_unpaid_ticket(sample_ticket.id)
        
        # Refresh ticket from database
        db_session.refresh(sample_ticket)
        
        # Verify ticket status changed to expired
        assert sample_ticket.status == TicketStatus.EXPIRED
    
    def test_expire_nonexistent_ticket(self, db_session):
        """Test expiring a ticket that doesn't exist."""
        # This should not raise an exception
        result = expire_unpaid_ticket(999)  # Non-existent ID
        
        # Task should complete without error
        assert result is None
    
    def test_expire_already_paid_ticket(self, db_session, paid_ticket):
        """Test attempting to expire an already paid ticket."""
        original_status = paid_ticket.status
        
        # Execute the task
        result = expire_unpaid_ticket(paid_ticket.id)
        
        # Refresh ticket from database
        db_session.refresh(paid_ticket)
        
        # Status should remain unchanged
        assert paid_ticket.status == original_status
        assert paid_ticket.status == TicketStatus.PAID
    
    def test_expire_already_expired_ticket(self, db_session, expired_ticket):
        """Test attempting to expire an already expired ticket."""
        original_status = expired_ticket.status
        
        # Execute the task
        result = expire_unpaid_ticket(expired_ticket.id)
        
        # Refresh ticket from database
        db_session.refresh(expired_ticket)
        
        # Status should remain unchanged
        assert expired_ticket.status == original_status
        assert expired_ticket.status == TicketStatus.EXPIRED
    
    @patch('app.tasks.SessionLocal')
    def test_database_connection_failure(self, mock_session_class):
        """Test task behavior when database connection fails."""
        # Mock database session to raise exception
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.side_effect = Exception("Database connection failed")
        
        # Task should handle exception gracefully
        try:
            expire_unpaid_ticket(1)
            # Should not raise exception due to finally block
        except Exception:
            pytest.fail("Task should handle database exceptions gracefully")
        
        # Verify session.close() was called in finally block
        mock_session.close.assert_called_once()
    
    @patch('app.tasks.SessionLocal')
    def test_database_commit_failure(self, mock_session_class):
        """Test task behavior when database commit fails."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock ticket query to return a reserved ticket
        mock_ticket = MagicMock()
        mock_ticket.status = TicketStatus.RESERVED
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticket
        
        # Mock commit to raise exception
        mock_session.commit.side_effect = Exception("Commit failed")
        
        # Task should handle commit failure
        try:
            result = expire_unpaid_ticket(1)
        except Exception:
            pytest.fail("Task should handle commit failures gracefully")
        
        # Verify session.close() was called in finally block
        mock_session.close.assert_called_once()
    
    def test_task_with_multiple_tickets_same_user(self, db_session, sample_user, sample_event):
        """Test expiring one ticket when user has multiple tickets."""
        # Create multiple tickets for same user        
        ticket1 = Ticket(
            user_id=sample_user.id,
            event_id=sample_event.id,
            status=TicketStatus.RESERVED,
            created_at=datetime.now(timezone.utc)
        )
        
        ticket2 = Ticket(
            user_id=sample_user.id,
            event_id=sample_event.id,
            status=TicketStatus.RESERVED,
            created_at=datetime.now(timezone.utc)
        )
        
        db_session.add_all([ticket1, ticket2])
        db_session.commit()
        db_session.refresh(ticket1)
        db_session.refresh(ticket2)
        
        # Expire only the first ticket
        result = expire_unpaid_ticket(ticket1.id)
        
        # Refresh both tickets
        db_session.refresh(ticket1)
        db_session.refresh(ticket2)
        
        # Only first ticket should be expired
        assert ticket1.status == TicketStatus.EXPIRED
        assert ticket2.status == TicketStatus.RESERVED


class TestCeleryTaskIntegration:
    """Test Celery task integration and scheduling."""
    
    @patch('app.tasks.expire_unpaid_ticket.apply_async')
    def test_task_scheduling_on_ticket_creation(self, mock_task, client, sample_user, sample_event):
        """Test that task is scheduled when ticket is created."""
        ticket_data = {
            "user_id": sample_user.id,
            "event_id": sample_event.id
        }
        
        response = client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == 200
        
        # Verify task was scheduled
        mock_task.assert_called_once()
        args, kwargs = mock_task.call_args
        
        # Verify task arguments
        ticket_id = response.json()["id"]
        assert args[0] == (ticket_id,)  # Task args should contain ticket ID
        assert kwargs["countdown"] == 120  # Should be scheduled for 2 minutes (120 seconds)
    
    @patch('app.tasks.expire_unpaid_ticket.apply_async')
    def test_task_not_scheduled_on_payment(self, mock_task, client, sample_ticket):
        """Test that no additional task is scheduled when paying for ticket."""
        response = client.post(f"/tickets/{sample_ticket.id}/pay")
        assert response.status_code == 200
        
        # No task should be scheduled during payment
        mock_task.assert_not_called()
    
    def test_task_execution_timing(self, db_session, sample_ticket):
        """Test that task correctly handles timing logic."""
        import time
        
        # Record initial time
        initial_time = datetime.now(timezone.utc)
        
        # Execute task immediately (simulating timer expiration)
        expire_unpaid_ticket(sample_ticket.id)
        
        # Refresh ticket
        db_session.refresh(sample_ticket)
        
        # Ticket should be expired regardless of actual time elapsed
        assert sample_ticket.status == TicketStatus.EXPIRED


class TestTaskErrorHandling:
    """Test error handling in Celery tasks."""
    
    @patch('builtins.print')
    def test_task_logging_success(self, mock_print, db_session, sample_ticket):
        """Test that task logs success message."""
        expire_unpaid_ticket(sample_ticket.id)
        
        # Verify success message was logged
        mock_print.assert_called()
        logged_message = mock_print.call_args[0][0]
        assert f"Ticket id={sample_ticket.id} has expired" in logged_message
    
    @patch('builtins.print')
    def test_task_logging_not_found(self, mock_print, db_session):
        """Test that task logs when ticket is not found."""
        non_existent_id = 999
        expire_unpaid_ticket(non_existent_id)
        
        # Verify not found message was logged
        mock_print.assert_called()
        logged_message = mock_print.call_args[0][0]
        assert f"Ticket id={non_existent_id} not found" in logged_message
    
    @patch('builtins.print')
    def test_task_logging_already_paid(self, mock_print, db_session, paid_ticket):
        """Test that task logs when ticket is already paid."""
        expire_unpaid_ticket(paid_ticket.id)
        
        # Verify already paid message was logged
        mock_print.assert_called()
        logged_message = mock_print.call_args[0][0]
        assert f"Ticket id={paid_ticket.id} not found or already paid/expired" in logged_message
