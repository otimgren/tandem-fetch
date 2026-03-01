# CLI Contract: Continuous Data Fetch

**Feature**: 008-continuous-fetch
**Date**: 2026-02-28

## Command: `continuous-fetch`

**Purpose**: Start a long-running process that repeatedly runs the full data pipeline at a configurable interval.

### Usage

```
continuous-fetch [--interval MINUTES]
```

### Arguments

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| --interval | integer | No | 5 | Minutes between pipeline cycles (minimum: 1) |

### Behavior

1. Validates the interval (must be >= 1 minute)
2. Logs the configured interval
3. Runs the full pipeline immediately (first cycle)
4. Waits for the configured interval
5. Repeats from step 3
6. On Ctrl+C: stops gracefully

### Example Invocations

```bash
# Default: fetch every 5 minutes
continuous-fetch

# Custom: fetch every 1 minute
continuous-fetch --interval 1

# Custom: fetch every 30 minutes
continuous-fetch --interval 30
```

### Output

```
Starting continuous fetch (interval: 5 minutes)
Press Ctrl+C to stop.

[2026-02-28 10:00:00] Starting full pipeline
[2026-02-28 10:00:15] Full pipeline completed successfully (15s, 12 new events)
[2026-02-28 10:05:00] Starting full pipeline
[2026-02-28 10:05:08] Full pipeline completed successfully (8s, 3 new events)
...
^C
Stopping continuous fetch...
```

### Error Conditions

- `--interval 0` → Error: "Interval must be at least 1 minute."
- `--interval -5` → Error: "Interval must be at least 1 minute."
- Network failure during cycle → Logs error, continues to next scheduled cycle
- Missing credentials → Logs error on first cycle, retries on next cycle

### Maps to

- FR-001 (continuous fetching command)
- FR-002 (5-minute default)
- FR-003 (custom interval)
- FR-004 (minimum 1 minute)
- FR-005 (immediate first cycle)
- FR-007 (graceful Ctrl+C shutdown)
- FR-009 (cycle logging)
