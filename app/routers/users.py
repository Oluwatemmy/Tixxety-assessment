from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models import User, Event, Ticket
from app.schemas.userpayload import UserCreate
from math import radians, sin, cos, sqrt, atan2
from app.schemas.event_payload import EventResponse
from app.schemas.ticket_payload import TicketResponse
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Return distance in km between two coordinates using Haversine."""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Create a new user
@router.post("/")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        location_address=payload.location_address,
        location_latitude=payload.location_latitude,
        location_longitude=payload.location_longitude,
    )
    db.add(user)
    db.commit()
    return {
        "message": "User created successfully",
        "user_id": user.id,
        "user_name": user.name,
        "user_email": user.email,
    }


@router.get("/for-you/", response_model=list[EventResponse])
def get_nearby_events(
    user_id: int,
    max_distance_km: float = 30,  # default radius 30 km
    db: Session = Depends(get_db)
):
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.location_latitude or not user.location_longitude:
        raise HTTPException(status_code=404, detail="User location not set")

    # Fetch only future events
    now = datetime.now(timezone.utc)
    events = (
        db.query(Event)
        .filter(Event.end_time > now)
        .filter(Event.latitude.isnot(None))
        .filter(Event.longitude.isnot(None))
        .all()
    )

    # Filter nearby events
    nearby_events = []
    for event in events:
        distance = calculate_distance(
            user.location_latitude,
            user.location_longitude,
            event.latitude,
            event.longitude,
        )
        if distance <= max_distance_km:
            nearby_events.append(( event, distance))
            
    # Sort by distance
    nearby_events.sort(key=lambda x: x[1])

    return [event for event, _ in nearby_events]


@router.get("/{user_id}/tickets", response_model=list[TicketResponse])
def get_user_tickets(user_id: int, db: Session = Depends(get_db)):
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch user's tickets
    tickets = db.query(Ticket).filter(Ticket.user_id == user.id).all()
    return tickets