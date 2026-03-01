# Implementation Plan: Continuous Data Fetch

**Branch**: `008-continuous-fetch` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-continuous-fetch/spec.md`

## Summary

Add a `continuous-fetch` CLI command that uses Prefect's `flow.serve()` to run the existing full data pipeline on a configurable interval (default 5 minutes). The served flow runs as a foreground process, handles transient errors via Prefect's built-in retry mechanism, prevents overlapping runs via concurrency limits, and stops gracefully on Ctrl+C.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Prefect 3.4.17 (existing), Loguru 0.7.3 (existing), Typer 0.12.0 (existing)
**Storage**: DuckDB local file at `data/tandem.db` (existing)
**Testing**: pytest 8.0 with pytest-xdist, Prefect test harness (existing)
**Target Platform**: macOS (local CLI, foreground process)
**Project Type**: Single project — new workflow + CLI entry point in existing package
**Performance Goals**: Pipeline cycle completes within the configured interval under normal conditions
**Constraints**: Minimum 1-minute interval; no overlapping cycles; single concurrent user
**Scale/Scope**: 1 new workflow file, 1 new CLI entry point, ~50-80 lines of new code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Reuses existing incremental pipeline. No new data path. Transient failures don't corrupt data — failed cycles are skipped cleanly. |
| II. Single-User Simplicity | PASS | Foreground CLI process. No daemon, no service manager, no web UI. Start with a command, stop with Ctrl+C. |
| III. Incremental & Resumable | PASS | Each cycle uses existing incremental logic (fetches only new data since last event). Constitution explicitly states: "Future scheduled fetches MUST use the same incremental logic." |
| IV. Clear Data Pipeline | PASS | Each cycle runs the full 4-stage pipeline (fetch → parse → extract CGM → extract basal). No partial runs. |
| V. Workflow Orchestration | PASS | Uses Prefect `flow.serve()` for scheduling — the existing workflow orchestrator. Provides logging, error tracking, and observability. |
| Credential Security | PASS | No credential changes. Existing auth flow handles token refresh. |
| Code Organization | PASS | New workflow in `workflows/` submodule. New CLI entry point in pyproject.toml. Follows existing patterns. |
| Dependency Management | PASS | No new dependencies. Prefect, Loguru, and Typer are all existing. |
| Testing Philosophy | PASS | Unit tests for interval validation; integration test for serve configuration. |

**Result**: All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/008-continuous-fetch/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli.md           # CLI contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/tandem_fetch/
├── workflows/
│   ├── backfills/
│   │   └── run_full_pipeline.py  # EXISTING — reused as the flow to serve
│   └── continuous_fetch.py       # NEW — serve() wrapper with interval config
└── definitions.py                # EXISTING — may add default interval constant

tests/unit/
└── test_workflows/
    └── test_continuous_fetch.py   # NEW — interval validation tests

pyproject.toml                     # MODIFIED — add continuous-fetch entry point
```

**Structure Decision**: Single new workflow file `continuous_fetch.py` in the existing `workflows/` submodule. This file wraps `run_full_pipeline` with Prefect's `flow.serve()` and provides CLI argument parsing for the interval. Follows the existing pattern of workflow files in this directory.
