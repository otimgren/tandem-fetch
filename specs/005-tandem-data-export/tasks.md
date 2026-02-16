# Tasks: Tandem Data Export Command

**Input**: Design documents from `/specs/005-tandem-data-export/`
**Prerequisites**: plan.md (tech stack), spec.md (user stories), data-model.md (entities), contracts/cli-interface.md (CLI spec)

**Tests**: No test tasks included - feature spec does not explicitly request TDD approach. Tests can be added separately if needed.

**Organization**: Tasks are grouped by user story (P1-P4) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project structure at repository root:
- Source: `src/tandem_fetch/`
- Tests: `tests/`
- Exports: `exports/` (new directory)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [x] T001 Add typer and rich dependencies to pyproject.toml [project.dependencies]
- [x] T002 Add export-data entry point to pyproject.toml [project.scripts] pointing to tandem_fetch.workflows.export_data:main
- [x] T003 Create exports/ directory and add to .gitignore
- [x] T004 Add EXPORT_DIR constant to src/tandem_fetch/definitions.py (default: ROOT_DIR / "exports")

**Checkpoint**: Dependencies installed, project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core export infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create ExportConfig dataclass in src/tandem_fetch/tasks/export.py with validation
- [x] T006 [P] Create ExportResult NamedTuple in src/tandem_fetch/tasks/export.py
- [x] T007 [P] Create ExportSummary dataclass in src/tandem_fetch/tasks/export.py
- [x] T008 Implement build_export_query() function in src/tandem_fetch/tasks/export.py (handles SQL generation with optional WHERE clause)
- [x] T009 Implement resolve_output_path() function in src/tandem_fetch/tasks/export.py (handles path resolution, directory creation, filename generation)
- [x] T010 [P] Implement validate_table_name() function in src/tandem_fetch/tasks/export.py (validates against VALID_TABLES constant)
- [x] T011 [P] Implement validate_date_range() function in src/tandem_fetch/tasks/export.py (ensures start_date <= end_date)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Export CGM Readings to Parquet (Priority: P1) 🎯 MVP

**Goal**: Enable single-table export to Parquet format with latest data fetch and progress indicators

**Independent Test**: Run `uv run export-data --tables cgm_readings`, verify parquet file created in exports/ with valid CGM data

**Acceptance Criteria**:
- FR-001: Fetches latest data before export
- FR-002: Exports to parquet format
- FR-004: Output file path specification
- FR-005: Table selection
- FR-006: Table validation
- FR-007: Parent directory creation
- FR-008: Progress indicators
- FR-009: Graceful error handling
- FR-011: Export logging
- FR-016: Full pipeline before export
- FR-017: Data type preservation

**Success Criteria**: SC-001 (export <30s for 100k records), SC-002 (99% success rate), SC-004 (pandas/polars compatible), SC-005 (90% self-explanatory errors)

### Implementation for User Story 1

- [x] T012 [US1] Implement validate_export_config() Prefect task in src/tandem_fetch/tasks/export.py (validates tables exist, output writable)
- [x] T013 [US1] Implement export_table_to_file() Prefect task in src/tandem_fetch/tasks/export.py (DuckDB COPY to parquet with progress logging)
- [x] T014 [US1] Implement run_export() Prefect flow in src/tandem_fetch/workflows/export_data.py (orchestrates single table export)
- [x] T015 [US1] Implement export_orchestrator_flow() Prefect flow in src/tandem_fetch/workflows/export_data.py (optional pipeline + export)
- [x] T016 [US1] Create Typer CLI application with --tables argument in src/tandem_fetch/workflows/export_data.py
- [x] T017 [US1] Add --format argument with parquet default to CLI in src/tandem_fetch/workflows/export_data.py
- [x] T018 [US1] Add --output-dir argument with exports/ default to CLI in src/tandem_fetch/workflows/export_data.py
- [x] T019 [US1] Add --fetch-latest/--no-fetch flag with True default to CLI in src/tandem_fetch/workflows/export_data.py
- [x] T020 [US1] Add --verbose flag for detailed logging to CLI in src/tandem_fetch/workflows/export_data.py
- [x] T021 [US1] Implement main() entry point function in src/tandem_fetch/workflows/export_data.py
- [x] T022 [US1] Add progress bar using rich.progress in export_table_to_file() task
- [x] T023 [US1] Add error handling with actionable messages in export_orchestrator_flow()
- [x] T024 [US1] Add loguru logging for all export operations (table, format, record count, duration)

**Checkpoint**: User Story 1 (P1/MVP) complete - single table parquet export works end-to-end

