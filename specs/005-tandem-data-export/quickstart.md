# Quickstart Guide: Tandem Data Export

**Feature**: 005-tandem-data-export
**Date**: 2026-02-08

Get started with exporting your tandem-fetch data in 5 minutes.

---

## Installation

No additional setup needed! The export command is included with tandem-fetch.

```bash
# Verify installation
uv run export-data --help
```

---

## Quick Examples

### Export CGM Readings (Most Common)

```bash
# Export to Parquet (recommended for data analysis)
uv run export-data --tables cgm_readings

# Export to CSV (for Excel or Google Sheets)
uv run export-data --tables cgm_readings --format csv
```

**Output**:
```
✓ Exporting cgm_readings... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Export complete!

Files created:
  • exports/cgm_readings_20260208_103000.parquet (12.5 MB, 125,000 rows)
```

---

### Export Last 7 Days

```bash
uv run export-data \
  --tables cgm_readings \
  --start-date $(date -d "7 days ago" +%Y-%m-%d)
```

**macOS version**:
```bash
uv run export-data \
  --tables cgm_readings \
  --start-date $(date -v-7d +%Y-%m-%d)
```

---

### Export Multiple Tables

```bash
uv run export-data \
  --tables cgm_readings basal_deliveries events
```

**Output**:
```
✓ Exporting cgm_readings... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Exporting basal_deliveries... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%
✓ Exporting events... [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 100%

Files created:
  • exports/cgm_readings_20260208_103000.parquet (12.5 MB, 125,000 rows)
  • exports/basal_deliveries_20260208_103000.parquet (7.8 MB, 50,000 rows)
  • exports/events_20260208_103000.parquet (47.2 MB, 500,000 rows)
```

---

## Common Use Cases

### 1. Daily Data Export

Export today's data for daily analysis:

```bash
#!/bin/bash
# save as: scripts/daily-export.sh

TODAY=$(date +%Y-%m-%d)
uv run export-data \
  --tables cgm_readings basal_deliveries \
  --start-date "$TODAY" \
  --output-dir ~/diabetes-data/daily \
  --overwrite
```

---

### 2. Monthly Summary

Export last month's data:

```bash
# First day of last month
START=$(date -d "$(date +%Y-%m-01) -1 month" +%Y-%m-%d)

# Last day of last month
END=$(date -d "$(date +%Y-%m-01) -1 day" +%Y-%m-%d)

uv run export-data \
  --tables cgm_readings basal_deliveries \
  --start-date "$START" \
  --end-date "$END" \
  --output-dir exports/monthly
```

---

### 3. Full Historical Export

Export all data for backup or migration:

```bash
uv run export-data \
  --tables cgm_readings basal_deliveries events raw_events \
  --no-fetch \
  --output-dir ~/diabetes-backup/$(date +%Y%m%d)
```

**Note**: Uses `--no-fetch` to skip API call and just export existing data.

---

### 4. Excel-Compatible Export

Export for non-technical analysis:

```bash
uv run export-data \
  --tables cgm_readings \
  --format csv \
  --start-date 2026-01-01 \
  --end-date 2026-01-31 \
  --output-dir ~/Documents
```

Then open `~/Documents/cgm_readings_*.csv` in Excel.

---

## Understanding Output Files

### File Naming

```
{table_name}_{timestamp}.{format}

Examples:
cgm_readings_20260208_103000.parquet
basal_deliveries_20260208_143022.csv
```

**Timestamp format**: `YYYYMMDD_HHMMSS` (local time)

---

### File Sizes

Typical sizes for one year of data:

| Table | Parquet | CSV | Rows |
|-------|---------|-----|------|
| cgm_readings | ~25 MB | ~125 MB | 500k |
| basal_deliveries | ~15 MB | ~75 MB | 250k |
| events | ~150 MB | ~750 MB | 2M |
| raw_events | ~250 MB | ~1.25 GB | 2M |

**Tip**: Parquet is 5x smaller than CSV with faster load times in pandas/polars.

---

## Working with Exported Data

### Load in Python

#### Parquet (Recommended)

```python
import polars as pl

# Load CGM data
df = pl.read_parquet("exports/cgm_readings_20260208_103000.parquet")

# Quick stats
print(df.describe())

# Time in range (70-180 mg/dL)
tir = (df.filter(pl.col("cgm_reading").is_between(70, 180)).height / df.height) * 100
print(f"Time in range: {tir:.1f}%")
```

