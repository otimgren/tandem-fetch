# CLI Framework Research for tandem-fetch Export Command

## Executive Summary

For the tandem-fetch export command with requirements for multiple table selection, format selection, date range filtering, and progress indicators, **Typer is the recommended choice**.

**Recommendation Rationale:**
1. **Type Safety**: Leverages Python 3.12+ type hints for automatic validation and documentation
2. **Project Alignment**: Complements Prefect (which uses Click internally) without redundancy
3. **Modern Developer Experience**: Auto-completion, auto-generated help, cleaner syntax
4. **Built on Click**: Inherits all Click power while reducing boilerplate by ~50%
5. **Maintainability**: Type hints serve as inline documentation for future developers

---

## 1. argparse (Standard Library)

### Overview
The Python standard library's built-in CLI argument parsing framework.

### Pros
- **No external dependencies** - Already available in Python
- **Stable and well-documented** - Decades of real-world usage
- **Built-in subcommand support** - Via `add_subparsers()`
- **Low memory footprint** - Lightweight execution
- **Wide familiarity** - Most Python developers understand it

### Cons
- **Verbose syntax** - Lots of boilerplate for complex CLIs
- **No type validation** - Manual string-to-type conversion required
- **Poor help generation** - Requires manual help text strings
- **No auto-completion** - Manual setup needed
- **Decorator-unfriendly** - Functional programming style feels dated

### Use Cases
- Simple scripts with 1-3 arguments
- Minimal dependencies required
- Legacy systems where adding dependencies is problematic

### Example Code

```python
import argparse
from datetime import datetime
from pathlib import Path

def export_tables():
    """Export database tables to parquet or CSV format."""
    parser = argparse.ArgumentParser(
        description="Export tables from tandem-fetch database"
    )

    # Multiple tables selection
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=["cgm_readings", "basal_deliveries", "events"],
        required=True,
        help="Tables to export"
    )

    # Format selection
    parser.add_argument(
        "--format",
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format (default: parquet)"
    )

    # Date range filtering
    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.fromisoformat(s).date(),
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=lambda s: datetime.fromisoformat(s).date(),
        help="End date (YYYY-MM-DD)"
    )

    # Optional output path
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("./exports"),
        help="Output directory (default: ./exports)"
    )

    # Boolean flags
    parser.add_argument(
        "--fetch-latest",
        action="store_true",
        help="Fetch latest data before exporting"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files"
    )

    args = parser.parse_args()

    # Manual validation
    if args.start_date and args.end_date:
        if args.start_date > args.end_date:
            parser.error("start-date must be before end-date")

    return args

if __name__ == "__main__":
    args = export_tables()
    print(f"Exporting tables: {args.tables}")
    print(f"Format: {args.format}")
    print(f"Output: {args.output_path}")
```

### Integration with Progress Indicators
```python
import argparse
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--tables", nargs="+", required=True)
args = parser.parse_args()

# Using tqdm with argparse
for table in tqdm(args.tables, desc="Exporting"):
    # Export logic here
    pass
```

---

## 2. Click (Popular Third-Party)

### Overview
Elegant and composable CLI creation library with decorator-based API.

### Pros
- **Decorator-based** - Clean, readable syntax
- **Excellent help generation** - Automatic based on docstrings
- **Built-in progress bars** - `click.progressbar()` for simple use cases
- **File handling** - `click.File` for automatic file management
- **Parameter validation** - Built-in options and callbacks
- **Composable commands** - Easy subcommand and group support
- **Used by industry leaders** - Flask, Pipenv, Pallets projects

### Cons
- **Callback-based progress** - More complex for interactive progress tracking
- **Less type safety** - No automatic validation from type hints
- **Decorator syntax can be verbose** - Multiple stacked decorators
- **Learning curve** - New concepts (Groups, callbacks, context)
- **Not the "right tool" for Prefect** - Prefect already uses Click internally

### Use Cases
- Medium-to-large CLI applications
- Tools requiring complex option handling
- Projects needing multiple command groups
- When you want the battle-tested solution

### Example Code

