from pydantic import BaseModel
from datetime import datetime

class TicketCreate(BaseModel):
    user_id: int
    event_id: int

class TicketResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
