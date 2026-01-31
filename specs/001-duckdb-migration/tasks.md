# Tasks: DuckDB Migration

**Input**: Design documents from `/specs/001-duckdb-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No test tasks included (not explicitly requested in specification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/tandem_fetch/` at repository root
- Database models in `src/tandem_fetch/db/`
- Workflows in `src/tandem_fetch/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Update dependencies and create directory structure

- [ ] T001 Update pyproject.toml: remove `psycopg2>=2.9.10`, add `duckdb>=1.0.0` and `duckdb-engine>=0.17.0`
- [ ] T002 Run `uv sync` to update lock file and install new dependencies
- [ ] T003 Create `data/` directory at repository root for DuckDB file
- [ ] T004 Add `data/` to .gitignore to exclude database file from version control

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database configuration that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Configuration

- [ ] T005 Update src/tandem_fetch/definitions.py: replace DATABASE_URL with DATABASE_PATH, default to `data/tandem.db`, generate DuckDB connection string `duckdb:///data/tandem.db`

### Model Updates (Add Sequences for Auto-increment)

- [ ] T006 [P] Update src/tandem_fetch/db/raw_events.py: add `from sqlalchemy import Sequence` and change id column to use `Sequence('raw_events_id_seq')`
- [ ] T007 [P] Update src/tandem_fetch/db/events.py: add `from sqlalchemy import Sequence` and change id column to use `Sequence('events_id_seq')`
- [ ] T008 [P] Update src/tandem_fetch/db/cgm_readings.py: add `from sqlalchemy import Sequence` and change id column to use `Sequence('cgm_readings_id_seq')`
- [ ] T009 [P] Update src/tandem_fetch/db/basal_deliveries.py: add `from sqlalchemy import Sequence` and change id column to use `Sequence('basal_deliveries_id_seq')`

### Alembic Configuration

- [ ] T010 Update alembic/env.py: add `AlembicDuckDBImpl` class with `__dialect__ = "duckdb"`, update URL handling to use DATABASE_PATH from definitions
- [ ] T011 Update alembic.ini: set sqlalchemy.url placeholder (will be overridden by env.py)
- [ ] T012 Delete all existing migration files in alembic/versions/
- [ ] T013 Generate fresh initial migration with `alembic revision --autogenerate -m "initial_duckdb_schema"`

**Checkpoint**: Foundation ready - database configured for DuckDB, user story implementation can now begin

---

## Phase 3: User Story 1 - Fresh Data Fetch to DuckDB (Priority: P1) 🎯 MVP

**Goal**: Enable fetching all pump data from Tandem Source and storing in DuckDB file

**Independent Test**: Run `uv run get-all-raw-pump-events` and verify data appears in `data/tandem.db` with correct schema and record counts

### Implementation for User Story 1

- [ ] T014 [US1] Update src/tandem_fetch/tasks/raw_events.py: change engine creation to use DuckDB connection string from definitions.py
- [ ] T015 [US1] Update src/tandem_fetch/workflows/get_all_raw_pump_events.py: change engine creation to use DuckDB connection string from definitions.py
- [ ] T016 [P] [US1] Update src/tandem_fetch/workflows/backfills/0_get_all_raw_pump_events.py: change engine creation to use DuckDB connection string
- [ ] T017 [P] [US1] Update src/tandem_fetch/workflows/backfills/1_parse_events_table.py: change engine creation to use DuckDB connection string
- [ ] T018 [P] [US1] Update src/tandem_fetch/workflows/backfills/2_parse_cgm_readings.py: change engine creation to use DuckDB connection string
- [ ] T019 [P] [US1] Update src/tandem_fetch/workflows/backfills/3_parse_basal_deliveries.py: change engine creation to use DuckDB connection string
- [ ] T020 [US1] Run `alembic upgrade head` to create schema in data/tandem.db
- [ ] T021 [US1] Validate: run `uv run get-all-raw-pump-events` and verify raw events are stored
- [ ] T022 [US1] Validate: run backfill workflows (1, 2, 3) and verify events, cgm_readings, basal_deliveries tables are populated

**Checkpoint**: User Story 1 complete - data fetch and full pipeline working with DuckDB

---

## Phase 4: User Story 2 - Analytics-Ready Data Access (Priority: P2)

**Goal**: Enable querying pump data with standard SQL tools for analytics

**Independent Test**: Connect to `data/tandem.db` with DuckDB CLI and run aggregation queries

### Implementation for User Story 2

