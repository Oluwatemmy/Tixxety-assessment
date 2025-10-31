from app.database import Base
from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as sqlEnum, Column, Integer, DateTime, ForeignKey

class TicketStatus(PyEnum):
    RESERVED = "reserved"
    PAID = "paid"
    EXPIRED = "expired"
    

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
