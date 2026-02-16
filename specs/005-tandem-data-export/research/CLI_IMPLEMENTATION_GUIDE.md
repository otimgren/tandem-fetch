# CLI Implementation Guide for tandem-fetch Export Command

Quick reference guide for implementing the export command using Typer.

## Quick Start: Project Setup

### 1. Add Dependencies

```bash
cd /Users/oskari/projects/tandem-fetch
uv add typer rich
```

This adds:
- **typer**: CLI framework (includes Click automatically)
- **rich**: Beautiful terminal output and progress bars

### 2. File Structure

```
src/tandem_fetch/
├── __init__.py              # Main CLI entry point
├── export.py                # Export command implementation
├── cli/
│   ├── __init__.py
│   ├── export_command.py   # Alternative: modular structure
│   └── validators.py        # Validation helpers
```

---

## Implementation Option 1: Simple (Single File)

**File:** `src/tandem_fetch/export.py`

```python
"""Export database tables to parquet or CSV formats."""

from datetime import date
from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger
from rich.progress import track

# Define constants
AVAILABLE_TABLES = ["cgm_readings", "basal_deliveries", "events", "raw_events"]
AVAILABLE_FORMATS = ["parquet", "csv"]

app = typer.Typer(help="Export tandem-fetch database tables")


@app.command()
def tables(
    table_names: List[str] = typer.Option(
        ...,
        "--tables",
        "--table",
        help="Tables to export (space-separated)",
    ),
    format_type: str = typer.Option(
        "parquet",
        "--format",
        "-f",
        help="Output format",
    ),
    start_date: Optional[date] = typer.Option(
        None,
        "--start-date",
        help="Filter by start date (YYYY-MM-DD)",
        formats=["%Y-%m-%d"],
    ),
    end_date: Optional[date] = typer.Option(
        None,
        "--end-date",
        help="Filter by end date (YYYY-MM-DD)",
        formats=["%Y-%m-%d"],
    ),
    output_path: Path = typer.Option(
        Path("./exports"),
        "--output-path",
        "-o",
        help="Output directory",
    ),
    fetch_latest: bool = typer.Option(
        False,
        "--fetch-latest",
        help="Fetch latest data from API first",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-w",
        help="Overwrite existing files",
    ),
):
    """Export tables from tandem-fetch database.

    Examples:

        # Export with defaults (parquet format)
        tandem-fetch export tables --tables cgm_readings

        # Multiple tables with CSV format
        tandem-fetch export tables --tables cgm_readings basal_deliveries --format csv

        # With date filtering
        tandem-fetch export tables --tables cgm_readings \\
            --start-date 2024-01-01 --end-date 2024-12-31

        # Custom output directory
        tandem-fetch export tables --tables cgm_readings --output-path ~/my_exports
    """

    try:
        _validate_inputs(table_names, format_type, start_date, end_date)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting to: {output_path}")

    # Fetch latest data if requested
    if fetch_latest:
        logger.info("Fetching latest data from API...")
        _fetch_latest_data()

    # Export tables with progress
    exported = 0
    failed = 0

    for table_name in track(table_names, description="[cyan]Exporting tables"):
        try:
            _export_table(
                table_name,
                format_type,
                start_date,
                end_date,
                output_path,
                overwrite,
            )
            logger.success(f"✓ {table_name}")
            exported += 1
        except Exception as e:
            logger.error(f"✗ {table_name}: {e}")
            failed += 1

    # Summary
    typer.echo()
    typer.secho(
        f"Export complete: {exported} succeeded, {failed} failed",
        fg=typer.colors.GREEN if failed == 0 else typer.colors.YELLOW,
        bold=True,
    )

    if failed > 0:
        raise typer.Exit(code=1)


def _validate_inputs(
    table_names: List[str],
    format_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
) -> None:
    """Validate user inputs."""
    if not table_names:
        raise ValueError("At least one table name is required")

    invalid_tables = set(table_names) - set(AVAILABLE_TABLES)
    if invalid_tables:
        raise ValueError(
            f"Invalid tables: {invalid_tables}\n"
            f"Available: {', '.join(AVAILABLE_TABLES)}"
        )

    if format_type not in AVAILABLE_FORMATS:
        raise ValueError(
            f"Invalid format: {format_type}\n"
            f"Available: {', '.join(AVAILABLE_FORMATS)}"
        )

    if start_date and end_date and start_date > end_date:
        raise ValueError("start-date must be before end-date")


def _export_table(
    table_name: str,
    format_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    output_path: Path,
    overwrite: bool,
) -> None:
    """Export a single table to the specified format."""
    output_file = output_path / f"{table_name}.{format_type}"

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"File exists: {output_file} (use --overwrite to replace)"
        )

    logger.debug(
        f"Exporting {table_name} to {output_file} "
        f"(dates: {start_date} to {end_date})"
    )

    # TODO: Implement actual export
    # 1. Query database using SQLAlchemy
    # 2. Convert to Polars DataFrame
    # 3. Filter by date range if provided
    # 4. Write to parquet or CSV


def _fetch_latest_data() -> None:
    """Fetch latest data from TConnect API."""
    # TODO: Implement API fetch
    logger.debug("Fetching latest data from TConnect API...")


@app.callback()
def callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """Global options."""
    if verbose:
        logger.enable("tandem_fetch")
        logger.debug("Verbose mode enabled")


if __name__ == "__main__":
    app()
```

