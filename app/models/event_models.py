from app.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    CheckConstraint,
    Index,
    Float,
)
from math import radians, sin, cos, sqrt, atan2
from sqlalchemy.orm import relationship, composite


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
