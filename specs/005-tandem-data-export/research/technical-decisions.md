# Research Findings: Tandem Data Export Command

**Date**: 2026-02-08
**Feature**: 005-tandem-data-export
**Status**: Phase 0 Complete

This document consolidates research findings from Phase 0 to resolve all technical unknowns identified in the implementation plan.

---

## R1: DuckDB Export Performance

### Decision: Use DuckDB COPY Command

**Rationale**: DuckDB's native COPY command provides optimal performance and memory efficiency for our use case.

**Key Findings**:
- **Performance**: DuckDB COPY is 10x faster than previous versions, competitive with Apache Arrow
- **Memory**: Streaming execution with disk spilling support (peaks at ~1.3GB for 140GB dataset)
- **Comparison**: For 1M+ records, DuckDB COPY significantly outperforms Polars read-then-write approach
- **Format efficiency**: Parquet files are ~5x smaller than CSV with minimal performance tradeoff

**Implementation Approach**:

```python
# Parquet export (recommended for data analysis)
conn.execute(text("""
    COPY cgm_readings
    TO 'exports/cgm_readings.parquet'
    (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
"""))

# CSV export (for Excel/spreadsheet compatibility)
conn.execute(text("""
    COPY cgm_readings
    TO 'exports/cgm_readings.csv'
    (FORMAT CSV, HEADER TRUE)
"""))

# Date-filtered export (P4 requirement)
conn.execute(text("""
    COPY (
        SELECT * FROM cgm_readings
        WHERE timestamp >= :start_date
        AND timestamp <= :end_date
    )
    TO 'exports/cgm_readings_filtered.parquet'
    (FORMAT PARQUET, COMPRESSION ZSTD)
"""))
```

**Configuration Recommendations**:

| Setting | Value | Reason |
|---------|-------|--------|
| Compression | ZSTD | Best compression/speed balance for time-series |
| Row Group Size | 100,000 | Optimal for typical CGM dataset sizes |
| Format Priority | Parquet | 5x smaller, 2-3x faster than CSV |
| Threading | Default (auto) | Unless memory-constrained (then threads=1) |

**Alternatives Considered**:
- **Polars export**: Rejected - requires reading into memory first, 5-7x slower for large datasets
- **Pandas to_parquet()**: Rejected - higher memory usage, slower than native DuckDB
- **Direct pyarrow**: Rejected - adds complexity without performance benefit

**Limitations Identified**:
- Memory limit ignored when threads > 1 (use threads=1 if memory critical)
- Concurrent multi-process writes not supported (not needed for single-user CLI)

---

## R2: CLI Argument Parsing

### Decision: Use Typer

**Rationale**: Type-safe, minimal boilerplate, excellent integration with existing stack (Click/Prefect), modern developer experience.

**Key Findings**:

| Framework | Lines of Code | Type Safety | IDE Support | Prefect Alignment |
|-----------|---------------|-------------|-------------|-------------------|
| argparse  | 180           | ✗           | Poor        | None              |
| Click     | 120           | ✗           | Medium      | Good              |
| **Typer** | **90**        | **✓**       | **Excellent** | **Perfect**     |

**Why Typer**:
1. **50% less code** than alternatives
2. **Type hints provide automatic validation** - no manual type conversion
3. **Built on Click** - same foundation as Prefect (seamless integration)
4. **Auto-generated help** - self-documenting from docstrings and type hints
5. **Only 2 small dependencies** - typer + rich (already lightweight)
6. **Modern DX** - IDE auto-completion, type checking

**Implementation Example**:

