"""Export tasks for tandem-fetch data."""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import NamedTuple, Optional

from loguru import logger
from prefect import task
from sqlalchemy import create_engine, text

from tandem_fetch.definitions import DATABASE_URL, EXPORT_DIR

# Valid table names for export
VALID_TABLES = ("cgm_readings", "basal_deliveries", "events", "raw_events")


@dataclass
class ExportConfig:
    """Configuration for an export operation.

    Attributes:
        tables: List of table names to export
        format: Export format (parquet or csv)
        output_dir: Directory where exported files will be written
        start_date: Optional start date for filtering (inclusive)
        end_date: Optional end date for filtering (inclusive)
        fetch_latest: Whether to run pipeline before export
        overwrite: Whether to overwrite existing files
        timestamp: ISO format timestamp when config was created
    """

    tables: list[str]
    format: str = "parquet"
    output_dir: Path = EXPORT_DIR
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    fetch_latest: bool = True
    overwrite: bool = False
    timestamp: str = ""

    def __post_init__(self):
        """Validate and normalize configuration after initialization."""
        # Generate timestamp if not provided
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

        # Ensure output_dir is a Path object
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        # Normalize format to lowercase
        self.format = self.format.lower()

        # Deduplicate tables while preserving order
        seen = set()
        self.tables = [t for t in self.tables if not (t in seen or seen.add(t))]


class ExportResult(NamedTuple):
    """Result of a single table export operation.

    Attributes:
        table: Name of table that was exported
        success: Whether export completed successfully
        rows_exported: Number of rows written to file
        output_path: Full path to exported file
        duration: Export duration in seconds
        error: Error message if export failed
        file_size_bytes: Size of exported file in bytes
        format: Format of exported file (parquet/csv)
    """

    table: str
    success: bool
    rows_exported: int = 0
    output_path: Optional[Path] = None
    duration: float = 0.0
    error: Optional[str] = None
    file_size_bytes: int = 0
    format: str = "parquet"


@dataclass
class ExportSummary:
    """Aggregated results from multiple table exports.

    Attributes:
        timestamp: When export operation completed
        config: Configuration used for export
        results: Individual table export results
        total_rows: Sum of rows_exported across all successful exports
        total_duration: Total duration in seconds
        success_count: Number of successful exports
        failure_count: Number of failed exports
        overall_success: Whether entire operation succeeded
    """

    timestamp: datetime
    config: ExportConfig
    results: list[ExportResult]
    total_rows: int = 0
    total_duration: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    overall_success: bool = False

    def __post_init__(self):
        """Calculate derived values after initialization."""
        self.success_count = sum(1 for r in self.results if r.success)
        self.failure_count = len(self.results) - self.success_count
        self.total_rows = sum(r.rows_exported for r in self.results if r.success)
        self.total_duration = sum(r.duration for r in self.results)
        # Overall success if at least one table exported successfully
        self.overall_success = self.success_count > 0


def validate_table_name(table: str) -> bool:
    """Validate that a table name is in the list of valid tables.

    Args:
        table: Table name to validate

    Returns:
        True if table name is valid

    Raises:
        ValueError: If table name is not valid
    """
    if table not in VALID_TABLES:
        # Provide helpful suggestion if close match
        suggestions = [t for t in VALID_TABLES if table.lower() in t or t in table.lower()]
        if suggestions:
            raise ValueError(
                f"Invalid table name '{table}'. Did you mean '{suggestions[0]}'?\n"
                f"Valid tables: {', '.join(VALID_TABLES)}"
            )
        else:
            raise ValueError(
                f"Invalid table name '{table}'.\nValid tables: {', '.join(VALID_TABLES)}"
            )
    return True


def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> bool:
    """Validate that date range is valid.

    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        True if date range is valid

    Raises:
        ValueError: If end_date is before start_date
    """
    if start_date and end_date and start_date > end_date:
        raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date})")
    return True


