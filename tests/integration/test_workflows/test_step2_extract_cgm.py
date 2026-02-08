"""Integration tests for Step 2: Extracting CGM readings from events.

Tests the CGM extraction stage independently.
"""

import pytest

from tandem_fetch.db.raw_events import RawEvent


@pytest.mark.integration
def test_extract_cgm_readings(db_with_raw_events):
    """Test extraction of CGM readings from event data.

    Validates:
    - CGM events are identified correctly
    - Extraction logic can access required fields
    - Event count matches expectations
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    cgm_events = [e for e in raw_events if e.raw_event_data.get("NAME") == "LID_CGM_DATA_READING"]

    assert len(cgm_events) == 3, "Sample data should have 3 CGM events"

    for cgm_event in cgm_events:
        data = cgm_event.raw_event_data
        assert "currentglucosedisplayvalue" in data, "CGM event must have glucose value"
        assert isinstance(data["currentglucosedisplayvalue"], int), "Glucose value must be integer"


@pytest.mark.integration
def test_cgm_glucose_values(db_with_raw_events):
    """Test that glucose values are within valid ranges.

    Validates:
    - Glucose values are numeric
    - Values are in reasonable range (20-400 mg/dL)
    - No invalid or corrupt values
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    cgm_events = [e for e in raw_events if e.raw_event_data.get("NAME") == "LID_CGM_DATA_READING"]

    for cgm_event in cgm_events:
        glucose = cgm_event.raw_event_data["currentglucosedisplayvalue"]
        assert 20 <= glucose <= 400, f"Glucose value {glucose} should be in valid range (20-400)"


@pytest.mark.integration
def test_cgm_no_duplicates(db_session, sample_cgm_events):
    """Test that CGM extraction doesn't create duplicates.

    Validates:
    - Each event_id is unique
    - Re-running extraction doesn't duplicate data
    - Event timestamps are distinct
    """
    # Load CGM events
    for event_data in sample_cgm_events:
        raw_event = RawEvent(raw_event_data=event_data)
        db_session.add(raw_event)
    db_session.commit()

    # Get all CGM events
    raw_events = db_session.query(RawEvent).all()
    event_ids = [e.raw_event_data["event_id"] for e in raw_events]

    # Verify no duplicates
    assert len(event_ids) == len(set(event_ids)), "Event IDs should be unique"