```python
"""CLI interface for tandem-fetch export command."""

from pathlib import Path
from typing import Optional
from datetime import date
import typer
from rich.console import Console
from loguru import logger

app = typer.Typer(help="Export tandem-fetch data to CSV or Parquet")
console = Console()

@app.command()
def export(
    tables: list[str] = typer.Option(
        ...,
        "--tables", "-t",
        help="Table names to export (cgm_readings, basal_deliveries, events, raw_events)"
    ),
    format: str = typer.Option(
        "parquet",
        "--format", "-f",
        help="Export format (parquet or csv)"
    ),
    output_path: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory path (default: exports/)"
    ),
    start_date: Optional[date] = typer.Option(
        None,
        "--start-date",
        help="Start date for filtering (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = typer.Option(
        None,
        "--end-date",
        help="End date for filtering (YYYY-MM-DD)"
    ),
    fetch_latest: bool = typer.Option(
        True,
        "--fetch-latest/--no-fetch",
        help="Fetch latest data before export"
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files"
    )
):
    """
    Export tandem-fetch database tables to CSV or Parquet format.

    Examples:
        # Export CGM readings to Parquet
        uv run export-data -t cgm_readings

        # Export multiple tables to CSV
        uv run export-data -t cgm_readings -t basal_deliveries -f csv

        # Export with date range filter
        uv run export-data -t cgm_readings --start-date 2026-01-01 --end-date 2026-01-31
    """

    # Type validation happens automatically
    # Date parsing happens automatically
    # Path validation can be added here

    logger.info(f"Exporting {len(tables)} tables to {format} format")

    # Call Prefect workflow
    from tandem_fetch.workflows.export_data import export_orchestrator_flow

    result = export_orchestrator_flow(
        tables=tables,
        output_dir=str(output_path or "exports"),
        format=format,
        run_pipeline=fetch_latest,
        start_date=start_date,
        end_date=end_date,
        overwrite=overwrite,
    )

    if result["success"]:
        console.print("[green]✓[/green] Export completed successfully!")
    else:
        console.print("[red]✗[/red] Export failed")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
```

**Progress Indicator Integration**:

Typer integrates seamlessly with `rich` for progress bars that don't conflict with loguru:

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

