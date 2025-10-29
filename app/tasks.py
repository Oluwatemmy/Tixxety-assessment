from datetime import datetime
from app.database import SessionLocal
from app.models import Ticket, TicketStatus
from .celery_worker import celery_app

@celery_app.task
def expire_unpaid_ticket(ticket_id: int):
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket and ticket.status == TicketStatus.RESERVED:
            ticket.status = TicketStatus.EXPIRED
            db.commit()
            print(f"Ticket id={ticket.id} has expired due to non-payment.")
        else:
            print(f"Ticket id={ticket_id} not found or already paid/expired.")
    finally:
        db.close()
