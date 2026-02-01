# tandem-fetch Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-31

## Active Technologies
- Python 3.12 (existing project constraint) + prek (pre-commit hook manager), ruff (formatter/linter), gitleaks (secret detection) (002-precommit-hooks)
- N/A (configuration files only) (002-precommit-hooks)

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
- 002-precommit-hooks: Added Python 3.12 (existing project constraint) + prek (pre-commit hook manager), ruff (formatter/linter), gitleaks (secret detection)

- 001-duckdb-migration: Added Python 3.12 + SQLAlchemy 2.x, duckdb-engine, Prefect, loguru

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
