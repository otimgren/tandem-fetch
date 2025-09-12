"""SQLAlchemy models for raw events."""

from typing import final

from sqlalchemy import JSON, Column, DateTime, Integer, Text
from sqlalchemy.sql import func

from tandem_fetch.db.base import Base


@final
class Event(Base):
    """Model for storing raw event data.

    Attributes:
        id: Unique identifier for the raw event.
        created: Timestamp when the event was created.
        raw_event_data: JSON blob containing the raw event data.

    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_events_id = Column(Integer, nullable=False, unique=True)
    created = Column(DateTime, default=func.now(), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    event_id = Column(Integer, nullable=False, unique=False)
    event_name = Column(Text, nullable=False)
    event_data = Column(JSON)
