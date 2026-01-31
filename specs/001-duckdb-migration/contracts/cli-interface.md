# CLI Interface Contract

**Date**: 2026-01-31
**Feature**: 001-duckdb-migration

## Overview

This project uses CLI commands for all data operations. No REST API or web interface.

## Commands

### get-all-raw-pump-events

**Purpose**: Fetch raw pump events from Tandem Source API and store in database.

**Invocation**:
```bash
uv run get-all-raw-pump-events
```

**Behavior**:
1. Load credentials from `sensitive/credentials.toml`
2. Authenticate with Tandem Source API
3. Query database for latest `created` timestamp in `raw_events`
4. Fetch events from (latest_timestamp or 2020-01-01) to now
5. Insert raw events in 7-day batches
6. Log progress via Prefect/loguru

**Exit Codes**:
- 0: Success
- 1: Credential error (missing/invalid credentials file)
- 1: API error (authentication failed, rate limited)
- 1: Database error (file locked, disk full)

**Output**: Prefect flow logs to stdout

### Backfill Workflows

Located in `src/tandem_fetch/workflows/backfills/`

#### 0_get_all_raw_pump_events.py
Same as `get-all-raw-pump-events` CLI command.

#### 1_parse_events_table.py
**Purpose**: Parse raw_events JSON into structured events table.

```bash
uv run python -m tandem_fetch.workflows.backfills.1_parse_events_table
```

#### 2_parse_cgm_readings.py
**Purpose**: Extract CGM readings from events into cgm_readings table.

```bash
uv run python -m tandem_fetch.workflows.backfills.2_parse_cgm_readings
```

#### 3_parse_basal_deliveries.py
**Purpose**: Extract basal deliveries from events into basal_deliveries table.

```bash
uv run python -m tandem_fetch.workflows.backfills.3_parse_basal_deliveries
```

## Configuration

### Credentials File

**Path**: `sensitive/credentials.toml`

**Format**:
```toml
[tandem]
email = "string"      # Required: Tandem account email
password = "string"   # Required: Tandem account password
pump_serial = "string" # Required: Pump serial number
```

### Database Configuration

**Path**: Configured in `src/tandem_fetch/definitions.py`

**Default**: `data/tandem.db` (relative to project root)

**Environment Override**: `DATABASE_PATH` environment variable (optional)

## Database Connection

**Connection String Format**:
```
duckdb:///data/tandem.db
```

**SQLAlchemy Engine Creation**:
```python
from sqlalchemy import create_engine

engine = create_engine('duckdb:///data/tandem.db')
```

## Error Handling

All commands follow these error handling patterns:

1. **Credential Errors**: Fail fast with clear message
2. **API Errors**: Log error context, exit non-zero
3. **Database Errors**: Rollback transaction, log error, exit non-zero
4. **Partial Failures**: Commit successful batches, report failures

## Logging

- **Framework**: loguru + Prefect
- **Destination**: stdout/stderr
- **Levels**: INFO for progress, ERROR for failures, SUCCESS for completions
