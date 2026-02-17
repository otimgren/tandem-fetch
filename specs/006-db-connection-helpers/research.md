# Research: Database Connection Helpers

**Feature**: 006-db-connection-helpers
**Date**: 2026-02-16

## Decision 1: Return Type — Engine vs Connection

**Decision**: Return a SQLAlchemy `Engine` rather than a raw `Connection`.

**Rationale**:
- SQLAlchemy 2.x idiomatic pattern is to hand out engines; consumers obtain connections via `engine.connect()` which naturally provides context manager support (FR-008).
- Engines allow consumers to also create ORM `Session` objects if needed, providing more flexibility.
- All existing code in tandem-fetch follows this pattern: `create_engine(DATABASE_URL)` then `engine.connect()`.
- Returning a bare `Connection` creates lifecycle/ownership ambiguity — who closes it? An engine is long-lived and disposable by the consumer.

**Alternatives considered**:
- Returning a `Connection` directly: Rejected because it forces single-use semantics and complicates resource management.
- Returning a `sessionmaker`: Rejected as overly opinionated — not all consumers need ORM sessions.

## Decision 2: Module Location

**Decision**: New module at `src/tandem_fetch/db/connect.py`, re-exported from `src/tandem_fetch/db/__init__.py`.

**Rationale**:
- The `db/` subpackage already contains all database-related code (models, base).
- Constitution principle: "Database models and operations in `db/` submodule."
- A dedicated `connect.py` module keeps it separate from model definitions.
- Re-exporting from `db/__init__.py` makes the public API: `from tandem_fetch.db import get_engine`.

**Alternatives considered**:
- Top-level `src/tandem_fetch/connect.py`: Rejected — database operations belong in the `db/` subpackage.
- Adding to `definitions.py`: Rejected — that module is for constants, not logic.

## Decision 3: Interactive Prompt Mechanism

**Decision**: Use Python's built-in `input()` for the interactive database-missing prompt.

**Rationale**:
- Constitution principle II (Single-User Simplicity): "CLI commands preferred over web interfaces."
- The project already uses `rich` for console output, so we can use it for formatting the prompt message.
- `input()` is the simplest approach that works in any terminal context.
- No new dependencies needed.

**Alternatives considered**:
- `typer.confirm()`: Would add coupling to typer for a simple yes/no prompt. However, typer is already a dependency — this remains a viable alternative.
- `rich.prompt.Confirm`: Also viable since rich is a dependency, but `input()` is simpler.

## Decision 4: Non-Interactive Mode API

**Decision**: Use an `interactive` parameter (default `True`) on the `get_engine()` function.

**Rationale**:
- Simple boolean flag is easy to understand and test.
- Default `True` matches the primary use case (developer at a terminal).
- When `interactive=False` and database is missing, raise `DatabaseNotFoundError` (custom exception) with an informative message.

**Alternatives considered**:
- Separate functions (`get_engine()` vs `get_engine_or_raise()`): Rejected — adds API surface for a single boolean distinction.
- Environment variable (`TANDEM_FETCH_INTERACTIVE=0`): Could be added later but a function parameter is more explicit and testable.

## Decision 5: Pipeline Invocation

**Decision**: Import and call `run_full_pipeline()` from `tandem_fetch.workflows.backfills.run_full_pipeline` when user chooses to fetch data.

**Rationale**:
- The full pipeline flow already exists and is well-tested.
- It handles all 4 stages: fetch raw events → parse → extract CGM → extract basal.
- It runs as a Prefect flow, providing logging and error handling.
- No need to duplicate or wrap this logic.

**Alternatives considered**:
- Calling individual steps: Rejected — the full pipeline already orchestrates them in the correct order.
- Subprocess call to `run-pipeline` CLI: Rejected — unnecessary process overhead when we can call the function directly.

## Decision 6: Custom Exception

**Decision**: Create a `DatabaseNotFoundError` exception class in `src/tandem_fetch/db/connect.py`.

**Rationale**:
- Provides a specific, catchable exception type for external consumers.
- The error message will include the expected database path and instructions to run the pipeline.
- Inherits from `FileNotFoundError` so it's also catchable by standard exception handlers.

**Alternatives considered**:
- Using plain `FileNotFoundError`: Rejected — loses the ability to add context-specific information and be specifically caught.
- Using `RuntimeError`: Rejected — too generic, doesn't convey the specific issue.
