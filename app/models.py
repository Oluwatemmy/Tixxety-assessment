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
)
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class TicketStatus(PyEnum):
    RESERVED = "reserved"
    PAID = "paid"
    EXPIRED = "expired"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)

    # Relationships
    tickets = relationship(
        "Ticket",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

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
    venue = Column(String(255), nullable=False)

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

