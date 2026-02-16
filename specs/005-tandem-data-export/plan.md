# Implementation Plan: Tandem Data Export Command

**Branch**: `005-tandem-data-export` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-tandem-data-export/spec.md`

## Summary

Create a CLI command that fetches the latest insulin pump data from Tandem Source API and exports it to Parquet or CSV format. The command will support single or multiple table exports, date range filtering, and provide progress indicators during operation. Uses DuckDB's native COPY command for efficient exports and integrates with existing Prefect workflows for data fetching.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: DuckDB 1.0.0, duckdb-engine 0.17.0, SQLAlchemy 2.0.43, Polars 1.33.0, Prefect 3.4.17, Loguru 0.7.3
**Storage**: DuckDB local database at `data/tandem.db`
**Testing**: pytest 8.0.0 with pytest-xdist for parallel execution
**Target Platform**: Local CLI on macOS/Linux/Windows
**Project Type**: Single project (CLI tool)
**Performance Goals**: Export 100k records in under 30 seconds, support millions of records efficiently
**Constraints**: Must preserve data types (timestamps, integers, JSON), 99% success rate for valid inputs
**Scale/Scope**: 4 database tables (cgm_readings, basal_deliveries, events, raw_events), typical dataset 100k-1M records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Data Integrity First ✅ PASS
- Exports preserve data types and precision (FR-017)
- Read-only operations (no data modification)
- Uses existing validated database as source

### Principle II: Single-User Simplicity ✅ PASS
- CLI command with simple arguments (no web interface)
- Uses existing credentials from `sensitive/credentials.toml` (FR-010)
- No multi-tenancy concerns

### Principle III: Incremental & Resumable ✅ PASS
- Fetches latest data before export using existing pipeline (FR-001, FR-016)
- Date range filtering supports incremental exports (FR-013, P4)

### Principle IV: Clear Data Pipeline ✅ PASS
- Exports from existing pipeline stages (raw_events, events, cgm_readings, basal_deliveries)
- Maintains pipeline architecture (no changes to existing stages)

### Principle V: Workflow Orchestration ✅ PASS
- Uses Prefect for workflow orchestration
- Integrates with existing workflows (run-pipeline)
- Follows existing pattern (numbered steps, logging)

### Data Handling - Credential Security ✅ PASS
- Uses existing credentials.toml (no new credential handling)
- No credentials in logs (existing pattern)

### Data Handling - Database Schema ✅ PASS
- Read-only operations (no schema changes)
- Respects existing SQLAlchemy models

### Development Workflow - Code Organization ✅ PASS
- New export task in `tasks/` submodule
- New export workflow in `workflows/` submodule
- Follows existing organizational pattern

**Constitution Check Result**: ✅ ALL GATES PASSED - No violations, no complexity tracking needed

### Post-Design Constitution Recheck (Phase 1 Complete)

**Re-evaluation Date**: 2026-02-08
**Design Artifacts**: research.md, data-model.md, contracts/cli-interface.md, quickstart.md

#### Principle I: Data Integrity First ✅ PASS
- Design maintains read-only operations
- No modifications to existing pipeline stages
- Data type preservation explicitly defined in data-model.md
- Timestamp precision (microseconds) and timezone handling documented

#### Principle II: Single-User Simplicity ✅ PASS
- CLI design remains simple with clear arguments (see cli-interface.md)
- No authentication, authorization, or multi-tenancy added
- Uses existing credentials.toml pattern
- Configuration via CLI args + optional config file (simple TOML)

#### Principle III: Incremental & Resumable ✅ PASS
- Date range filtering enables incremental exports (--start-date, --end-date)
- Integrates with existing run_full_pipeline for latest data fetch
- Partial failure handling allows resuming failed table exports

#### Principle IV: Clear Data Pipeline ✅ PASS
- Export operates on existing pipeline stages (read-only)
- No new pipeline stages introduced
- Maintains existing architecture: raw_events → events → domain tables

#### Principle V: Workflow Orchestration ✅ PASS
- Uses Prefect for orchestration (existing pattern)
- Follows subflow pattern consistent with run_full_pipeline
- Loguru for logging (existing pattern)
- Documented in research.md R3 findings

#### Data Handling ✅ PASS
- No new credential handling
- No schema changes
- Read-only database operations

#### Development Workflow ✅ PASS
- New code follows existing organization:
  - tasks/export.py (task functions)
  - workflows/export_data.py (Prefect flow)
- Only 2 new dependencies added: typer, rich (both lightweight, stable)

**Final Result**: ✅ ALL PRINCIPLES MAINTAINED - Design adheres to constitution, ready for implementation (Phase 2: Tasks)

## Project Structure

### Documentation (this feature)

```text
specs/005-tandem-data-export/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── checklists/          # Specification quality checklist
│   └── requirements.md
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-interface.md # CLI command interface specification
├── research/            # Phase 0 research outputs
│   ├── technical-decisions.md     # Consolidated research findings
│   ├── README_CLI_RESEARCH.md     # CLI research navigation
│   ├── CLI_RESEARCH_SUMMARY.md    # Executive summary
│   ├── CLI_FRAMEWORK_RESEARCH.md  # Deep framework analysis
│   ├── CLI_IMPLEMENTATION_GUIDE.md # Code templates
│   ├── CLI_DECISION_TREE.md       # Visual comparisons
│   └── CLI_QUICK_REFERENCE.md     # Cheat sheet
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/tandem_fetch/
├── db/                  # Existing: Database models
│   ├── base.py
│   ├── raw_events.py
│   ├── events.py
│   ├── cgm_readings.py
│   └── basal_deliveries.py
├── tasks/               # Existing: Prefect task functions
│   ├── auth.py
│   ├── fetch.py
│   ├── raw_events.py
│   └── export.py        # NEW: Export task functions
├── workflows/           # Existing: Prefect workflows
│   └── backfills/
│       ├── run_full_pipeline.py
│       ├── step0_get_all_raw_pump_events.py
│       ├── step1_parse_events_table.py
│       ├── step2_parse_cgm_readings.py
│       ├── step3_parse_basal_deliveries.py
│       └── export_data.py  # NEW: Export workflow
└── definitions.py       # Existing: Project-wide constants (add EXPORT_DIR)

