# Tasks: Continuous Data Fetch

**Input**: Design documents from `/specs/008-continuous-fetch/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli.md

**Tests**: Included — the spec references unit tests for interval validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add the entry point and install dependencies

- [x] T001 Add `continuous-fetch` script entry point to `pyproject.toml` pointing to `tandem_fetch.workflows.continuous_fetch:main`
- [x] T002 Run `uv sync --all-groups` to install updated entry point

---

## Phase 2: User Story 1 - Start Continuous Data Fetching (Priority: P1) 🎯 MVP

**Goal**: A `continuous-fetch` command that uses Prefect `flow.serve()` to run the existing full pipeline on a 5-minute default interval, with graceful Ctrl+C shutdown and overlap prevention.

**Independent Test**: Run `continuous-fetch`, verify the pipeline runs immediately, then repeats on schedule. Press Ctrl+C to stop.

**Maps to**: FR-001, FR-002, FR-005, FR-006, FR-007, FR-009, FR-010

### Implementation

- [x] T003 [US1] Create `src/tandem_fetch/workflows/continuous_fetch.py` with: (1) a `main()` function using Typer that accepts `--interval` (default 5, min 1), (2) startup log messages per CLI contract, (3) call `run_full_pipeline.serve(name="continuous-fetch", interval=timedelta(minutes=interval), limit=1)` to start the long-running process
- [x] T004 [US1] Write unit tests in `tests/unit/test_workflows/test_continuous_fetch.py`: test that `main()` calls `serve()` with correct default interval (5 min) and `limit=1`; test startup log output

**Checkpoint**: `continuous-fetch` works with 5-minute default interval, graceful shutdown, and overlap prevention (all provided by Prefect `flow.serve()`)

---

## Phase 3: User Story 2 - Configurable Fetch Interval (Priority: P2)

**Goal**: Users can pass `--interval N` to set a custom interval in minutes, with validation enforcing a minimum of 1 minute.

**Independent Test**: Run `continuous-fetch --interval 1` and verify 1-minute cycles. Run `continuous-fetch --interval 0` and verify error message.

**Maps to**: FR-003, FR-004

### Implementation

- [x] T005 [US2] Add interval validation in `src/tandem_fetch/workflows/continuous_fetch.py`: reject values < 1 with error message "Interval must be at least 1 minute." (use Typer callback or early check in `main()`)
- [x] T006 [US2] Write unit tests in `tests/unit/test_workflows/test_continuous_fetch.py`: test custom interval is passed to `serve()`; test interval=0 raises error; test interval=-5 raises error

**Checkpoint**: Custom intervals work, invalid values are rejected with clear error messages

---

## Phase 4: User Story 3 - Resilient Operation Through Transient Failures (Priority: P2)

**Goal**: Failed cycles don't stop the process. Prefect's `flow.serve()` provides this inherently — failed flow runs are logged but scheduling continues.

**Independent Test**: Verify that Prefect's built-in error handling is configured (no custom error handling needed beyond what `flow.serve()` provides).

**Maps to**: FR-008

### Implementation

- [x] T007 [US3] Verify and document in `src/tandem_fetch/workflows/continuous_fetch.py` that `flow.serve()` naturally handles transient errors (failed runs don't stop scheduling). No additional code needed — Prefect provides this behavior. Add a brief docstring or comment confirming this design decision.

**Checkpoint**: Error resilience is handled by Prefect — no custom error handling code required

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T008 Run full test suite (`uv run pytest`) to verify no regressions
- [x] T009 Validate quickstart.md by running `continuous-fetch` and `continuous-fetch --interval 1`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on Phase 1 — creates the core module
- **US2 (Phase 3)**: Depends on Phase 2 — adds validation to the same file
- **US3 (Phase 4)**: Depends on Phase 2 — verifies built-in behavior
- **Polish (Phase 5)**: Depends on all user stories being complete

### Within Each User Story

- Implementation before tests (tests verify serve() is called correctly via mocking)
- T003 is the core task — T004, T005, T006, T007 all build on it

### Parallel Opportunities

- T005 and T007 can run in parallel (different concerns in the same file, but non-overlapping changes)
- T004 and T006 test different behaviors and can be written in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: User Story 1 (T003-T004)
3. **STOP and VALIDATE**: Run `continuous-fetch` and verify it works
4. This alone delivers the core value — automated continuous data fetching

### Incremental Delivery

1. Setup → US1 → Validate (MVP — continuous fetch with 5-min default)
2. Add US2 → Validate (custom intervals with validation)
3. Add US3 → Validate (confirm error resilience)
4. Polish → Final validation

---

## Notes

- This is a small feature (~50-80 lines of new code) with most complexity handled by Prefect's `flow.serve()`
- The existing `run_full_pipeline` flow is reused as-is — no modifications needed
- Error resilience (US3) requires no new code — it's inherent to `flow.serve()` behavior
- All 9 tasks, most sequential due to single-file implementation