#### CSV (For Compatibility)

```python
import pandas as pd

df = pd.read_csv("exports/cgm_readings_20260208_103000.csv")

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Daily averages
daily_avg = df.set_index('timestamp').resample('D')['cgm_reading'].mean()
print(daily_avg)
```

---

### Load in R

```r
library(arrow)
library(dplyr)

# Read parquet file
cgm_data <- read_parquet("exports/cgm_readings_20260208_103000.parquet")

# Summary statistics
cgm_data %>%
  summarise(
    avg_glucose = mean(cgm_reading),
    min_glucose = min(cgm_reading),
    max_glucose = max(cgm_reading)
  )
```

---

### Load in Excel

1. Open Excel
2. **Data** → **Get Data** → **From File** → **From Text/CSV**
3. Select your exported CSV file
4. Click **Load**

**Note**: Parquet files require Power Query or third-party add-ins.

---

## Automation

### Cron Job (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add daily export at 6 AM
0 6 * * * cd /path/to/tandem-fetch && uv run export-data --tables cgm_readings --overwrite

# Add weekly full export on Sunday at 2 AM
0 2 * * 0 cd /path/to/tandem-fetch && uv run export-data --tables cgm_readings basal_deliveries events --output-dir ~/backups/$(date +\%Y\%m\%d) --no-fetch
```

---

### Scheduled Task (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. **Trigger**: Daily at 6:00 AM
4. **Action**: Start a program
   - Program: `uv`
   - Arguments: `run export-data --tables cgm_readings --overwrite`
   - Start in: `C:\path\to\tandem-fetch`

---

## Advanced Usage

### Date Range Presets

Use shell functions for common ranges:

```bash
# Add to ~/.bashrc or ~/.zshrc
export_last_week() {
    uv run export-data \
        --tables cgm_readings basal_deliveries \
        --start-date $(date -d "7 days ago" +%Y-%m-%d) \
        --output-dir exports/weekly
}

export_last_month() {
    uv run export-data \
        --tables cgm_readings basal_deliveries \
        --start-date $(date -d "1 month ago" +%Y-%m-%d) \
        --output-dir exports/monthly
}

# Usage
export_last_week
export_last_month
```

---

### Export Configuration File

Create reusable configurations:

```toml
# export-daily.toml
[export]
tables = ["cgm_readings", "basal_deliveries"]
format = "parquet"
output_dir = "exports/daily"
fetch_latest = true
overwrite = true

[export.date_range]
# Last 24 hours
start_date = "auto:-1d"
```

**Usage**:
```bash
uv run export-data --config export-daily.toml
```

---

### Filtering Specific Time Ranges

Export business hours only:

```python
# post-process-filter.py
import polars as pl

# Load export
df = pl.read_parquet("exports/cgm_readings_20260208_103000.parquet")

# Filter 9 AM - 5 PM
business_hours = df.filter(
    (pl.col("timestamp").dt.hour() >= 9) &
    (pl.col("timestamp").dt.hour() < 17)
)

# Save filtered data
business_hours.write_parquet("exports/cgm_business_hours.parquet")
```

---

## Troubleshooting

### "Table not found"

**Problem**: Table hasn't been populated yet.

**Solution**: Run the pipeline first:
```bash
uv run run-pipeline
uv run export-data --tables cgm_readings
```

---

### "No space left on device"

**Problem**: Insufficient disk space for export.

**Solution**: Free up space or use a different directory:
```bash
# Export to external drive
uv run export-data --tables cgm_readings --output-dir /mnt/external/exports

