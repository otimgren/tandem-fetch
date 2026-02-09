# Tasks: Integration Tests with Mocked Tandem Source API

**Input**: Design documents from `/specs/003-integration-tests/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `tests/` at repository root
- Test organization: `tests/unit/`, `tests/integration/`, `tests/fixtures/`

---

## Phase 1: Setup (Test Infrastructure)

**Purpose**: Install dependencies and create basic test directory structure

- [x] T001 Add pytest dependencies to pyproject.toml (pytest, pytest-xdist, requests-mock, pytest-alembic)
- [x] T002 [P] Create test directory structure (tests/, tests/unit/, tests/integration/, tests/fixtures/)
- [x] T003 [P] Create fixture subdirectories (tests/fixtures/api_responses/, tests/fixtures/expected/)
- [x] T004 Configure pytest settings in pyproject.toml (parallel execution, markers, test paths)

---

## Phase 2: Foundational (Core Test Fixtures)

**Purpose**: Shared test fixtures and mocking infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story testing can begin until this phase is complete

- [x] T005 Create root tests/conftest.py with test_db_engine fixture (in-memory DuckDB)
- [x] T006 [P] Add db_session fixture to tests/conftest.py (SQLAlchemy session management)
- [x] T007 [P] Create tandem_api_mock fixture in tests/conftest.py using requests-mock
- [x] T008 [P] Add Prefect test harness fixture to tests/conftest.py (prefect_test_mode)
- [x] T009 Create sample auth success response in tests/fixtures/api_responses/auth_success.json
- [x] T010 [P] Create sample pump events response in tests/fixtures/api_responses/pump_events_sample.json
- [x] T011 [P] Create sample CGM events response in tests/fixtures/api_responses/cgm_events.json
- [x] T012 [P] Create sample basal events response in tests/fixtures/api_responses/basal_events.json
- [x] T013 Create integration conftest.py at tests/integration/conftest.py with sample_pump_events fixture
- [x] T014 [P] Add sample_cgm_events fixture to tests/integration/conftest.py
- [x] T015 [P] Add sample_basal_events fixture to tests/integration/conftest.py
- [x] T016 [P] Add db_with_raw_events fixture to tests/integration/conftest.py (pre-populated database)

**Checkpoint**: Foundation ready - user story test implementation can now begin in parallel

---

## Phase 3: User Story 1 - End-to-End Pipeline Testing (Priority: P1) 🎯 MVP

**Goal**: Validate complete data pipeline (fetch → parse → extract) works correctly with mocked Tandem API

**Independent Test**: Run `pytest tests/integration/test_workflows/test_full_pipeline.py` and verify all stages execute successfully

### Implementation for User Story 1

- [x] T017 [P] [US1] Create test_full_pipeline.py at tests/integration/test_workflows/test_full_pipeline.py
- [x] T018 [US1] Implement test_full_pipeline_fetch_to_cgm test (validates fetch → parse → CGM extraction)
- [x] T019 [US1] Implement test_full_pipeline_fetch_to_basal test (validates fetch → parse → basal extraction)
- [x] T020 [US1] Implement test_full_pipeline_data_integrity test (validates data remains consistent across stages)
- [x] T021 [US1] Add test_pipeline_with_pagination test (validates handling of paginated API responses)
- [x] T022 [US1] Create expected output fixtures in tests/fixtures/expected/full_pipeline_cgm.json
- [x] T023 [P] [US1] Create expected output fixtures in tests/fixtures/expected/full_pipeline_basal.json

**Checkpoint**: Full pipeline tests pass - core integration testing complete

---

## Phase 4: User Story 2 - Isolated Component Testing (Priority: P2)

**Goal**: Test individual pipeline stages independently for faster development feedback

**Independent Test**: Run each component test file individually and verify stage-specific functionality

### Implementation for User Story 2

- [x] T024 [P] [US2] Create test_step0_fetch_raw_events.py at tests/integration/test_workflows/test_step0_fetch_raw_events.py
- [x] T025 [US2] Implement test_fetch_raw_events_success in test_step0_fetch_raw_events.py
- [x] T026 [US2] Implement test_fetch_raw_events_pagination in test_step0_fetch_raw_events.py
- [x] T027 [US2] Implement test_fetch_raw_events_authentication in test_step0_fetch_raw_events.py
- [x] T028 [P] [US2] Create test_step1_parse_events.py at tests/integration/test_workflows/test_step1_parse_events.py
- [x] T029 [US2] Implement test_parse_pump_events in test_step1_parse_events.py (validates event type identification)
- [x] T030 [US2] Implement test_parse_events_timestamps in test_step1_parse_events.py (validates timestamp preservation)
- [x] T031 [US2] Implement test_parse_events_data_extraction in test_step1_parse_events.py (validates event_data parsing)
- [x] T032 [P] [US2] Create test_step2_extract_cgm.py at tests/integration/test_workflows/test_step2_extract_cgm.py
- [x] T033 [US2] Implement test_extract_cgm_readings in test_step2_extract_cgm.py
- [x] T034 [US2] Implement test_cgm_glucose_values in test_step2_extract_cgm.py
- [x] T035 [US2] Implement test_cgm_no_duplicates in test_step2_extract_cgm.py
- [x] T036 [P] [US2] Create test_step3_extract_basal.py at tests/integration/test_workflows/test_step3_extract_basal.py
- [x] T037 [US2] Implement test_extract_basal_deliveries in test_step3_extract_basal.py
- [x] T038 [US2] Implement test_basal_rate_values in test_step3_extract_basal.py
- [x] T039 [US2] Implement test_basal_timestamps in test_step3_extract_basal.py
- [x] T040 [US2] Create expected parsed events fixture in tests/fixtures/expected/parsed_events.json
- [x] T041 [P] [US2] Create expected CGM readings fixture in tests/fixtures/expected/cgm_readings.json
- [x] T042 [P] [US2] Create expected basal deliveries fixture in tests/fixtures/expected/basal_deliveries.json

**Checkpoint**: All component tests pass - individual stages can be tested independently

---

## Phase 5: User Story 3 - API Mock Validation (Priority: P3)

**Goal**: Ensure mock API responses match real Tandem Source API structure

**Independent Test**: Run schema validation tests and verify mock responses comply with documented API schemas

### Implementation for User Story 3

- [x] T043 [P] [US3] Create API response schema at specs/003-integration-tests/contracts/api-response-schema.yaml
- [x] T044 [US3] Document PumpEventsResponse schema in api-response-schema.yaml
- [x] T045 [US3] Document CGMEventsResponse schema in api-response-schema.yaml
- [x] T046 [US3] Document BasalEventsResponse schema in api-response-schema.yaml
- [x] T047 [US3] Document AuthenticationResponse schema in api-response-schema.yaml
- [x] T048 [P] [US3] Create test_mock_validation.py at tests/unit/test_fixtures/test_mock_validation.py
- [x] T049 [US3] Implement test_pump_events_schema_compliance in test_mock_validation.py
- [x] T050 [US3] Implement test_cgm_events_schema_compliance in test_mock_validation.py
- [x] T051 [US3] Implement test_basal_events_schema_compliance in test_mock_validation.py
- [x] T052 [US3] Implement test_auth_response_schema_compliance in test_mock_validation.py
- [x] T053 [US3] Implement test_fixture_data_types in test_mock_validation.py (validate field types match schema)

**Checkpoint**: Mock validation complete - fixture quality ensured

---

## Phase 6: Unit Tests (Supporting Components)

**Purpose**: Test isolated logic and database models

- [x] T054 [P] Create unit test conftest.py at tests/unit/conftest.py
- [x] T055 [P] Create test_models.py at tests/unit/test_db/test_models.py
- [x] T056 Implement test_raw_event_model in test_models.py (validates RawEvent model)
- [x] T057 Implement test_event_model in test_models.py (validates Event model)
- [x] T058 Implement test_cgm_reading_model in test_models.py (validates CGMReading model)
- [x] T059 Implement test_basal_delivery_model in test_models.py (validates BasalDelivery model)
- [x] T060 Implement test_model_relationships in test_models.py (validates SQLAlchemy relationships)
- [x] T061 [P] Create test_transforms.py at tests/unit/test_pump_events/test_transforms.py
- [x] T062 Implement test_event_type_classification in test_transforms.py
- [x] T063 Implement test_timestamp_parsing in test_transforms.py
- [x] T064 Implement test_glucose_value_extraction in test_transforms.py
- [x] T065 Implement test_basal_rate_calculation in test_transforms.py

---

## Phase 7: Alembic Migration Testing

**Purpose**: Validate database migrations work correctly

- [x] T066 [P] Create test_migrations.py at tests/unit/test_db/test_migrations.py
- [x] T067 Implement test_single_head_revision in test_migrations.py (ensures no merge conflicts)
- [x] T068 Implement test_upgrade_to_head in test_migrations.py (validates migrations run)
- [x] T069 Implement test_model_definitions_match_ddl in test_migrations.py (ensures models match schema)

---

## Phase 8: Pre-Commit Integration

**Purpose**: Add pytest to pre-commit hooks for automatic testing

- [x] T070 Add pytest-fast hook to .pre-commit-config.yaml
- [x] T071 Configure pytest hook with fast test markers (-m "not slow")
- [x] T072 Add parallel execution flags to pre-commit pytest (-n auto)
- [x] T073 Configure hook to stop on first failure (-x) for faster feedback
- [x] T074 Test pre-commit hook by running `pre-commit run pytest-fast --all-files`

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Finalize testing infrastructure and documentation

- [x] T075 [P] Mark slow tests with @pytest.mark.slow decorator
- [x] T076 [P] Mark integration tests with @pytest.mark.integration decorator
- [x] T077 Add test execution examples to quickstart.md (already created, validate completeness)
- [x] T078 Validate all test fixtures have proper error handling
- [x] T079 Run full test suite and verify <30 second execution time with `pytest -n auto`
- [x] T080 Run fast tests only and verify <20 second execution with `pytest -m "not slow" -n auto`
- [x] T081 Verify tests run without credentials (remove .env, run pytest)
- [x] T082 Verify test cleanup (no artifacts remain in /tmp or project root)
- [x] T083 Run pytest --collect-only to verify test discovery works correctly
- [x] T084 Validate all success criteria from spec.md (SC-001 through SC-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - No dependencies on other stories
  - User Story 3 (P3): Can start after Foundational - No dependencies on other stories
- **Unit Tests (Phase 6)**: Can run in parallel with user stories (tests core components)
- **Migration Tests (Phase 7)**: Can run in parallel with user stories
- **Pre-Commit (Phase 8)**: Depends on at least User Story 1 complete
- **Polish (Phase 9)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Full pipeline testing - Independent, can start after Foundational
- **User Story 2 (P2)**: Component testing - Independent, can start after Foundational
- **User Story 3 (P3)**: Mock validation - Independent, can start after Foundational

### Within Each User Story

- Tests can be created in parallel if marked [P]
- Expected output fixtures can be created in parallel with test files
- All tests should fail initially (no implementation to test yet - we're testing existing code)

### Parallel Opportunities

- Phase 1: Tasks T002 and T003 can run in parallel (different directories)
- Phase 2: Tasks T006, T007, T008 can run in parallel (different fixtures in same file)
- Phase 2: Tasks T010, T011, T012 can run in parallel (different JSON files)
- Phase 2: Tasks T014, T015, T016 can run in parallel (different fixtures in same file)
- User Story 1: Tasks T017, T022, T023 can run in parallel (different files)
- User Story 2: Tasks T024, T028, T032, T036 can run in parallel (different test files)
- User Story 2: Tasks T040, T041, T042 can run in parallel (different fixture files)
- User Story 3: Tasks T043, T048 can run in parallel (schema and test file)
- Phase 6: Tasks T054, T055, T061 can run in parallel (different test files)
- Phase 9: Tasks T075, T076, T077 can run in parallel (different files/concerns)

---

## Parallel Example: User Story 1

```bash
# Launch test file and fixtures together:
Task: "Create test_full_pipeline.py at tests/integration/test_workflows/test_full_pipeline.py"
Task: "Create expected output fixtures in tests/fixtures/expected/full_pipeline_cgm.json"
Task: "Create expected output fixtures in tests/fixtures/expected/full_pipeline_basal.json"
```

## Parallel Example: User Story 2

```bash
# Launch all component test files together:
Task: "Create test_step0_fetch_raw_events.py at tests/integration/test_workflows/test_step0_fetch_raw_events.py"
Task: "Create test_step1_parse_events.py at tests/integration/test_workflows/test_step1_parse_events.py"
Task: "Create test_step2_extract_cgm.py at tests/integration/test_workflows/test_step2_extract_cgm.py"
Task: "Create test_step3_extract_basal.py at tests/integration/test_workflows/test_step3_extract_basal.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (12 tasks) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (7 tasks) - Full pipeline testing
4. **STOP and VALIDATE**: Run `pytest tests/integration/test_workflows/test_full_pipeline.py`
5. If tests pass, MVP is complete

### Incremental Delivery

1. Complete Setup + Foundational → Test infrastructure ready
2. Add User Story 1 → Test independently → **MVP Complete** (full pipeline validated)
3. Add User Story 2 → Test independently → Component testing available
4. Add User Story 3 → Test independently → Mock validation complete
5. Add Unit Tests (Phase 6) → Component coverage increased
6. Add Migration Tests (Phase 7) → Schema validation complete
7. Add Pre-Commit Integration (Phase 8) → Automatic quality gate
8. Polish (Phase 9) → Production ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (16 tasks)
2. Once Foundational is done:
   - Developer A: User Story 1 (7 tasks)
   - Developer B: User Story 2 (19 tasks)
   - Developer C: User Story 3 (11 tasks)
   - Developer D: Unit Tests (12 tasks) + Migration Tests (4 tasks)
3. Stories complete independently
4. Team reconvenes for Pre-Commit Integration + Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable
- Tests are written for **existing code** - they validate the current pipeline implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All JSON fixtures should be formatted for readability (pretty-printed)
- Mock API responses must match real Tandem API structure (documented in research.md)
- In-memory databases ensure test isolation and fast execution
- Target: <30 seconds for full suite, <20 seconds for fast tests only
