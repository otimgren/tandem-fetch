# Tasks: Database Connection Helpers

**Input**: Design documents from `/specs/006-db-connection-helpers/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.md

**Tests**: Included — SC-005 in spec.md explicitly requires "full unit test coverage for all acceptance scenarios."

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Shared Infrastructure)

**Purpose**: Create the module, custom exception, and public API re-exports that all user stories depend on.

- [X] T001 Create `DatabaseNotFoundError` exception class and `get_engine()` function stub in `src/tandem_fetch/db/connect.py`. The exception inherits from `FileNotFoundError` with a `database_path` attribute (see contracts/api.md). The `get_engine()` stub should accept `interactive: bool = True` and raise `NotImplementedError` for now.
- [X] T002 Update `src/tandem_fetch/db/__init__.py` to re-export `get_engine` and `DatabaseNotFoundError` from `.connect` module, alongside existing model exports.

**Checkpoint**: `from tandem_fetch.db import get_engine, DatabaseNotFoundError` should resolve without errors.

---

## Phase 2: User Story 1 - Connect to Existing Database (Priority: P1) — MVP

**Goal**: When the database file exists, `get_engine()` returns a working SQLAlchemy Engine connected to the DuckDB file.

**Independent Test**: Call `get_engine()` with a valid database file present and verify queries succeed against all tables.

### Implementation for User Story 1

- [X] T003 [US1] Implement the happy path in `get_engine()` in `src/tandem_fetch/db/connect.py`: check that `DATABASE_PATH` from `tandem_fetch.definitions` exists, create a SQLAlchemy engine via `create_engine(DATABASE_URL)`, and return it. If the file does not exist, raise `DatabaseNotFoundError` as a temporary placeholder (US2 and US3 will refine this behavior).
- [X] T004 [US1] Write unit tests for the DB-exists happy path in `tests/unit/test_db/test_connect.py`. Tests should: (1) verify `get_engine()` returns a SQLAlchemy `Engine` when DB file exists, (2) verify the returned engine can execute a query via `engine.connect()`, (3) verify the connection works as a context manager. Use `tmp_path` and a temporary DuckDB file for isolation (not in-memory, since the feature checks file existence).

**Checkpoint**: `get_engine()` returns a working Engine when the DB file exists. Tests pass.

---

## Phase 3: User Story 2 - Database Missing with Recovery Option (Priority: P2)

**Goal**: When the database file is missing and `interactive=True` (default), prompt the user to either fetch data via the pipeline or exit gracefully.

**Independent Test**: Call `get_engine()` when DB file is missing, mock `input()` to simulate user choices, and verify correct behavior for both "yes" and "no" responses.

### Implementation for User Story 2

- [X] T005 [US2] Add interactive prompt logic to `get_engine()` in `src/tandem_fetch/db/connect.py`. When `interactive=True` and DB file is missing: (1) print a message explaining the database was not found at the expected path, (2) use `input()` to ask if the user wants to fetch data now, (3) if yes, import and call `run_full_pipeline` from `tandem_fetch.workflows.backfills.run_full_pipeline`, then return the engine, (4) if no, print instructions for running `run-pipeline` manually and return `None`.
- [X] T006 [US2] Write unit tests for interactive missing-DB scenarios in `tests/unit/test_db/test_connect.py`. Tests should: (1) mock `input()` returning "y" and mock `run_full_pipeline`, verify pipeline is called and engine is returned (create the DB file in the mock to simulate pipeline success), (2) mock `input()` returning "n", verify `None` is returned and no pipeline is called, (3) verify the prompt message includes the database path.

**Checkpoint**: Interactive prompt works for both "yes" and "no" user responses. Tests pass.

---

## Phase 4: User Story 3 - Programmatic Non-Interactive Mode (Priority: P3)

**Goal**: When `interactive=False` and the database file is missing, raise `DatabaseNotFoundError` with an informative message instead of prompting.

**Independent Test**: Call `get_engine(interactive=False)` when DB file is missing and verify `DatabaseNotFoundError` is raised with the correct path and message.

### Implementation for User Story 3

- [X] T007 [US3] Refine the missing-DB branch in `get_engine()` in `src/tandem_fetch/db/connect.py`. When `interactive=False` and DB file is missing, raise `DatabaseNotFoundError` with `database_path` set and a message including the expected path and instructions to run `run-pipeline`. Ensure the `interactive=True` path from US2 is checked first (i.e., `if not interactive: raise DatabaseNotFoundError(...)`).
- [X] T008 [US3] Write unit tests for non-interactive missing-DB scenarios in `tests/unit/test_db/test_connect.py`. Tests should: (1) verify `DatabaseNotFoundError` is raised when `interactive=False` and DB missing, (2) verify the exception's `database_path` attribute matches the expected path, (3) verify the exception is catchable as `FileNotFoundError`, (4) verify `get_engine(interactive=False)` still returns an Engine when DB exists (same as US1 happy path).

**Checkpoint**: All three code paths work correctly. Full test suite passes.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup.

- [X] T009 Run full test suite (`pytest`) and verify all existing tests still pass alongside new tests.
- [X] T010 Validate quickstart.md examples work against the real database (manual check - verified implementation matches spec).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — creates module and re-exports
- **User Story 1 (Phase 2)**: Depends on Phase 1 — implements happy path
- **User Story 2 (Phase 3)**: Depends on Phase 2 — adds interactive prompt to existing function
- **User Story 3 (Phase 4)**: Depends on Phase 2 — adds non-interactive error raising (can be done in parallel with US2 if careful about merge)
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundational only — no dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (extends the same function's missing-DB branch)
- **User Story 3 (P3)**: Depends on US1 (extends the same function's missing-DB branch). Can be implemented in parallel with US2 since they modify different code paths within the same branch.

### Within Each User Story

- Implementation before tests (tests validate the implementation)
- Each story builds on the same file (`connect.py`) incrementally

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T003 and T004 are sequential (implement then test)
- US2 (T005-T006) and US3 (T007-T008) could theoretically run in parallel since they handle different branches (`interactive=True` vs `interactive=False`), but since they modify the same file, sequential execution is safer
- T009 and T010 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (T001-T002)
2. Complete Phase 2: User Story 1 (T003-T004)
3. **STOP and VALIDATE**: `get_engine()` works when DB exists
4. This alone provides value — external packages can connect to the database

### Incremental Delivery

1. Phase 1 → Module and exception class ready
2. Phase 2 (US1) → Core connection works → MVP
3. Phase 3 (US2) → Interactive recovery for missing DB
4. Phase 4 (US3) → Non-interactive error handling for automation
5. Phase 5 → Full validation

---

## Notes

- All tasks modify only 3 files total: `connect.py` (new), `__init__.py` (modify), `test_connect.py` (new)
- Tests use `tmp_path` with real DuckDB files (not in-memory) to properly test file-existence checks
- Pipeline invocation in US2 is mocked in tests — no actual API calls or data fetching
- Commit after each phase for clean git history
