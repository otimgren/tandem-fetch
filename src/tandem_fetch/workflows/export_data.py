"""Export workflow for tandem-fetch data."""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from prefect import flow
from rich.console import Console

from tandem_fetch.definitions import EXPORT_DIR
from tandem_fetch.tasks.export import (
    VALID_TABLES,
    ExportConfig,
    aggregate_export_results,
    export_table_to_file,
    validate_export_config,
)
from tandem_fetch.workflows.backfills.run_full_pipeline import run_full_pipeline


def parse_date_string(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        date object

    Raises:
        ValueError: If date string is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD format.") from e


# Create Typer app and Rich console
app = typer.Typer(help="Export tandem-fetch data to CSV or Parquet")
console = Console()


@flow(name="run-export")
def run_export(config: ExportConfig) -> dict:
    """Execute the export workflow for single or multiple tables.

    Args:
        config: Export configuration

    Returns:
        Dictionary with export results
    """
    logger.info(f"Starting export: {config.tables} → {config.output_dir}")

    # Validate configuration
    validate_export_config(config)

    # Export each table with progress indicator
    results = []
    total_tables = len(config.tables)
    for idx, table in enumerate(config.tables, 1):
        if total_tables > 1:
            logger.info(f"[{idx}/{total_tables}] Exporting {table}...")

        result = export_table_to_file(
            table_name=table,
            output_dir=config.output_dir,
            format=config.format,
            timestamp=config.timestamp,
            start_date=config.start_date,
            end_date=config.end_date,
            overwrite=config.overwrite,
        )
        results.append(result)

    # Aggregate results
    summary = aggregate_export_results(config, results)

    return {
        "success": summary.overall_success,
        "summary": summary,
        "results": results,
    }


@flow(name="export-with-optional-pipeline")
def export_orchestrator_flow(
    tables: list[str],
    output_dir: str,
    format: str = "parquet",
    run_pipeline: bool = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    overwrite: bool = False,
) -> dict:
    """Orchestrate optional pipeline run followed by export.

    Args:
        tables: List of table names to export
        output_dir: Directory to write exported files
        format: Export format (parquet, csv, etc.)
        run_pipeline: Whether to run the full data pipeline first
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        overwrite: Whether to overwrite existing files

    Returns:
        Dictionary with export results and any pipeline results
    """
    logger.info("Export orchestrator started")

    config = ExportConfig(
        tables=tables,
        output_dir=Path(output_dir),
        format=format,
        start_date=start_date,
        end_date=end_date,
        fetch_latest=run_pipeline,
        overwrite=overwrite,
    )

    results = {
        "pipeline_run": None,
        "export_results": None,
        "success": False,
    }

    # Optional pipeline execution
    if run_pipeline:
        try:
            logger.info("Running data pipeline before export")
            run_full_pipeline()
            results["pipeline_run"] = {
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.success("Pipeline completed successfully")
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            results["pipeline_run"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            # Fail the whole operation if pipeline was required
            logger.error("Pipeline was required, aborting export")
            raise

    # Execute export
    try:
        logger.info("Running export")
        export_result = run_export(config)
        results["export_results"] = export_result
        results["success"] = export_result["success"]
        logger.success("Export orchestrator completed successfully")
    except Exception as e:
        logger.error(f"Export failed: {e}")
        results["export_results"] = {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results["success"] = False
        raise

    return results


@app.command()
def export(
    tables: Optional[list[str]] = typer.Option(
        None,
        "--tables",
        "-t",
        help="Table names to export (default: all tables). Available: cgm_readings, basal_deliveries, events, raw_events",
    ),
    format: str = typer.Option(
        "parquet",
        "--format",
        "-f",
        help="Export format (parquet or csv)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory path (default: exports/)",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date for filtering (YYYY-MM-DD)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date",
        help="End date for filtering (YYYY-MM-DD)",
    ),
    fetch_latest: bool = typer.Option(
        True,
        "--fetch-latest/--no-fetch",
        help="Fetch latest data before export",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """
    Export tandem-fetch database tables to CSV or Parquet format.

    Fetches the latest data from Tandem Source and exports it to files for
    analysis. Supports multiple tables, date range filtering, and both Parquet
    (efficient) and CSV (Excel-compatible) formats.

    Examples:

        # Export all tables to Parquet (default)
        export-data

        # Export specific table
        export-data -t cgm_readings

        # Export multiple tables to CSV
        export-data -t cgm_readings -t basal_deliveries --format csv

        # Export with date range filter
        export-data -t cgm_readings --start-date 2026-01-01 --end-date 2026-01-31
    """
    # Default to all tables if none specified
    if tables is None or len(tables) == 0:
        tables = list(VALID_TABLES)
        logger.info("No tables specified, exporting all tables")

    # Set log level based on verbose flag
    if verbose:
        logger.remove()
        logger.add(
            lambda msg: console.print(msg, end=""),
            format="<level>{level: <8}</level> | {message}",
            level="DEBUG",
        )

    # Use default output directory if not specified
    if output_dir is None:
        output_dir = EXPORT_DIR

    # Parse date strings if provided
    parsed_start_date = parse_date_string(start_date) if start_date else None
    parsed_end_date = parse_date_string(end_date) if end_date else None

    logger.info(f"Exporting {len(tables)} table(s) to {format} format")

    try:
        # Run export orchestrator flow
        result = export_orchestrator_flow(
            tables=tables,
            output_dir=str(output_dir),
            format=format,
            run_pipeline=fetch_latest,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            overwrite=overwrite,
        )

        if result["success"]:
            # Display summary
            if result["export_results"]:
                summary = result["export_results"]["summary"]

                # Check if partial success
                if summary.failure_count > 0:
                    console.print("[yellow]⚠️[/yellow]  Export completed with errors")
                else:
                    console.print("[green]✓[/green] Export completed successfully!")

                console.print("\nSummary:")
                console.print(f"  Tables exported:  {summary.success_count}/{len(summary.results)}")
                console.print(f"  Total rows:       {summary.total_rows:,}")
                console.print(
                    f"  Total size:       {sum(r.file_size_bytes for r in summary.results) / 1024 / 1024:.1f} MB"
                )
                console.print(f"  Duration:         {summary.total_duration:.1f}s")
                console.print(f"  Output:           {output_dir}/")

                # Show date range if provided
                if summary.config.start_date or summary.config.end_date:
                    date_range_str = ""
                    if summary.config.start_date and summary.config.end_date:
                        date_range_str = f"{summary.config.start_date} to {summary.config.end_date}"
                    elif summary.config.start_date:
                        date_range_str = f"from {summary.config.start_date} onwards"
                    elif summary.config.end_date:
                        date_range_str = f"up to {summary.config.end_date}"
                    console.print(f"  Date range:       {date_range_str}")

                # List successfully created files
                if summary.success_count > 0:
                    console.print("\n[green]✓[/green] Successfully exported:")
                    for r in summary.results:
                        if r.success and r.output_path:
                            file_size_mb = r.file_size_bytes / 1024 / 1024
                            console.print(
                                f"  • {r.output_path.name} ({file_size_mb:.1f} MB, {r.rows_exported:,} rows)"
                            )

                # List failed exports if any
                if summary.failure_count > 0:
                    console.print("\n[red]✗[/red] Failed to export:")
                    for r in summary.results:
                        if not r.success:
                            console.print(f"  • {r.table}: {r.error}")
                    console.print("\nExit code: 5")
                    raise typer.Exit(code=5)  # Partial success

            raise typer.Exit(code=0)
        else:
            console.print("[red]✗[/red] Export failed")
            raise typer.Exit(code=3)

    except typer.Exit:
        # Re-raise Exit exceptions without logging
        raise
    except ValueError as e:
        # Validation error
        console.print(f"[red]❌ Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        # General error
        console.print(f"[red]❌ Error:[/red] {e}")
        logger.exception("Export failed with exception")
        raise typer.Exit(code=3)


def main():
    """Main entry point for the export-data command."""
    app()


if __name__ == "__main__":
    main()
