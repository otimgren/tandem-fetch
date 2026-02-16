# Tandem Fetch

![CI](https://github.com/otimgren/tandem-fetch/workflows/CI/badge.svg)

Fetch and store insulin pump data from Tandem Source for personal analytics.

Based on [tconnectsync](https://github.com/jwoglom/tconnectsync).

## Setup

### 1. Install Dependencies

```bash
uv sync
```

That's it! No database server installation required - data is stored in a local DuckDB file.

### 2. Set Up Pre-Commit Hooks (Recommended)

Install pre-commit hooks to automatically format code and detect secrets:

```bash
uv tool install prek
prek install --hook-type pre-commit --hook-type pre-push
```

**What runs when:**
- **On commit**: Code formatting (ruff), linting, secret detection (gitleaks)
- **On push**: All the above + full test suite

This ensures code quality without slowing down commits. See [Pre-Commit Hooks Guide](specs/002-precommit-hooks/quickstart.md) for details.

**Bypass hooks** (for exceptional cases only):
```bash
SKIP=hook-id git commit  # Skip specific hook
git commit --no-verify   # Skip all hooks (use sparingly)
git push --no-verify     # Skip pre-push tests
```

### 3. Configure Credentials

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

### Run Complete Pipeline (Recommended)

```bash
uv run run-pipeline
```

This runs the entire workflow:
1. Fetches raw pump events from Tandem Source (incremental)
2. Parses raw events into structured events table
3. Extracts CGM readings
4. Extracts basal deliveries

### Individual Steps

You can also run each step separately:

```bash
# Step 0: Fetch raw events
uv run get-all-raw-pump-events

# Step 1: Parse raw events into structured events table
uv run parse-events

# Step 2: Extract CGM readings
uv run parse-cgm-readings

# Step 3: Extract basal deliveries
uv run parse-basal-deliveries
```

## Exporting Data

The `export-data` command fetches the latest data and exports it to Parquet or CSV format for analysis in Python, R, Excel, or other tools.

### Quick Start (First Time Setup)

For first-time users, run the full pipeline once to populate the database:

```bash
# 1. Run pipeline to fetch and process data (one-time setup)
uv run run-pipeline

# 2. Export all tables to Parquet (recommended for data science)
uv run export-data

# Or export just CGM readings
uv run export-data --tables cgm_readings

# Your data is now in: exports/
```

### Basic Usage

```bash
# Export all tables (fetches latest data automatically)
uv run export-data

# Export single table
uv run export-data --tables cgm_readings

# Export multiple specific tables
uv run export-data --tables cgm_readings basal_deliveries events

# Export to CSV for Excel/spreadsheets
uv run export-data --tables cgm_readings --format csv

# Specify custom output directory
uv run export-data --tables cgm_readings --output-dir ~/diabetes-data
```

### Advanced Options

**Skip pipeline run** (use existing data, faster):
```bash
uv run export-data --tables cgm_readings --no-fetch
```

**Date range filtering** (export only specific period):
```bash
# Last 7 days
uv run export-data --tables cgm_readings \
  --start-date 2026-01-01 --end-date 2026-01-07

# Everything from specific date onwards
uv run export-data --tables cgm_readings --start-date 2026-01-01

# Everything up to specific date
uv run export-data --tables cgm_readings --end-date 2026-12-31
```

**Overwrite existing files**:
```bash
uv run export-data --tables cgm_readings --overwrite
```

**Verbose output** (see detailed progress):
```bash
uv run export-data --tables cgm_readings --verbose
```

### Available Tables

- `cgm_readings` - Continuous glucose monitoring data (most commonly exported)
- `basal_deliveries` - Basal insulin delivery data
- `events` - Parsed pump events (boluses, alarms, etc.)
- `raw_events` - Raw API responses (source of truth)

### Using Exported Data

**In Python (Pandas)**:
```python
import pandas as pd

# Read Parquet file
df = pd.read_parquet('exports/cgm_readings_20260208_103000.parquet')

# Quick analysis
print(df.describe())
print(f"Time in range (70-180): {len(df[(df['cgm_reading'] >= 70) & (df['cgm_reading'] <= 180)]) / len(df) * 100:.1f}%")
```

**In Python (Polars - faster)**:
```python
import polars as pl

# Read Parquet file
df = pl.read_parquet('exports/cgm_readings_20260208_103000.parquet')

# Quick analysis
print(df.describe())
```

**In Excel**:
1. Export to CSV: `uv run export-data --tables cgm_readings --format csv`
2. Open the CSV file in Excel or Google Sheets

**In R**:
```r
library(arrow)
df <- read_parquet("exports/cgm_readings_20260208_103000.parquet")
```

### Tips

- **First export**: Always run `uv run run-pipeline` first to populate the database
- **Subsequent exports**: Use `--fetch-latest` (default) to get the latest data automatically
- **Quick re-exports**: Use `--no-fetch` to skip the pipeline and just export existing data
- **Parquet vs CSV**: Parquet is 5x smaller and 10x faster to load - use it for data science
- **CSV for Excel**: Use `--format csv` if you need to open the data in Excel or Google Sheets
- **Date filtering**: Use date ranges to create smaller, focused exports for analysis

### Common Workflows

**Daily export** (for ongoing analysis):
```bash
# Fetch latest data and export all tables
uv run export-data

# Or export specific tables
uv run export-data --tables cgm_readings basal_deliveries
```

**Weekly summary** (last 7 days):
```bash
uv run export-data --tables cgm_readings \
  --start-date $(date -d '7 days ago' +%Y-%m-%d)
```

**Monthly report** (specific month):
```bash
uv run export-data --tables cgm_readings basal_deliveries \
  --start-date 2026-01-01 --end-date 2026-01-31 \
  --output-dir ~/reports/january-2026
```

**Backup all data** (full historical export):
```bash
# Export all tables without fetching new data
uv run export-data --no-fetch --output-dir ~/backups/$(date +%Y%m%d)
```

### Troubleshooting

**"Table not found" error**:
```bash
# Run pipeline first to populate the database
uv run run-pipeline
```

**"No space left on device"**:
```bash
# Use a different directory with more space
uv run export-data --tables cgm_readings --output-dir /path/with/space

# Or export only recent data
uv run export-data --tables cgm_readings --start-date 2026-01-01
```

**Want to see what's happening**:
```bash
# Add --verbose flag for detailed output
uv run export-data --tables cgm_readings --verbose
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

### Export from DuckDB CLI

You can also export directly from the DuckDB CLI:

```sql
-- Export to Parquet (columnar, efficient)
COPY cgm_readings TO 'exports/cgm_readings.parquet' (FORMAT PARQUET);

-- Export to CSV
COPY cgm_readings TO 'exports/cgm_readings.csv' (HEADER, DELIMITER ',');
```

**Note**: The `export-data` command (see [Exporting Data](#exporting-data) section) is recommended as it handles the full pipeline and provides more features.

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

## Continuous Integration

GitHub Actions automatically runs tests on every push and pull request. The CI workflow:
- Runs ruff linting and formatting checks
- Executes the full test suite (37 tests) with parallel execution
- Caches dependencies for faster runs
- Completes in under 2 minutes

### Running CI Locally

Before pushing code, you can run the same CI checks locally:

```bash
bash .github/scripts/run-ci-locally.sh
```

This script runs:
1. Dependency installation (`uv sync`)
2. Ruff linting (`ruff check`)
3. Ruff formatting check (`ruff format --check`)
4. Full test suite (`pytest`)

**Tip**: Running CI locally helps catch issues before pushing, saving time and CI resources.

### CI Performance

The CI workflow is optimized for speed:

- **Dependency caching**: Dependencies are cached based on `uv.lock`, reducing setup time from ~3 minutes to under 1 minute on subsequent runs
- **Parallel test execution**: Tests run in parallel using pytest-xdist (`-n auto`), typically providing 2-3x speedup
- **Expected timings**:
  - Cold start (no cache): < 3 minutes
  - Warm start (with cache): < 2 minutes
  - Test suite: ~10 seconds (37 tests in parallel)

Cache is automatically refreshed weekly and when `uv.lock` changes.

### Troubleshooting CI

**CI fails with linting errors:**
```bash
# Fix automatically
uv run ruff check --fix .
uv run ruff format .
```

**CI fails with test errors:**
```bash
# Run tests locally to debug
uv run pytest -v
# Or run specific test file
uv run pytest tests/path/to/test_file.py -v
```

**Dependencies out of sync:**
```bash
# Ensure uv.lock is up to date
uv lock
# Then sync dependencies
uv sync --locked --all-extras --group dev --group test
```

**CI is unusually slow:**
- Check if cache was invalidated (uv.lock changed)
- First run after uv.lock change will be slower (rebuilding cache)
- Subsequent runs should be fast (~2 minutes total)

### Optional: Branch Protection

To prevent merging code that fails CI:

1. Go to GitHub: **Settings → Branches → Branch protection rules**
2. Add rule for `main` branch
3. Enable:
   - ☑ Require status checks to pass before merging
   - ☑ Status checks: Select `ci`
   - ☑ Require branches to be up to date before merging

This ensures only code that passes all tests can be merged to main.

## File Structure

| Path | Description |
|------|-------------|
| `data/tandem.db` | DuckDB database (gitignored) |
| `exports/` | Exported data files (gitignored) |
| `sensitive/credentials.toml` | Tandem credentials (gitignored) |
| `src/tandem_fetch/` | Source code |
| `alembic/` | Database migrations |
| `.github/workflows/ci.yml` | GitHub Actions CI workflow |
| `.github/scripts/run-ci-locally.sh` | Local CI validation script |