**Update main CLI:** `src/tandem_fetch/__init__.py`

```python
"""tandem-fetch: Diabetes data management tool."""

from dataclasses import asdict

import polars as pl
import typer

from tandem_fetch import credentials, tsource
from tandem_fetch.export import app as export_app

# Configure Polars display
pl.Config.set_fmt_str_lengths(1000)
pl.Config.set_tbl_rows(100)

# Create main app
main_app = typer.Typer(
    help="tandem-fetch: Diabetes data management and analysis tool",
    no_args_is_help=True,
)

# Add export subcommand group
main_app.add_typer(export_app, name="export", help="Export database tables")


@main_app.command()
def info():
    """Display information about current configuration."""
    print("Hello from tandem-fetch!")
    creds = credentials.TConnectCredentials.get_credentials()
    api = tsource.TSourceAPI(credentials=creds)
    pumper_info = api.get_pumper_info()
    pump_event_metadata = api.get_pump_event_metadata()
    pump_events = api.get_pump_events()
    print(f"{pumper_info=}")
    print(f"{pump_event_metadata=}")
    print(f"Number of pump events: {len(pump_events)=}")
    print("Last 2 events:")
    print(pump_events[-2:])

    df_events = pl.DataFrame(
        {
            "event_name": [repr(e.NAME) for e in pump_events],
        }
    )
    print(df_events["event_name"].value_counts().sort("count", descending=True))

    event = pump_events[0]
    print(f"First event: {asdict(event)}, name: {event.NAME}")


def main():
    """Main entry point."""
    main_app()


if __name__ == "__main__":
    main()
```

---

## Implementation Option 2: Modular (Better for Large Projects)

**File:** `src/tandem_fetch/cli/__init__.py`

```python
"""CLI commands for tandem-fetch."""

import typer

from tandem_fetch.cli.export_command import app as export_app

# Create main app
main_app = typer.Typer(
    help="tandem-fetch: Diabetes data management tool",
    no_args_is_help=True,
)

# Register subcommand groups
main_app.add_typer(export_app, name="export", help="Export database tables")


def main():
    """Main entry point."""
    main_app()


if __name__ == "__main__":
    main()
```

**File:** `src/tandem_fetch/cli/export_command.py`

