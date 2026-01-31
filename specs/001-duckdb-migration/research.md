# Research: DuckDB Migration

**Date**: 2026-01-31
**Feature**: 001-duckdb-migration

## Decision Summary

| Topic | Decision | Rationale |
|-------|----------|-----------|
| SQLAlchemy Dialect | `duckdb-engine` | Official, well-maintained, supports SQLAlchemy 2.0 |
| JSON Support | Native DuckDB JSON type | Works with `sqlalchemy.types.JSON` |
| DateTime/Timezone | `TIMESTAMPTZ` supported | Stores UTC microseconds, timezone for display only |
| Migration Approach | Keep Alembic with custom impl class | Familiar workflow, minimal code change |
| Auto-increment | Use `Sequence()` | DuckDB lacks SERIAL, sequences work |
| Connection String | `duckdb:///path/to/file.db` | Relative path with 3 slashes |

## Research Findings

### 1. SQLAlchemy Dialect Package

**Package**: `duckdb-engine` (PyPI) / import as `duckdb_engine`

- Current Version: 0.17.0
- Python Support: 3.9 - 3.13
- SQLAlchemy Support: 1.4+ and 2.0
- Repository: github.com/Mause/duckdb_engine

**Installation**: Add to pyproject.toml dependencies:
```toml
"duckdb-engine>=0.17.0"
```

### 2. JSON Column Type

DuckDB has native JSON support:
- `JSON` logical type validates JSON data
- Stored as VARCHAR internally with validation
- JSON extension auto-loads in recent versions
- Compatible with `sqlalchemy.types.JSON`

**No code changes needed** for existing JSON columns.

### 3. DateTime with Timezone

DuckDB supports `TIMESTAMPTZ`:
- Stores microseconds since Unix epoch as INT64
- Does NOT store actual timezone (unlike PostgreSQL)
- Timezone affects display/operations, not storage
- `DateTime(timezone=True)` works in SQLAlchemy

**Consideration**: All timestamps effectively stored as UTC. This is fine for this project since we only care about the timestamp values, not original timezones.

### 4. SQLAlchemy 2.0 Compatibility

Fully supported in duckdb-engine 0.17.0. No issues with current SQLAlchemy version in project.

### 5. Connection String Format

```python
# Relative path (3 slashes) - recommended for portability
engine = create_engine('duckdb:///data/tandem.db')

# Absolute path (4 slashes)
engine = create_engine('duckdb:////Users/oskari/projects/tandem-fetch/data/tandem.db')

# In-memory (for testing)
engine = create_engine('duckdb:///:memory:')

# With options
engine = create_engine(
    'duckdb:///data/tandem.db',
    connect_args={'read_only': False}
)
```

### 6. Alembic Support

Alembic works with DuckDB but requires a small configuration class:

```python
from alembic.ddl.impl import DefaultImpl

class AlembicDuckDBImpl(DefaultImpl):
    """Alembic implementation for DuckDB."""
    __dialect__ = "duckdb"
```

**Recommendation**: Keep Alembic for schema management. Add the impl class to `alembic/env.py`.

**Alternative considered**: Direct schema creation via `Base.metadata.create_all()`. Rejected because:
- Loses migration history
- Harder to evolve schema over time
- Alembic approach is familiar

### 7. Key Differences from PostgreSQL

| Feature | PostgreSQL | DuckDB | Migration Impact |
|---------|------------|--------|------------------|
| SERIAL/autoincrement | Built-in | Use Sequence() | Change model definitions |
| Integer division | Returns int | Returns float | No impact (not used) |
| Connection pooling | Full support | Limited (file-based) | Simplify engine creation |
| Concurrent writes | Full MVCC | Single writer | Fine for single-user |
| psycopg2 driver | Required | Not needed | Remove dependency |

### 8. Dependencies to Change

**Remove**:
- `psycopg2>=2.9.10` - PostgreSQL driver

**Add**:
- `duckdb>=1.0.0` - DuckDB core
- `duckdb-engine>=0.17.0` - SQLAlchemy dialect

### 9. Files Requiring Modification

| File | Change Required |
|------|-----------------|
| `pyproject.toml` | Swap psycopg2 for duckdb/duckdb-engine |
| `src/tandem_fetch/definitions.py` | Change DATABASE_URL to file path |
| `src/tandem_fetch/db/base.py` | No change needed |
| `src/tandem_fetch/db/raw_events.py` | Add Sequence for id |
| `src/tandem_fetch/db/events.py` | Add Sequence for id |
| `src/tandem_fetch/db/cgm_readings.py` | Add Sequence for id |
| `src/tandem_fetch/db/basal_deliveries.py` | Add Sequence for id |
| `alembic/env.py` | Add AlembicDuckDBImpl class, update URL handling |
| `alembic.ini` | Update sqlalchemy.url |
| `README.md` | Simplify setup instructions |

### 10. Schema Creation Strategy

Since user stated "start the whole thing over", two options:

**Option A: Fresh Alembic migrations**
- Delete existing migration files
- Create new initial migration for DuckDB
- Run `alembic upgrade head`

**Option B: Direct schema creation**
- Use `Base.metadata.create_all(engine)` for initial setup
- Keep Alembic for future changes

**Decision**: Option A - maintains clean migration history and standard workflow.

## Alternatives Considered

### Alternative 1: SQLite instead of DuckDB
- **Rejected**: User specifically requested DuckDB for analytics capabilities
- DuckDB has better performance for analytical queries (columnar storage)

### Alternative 2: Direct DuckDB Python API (no SQLAlchemy)
- **Rejected**: Would require rewriting all database code
- SQLAlchemy provides ORM benefits and familiar patterns
- duckdb-engine makes migration straightforward

### Alternative 3: Polars with DuckDB backend
- **Considered for future**: Polars already in dependencies
- Could use for analytics layer on top of DuckDB
- Not needed for this migration scope
