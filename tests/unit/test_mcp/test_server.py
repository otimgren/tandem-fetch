"""Unit tests for the MCP server tools and validation logic."""

from unittest.mock import MagicMock

import pytest
from fastmcp.exceptions import ToolError
from sqlalchemy import text

from tandem_fetch.mcp.server import (
    _format_results,
    _validate_query,
    describe_table,
    list_tables,
    query,
)

# @mcp.tool wraps functions as FunctionTool objects; access .fn for the original callable
_list_tables = list_tables.fn
_describe_table = describe_table.fn
_query = query.fn


@pytest.fixture()
def mock_db(test_db_engine, monkeypatch):
    """Patch the MCP server to use the in-memory test database."""
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    monkeypatch.setattr("tandem_fetch.mcp.server.DATABASE_PATH", mock_path)
    monkeypatch.setattr("tandem_fetch.mcp.server.get_engine", lambda interactive: test_db_engine)
    return test_db_engine


class TestValidateQuery:
    """Tests for the _validate_query helper function."""

    def test_accepts_simple_select(self):
        _validate_query("SELECT * FROM cgm_readings")

    def test_accepts_select_with_where(self):
        _validate_query("SELECT cgm_reading FROM cgm_readings WHERE timestamp > '2026-01-01'")

    def test_accepts_with_cte(self):
        _validate_query("WITH cte AS (SELECT * FROM events) SELECT * FROM cte")

    def test_accepts_lowercase_select(self):
        _validate_query("select * from cgm_readings")

    def test_accepts_mixed_case(self):
        _validate_query("Select * From cgm_readings")

    def test_accepts_leading_whitespace(self):
        _validate_query("  SELECT * FROM cgm_readings")

    def test_rejects_insert(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("INSERT INTO cgm_readings VALUES (1, 1, '2026-01-01', 100)")

    def test_rejects_update(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("UPDATE cgm_readings SET cgm_reading = 0")

    def test_rejects_delete(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("DELETE FROM cgm_readings")

    def test_rejects_drop(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("DROP TABLE cgm_readings")

    def test_rejects_alter(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("ALTER TABLE cgm_readings ADD COLUMN foo INT")

    def test_rejects_create(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("CREATE TABLE foo (id INT)")

    def test_rejects_truncate(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("TRUNCATE TABLE cgm_readings")

    def test_rejects_semicolons(self):
        with pytest.raises(ToolError, match="single SQL statements"):
            _validate_query("SELECT 1; DROP TABLE cgm_readings")

    def test_rejects_trailing_semicolon(self):
        with pytest.raises(ToolError, match="single SQL statements"):
            _validate_query("SELECT * FROM cgm_readings;")

    def test_rejects_non_select_start(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _validate_query("EXPLAIN SELECT * FROM cgm_readings")


class TestFormatResults:
    """Tests for the _format_results helper function."""

    def test_formats_basic_results(self):
        columns = ["id", "value"]
        rows = [(1, 100), (2, 200)]
        result = _format_results(columns, rows, limit=1000)
        assert "id\tvalue" in result
        assert "1\t100" in result
        assert "2\t200" in result
        assert "2 rows returned." in result

    def test_formats_empty_results(self):
        result = _format_results(["id"], [], limit=1000)
        assert "0 rows returned." in result

    def test_truncation_notice(self):
        columns = ["id"]
        rows = [(i,) for i in range(4)]  # 4 rows, limit 3
        result = _format_results(columns, rows, limit=3)
        assert "3 rows returned" in result
        assert "truncated" in result

    def test_no_truncation_at_limit(self):
        columns = ["id"]
        rows = [(i,) for i in range(3)]  # exactly 3 rows, limit 3
        result = _format_results(columns, rows, limit=3)
        assert "3 rows returned." in result
        assert "truncated" not in result


class TestListTables:
    """Tests for the list_tables tool."""

    def test_returns_all_tables(self):
        result = _list_tables()
        assert "cgm_readings" in result
        assert "basal_deliveries" in result
        assert "events" in result
        assert "raw_events" in result

    def test_includes_descriptions(self):
        result = _list_tables()
        assert "CGM" in result
        assert "basal" in result.lower()


class TestDescribeTable:
    """Tests for the describe_table tool."""

    def test_rejects_invalid_table(self):
        with pytest.raises(ToolError, match="Unknown table"):
            _describe_table("nonexistent_table")

    def test_error_lists_valid_tables(self):
        with pytest.raises(ToolError, match="cgm_readings"):
            _describe_table("bad_name")

    def test_describes_cgm_readings(self, mock_db):
        result = _describe_table("cgm_readings")
        assert "Table: cgm_readings" in result
        assert "timestamp" in result
        assert "cgm_reading" in result


class TestQuery:
    """Tests for the query tool."""

    def test_rejects_write_query(self):
        with pytest.raises(ToolError, match="read-only SELECT"):
            _query("DELETE FROM cgm_readings")

    def test_executes_select(self, mock_db):
        result = _query("SELECT 1 AS num")
        assert "num" in result
        assert "1" in result
        assert "1 rows returned." in result

    def test_respects_limit(self, mock_db):
        # Insert events first (FK target), then cgm_readings
        with mock_db.connect() as conn:
            for i in range(5):
                conn.execute(
                    text(
                        "INSERT INTO events (id, raw_events_id, created, timestamp, "
                        f"event_id, event_name) VALUES ({i + 100}, {i + 100}, "
                        f"'2026-01-01', '2026-01-01', 1, 'test')"
                    )
                )
            for i in range(5):
                conn.execute(
                    text(
                        "INSERT INTO cgm_readings (id, events_id, timestamp, cgm_reading) "
                        f"VALUES ({i + 100}, {i + 100}, '2026-01-01 00:00:00', {100 + i})"
                    )
                )
            conn.commit()

        result = _query("SELECT * FROM cgm_readings", limit=3)
        assert "3 rows returned" in result
        assert "truncated" in result

    def test_clamps_limit_to_minimum(self, mock_db):
        # Should not error with limit=0 (clamped to 1)
        result = _query("SELECT 1 AS num", limit=0)
        assert "1 rows returned." in result
