# Implementation Plan: Database Connection Helpers

**Branch**: `006-db-connection-helpers` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-db-connection-helpers/spec.md`

## Summary

Add a `get_engine()` helper function to `tandem_fetch.db` that external packages can call to obtain a SQLAlchemy Engine connected to the local DuckDB database. The function validates that the database file exists, and when it's missing, either prompts the user interactively to fetch data (via the existing pipeline) or raises a `DatabaseNotFoundError` in non-interactive mode.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: SQLAlchemy 2.x, duckdb-engine, Prefect (for pipeline invocation)
**Storage**: DuckDB local file at `data/tandem.db`
**Testing**: pytest with in-memory DuckDB, Prefect test harness
**Target Platform**: Local development (macOS/Linux)
**Project Type**: Single project (Python library + CLI)
**Performance Goals**: N/A — connection establishment is a one-time operation
**Constraints**: Must work with existing DuckDB file format and SQLAlchemy engine patterns
**Scale/Scope**: Single user, single database file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Read-only access for external consumers. Pipeline invocation uses existing tested flow. |
| II. Single-User Simplicity | PASS | Single function, simple `input()` prompt, no authentication or config systems. |
| III. Incremental & Resumable | PASS | Pipeline invocation uses existing incremental logic. Not directly applicable to connection helper itself. |
| IV. Clear Data Pipeline | PASS | No new pipeline stages. Helper provides access to existing pipeline output. |
| V. Workflow Orchestration | PASS | Pipeline triggering uses existing Prefect flow (`run_full_pipeline`). |
| Code Organization | PASS | New module in `db/` subpackage per constitution: "Database models and operations in `db/` submodule." |
| Testing Philosophy | PASS | Unit tests for connection logic, integration tested via existing pipeline tests. |

**Post-Phase 1 Re-check**: All gates still pass. The design adds one module with one public function — minimal complexity, no new dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/006-db-connection-helpers/
├── plan.md              # This file
├── research.md          # Phase 0: design decisions and rationale
├── data-model.md        # Phase 1: entity overview and state transitions
├── quickstart.md        # Phase 1: usage guide
├── contracts/
│   └── api.md           # Phase 1: public API contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/tandem_fetch/
├── db/
│   ├── __init__.py          # Modified: re-export get_engine, DatabaseNotFoundError
│   ├── connect.py           # NEW: get_engine(), DatabaseNotFoundError
│   ├── base.py              # Unchanged
│   ├── raw_events.py        # Unchanged
│   ├── events.py            # Unchanged
│   ├── cgm_readings.py      # Unchanged
│   └── basal_deliveries.py  # Unchanged
└── ...                      # All other modules unchanged

tests/
├── unit/
│   └── test_db/
│       └── test_connect.py  # NEW: unit tests for get_engine
└── ...                      # All other tests unchanged
```

**Structure Decision**: Single project structure. This feature adds one new module (`db/connect.py`) and one test file (`test_connect.py`) to the existing layout. No structural changes needed.
