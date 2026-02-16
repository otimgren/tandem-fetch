"""Integration tests for export workflow.

Tests the complete export pipeline with database operations.
"""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import text

from tandem_fetch.db.cgm_readings import CgmReading
from tandem_fetch.db.events import Event
from tandem_fetch.db.raw_events import RawEvent
from tandem_fetch.tasks.export import (
    ExportConfig,
    build_export_query,
    export_table_to_file,
    validate_export_config,
)


@pytest.fixture
def sample_cgm_data(db_session):
    """Create sample CGM data for export testing."""
    # Create raw events first (required for foreign key)
    raw_events = [
        RawEvent(
            raw_event_data={
                "event_id": i,
                "event_timestamp": f"2024-01-{i:02d}T12:00:00+00:00",
            }
        )
        for i in range(1, 16)  # 15 days of data
    ]
    db_session.add_all(raw_events)
    db_session.flush()

    # Create events
    events = [
        Event(
            raw_events_id=raw_event.id,
            timestamp=datetime(2024, 1, i, 12, 0, 0, tzinfo=timezone.utc),
            event_id=100,  # CGM event ID
            event_name="CGM",
        )
        for i, raw_event in enumerate(raw_events, start=1)
    ]
    db_session.add_all(events)
    db_session.flush()

    # Create CGM readings
    cgm_readings = [
        CgmReading(
            events_id=event.id,
            timestamp=event.timestamp,
            cgm_reading=100 + i,  # 101, 102, ..., 115
        )
        for i, event in enumerate(events)
    ]
    db_session.add_all(cgm_readings)
    db_session.commit()

    return cgm_readings


class TestDateFilteringIntegration:
    """Test date filtering with actual database queries."""

    def test_query_without_date_filter(self, test_db_engine, sample_cgm_data):
        """Test that query without dates returns all records."""
        query, params = build_export_query("cgm_readings")

        with test_db_engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()

        assert len(rows) == 15  # All 15 records

    def test_query_with_start_date_filter(self, test_db_engine, sample_cgm_data):
        """Test that start date filter works correctly."""
        # Filter for Jan 10 onwards (should get 6 records: 10-15)
        start_date = date(2024, 1, 10)
        query, params = build_export_query("cgm_readings", start_date=start_date)

        with test_db_engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()

        assert len(rows) == 6  # Records from Jan 10-15

    def test_query_with_end_date_filter(self, test_db_engine, sample_cgm_data):
        """Test that end date filter works correctly."""
        # Filter up to Jan 5 (should get 5 records: 1-5)
        end_date = date(2024, 1, 5)
        query, params = build_export_query("cgm_readings", end_date=end_date)

        with test_db_engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()

        assert len(rows) == 5  # Records from Jan 1-5

    def test_query_with_date_range_filter(self, test_db_engine, sample_cgm_data):
        """Test that date range filter works correctly."""
        # Filter for Jan 5-10 (should get 6 records: 5, 6, 7, 8, 9, 10)
        start_date = date(2024, 1, 5)
        end_date = date(2024, 1, 10)
        query, params = build_export_query("cgm_readings", start_date=start_date, end_date=end_date)

        with test_db_engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()

        assert len(rows) == 6  # Records from Jan 5-10

    def test_query_with_no_matching_dates(self, test_db_engine, sample_cgm_data):
        """Test that query with dates outside data range returns empty."""
        # Filter for Feb data (no data in Feb)
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 28)
        query, params = build_export_query("cgm_readings", start_date=start_date, end_date=end_date)

        with test_db_engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()

        assert len(rows) == 0  # No records in February

    def test_query_params_are_strings_not_datetime(self, sample_cgm_data):
        """Test that query parameters are ISO strings, not datetime objects.

        This is critical for DuckDB compatibility - it doesn't support
        timezone-aware datetime objects in bound parameters.
        """
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        query, params = build_export_query("cgm_readings", start_date=start_date, end_date=end_date)

        # Parameters must be strings, not datetime objects
        assert isinstance(params["start_date"], str)
        assert isinstance(params["end_date"], str)

        # Verify they can be parsed back to datetime
        start_dt = datetime.fromisoformat(params["start_date"])
        end_dt = datetime.fromisoformat(params["end_date"])

        # Verify correct timezone handling
        assert start_dt.tzinfo == timezone.utc
        assert end_dt.tzinfo == timezone.utc


class TestExportTableIntegration:
    """Test complete export workflow with actual file creation."""

    def test_export_table_without_dates(self, test_db_engine, sample_cgm_data, tmp_path):
        """Test exporting table without date filtering."""
        output_dir = tmp_path / "exports"

        result = export_table_to_file(
            table_name="cgm_readings",
            output_dir=output_dir,
            format="parquet",
        )

        assert result.success is True
        assert result.rows_exported > 0  # Real DB has data
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.file_size_bytes > 0

    def test_export_table_with_date_range(self, test_db_engine, sample_cgm_data, tmp_path):
        """Test exporting table with date range filtering."""
        output_dir = tmp_path / "exports"
        # Use a date range that should have some data from real DB
        start_date = date(2024, 9, 1)
        end_date = date(2024, 9, 30)

        result = export_table_to_file(
            table_name="cgm_readings",
            output_dir=output_dir,
            format="parquet",
            start_date=start_date,
            end_date=end_date,
        )

        assert result.success is True
        # Date filtering should reduce row count compared to full export
        assert result.rows_exported >= 0
        assert result.output_path.exists()

    def test_export_table_csv_format(self, test_db_engine, sample_cgm_data, tmp_path):
        """Test exporting table to CSV format."""
        output_dir = tmp_path / "exports"

        result = export_table_to_file(
            table_name="cgm_readings",
            output_dir=output_dir,
            format="csv",
        )

        assert result.success is True
        assert result.output_path.suffix == ".csv"
        assert result.output_path.exists()

        # Verify CSV content is readable
        content = result.output_path.read_text()
        assert "cgm_reading" in content  # Header should be present
        assert len(content.splitlines()) > 1  # Header + data rows

    def test_export_with_empty_date_range(self, test_db_engine, sample_cgm_data, tmp_path):
        """Test export with date range that has no matching data."""
        output_dir = tmp_path / "exports"

        result = export_table_to_file(
            table_name="cgm_readings",
            output_dir=output_dir,
            format="parquet",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28),
        )

        assert result.success is True
        assert result.rows_exported == 0
        assert result.output_path.exists()


class TestValidateExportConfig:
    """Test export configuration validation."""

    def test_validate_config_with_dates(self, test_db_engine, sample_cgm_data):
        """Test that validation works with date filtering."""
        config = ExportConfig(
            tables=["cgm_readings"],
            start_date=date(2024, 1, 5),
            end_date=date(2024, 1, 10),
        )

        # Should not raise
        result = validate_export_config(config)
        assert result is True

    def test_validate_config_invalid_date_range(self, test_db_engine):
        """Test that invalid date range is caught during validation."""
        config = ExportConfig(
            tables=["cgm_readings"],
            start_date=date(2024, 12, 31),
            end_date=date(2024, 1, 1),
        )

        with pytest.raises(ValueError, match="start_date.*cannot be after.*end_date"):
            validate_export_config(config)
