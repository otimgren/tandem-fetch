# tandem-fetch Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-31

## Active Technologies
- Python 3.12 (existing project constraint) + prek (pre-commit hook manager), ruff (formatter/linter), gitleaks (secret detection) (002-precommit-hooks)
- N/A (configuration files only) (002-precommit-hooks)
- Python 3.12 + DuckDB 1.0.0, duckdb-engine 0.17.0, SQLAlchemy 2.0.43, Polars 1.33.0, Prefect 3.4.17, Loguru 0.7.3 (001-tandem-data-export)
- DuckDB local database at `data/tandem.db` (001-tandem-data-export)
- Python 3.12 + SQLAlchemy 2.x, duckdb-engine, Prefect (for pipeline invocation) (006-db-connection-helpers)
- DuckDB local file at `data/tandem.db` (006-db-connection-helpers)

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
- 006-db-connection-helpers: Added Python 3.12 + SQLAlchemy 2.x, duckdb-engine, Prefect (for pipeline invocation)
- 001-tandem-data-export: Added Python 3.12 + DuckDB 1.0.0, duckdb-engine 0.17.0, SQLAlchemy 2.0.43, Polars 1.33.0, Prefect 3.4.17, Loguru 0.7.3
- 004-github-actions-ci: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
