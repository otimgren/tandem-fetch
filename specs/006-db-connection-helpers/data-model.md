# Data Model: Database Connection Helpers

**Feature**: 006-db-connection-helpers
**Date**: 2026-02-16

## Entities

This feature does not introduce new database tables or persistent entities. It provides access to the existing schema.

### Existing Entities (read access provided)

| Entity | Table | Description |
|--------|-------|-------------|
| RawEvent | `raw_events` | Unprocessed API responses stored as JSON |
| Event | `events` | Structured event records parsed from raw data |
| CgmReading | `cgm_readings` | Blood glucose measurements from CGM sensor |
| BasalDelivery | `basal_deliveries` | Insulin basal rate delivery records |

### New Types (non-persistent)

#### DatabaseNotFoundError

A custom exception raised when the database file does not exist and the caller is in non-interactive mode.

- Inherits from: `FileNotFoundError`
- Attributes:
  - `database_path` (Path): The expected path to the database file
  - `message` (str): Human-readable error with instructions

#### get_engine Function Signature

```
get_engine(interactive: bool = True) -> Engine
```

- **Input**: `interactive` flag controlling missing-database behavior
- **Output**: SQLAlchemy `Engine` connected to the DuckDB database file
- **Side effects**: May trigger full data pipeline if database is missing and user consents
- **Exceptions**: `DatabaseNotFoundError` if database missing and `interactive=False`

## State Transitions

```
[Call get_engine()]
       │
       ├── DB file exists → Return Engine ✓
       │
       └── DB file missing
               │
               ├── interactive=True
               │       │
               │       ├── User says "yes" → Run pipeline → Return Engine ✓
               │       │
               │       └── User says "no" → Return None (with message)
               │
               └── interactive=False → Raise DatabaseNotFoundError
```

## Relationships

No new entity relationships are introduced. The connection helper provides access to the existing entity graph:

```
raw_events (1) ──→ (1) events (1) ──→ (0..1) cgm_readings
                                  (1) ──→ (0..1) basal_deliveries
```
