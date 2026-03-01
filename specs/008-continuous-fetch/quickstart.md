# Quickstart: Continuous Data Fetch

**Feature**: 008-continuous-fetch
**Date**: 2026-02-28

## Prerequisites

1. Python 3.12+
2. The tandem-fetch project installed with dependencies
3. Valid Tandem API credentials configured in `sensitive/credentials.toml`

## Starting Continuous Fetch

### Default interval (every 5 minutes)

```bash
continuous-fetch
```

### Custom interval

```bash
# Fetch every 1 minute (near real-time)
continuous-fetch --interval 1

# Fetch every 30 minutes (low API usage)
continuous-fetch --interval 30
```

### What happens

1. The pipeline runs immediately on startup
2. After each cycle, it waits for the configured interval
3. Each cycle fetches only new data (incremental)
4. Failed cycles are logged but don't stop the process
5. Press Ctrl+C to stop

## Monitoring

While the process runs, you'll see log output for each cycle:

```
Starting continuous fetch (interval: 5 minutes)
Press Ctrl+C to stop.

[10:00:00] Starting full pipeline
[10:00:00] Step 0: Fetching raw pump events from Tandem Source
[10:00:08] Step 1: Parsing raw events into structured events table
[10:00:09] Step 2: Extracting CGM readings
[10:00:09] Step 3: Extracting basal deliveries
[10:00:10] Full pipeline completed successfully
```

## Using with MCP Server

Run the continuous fetch in one terminal and the MCP server in another:

```bash
# Terminal 1: Keep data fresh
continuous-fetch

# Terminal 2: Query via AI agent
tandem-mcp
```

The MCP server will always see the latest data because the continuous fetch keeps the database up to date.

## Running Tests

```bash
pytest tests/unit/test_workflows/test_continuous_fetch.py
```
