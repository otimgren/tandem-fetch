# MCP Tool Contracts: MCP Database Server

**Feature**: 007-mcp-server
**Date**: 2026-02-16

## Tool 1: `list_tables`

**Purpose**: Discover available database tables and their descriptions.

**Parameters**: None

**Returns**: Text listing of all tables with descriptions.

**Example response**:
```
Available tables:

- cgm_readings: CGM (continuous glucose monitor) sensor readings with timestamps. Each row is a single glucose reading.
- basal_deliveries: Insulin basal delivery rates with timestamps. Includes profile, algorithm-adjusted, and temporary basal rates.
- events: Parsed pump events with event type, name, timestamp, and event-specific data as JSON.
- raw_events: Raw unprocessed API responses from the Tandem pump. Contains complete JSON blobs. Prefer querying the parsed tables (events, cgm_readings, basal_deliveries) for structured data.
```

**Error conditions**:
- Database file not found → Returns guidance to run `run-pipeline`

**Maps to**: FR-001, FR-009

---

## Tool 2: `describe_table`

**Purpose**: Get the schema (column names and types) for a specific table.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| table_name | string | Yes | Name of the table to describe |

**Returns**: Text listing of column names and their types for the specified table.

**Example request**: `describe_table(table_name="cgm_readings")`

**Example response**:
```
Table: cgm_readings

Columns:
- id: INTEGER (primary key)
- events_id: INTEGER (foreign key → events.id)
- timestamp: TIMESTAMP
- cgm_reading: INTEGER
```

**Error conditions**:
- Invalid table name → Returns error with list of valid table names
- Database file not found → Returns guidance to run `run-pipeline`

**Maps to**: FR-002, FR-009

---

## Tool 3: `query`

**Purpose**: Execute a read-only SQL query against the database.

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| sql | string | Yes | — | SQL SELECT query to execute |
| limit | integer | No | 1000 | Maximum number of rows to return (1-10000) |

**Returns**: Text-formatted query results with column headers, row data, and row count. Includes truncation notice if results were limited.

**Example request**: `query(sql="SELECT timestamp, cgm_reading FROM cgm_readings ORDER BY timestamp DESC", limit=5)`

**Example response**:
```
timestamp            cgm_reading
2026-02-16 10:30:00  125
2026-02-16 10:25:00  130
2026-02-16 10:20:00  128
2026-02-16 10:15:00  132
2026-02-16 10:10:00  127

5 rows returned.
```

**Example response (truncated)**:
```
timestamp            cgm_reading
...
(data rows)
...

1000 rows returned (results truncated — set a higher limit or add a WHERE clause to narrow results).
```

**Validation rules**:
1. Query must start with `SELECT` or `WITH` (case-insensitive, after stripping whitespace)
2. Query must not contain write keywords: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE, MERGE
3. Query must not contain multiple statements (no semicolons except inside string literals)
4. Limit parameter must be between 1 and 10000

**Error conditions**:
- Write operation attempted → Returns "Only read-only SELECT queries are allowed. Write operations (INSERT, UPDATE, DELETE, DROP, etc.) are not permitted."
- Multiple statements detected → Returns "Only single SQL statements are allowed. Remove semicolons to execute one query at a time."
- SQL syntax error → Returns the database error message to help the agent fix the query
- Query timeout (30s) → Returns "Query timed out after 30 seconds. Try a simpler query or add filters to reduce the data scanned."
- Database file not found → Returns guidance to run `run-pipeline`

**Maps to**: FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-011
