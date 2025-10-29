from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ticket, User, Event, TicketStatus
from app.schemas.ticket_payload import TicketCreate, TicketResponse
from app.models import TicketStatus
from app.tasks import expire_unpaid_ticket

router = APIRouter()

@router.post("/", response_model=TicketResponse)
def reserve_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if event exists
    event = db.query(Event).filter(Event.id == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event not found")

    # Check if event is sold out
    if event.tickets_sold >= event.total_tickets:
        raise HTTPException(status_code=400, detail="Event is sold out")

    # Create ticket with reserved status
    ticket = Ticket(
        user_id=payload.user_id,
        event_id=payload.event_id,
        status=TicketStatus.RESERVED
    )
    db.add(ticket)

    # Update event tickets_sold
    event.tickets_sold += 1

    db.commit()
    db.refresh(ticket)
    
    # Schedule expiration after 2 minutes
    expire_unpaid_ticket.apply_async((ticket.id,), countdown=120)

    return ticket


@router.post("/{ticket_id}/pay", response_model=TicketResponse)
def pay_for_ticket(ticket_id: int, db: Session = Depends(get_db)):
    # Find ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Ensure it's still reserved
    if ticket.status != TicketStatus.RESERVED:
        raise HTTPException(status_code=400, detail="Ticket already paid or expired")

    # Update status
    ticket.status = TicketStatus.PAID
    db.commit()
    db.refresh(ticket)

    return ticket
