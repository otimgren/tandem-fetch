"""Integration test fixtures for pipeline testing."""

import json
from pathlib import Path

import pytest

from tandem_fetch.db.raw_events import RawEvent

# Fixtures directory for loading test data
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_pump_events():
    """Load sample pump events from fixture file.

    Returns a list of pump event dictionaries representing various event types.
    """
    with open(FIXTURES_DIR / "api_responses" / "pump_events_sample.json") as f:
        return json.load(f)


@pytest.fixture
def sample_cgm_events():
    """Load sample CGM events from fixture file.

    Returns a list of CGM reading event dictionaries.
    """
    with open(FIXTURES_DIR / "api_responses" / "cgm_events.json") as f:
        return json.load(f)


@pytest.fixture
def sample_basal_events():
    """Load sample basal delivery events from fixture file.

    Returns a list of basal rate change event dictionaries.
    """
    with open(FIXTURES_DIR / "api_responses" / "basal_events.json") as f:
        return json.load(f)


@pytest.fixture
def db_with_raw_events(db_session, sample_pump_events):
    """Create a database session pre-populated with raw events.

    Inserts sample pump events into the raw_events table for testing
    the parsing and extraction stages.

    Returns:
        SQLAlchemy session with raw events already in the database
    """
    for event_data in sample_pump_events:
        raw_event = RawEvent(raw_event_data=event_data)
        db_session.add(raw_event)

    db_session.commit()
    return db_session