tests/
├── unit/
│   └── test_export.py   # NEW: Unit tests for export logic
└── integration/
    └── test_export_workflow.py  # NEW: Integration tests for export workflow

exports/                 # NEW: Default output directory (gitignored)
```

**Structure Decision**: Single project structure maintained. New export functionality follows existing pattern of tasks/ (Prefect task functions) and workflows/ (Prefect flows). Export output goes to new `exports/` directory at project root (will be added to .gitignore).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - All constitution checks passed without violations.

## Phase 0: Research & Discovery

*Status: ✅ COMPLETED*

Research tasks identified from Technical Context:

### R1: DuckDB Export Performance Benchmarks
**Question**: What is the performance difference between DuckDB COPY command vs. Polars export for different file sizes?

**Research needed**:
- Benchmark COPY vs. Polars for 10k, 100k, 1M records
- Memory usage comparison
- CSV vs. Parquet performance characteristics

### R2: CLI Argument Parsing Best Practices
**Question**: What is the best way to structure CLI commands in Python for the export use case?

**Research needed**:
- Compare argparse (stdlib) vs. Click vs. Typer
- How to handle multiple table selection elegantly
- Date parsing for range filters
- Progress indicator libraries (tqdm, rich, loguru-based)

### R3: Prefect Integration Patterns
**Question**: How should the export workflow integrate with existing Prefect flows?

**Research needed**:
- Should export trigger full pipeline or be standalone?
- How to handle optional data fetch (P1 requires latest data)
- Error handling and retry strategies
- Logging best practices with Prefect + Loguru

### R4: File Path Handling
**Question**: How to handle cross-platform file path creation and validation?

**Research needed**:
- pathlib usage for cross-platform compatibility
- Parent directory creation (FR-007)
- File overwrite strategies (FR-015)
- Special character and space handling in paths

### R5: Date Range Filtering Implementation
**Question**: What is the best way to implement date range filtering with SQLAlchemy + DuckDB?

**Research needed**:
- SQL WHERE clause generation with optional start/end dates
- Date format parsing and validation
- Timezone handling (all timestamps are timezone-aware)

**Output**: All research findings will be consolidated in `research.md` with decisions, rationale, and alternatives considered.

## Phase 1: Design & Contracts

*Status: ✅ COMPLETED*

### Data Model Extraction

From feature spec, three key entities identified for `data-model.md`:

1. **Export Configuration**
   - Table name(s): List[str]
   - Output format: Enum[parquet, csv]
   - File path: Optional[Path]
   - Start date: Optional[datetime]
   - End date: Optional[datetime]
   - Fetch latest: bool (default True for P1)

2. **Data Table**
   - Table name: str (one of: cgm_readings, basal_deliveries, events, raw_events)
   - Schema: Derived from SQLAlchemy models
   - Record count: int
   - Date range: (min_timestamp, max_timestamp)

3. **Export Result**
   - Success: bool
   - Table name: str
   - Output path: Path
   - Record count: int
   - Duration: float (seconds)
   - Error message: Optional[str]

### API Contracts

CLI interface specification will be created in `/contracts/cli-interface.md`:

**Command signature**:
```bash
uv run export-data \
  --tables cgm_readings [basal_deliveries events raw_events] \
  --format [parquet|csv] \
  --output-path path/to/file \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD \
  --fetch-latest [true|false] \
  --overwrite [true|false]
