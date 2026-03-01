# tandem-fetch Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-31

## Active Technologies
- Python 3.12 (existing project constraint) + prek (pre-commit hook manager), ruff (formatter/linter), gitleaks (secret detection) (002-precommit-hooks)
- N/A (configuration files only) (002-precommit-hooks)
- Python 3.12 + DuckDB 1.0.0, duckdb-engine 0.17.0, SQLAlchemy 2.0.43, Polars 1.33.0, Prefect 3.4.17, Loguru 0.7.3 (001-tandem-data-export)
- DuckDB local database at `data/tandem.db` (001-tandem-data-export)
- Python 3.12 + SQLAlchemy 2.x, duckdb-engine, Prefect (for pipeline invocation) (006-db-connection-helpers)
- DuckDB local file at `data/tandem.db` (006-db-connection-helpers)
- Python 3.12 + FastMCP 2.x, SQLAlchemy 2.0.43, duckdb-engine 0.17.0, DuckDB 1.0.0 (007-mcp-server)
- DuckDB local file at `data/tandem.db` (read-only access) (007-mcp-server)
- Python 3.12 + Prefect 3.4.17 (existing), Loguru 0.7.3 (existing), Typer 0.12.0 (existing) (008-continuous-fetch)
- DuckDB local file at `data/tandem.db` (existing) (008-continuous-fetch)

- Python 3.12 + SQLAlchemy 2.x, duckdb-engine, Prefect, loguru (001-duckdb-migration)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 008-continuous-fetch: Added Python 3.12 + Prefect 3.4.17 (existing), Loguru 0.7.3 (existing), Typer 0.12.0 (existing)
- 007-mcp-server: Added Python 3.12 + FastMCP 2.x, SQLAlchemy 2.0.43, duckdb-engine 0.17.0, DuckDB 1.0.0
- 006-db-connection-helpers: Added Python 3.12 + SQLAlchemy 2.x, duckdb-engine, Prefect (for pipeline invocation)

<!-- MANUAL ADDITIONS START -->
- `uv` is used to run code, e.g. `uv run python -c "import prefect; print(prefect.__version__);`
<!-- MANUAL ADDITIONS END -->
