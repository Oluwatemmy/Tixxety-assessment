from .database import Base
from enum import Enum as PyEnum
from sqlalchemy import (
    Enum as sqlEnum,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    Float,
)
from datetime import datetime, timezone
from sqlalchemy.orm import relationship, composite


class TicketStatus(PyEnum):
    RESERVED = "reserved"
    PAID = "paid"
    EXPIRED = "expired"
    
class Venue:
    """Value object for composite venue/location mapping, for storing address + coordinates.

    Attributes:
        latitude (float): Latitude in decimal degrees.
        longitude (float): Longitude in decimal degrees.
        address (str): Human-readable address.
    """

    def __init__(self, latitude: float | None, longitude: float | None, address: str | None):
        self.latitude = float(latitude) if latitude is not None else None
        self.longitude = float(longitude) if longitude is not None else None
        self.address = address

    def __composite_values__(self):
        return self.latitude, self.longitude, self.address

    def __repr__(self) -> str:  # pragma: no cover
        return f"Venue(lat={self.latitude:.4f}, lng={self.longitude:.4f}, addr={self.address!r})"

    def distance_to(self, lat, lng):
        from math import radians, sin, cos, sqrt, atan2
        R = 6371  # km
        dlat = radians(lat - self.latitude)
        dlon = radians(lng - self.longitude)
        a = sin(dlat / 2) ** 2 + cos(radians(self.latitude)) * cos(radians(lat)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c  # distance in km

    def __eq__(self, other) -> bool:
        if not isinstance(other, Venue):
            return False
        return (
            self.latitude == other.latitude
            and self.longitude == other.longitude
            and self.address == other.address
        )

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


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


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    tickets_sold = Column(Integer, nullable=False, default=0)
    
    address = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    venue = composite(Venue, latitude, longitude, address)

    # Relationships
    tickets = relationship(
        "Ticket",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("tickets_sold >= 0", name="ck_events_tickets_sold_non_negative"),
        CheckConstraint(
            "tickets_sold <= total_tickets",
            name="ck_events_tickets_sold_not_exceed_total",
        ),
        Index("ix_events_latitude", "latitude"),
        Index("ix_events_longitude", "longitude"),
        Index("ix_events_start_time", "start_time"),
    )

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return f"<Event id={self.id} title={self.title!r} venue={self.venue!r}>"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        sqlEnum(TicketStatus, name="ticket_status", native_enum=False),
        nullable=False,
        default=TicketStatus.RESERVED,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="tickets")
    event = relationship("Event", back_populates="tickets")

    def __repr__(self) -> str:  # pragma: no cover - repr helper
        return (
            f"<Ticket id={self.id} user_id={self.user_id} "
            f"event_id={self.event_id} status={self.status.value}>"
        )


