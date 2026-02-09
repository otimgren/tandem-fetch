"""Root conftest.py for shared test fixtures across all tests."""

import json
from pathlib import Path

import pytest
from prefect.testing.utilities import prefect_test_harness
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tandem_fetch.db.base import Base

# Fixtures directory for loading test data
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory DuckDB engine for each test.

    Provides complete isolation - each test gets a fresh database.
    Automatically creates all tables and cleans up after test completion.
    """
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine):
    """Create a database session for each test.

    Provides a SQLAlchemy session connected to the in-memory test database.
    Automatically rolls back changes and closes the session after the test.
    """
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def tandem_api_mock(requests_mock):
    """Mock Tandem Source API with common responses.

    Uses requests-mock to intercept HTTP requests and return fixture data.
    Load fixture files from tests/fixtures/api_responses/ directory.
    """
    # Load authentication success response
    auth_fixture_path = FIXTURES_DIR / "api_responses" / "auth_success.json"
    if auth_fixture_path.exists():
        with open(auth_fixture_path) as f:
            auth_data = json.load(f)
            requests_mock.post("https://api.tandemdiabetes.com/auth", json=auth_data)

    return requests_mock


@pytest.fixture(autouse=True, scope="session")
def prefect_test_mode():
    """Enable Prefect test harness for all tests.

    Provides deterministic flow execution without actual scheduling.
    Runs automatically for all tests (autouse=True).
    """
    with prefect_test_harness():
        yield
