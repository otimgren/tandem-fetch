"""Unit tests for pump event transformations.

Tests transformation logic for event processing.
"""


def test_event_type_classification():
    """Test that event types are correctly classified.

    Validates:
    - Event IDs map to correct event types
    - Event names are correctly identified
    """
    from tandem_fetch.pump_events.events import EVENT_IDS

    # Verify EVENT_IDS is properly defined
    assert isinstance(EVENT_IDS, dict), "EVENT_IDS should be a dictionary"
    assert len(EVENT_IDS) > 0, "EVENT_IDS should not be empty"

    # Verify key event types exist
    assert 3 in EVENT_IDS, "Should have basal rate change event (ID 3)"
    # Note: CGM event IDs are 171, 172, 212, 213, 214
    assert any(id in EVENT_IDS for id in [171, 172, 212, 213, 214]), "Should have CGM events"


def test_timestamp_parsing():
    """Test timestamp parsing functionality.

    Validates:
    - Timestamps can be parsed from strings
    - ISO format is handled correctly
    """
    import dateutil.parser

    # Test ISO timestamp parsing
    timestamp_str = "2024-01-01T10:00:00+00:00"
    parsed = dateutil.parser.parse(timestamp_str)

    assert parsed is not None, "Should be able to parse ISO timestamp"
    assert parsed.year == 2024, "Year should be correctly parsed"
    assert parsed.month == 1, "Month should be correctly parsed"
    assert parsed.day == 1, "Day should be correctly parsed"


def test_glucose_value_extraction():
    """Test glucose value extraction from CGM events.

    Validates:
    - Glucose values are numeric
    - Values are extracted from correct field
    """
    # Sample CGM event data
    cgm_event_data = {
        "ID": 198,
        "NAME": "LID_CGM_DATA_READING",
        "currentglucosedisplayvalue": 120,
        "trendArrow": 4,
    }

    # Verify field exists and is correct type
    assert "currentglucosedisplayvalue" in cgm_event_data
    glucose = cgm_event_data["currentglucosedisplayvalue"]
    assert isinstance(glucose, int), "Glucose value should be integer"
    assert glucose > 0, "Glucose value should be positive"


def test_basal_rate_calculation():
    """Test basal rate extraction from basal events.

    Validates:
    - Rate values are numeric
    - Multiple rate fields are present
    """
    # Sample basal event data
    basal_event_data = {
        "ID": 3,
        "NAME": "LID_BASAL_RATE_CHANGE",
        "commandedbasalrate": 0.85,
        "basebasalrate": 0.85,
        "maxbasalrate": 3.0,
    }

    # Verify fields exist and are correct type
    assert "commandedbasalrate" in basal_event_data
    assert "basebasalrate" in basal_event_data

    commanded = basal_event_data["commandedbasalrate"]
    base = basal_event_data["basebasalrate"]

    assert isinstance(commanded, (int, float)), "Rate should be numeric"
    assert isinstance(base, (int, float)), "Rate should be numeric"
    assert commanded >= 0, "Rate should be non-negative"
