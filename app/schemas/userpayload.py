from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    location_address: Optional[str] = None
    location_latitude: Optional[float] = Field(None, ge=-90, le=90)
    location_longitude: Optional[float] = Field(None, ge=-180, le=180)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    location_address: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
