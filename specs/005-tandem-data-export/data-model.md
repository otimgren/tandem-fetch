# Data Model: Tandem Data Export Command

**Feature**: 005-tandem-data-export
**Date**: 2026-02-08
**Status**: Phase 1 Complete

This document defines the data entities and their relationships for the export feature.

---

## Entity Diagram

```
┌─────────────────────┐
│  ExportConfig       │
│──────────────────── │
│ - tables: List[str] │
│ - format: str       │
│ - output_dir: Path  │
│ - start_date: date? │
│ - end_date: date?   │
│ - fetch_latest: bool│
│ - overwrite: bool   │
│ - timestamp: str    │
└──────────┬──────────┘
           │ configures
           │ 1:N
           ▼
┌──────────────────────┐
│  ExportOperation     │◄──────── validates against ──────┐
│───────────────────── │                                   │
│ - table: str         │                                   │
│ - output_path: Path  │                                   │
│ - query: str         │                                   │
│ - params: dict       │                                   │
└──────────┬───────────┘                                   │
           │ produces                                      │
           │ 1:1                                           │
           ▼                                               │
┌──────────────────────┐                           ┌──────┴────────┐
│  ExportResult        │                           │  DataTable    │
│───────────────────── │                           │───────────────│
│ - table: str         │                           │ - name: str   │
│ - success: bool      │                           │ - schema: dict│
│ - rows_exported: int │                           │ - row_count   │
│ - output_path: Path  │                           │ - date_range  │
│ - duration: float    │                           └───────────────┘
│ - error: str?        │
└──────────────────────┘
```

---

## Entity Definitions

### 1. ExportConfig

**Purpose**: Represents the complete configuration for an export operation as provided by the user via CLI.

**Attributes**:

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tables` | `List[str]` | Yes | - | Names of tables to export (cgm_readings, basal_deliveries, events, raw_events) |
| `format` | `str` | Yes | "parquet" | Export format: "parquet" or "csv" |
| `output_dir` | `Path` | Yes | "exports/" | Directory where exported files will be written |
| `start_date` | `Optional[date]` | No | None | Start date for filtering (inclusive) |
| `end_date` | `Optional[date]` | No | None | End date for filtering (inclusive) |
| `fetch_latest` | `bool` | Yes | True | Whether to run pipeline before export |
| `overwrite` | `bool` | Yes | False | Whether to overwrite existing files |
| `timestamp` | `str` | Yes | auto | ISO format timestamp when config was created |

**Validation Rules**:
- `tables` must be non-empty list
- Each table name must be one of: `cgm_readings`, `basal_deliveries`, `events`, `raw_events`
- `format` must be either `parquet` or `csv`
- `output_dir` must be writable or creatable
- If both dates provided: `start_date` <= `end_date`
- `timestamp` auto-generated if not provided

**State Transitions**: Immutable after creation (configuration object)

**Example**:
```python
config = ExportConfig(
    tables=["cgm_readings", "basal_deliveries"],
    format="parquet",
    output_dir=Path("exports"),
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31),
    fetch_latest=True,
    overwrite=False,
    timestamp="2026-02-08T10:30:00"
)
```

---

### 2. DataTable

**Purpose**: Represents metadata about a database table available for export.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Table name (cgm_readings, basal_deliveries, events, raw_events) |
| `schema` | `dict` | Yes | Column names and types from SQLAlchemy model |
| `row_count` | `int` | Yes | Total number of rows in table |
| `date_range` | `tuple[datetime, datetime]` | Yes | (min_timestamp, max_timestamp) for date filtering |

**Relationships**:
- **Used by**: ExportOperation (1:1) - validates that table exists before export
- **Derived from**: SQLAlchemy models in `src/tandem_fetch/db/`

**Schema Structure**:

Each table has a known schema derived from SQLAlchemy models:

```python
# cgm_readings schema
{
    "id": "INTEGER",
    "events_id": "INTEGER (FK → events.id)",
    "timestamp": "TIMESTAMP WITH TIMEZONE",
    "cgm_reading": "INTEGER"
}

