from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TicketCreate(BaseModel):
    user_id: int
    event_id: int

class TicketResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
