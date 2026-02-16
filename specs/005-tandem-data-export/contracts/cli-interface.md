# CLI Interface Contract: Tandem Data Export Command

**Feature**: 005-tandem-data-export
**Date**: 2026-02-08
**Status**: Phase 1 Complete

This document defines the command-line interface contract for the export command.

---

## Command Registration

### Entry Point

```toml
# pyproject.toml
[project.scripts]
export-data = "tandem_fetch.workflows.export_data:main"
```

### Invocation

```bash
uv run export-data [OPTIONS]
```

---

## Command Signature

```
export-data --tables TABLE [TABLE ...] [OPTIONS]

Export tandem-fetch database tables to CSV or Parquet format.
```

---

## Arguments

### Required Arguments

#### `--tables`, `-t`

**Type**: `List[str]`
**Required**: Yes
**Multiple**: Yes
**Description**: Names of database tables to export

**Valid Values**:
- `cgm_readings` - Continuous glucose monitoring data
- `basal_deliveries` - Basal insulin delivery data
- `events` - Parsed pump events
- `raw_events` - Raw API responses (source of truth)

**Examples**:
```bash
# Single table
export-data --tables cgm_readings

# Multiple tables (space-separated)
export-data --tables cgm_readings basal_deliveries

# Multiple tables (repeated flag)
export-data -t cgm_readings -t basal_deliveries -t events
```

**Validation**:
- Must provide at least one table
- Each table name must be one of the four valid values (case-sensitive)
- Duplicate table names are ignored (deduped)
- Invalid table names cause immediate error with helpful message

**Error Messages**:
```
❌ Error: Invalid table name 'cgm_reading' (did you mean 'cgm_readings'?)
   Valid tables: cgm_readings, basal_deliveries, events, raw_events

❌ Error: --tables is required. Specify at least one table to export.
```

---

### Optional Arguments

#### `--format`, `-f`

**Type**: `str`
**Default**: `"parquet"`
**Choices**: `["parquet", "csv"]`
**Description**: Output file format

**Examples**:
```bash
# Parquet (default)
export-data -t cgm_readings

# Explicit parquet
export-data -t cgm_readings --format parquet

# CSV for Excel
export-data -t cgm_readings --format csv
```

**Validation**:
- Must be either "parquet" or "csv" (case-insensitive)
- Invalid format causes error with valid options

**Error Messages**:
```
❌ Error: Invalid format 'json'. Choose 'parquet' or 'csv'.
```

---

#### `--output-dir`, `-o`

**Type**: `Path`
**Default**: `"exports/"`
**Description**: Directory where exported files will be written

**Behavior**:
- Creates directory if it doesn't exist (including parents)
- Files named automatically: `{table}_{timestamp}.{format}`
- Timestamp format: `YYYYMMDD_HHMMSS`

**Examples**:
```bash
# Default directory
export-data -t cgm_readings
# Creates: exports/cgm_readings_20260208_103000.parquet

# Custom directory
export-data -t cgm_readings --output-dir /path/to/exports
# Creates: /path/to/exports/cgm_readings_20260208_103000.parquet

# Relative path
export-data -t cgm_readings -o ../data/exports
# Creates: ../data/exports/cgm_readings_20260208_103000.parquet

# User home directory
export-data -t cgm_readings -o ~/diabetes-data
# Creates: /Users/username/diabetes-data/cgm_readings_20260208_103000.parquet
```

**Validation**:
- Path must be writable or creatable
- Parent directories are created automatically (`mkdir -p` behavior)
- Special characters and spaces in path are handled

**Error Messages**:
```
❌ Error: Cannot create output directory: /readonly/path
   Permission denied

❌ Error: Output directory path is invalid: /path/with/\0/null
```

---

#### `--start-date`

**Type**: `date`
**Format**: `YYYY-MM-DD`
**Default**: `None` (no filtering)
**Description**: Start date for filtering records (inclusive)

**Examples**:
```bash
# Export only records from 2026-01-01 onwards
export-data -t cgm_readings --start-date 2026-01-01

# Combined with end date
export-data -t cgm_readings --start-date 2026-01-01 --end-date 2026-01-31
```