# basal_deliveries schema
{
    "id": "INTEGER",
    "events_id": "INTEGER (FK → events.id)",
    "timestamp": "TIMESTAMP WITH TIMEZONE",
    "profile_basal_rate": "INTEGER",
    "algorithm_basal_rate": "INTEGER",
    "temp_basal_rate": "INTEGER"
}

# events schema
{
    "id": "INTEGER",
    "raw_events_id": "INTEGER (FK → raw_events.id)",
    "created": "TIMESTAMP WITH TIMEZONE",
    "timestamp": "TIMESTAMP WITH TIMEZONE",
    "event_id": "INTEGER",
    "event_name": "TEXT",
    "event_data": "JSON"
}

# raw_events schema
{
    "id": "INTEGER",
    "pump_serial": "TEXT",
    "event_timestamp": "TIMESTAMP WITH TIMEZONE",
    "raw_event_data": "JSON"
}
```

**Validation Rules**:
- `name` must be one of the four known tables
- `row_count` >= 0
- `date_range` timestamps must be timezone-aware (UTC)

**Example**:
```python
table = DataTable(
    name="cgm_readings",
    schema={
        "id": "INTEGER",
        "timestamp": "TIMESTAMP WITH TIMEZONE",
        "cgm_reading": "INTEGER"
    },
    row_count=125_000,
    date_range=(
        datetime(2025, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 2, 8, tzinfo=timezone.utc)
    )
)
```

---

### 3. ExportOperation

**Purpose**: Represents a single table export operation with its generated query and parameters.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | `str` | Yes | Name of table being exported |
| `output_path` | `Path` | Yes | Full path to output file (including filename) |
| `query` | `str` | Yes | SQL query to execute (with placeholders) |
| `params` | `dict` | Yes | Bound parameters for query (empty if no filtering) |
| `format` | `str` | Yes | Export format (parquet/csv) |

**Relationships**:
- **Created from**: ExportConfig (1:N) - one operation per table in config
- **Validates against**: DataTable (1:1) - ensures table exists
- **Produces**: ExportResult (1:1) - outcome of execution

**Query Generation**:

The query is built from config with optional WHERE clause:

```python
# No date filtering
ExportOperation(
    table="cgm_readings",
    output_path=Path("exports/cgm_readings_20260208_103000.parquet"),
    query="SELECT * FROM cgm_readings ORDER BY timestamp",
    params={},
    format="parquet"
)

