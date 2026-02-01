# Tandem Fetch

Fetch and store insulin pump data from Tandem Source for personal analytics.

Based on [tconnectsync](https://github.com/jwoglom/tconnectsync).

## Setup

### 1. Install Dependencies

```bash
uv sync
```

That's it! No database server installation required - data is stored in a local DuckDB file.

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

## Usage

### Fetch All Data

```bash
uv run get-all-raw-pump-events
```

This command:
- Creates the database automatically if it doesn't exist
- Fetches all pump events from Tandem Source
- Stores raw events in `data/tandem.db`
- On subsequent runs, only fetches new data (incremental)

### Process Data Pipeline

After fetching raw data, process it through the pipeline:

```bash
# Parse raw events into structured events table
uv run python -m tandem_fetch.workflows.backfills.step1_parse_events_table

# Extract CGM readings
uv run python -m tandem_fetch.workflows.backfills.step2_parse_cgm_readings

# Extract basal deliveries
uv run python -m tandem_fetch.workflows.backfills.step3_parse_basal_deliveries
```

## Querying Data

### Using DuckDB CLI

```bash
duckdb data/tandem.db
```

Example queries:

```sql
-- Count records per table
SELECT 'raw_events' as tbl, COUNT(*) FROM raw_events
UNION ALL SELECT 'events', COUNT(*) FROM events
UNION ALL SELECT 'cgm_readings', COUNT(*) FROM cgm_readings
UNION ALL SELECT 'basal_deliveries', COUNT(*) FROM basal_deliveries;

-- Daily CGM averages (last 7 days)
SELECT
    DATE_TRUNC('day', timestamp) as date,
    ROUND(AVG(cgm_reading), 1) as avg_glucose,
    MIN(cgm_reading) as min_glucose,
    MAX(cgm_reading) as max_glucose,
    COUNT(*) as readings
FROM cgm_readings
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY 1
ORDER BY 1 DESC;

-- Time in range (70-180 mg/dL)
SELECT
    ROUND(COUNT(*) FILTER (WHERE cgm_reading BETWEEN 70 AND 180) * 100.0 / COUNT(*), 1) as time_in_range_pct
FROM cgm_readings
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
```

### Export to Parquet/CSV

```sql
-- Export to Parquet (columnar, efficient)
COPY cgm_readings TO 'exports/cgm_readings.parquet' (FORMAT PARQUET);

-- Export to CSV
COPY cgm_readings TO 'exports/cgm_readings.csv' (HEADER, DELIMITER ',');
```

### Using Python

```python
import duckdb

conn = duckdb.connect('data/tandem.db')
df = conn.execute("SELECT * FROM cgm_readings ORDER BY timestamp DESC LIMIT 100").fetchdf()
```

## Data Pipeline

```
Tandem Source API
       ↓
   raw_events (JSON blobs - source of truth)
       ↓
     events (parsed with timestamp, event type)
       ↓
   ┌───┴───┐
   ↓       ↓
cgm_readings  basal_deliveries
```

## File Structure

| Path | Description |
|------|-------------|
| `data/tandem.db` | DuckDB database (gitignored) |
| `sensitive/credentials.toml` | Tandem credentials (gitignored) |
| `src/tandem_fetch/` | Source code |
| `alembic/` | Database migrations |
