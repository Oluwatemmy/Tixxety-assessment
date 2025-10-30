from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VenueBase(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

class EventCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    total_tickets: int
    venue: VenueBase

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    total_tickets: int
    tickets_sold: int
    venue: VenueBase

    class Config:
        from_attributes = True