# Export only recent data
uv run export-data --tables cgm_readings --start-date 2026-01-01
```

---

### "Permission denied"

**Problem**: No write access to output directory.

**Solution**: Choose a writable directory:
```bash
uv run export-data --tables cgm_readings --output-dir ~/Documents/diabetes-data
```

---

### "Export is slow"

**Problem**: Exporting millions of records takes time.

**Solutions**:

1. **Use date range filtering**:
```bash
uv run export-data --tables cgm_readings --start-date 2026-01-01
```

2. **Use Parquet instead of CSV** (5x faster):
```bash
uv run export-data --tables cgm_readings --format parquet
```

3. **Skip the pipeline** if data is recent:
```bash
uv run export-data --tables cgm_readings --no-fetch
```

---

### "File already exists"

**Problem**: Output file from previous export exists.

**Solutions**:

1. **Let the command prompt you**:
```bash
uv run export-data --tables cgm_readings
# Responds to prompt: Overwrite? [y/N]: y
```

2. **Always overwrite**:
```bash
uv run export-data --tables cgm_readings --overwrite
```

3. **Use different output directory**:
```bash
uv run export-data --tables cgm_readings --output-dir exports/archive
```

---

## Best Practices

### 1. Use Parquet for Data Science

```bash
# Recommended
uv run export-data --tables cgm_readings --format parquet
```

**Why**: 5x smaller files, 10x faster to load, preserves data types

---

### 2. Use CSV for Spreadsheets

```bash
# For Excel/Sheets
uv run export-data --tables cgm_readings --format csv
```

**Why**: Universal compatibility, easy to open

---

### 3. Export Incrementally

```bash
# Don't export entire history every day
# Instead, export last 7 days
uv run export-data \
  --tables cgm_readings \
  --start-date $(date -d "7 days ago" +%Y-%m-%d)
```

**Why**: Faster exports, smaller files, less disk space

---

### 4. Organize Exports by Date

```bash
# Create dated directories
EXPORT_DIR="exports/$(date +%Y-%m)"
uv run export-data --tables cgm_readings --output-dir "$EXPORT_DIR"
```

**Why**: Easy to find historical exports

---

### 5. Verify Exports

```bash
# Count rows in exported file
python -c "import polars as pl; print(len(pl.read_parquet('exports/cgm_readings_*.parquet')))"

# Compare with database count
duckdb data/tandem.db "SELECT COUNT(*) FROM cgm_readings"
```

**Why**: Ensure export completed successfully

---

## Performance Tips

### Expected Times

| Rows | Format | Time |
|------|--------|------|
| 10k | Parquet | <1s |
| 100k | Parquet | 2-3s |
| 1M | Parquet | 10-15s |
| 10k | CSV | 1-2s |
| 100k | CSV | 5-8s |
| 1M | CSV | 30-60s |

---

### Speed Up Exports

1. **Use `--no-fetch`** if data is already fresh:
```bash
uv run export-data --tables cgm_readings --no-fetch
```

2. **Export during off-hours** (automated):
```bash
# Cron: Run at 2 AM when system is idle
0 2 * * * uv run export-data --tables cgm_readings
```

3. **Export to SSD**, not spinning disk:
```bash
uv run export-data --tables cgm_readings --output-dir /mnt/ssd/exports
```

---

## Next Steps

### Analyze Your Data

- **Jupyter Notebook**: See `examples/cgm-analysis.ipynb` (coming soon)
- **Dashboard**: See `examples/diabetes-dashboard/` (coming soon)
- **Reports**: See `examples/monthly-report.py` (coming soon)

### Automate Your Workflow

- **GitHub Actions**: See `.github/workflows/export-data.yml` (coming soon)
- **Prefect Deployments**: See `docs/prefect-scheduling.md` (coming soon)

### Share Your Data

- **With Healthcare Provider**: Export to CSV, upload to patient portal
- **With Researchers**: Export to Parquet, de-identify, share securely
- **With Family**: Export to CSV, open in Google Sheets

---

## Getting Help

### Command Help

```bash
uv run export-data --help
```

### Verbose Output

```bash
uv run export-data --tables cgm_readings --verbose
```

### Check Logs

```bash
# View Prefect logs
prefect flow-run logs <flow-run-id>

# View tandem-fetch logs
tail -f logs/tandem-fetch.log
```

### Report Issues

If you encounter problems:

1. Check [Troubleshooting](#troubleshooting) section
2. Review error message and suggestions
3. Run with `--verbose` for detailed output
4. Open issue: https://github.com/otimgren/tandem-fetch/issues

---

## Summary

You now know how to:

✓ Export CGM readings to Parquet/CSV
✓ Filter by date range
✓ Export multiple tables
✓ Automate exports with cron
✓ Load exported data in Python/R/Excel
✓ Troubleshoot common issues

**Most common command**:
```bash
uv run export-data --tables cgm_readings
```

Happy exporting! 📊
