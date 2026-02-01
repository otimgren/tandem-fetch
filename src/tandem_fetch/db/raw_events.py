"""SQLAlchemy models for raw events."""

from typing import final, override

from sqlalchemy import JSON, Column, DateTime, Integer, Sequence
from sqlalchemy.sql import func

from tandem_fetch.db.base import Base


@final
class RawEvent(Base):
    """Model for storing raw event data.

    Attributes:
        id: Unique identifier for the raw event.
        created: Timestamp when the event was created.
        raw_event_data: JSON blob containing the raw event data.

    """

    __tablename__ = "raw_events"

    id = Column(
        Integer, Sequence("raw_events_id_seq"), primary_key=True, autoincrement=True
    )
    created = Column(DateTime, default=func.now(), nullable=False)
    raw_event_data = Column(JSON, nullable=False)

    @override
    def __repr__(self) -> str:
        """Return string representation of the RawEvents instance."""
        return f"<RawEvents(id={self.id}, created={self.created})>"