- [ ] T023 [US2] Validate: install DuckDB CLI (`brew install duckdb` or download) and connect to data/tandem.db
- [ ] T024 [US2] Validate: run sample analytical query (daily CGM averages) in DuckDB CLI to verify data access
- [ ] T025 [US2] Validate: run time-in-range calculation query to verify aggregations work
- [ ] T026 [US2] Validate: export cgm_readings to Parquet using `COPY cgm_readings TO 'exports/cgm_readings.parquet' (FORMAT PARQUET)`

**Checkpoint**: User Story 2 complete - data queryable with standard SQL tools

---

## Phase 5: User Story 3 - Zero-Setup Database (Priority: P3)

**Goal**: Ensure database works without any server installation or manual configuration

**Independent Test**: Clone repo on fresh machine, run `uv sync`, then run fetch command - database file created automatically

### Implementation for User Story 3

- [ ] T027 [US3] Update README.md: remove all PostgreSQL setup instructions (install PostgreSQL, create database, configure connection string)
- [ ] T028 [US3] Update README.md: simplify setup to single `uv sync` step
- [ ] T029 [US3] Update README.md: update usage examples to reflect new workflow (no alembic init needed, database auto-creates)
- [ ] T030 [US3] Update README.md: add DuckDB CLI query examples for analytics
- [ ] T031 [US3] Validate: verify database file is auto-created when running fetch command on fresh setup (delete data/tandem.db, run fetch)

**Checkpoint**: User Story 3 complete - zero database server setup required

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T032 Validate SC-001: confirm only `uv sync` is needed for setup (no database server)
- [ ] T033 Validate SC-002: confirm all pipeline stages (raw → events → cgm/basal) complete with DuckDB
- [ ] T034 Validate SC-004: confirm analytical queries work in DuckDB CLI
- [ ] T035 Validate SC-005: copy data/tandem.db to different location, open with DuckDB CLI, verify data accessible
- [ ] T036 Validate SC-006: review README and confirm setup instructions reduced to 1 step
- [ ] T037 Run quickstart.md validation: follow quickstart guide end-to-end on current setup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - core data fetch functionality
- **User Story 2 (Phase 4)**: Depends on User Story 1 (needs data in database to query)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (documentation describes working system)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 - needs populated database to validate analytics
- **User Story 3 (P3)**: Depends on US1 - documentation must describe working system

### Within Each Phase

- Tasks without [P] marker must be executed sequentially
- Tasks with [P] marker within same phase can run in parallel
- Validation tasks (T021-T022, T023-T026, T031) should run after implementation tasks

### Parallel Opportunities

- T003 and T004 (Setup) can run in parallel
- T006, T007, T008, T009 (Model updates) can run in parallel
- T016, T017, T018, T019 (Backfill workflow updates) can run in parallel

---

## Parallel Example: Phase 2 Model Updates

```bash
# Launch all model updates together:
Task: "Update src/tandem_fetch/db/raw_events.py: add Sequence"
Task: "Update src/tandem_fetch/db/events.py: add Sequence"
Task: "Update src/tandem_fetch/db/cgm_readings.py: add Sequence"
Task: "Update src/tandem_fetch/db/basal_deliveries.py: add Sequence"
```

## Parallel Example: Phase 3 Backfill Updates

```bash
# Launch all backfill workflow updates together:
Task: "Update src/tandem_fetch/workflows/backfills/0_get_all_raw_pump_events.py"
Task: "Update src/tandem_fetch/workflows/backfills/1_parse_events_table.py"
Task: "Update src/tandem_fetch/workflows/backfills/2_parse_cgm_readings.py"
Task: "Update src/tandem_fetch/workflows/backfills/3_parse_basal_deliveries.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T013)
3. Complete Phase 3: User Story 1 (T014-T022)
4. **STOP and VALIDATE**: Run fetch command, verify data in DuckDB
5. System is usable at this point

### Incremental Delivery

1. Complete Setup + Foundational → Database configured
2. Add User Story 1 → Test fetch → **MVP complete!**
3. Add User Story 2 → Validate analytics queries work
4. Add User Story 3 → Update documentation
5. Polish phase → Final validation

### Single Developer Strategy

Execute phases sequentially:
1. Phase 1: Setup (~5 min)
2. Phase 2: Foundational (~30 min)
3. Phase 3: User Story 1 + validation (~20 min)
4. Phase 4: User Story 2 validation (~10 min)
5. Phase 5: User Story 3 documentation (~15 min)
6. Phase 6: Final validation (~10 min)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Validation tasks (T021-T026, T031-T037) require running commands and verifying output
- Delete existing PostgreSQL database and data when ready to switch (not tracked in tasks - user decision)
- All workflow files follow same pattern for engine creation update
- No test code tasks included - spec did not request TDD approach
