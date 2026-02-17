# API Contract: Database Connection Helpers

**Feature**: 006-db-connection-helpers
**Date**: 2026-02-16

## Public API

This feature exposes a Python library API (not HTTP/REST). External packages import directly from `tandem_fetch`.

### Module: `tandem_fetch.db`

#### `get_engine(interactive: bool = True) -> Engine`

Returns a SQLAlchemy Engine connected to the local DuckDB database.

**Parameters**:
- `interactive` (bool, default=True): Controls behavior when the database file is missing.
  - `True`: Prompts the user via stdin to fetch data or exit.
  - `False`: Raises `DatabaseNotFoundError` immediately.

**Returns**:
- `sqlalchemy.engine.Engine`: A connected engine to the DuckDB database file.

**Raises**:
- `DatabaseNotFoundError`: When `interactive=False` and the database file does not exist.

**Usage**:
```python
from tandem_fetch.db import get_engine

# Interactive (default) — prompts user if DB missing
engine = get_engine()

# Non-interactive — raises if DB missing
engine = get_engine(interactive=False)

# Use the engine
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM cgm_readings LIMIT 10"))
    rows = result.fetchall()
```

---

#### `DatabaseNotFoundError`

Custom exception for missing database files.

**Inherits**: `FileNotFoundError`

**Attributes**:
- `database_path` (Path): The expected database file path.

**Usage**:
```python
from tandem_fetch.db import get_engine, DatabaseNotFoundError

try:
    engine = get_engine(interactive=False)
except DatabaseNotFoundError as e:
    print(f"Database not found at {e.database_path}")
    print("Run 'run-pipeline' to fetch data.")
```

---

## Import Paths

After implementation, the following imports will be available:

```python
# Primary imports
from tandem_fetch.db import get_engine
from tandem_fetch.db import DatabaseNotFoundError

# Existing imports (unchanged)
from tandem_fetch.db import Base, RawEvent, Event, CgmReading, BasalDelivery
```