```python
import click
from datetime import date
from pathlib import Path
from loguru import logger

@click.group()
def export_group():
    """Export tables from tandem-fetch database."""
    pass

@export_group.command()
@click.option(
    "--tables",
    multiple=True,
    type=click.Choice(["cgm_readings", "basal_deliveries", "events"]),
    required=True,
    help="Tables to export"
)
@click.option(
    "--format",
    type=click.Choice(["parquet", "csv"]),
    default="parquet",
    help="Output format"
)
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Start date (YYYY-MM-DD)"
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="End date (YYYY-MM-DD)"
)
@click.option(
    "--output-path",
    type=click.Path(),
    default="./exports",
    help="Output directory"
)
@click.option(
    "--fetch-latest",
    is_flag=True,
    help="Fetch latest data before exporting"
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing files"
)
def tables(tables, format, start_date, end_date, output_path, fetch_latest, overwrite):
    """Export specific tables to parquet or CSV format."""

    # Validation
    if start_date and end_date:
        if start_date > end_date:
            raise click.BadParameter("start-date must be before end-date")

    logger.info(f"Exporting tables: {tables}")
    logger.info(f"Format: {format}")

    # Using Click's progress bar
    with click.progressbar(
        tables,
        label="Exporting tables",
        show_pos=True,
        show_percent=True
    ) as bar:
        for table in bar:
            # Export logic here
            pass

if __name__ == "__main__":
    export_group()
```

### Integration with Progress Indicators
```python
import click
from rich.progress import track
from tqdm import tqdm

@click.command()
@click.option("--tables", multiple=True, required=True)
def cmd(tables):
    # Using Click's built-in progress bar
    with click.progressbar(tables) as bar:
        for table in bar:
            pass

    # Or using rich for fancier output
    for table in track(tables, description="Exporting..."):
        pass

    # Or using tqdm
    for table in tqdm(tables, desc="Exporting"):
        pass
```

---

## 3. Typer (Modern, Type-Hint Based)

### Overview
Modern CLI library built on top of Click, leveraging Python type hints.

### Pros
- **Type-safe** - Automatic validation and documentation from type hints
- **Built on Click** - Inherits all Click power (progress bars, file handling, validation)
- **Minimal boilerplate** - ~50% less code than Click for same functionality
- **Auto-completion** - Automatic shell completion (bash, zsh, fish, powershell)
- **Auto-generated help** - Based on type hints and docstrings
- **Modern Python** - Designed for Python 3.6+, perfect for 3.12
- **IDE support** - Excellent autocomplete and type checking
- **Cleaner syntax** - Function parameters replace decorators

### Cons
- **Smaller community** - Less Stack Overflow answers than Click
- **Dependency overhead** - Still requires Click (but minimal additional overhead)
- **Learning curve** - Different paradigm from Click if familiar with it
- **Slightly newer** - Less battle-tested than Click (though solid track record)

### Use Cases
- **RECOMMENDED FOR tandem-fetch** - Modern codebase with type hints
- CLI tools with strong type validation needs
- Projects valuing developer experience and maintainability
- Teams already using FastAPI (same creator)

### Example Code

```python
import typer
from datetime import date
from typing import Optional, List
from pathlib import Path
from loguru import logger
from rich.progress import track

app = typer.Typer(
    help="Export tables from tandem-fetch database.",
    invoke_without_command=True,
    no_args_is_help=True,
)

# Define choices as a module-level constant for reusability
TABLE_CHOICES = ["cgm_readings", "basal_deliveries", "events"]
FORMAT_CHOICES = ["parquet", "csv"]

@app.command()
def tables(
    tables: List[str] = typer.Option(
        ...,
        "--tables",
        help="Tables to export",
        case_sensitive=False,
    ),
    format: str = typer.Option(
        "parquet",
        "--format",
        help="Output format",
    ),
    start_date: Optional[date] = typer.Option(
        None,
        "--start-date",
        help="Start date (YYYY-MM-DD)",
        formats=["%Y-%m-%d"],
    ),
    end_date: Optional[date] = typer.Option(
        None,
        "--end-date",
        help="End date (YYYY-MM-DD)",
        formats=["%Y-%m-%d"],
    ),
    output_path: Path = typer.Option(
        Path("./exports"),
        "--output-path",
        help="Output directory",
        dir_okay=True,
        file_okay=False,
        writable=True,
    ),
    fetch_latest: bool = typer.Option(
        False,
        "--fetch-latest",
        help="Fetch latest data before exporting",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files",
    ),
):
    """Export specific tables to parquet or CSV format.

    Examples:
        tandem-fetch export tables --tables cgm_readings basal_deliveries --format parquet
        tandem-fetch export tables --tables cgm_readings --start-date 2024-01-01 --end-date 2024-12-31
    """

    # Type validation is automatic, but you can add business logic validation
    if start_date and end_date:
        if start_date > end_date:
            typer.echo(
                typer.style(
                    "Error: start-date must be before end-date",
                    fg=typer.colors.RED,
                    bold=True,
                ),
                err=True,
            )
            raise typer.Exit(code=1)

    logger.info(f"Exporting tables: {tables}")
    logger.info(f"Format: {format}")
    logger.info(f"Date range: {start_date} to {end_date}")

    # Validate table choices at runtime with helpful error message
    invalid_tables = set(tables) - set(TABLE_CHOICES)
    if invalid_tables:
        typer.echo(
            typer.style(
                f"Error: Invalid tables: {invalid_tables}. "
                f"Choose from: {', '.join(TABLE_CHOICES)}",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(code=1)

    # Using rich.progress for better visual feedback (integrates with loguru)
    output_path.mkdir(parents=True, exist_ok=True)

    for table in track(tables, description="[cyan]Exporting tables..."):
        try:
            export_table(
                table,
                format,
                start_date,
                end_date,
                output_path,
                overwrite,
            )
            logger.info(f"✓ Successfully exported {table}")
        except Exception as e:
            logger.error(f"✗ Failed to export {table}: {e}")
            if not typer.confirm("Continue with next table?"):
                raise typer.Exit(code=1)

    typer.secho(
        f"✓ Export complete! Files saved to {output_path}",
        fg=typer.colors.GREEN,
        bold=True,
    )

def export_table(
    table_name: str,
    format: str,
    start_date: Optional[date],
    end_date: Optional[date],
    output_path: Path,
    overwrite: bool,
):
    """Export a single table (placeholder for actual implementation)."""
    # Actual export logic would go here
    output_file = output_path / f"{table_name}.{format}"

    if output_file.exists() and not overwrite:
        raise FileExistsError(f"File exists: {output_file}. Use --overwrite to replace.")

    # Database query and export would happen here
    logger.debug(f"Exporting {table_name} to {output_file}")

@app.callback()
def callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """Callback runs before any command."""
    if verbose:
        logger.enable("tandem_fetch")

if __name__ == "__main__":
    app()
```