# With date filtering
ExportOperation(
    table="cgm_readings",
    output_path=Path("exports/cgm_readings_filtered.parquet"),
    query="""
        SELECT * FROM cgm_readings
        WHERE timestamp >= :start_date
        AND timestamp <= :end_date
        ORDER BY timestamp
    """,
    params={
        "start_date": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "end_date": datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    },
    format="parquet"
)
```

**State Transitions**:
1. **Created**: Operation object instantiated from config
2. **Validated**: Table existence confirmed, query built
3. **Executing**: Query running, writing to file
4. **Completed**: ExportResult produced

**Validation Rules**:
- `table` must exist in database
- `output_path` parent directory must be writable
- `query` must be valid SQL
- `params` keys must match query placeholders

---

### 4. ExportResult

**Purpose**: Represents the outcome of a single table export operation.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | `str` | Yes | Name of table that was exported |
| `success` | `bool` | Yes | Whether export completed successfully |
| `rows_exported` | `int` | Yes | Number of rows written to file |
| `output_path` | `Path` | Yes | Full path to exported file |
| `duration` | `float` | Yes | Export duration in seconds |
| `error` | `Optional[str]` | No | Error message if export failed |
| `file_size_bytes` | `int` | Yes | Size of exported file in bytes |
| `format` | `str` | Yes | Format of exported file (parquet/csv) |

**Relationships**:
- **Produced by**: ExportOperation (1:1) - result of executing operation
- **Aggregated into**: ExportSummary (N:1) - multiple results form summary

**Success Criteria**:
- `success = True` requires:
  - Query executed without errors
  - File written successfully
  - `rows_exported` > 0 (or table was empty)
  - File exists at `output_path`

**Failure Cases**:
- `success = False` when:
  - Database connection failed
  - Query execution failed
  - File write failed (disk full, permissions)
  - Export interrupted (Ctrl+C)

**Example (Success)**:
```python
result = ExportResult(
    table="cgm_readings",
    success=True,
    rows_exported=125_000,
    output_path=Path("exports/cgm_readings_20260208_103000.parquet"),
    duration=2.45,
    error=None,
    file_size_bytes=1_250_000,
    format="parquet"
)
```

**Example (Failure)**:
```python
result = ExportResult(
    table="nonexistent_table",
    success=False,
    rows_exported=0,
    output_path=Path("exports/nonexistent_table_20260208_103000.parquet"),
    duration=0.15,
    error="Table 'nonexistent_table' does not exist",
    file_size_bytes=0,
    format="parquet"
)
```

---

### 5. ExportSummary

**Purpose**: Aggregated results from multiple table exports for reporting.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `timestamp` | `datetime` | Yes | When export operation completed |
| `config` | `ExportConfig` | Yes | Configuration used for export |
| `results` | `List[ExportResult]` | Yes | Individual table export results |
| `total_rows` | `int` | Yes | Sum of rows_exported across all successful exports |
| `total_duration` | `float` | Yes | Total duration in seconds |
| `success_count` | `int` | Yes | Number of successful exports |
| `failure_count` | `int` | Yes | Number of failed exports |
| `overall_success` | `bool` | Yes | Whether entire operation succeeded |

**Derived Values**:
```python
summary.success_count = len([r for r in results if r.success])
summary.failure_count = len([r for r in results if not r.success])
summary.total_rows = sum(r.rows_exported for r in results if r.success)
summary.overall_success = summary.failure_count < len(results)  # Allow partial success
```

**Failure Policy**:
- `overall_success = True` if at least one table exported successfully
- `overall_success = False` if all tables failed to export

**Example**:
```python
summary = ExportSummary(
    timestamp=datetime.now(timezone.utc),
    config=config,  # ExportConfig object
    results=[result1, result2, result3],  # List of ExportResult
    total_rows=250_000,
    total_duration=5.67,
    success_count=2,
    failure_count=1,
    overall_success=True
)
```

---

## Data Flow

### Export Lifecycle

```
1. User Input (CLI)
   │
   ├─► ExportConfig created
   │
2. Validation Phase
   │
   ├─► DataTable metadata queried for each table
   │   ├─ Table existence check
   │   ├─ Row count retrieval
   │   └─ Date range retrieval
   │
3. Operation Generation
   │
   ├─► ExportOperation created per table
   │   ├─ Query built with optional WHERE clause
   │   ├─ Output path resolved
   │   └─ Parameters bound
   │
4. Execution Phase
   │
   ├─► ExportOperation executed (DuckDB COPY)
   │   ├─ Query executed
   │   ├─ File written
   │   └─ Metrics collected
   │
5. Result Collection
   │
   ├─► ExportResult created per operation
   │
6. Aggregation
   │
   └─► ExportSummary created from all results
```

---

## Storage Considerations

### File Naming Convention

```
{table_name}_{timestamp}.{format}

Examples:
- cgm_readings_20260208_103000.parquet
- basal_deliveries_20260208_103000.csv
- events_20260208_103000.parquet
```

### Directory Structure

```
exports/                          # Default output directory
├── cgm_readings_20260208_103000.parquet
├── basal_deliveries_20260208_103000.parquet
├── events_20260208_103000.parquet
└── raw_events_20260208_103000.parquet
```

### File Size Estimates

Based on typical data volumes:

| Table | Typical Rows | Parquet Size | CSV Size | Notes |
|-------|--------------|--------------|----------|-------|
| cgm_readings | 100k | ~2 MB | ~10 MB | Time-series, high compression |
| basal_deliveries | 50k | ~1.5 MB | ~7 MB | Similar to CGM |
| events | 500k | ~15 MB | ~75 MB | JSON columns, less compressible |
| raw_events | 500k | ~25 MB | ~125 MB | Full JSON blobs |

---

## Type Precision Requirements

### Timestamp Handling

All timestamps must preserve:
- **Timezone awareness**: Store and export as UTC
- **Precision**: Microsecond precision (PostgreSQL TIMESTAMP(6))
- **Format**: ISO 8601 in CSV, native TIMESTAMP in Parquet

```python
# DuckDB preserves timezone-aware timestamps
timestamp: datetime = datetime(2026, 2, 8, 10, 30, 0, 123456, tzinfo=timezone.utc)

