"""MCP server for read-only access to the Tandem pump DuckDB database."""

import signal
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from sqlalchemy import inspect, text

from tandem_fetch.db.connect import get_engine
from tandem_fetch.definitions import DATABASE_PATH

mcp = FastMCP("tandem-db")

_WRITE_KEYWORDS = frozenset(
    {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "REPLACE",
        "MERGE",
    }
)

_TABLE_DESCRIPTIONS: dict[str, str] = {
    "cgm_readings": (
        "CGM (continuous glucose monitor) sensor readings with timestamps. "
        "Each row is a single glucose reading."
    ),
    "basal_deliveries": (
        "Insulin basal delivery rates with timestamps. "
        "Includes profile, algorithm-adjusted, and temporary basal rates."
    ),
    "events": (
        "Parsed pump events with event type, name, timestamp, and event-specific data as JSON."
    ),
    "raw_events": (
        "Raw unprocessed API responses from the Tandem pump. "
        "Contains complete JSON blobs. Prefer querying the parsed tables "
        "(events, cgm_readings, basal_deliveries) for structured data."
    ),
}

_QUERY_TIMEOUT_SECONDS = 30


def _check_database() -> None:
    """Check that the database file exists, raising ToolError if not."""
    if not DATABASE_PATH.exists():
        raise ToolError(
            f"Database not found at {DATABASE_PATH}. "
            "Run 'run-pipeline' to fetch data from the Tandem API before querying."
        )


def _validate_query(sql: str) -> None:
    """Validate that a SQL query is read-only.

    Raises ToolError if the query is not a SELECT/WITH statement,
    contains write keywords, or contains multiple statements.
    """
    stripped = sql.strip()
    upper = stripped.upper()

    # Must start with SELECT or WITH
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise ToolError(
            "Only read-only SELECT queries are allowed. "
            "Write operations (INSERT, UPDATE, DELETE, DROP, etc.) are not permitted."
        )

    # Reject multiple statements (check before write keywords so
    # "SELECT 1; DROP TABLE x" gets the semicolon error)
    if ";" in stripped:
        raise ToolError(
            "Only single SQL statements are allowed. "
            "Remove semicolons to execute one query at a time."
        )

    # Reject write keywords anywhere in the query
    tokens = set(upper.split())
    if tokens & _WRITE_KEYWORDS:
        raise ToolError(
            "Only read-only SELECT queries are allowed. "
            "Write operations (INSERT, UPDATE, DELETE, DROP, etc.) are not permitted."
        )


def _format_results(columns: list[str], rows: list[Any], limit: int) -> str:
    """Format query results as tab-separated text with headers."""
    truncated = len(rows) > limit
    display_rows = rows[:limit]

    lines = ["\t".join(columns)]
    for row in display_rows:
        lines.append("\t".join(str(v) for v in row))

    row_count = len(display_rows)
    if truncated:
        lines.append(
            f"\n{row_count} rows returned "
            "(results truncated — set a higher limit or add a WHERE clause "
            "to narrow results)."
        )
    else:
        lines.append(f"\n{row_count} rows returned.")

    return "\n".join(lines)


@mcp.tool
def list_tables() -> str:
    """List all available database tables and their descriptions."""
    lines = ["Available tables:", ""]
    for table_name, description in _TABLE_DESCRIPTIONS.items():
        lines.append(f"- {table_name}: {description}")
    return "\n".join(lines)


@mcp.tool
def describe_table(table_name: str) -> str:
    """Get the schema (column names and types) for a specific database table."""
    if table_name not in _TABLE_DESCRIPTIONS:
        valid = ", ".join(_TABLE_DESCRIPTIONS.keys())
        raise ToolError(f"Unknown table '{table_name}'. Valid tables are: {valid}")

    _check_database()
    engine = get_engine(interactive=False)

    insp = inspect(engine)
    columns = insp.get_columns(table_name)

    lines = [f"Table: {table_name}", "", "Columns:"]
    for col in columns:
        col_type = str(col["type"])
        lines.append(f"- {col['name']}: {col_type}")

    return "\n".join(lines)


def _timeout_handler(signum: int, frame: Any) -> None:
    raise TimeoutError


@mcp.tool
def query(sql: str, limit: int = 1000) -> str:
    """Execute a read-only SQL query against the Tandem pump database. Only SELECT queries are allowed."""
    _validate_query(sql)
    _check_database()

    limit = max(1, min(limit, 10000))

    engine = get_engine(interactive=False)

    wrapped_sql = f"SELECT * FROM ({sql}) sub LIMIT {limit + 1}"

    old_handler = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(_QUERY_TIMEOUT_SECONDS)

        with engine.connect() as conn:
            result = conn.execute(text(wrapped_sql))
            columns = list(result.keys())
            rows = result.fetchall()

        signal.alarm(0)
    except TimeoutError:
        raise ToolError(
            f"Query timed out after {_QUERY_TIMEOUT_SECONDS} seconds. "
            "Try a simpler query or add filters to reduce the data scanned."
        )
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Query error: {e}")
    finally:
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)

    return _format_results(columns, rows, limit)


def main() -> None:
    """Entry point for the tandem-mcp CLI command."""
    mcp.run()