---

## Phase 4: User Story 2 - Export Multiple Tables (Priority: P2)

**Goal**: Enable multi-table export in a single command with partial failure handling

**Independent Test**: Run `uv run export-data --tables cgm_readings basal_deliveries events`, verify 3 separate parquet files created

**Acceptance Criteria**:
- FR-012: Multi-table export in single command
- Partial failure handling (continue on errors)

**Success Criteria**: SC-006 (all tables with single command flag)

**Dependencies**: Requires User Story 1 (P1) complete

### Implementation for User Story 2

- [x] T025 [US2] Update run_export() flow in src/tandem_fetch/workflows/export_data.py to iterate over multiple tables
- [x] T026 [US2] Modify export_table_to_file() task in src/tandem_fetch/tasks/export.py to return ExportResult (success/failure) instead of raising
- [x] T027 [US2] Implement aggregate_export_results() task in src/tandem_fetch/tasks/export.py (collects results, determines overall success)
- [x] T028 [US2] Update export_orchestrator_flow() in src/tandem_fetch/workflows/export_data.py to handle multiple ExportResult objects
- [x] T029 [US2] Add multi-table progress indicator in export_orchestrator_flow() showing "Exporting N of M tables"
- [x] T030 [US2] Update CLI output in main() to show summary for multi-table exports (successful, failed, file list)
- [x] T031 [US2] Implement exit code 5 for partial success in main() function

**Checkpoint**: User Stories 1 AND 2 complete - multi-table export with partial failure handling works

---

## Phase 5: User Story 3 - Export to CSV Format (Priority: P3)

**Goal**: Enable CSV format export for Excel/spreadsheet compatibility

**Independent Test**: Run `uv run export-data --tables cgm_readings --format csv`, verify CSV file opens in Excel with proper formatting

**Acceptance Criteria**:
- FR-003: CSV format support
- FR-017: Data type preservation in CSV

**Success Criteria**: SC-003 (Excel-compatible without formatting issues)

**Dependencies**: Requires User Story 1 (P1) complete; independent of User Story 2

### Implementation for User Story 3

- [x] T032 [US3] Update build_export_query() in src/tandem_fetch/tasks/export.py to generate COPY statement for CSV format
- [x] T033 [US3] Update export_table_to_file() task in src/tandem_fetch/tasks/export.py to handle format parameter (parquet/csv)
- [x] T034 [US3] Add CSV-specific COPY options in export_table_to_file(): HEADER TRUE, DELIMITER ','
- [x] T035 [US3] Update validate_export_config() in src/tandem_fetch/tasks/export.py to validate format is "parquet" or "csv"
- [x] T036 [US3] Update resolve_output_path() in src/tandem_fetch/tasks/export.py to use correct file extension based on format

**Checkpoint**: User Stories 1, 2, AND 3 complete - CSV export works for all tables

---

## Phase 6: User Story 4 - Date Range Filtering (Priority: P4)

**Goal**: Enable incremental exports with date range filters for reduced file sizes

**Independent Test**: Run `uv run export-data --tables cgm_readings --start-date 2026-01-01 --end-date 2026-01-31`, verify output contains only January records

**Acceptance Criteria**:
- FR-013: Date range filtering support
- FR-014: Date range validation

**Success Criteria**: SC-007 (proportional file size reduction)

**Dependencies**: Requires User Story 1 (P1) complete; independent of User Stories 2 and 3

### Implementation for User Story 4

- [x] T037 [US4] Add --start-date argument with date type to CLI in src/tandem_fetch/workflows/export_data.py
- [x] T038 [US4] Add --end-date argument with date type to CLI in src/tandem_fetch/workflows/export_data.py
- [x] T039 [US4] Update ExportConfig dataclass in src/tandem_fetch/tasks/export.py to include start_date and end_date fields
- [x] T040 [US4] Update build_export_query() in src/tandem_fetch/tasks/export.py to add WHERE clause for date filtering
- [x] T041 [US4] Implement date-to-datetime conversion in build_export_query() (start: 00:00:00, end: 23:59:59)
- [x] T042 [US4] Update validate_export_config() in src/tandem_fetch/tasks/export.py to call validate_date_range()
- [x] T043 [US4] Add date range to log messages in export_table_to_file() task
- [x] T044 [US4] Update CLI output in main() to show date range in summary if provided

**Checkpoint**: All user stories (P1-P4) complete - full feature set implemented

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Additional features and refinements that enhance all user stories

