# CLI Framework Quick Reference & Cheat Sheet

Fast lookup guide for implementing the tandem-fetch export command with Typer.

---

## The Recommendation (TL;DR)

```
Use Typer + Rich + loguru

Why?
├─ Type safety (auto validation)
├─ 50% less code than Click
├─ Perfect fit with Prefect/SQLAlchemy/Polars
└─ Beautiful progress bars without conflicts

Timeline: 3 hours
Cost: 2 small dependencies (typer + rich)
Risk: LOW (stable since 2019)
```

---

## Installation

```bash
cd /Users/oskari/projects/tandem-fetch
uv add typer rich
```

That's it. You now have everything needed for a modern CLI.

---

## Minimal Working Example

**File:** `src/tandem_fetch/export.py`

```python
from typing import List, Optional
from datetime import date
import typer
from rich.progress import track
from loguru import logger

app = typer.Typer(help="Export database tables")

@app.command()
def tables(
    tables: List[str] = typer.Option(..., "--tables"),
    format_type: str = typer.Option("parquet", "--format"),
    output_path: str = typer.Option("./exports", "--output-path"),
):
    """Export tables to parquet or CSV."""
    for table in track(tables, description="Exporting"):
        logger.info(f"Processing {table}")
        # TODO: implement export logic
    logger.success("✓ Export complete")

if __name__ == "__main__":
    app()
```

**Usage:**
```bash
python -m tandem_fetch.export tables --tables cgm_readings basal_deliveries
```

---

## Common Options

### Multiple Values
```python
# For --tables cgm_readings basal_deliveries
tables: List[str] = typer.Option(..., "--tables")
```

### Optional Values
```python
# For optional --start-date
start_date: Optional[date] = typer.Option(None, "--start-date", formats=["%Y-%m-%d"])
```

### Default Values
```python
# Default to "parquet"
format_type: str = typer.Option("parquet", "--format")
```

### Boolean Flags
```python
# For --fetch-latest
fetch_latest: bool = typer.Option(False, "--fetch-latest")
```

### Path Types
```python
from pathlib import Path
output_path: Path = typer.Option(Path("./exports"), "--output-path")
```

### Enum/Choice
```python
from typing import Literal
format_type: Literal["parquet", "csv"] = typer.Option("parquet", "--format")
```

### Environment Variable Fallback
```python
import os
api_key: str = typer.Option(..., envvar="TANDEM_API_KEY")
```

### Short Form Aliases
```python
# Allows both -f and --format
format_type: str = typer.Option("parquet", "-f", "--format")
```

---

## Validation Patterns

### Manual Validation
```python
@app.command()
def tables(
    start_date: Optional[date] = typer.Option(None, "--start-date"),
    end_date: Optional[date] = typer.Option(None, "--end-date"),
):
    if start_date and end_date and start_date > end_date:
        typer.secho("Error: start must be before end", fg=typer.colors.RED)
        raise typer.Exit(code=1)
```

### Confirm Before Action
```python
if not typer.confirm("Overwrite existing files?", default=False):
    typer.echo("Aborted")
    raise typer.Exit(code=0)
```

### Show Error Message
```python
typer.secho("Error message", fg=typer.colors.RED, err=True)
raise typer.Exit(code=1)
```

### Show Success Message
```python
typer.secho("Success!", fg=typer.colors.GREEN, bold=True)
```

---

## Progress Bar Patterns

### Basic (1 line)
```python
from rich.progress import track
for item in track(items, description="Processing"):
    do_work(item)
```

### With loguru Integration (Recommended)
```python
from rich.console import Console
from rich.progress import track
from loguru import logger

# One-time setup
console = Console()
logger.remove()
logger.add(lambda msg: console.print(msg.rstrip()), format="{message}")

# Then use together
for item in track(items, description="Processing"):
    logger.info(f"Doing {item}")
    do_work(item)
```

### Transient (Disappears When Done)
```python
for item in track(items, description="Processing", transient=True):
    do_work(item)
```

### Custom Style
```python
for item in track(items, description="[cyan]Processing [bold]data"):
    do_work(item)
```

### Manual Progress
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Exporting...", total=len(tables))
    for table in tables:
        export_table(table)
        progress.update(task, advance=1)
```

---

## Testing

### Setup
```python
from typer.testing import CliRunner
from tandem_fetch.export import app

