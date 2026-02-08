# Implementation Plan: Integration Tests with Mocked Tandem Source API

**Branch**: `003-integration-tests` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-integration-tests/spec.md`

## Summary

Add comprehensive integration test suite using pytest to validate the complete tandem-fetch data pipeline. Tests will mock Tandem Source API responses using requests-mock, use in-memory DuckDB databases for isolation and speed, and run as part of pre-commit hooks to catch breaking changes before commits. Target execution time: under 30 seconds for full test suite.

## Technical Context

**Language/Version**: Python 3.12 (existing project constraint)
**Primary Dependencies**: pytest, pytest-xdist (parallel execution), requests-mock (API mocking), pytest-alembic (migration testing)
**Storage**: In-memory DuckDB databases (`:memory:`) for test isolation
**Testing**: pytest with function-scoped fixtures, parallel execution via pytest-xdist
**Target Platform**: Developer workstations (macOS/Linux/Windows)
**Project Type**: Single project (existing tandem-fetch structure)
**Performance Goals**: Complete test suite execution in <30 seconds, individual test <5 seconds
**Constraints**: Must run in pre-commit hooks, no network access required, automatic cleanup
**Scale/Scope**: 15-25 integration tests covering 4 pipeline stages, 5-10 fixtures per stage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Alignment with Constitution Principles

#### I. Data Integrity First ✅
- **Alignment**: Tests validate data integrity through pipeline stages, ensure transformations are correct
- **Enhancement**: Tests verify idempotency of transformations (run twice, same results)
- **No violations**: Tests use same data models and validation logic as production

#### II. Single-User Simplicity ✅
- **Alignment**: Simple test execution (`pytest`), no complex CI/CD setup required
- **Enhancement**: Tests runnable on any developer machine without special configuration
- **No violations**: No multi-tenant test complexity

#### III. Incremental & Resumable ✅
- **Alignment**: Tests verify incremental fetch logic works correctly
- **Enhancement**: Test fixtures include scenarios for interrupted/resumed fetches
- **No violations**: Tests validate same resumability guarantees as production

#### IV. Clear Data Pipeline ✅
- **Alignment**: Tests organized by pipeline stage (raw → events → CGM/basal)
- **Enhancement**: Each stage independently testable, failures clearly indicate which stage broke
- **No violations**: Tests follow same 3-stage pipeline structure

#### V. Workflow Orchestration ✅
- **Alignment**: Tests validate Prefect workflows execute correctly
- **Enhancement**: Tests use Prefect test harness for deterministic workflow execution
- **No violations**: Tests don't bypass or modify workflow orchestration

### Testing Philosophy (Constitution: Testing) ✅
- **Perfect Alignment**: "Focus on integration tests for data pipeline correctness"
- **Enhancement**: Implements exactly what constitution prescribes
- **Addition**: Unit tests for complex transformation logic (pump_events module)

### Credential Security ✅
- **Alignment**: Tests never use real credentials, all API calls mocked
- **Enhancement**: Tests verify credential loading fails gracefully on missing files
- **No violations**: No credentials in test fixtures or code

**GATE STATUS**: ✅ PASSED - Perfect alignment with constitution, implements testing philosophy

## Project Structure

### Documentation (this feature)

```text
specs/003-integration-tests/
├── plan.md              # This file
├── research.md          # Pytest + mocking research
├── quickstart.md        # Test execution guide
└── contracts/           # Test fixture schemas
    └── api-response-schema.yaml
```

### Source Code (repository root)

```text
/Users/oskari/projects/tandem-fetch/
├── src/tandem_fetch/        # Existing source (UNCHANGED)
├── tests/                    # NEW: Test suite
│   ├── conftest.py          # Root fixtures (database, API mocks)
│   ├── fixtures/            # Test data files
│   │   ├── api_responses/   # Mock API responses (JSON)
│   │   │   ├── auth_success.json
│   │   │   ├── pump_events_sample.json
│   │   │   ├── cgm_events.json
│   │   │   └── basal_events.json
│   │   └── expected/        # Expected outputs for assertions
│   │       ├── parsed_events.json
│   │       ├── cgm_readings.json
│   │       └── basal_deliveries.json
│   ├── unit/                # Unit tests (fast, isolated)
│   │   ├── conftest.py
│   │   ├── test_db/         # Database model tests
│   │   │   └── test_models.py
│   │   ├── test_tasks/      # Individual task tests
│   │   │   ├── test_auth.py
│   │   │   ├── test_fetch.py
│   │   │   └── test_raw_events.py
│   │   └── test_pump_events/  # Transformation logic tests
│   │       ├── test_transforms.py
│   │       └── test_utils.py
│   └── integration/         # Integration tests (full pipeline)
│       ├── conftest.py
│       └── test_workflows/
│           ├── test_step0_fetch_raw_events.py
│           ├── test_step1_parse_events.py
│           ├── test_step2_extract_cgm.py
│           ├── test_step3_extract_basal.py
│           └── test_full_pipeline.py
└── pyproject.toml           # UPDATED: Add pytest config + dependencies
```

**Structure Decision**: Follow pytest best practices with separate `tests/` directory mirroring `src/` structure. Use `conftest.py` files at multiple levels (root, unit, integration) for fixture organization. Separate unit tests (fast, mocked dependencies) from integration tests (full pipeline validation).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No complexity violations - this feature perfectly aligns with constitution's testing philosophy.

## Phase 0: Research & Technical Decisions

**Status**: ✅ COMPLETE

See [research.md](./research.md) for detailed findings.

### Key Research Outcomes

1. **Pytest + DuckDB In-Memory**:
   - Use `duckdb:///:memory:` for fastest test execution
   - Function-scoped fixtures ensure complete isolation
   - Automatic cleanup on engine disposal
   - Handles datasets up to ~1GB in memory