def build_export_query(
    table_name: str,
    format: str = "parquet",
    output_path: Optional[Path] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> tuple[str, dict]:
    """Build export query with optional date range filtering.

    Args:
        table_name: Name of table to export
        format: Export format (parquet or csv)
        output_path: Path to output file
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        Tuple of (query_string, bind_params)
    """
    # Build base query
    params = {}

    # Build WHERE clause for date filtering if provided
    where_conditions = []
    if start_date:
        where_conditions.append("timestamp >= :start_date")
        # Convert date to datetime at start of day (00:00:00 UTC) as ISO string
        start_datetime = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        params["start_date"] = start_datetime.isoformat()

    if end_date:
        where_conditions.append("timestamp <= :end_date")
        # Convert date to datetime at end of day (23:59:59 UTC) as ISO string
        end_datetime = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        params["end_date"] = end_datetime.isoformat()

    # Build SELECT query with optional WHERE clause
    select_query = f"SELECT * FROM {table_name}"
    if where_conditions:
        select_query += " WHERE " + " AND ".join(where_conditions)
    select_query += " ORDER BY id"

    # If output_path is provided, build COPY statement
    if output_path:
        # Build COPY options based on format
        if format == "csv":
            copy_options = "FORMAT CSV, HEADER TRUE"
        else:  # parquet
            copy_options = "FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000"

        copy_query = f"""
            COPY ({select_query})
            TO '{output_path}'
            ({copy_options})
        """
        return copy_query, params
    else:
        # Return SELECT query for counting or preview
        return select_query, params


def resolve_output_path(
    table_name: str,
    output_dir: Path,
    format: str,
    timestamp: Optional[str] = None,
) -> Path:
    """Resolve and validate output path with directory creation.

    Args:
        table_name: Name of table being exported
        output_dir: Directory where file will be written
        format: Export format (parquet or csv)
        timestamp: Optional timestamp for filename (defaults to current time)

    Returns:
        Resolved output path

    Raises:
        ValueError: If directory cannot be created or is not writable
    """
    # Ensure output_dir is a Path object
    output_dir = Path(output_dir).expanduser().resolve()

    # Generate filename with timestamp
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        # Parse ISO timestamp and format it
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = dt.strftime("%Y%m%d_%H%M%S")
        except (ValueError, AttributeError):
            # Fallback to current time if parsing fails
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{table_name}_{timestamp}.{format}"
    output_path = output_dir / filename

    # Create parent directories if they don't exist
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        raise ValueError(f"Cannot create output directory '{output_path.parent}': {e}")

    # Verify directory is writable by creating a test file
    test_file = output_path.parent / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        raise ValueError(f"No write permission in directory: {output_path.parent}")

    return output_path


def handle_existing_file(output_path: Path, overwrite: bool) -> bool:
    """Handle existing file based on overwrite preference.

    Args:
        output_path: Path to check for existing file
        overwrite: Whether to overwrite without prompting

    Returns:
        True if should proceed with write, False otherwise
    """
    if not output_path.exists():
        return True

    if overwrite:
        logger.warning(f"Overwriting existing file: {output_path}")
        return True

    # File exists and overwrite is False - this shouldn't happen in non-interactive mode
    # In CLI mode, this would be handled by prompting the user
    logger.warning(f"File exists: {output_path} (overwrite=False, skipping)")
    return False


@task(
    retries=2,
    retry_delay_seconds=[2, 5],
    cache_policy=None,
    task_run_name="validate-export-config",
)
def validate_export_config(config: ExportConfig) -> bool:
    """Validate export configuration before proceeding.

    Args:
        config: Export configuration to validate

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    logger.info(f"Validating export config: {len(config.tables)} table(s)")

    # Validate table names
    for table in config.tables:
        validate_table_name(table)

    # Validate format
    if config.format not in ("parquet", "csv"):
        raise ValueError(f"Invalid format '{config.format}'. Choose 'parquet' or 'csv'.")

    # Validate date range
    validate_date_range(config.start_date, config.end_date)

    # Validate output directory
    output_dir = Path(config.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not output_dir.is_dir():
        raise ValueError(f"Output directory is not writable: {config.output_dir}")

    # Verify tables exist in database
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        for table in config.tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                date_range_info = ""
                if config.start_date or config.end_date:
                    # Get filtered count
                    query, params = build_export_query(
                        table,
                        start_date=config.start_date,
                        end_date=config.end_date,
                    )
                    filtered_result = conn.execute(text(query), params)
                    filtered_count = len(filtered_result.fetchall())
                    date_range_info = f" ({filtered_count} rows after date filtering)"
                logger.info(f"Table '{table}': {count} rows available{date_range_info}")
            except Exception as e:
                raise ValueError(f"Table '{table}' not found: {e}")

    logger.success("Configuration validation passed")
    return True


@task(
    retries=3,
    retry_delay_seconds=[2, 5, 10],
    cache_policy=None,
    task_run_name="export-table-{table_name}",
)
def export_table_to_file(
    table_name: str,
    output_dir: Path,
    format: str = "parquet",
    timestamp: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    overwrite: bool = False,
) -> ExportResult:
    """Export a single table to file using DuckDB COPY.

    Args:
        table_name: Name of table to export
        output_dir: Directory where file will be written
        format: Export format (parquet or csv)
        timestamp: Optional timestamp for filename
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        ExportResult with success/failure status and details
    """
    import time

    start_time = time.time()

    # Build date range info for logging
    date_range_info = ""
    if start_date or end_date:
        if start_date and end_date:
            date_range_info = f" (date range: {start_date} to {end_date})"
        elif start_date:
            date_range_info = f" (from {start_date} onwards)"
        elif end_date:
            date_range_info = f" (up to {end_date})"

    logger.info(f"Exporting table '{table_name}' (format: {format}){date_range_info}")

    try:
        # Resolve output path
        output_path = resolve_output_path(table_name, output_dir, format, timestamp)

        # Check if file exists and handle overwrite
        if not handle_existing_file(output_path, overwrite):
            logger.info(f"Skipping export of {table_name} (file exists, overwrite=False)")
            return ExportResult(
                table=table_name,
                success=True,
                rows_exported=0,
                output_path=output_path,
                duration=0.0,
                error=None,
                file_size_bytes=output_path.stat().st_size if output_path.exists() else 0,
                format=format,
            )

        # Build export query
        query, params = build_export_query(
            table_name,
            format=format,
            output_path=output_path,
            start_date=start_date,
            end_date=end_date,
        )

        # Execute export using DuckDB COPY
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Get row count before export for logging
            count_query, count_params = build_export_query(
                table_name,
                start_date=start_date,
                end_date=end_date,
            )
            result = conn.execute(text(count_query), count_params)
            rows = result.fetchall()
            row_count = len(rows)

            logger.info(f"Retrieved {row_count:,} rows from {table_name}")

            # Execute COPY command
            conn.execute(text(query), params)
            conn.commit()

        # Get file size
        file_size = output_path.stat().st_size if output_path.exists() else 0

        duration = time.time() - start_time

        logger.success(
            f"Exported {table_name}: {row_count:,} rows to {output_path.name} "
            f"({file_size / 1024 / 1024:.2f} MB) in {duration:.2f}s"
        )

        return ExportResult(
            table=table_name,
            success=True,
            rows_exported=row_count,
            output_path=output_path,
            duration=duration,
            error=None,
            file_size_bytes=file_size,
            format=format,
        )

    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Failed to export {table_name}: {error_msg}")

        return ExportResult(
            table=table_name,
            success=False,
            rows_exported=0,
            output_path=output_path if "output_path" in locals() else None,
            duration=duration,
            error=error_msg,
            file_size_bytes=0,
            format=format,
        )


@task(task_run_name="aggregate-export-results")
def aggregate_export_results(
    config: ExportConfig,
    results: list[ExportResult],
) -> ExportSummary:
    """Aggregate export results and determine overall success.

    Args:
        config: Export configuration used
        results: List of individual table export results

    Returns:
        ExportSummary with aggregated statistics

    Raises:
        RuntimeError: If all tables failed to export
    """
    summary = ExportSummary(
        timestamp=datetime.now(timezone.utc),
        config=config,
        results=results,
    )

    logger.info(
        f"Export summary: {summary.success_count} successful, {summary.failure_count} failed"
    )

    # If all tables failed, raise an exception
    if summary.failure_count == len(results):
        error_details = "\n".join([f"  - {r.table}: {r.error}" for r in results if not r.success])
        raise RuntimeError(f"All {len(results)} table(s) failed to export:\n{error_details}")

    # If some failed, log warning but don't fail (partial success)
    if summary.failure_count > 0:
        failed_tables = [r.table for r in results if not r.success]
        logger.warning(
            f"Partial success: {summary.failure_count} table(s) failed: {', '.join(failed_tables)}"
        )

    return summary