- [x] T045 [P] Add --overwrite flag to CLI in src/tandem_fetch/workflows/export_data.py (FR-015)
- [x] T046 [P] Implement handle_existing_file() function in src/tandem_fetch/tasks/export.py with overwrite logic
- [x] T047 [P] Add file overwrite confirmation prompt using typer.confirm() when overwrite=False
- [x] T048 Add --help flag with comprehensive help text and examples to CLI
- [x] T049 Add exit code handling (0-5) in main() function per contracts/cli-interface.md
- [x] T050 [P] Add input validation error messages with suggestions (e.g., "did you mean cgm_readings?")
- [x] T051 [P] Update quickstart.md with actual command examples once implementation complete
- [x] T052 Add edge case handling: empty table (warn but succeed with 0 rows exported)
- [x] T053 Add edge case handling: disk full (catch and provide actionable error)
- [x] T054 Add edge case handling: invalid path characters (sanitize or reject with clear message)
- [x] T055 Add Ctrl+C graceful shutdown (Prefect handles this automatically, verify it works)

**Checkpoint**: Feature complete, polished, and ready for production use

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - MVP delivery
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) AND User Story 1 (Phase 3) - builds on single-table export
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) AND User Story 1 (Phase 3) - parallel to US2
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) AND User Story 1 (Phase 3) - parallel to US2 and US3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Setup (Phase 1)
    ↓
Foundational (Phase 2) [BLOCKS ALL]
    ↓
    ├─→ User Story 1 (P1/MVP) [Phase 3] ← Start here
    │       ↓
    │   ┌───┴───┬──────────┬──────────┐
    │   ↓       ↓          ↓          ↓
    │   US2     US3        US4       Polish
    │  (P2)    (P3)       (P4)     (Phase 7)
    │   │       │          │          │
    │   └───────┴──────────┴──────────┘
    │                 ↓
    └───────→ Complete Feature
```

**Key Relationships**:
- **US1 (P1)**: Foundation for all other stories - MUST complete first
- **US2 (P2)**: Extends US1 for multiple tables
- **US3 (P3)**: Extends US1 for CSV format (parallel to US2)
- **US4 (P4)**: Extends US1 for date filtering (parallel to US2 and US3)

### Within Each User Story

- Foundational tasks (T005-T011) before any story-specific tasks
- Core functions (build_export_query, resolve_output_path) before Prefect tasks
- Prefect tasks before Prefect flows
- Flows before CLI implementation
- CLI implementation before CLI arguments/flags
- Progress/error handling after core functionality

### Parallel Opportunities

**Phase 1 (Setup)**: All tasks can run in parallel (different sections of pyproject.toml and definitions.py)

**Phase 2 (Foundational)**: T005, T006, T007 can run in parallel (different dataclasses), T010 and T011 can run in parallel after T008 and T009

**Phase 3 (User Story 1)**: T016-T020 (CLI arguments) can run in parallel after T015 is complete

**Phase 5 (User Story 3)**: All US3 tasks are independent modifications - can work in parallel if careful with merge conflicts

**Phase 7 (Polish)**: T045-T047 (overwrite), T050 (validation errors), T051 (docs), T052-T054 (edge cases) can all run in parallel

**Across User Stories**: After US1 (P1) is complete, US2 (P2), US3 (P3), and US4 (P4) can be developed in parallel by different developers

---

## Parallel Example: User Story 1 (MVP)

After completing Foundational phase, User Story 1 can proceed with some parallelization:

```bash
# Step 1: Core implementation (sequential)
Task T012: validate_export_config() task
Task T013: export_table_to_file() task
Task T014: run_export() flow
Task T015: export_orchestrator_flow()

# Step 2: CLI arguments (parallel after T015)
Task T016: CLI app with --tables
Task T017: --format argument
Task T018: --output-dir argument
Task T019: --fetch-latest flag
Task T020: --verbose flag

# Step 3: Polish (sequential)
Task T021: main() entry point
Task T022: Progress bars
Task T023: Error handling
Task T024: Logging
```

**Parallel execution for CLI arguments reduces US1 time by ~50%**

---

## Parallel Example: After MVP (US2, US3, US4)

Once User Story 1 (P1/MVP) is complete, the remaining stories can proceed in parallel:

```bash
# Developer A: User Story 2 (Multi-table)
Task T025-T031: Multi-table export with partial failures

# Developer B: User Story 3 (CSV format)
Task T032-T036: CSV format support

# Developer C: User Story 4 (Date filtering)
Task T037-T044: Date range filtering

