"""Unit tests for export tasks.

Tests date handling, query building, and export configuration.
"""

from datetime import date, datetime, time, timezone
from pathlib import Path

import pytest

from tandem_fetch.tasks.export import (
    ExportConfig,
    build_export_query,
    resolve_output_path,
    validate_date_range,
    validate_table_name,
)


class TestDateStringParsing:
    """Test parse_date_string function from workflows.export_data."""

    def test_parse_valid_date_string(self):
        """Test parsing a valid YYYY-MM-DD date string."""
        from tandem_fetch.workflows.export_data import parse_date_string

        result = parse_date_string("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_date_string_invalid_format(self):
        """Test that invalid date format raises ValueError."""
        from tandem_fetch.workflows.export_data import parse_date_string

        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_string("01/15/2024")

    def test_parse_date_string_invalid_date(self):
        """Test that invalid date values raise ValueError."""
        from tandem_fetch.workflows.export_data import parse_date_string

        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_string("2024-13-01")  # Invalid month


class TestDateRangeValidation:
    """Test date range validation logic."""

    def test_validate_date_range_valid(self):
        """Test that valid date ranges pass validation."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        assert validate_date_range(start, end) is True

    def test_validate_date_range_same_date(self):
        """Test that same start and end date is valid."""
        same_date = date(2024, 1, 1)
        assert validate_date_range(same_date, same_date) is True

    def test_validate_date_range_none_values(self):
        """Test that None values are valid (no filtering)."""
        assert validate_date_range(None, None) is True
        assert validate_date_range(date(2024, 1, 1), None) is True
        assert validate_date_range(None, date(2024, 12, 31)) is True

    def test_validate_date_range_invalid(self):
        """Test that end date before start date raises ValueError."""
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        with pytest.raises(ValueError, match="start_date.*cannot be after.*end_date"):
            validate_date_range(start, end)


class TestTableNameValidation:
    """Test table name validation."""

    def test_validate_valid_table_names(self):
        """Test that valid table names pass validation."""
        valid_tables = ["cgm_readings", "basal_deliveries", "events", "raw_events"]
        for table in valid_tables:
            assert validate_table_name(table) is True

    def test_validate_invalid_table_name(self):
        """Test that invalid table name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid table name"):
            validate_table_name("nonexistent_table")

    def test_validate_invalid_table_name_with_suggestion(self):
        """Test that close match provides helpful suggestion."""
        with pytest.raises(ValueError, match="Did you mean 'cgm_readings'"):
            validate_table_name("cgm")


class TestBuildExportQuery:
    """Test SQL query building with date filtering."""

    def test_build_query_without_dates(self):
        """Test building query without date filtering."""
        query, params = build_export_query("cgm_readings")

        assert "SELECT * FROM cgm_readings" in query
        assert "WHERE" not in query
        assert "ORDER BY id" in query
        assert params == {}

    def test_build_query_with_start_date(self):
        """Test building query with start date filtering."""
        start_date = date(2024, 1, 1)
        query, params = build_export_query("cgm_readings", start_date=start_date)

        assert "SELECT * FROM cgm_readings" in query
        assert "WHERE timestamp >= :start_date" in query
        assert "ORDER BY id" in query

        # Verify parameter is ISO string (not datetime object with timezone)
        assert "start_date" in params
        assert isinstance(params["start_date"], str)
        # Parse it back to verify format
        parsed = datetime.fromisoformat(params["start_date"])
        assert parsed.date() == start_date
        assert parsed.time() == time.min
        assert parsed.tzinfo == timezone.utc

    def test_build_query_with_end_date(self):
        """Test building query with end date filtering."""
        end_date = date(2024, 12, 31)
        query, params = build_export_query("cgm_readings", end_date=end_date)

        assert "WHERE timestamp <= :end_date" in query

        # Verify parameter is ISO string with end of day time
        assert "end_date" in params
        assert isinstance(params["end_date"], str)
        parsed = datetime.fromisoformat(params["end_date"])
        assert parsed.date() == end_date
        assert parsed.time() == time.max
        assert parsed.tzinfo == timezone.utc

    def test_build_query_with_date_range(self):
        """Test building query with both start and end dates."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        query, params = build_export_query("cgm_readings", start_date=start_date, end_date=end_date)

        assert "WHERE timestamp >= :start_date AND timestamp <= :end_date" in query
        assert "start_date" in params
        assert "end_date" in params
        assert isinstance(params["start_date"], str)
        assert isinstance(params["end_date"], str)

    def test_build_copy_query_parquet(self):
        """Test building COPY query for Parquet export."""
        output_path = Path("/tmp/test.parquet")
        query, params = build_export_query(
            "cgm_readings", format="parquet", output_path=output_path
        )

        assert "COPY (SELECT * FROM cgm_readings" in query
        assert f"TO '{output_path}'" in query
        assert "FORMAT PARQUET" in query
        assert "COMPRESSION ZSTD" in query

    def test_build_copy_query_csv(self):
        """Test building COPY query for CSV export."""
        output_path = Path("/tmp/test.csv")
        query, params = build_export_query("cgm_readings", format="csv", output_path=output_path)

        assert "COPY (SELECT * FROM cgm_readings" in query
        assert f"TO '{output_path}'" in query
        assert "FORMAT CSV" in query
        assert "HEADER TRUE" in query

    def test_build_copy_query_with_date_filtering(self):
        """Test that COPY query includes date filtering."""
        output_path = Path("/tmp/test.parquet")
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        query, params = build_export_query(
            "cgm_readings",
            format="parquet",
            output_path=output_path,
            start_date=start_date,
            end_date=end_date,
        )

        assert "WHERE timestamp >= :start_date AND timestamp <= :end_date" in query
        assert "start_date" in params
        assert "end_date" in params


class TestResolveOutputPath:
    """Test output path resolution."""

    def test_resolve_output_path_basic(self, tmp_path):
        """Test basic output path resolution."""
        output_dir = tmp_path / "exports"
        timestamp = "2024-01-01T12:00:00+00:00"

        path = resolve_output_path("cgm_readings", output_dir, "parquet", timestamp)

        assert path.parent == output_dir
        assert path.name == "cgm_readings_20240101_120000.parquet"
        assert output_dir.exists()  # Directory should be created

    def test_resolve_output_path_csv_format(self, tmp_path):
        """Test output path with CSV format."""
        output_dir = tmp_path / "exports"

        path = resolve_output_path("events", output_dir, "csv")

        assert path.suffix == ".csv"
        assert "events_" in path.name

    def test_resolve_output_path_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nested" / "exports"
        assert not output_dir.exists()

        resolve_output_path("cgm_readings", output_dir, "parquet")

        assert output_dir.exists()

    def test_resolve_output_path_timestamp_parsing(self, tmp_path):
        """Test that ISO timestamp is correctly parsed to filename format."""
        output_dir = tmp_path / "exports"
        timestamp = "2024-03-15T14:30:45.123456+00:00"

        path = resolve_output_path("cgm_readings", output_dir, "parquet", timestamp)

        # Should format as YYYYMMDD_HHMMSS
        assert "20240315_143045" in path.name


class TestExportConfig:
    """Test ExportConfig dataclass."""

    def test_export_config_defaults(self):
        """Test ExportConfig with default values."""
        config = ExportConfig(tables=["cgm_readings"])

        assert config.format == "parquet"
        assert config.fetch_latest is True
        assert config.overwrite is False
        assert config.start_date is None
        assert config.end_date is None
        assert config.timestamp != ""  # Should be auto-generated

    def test_export_config_timestamp_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        config1 = ExportConfig(tables=["cgm_readings"])
        config2 = ExportConfig(tables=["cgm_readings"])

        # Both should have timestamps
        assert config1.timestamp
        assert config2.timestamp
        # Timestamps should be ISO format
        datetime.fromisoformat(config1.timestamp)
        datetime.fromisoformat(config2.timestamp)

    def test_export_config_deduplicates_tables(self):
        """Test that duplicate table names are removed."""
        config = ExportConfig(tables=["cgm_readings", "events", "cgm_readings", "events"])

        assert len(config.tables) == 2
        assert "cgm_readings" in config.tables
        assert "events" in config.tables

    def test_export_config_normalizes_format(self):
        """Test that format is normalized to lowercase."""
        config = ExportConfig(tables=["cgm_readings"], format="PARQUET")

        assert config.format == "parquet"

    def test_export_config_output_dir_path_conversion(self):
        """Test that output_dir is converted to Path object."""
        config = ExportConfig(tables=["cgm_readings"], output_dir="/tmp/exports")

        assert isinstance(config.output_dir, Path)
        assert config.output_dir == Path("/tmp/exports")