runner = CliRunner()
```

### Test Basic Command
```python
def test_export():
    result = runner.invoke(app, ["tables", "--tables", "cgm_readings"])
    assert result.exit_code == 0
    assert "✓" in result.stdout
```

### Test with Options
```python
def test_export_with_format():
    result = runner.invoke(app, [
        "tables",
        "--tables", "cgm_readings",
        "--format", "csv"
    ])
    assert result.exit_code == 0
```

### Test Error Cases
```python
def test_invalid_table():
    result = runner.invoke(app, ["tables", "--tables", "invalid"])
    assert result.exit_code != 0
    assert "Invalid" in result.stdout
```

### Test with Temp Directory
```python
from pathlib import Path
import tempfile

def test_export_to_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, [
            "tables",
            "--tables", "cgm_readings",
            "--output-path", tmpdir
        ])
        assert result.exit_code == 0
        assert (Path(tmpdir) / "cgm_readings.parquet").exists()
```

---

## Integration with Main CLI

### Add Export Subcommand
```python
# src/tandem_fetch/__init__.py
import typer
from tandem_fetch.export import app as export_app

main_app = typer.Typer(help="tandem-fetch CLI")

# Register export as subcommand
main_app.add_typer(export_app, name="export")

def main():
    main_app()
```

### Usage
```bash
tandem-fetch export tables --tables cgm_readings
```

---

## Common Mistakes and Solutions

### ❌ Using str instead of List[str]
```python
# WRONG - only accepts one table
tables: str = typer.Option(...)

# RIGHT - accepts multiple tables
tables: List[str] = typer.Option(...)
```

### ❌ Forgetting imports
```python
# WRONG - typer not imported
def tables(items: List[str] = typer.Option(...)):

# RIGHT
import typer
from typing import List
def tables(items: List[str] = typer.Option(...)):
```

### ❌ Not handling Optional dates
```python
# WRONG - crashes if no date provided
start_date: date = typer.Option(None, "--start-date")

# RIGHT - Optional handles None
start_date: Optional[date] = typer.Option(None, "--start-date")
```

### ❌ Progress bar breaks loguru output
```python
# WRONG - output breaks progress bar
from loguru import logger
for item in track(items):
    logger.info(f"Processing {item}")

# RIGHT - configure loguru first
console = Console()
logger.remove()
logger.add(lambda msg: console.print(msg.rstrip()))
for item in track(items):
    logger.info(f"Processing {item}")  # Now works!
```

### ❌ Not validating date order
```python
# WRONG - allows start > end
start_date: date = typer.Option(None, "--start-date")
end_date: date = typer.Option(None, "--end-date")

# RIGHT - validate in function
if start_date and end_date and start_date > end_date:
    raise typer.Exit(code=1)
```

---

## Useful Type Annotations

```python
from typing import List, Optional, Literal
from datetime import date
from pathlib import Path

# Multiple values
tables: List[str] = typer.Option(...)

# Optional values
start_date: Optional[date] = typer.Option(None, "--start-date")

# Choice/Enum
format_type: Literal["parquet", "csv"] = typer.Option("parquet")

# File paths
output_path: Path = typer.Option(Path("./exports"))

# Boolean flags
overwrite: bool = typer.Option(False, "--overwrite")

# Required value
api_key: str = typer.Option(..., envvar="API_KEY")
```

---

## Color and Styling

```python
import typer

# Colors
typer.colors.RED
typer.colors.GREEN
typer.colors.YELLOW
typer.colors.CYAN
typer.colors.BRIGHT_WHITE
typer.colors.BRIGHT_CYAN

# Usage
typer.secho("Success!", fg=typer.colors.GREEN)
typer.secho("Error!", fg=typer.colors.RED, bold=True)
typer.secho("Warning", fg=typer.colors.YELLOW, dim=True)

# Echo with error flag
typer.echo("This goes to stderr", err=True)
```

---

## Logging Integration

```python
from loguru import logger

# Basic logging
logger.debug("Debug info")
logger.info("Information")
logger.success("✓ Success")
logger.warning("⚠ Warning")
logger.error("✗ Error")

# With rich progress (setup once)
from rich.console import Console
console = Console()
logger.remove()
logger.add(lambda msg: console.print(msg.rstrip()))

# Then use everywhere
for item in track(items):
    logger.info(f"Processing {item}")
```

---

## File Handling

```python
from pathlib import Path

# Create output directory if needed
output_path = Path("./exports")
output_path.mkdir(parents=True, exist_ok=True)

