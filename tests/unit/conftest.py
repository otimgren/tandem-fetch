"""Unit test fixtures for isolated component testing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tandem_fetch.db.base import Base


@pytest.fixture(scope="function")
def unit_db_engine():
    """Create an in-memory database engine for unit tests.

    Provides a fresh, isolated database for each unit test.
    """
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def unit_db_session(unit_db_engine):
    """Create a database session for unit tests."""
    SessionLocal = sessionmaker(bind=unit_db_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
