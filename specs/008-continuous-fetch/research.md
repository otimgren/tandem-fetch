# Research: Continuous Data Fetch

**Feature**: 008-continuous-fetch
**Date**: 2026-02-28

## R1: Scheduling Mechanism

**Decision**: Prefect `flow.serve()` with `interval` parameter

**Rationale**: Prefect is already the workflow orchestrator in this project (Constitution Principle V). `flow.serve()` creates a long-running foreground process that schedules the flow at a fixed interval — exactly what's needed. It provides built-in error handling (failed runs don't stop scheduling), concurrency control (`limit=1` prevents overlapping runs), and graceful shutdown on Ctrl+C. No new dependencies required.

**Alternatives considered**:
- Simple `while True` loop with `time.sleep()`: Simpler but loses Prefect's error tracking, retry logic, and observability. Would also require manual overlap prevention and signal handling.
- System cron: Not portable, external to the project, and harder to configure. Doesn't align with single-user CLI simplicity.
- Prefect deployment + worker: Over-engineered for a single-user local process. Requires running a separate worker process and Prefect server.

## R2: Interval Configuration

**Decision**: Accept interval as a CLI argument (in minutes) with a default of 5 minutes and a minimum of 1 minute. Use Typer for CLI parsing (already a project dependency).

**Rationale**: Typer is already used in the project for CLI commands (e.g., `export-data`). Accepting the interval as a CLI argument is the simplest UX — no config files, no environment variables. Minutes are the natural unit for this cadence.

**Alternatives considered**:
- Seconds as the unit: Too granular for the use case. Users think in minutes for fetch intervals.
- Config file: Over-engineered for a single parameter. CLI argument is simpler and more discoverable.

## R3: Error Recovery

**Decision**: Use Prefect's built-in behavior — failed flow runs are logged but don't stop scheduling. Each cycle is an independent flow run. Optionally add `retries=1` to the flow for immediate retry of transient failures within a cycle.

**Rationale**: Prefect's `flow.serve()` naturally continues scheduling after a failed run. The existing pipeline already handles incremental state via the database (last event timestamp), so a failed cycle doesn't lose progress — the next cycle picks up where it left off. Adding a single retry gives one immediate re-attempt before waiting for the next interval.

**Alternatives considered**:
- Exponential backoff on failure: Unnecessary complexity. The interval itself provides natural backoff (5 minutes between attempts).
- Circuit breaker pattern: Over-engineered for single-user local use.

## R4: Overlap Prevention

**Decision**: Use `limit=1` parameter in `flow.serve()` to prevent concurrent runs.

**Rationale**: If a cycle takes longer than the interval, Prefect will queue the next run and execute it after the current one completes. This is the built-in mechanism — no custom locking needed.

## R5: Entry Point

**Decision**: Add `continuous-fetch` script entry point in pyproject.toml pointing to a `main()` function in `tandem_fetch.workflows.continuous_fetch`.

**Rationale**: Follows the existing pattern of CLI entry points (run-pipeline, export-data, tandem-mcp). The `main()` function uses Typer to parse the interval argument, then calls `flow.serve()`.