# Check if file exists
output_file = output_path / "data.parquet"
if output_file.exists():
    if not overwrite:
        raise FileExistsError(f"{output_file} exists")

# Write using Polars
import polars as pl
df.write_parquet(str(output_file))
df.write_csv(str(output_file))
```

---

## Complete Production Example

```python
from datetime import date
from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger
from rich.console import Console
from rich.progress import track

app = typer.Typer(help="Export tandem-fetch database")

AVAILABLE_TABLES = ["cgm_readings", "basal_deliveries", "events"]
AVAILABLE_FORMATS = ["parquet", "csv"]

@app.command()
def tables(
    table_names: List[str] = typer.Option(..., "--tables"),
    format_type: str = typer.Option("parquet", "--format"),
    start_date: Optional[date] = typer.Option(None, "--start-date", formats=["%Y-%m-%d"]),
    end_date: Optional[date] = typer.Option(None, "--end-date", formats=["%Y-%m-%d"]),
    output_path: Path = typer.Option(Path("./exports"), "--output-path"),
    overwrite: bool = typer.Option(False, "--overwrite"),
):
    """Export tables to parquet or CSV format."""

    # Validation
    invalid = set(table_names) - set(AVAILABLE_TABLES)
    if invalid:
        typer.secho(f"Invalid tables: {invalid}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if format_type not in AVAILABLE_FORMATS:
        typer.secho(f"Invalid format: {format_type}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    if start_date and end_date and start_date > end_date:
        typer.secho("start-date must be before end-date", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # Setup
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting to: {output_path}")

    # Export
    exported = 0
    for table in track(table_names, description="[cyan]Exporting"):
        try:
            output_file = output_path / f"{table}.{format_type}"
            if output_file.exists() and not overwrite:
                logger.warning(f"Skipping {table} (exists)")
                continue

            # TODO: Implement actual export
            logger.debug(f"Exporting {table} to {output_file}")
            logger.success(f"✓ {table}")
            exported += 1
        except Exception as e:
            logger.error(f"✗ {table}: {e}")

    # Summary
    typer.secho(f"\n✓ Exported {exported} table(s)", fg=typer.colors.GREEN, bold=True)

@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Global options."""
    if verbose:
        logger.enable("tandem_fetch")

if __name__ == "__main__":
    # Configure loguru for rich compatibility (one-time setup)
    console = Console()
    logger.remove()
    logger.add(
        lambda msg: console.print(msg.rstrip()),
        format="{message}",
    )

    app()
```

---

## Git Integration

After implementation, you might want to:

```bash
# Stage the new files
git add src/tandem_fetch/export.py
git add tests/test_export_command.py

# Commit with proper message
git commit -m "feat: Add CLI export command with Typer"

# Or if modifying existing files
git commit -m "feat: Integrate Typer CLI for table exports"
```

---

## Useful Commands

```bash
# Show help
tandem-fetch export tables --help

# Export with defaults
tandem-fetch export tables --tables cgm_readings

# Multiple tables
tandem-fetch export tables --tables cgm_readings basal_deliveries

# Custom format and path
tandem-fetch export tables \
    --tables cgm_readings \
    --format csv \
    --output-path ./my_exports

# With date filtering
tandem-fetch export tables \
    --tables cgm_readings \
    --start-date 2024-01-01 \
    --end-date 2024-12-31

# Verbose output
tandem-fetch export tables --tables cgm_readings -v

# Overwrite existing files
tandem-fetch export tables --tables cgm_readings --overwrite
```

---

## Where to Go for More Info

| Question | Document |
|----------|----------|
| Why Typer? | CLI_RESEARCH_SUMMARY.md |
| How to implement? | CLI_IMPLEMENTATION_GUIDE.md |
| See all options? | CLI_FRAMEWORK_RESEARCH.md |
| Visual comparison? | CLI_DECISION_TREE.md |
| Need an overview? | CLI_RESEARCH_INDEX.md |

---

## Next Steps

1. **Create the file:**
   ```bash
   touch src/tandem_fetch/export.py
   ```

2. **Copy the "Complete Production Example"** from above

3. **Update `__init__.py`:**
   ```python
   from tandem_fetch.export import app as export_app
   main_app.add_typer(export_app, name="export")
   ```

4. **Test it:**
   ```bash
   tandem-fetch export tables --help
   ```

5. **Implement the actual export logic** in the placeholder

Done! You now have a professional CLI.
