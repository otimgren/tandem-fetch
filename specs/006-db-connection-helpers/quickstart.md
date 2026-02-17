# Quickstart: Database Connection Helpers

**Feature**: 006-db-connection-helpers
**Date**: 2026-02-16

## Overview

This feature adds a `get_engine()` helper to `tandem_fetch.db` that external packages can use to connect to the DuckDB database. It validates the database file exists and offers to fetch data if it's missing.

## Quick Usage

```python
from tandem_fetch.db import get_engine

# Get a SQLAlchemy engine (prompts if DB missing)
engine = get_engine()

# Query data
with engine.connect() as conn:
    from sqlalchemy import text
    result = conn.execute(text("SELECT * FROM cgm_readings LIMIT 5"))
    for row in result:
        print(row)
```

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `src/tandem_fetch/db/connect.py` | Create | Connection helper and custom exception |
| `src/tandem_fetch/db/__init__.py` | Modify | Re-export `get_engine` and `DatabaseNotFoundError` |
| `tests/unit/test_db/test_connect.py` | Create | Unit tests for all scenarios |

## Key Design Decisions

1. **Returns Engine, not Connection**: Gives consumers flexibility to create connections or sessions.
2. **Interactive by default**: Matches the primary use case of a developer at a terminal.
3. **Custom exception**: `DatabaseNotFoundError` inherits from `FileNotFoundError` for easy catching.
4. **Uses existing pipeline**: Calls `run_full_pipeline()` directly when user opts to fetch data.

## Testing

```bash
# Run unit tests
pytest tests/unit/test_db/test_connect.py

# Run all tests
pytest
```