**Validation**:
- Must be in YYYY-MM-DD format
- Must be <= end_date (if end_date provided)
- Must be a valid date (no Feb 31st, etc.)

**Error Messages**:
```
❌ Error: Invalid date format '2026/01/01'. Use YYYY-MM-DD format.

❌ Error: start_date (2026-02-01) cannot be after end_date (2026-01-31)

❌ Error: Invalid date: 2026-02-30
```

---

#### `--end-date`

**Type**: `date`
**Format**: `YYYY-MM-DD`
**Default**: `None` (no filtering)
**Description**: End date for filtering records (inclusive)

**Examples**:
```bash
# Export only records up to 2026-01-31
export-data -t cgm_readings --end-date 2026-01-31

# Combined with start date (date range)
export-data -t cgm_readings --start-date 2026-01-01 --end-date 2026-01-31
```

**Validation**:
- Must be in YYYY-MM-DD format
- Must be >= start_date (if start_date provided)
- Must be a valid date

**Error Messages**:
Same as `--start-date`

---

#### `--fetch-latest` / `--no-fetch`

**Type**: `bool`
**Default**: `True`
**Description**: Whether to run the full pipeline before export to fetch latest data

**Examples**:
```bash
# Fetch latest data first (default)
export-data -t cgm_readings --fetch-latest

# Use existing data only
export-data -t cgm_readings --no-fetch

# Explicit true
export-data -t cgm_readings --fetch-latest=true
```

**Behavior**:
- `--fetch-latest` (default): Runs `run-pipeline` before export
- `--no-fetch`: Uses existing database data, skips API fetch

**Use Cases**:
- `--fetch-latest`: Daily exports, ensure freshest data
- `--no-fetch`: Re-export existing data with different filters

---

#### `--overwrite`

**Type**: `bool`
**Default**: `False`
**Description**: Whether to overwrite existing files without prompting

**Examples**:
```bash
# Prompt if file exists (default)
export-data -t cgm_readings

# Overwrite without prompting
export-data -t cgm_readings --overwrite
```

**Behavior**:
- `False` (default): Prompts user if output file exists
- `True`: Silently overwrites existing files

**Interactive Prompt** (when False and file exists):
```
⚠️  File exists: exports/cgm_readings_20260208_103000.parquet
   Overwrite? [y/N]:
```

---

#### `--verbose`, `-v`

**Type**: `bool`
**Default**: `False`
**Description**: Enable verbose logging output

**Examples**:
```bash
# Normal output
export-data -t cgm_readings

# Verbose output
export-data -t cgm_readings --verbose
export-data -t cgm_readings -v
```

**Output Difference**:

**Normal**:
```
✓ Exporting cgm_readings...
✓ Export complete: 125,000 rows in 2.5s
```

**Verbose**:
```
[INFO] Validating export configuration...
[INFO] Table 'cgm_readings': 125,000 rows available
[INFO] Date range: 2025-01-01 to 2026-02-08
[INFO] Building export query with date filter: 2026-01-01 to 2026-01-31
[INFO] Executing query: SELECT * FROM cgm_readings WHERE timestamp >= ? AND timestamp <= ?
[INFO] Retrieved 31,250 rows from database
[INFO] Writing to exports/cgm_readings_20260208_103000.parquet
[INFO] Compression: ZSTD, row group size: 100,000
[SUCCESS] Export complete: 31,250 rows in 2.5s (12.5 MB)
```

---

#### `--help`, `-h`

**Type**: `flag`
**Description**: Show help message and exit

**Example**:
```bash
export-data --help
```