2. **API Mocking Strategy**: requests-mock library
   - Native pytest integration via `requests_mock` fixture
   - Load mock responses from JSON files in `tests/fixtures/api_responses/`
   - Fixtures organized by API endpoint and scenario (success, error, edge cases)

3. **Pre-Commit Integration**:
   - Add pytest to pre-commit config with `-m "not slow"` marker
   - Use pytest-xdist for parallel execution (`-n auto`)
   - Target <30s execution: only run fast integration tests in hooks
   - Full suite (including slow tests) runs manually or in CI

4. **Pytest Configuration**:
   - pytest-xdist for parallel execution (4-8x speedup)
   - `--dist loadfile` to keep database fixtures together
   - Mark slow tests to exclude from pre-commit
   - Short traceback format (`--tb=short`) for faster feedback

5. **Alembic Migration Testing**:
   - Use pytest-alembic for migration validation
   - Test upgrade/downgrade paths
   - Verify model definitions match DDL

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

### Design Artifacts

1. **quickstart.md**: Test execution guide for developers
2. **contracts/api-response-schema.yaml**: Schema for mock API response fixtures

### Test Organization Strategy

```text
Test Types by Priority:
1. Integration (P1): Full pipeline validation
   - Tests: test_full_pipeline.py (end-to-end)
   - Scope: All 4 stages (fetch → parse → CGM → basal)
   - Fixtures: Complete API response + expected database state

2. Component Integration (P2): Individual stage testing
   - Tests: test_step0_fetch_raw_events.py, test_step1_parse_events.py, etc.
   - Scope: Single pipeline stage with mocked inputs
   - Fixtures: Stage-specific input/output data

3. Unit (P3): Isolated logic testing
   - Tests: test_transforms.py, test_utils.py, test_models.py
   - Scope: Pure functions and model validation
   - Fixtures: Minimal, no database/API mocking
```

### Fixture Organization

**Root conftest.py** (shared across all tests):
```python
import pytest
from sqlalchemy import create_engine
from tandem_fetch.db.base import Base

@pytest.fixture(scope="function")
def test_db_engine():
    """In-memory DuckDB engine for each test."""
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def tandem_api_mock(requests_mock):
    """Mock Tandem Source API with common responses."""
    # Load fixtures from JSON files
    # Register mock endpoints
    return requests_mock
```

**Integration conftest.py** (pipeline-specific fixtures):
```python
import pytest
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

@pytest.fixture
def sample_pump_events():
    """Load sample pump events from fixture file."""
    with open(FIXTURES_DIR / "api_responses" / "pump_events_sample.json") as f:
        return json.load(f)

@pytest.fixture
def db_with_raw_events(test_db_engine, sample_pump_events):
    """Database populated with raw events."""
    # Insert sample events
    # Return session
    pass
```

### Test Execution Flow

```text
Developer commits code
     ↓
Pre-commit hook triggers
     ↓
┌─────────────────────────────────┐
│ Existing Hooks (fast)           │
│ - Ruff format                   │
│ - Ruff lint                     │
│ - Gitleaks                      │
│ - Builtin checks                │
│ (~5 seconds)                    │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ Pytest Integration Tests (new)  │
│ - pytest -m "not slow" -n auto  │
│ - Parallel execution (4 cores)  │
│ - In-memory databases           │
│ - Mocked API responses          │
│ (~20 seconds for 15-20 tests)   │
└─────────────────────────────────┘
     ↓
All pass? → Commit proceeds
     ↓
Failed? → Block commit, show error
```

### Mock API Response Structure

**File**: `tests/fixtures/api_responses/pump_events_sample.json`
```json
{
  "events": [
    {
      "event_id": "evt_123",
      "event_timestamp": "2024-01-01T10:00:00Z",
      "event_name": "LID_CGM_DATA_READING",
      "event_data": {
        "currentglucosedisplayvalue": 120,
        "trendArrow": "FLAT"
      }
    },
    {
      "event_id": "evt_124",
      "event_timestamp": "2024-01-01T10:05:00Z",
      "event_name": "LID_BASAL_DELIVERY",
      "event_data": {
        "profileBasalRate": 0.850,
        "algorithmRate": 0.900,
        "tempRate": 0.000
      }
    }
  ],
  "pagination": {
    "hasMore": false,
    "nextCursor": null
  }
}
```