```python
"""Export command implementation."""

from datetime import date
from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger
from rich.progress import track

from tandem_fetch.cli.validators import validate_export_inputs
from tandem_fetch.db import get_database_session  # TODO: implement

app = typer.Typer(help="Export database tables")

AVAILABLE_TABLES = ["cgm_readings", "basal_deliveries", "events", "raw_events"]
AVAILABLE_FORMATS = ["parquet", "csv"]


@app.command()
def tables(
    table_names: List[str] = typer.Option(..., "--tables"),
    format_type: str = typer.Option("parquet", "--format", "-f"),
    start_date: Optional[date] = typer.Option(None, "--start-date", formats=["%Y-%m-%d"]),
    end_date: Optional[date] = typer.Option(None, "--end-date", formats=["%Y-%m-%d"]),
    output_path: Path = typer.Option(Path("./exports"), "--output-path", "-o"),
    fetch_latest: bool = typer.Option(False, "--fetch-latest"),
    overwrite: bool = typer.Option(False, "--overwrite", "-w"),
):
    """Export tables from database."""
    try:
        validate_export_inputs(table_names, format_type, start_date, end_date)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    output_path.mkdir(parents=True, exist_ok=True)

    for table_name in track(table_names, description="Exporting"):
        try:
            _do_export(table_name, format_type, start_date, end_date, output_path, overwrite)
            logger.success(f"✓ {table_name}")
        except Exception as e:
            logger.error(f"✗ {table_name}: {e}")


def _do_export(
    table_name: str,
    format_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    output_path: Path,
    overwrite: bool,
) -> None:
    """Export a single table."""
    # Implementation here
    pass
```

**File:** `src/tandem_fetch/cli/validators.py`

```python
"""Input validation for CLI commands."""

from datetime import date
from typing import List, Optional


def validate_export_inputs(
    table_names: List[str],
    format_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
) -> None:
    """Validate export command inputs."""
    AVAILABLE_TABLES = ["cgm_readings", "basal_deliveries", "events", "raw_events"]
    AVAILABLE_FORMATS = ["parquet", "csv"]

    if not table_names:
        raise ValueError("At least one table name is required")

    invalid = set(table_names) - set(AVAILABLE_TABLES)
    if invalid:
        raise ValueError(f"Invalid tables: {invalid}\nAvailable: {', '.join(AVAILABLE_TABLES)}")

    if format_type not in AVAILABLE_FORMATS:
        raise ValueError(f"Invalid format: {format_type}\nAvailable: {', '.join(AVAILABLE_FORMATS)}")

    if start_date and end_date and start_date > end_date:
        raise ValueError("start-date must be before end-date")
```

---

## Testing the CLI

**File:** `tests/test_export_command.py`

```python
"""Tests for export command."""

from datetime import date
from pathlib import Path
from typer.testing import CliRunner
from tandem_fetch.export import app

runner = CliRunner()


def test_export_single_table(tmp_path):
    """Test exporting a single table."""
    result = runner.invoke(
        app,
        [
            "tables",
            "--tables", "cgm_readings",
            "--output-path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "✓" in result.stdout


def test_export_multiple_tables(tmp_path):
    """Test exporting multiple tables."""
    result = runner.invoke(
        app,
        [
            "tables",
            "--tables", "cgm_readings", "basal_deliveries",
            "--output-path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0


def test_export_with_format(tmp_path):
    """Test exporting with specific format."""
    result = runner.invoke(
        app,
        [
            "tables",
            "--tables", "cgm_readings",
            "--format", "csv",
            "--output-path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0


def test_export_with_date_filter(tmp_path):
    """Test exporting with date filtering."""
    result = runner.invoke(
        app,
        [
            "tables",
            "--tables", "cgm_readings",
            "--start-date", "2024-01-01",
            "--end-date", "2024-12-31",
            "--output-path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0


def test_invalid_table_error():
    """Test error on invalid table name."""
    result = runner.invoke(
        app,
        ["tables", "--tables", "invalid_table"],
    )
    assert result.exit_code != 0
    assert "Invalid tables" in result.stdout


def test_invalid_format_error():
    """Test error on invalid format."""
    result = runner.invoke(
        app,
        ["tables", "--tables", "cgm_readings", "--format", "xml"],
    )
    assert result.exit_code != 0


def test_date_order_validation():
    """Test validation of date order."""
    result = runner.invoke(
        app,
        [
            "tables",
            "--tables", "cgm_readings",
            "--start-date", "2024-12-31",
            "--end-date", "2024-01-01",
        ],
    )
    assert result.exit_code != 0
    assert "before" in result.stdout.lower()
```