**Output**:
```
Usage: export-data [OPTIONS]

  Export tandem-fetch database tables to CSV or Parquet format.

  Fetches the latest data from Tandem Source and exports it to files for
  analysis. Supports multiple tables, date range filtering, and both Parquet
  (efficient) and CSV (Excel-compatible) formats.

Options:
  -t, --tables TEXT           Table names to export (required) [multiple]
                              Choices: cgm_readings, basal_deliveries, events, raw_events
  -f, --format [parquet|csv]  Output format [default: parquet]
  -o, --output-dir PATH       Output directory [default: exports/]
  --start-date DATE           Start date for filtering (YYYY-MM-DD)
  --end-date DATE             End date for filtering (YYYY-MM-DD)
  --fetch-latest/--no-fetch   Fetch latest data before export [default: fetch-latest]
  --overwrite                 Overwrite existing files [default: false]
  -v, --verbose               Enable verbose logging
  -h, --help                  Show this message and exit

Examples:
  # Export CGM readings to Parquet
  export-data -t cgm_readings

  # Export multiple tables to CSV
  export-data -t cgm_readings -t basal_deliveries --format csv

  # Export with date range filter
  export-data -t cgm_readings --start-date 2026-01-01 --end-date 2026-01-31

  # Export all tables without fetching latest
  export-data -t cgm_readings -t basal_deliveries -t events -t raw_events --no-fetch

For more information, see: specs/005-tandem-data-export/quickstart.md
```

---

## Exit Codes

| Code | Name | Description |
|------|------|-------------|
| `0` | Success | All tables exported successfully |
| `1` | Validation Error | Invalid arguments or configuration |
| `2` | Table Not Found | One or more tables don't exist in database |
| `3` | Export Failed | Export operation failed (DB, I/O, or other error) |
| `4` | Network Error | Pipeline run failed (Tandem API unavailable) |
| `5` | Partial Success | Some tables exported, others failed (see logs) |

**Exit Code Examples**:

```bash
# Success
$ export-data -t cgm_readings
✓ Export complete
$ echo $?
0

# Invalid table name
$ export-data -t invalid_table
❌ Error: Invalid table name
$ echo $?
1

# Table doesn't exist
$ export-data -t nonexistent_table
❌ Error: Table not found
$ echo $?
2

# Export failed (disk full)
$ export-data -t cgm_readings
❌ Error: No space left on device
$ echo $?
3

# Network error (API down)
$ export-data -t cgm_readings --fetch-latest
❌ Error: Failed to connect to Tandem Source API
$ echo $?
4

# Partial success (cgm_readings OK, basal_deliveries failed)
$ export-data -t cgm_readings -t basal_deliveries
✓ Exported cgm_readings: 125,000 rows
❌ Failed to export basal_deliveries: Permission denied
⚠️  Partial success: 1 of 2 tables exported
$ echo $?
5
```

---

## Output Format

### Success Output

```
✓ Validating export configuration...
✓ Exporting cgm_readings... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Export complete!

Summary:
  Tables exported:  1
  Total rows:       125,000
  Total size:       12.5 MB
  Duration:         2.5s
  Output:           exports/

Files created:
  • cgm_readings_20260208_103000.parquet (12.5 MB, 125,000 rows)
```

### Multi-Table Success Output

```
✓ Validating export configuration...
✓ Exporting cgm_readings... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Exporting basal_deliveries... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Exporting events... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Export complete!

Summary:
  Tables exported:  3
  Total rows:       675,000
  Total size:       67.5 MB
  Duration:         8.2s
  Output:           exports/

Files created:
  • cgm_readings_20260208_103000.parquet (12.5 MB, 125,000 rows)
  • basal_deliveries_20260208_103000.parquet (7.8 MB, 50,000 rows)
  • events_20260208_103000.parquet (47.2 MB, 500,000 rows)
```

### Partial Failure Output

```
✓ Validating export configuration...
✓ Exporting cgm_readings... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
❌ Exporting basal_deliveries... Failed!
✓ Exporting events... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%

⚠️  Export completed with errors

Summary:
  Tables exported:  2 / 3
  Total rows:       625,000
  Total size:       59.7 MB
  Duration:         7.5s
  Output:           exports/

✓ Successfully exported:
  • cgm_readings_20260208_103000.parquet (12.5 MB, 125,000 rows)
  • events_20260208_103000.parquet (47.2 MB, 500,000 rows)

❌ Failed to export:
  • basal_deliveries: Permission denied writing to exports/basal_deliveries_20260208_103000.parquet

Exit code: 5
```

### Complete Failure Output

```
✓ Validating export configuration...
❌ Exporting cgm_readings... Failed!
❌ Exporting basal_deliveries... Failed!

❌ Export failed!

Error: All tables failed to export

Details:
  • cgm_readings: Disk full (no space left on device)
  • basal_deliveries: Disk full (no space left on device)

Suggestions:
  1. Free up disk space in exports/ directory
  2. Use a different output directory: --output-dir /path/with/space
  3. Export fewer tables or use date range filtering

Exit code: 3
```

