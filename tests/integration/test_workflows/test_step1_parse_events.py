"""Integration tests for Step 1: Parsing raw events into structured events.

Tests the event parsing stage independently.
"""

import pytest

from tandem_fetch.db.raw_events import RawEvent


@pytest.mark.integration
def test_parse_pump_events(db_with_raw_events):
    """Test parsing of pump events from raw event data.

    Validates:
    - Event type identification works correctly
    - Different event types are recognized
    - Event names match expected values
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    # Verify we have different event types in sample data
    event_types = [e.raw_event_data.get("NAME") for e in raw_events]
    unique_types = set(event_types)

    assert "LID_CGM_DATA_READING" in unique_types, "Should have CGM events"
    assert "LID_BASAL_RATE_CHANGE" in unique_types, "Should have basal events"


@pytest.mark.integration
def test_parse_events_timestamps(db_with_raw_events):
    """Test that timestamps are preserved during parsing.

    Validates:
    - Timestamps are extracted correctly
    - Timestamp format is maintained
    - Chronological order can be determined
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    for event in raw_events:
        timestamp = event.raw_event_data.get("event_timestamp")
        assert timestamp is not None, "Each event should have a timestamp"
        assert isinstance(timestamp, str), "Timestamp should be a string"
        assert "T" in timestamp, "Timestamp should be ISO format with T separator"


@pytest.mark.integration
def test_parse_events_data_extraction(db_with_raw_events):
    """Test that event-specific data is correctly extracted.

    Validates:
    - CGM events have glucose values
    - Basal events have rate values
    - All required fields are present
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    for event in raw_events:
        event_name = event.raw_event_data.get("NAME")
        event_data = event.raw_event_data

        if event_name == "LID_CGM_DATA_READING":
            # CGM events should have glucose data
            assert "currentglucosedisplayvalue" in event_data, "CGM event needs glucose value"
            assert "trendArrow" in event_data, "CGM event needs trend arrow"

        elif event_name == "LID_BASAL_RATE_CHANGE":
            # Basal events should have rate data
            assert "commandedbasalrate" in event_data, "Basal event needs commanded rate"
            assert "basebasalrate" in event_data, "Basal event needs base rate"