```

**Exit codes**:
- 0: Success
- 1: Invalid arguments
- 2: Table not found
- 3: Export failed
- 4: Network error (fetch failed)

### Quickstart

User guide will be created in `quickstart.md` with:
- Basic usage examples (P1)
- Multi-table export examples (P2)
- CSV export examples (P3)
- Date range filtering examples (P4)
- Troubleshooting common errors

### Agent Context Update

After design completion, run:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This will update `CLAUDE.md` with new technologies:
- DuckDB COPY command for exports
- CLI argument parsing library (TBD in research phase)
- Progress indicator library (TBD in research phase)

## Phase 2: Task Breakdown

*Status: NOT STARTED (Use /speckit.tasks command after Phase 1 completion)*

Task breakdown will be generated from:
- Functional requirements FR-001 through FR-017
- User stories P1 through P4 (prioritized)
- Design artifacts from Phase 1
- Constitution alignment validation

## Notes

### Implementation Order (by Priority)

**P1 - MVP**: Single table export to Parquet with latest data fetch
- Core functionality: validate table, fetch latest, export, progress logging
- Target: cgm_readings table first (most common use case)
- Success criteria: SC-001, SC-002, SC-004, SC-005

**P2 - Multi-table**: Export multiple tables in one command
- Add loop over tables
- Continue on partial failures
- Success criteria: SC-006

**P3 - CSV Support**: Add CSV format option
- Format parameter handling
- CSV-specific options (headers, delimiters, escaping)
- Success criteria: SC-003

**P4 - Date Filtering**: Add date range parameters
- Optional start/end date parsing
- WHERE clause generation
- Success criteria: SC-007

### Key Integration Points

1. **Existing Pipeline Integration**: Reuse `run_full_pipeline:run_full_pipeline()` for data fetching (FR-016)
2. **Database Connection**: Use existing `definitions.DATABASE_URL` pattern
3. **Logging**: Use existing `loguru` logger for progress (FR-008, FR-011)
4. **Error Handling**: Follow existing error handling patterns in workflows/

### Edge Cases Requiring Special Attention

From spec edge cases section:
- Empty table handling (fresh install)
- Disk full / permission denied errors
- Invalid table names
- Invalid date ranges (end before start)
- API unavailable during fetch
- Very large exports (millions of records)
- Existing file handling
- Special characters in paths
- Ctrl+C cancellation (Prefect handles gracefully)

### Success Criteria Mapping

| Success Criteria | Implementation Note |
|------------------|---------------------|
| SC-001: <30s for 100k records | Use DuckDB COPY (fastest method) |
| SC-002: 99% success rate | Robust error handling, validation |
| SC-003: Excel-compatible CSV | Proper escaping, standard delimiters |
| SC-004: Pandas/Polars compatible | Standard parquet schema |
| SC-005: 90% self-explanatory errors | Clear error messages, actionable |
| SC-006: Single command for all tables | Multi-table loop with `--all` flag |
| SC-007: Proportional file size reduction | WHERE clause on timestamp column |
