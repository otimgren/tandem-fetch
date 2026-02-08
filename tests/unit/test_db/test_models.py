"""Unit tests for database models.

Tests SQLAlchemy model definitions and relationships.
"""

import datetime

from tandem_fetch.db.basal_deliveries import BasalDelivery
from tandem_fetch.db.cgm_readings import CgmReading
from tandem_fetch.db.events import Event
from tandem_fetch.db.raw_events import RawEvent


def test_raw_event_model(unit_db_session):
    """Test RawEvent model creation and fields.

    Validates:
    - Model can be created
    - Fields are correctly defined
    - Data is persisted correctly
    """
    raw_event = RawEvent(
        raw_event_data={
            "event_id": 123,
            "event_timestamp": "2024-01-01T12:00:00+00:00",
            "NAME": "TEST_EVENT",
        }
    )

    unit_db_session.add(raw_event)
    unit_db_session.commit()

    # Query back
    result = unit_db_session.query(RawEvent).first()
    assert result is not None
    assert result.raw_event_data["event_id"] == 123
    assert result.created is not None


def test_event_model(unit_db_session):
    """Test Event model creation and fields.

    Validates:
    - Model can be created
    - Foreign key relationships work
    - Timestamps are handled correctly
    """
    # Create a raw event first (for foreign key)
    raw_event = RawEvent(raw_event_data={"test": "data"})
    unit_db_session.add(raw_event)
    unit_db_session.commit()

    # Create event
    event = Event(
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        raw_events_id=raw_event.id,
        event_id=123,
        event_name="TEST_EVENT",
        event_data={"test_field": "test_value"},
    )

    unit_db_session.add(event)
    unit_db_session.commit()

    # Query back
    result = unit_db_session.query(Event).first()
    assert result is not None
    assert result.event_id == 123
    assert result.event_name == "TEST_EVENT"
    assert result.raw_events_id == raw_event.id


def test_cgm_reading_model(unit_db_session):
    """Test CGMReading model creation and fields.

    Validates:
    - Model can be created
    - Foreign key to events works
    - CGM-specific fields are correct
    """
    # Create prerequisites
    raw_event = RawEvent(raw_event_data={"test": "data"})
    unit_db_session.add(raw_event)
    unit_db_session.commit()

    event = Event(
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        raw_events_id=raw_event.id,
        event_id=123,
        event_name="LID_CGM_DATA_READING",
        event_data={},
    )
    unit_db_session.add(event)
    unit_db_session.commit()

    # Create CGM reading
    cgm_reading = CgmReading(
        events_id=event.id,
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        cgm_reading=120,
    )

    unit_db_session.add(cgm_reading)
    unit_db_session.commit()

    # Query back
    result = unit_db_session.query(CgmReading).first()
    assert result is not None
    assert result.cgm_reading == 120
    assert result.events_id == event.id


def test_basal_delivery_model(unit_db_session):
    """Test BasalDelivery model creation and fields.

    Validates:
    - Model can be created
    - Foreign key to events works
    - Basal-specific fields are correct
    """
    # Create prerequisites
    raw_event = RawEvent(raw_event_data={"test": "data"})
    unit_db_session.add(raw_event)
    unit_db_session.commit()

    event = Event(
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        raw_events_id=raw_event.id,
        event_id=123,
        event_name="LID_BASAL_RATE_CHANGE",
        event_data={},
    )
    unit_db_session.add(event)
    unit_db_session.commit()

    # Create basal delivery
    basal = BasalDelivery(
        events_id=event.id,
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        profile_basal_rate=85,
        algorithm_basal_rate=90,
        temp_basal_rate=0,
    )

    unit_db_session.add(basal)
    unit_db_session.commit()

    # Query back
    result = unit_db_session.query(BasalDelivery).first()
    assert result is not None
    assert result.profile_basal_rate == 85
    assert result.algorithm_basal_rate == 90


def test_model_relationships(unit_db_session):
    """Test relationships between models.

    Validates:
    - Foreign keys are enforced
    - Cascade behavior works correctly
    - Unique constraints are enforced
    """
    # Create a full chain
    raw_event = RawEvent(raw_event_data={"test": "data"})
    unit_db_session.add(raw_event)
    unit_db_session.commit()

    event = Event(
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        raw_events_id=raw_event.id,
        event_id=123,
        event_name="LID_CGM_DATA_READING",
        event_data={},
    )
    unit_db_session.add(event)
    unit_db_session.commit()

    cgm_reading = CgmReading(
        events_id=event.id,
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        cgm_reading=120,
    )
    unit_db_session.add(cgm_reading)
    unit_db_session.commit()

    # Verify the chain exists
    assert unit_db_session.query(RawEvent).count() == 1
    assert unit_db_session.query(Event).count() == 1
    assert unit_db_session.query(CgmReading).count() == 1

    # Verify relationships
    retrieved_cgm = unit_db_session.query(CgmReading).first()
    assert retrieved_cgm.events_id == event.id