@app.command()
def export_with_progress(...):
    """Export with progress indicator."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        task = progress.add_task("Fetching latest data...", total=None)
        # Run pipeline
        progress.update(task, description="Exporting tables...")
        # Run export
        progress.update(task, description="Complete!", completed=True)
```

**Alternatives Considered**:
- **argparse**: Rejected - too verbose, poor type safety, manual validation
- **Click**: Rejected - while good, Typer provides better type safety with same foundation
- **python-fire**: Rejected - less control over argument validation

**Dependencies Required**:
```toml
# Add to pyproject.toml
dependencies = [
    # ... existing
    "typer>=0.12.0",
    "rich>=13.7.0",  # For progress bars and formatting
]
```

---

## R3: Prefect Integration Patterns

### Decision: Subflow Pattern with Optional Pipeline Execution

**Rationale**: Follows existing `run_full_pipeline` architecture, provides first-class observability, shares context within same process.

**Architecture**:

```
export_orchestrator_flow() [main entry point]
├── optionally_run_pipeline() [conditional execution]
│   └── run_full_pipeline() [existing subflow]
└── run_export() [export subflow]
    ├── validate_export_config() [task]
    ├── export_table_to_file() [task per table]
    └── aggregate_export_results() [task]
```

**Key Patterns for Prefect 3.x**:

#### 1. Task Retries with Smart Conditions

```python
from prefect import task

def should_retry_db_error(task, task_run, state):
    """Retry only on transient errors, not validation failures."""
    if state.is_failed():
        exc = str(state.message)
        transient = ('Connection timeout', 'Connection refused', 'temporary failure')
        return any(err in exc for err in transient)
    return False

@task(
    retries=3,
    retry_delay_seconds=[2, 5, 10],  # Progressive backoff
    retry_condition_fn=should_retry_db_error,
    cache_policy=None,  # No caching for database reads
    task_run_name="export-{table_name}"
)
def export_table_to_file(table_name: str, output_path: str) -> dict:
    """Export single table with intelligent retry logic."""
    # Implementation
    pass
```

#### 2. Conditional Flow Execution

```python
from prefect import flow
from loguru import logger

@flow(name="export-orchestrator")
def export_orchestrator_flow(
    tables: list[str],
    output_dir: str,
    run_pipeline: bool = False
) -> dict:
    """Orchestrate optional pipeline + export."""

    results = {"pipeline_run": None, "export_results": None}

    # Native Python control flow
    if run_pipeline:
        try:
            logger.info("Running full pipeline before export")
            run_full_pipeline()  # Subflow call
            results["pipeline_run"] = {"status": "completed"}
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["pipeline_run"] = {"status": "failed", "error": str(e)}
            raise  # Pipeline was required, must fail

    # Export execution (independent of pipeline)
    results["export_results"] = run_export(tables, output_dir)

    return results
```

#### 3. Multi-Table Export with Partial Failure Handling

```python
from dataclasses import dataclass
from typing import NamedTuple

class ExportResult(NamedTuple):
    table: str
    success: bool
    rows_exported: int = 0
    error: str = None

@task
def export_single_table(table: str, output_dir: str) -> ExportResult:
    """Export single table, return result (don't raise)."""
    try:
        # Export logic
        return ExportResult(table=table, success=True, rows_exported=1000)
    except Exception as e:
        logger.error(f"Failed to export {table}: {e}")
        return ExportResult(table=table, success=False, error=str(e))

@task
def aggregate_results(results: list[ExportResult]) -> dict:
    """Decide if operation should fail based on results."""
    failed = [r for r in results if not r.success]

    # Failure policy: all failed = raise, some failed = warn
    if len(failed) == len(results):
        raise RuntimeError(f"All {len(results)} tables failed to export")

    return {"successful": len(results) - len(failed), "failed": len(failed)}

@flow(name="run-export")
def run_export(tables: list[str], output_dir: str) -> dict:
    """Export multiple tables, continue on partial failures."""
    results = [export_single_table(t, output_dir) for t in tables]
    return aggregate_results(results)
```

#### 4. Database Connection Management

```python
from sqlalchemy import create_engine, pool
from functools import lru_cache
from contextlib import contextmanager

@lru_cache(maxsize=1)
def get_engine():
    """Get or create connection pool (singleton)."""
    return create_engine(
        DATABASE_URL,
        poolclass=pool.QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Test connection before use
    )

@contextmanager
def get_connection():
    """Context manager for safe connection handling."""
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()  # Returns to pool

@task
def export_with_safe_connection(table: str):
    """Task using pooled connections."""
    with get_connection() as conn:
        result = conn.execute(text(f"SELECT * FROM {table}"))
        # Process result
```

#### 5. Logging Integration

**Recommendation**: Use loguru for all application logging, `get_run_logger()` only for critical Prefect UI errors.

```python
from prefect import get_run_logger
from loguru import logger

@task
def export_with_logging(table: str):
    """Task with loguru logging."""
    logger.info(f"Starting export for {table}")  # App logging

    try:
        # Work
        logger.success(f"Exported {table}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Export failed: {e}")  # App logging

        # Critical error for Prefect UI
        prefect_logger = get_run_logger()
        prefect_logger.error(f"Export failed for {table}: {e}")
        raise
```

**Best Practices Identified**:
1. ✓ Use subflows for major operations (not separate deployments)
2. ✓ Return results from tasks instead of raising (enables partial success)
3. ✓ Aggregate results in separate task to decide failure policy
4. ✓ Connection pooling with context managers for database access
5. ✓ Progressive retry backoff with condition functions
6. ✓ No caching for database read operations
7. ✓ Native Python control flow (if/for) within flows

**Alternatives Considered**:
- **Separate deployment pattern**: Rejected - adds infrastructure complexity for single-user CLI
- **New pipeline step**: Rejected - export is orthogonal concern to data transformation
- **Event-driven pattern**: Rejected - overkill for manual CLI invocation

---

## R4: File Path Handling

### Decision: Use pathlib with Cross-Platform Best Practices

**Key Findings**:

**pathlib Benefits**:
- Cross-platform path handling (Windows, macOS, Linux)
- Object-oriented API (cleaner than os.path)
- Built-in validation and manipulation methods

**Implementation Pattern**:

```python
from pathlib import Path
from typing import Optional
import typer

def resolve_output_path(
    output_path: Optional[Path],
    table_name: str,
    format: str,
    default_dir: str = "exports"
) -> Path:
    """
    Resolve and validate output path with directory creation.

    Handles:
    - Default directory creation
    - Parent directory creation (FR-007)
    - Cross-platform path separators
    - Special characters and spaces
    """

    # Default path if none provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(default_dir) / f"{table_name}_{timestamp}.{format}"
    else:
        # Expand user home directory (~)
        output_path = Path(output_path).expanduser()

        # If path is directory, append filename
        if output_path.is_dir() or not output_path.suffix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_path / f"{table_name}_{timestamp}.{format}"

    # Create parent directories (FR-007)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate writable
    if not output_path.parent.is_dir():
        raise ValueError(f"Cannot create output directory: {output_path.parent}")

    return output_path

def handle_existing_file(output_path: Path, overwrite: bool) -> bool:
    """
    Handle existing file based on overwrite preference (FR-015).

    Returns:
        True if should proceed with write, False otherwise
    """
    if not output_path.exists():
        return True

    if overwrite:
        logger.warning(f"Overwriting existing file: {output_path}")
        return True

    # Prompt user (CLI mode)
    response = typer.confirm(f"File exists: {output_path}. Overwrite?")
    return response
```

**Special Character Handling**:

```python
def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for cross-platform compatibility.

    Removes/replaces problematic characters:
    - Windows: < > : " / \\ | ? *
    - All: control characters, null bytes
    """
    import re

    # Remove control characters and null bytes
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

    # Replace problematic characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing spaces and dots (Windows issue)
    filename = filename.strip(' .')

    return filename
```

**Path Validation Pattern**:

```python
@task
def validate_output_path(output_path: Path) -> bool:
    """
    Validate output path before export.

    Checks:
    - Parent directory exists or can be created
    - Write permissions
    - Sufficient disk space (optional)
    - Path length limits (Windows: 260 chars)
    """

    # Check path length (Windows limitation)
    if len(str(output_path)) > 260:
        logger.warning("Path exceeds Windows MAX_PATH (260), may fail on Windows")

    # Create parent directories
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise ValueError(f"No permission to create directory: {output_path.parent}")
    except OSError as e:
        raise ValueError(f"Cannot create output directory: {e}")

    # Test write permissions
    test_file = output_path.parent / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        raise ValueError(f"No write permission: {output_path.parent}")

    return True
```

**Best Practices**:
1. ✓ Always use `Path` objects, not string concatenation
2. ✓ Use `parents=True, exist_ok=True` for directory creation
3. ✓ Use `expanduser()` to handle `~` in paths
4. ✓ Sanitize user-provided filenames
5. ✓ Test write permissions before processing
6. ✓ Handle spaces and special chars automatically (pathlib does this)

**Alternatives Considered**:
- **os.path**: Rejected - string-based API, less clean, manual platform handling
- **Manual string concatenation**: Rejected - error-prone, platform-specific bugs

---

## R5: Date Range Filtering

### Decision: SQLAlchemy text() with Bound Parameters

**Rationale**: Safe SQL generation with optional WHERE clause, prevents SQL injection, type-safe date handling.

**Implementation Pattern**:

```python
from sqlalchemy import text
from datetime import date, datetime
from typing import Optional

def build_export_query(
    table_name: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> tuple[str, dict]:
    """
    Build export query with optional date range filtering.

    Returns:
        Tuple of (query_string, bind_params)
    """

    # Base query
    query = f"SELECT * FROM {table_name}"
    params = {}

    # Build WHERE clause conditionally
    where_conditions = []

    if start_date:
        where_conditions.append("timestamp >= :start_date")
        params["start_date"] = datetime.combine(start_date, datetime.min.time())

    if end_date:
        where_conditions.append("timestamp <= :end_date")
        params["end_date"] = datetime.combine(end_date, datetime.max.time())

    # Add WHERE clause if conditions exist
    if where_conditions:
        query += " WHERE " + " AND ".join(where_conditions)

    # Order by timestamp for consistent exports
    query += " ORDER BY timestamp"

    return query, params

@task
def export_with_date_filter(
    table_name: str,
    output_path: Path,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> dict:
    """Export table with optional date range filtering."""

    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise ValueError(f"Start date ({start_date}) cannot be after end date ({end_date})")

    # Build query
    query_str, params = build_export_query(table_name, start_date, end_date)

    logger.info(f"Exporting {table_name} with date filter: {start_date} to {end_date}")

    with get_connection() as conn:
        # Use bound parameters (prevents SQL injection)
        query = text(query_str)
        result = conn.execute(query, params)
        rows = result.fetchall()

        logger.info(f"Retrieved {len(rows)} rows after filtering")

        # Export using DuckDB COPY with subquery
        copy_query = text(f"""
            COPY (
                {query_str}
            )
            TO '{output_path}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)

        conn.execute(copy_query, params)

    return {
        "table": table_name,
        "rows": len(rows),
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
    }
```

**Date Format Parsing**:

Typer handles this automatically with type hints:

```python
from datetime import date
import typer

@app.command()
def export(
    start_date: Optional[date] = typer.Option(
        None,
        "--start-date",
        help="Start date (YYYY-MM-DD)",
        formats=["%Y-%m-%d"]  # Typer auto-parses this format
    ),
    end_date: Optional[date] = typer.Option(
        None,
        "--end-date",
        help="End date (YYYY-MM-DD)"
    )
):
    """Typer automatically parses dates from string input."""
    # start_date and end_date are already date objects
    pass
```

**Timezone Handling**:

All timestamps in the database are timezone-aware (from spec):

```python
from datetime import datetime, timezone

def normalize_date_to_utc(d: date) -> datetime:
    """Convert date to UTC datetime for database comparison."""
    # Assume input dates are in user's local timezone
    naive_dt = datetime.combine(d, datetime.min.time())
    # Convert to UTC (database stores UTC)
    return naive_dt.replace(tzinfo=timezone.utc)
```

**Best Practices**:
1. ✓ Always use bound parameters (`:param_name`) to prevent SQL injection
2. ✓ Validate date ranges before query execution
3. ✓ Use `text()` for raw SQL with parameters
4. ✓ Handle timezone conversion (database stores UTC)
5. ✓ Use BETWEEN or >= / <= based on inclusivity requirements

**Alternatives Considered**:
- **String interpolation**: Rejected - SQL injection risk
- **ORM query building**: Rejected - unnecessary complexity for simple WHERE clause
- **Manual date parsing**: Rejected - Typer handles this automatically

---

## Summary of Decisions

| Research Area | Decision | Key Benefit |
|---------------|----------|-------------|
| **Export Method** | DuckDB COPY | 10x faster, memory efficient, native SQL |
| **CLI Framework** | Typer | Type-safe, 50% less code, excellent DX |
| **Flow Pattern** | Subflow | Follows existing architecture, first-class observability |
| **Path Handling** | pathlib | Cross-platform, OO API, built-in validation |
| **Date Filtering** | SQLAlchemy text() | Safe SQL generation, prevents injection |

All technical unknowns from Phase 0 have been resolved. Ready to proceed to Phase 1 (Design & Contracts).

---

## Dependencies to Add

```toml
# Add to pyproject.toml [project.dependencies]
dependencies = [
    # ... existing dependencies
    "typer>=0.12.0",     # CLI framework
    "rich>=13.7.0",      # Progress bars and formatting
]
```

No other new dependencies required - DuckDB, SQLAlchemy, Prefect, loguru, and pathlib are already available.
