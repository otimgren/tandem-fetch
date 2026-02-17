"""Unit tests for database connection helpers."""

from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
from sqlalchemy import Engine, text

from tandem_fetch.db import DatabaseNotFoundError, get_engine


class TestGetEngineHappyPath:
    """Tests for get_engine() when database file exists."""

    def test_returns_engine_when_db_exists(self, tmp_path: Path):
        """Test that get_engine() returns a SQLAlchemy Engine when DB exists."""
        # Create a temporary DuckDB file
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        # Patch DATABASE_PATH and DATABASE_URL in definitions module
        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            # Create a valid DuckDB file
            conn = duckdb.connect(str(db_file))
            conn.close()

            # Call get_engine()
            engine = get_engine()

            # Verify we got an Engine
            assert isinstance(engine, Engine)

    def test_returned_engine_can_execute_queries(self, tmp_path: Path):
        """Test that the returned engine can execute queries."""
        # Create a temporary DuckDB file
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            # Create a valid DuckDB file
            conn = duckdb.connect(str(db_file))
            conn.close()

            engine = get_engine()

            # Execute a simple query
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test_col"))
                row = result.fetchone()
                assert row is not None
                assert row[0] == 1

    def test_connection_works_as_context_manager(self, tmp_path: Path):
        """Test that connections work as context managers (FR-008)."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            # Create a valid DuckDB file
            conn = duckdb.connect(str(db_file))
            conn.close()

            engine = get_engine()

            # Use connection as context manager
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 42 as answer"))
                assert result.fetchone()[0] == 42

            # Connection should be cleanly closed after context exit
            # (No explicit test needed - context manager handles it)


class TestGetEngineInteractive:
    """Tests for get_engine() when database is missing and interactive=True."""

    def test_user_says_yes_runs_pipeline_and_returns_engine(self, tmp_path: Path):
        """Test that when user says 'y', pipeline is called and engine is returned."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
            patch("builtins.input", return_value="y"),
            patch(
                "tandem_fetch.workflows.backfills.run_full_pipeline.run_full_pipeline"
            ) as mock_pipeline,
            patch("builtins.print") as mock_print,
        ):
            # Simulate pipeline creating the DB file
            def create_db(*args, **kwargs):
                conn = duckdb.connect(str(db_file))
                conn.close()

            mock_pipeline.side_effect = create_db

            # Call get_engine()
            engine = get_engine(interactive=True)

            # Verify pipeline was called
            mock_pipeline.assert_called_once()

            # Verify engine was returned
            assert isinstance(engine, Engine)

            # Verify appropriate messages were printed
            assert any(
                f"Database not found at {db_file}" in str(call)
                for call in mock_print.call_args_list
            )

    def test_user_says_no_returns_none_and_prints_instructions(self, tmp_path: Path):
        """Test that when user says 'n', None is returned and manual instructions printed."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
            patch("builtins.input", return_value="n"),
            patch(
                "tandem_fetch.workflows.backfills.run_full_pipeline.run_full_pipeline"
            ) as mock_pipeline,
            patch("builtins.print") as mock_print,
        ):
            # Call get_engine()
            engine = get_engine(interactive=True)

            # Verify pipeline was NOT called
            mock_pipeline.assert_not_called()

            # Verify None was returned
            assert engine is None

            # Verify instructions were printed
            assert any("run-pipeline" in str(call) for call in mock_print.call_args_list)

    def test_prompt_includes_database_path(self, tmp_path: Path):
        """Test that the prompt message includes the expected database path."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
            patch("builtins.input", return_value="n"),
            patch("builtins.print") as mock_print,
        ):
            get_engine(interactive=True)

            # Check that database path appears in print output
            printed_output = " ".join(str(call) for call in mock_print.call_args_list)
            assert str(db_file) in printed_output


class TestGetEngineNonInteractive:
    """Tests for get_engine() in non-interactive mode (interactive=False)."""

    def test_raises_error_when_db_missing(self, tmp_path: Path):
        """Test that DatabaseNotFoundError is raised when DB is missing and interactive=False."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            # Call get_engine in non-interactive mode
            with pytest.raises(DatabaseNotFoundError):
                get_engine(interactive=False)

    def test_exception_has_correct_database_path(self, tmp_path: Path):
        """Test that the exception's database_path attribute is correct."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            try:
                get_engine(interactive=False)
            except DatabaseNotFoundError as e:
                assert e.database_path == db_file
                # Verify message includes path
                assert str(db_file) in str(e)
                # Verify message includes instructions
                assert "run-pipeline" in str(e)
            else:
                pytest.fail("DatabaseNotFoundError was not raised")

    def test_catchable_as_file_not_found_error(self, tmp_path: Path):
        """Test that DatabaseNotFoundError can be caught as FileNotFoundError."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            # Verify it can be caught as FileNotFoundError
            with pytest.raises(FileNotFoundError):
                get_engine(interactive=False)

    def test_returns_engine_when_db_exists_non_interactive(self, tmp_path: Path):
        """Test that engine is still returned when DB exists in non-interactive mode."""
        db_file = tmp_path / "test.db"
        db_url = f"duckdb:///{db_file}"

        with (
            patch("tandem_fetch.definitions.DATABASE_PATH", db_file),
            patch("tandem_fetch.definitions.DATABASE_URL", db_url),
        ):
            # Create a valid DuckDB file
            conn = duckdb.connect(str(db_file))
            conn.close()

            # Call get_engine in non-interactive mode
            engine = get_engine(interactive=False)

            # Verify engine is returned (same as US1 happy path)
            assert isinstance(engine, Engine)