---

## Progress Indicators

### Spinner (Validation & Setup)

```
⠋ Validating export configuration...
```

### Progress Bar (Export)

```
Exporting cgm_readings [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100% 125,000/125,000 rows
```

### Multi-Table Progress

```
[1/3] Exporting cgm_readings... ✓ (2.5s)
[2/3] Exporting basal_deliveries... ✓ (1.8s)
[3/3] Exporting events... ⠋ (47% complete)
```

---

## Environment Variables

### Optional Configuration

#### `TANDEM_FETCH_DB`

**Type**: `str`
**Default**: `"data/tandem.db"`
**Description**: Path to DuckDB database file

**Example**:
```bash
export TANDEM_FETCH_DB="/custom/path/tandem.db"
export-data -t cgm_readings
```

#### `TANDEM_FETCH_EXPORT_DIR`

**Type**: `str`
**Default**: `"exports/"`
**Description**: Default export directory (overridden by `--output-dir`)

**Example**:
```bash
export TANDEM_FETCH_EXPORT_DIR="/mnt/external/diabetes-exports"
export-data -t cgm_readings  # Uses /mnt/external/diabetes-exports
```

---

## Configuration File Support

### Optional: `export-config.toml`

For repeated exports with same settings:

```toml
[export]
tables = ["cgm_readings", "basal_deliveries"]
format = "parquet"
output_dir = "exports/"
fetch_latest = true
overwrite = false

[export.date_range]
start_date = "2026-01-01"
end_date = "2026-01-31"
```

**Usage**:
```bash
export-data --config export-config.toml

# CLI args override config file
export-data --config export-config.toml --format csv
```

**Priority** (highest to lowest):
1. CLI arguments
2. Config file
3. Environment variables
4. Defaults

---

## Integration with Existing Commands

### Pipeline Integration

```bash
# Manual pipeline + export
uv run run-pipeline
uv run export-data -t cgm_readings --no-fetch

# Automatic pipeline + export (default)
uv run export-data -t cgm_readings --fetch-latest
```

### Workflow Example

```bash
# Daily automated export (cron job)
#!/bin/bash
uv run export-data \
  --tables cgm_readings basal_deliveries \
  --format parquet \
  --output-dir ~/diabetes-data/daily \
  --start-date $(date -d "yesterday" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --fetch-latest \
  --overwrite
```

---

## API Compatibility

### Versioning

- **Command name**: `export-data` (stable)
- **Arguments**: Follow semantic versioning
  - New arguments: MINOR version bump
  - Argument removal: MAJOR version bump
  - Default changes: MINOR version bump

### Deprecation Policy

- Deprecated arguments: Show warning, continue working for 1 major version
- Example: `--output-path` renamed to `--output-dir`

```
⚠️  Warning: --output-path is deprecated and will be removed in v2.0.0
   Use --output-dir instead

✓ Exporting cgm_readings...
```

---

## Testing

### Test Cases

```bash
# Positive cases
export-data -t cgm_readings  # Success
export-data -t cgm_readings -t basal_deliveries  # Multi-table
export-data -t cgm_readings --format csv  # CSV format
export-data -t cgm_readings --start-date 2026-01-01  # Date filter

# Negative cases
export-data  # Missing required --tables
export-data -t invalid_table  # Invalid table name
export-data -t cgm_readings --format xml  # Invalid format
export-data -t cgm_readings --start-date 2026-02-01 --end-date 2026-01-01  # Invalid date range
```

### Contract Validation

All CLI behavior defined in this document will be validated by integration tests in `tests/integration/test_export_cli.py`.

---

## Summary

This CLI interface provides:

✓ **Type-safe arguments** with automatic validation
✓ **Helpful error messages** with suggestions
✓ **Progress indicators** for user feedback
✓ **Flexible configuration** (CLI, env vars, config file)
✓ **Predictable exit codes** for automation
✓ **Comprehensive help** with examples
✓ **Cross-platform compatibility** (Windows, macOS, Linux)