### Advanced Typer Features

```python
import typer
from typing import List

app = typer.Typer()

@app.command()
def export(
    tables: List[str] = typer.Argument(
        ...,
        help="Tables to export (positional arguments)"
    ),
    format: str = typer.Option("parquet"),
):
    """Export command with positional arguments."""
    pass

@app.command()
def list_tables():
    """List available tables (subcommand)."""
    pass

# Usage:
# tandem-fetch export cgm_readings basal_deliveries --format csv
# tandem-fetch list-tables
```

### Integration with Progress Indicators

```python
from rich.progress import track
from loguru import logger
import typer

@app.command()
def tables(
    tables: List[str] = typer.Option(..., "--tables"),
):
    """Export tables with progress tracking."""

    # Rich integration (recommended for visual appeal)
    for table in track(tables, description="[cyan]Exporting..."):
        logger.info(f"Processing {table}")
        # Export logic

    # Alternative: Using Click's progress bar (Typer can access it)
    import click
    with click.progressbar(tables, label="Exporting") as bar:
        for table in bar:
            pass
```

---

## 4. Comparison Matrix

| Feature | argparse | Click | Typer |
|---------|----------|-------|-------|
| **Type Safety** | Manual | Manual | Automatic (type hints) |
| **Boilerplate** | High | Medium | Low |
| **Help Generation** | Manual | Automatic | Automatic + detailed |
| **Auto-completion** | Manual | Manual | Automatic |
| **Progress Bars** | Manual (tqdm/rich) | Built-in `progressbar()` | Built-in (via Click) |
| **Subcommands** | `add_subparsers()` | `@click.group()` | `typer.Typer()` with methods |
| **Date/Type Validation** | Manual | Callbacks | Automatic |
| **Decorator Pattern** | No | Yes | Yes (function params instead) |
| **IDE Support** | Poor | Medium | Excellent |
| **Dependencies** | 0 | 1 (Click) | 1 (Click) |
| **Learning Curve** | Low | Medium | Low |
| **Community Size** | Large | Large | Growing |
| **Prefect Alignment** | None | Good (Prefect uses Click) | Excellent (built on Click) |

---

## 5. Progress Indicator Integration

### argparse + tqdm
```python
import argparse
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--tables", nargs="+")
args = parser.parse_args()

for table in tqdm(args.tables, desc="Exporting"):
    # Export logic
    pass
```

### argparse + rich
```python
import argparse
from rich.progress import track

parser = argparse.ArgumentParser()
parser.add_argument("--tables", nargs="+")
args = parser.parse_args()

for table in track(args.tables, description="Exporting..."):
    # Export logic
    pass
```

