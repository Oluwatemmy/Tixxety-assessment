from app.database import Base
from .event_models import Venue
from sqlalchemy.orm import relationship, composite
from sqlalchemy import Column, Integer, String, UniqueConstraint, Float


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # User's current location as a composite (latitude, longitude, address)
    location_address = Column(String(255), nullable=True)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)

    # Composite mapped attribute for convenience
    location = composite(Venue, location_latitude, location_longitude, location_address)

    # Relationships
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete-orphan",)

    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<User id={self.id} name={self.name!r} email={self.email!r}>"

