from sqlalchemy import Column, DateTime, ForeignKey, Integer

from tandem_fetch.db.base import Base


class BasalDelivery(Base):
    __tablename__ = "basal_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    events_id = Column(
        Integer, ForeignKey("events.id"), nullable=False, unique=True
    )
    timestamp = Column(DateTime, nullable=False)
    profile_basal_rate = Column(Integer)
    algorithm_basal_rate = Column(Integer)
    temp_basal_rate = Column(Integer)

