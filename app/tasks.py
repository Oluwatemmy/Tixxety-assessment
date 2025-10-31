from app.database import SessionLocal
from .celery_worker import celery_app
from app.models import Ticket, TicketStatus

@celery_app.task
def expire_unpaid_ticket(ticket_id: int, db_session=None) -> None:
    external_session = db_session is not None
    db = db_session or SessionLocal()

    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket and ticket.status == TicketStatus.RESERVED:
            ticket.status = TicketStatus.EXPIRED
            db.commit()
            print(f"Ticket id={ticket.id} has expired due to non-payment.")
        else:
            print(f"Ticket id={ticket_id} not found or already paid/expired.")
    except Exception as e:
        if not external_session:
            db.rollback()
        print(f"Error expiring ticket id={ticket_id}: {e}")
    finally:
        if not external_session:
            db.close()
