from sqlalchemy import Column, DateTime, ForeignKey, Integer

from tandem_fetch.db.base import Base


class CgmReading(Base):
    __tablename__ = "cgm_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    events_id = Column(
        Integer, ForeignKey("events.id"), nullable=False, unique=True
    )
    timestamp = Column(DateTime, nullable=False)
    cgm_reading = Column(Integer, nullable=False)
