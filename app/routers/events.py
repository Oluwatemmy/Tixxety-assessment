from app.models import Event
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.schemas.event_payload import EventCreate, EventResponse

router = APIRouter()

@router.post("/")
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        total_tickets=payload.total_tickets,
        address=payload.venue.address,
        latitude=payload.venue.latitude,
        longitude=payload.venue.longitude,
    )
    db.add(event)
    db.commit()
    return {
        "message": "Event created successfully",
        "event_id": event.id,
        "event_title": event.title,
        "total_tickets": event.total_tickets,
    }

@router.get("/", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return events