### Click + Built-in Progress Bar
```python
import click

@click.command()
@click.option("--tables", multiple=True, required=True)
def export(tables):
    with click.progressbar(tables, label="Exporting") as bar:
        for table in bar:
            # Export logic
            pass
```

### Click + Rich (Better Visuals)
```python
import click
from rich.progress import track

@click.command()
@click.option("--tables", multiple=True, required=True)
def export(tables):
    # Rich provides superior visual formatting
    for table in track(tables, description="[cyan]Exporting..."):
        # Export logic
        pass
```

### Typer + Rich (Recommended)
```python
from typing import List
import typer
from rich.progress import track
from loguru import logger

app = typer.Typer()

@app.command()
def tables(tables: List[str] = typer.Option(..., "--tables")):
    """Export tables with rich progress and loguru logging."""
    for table in track(tables, description="[cyan]Exporting..."):
        logger.info(f"Processing {table}")
        # Export logic
        pass
```

### loguru + Rich Integration (Best Practice)
```python
from rich.console import Console
from rich.progress import track
from loguru import logger
import sys

# Configure loguru to not break rich progress bar
console = Console()
logger.remove()  # Remove default handler
logger.add(
    lambda msg: console.print(msg.rstrip()),
    format="{message}",
    level="DEBUG"
)

# Now use rich progress and loguru logging together without conflicts
for item in track(items, description="Processing..."):
    logger.info(f"Working on {item}")
```

---

## 6. Detailed Recommendation for tandem-fetch

### Recommended: **Typer**

**Primary Reasons:**

1. **Type Safety Excellence**
   - Automatic validation of --tables arguments
   - Date parsing built into type system
   - IDE autocomplete for your team

2. **Project Alignment**
   - Already uses Python 3.12 (Typer designed for modern Python)
   - Uses loguru and Prefect (which internally uses Click)
   - Typer sits perfectly on top of Click - no redundancy

3. **Development Experience**
   - Code is ~50% shorter than Click for same functionality
   - Self-documenting with type hints
   - Auto-completion in terminal and IDEs

4. **Maintainability**
   - Type hints serve as inline documentation
   - Future developers understand parameters instantly
   - Easier testing with typed functions

5. **Progress Bar Integration**
   - Rich library integrates seamlessly
   - Loguru compatibility with best-practice handler setup
   - Already used in project dependencies

### Implementation Recommendation

```python
# src/tandem_fetch/export.py
from datetime import date
from pathlib import Path
from typing import List, Optional
import typer
from rich.progress import track
from loguru import logger

app = typer.Typer(help="Export tables from tandem-fetch")

# Define available tables as enum-like constant
AVAILABLE_TABLES = ["cgm_readings", "basal_deliveries", "events", "raw_events"]
FORMATS = ["parquet", "csv"]

@app.command()
def tables(
    tables: List[str] = typer.Option(
        ...,
        "--tables",
        help="Tables to export (e.g., --tables cgm_readings basal_deliveries)",
    ),
    format: str = typer.Option(
        "parquet",
        "--format",
        help="Output format: parquet or csv",
    ),
    start_date: Optional[date] = typer.Option(
        None,
        "--start-date",
        help="Start date filter (YYYY-MM-DD)",
        formats=["%Y-%m-%d"],
    ),
    end_date: Optional[date] = typer.Option(
        None,
        "--end-date",
        help="End date filter (YYYY-MM-DD)",
        formats=["%Y-%m-%d"],
    ),
    output_path: Path = typer.Option(
        Path("./exports"),
        "--output-path",
        help="Output directory",
        dir_okay=True,
        file_okay=False,
    ),
    fetch_latest: bool = typer.Option(
        False,
        "--fetch-latest",
        help="Fetch latest data from API before exporting",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files",
    ),
):
    """Export database tables to parquet or CSV format.

    Examples:
        tandem-fetch export tables \\
            --tables cgm_readings basal_deliveries \\
            --format parquet

        tandem-fetch export tables \\
            --tables cgm_readings \\
            --start-date 2024-01-01 \\
            --end-date 2024-12-31 \\
            --output-path ./my_exports
    """

    # Validate date range
    if start_date and end_date and start_date > end_date:
        typer.secho(
            "Error: start-date must be before end-date",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # Validate table names
    invalid = set(tables) - set(AVAILABLE_TABLES)
    if invalid:
        typer.secho(
            f"Error: Invalid tables: {invalid}\n"
            f"Available: {', '.join(AVAILABLE_TABLES)}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # Validate format
    if format not in FORMATS:
        typer.secho(
            f"Error: Invalid format '{format}'. Use: {', '.join(FORMATS)}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    logger.info(f"Starting export of {len(tables)} table(s)")
    output_path.mkdir(parents=True, exist_ok=True)

    # Export with progress tracking
    for table in track(tables, description="[cyan]Exporting tables"):
        try:
            _export_single_table(
                table,
                format,
                start_date,
                end_date,
                output_path,
                overwrite,
            )
            logger.success(f"✓ Exported {table}")
        except Exception as e:
            logger.error(f"✗ Failed to export {table}: {e}")
            if not typer.confirm("Continue with next table?", default=True):
                raise typer.Exit(code=1)

    typer.secho(
        f"\n✓ Export complete! Files saved to {output_path}",
        fg=typer.colors.GREEN,
        bold=True,
    )

def _export_single_table(
    table_name: str,
    format: str,
    start_date: Optional[date],
    end_date: Optional[date],
    output_path: Path,
    overwrite: bool,
) -> None:
    """Export a single table to the specified format."""
    output_file = output_path / f"{table_name}.{format}"

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"File exists: {output_file}\nUse --overwrite to replace"
        )

    logger.debug(f"Exporting {table_name} to {output_file}")

    # TODO: Implement actual export logic using:
    # - SQLAlchemy queries to fetch from duckdb
    # - Polars for format conversion
    # - Date filtering if start_date/end_date provided

@app.callback()
def callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """Configure global options."""
    if verbose:
        logger.enable("tandem_fetch")
        logger.debug("Verbose logging enabled")

def get_app() -> typer.Typer:
    """Get the export app (for integration with main CLI)."""
    return app

if __name__ == "__main__":
    app()
```