# CSV export format
"2026-02-08T10:30:00.123456+00:00"

# Parquet stores as INT96 or INT64 with timezone metadata
```

### Numeric Precision

- **CGM readings**: INTEGER (mg/dL, no decimals)
- **Basal rates**: INTEGER (units/hour × 1000, e.g., 0.850 U/h = 850)
- **IDs**: INTEGER (64-bit)

### JSON Preservation

- **events.event_data**: JSON object, preserve structure
- **raw_events.raw_event_data**: JSON object, preserve structure

For CSV export, JSON columns are serialized as JSON strings:
```csv
id,event_name,event_data
123,"CGM_READING","{""reading"": 120, ""trend"": ""steady""}"
```

For Parquet export, JSON can be stored as STRING or STRUCT (DuckDB chooses optimal).

---

## Validation Rules Summary

### Pre-Export Validation

| Check | Entity | Rule |
|-------|--------|------|
| Table exists | DataTable | Query `SELECT 1 FROM {table} LIMIT 1` |
| Output writable | ExportConfig | Create test file in output_dir |
| Date range valid | ExportConfig | start_date <= end_date |
| Format valid | ExportConfig | format in ["parquet", "csv"] |
| Tables non-empty | ExportConfig | tables list has at least one element |

### Post-Export Validation

| Check | Entity | Rule |
|-------|--------|------|
| File exists | ExportResult | output_path.exists() |
| File non-empty | ExportResult | file_size_bytes > 0 or table was empty |
| Rows match | ExportResult | rows_exported matches query count |

---

## Error Handling

### Validation Errors

- **Invalid table name**: Raise `ValueError` before operation creation
- **Invalid date range**: Raise `ValueError` in ExportConfig creation
- **Output directory not writable**: Raise `ValueError` in validation phase

### Execution Errors

- **Database connection failed**: Return `ExportResult(success=False, error=...)`
- **Query execution failed**: Return `ExportResult(success=False, error=...)`
- **File write failed**: Return `ExportResult(success=False, error=...)`

### Recovery Strategy

- **Partial failures**: Continue exporting remaining tables
- **All failures**: Raise exception after collecting all results
- **Interruption (Ctrl+C)**: Prefect handles graceful shutdown

---

## Implementation Notes

### SQLAlchemy Model Mapping

Map entity attributes to SQLAlchemy models:

```python
# DataTable schema derived from SQLAlchemy models
from tandem_fetch.db.cgm_readings import CgmReading
from sqlalchemy import inspect

def get_table_schema(model_class) -> dict:
    """Extract schema from SQLAlchemy model."""
    mapper = inspect(model_class)
    return {
        col.name: str(col.type)
        for col in mapper.columns
    }

cgm_schema = get_table_schema(CgmReading)
# {'id': 'INTEGER', 'timestamp': 'DATETIME', 'cgm_reading': 'INTEGER'}
```

### Prefect Task Signatures

```python
@task
def create_export_operation(
    config: ExportConfig,
    table_name: str
) -> ExportOperation:
    """Create export operation from config for single table."""
    pass

@task
def execute_export_operation(
    operation: ExportOperation
) -> ExportResult:
    """Execute export and return result."""
    pass

@task
def aggregate_export_results(
    config: ExportConfig,
    results: List[ExportResult]
) -> ExportSummary:
    """Aggregate results into summary."""
    pass
```

---

## Appendix: Table Relationships

### Database Schema (Existing)

```
raw_events (source of truth)
    ↓ 1:1
  events (parsed)
    ↓ 1:1
  ┌─────┴─────┐
  ↓           ↓
cgm_readings  basal_deliveries
```

**Foreign Key Constraints**:
- `events.raw_events_id` → `raw_events.id` (UNIQUE)
- `cgm_readings.events_id` → `events.id` (UNIQUE)
- `basal_deliveries.events_id` → `events.id` (UNIQUE)

**Export Independence**:
- Each table can be exported independently
- No need to preserve FK relationships in export files
- User can JOIN tables after import if needed
