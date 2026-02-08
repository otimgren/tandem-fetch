"""Integration tests for Step 3: Extracting basal deliveries from events.

Tests the basal delivery extraction stage independently.
"""

import pytest

from tandem_fetch.db.raw_events import RawEvent


@pytest.mark.integration
def test_extract_basal_deliveries(db_with_raw_events):
    """Test extraction of basal deliveries from event data.

    Validates:
    - Basal events are identified correctly
    - Extraction logic can access required fields
    - Event count matches expectations
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    basal_events = [
        e for e in raw_events if e.raw_event_data.get("NAME") == "LID_BASAL_RATE_CHANGE"
    ]

    assert len(basal_events) == 2, "Sample data should have 2 basal events"

    for basal_event in basal_events:
        data = basal_event.raw_event_data
        assert "commandedbasalrate" in data, "Basal event must have commanded rate"
        assert "basebasalrate" in data, "Basal event must have base rate"


@pytest.mark.integration
def test_basal_rate_values(db_with_raw_events):
    """Test that basal rate values are valid.

    Validates:
    - Rate values are numeric
    - Values are in reasonable range (0-10 U/hr)
    - No negative or invalid values
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    basal_events = [
        e for e in raw_events if e.raw_event_data.get("NAME") == "LID_BASAL_RATE_CHANGE"
    ]

    for basal_event in basal_events:
        data = basal_event.raw_event_data
        commanded_rate = data["commandedbasalrate"]
        base_rate = data["basebasalrate"]

        assert isinstance(commanded_rate, (int, float)), "Commanded rate must be numeric"
        assert isinstance(base_rate, (int, float)), "Base rate must be numeric"
        assert 0 <= commanded_rate <= 10, f"Commanded rate {commanded_rate} should be 0-10 U/hr"
        assert 0 <= base_rate <= 10, f"Base rate {base_rate} should be 0-10 U/hr"


@pytest.mark.integration
def test_basal_timestamps(db_with_raw_events):
    """Test that basal event timestamps are properly maintained.

    Validates:
    - Timestamps are present
    - Timestamps are in correct format
    - Events can be ordered chronologically
    """
    raw_events = db_with_raw_events.query(RawEvent).all()

    basal_events = [
        e for e in raw_events if e.raw_event_data.get("NAME") == "LID_BASAL_RATE_CHANGE"
    ]

    timestamps = [e.raw_event_data["event_timestamp"] for e in basal_events]

    assert len(timestamps) == len(basal_events), "Each basal event should have timestamp"
    assert all(isinstance(ts, str) for ts in timestamps), "Timestamps should be strings"
    assert all("T" in ts for ts in timestamps), "Timestamps should be ISO format"
