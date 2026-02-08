"""Unit tests for validating mock API response fixtures.

Ensures that mock fixtures match the documented API response schemas.
"""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "api_responses"


@pytest.fixture
def auth_response_fixture():
    """Load authentication response fixture."""
    with open(FIXTURES_DIR / "auth_success.json") as f:
        return json.load(f)


@pytest.fixture
def pump_events_fixture():
    """Load pump events response fixture."""
    with open(FIXTURES_DIR / "pump_events_sample.json") as f:
        return json.load(f)


@pytest.fixture
def cgm_events_fixture():
    """Load CGM events response fixture."""
    with open(FIXTURES_DIR / "cgm_events.json") as f:
        return json.load(f)


@pytest.fixture
def basal_events_fixture():
    """Load basal events response fixture."""
    with open(FIXTURES_DIR / "basal_events.json") as f:
        return json.load(f)


def test_pump_events_schema_compliance(pump_events_fixture):
    """Test that pump events fixture complies with PumpEventResponse schema."""
    assert isinstance(pump_events_fixture, list), "Pump events should be an array"
    assert len(pump_events_fixture) > 0, "Should have at least one pump event"

    for event in pump_events_fixture:
        # Required fields
        assert "ID" in event and isinstance(event["ID"], int)
        assert "NAME" in event and isinstance(event["NAME"], str)
        assert "raw_event" in event and isinstance(event["raw_event"], dict)
        assert "event_timestamp" in event and isinstance(event["event_timestamp"], str)
        assert "event_id" in event and isinstance(event["event_id"], int)

        # raw_event structure
        raw = event["raw_event"]
        assert "id" in raw and isinstance(raw["id"], int)
        assert "timestamp" in raw and isinstance(raw["timestamp"], str)


def test_cgm_events_schema_compliance(cgm_events_fixture):
    """Test that CGM events fixture complies with CGMEventResponse schema."""
    for event in cgm_events_fixture:
        assert event["NAME"] == "LID_CGM_DATA_READING"
        assert "currentglucosedisplayvalue" in event
        glucose = event["currentglucosedisplayvalue"]
        assert 20 <= glucose <= 400


def test_basal_events_schema_compliance(basal_events_fixture):
    """Test that basal events fixture complies with BasalEventResponse schema."""
    for event in basal_events_fixture:
        assert event["NAME"] == "LID_BASAL_RATE_CHANGE"
        assert "commandedbasalrate" in event
        assert 0 <= event["commandedbasalrate"] <= 10


def test_auth_response_schema_compliance(auth_response_fixture):
    """Test that auth response fixture complies with AuthenticationResponse schema."""
    assert "access_token" in auth_response_fixture
    assert "token_type" in auth_response_fixture
    assert auth_response_fixture["token_type"] == "Bearer"


def test_fixture_data_types(pump_events_fixture):
    """Test that all fixture files use correct data types."""
    for event in pump_events_fixture:
        assert isinstance(event["ID"], int)
        assert isinstance(event["event_timestamp"], str)
        assert "T" in event["event_timestamp"]
