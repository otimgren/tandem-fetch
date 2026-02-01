"""SQLAlchemy models for CGM readings."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence

from tandem_fetch.db.base import Base


class CgmReading(Base):
    """Model for storing CGM reading data."""

    __tablename__ = "cgm_readings"

    id = Column(Integer, Sequence("cgm_readings_id_seq"), primary_key=True, autoincrement=True)
    events_id = Column(Integer, ForeignKey("events.id"), nullable=False, unique=True)
    timestamp = Column(DateTime, nullable=False)
    cgm_reading = Column(Integer, nullable=False)