### Integration with Main CLI

```python
# src/tandem_fetch/__init__.py
import typer
from tandem_fetch.export import get_app as get_export_app

main_app = typer.Typer()

@main_app.callback()
def main_callback():
    """tandem-fetch: Diabetes data management and analysis tool."""
    pass

# Add export subcommand group
export_app = get_export_app()
main_app.add_typer(export_app, name="export", help="Export database tables")

def main():
    main_app()

if __name__ == "__main__":
    main()
```

### Usage Examples

```bash
# Basic export
tandem-fetch export tables --tables cgm_readings basal_deliveries

# With format specification
tandem-fetch export tables --tables cgm_readings --format csv

# With date filtering
tandem-fetch export tables \
    --tables cgm_readings \
    --start-date 2024-01-01 \
    --end-date 2024-12-31

# With custom output path
tandem-fetch export tables \
    --tables cgm_readings basal_deliveries \
    --output-path ./my_exports \
    --fetch-latest

# Overwrite existing files
tandem-fetch export tables \
    --tables cgm_readings \
    --overwrite

# Verbose output
tandem-fetch export tables --tables cgm_readings -v

# Auto-completion (after installation)
tandem-fetch export tables --help  # Shows all options
```

---

## 7. Migration Path (If Starting with argparse)

If you want to start simple and migrate later:

```python
# Phase 1: argparse (quick start)
# - Simple to implement
# - Can migrate to Typer later without breaking users

# Phase 2: Typer migration
# - Same CLI interface
# - Better type safety
# - Easier maintenance
```

The good news: Both argparse and Typer can coexist. You can add Typer gradually.

---

## 8. Dependencies to Add

For the recommended Typer approach:

```toml
# pyproject.toml
dependencies = [
    # ... existing dependencies ...
    "typer>=0.12.0",          # Typer already includes Click
    "rich>=13.0.0",           # For beautiful progress bars and formatted output
    # loguru and prefect already present
]
```

**Total new dependencies:** Just Typer (Click is included)
**Dependencies you already have that integrate:** loguru, prefect

---

## 9. Final Recommendation Summary

**Use Typer because:**

1. ✅ Type-safe by default - matches Python 3.12 philosophy
2. ✅ Less boilerplate - clean, readable code
3. ✅ Built on Click - all Click power available
4. ✅ Auto-completion - better user experience
5. ✅ Rich integration - beautiful progress indicators
6. ✅ Loguru compatible - your existing logging works perfectly
7. ✅ Prefect alignment - uses same underlying Click framework
8. ✅ Future-proof - modern Python approach
9. ✅ Developer experience - types serve as documentation

**Typer implementation will:**
- Take ~300-400 LOC for full export command implementation
- Provide automatic --help with examples
- Support shell auto-completion (bash, zsh, fish, powershell)
- Integrate seamlessly with existing Prefect workflows
- Be 50% smaller than equivalent Click code
- Be immediately understandable to any Python developer familiar with type hints
