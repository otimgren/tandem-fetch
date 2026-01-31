# Quickstart: DuckDB Migration

**Date**: 2026-01-31
**Feature**: 001-duckdb-migration

## Prerequisites

- Python 3.12+
- uv package manager
- Tandem Source account with pump data

## Setup (One-time)

### 1. Install Dependencies

```bash
uv sync
```

This installs all required packages including DuckDB. No database server installation needed.

### 2. Configure Credentials

```bash
cp sensitive/credentials.template.toml sensitive/credentials.toml
```

Edit `sensitive/credentials.toml` with your Tandem credentials:
```toml
[tandem]
email = "your-email@example.com"
password = "your-password"
pump_serial = "12345678"
```

### 3. Initialize Database

The database file is created automatically on first run. No manual setup required.

**Optional**: Initialize schema before first fetch:
```bash
uv run alembic upgrade head
```

## Usage

### Fetch All Data (Initial Backfill)

```bash
uv run get-all-raw-pump-events
```

This command:
1. Creates `data/tandem.db` if it doesn't exist
2. Authenticates with Tandem Source
3. Fetches all pump events in 7-day batches
4. Stores raw events in the database

### Incremental Updates

Run the same command to fetch only new data:
```bash
uv run get-all-raw-pump-events
```

The system automatically detects the last fetch timestamp and only retrieves new events.

### Process Raw Events

After fetching, process raw events into structured tables:

```bash
# Parse raw events into events table
uv run python -m tandem_fetch.workflows.backfills.1_parse_events_table

# Extract CGM readings
uv run python -m tandem_fetch.workflows.backfills.2_parse_cgm_readings

# Extract basal deliveries
uv run python -m tandem_fetch.workflows.backfills.3_parse_basal_deliveries
```

## Querying Data

### Using DuckDB CLI

```bash
# Install DuckDB CLI (if not already available)
brew install duckdb  # macOS
# or download from https://duckdb.org/docs/installation/

# Connect to database
duckdb data/tandem.db
```

Example queries:
```sql
-- Count records per table
SELECT 'raw_events' as table_name, COUNT(*) as count FROM raw_events
UNION ALL
SELECT 'events', COUNT(*) FROM events
UNION ALL
SELECT 'cgm_readings', COUNT(*) FROM cgm_readings
UNION ALL
SELECT 'basal_deliveries', COUNT(*) FROM basal_deliveries;

-- Daily CGM averages
SELECT
    DATE_TRUNC('day', timestamp) as date,
    AVG(cgm_reading) as avg_glucose,
    MIN(cgm_reading) as min_glucose,
    MAX(cgm_reading) as max_glucose,
    COUNT(*) as readings
FROM cgm_readings
GROUP BY 1
ORDER BY 1 DESC
LIMIT 7;

-- Time in range (70-180 mg/dL)
SELECT
    COUNT(*) FILTER (WHERE cgm_reading BETWEEN 70 AND 180) * 100.0 / COUNT(*) as time_in_range
FROM cgm_readings
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
```

### Using Python

```python
import duckdb

# Direct DuckDB connection
conn = duckdb.connect('data/tandem.db')
df = conn.execute("SELECT * FROM cgm_readings ORDER BY timestamp DESC LIMIT 100").fetchdf()

# With Polars (already in dependencies)
import polars as pl
df = pl.read_database("SELECT * FROM cgm_readings", "duckdb:///data/tandem.db")
```

### Export to Parquet/CSV

```sql
-- In DuckDB CLI
COPY cgm_readings TO 'exports/cgm_readings.parquet' (FORMAT PARQUET);
COPY cgm_readings TO 'exports/cgm_readings.csv' (HEADER, DELIMITER ',');
```

## File Locations

| Path | Description |
|------|-------------|
| `data/tandem.db` | DuckDB database file (gitignored) |
| `sensitive/credentials.toml` | Tandem credentials (gitignored) |
| `alembic/` | Database migrations |

## Troubleshooting

### Database locked error
DuckDB allows only one writer at a time. Close other connections (DuckDB CLI, Python sessions) before running fetch commands.

### Missing data after fetch
Check Prefect logs for API errors. Common issues:
- Invalid credentials
- Rate limiting (wait and retry)
- Network timeout (will resume on next run)

### Schema mismatch
If schema changes, run migrations:
```bash
uv run alembic upgrade head
```

### Start fresh
Delete and recreate the database:
```bash
rm data/tandem.db
uv run alembic upgrade head
uv run get-all-raw-pump-events
```

## Comparison: Before vs After

| Aspect | PostgreSQL (Before) | DuckDB (After) |
|--------|---------------------|----------------|
| Setup steps | 5+ (install, create DB, configure, migrate) | 1 (uv sync) |
| External dependencies | PostgreSQL server | None |
| Configuration | DATABASE_URL env var | Automatic |
| Data portability | pg_dump/restore | Copy single file |
| Analytics queries | Good | Excellent (columnar) |
| Concurrent writes | Full support | Single writer |
