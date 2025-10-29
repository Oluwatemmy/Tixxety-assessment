from pydantic import BaseModel
from datetime import datetime

class EventCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    total_tickets: int
    venue: str

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    venue: str
    total_tickets: int
    tickets_sold: int

    class Config:
        from_attributes = True
