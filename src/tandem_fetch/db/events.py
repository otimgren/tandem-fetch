"""SQLAlchemy models for events."""

from typing import final

from sqlalchemy import JSON, Column, DateTime, Integer, Sequence, Text
from sqlalchemy.sql import func

from tandem_fetch.db.base import Base


@final
class Event(Base):
    """Model for storing parsed event data.

    Attributes:
        id: Unique identifier for the event.
        raw_events_id: Foreign key to raw_events table.
        created: Timestamp when the event was created.
        timestamp: Event timestamp from pump.
        event_id: Tandem event type ID.
        event_name: Human-readable event name.
        event_data: Parsed event-specific data.

    """

    __tablename__ = "events"

    id = Column(Integer, Sequence("events_id_seq"), primary_key=True, autoincrement=True)
    raw_events_id = Column(Integer, nullable=False, unique=True)
    created = Column(DateTime, default=func.now(), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    event_id = Column(Integer, nullable=False, unique=False)
    event_name = Column(Text, nullable=False)
    event_data = Column(JSON)