# All converge to Phase 7 (Polish) after their stories complete
```

**Team of 3 can deliver US2, US3, US4 in parallel, reducing overall time by ~60%**

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Goal**: Deliver minimum viable product quickly

1. **Phase 1**: Setup (T001-T004) - ~30 minutes
2. **Phase 2**: Foundational (T005-T011) - ~2 hours
3. **Phase 3**: User Story 1 (T012-T024) - ~4 hours
4. **VALIDATE**: Test single-table parquet export end-to-end
5. **DEPLOY**: Merge to main, tag as v1.0.0-mvp

**Total MVP time**: ~6.5 hours (single developer)

**MVP delivers**:
- Core export functionality
- Parquet format (most efficient)
- Single table at a time
- Validates all core patterns work

### Incremental Delivery (Recommended)

**Goal**: Add features incrementally, testing each independently

1. **Foundation** (Phases 1-2): Setup + Foundational - ~2.5 hours
2. **MVP** (Phase 3): User Story 1 → Test → Deploy (v1.0) - ~4 hours
3. **Multi-table** (Phase 4): User Story 2 → Test → Deploy (v1.1) - ~2 hours
4. **CSV Support** (Phase 5): User Story 3 → Test → Deploy (v1.2) - ~1.5 hours
5. **Date Filtering** (Phase 6): User Story 4 → Test → Deploy (v1.3) - ~2 hours
6. **Polish** (Phase 7): Polish tasks → Test → Deploy (v1.4) - ~2 hours

**Total time**: ~14 hours (single developer, sequential)

**Benefits**:
- Each deployment is independently valuable
- Users get value sooner (MVP after 6.5 hours)
- Can stop at any point if priorities change
- Each story is fully tested before proceeding

### Parallel Team Strategy

**Goal**: Maximize velocity with multiple developers

**Team of 2**:
1. Both: Complete Phases 1-2 (Foundation) together - ~2.5 hours
2. Both: Complete Phase 3 (US1/MVP) together - ~4 hours
3. **Split work**:
   - Developer A: Phase 4 (US2 - Multi-table)
   - Developer B: Phase 5 (US3 - CSV) + Phase 6 (US4 - Date filtering)
4. Both: Phase 7 (Polish) together

**Time savings**: Complete in ~11 hours vs. 14 hours (20% faster)

**Team of 3**:
1. All: Phases 1-3 (Foundation + MVP) together - ~6.5 hours
2. **Split work**:
   - Developer A: Phase 4 (US2)
   - Developer B: Phase 5 (US3)
   - Developer C: Phase 6 (US4)
3. All: Phase 7 (Polish) together

**Time savings**: Complete in ~10 hours vs. 14 hours (30% faster)

---

## Task Count Summary

| Phase | Task Count | Parallelizable | Estimated Time |
|-------|------------|----------------|----------------|
| Phase 1: Setup | 4 | 3 | 30 min |
| Phase 2: Foundational | 7 | 4 | 2 hours |
| Phase 3: US1 (MVP) | 13 | 5 | 4 hours |
| Phase 4: US2 (Multi-table) | 7 | 0 | 2 hours |
| Phase 5: US3 (CSV) | 5 | 0 | 1.5 hours |
| Phase 6: US4 (Date filtering) | 8 | 0 | 2 hours |
| Phase 7: Polish | 11 | 6 | 2 hours |
| **Total** | **55 tasks** | **18 parallel** | **~14 hours** |

**Parallel opportunities**: 33% of tasks can run in parallel (18 of 55)

**MVP scope**: 24 tasks (Phases 1-3) deliver functional single-table parquet export

---

## Notes

- **[P] marker**: Task can run in parallel with others (different files, no dependencies)
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- **Independent testability**: Each user story can be tested on its own without requiring other stories
- **File paths**: All file paths are explicit - ready for immediate implementation
- **Constitution compliance**: All tasks maintain read-only operations, use existing patterns, follow single-user simplicity
- **DuckDB COPY**: Core export uses native DuckDB COPY command for optimal performance (R1 research finding)
- **Typer CLI**: Type-safe CLI with automatic validation (R2 research finding)
- **Prefect patterns**: Subflow pattern matching existing run_full_pipeline architecture (R3 research finding)
- **Error handling**: Graceful degradation for partial failures, actionable error messages
- **Progress indicators**: Rich progress bars for user feedback during long exports
- **Logging**: Loguru for all operations (table, format, record count, duration)

**Checkpoint validation**: Stop after each phase checkpoint to verify independent functionality before proceeding

**Commit strategy**: Commit after completing each task or logical group (e.g., all CLI arguments together)

**Testing strategy**: Manual testing after each checkpoint using examples from quickstart.md
