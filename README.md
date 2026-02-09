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
prek install
```

This ensures code quality and prevents accidentally committing sensitive data. See [Pre-Commit Hooks Guide](specs/002-precommit-hooks/quickstart.md) for details.

**Bypass hooks** (for exceptional cases only):
```bash
SKIP=hook-id git commit  # Skip specific hook
git commit --no-verify   # Skip all hooks (use sparingly)
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
| `sensitive/credentials.toml` | Tandem credentials (gitignored) |
| `src/tandem_fetch/` | Source code |
| `alembic/` | Database migrations |
| `.github/workflows/ci.yml` | GitHub Actions CI workflow |
| `.github/scripts/run-ci-locally.sh` | Local CI validation script |