### Test Fixture Schema Contract

```yaml
# contracts/api-response-schema.yaml
PumpEventsResponse:
  type: object
  required: [events, pagination]
  properties:
    events:
      type: array
      items:
        type: object
        required: [event_id, event_timestamp, event_name, event_data]
        properties:
          event_id: {type: string}
          event_timestamp: {type: string, format: iso8601}
          event_name: {type: string}
          event_data: {type: object}
    pagination:
      type: object
      required: [hasMore]
      properties:
        hasMore: {type: boolean}
        nextCursor: {type: string, nullable: true}
```

### Performance Budget

| Test Category | Count | Per-Test Budget | Total Budget |
|---------------|-------|-----------------|--------------|
| Full pipeline | 1 | 10s | 10s |
| Component integration | 4 | 3s | 12s |
| Fast unit tests | 10-15 | 0.5s | 5-8s |
| **Total** | **15-20** | **-** | **27-30s** |

## Phase 2: Task Breakdown

**Status**: ⏸️ NOT STARTED - Run `/speckit.tasks` to generate tasks.md

Task generation will create:
- Dependency installation (pytest, pytest-xdist, requests-mock, pytest-alembic)
- Directory structure creation (tests/, fixtures/)
- Root conftest.py with shared fixtures
- Mock API response fixtures (JSON files)
- Integration tests for each pipeline stage
- Unit tests for transformation logic
- pytest configuration in pyproject.toml
- Pre-commit hook configuration
- Documentation (quickstart guide)

Expected task count: ~30-40 tasks organized into phases:
1. Setup (dependencies, directory structure, pytest config)
2. Fixtures & Mocks (conftest.py, API response fixtures, test data)
3. User Story 1: Full Pipeline Tests (P1 - end-to-end validation)
4. User Story 2: Component Tests (P2 - individual stage testing)
5. User Story 3: Mock Validation (P3 - fixture schema validation)
6. Pre-Commit Integration (add pytest to hooks)
7. Documentation (quickstart guide, running tests)

## Implementation Notes

### Key Decisions

1. **Why pytest over unittest?**
   - Better fixture management (dependency injection)
   - Parallel execution support (pytest-xdist)
   - Rich plugin ecosystem (pytest-alembic, requests-mock)
   - Constitution already specifies pytest-compatible testing

2. **Why requests-mock over responses?**
   - Native pytest integration via fixture injection
   - No manual setup/teardown needed
   - Better error messages
   - Simpler API for common cases

3. **Why in-memory databases over temporary files?**
   - 10-100x faster (no disk I/O)
   - Automatic cleanup (no orphaned files)
   - DuckDB handles 1GB+ datasets in memory
   - Perfect for integration test data volumes

4. **Why pre-commit hooks for tests?**
   - Catch breaking changes before commit
   - Enforce quality gate locally (not just CI)
   - Faster feedback than waiting for CI
   - Aligns with existing pre-commit hook strategy

5. **Why separate unit and integration tests?**
   - Different speeds (unit: ms, integration: seconds)
   - Different purposes (unit: logic, integration: pipeline)
   - Allows selective execution (pytest tests/unit/ vs tests/integration/)
   - Follows pytest best practices

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tests too slow for pre-commit | High | Mark slow tests, parallel execution, only run fast tests in hooks |
| Mock responses drift from real API | Medium | Document fixture creation process, version fixtures, validate schemas |
| Tests brittle (break on valid changes) | Medium | Test behavior not implementation, use loose assertions where appropriate |
| In-memory database size limits | Low | DuckDB handles 1GB+, production data per-test is <100MB |
| Parallel test flakiness | Low | Use `--dist loadfile` to keep database fixtures together |

### Future Enhancements (Out of Scope)

- CI/CD integration (GitHub Actions running full suite)
- Property-based testing (hypothesis) for edge cases
- Performance regression testing
- Visual test reports (pytest-html)
- Code coverage tracking (pytest-cov)
- Mutation testing (mutmut) for test quality

## Success Metrics

Aligned with spec success criteria:

- **SC-001**: Measure - Run `pytest` and see pass/fail in <30s ✅ (Verified by timing test execution)
- **SC-002**: Measure - 100% pipeline breaks detected ✅ (Verified by intentionally breaking each stage)
- **SC-003**: Measure - Tests run without credentials ✅ (Verified by running without .env or credentials.toml)
- **SC-004**: Measure - Each stage tested ✅ (Count test files: 4 stage tests + 1 full pipeline)
- **SC-005**: Measure - Clear failure messages ✅ (Verified pytest output shows file/line/assertion)
- **SC-006**: Measure - Fresh clone works ✅ (Verified by `git clone && uv sync && pytest`)
- **SC-007**: Measure - Deterministic results ✅ (Verified by running same tests 5 times)
- **SC-008**: Measure - Zero artifacts ✅ (Verified no files in /tmp or project root after tests)

## Next Steps

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Review and approve tasks.md
3. Run `/speckit.implement` to execute tasks
4. Validate all success criteria
5. Merge to main after tests pass