---

## Integration with Existing Entry Point

**Update pyproject.toml:**

```toml
[project.scripts]
tandem-fetch = "tandem_fetch:main"  # Update to use new CLI
run-pipeline = "tandem_fetch.workflows.backfills.run_full_pipeline:run_full_pipeline"
# ... keep other scripts
```

---

## Progress Bar Customization Examples

### Basic Progress (Default)
```python
from rich.progress import track

for table in track(tables, description="Exporting"):
    export_table(table)
```

### Progress with Spinner
```python
from rich.progress import track, SpinnerColumn

for table in track(
    tables,
    description="[cyan]Exporting",
    transient=True,  # Remove when done
):
    export_table(table)
```

### Detailed Progress
```python
from rich.progress import track, Progress, SpinnerColumn, TimeRemainingColumn

with Progress(
    SpinnerColumn(),
    *track.COLUMNS,
    TimeRemainingColumn(),
) as progress:
    task = progress.add_task("[cyan]Exporting...", total=len(tables))
    for table in tables:
        export_table(table)
        progress.update(task, advance=1)
```

### With loguru Integration
```python
from rich.console import Console
from rich.progress import track
from loguru import logger

# Setup console
console = Console()

# Reconfigure loguru to use rich console
logger.remove()
logger.add(
    lambda msg: console.print(msg.rstrip()),
    format="{message}",
)

# Now both work together
for table in track(tables, description="Exporting"):
    logger.info(f"Processing {table}")
    export_table(table)
```

---

## Common Tasks

### Add a New Export Format
```python
# 1. Update constants
AVAILABLE_FORMATS = ["parquet", "csv", "feather"]  # Add feather

# 2. Update export function
def _export_table(...):
    if format_type == "feather":
        df.write_ipc(output_file)  # Polars feather format
```

### Add Date Range Validation
```python
from dateutil import parser

@app.command()
def tables(
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date (flexible format)",
    ),
):
    """Parse flexible date formats."""
    if start_date:
        parsed_date = parser.parse(start_date).date()
```

### Add Confirmation Prompts
```python
if output_path.exists() and not overwrite:
    if not typer.confirm(f"Overwrite {output_path}?"):
        typer.echo("Aborted")
        raise typer.Exit(code=1)
```

### Environment Variable Support
```python
import os

@app.command()
def tables(
    output_path: Path = typer.Option(
        Path(os.getenv("TANDEM_EXPORT_PATH", "./exports")),
        "--output-path",
    ),
):
    """Support environment variable override."""
    pass
```

---

## Useful Typer Features

### Argument Abbreviation
```python
@app.command()
def tables(
    tables: List[str] = typer.Option(
        ...,
        "--tables",
        "-t",  # Short form
        "--table",  # Alternative long form
    ),
):
```

### Show Default Values
```python
@app.command()
def tables(
    format_type: str = typer.Option(
        "parquet",
        "--format",
        show_default=True,  # Shows "(default: parquet)" in help
    ),
):
```

### Hidden Options
```python
@app.command()
def tables(
    debug: bool = typer.Option(
        False,
        "--debug",
        hidden=True,  # Not shown in --help
    ),
):
```

### Envvars
```python
@app.command()
def tables(
    api_key: str = typer.Option(
        ...,
        envvar="TANDEM_API_KEY",  # Falls back to env var
    ),
):
```

---

## Next Steps

1. **Install dependencies**: `uv add typer rich`
2. **Implement basic export**: Follow Option 1 above
3. **Write tests**: Use `CliRunner` from typer.testing
4. **Add database integration**: Query actual tables
5. **Test progress indicators**: Ensure loguru + rich work well
6. **Document subcommands**: Add more export types (e.g., `export raw`, `export summary`)
