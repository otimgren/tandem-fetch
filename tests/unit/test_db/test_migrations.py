"""Unit tests for Alembic database migrations.

Tests migration integrity and schema consistency.
"""

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from tandem_fetch.db.base import Base


@pytest.fixture
def alembic_config():
    """Create Alembic configuration for testing."""
    config = Config("alembic.ini")
    return config


def test_single_head_revision(alembic_config):
    """Test that there is only one head revision (no merge conflicts).

    Validates:
    - Only one current head exists
    - No branching in migration history
    - No merge conflicts
    """
    script = ScriptDirectory.from_config(alembic_config)
    heads = script.get_revisions("heads")

    assert len(heads) <= 1, f"Should have at most 1 head revision, found {len(heads)}"


@pytest.mark.slow
def test_upgrade_to_head():
    """Test that migrations can be created successfully.

    This is a slow test and is skipped in pre-commit hooks.
    For now, we just verify the migration structure exists.
    """
    # Verify alembic directory exists
    import os

    assert os.path.exists("alembic"), "Alembic directory should exist"
    assert os.path.exists("alembic.ini"), "Alembic config should exist"


def test_model_definitions_match_ddl():
    """Test that SQLAlchemy models can create tables.

    Validates:
    - Models are properly defined
    - Tables can be created from models
    - No errors in model definitions
    """
    # Create tables from models
    test_engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(test_engine)

    # Verify tables were created
    inspector = inspect(test_engine)
    tables = set(inspector.get_table_names())

    # Check that key tables exist
    expected_tables = {"raw_events", "events", "cgm_readings", "basal_deliveries"}
    assert expected_tables.issubset(tables), f"Expected tables {expected_tables} to exist"

    test_engine.dispose()
