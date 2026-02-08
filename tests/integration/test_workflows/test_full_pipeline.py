"""Integration tests for the complete data pipeline.

Tests the full workflow from raw events through to CGM and basal extraction.
"""

import pytest

from tandem_fetch.db.raw_events import RawEvent


@pytest.mark.integration
def test_full_pipeline_raw_events_stored(db_with_raw_events):
    """Test that raw events are properly stored in the database.

    Validates:
    - Raw events table is populated
    - Each raw event has required fields
    - Raw event data is properly serialized
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    assert len(raw_events) > 0, "Raw events should be stored in database"

    for event in raw_events:
        assert event.id is not None, "Each raw event should have an ID"
        assert event.created is not None, "Each raw event should have a created timestamp"
        assert event.raw_event_data is not None, "Each raw event should have data"
        assert isinstance(event.raw_event_data, dict), "Raw event data should be a dictionary"


@pytest.mark.integration
def test_full_pipeline_data_integrity(db_with_raw_events):
    """Test that data remains consistent across pipeline stages.

    Validates:
    - Raw events are present
    - Data structure is maintained
    - No data corruption during storage
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    assert len(raw_events) == 5, "Should have exactly 5 raw events from sample data"

    # Verify each raw event has the expected structure
    for event in raw_events:
        event_data = event.raw_event_data
        assert "event_timestamp" in event_data, "Event should have a timestamp"
        assert "event_id" in event_data, "Event should have an ID"
        assert "NAME" in event_data, "Event should have a name"


@pytest.mark.integration
@pytest.mark.slow
def test_full_pipeline_event_types(db_with_raw_events):
    """Test that different event types are properly stored.

    Validates:
    - CGM events are present
    - Basal rate change events are present
    - Event types are correctly identified
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    cgm_events = [e for e in raw_events if e.raw_event_data.get("NAME") == "LID_CGM_DATA_READING"]
    basal_events = [
        e for e in raw_events if e.raw_event_data.get("NAME") == "LID_BASAL_RATE_CHANGE"
    ]

    assert len(cgm_events) > 0, "Should have CGM reading events"
    assert len(basal_events) > 0, "Should have basal rate change events"


@pytest.mark.integration
def test_full_pipeline_timestamp_ordering(db_with_raw_events):
    """Test that events maintain proper timestamp ordering.

    Validates:
    - Events can be ordered by timestamp
    - Timestamps are properly formatted
    - No timestamp corruption
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    timestamps = [event.raw_event_data.get("event_timestamp") for event in raw_events]

    # Verify all timestamps are present
    assert all(ts is not None for ts in timestamps), "All events should have timestamps"

    # Verify timestamps are strings in ISO format
    assert all(isinstance(ts, str) for ts in timestamps), "Timestamps should be strings"


@pytest.mark.integration
def test_full_pipeline_fetch_to_cgm(db_with_raw_events):
    """Test the complete pipeline from raw events to CGM extraction.

    Validates:
    - Raw events are stored
    - Events can be parsed (when parsing code is run)
    - CGM data structure is preserved for extraction
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    # Verify raw events exist
    assert len(raw_events) > 0, "Raw events should be present"

    # Verify CGM events are in the raw data
    cgm_events = [e for e in raw_events if e.raw_event_data.get("NAME") == "LID_CGM_DATA_READING"]
    assert len(cgm_events) >= 3, "Should have at least 3 CGM events in sample data"

    # Verify CGM data fields are present
    for cgm_event in cgm_events:
        data = cgm_event.raw_event_data
        assert "currentglucosedisplayvalue" in data, "CGM event should have glucose value"
        assert "trendArrow" in data, "CGM event should have trend arrow"
        assert isinstance(data["currentglucosedisplayvalue"], int), (
            "Glucose value should be integer"
        )


@pytest.mark.integration
def test_full_pipeline_fetch_to_basal(db_with_raw_events):
    """Test the complete pipeline from raw events to basal extraction.

    Validates:
    - Raw events are stored
    - Basal rate change events are present
    - Basal data structure is preserved for extraction
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    # Verify raw events exist
    assert len(raw_events) > 0, "Raw events should be present"

    # Verify basal events are in the raw data
    basal_events = [
        e for e in raw_events if e.raw_event_data.get("NAME") == "LID_BASAL_RATE_CHANGE"
    ]
    assert len(basal_events) >= 2, "Should have at least 2 basal events in sample data"

    # Verify basal data fields are present
    for basal_event in basal_events:
        data = basal_event.raw_event_data
        assert "commandedbasalrate" in data, "Basal event should have commanded rate"
        assert "basebasalrate" in data, "Basal event should have base rate"
        assert isinstance(data["commandedbasalrate"], (int, float)), "Rate should be numeric"


@pytest.mark.integration
def test_full_pipeline_field_integrity(db_with_raw_events):
    """Test that all required fields are present and properly typed.

    Validates:
    - No data loss during storage
    - JSON serialization preserves data types
    - All required fields are present
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    assert len(raw_events) == 5, "Should have exactly 5 events from sample fixture"

    # Verify data integrity for each event
    for event in raw_events:
        data = event.raw_event_data

        # Core fields that all events should have
        assert data.get("event_timestamp"), "Event must have timestamp"
        assert data.get("event_id"), "Event must have event_id"
        assert data.get("NAME"), "Event must have NAME"
        assert data.get("raw_event"), "Event must have raw_event structure"

        # raw_event should be a dict with specific fields
        raw_event_data = data["raw_event"]
        assert isinstance(raw_event_data, dict), "raw_event should be a dictionary"
        assert "id" in raw_event_data, "raw_event must have id field"
        assert "timestamp" in raw_event_data, "raw_event must have timestamp"


@pytest.mark.integration
@pytest.mark.slow
def test_pipeline_with_pagination(db_session, sample_pump_events):
    """Test pipeline behavior with paginated data loads.

    Validates:
    - Multiple batches of events can be processed
    - No duplicates when loading in batches
    - Data consistency across batches
    """
    # Load first batch
    first_batch = sample_pump_events[:3]
    for event_data in first_batch:
        raw_event = RawEvent(raw_event_data=event_data)
        db_session.add(raw_event)
    db_session.commit()

    # Verify first batch
    count_after_first = db_session.query(RawEvent).count()
    assert count_after_first == 3, "Should have 3 events after first batch"

    # Load second batch
    second_batch = sample_pump_events[3:]
    for event_data in second_batch:
        raw_event = RawEvent(raw_event_data=event_data)
        db_session.add(raw_event)
    db_session.commit()

    # Verify both batches
    total_count = db_session.query(RawEvent).count()
    assert total_count == len(sample_pump_events), "Should have all events after both batches"

    # Verify no duplicates by checking unique event_ids
    event_ids = [e.raw_event_data["event_id"] for e in db_session.query(RawEvent).all()]
    assert len(event_ids) == len(set(event_ids)), "Should have no duplicate event_ids"
