# Research: Integration Testing with Pytest for Data Pipelines

**Feature**: 003-integration-tests
**Date**: 2026-02-07
**Status**: Complete

## Executive Summary

Research evaluated pytest-based integration testing strategies for tandem-fetch data pipeline. Selected **pytest + requests-mock + in-memory DuckDB** stack for optimal speed (<30s), isolation, and developer experience. Key finding: pytest-xdist parallel execution provides 4-8x speedup, making pre-commit hook integration feasible.

## Decision 1: In-Memory vs File-Based Test Databases

**Decision**: Use in-memory DuckDB databases (`:memory:`)

**Rationale**:
1. **Performance**: 10-100x faster than file-based (no disk I/O)
2. **Automatic Cleanup**: Memory freed on engine disposal, no orphaned files
3. **Sufficient Capacity**: DuckDB handles 1GB+ datasets in memory
4. **Test Data Size**: Integration tests use <100MB per test
5. **Isolation**: Each test gets fresh database, zero cross-contamination

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **In-memory DuckDB** | Fastest, auto-cleanup, perfect isolation | Limited to RAM size | ✅ **Selected** |
| **Temporary file databases** | Handles >RAM datasets, inspectable | Slower, cleanup complexity | ❌ Rejected - unnecessary for test data volumes |
| **Shared test database** | Fast setup | Cross-test contamination risk | ❌ Rejected - violates isolation |
| **SQLite :memory:** | Fast, standard | No DuckDB-specific feature testing | ❌ Rejected - doesn't match production |

**Implementation**:
```python
@pytest.fixture(scope="function")
def test_db_engine():
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()  # Automatic cleanup
```

**References**:
- DuckDB handles 1GB+ in memory efficiently
- Function-scoped fixtures recommended for database testing
- In-memory provides complete test isolation

---

## Decision 2: API Mocking Library

**Decision**: Use requests-mock for Tandem Source API mocking

**Rationale**:
1. **Native Pytest Integration**: Provides `requests_mock` fixture automatically
2. **Zero Boilerplate**: No setup/teardown code needed
3. **Simple API**: `requests_mock.get(url, json=data)` - intuitive
4. **Existing Stack**: Project already uses `requests` library
5. **Mature**: Stable, well-documented, active maintenance

**Alternatives Considered**:

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| **requests-mock** | Pytest fixture, simple API, requests-compatible | Only works with requests library | ✅ **Selected** |
| **responses** | Popular, flexible | Manual setup/teardown, no pytest integration | ❌ Rejected - more boilerplate |
| **pytest-httpx** | Modern, async support | Requires httpx library (not using) | ❌ Rejected - wrong HTTP client |
| **VCR.py** | Records real responses | Requires real API access initially | ❌ Rejected - want fully mocked |

**Implementation**:
```python
@pytest.fixture
def tandem_api_mock(requests_mock):
    requests_mock.post(
        'https://api.tandemdiabetes.com/auth',
        json={'access_token': 'mock_token'}
    )
    return requests_mock
```

**Fixture Organization**: Store mock responses in JSON files under `tests/fixtures/api_responses/` for easy versioning and updates.

**References**:
- requests-mock provides seamless pytest integration
- JSON fixtures recommended for API response test data
- Separation of test data from test code improves maintainability

---

## Decision 3: Parallel Test Execution

**Decision**: Use pytest-xdist with `--dist loadfile` strategy

**Rationale**:
1. **Speed**: 4-8x faster with parallel execution across CPU cores
2. **30-Second Goal**: Achievable with 4+ cores running tests in parallel
3. **Database Compatibility**: `loadfile` keeps database fixtures together (no conflicts)
4. **Simple Setup**: Just add `-n auto` to pytest command
5. **Pre-Commit Friendly**: Fast enough for pre-commit hooks

**Configuration**:
```toml
[tool.pytest.ini_options]
addopts = "-n auto --dist loadfile --tb=short"
```

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **pytest-xdist** | 4-8x speedup, stable, simple | Slightly complex fixture management | ✅ **Selected** |
| **Sequential execution** | Simple, predictable | Too slow for 30s goal (>60s) | ❌ Rejected - misses performance target |
| **pytest-parallel** | Alternative to xdist | Less mature, fewer features | ❌ Rejected - xdist is standard |

**Distribution Strategies**:
- `--dist loadfile`: Keeps all tests in same file together (good for shared database fixtures)
- `--dist loadscope`: Groups by class/module (more granular)
- Selected `loadfile` to avoid database fixture conflicts

**Performance Impact**:
- 20 tests @ 2s each = 40s sequential
- 20 tests @ 2s each / 4 cores = 10s parallel
- Overhead ~2-3s = **13s total** (well under 30s goal)

**References**:
- pytest-xdist recommended for CPU-bound test suites
- `loadfile` distribution prevents database fixture conflicts
- Auto-detection (`-n auto`) uses all physical cores

---

## Decision 4: Pre-Commit Hook Integration

**Decision**: Add pytest to pre-commit with fast tests only (`-m "not slow"`)

**Rationale**:
1. **Early Feedback**: Catch breaks before commit, not in CI
2. **Quality Gate**: Enforces working code in every commit
3. **Fast Enough**: <30s with parallel execution and test markers
4. **Existing Pattern**: Aligns with project's pre-commit strategy (ruff, gitleaks)
5. **Developer Control**: Can bypass with `--no-verify` if needed

**Configuration**:
```yaml
- repo: local
  hooks:
    - id: pytest-fast
      name: pytest-fast
      entry: uv run pytest
      args: ['-m', 'not slow', '-n', 'auto', '-x', '--tb=short']
      language: system
      pass_filenames: false
      always_run: true
```

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Pre-commit integration** | Immediate feedback, local quality gate | Slows commit workflow | ✅ **Selected** - acceptable with fast tests |
| **Pre-push hook** | Less frequent interruption | Delayed feedback (after multiple commits) | ❌ Rejected - too late to catch issues |
| **CI-only testing** | Zero local impact | Very delayed feedback (minutes to hours) | ❌ Rejected - feedback too slow |
| **Manual pytest** | Full developer control | Tests often skipped | ❌ Rejected - inconsistent enforcement |

**Test Markers**:
- `@pytest.mark.slow`: Long-running tests (>5s), excluded from pre-commit
- `@pytest.mark.integration`: All pipeline integration tests
- `@pytest.mark.unit`: Fast unit tests (<1s)

**Pre-Commit Behavior**:
- Runs only unmarked tests and `@pytest.mark.integration` tests
- Skips `@pytest.mark.slow` tests (full backfill scenarios, large datasets)
- Stops on first failure (`-x`) for faster feedback
- Shows short tracebacks (`--tb=short`) for quick diagnosis

**References**:
- Pre-commit pytest integration common but needs performance tuning
- Test markers recommended for separating fast/slow tests
- Many projects run only linting in pre-commit and defer testing to CI (we do both)

---

## Decision 5: Alembic Migration Testing

**Decision**: Use pytest-alembic for database migration validation

**Rationale**:
1. **Schema Validation**: Verifies migrations create correct database schema
2. **Migration Safety**: Tests upgrade/downgrade paths
3. **Model Sync**: Ensures SQLAlchemy models match migration DDL
4. **Pytest Integration**: Works with in-memory databases
5. **Early Detection**: Catches migration errors before applying to production

**Implementation**:
```python
@pytest.fixture
def alembic_config():
    return Config.from_raw_config({
        "script_location": "alembic",
    })

def test_upgrade(alembic_runner):
    alembic_runner.migrate_up_to("head")

def test_model_definitions_match_ddl(alembic_runner):
    alembic_runner.migrate_up_to("head")
    alembic_runner.check_model_definitions()
```

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **pytest-alembic** | Full migration testing, model validation | Additional dependency | ✅ **Selected** |
| **Manual Alembic calls** | No extra dependency | Boilerplate code, incomplete coverage | ❌ Rejected - reinventing wheel |
| **No migration testing** | Simplest | Catches migration errors too late | ❌ Rejected - too risky |

**Test Coverage**:
- Single head revision (no merge conflicts)
- Upgrade from base to head
- Model definitions match DDL
- Downgrade paths (optional)

**References**:
- pytest-alembic recommended for production Alembic usage
- Works with in-memory databases despite common misconceptions
- Catches schema drift early in development

---

## Fixture Organization Strategy

**Decision**: Multi-level conftest.py with JSON fixture files

**Structure**:
```text
tests/
  conftest.py              # Shared: database engines, API mocks
  fixtures/
    api_responses/         # JSON files with mock API responses
    expected/              # JSON files with expected outputs
  unit/
    conftest.py            # Unit-test specific fixtures
  integration/
    conftest.py            # Integration-test specific fixtures
```

**Rationale**:
1. **Reusability**: Shared fixtures at root, specialized at sub-levels
2. **Maintainability**: Separate test data from test logic
3. **Versioning**: JSON fixtures can be version-controlled and reviewed
4. **Non-Developer Friendly**: JSON easier to update than Python code
5. **Pytest Best Practice**: Recommended fixture organization pattern

**Fixture Loading**:
```python
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_pump_events():
    with open(FIXTURES_DIR / "api_responses" / "pump_events_sample.json") as f:
        return json.load(f)
```

**References**:
- Multi-level conftest.py follows pytest good practices
- JSON fixtures separate concerns (data vs logic)
- Easier to maintain and review than inline Python dictionaries

---

## Performance Budget Breakdown

**Target**: <30 seconds total execution time

| Component | Time Budget | Justification |
|-----------|-------------|---------------|
| Test discovery | 1s | Pytest scan of test files |
| Fixture setup (parallel) | 2s | In-memory DB creation across workers |
| Full pipeline test | 8s | End-to-end validation (1 test) |
| Component tests (4x) | 12s | 4 stages @ 3s each |
| Unit tests (15x) | 5s | Fast tests @ 0.3s each |
| Teardown & reporting | 2s | Cleanup and output formatting |
| **Total** | **30s** | Within target |

**Optimization Strategies**:
1. Parallel execution (`-n auto`) reduces 40s sequential to 12s parallel
2. In-memory databases (vs files) saves 5-10s
3. Fast-only markers skip slow tests (saves 20-30s)
4. Stop on first failure (`-x`) provides faster feedback on errors

---

## Testing Prefect Workflows

**Decision**: Use Prefect test harness with mocked dependencies

**Setup**:
```python
from prefect.testing.utilities import prefect_test_harness

@pytest.fixture(autouse=True, scope="session")
def prefect_test_mode():
    with prefect_test_harness():
        yield
```

**Testing Strategy**:
1. **Task-level**: Test individual Prefect tasks in isolation
2. **Flow-level**: Test complete workflows with mocked external dependencies
3. **End-to-end**: Validate flow orchestration logic

**Benefits**:
- Deterministic flow execution (no actual scheduling)
- Faster execution (no Prefect server needed)
- Isolated testing (no shared state between tests)

**References**:
- Prefect test harness provides isolated test environment
- Mock external services (API, database writes in production)
- Test workflows as pure functions

---

## Open Questions and Future Work

### Resolved in This Research

- ✅ Database strategy? **In-memory DuckDB**
- ✅ API mocking library? **requests-mock**
- ✅ Parallel execution? **pytest-xdist with loadfile**
- ✅ Pre-commit integration? **Yes, with fast-test markers**
- ✅ Migration testing? **pytest-alembic**
- ✅ Performance achievable? **Yes, 13-20s estimated**

### Future Enhancements (Out of Scope)

- [ ] CI/CD integration (GitHub Actions)
- [ ] Code coverage tracking (pytest-cov)
- [ ] Property-based testing (hypothesis)
- [ ] Performance regression testing
- [ ] Mutation testing (mutmut)
- [ ] Visual test reports (pytest-html)

---

## References

### pytest & DuckDB
- pytest-with-eric.com: Database Testing with Pytest and SQLModel
- medium.com/@geoffreykoh: Fun with Fixtures for Database Applications
- medium.com/clarityai-engineering: Unit testing SQL queries with DuckDB
- DuckDB handles larger-than-memory processing efficiently

### API Mocking
- requests-mock.readthedocs.io: Pytest integration documentation
- colin-b.github.io/pytest_httpx: pytest-httpx for httpx library
- codilime.com: Testing APIs with PyTest Mocks

### Parallel Execution
- pytest-xdist.readthedocs.io: Distribution strategies
- pytest-with-eric.com: Parallel Testing Made Easy
- johal.in: Pytest Parallel Execution for Large Test Suites

### Pre-Commit Integration
- medium.com/@fistralpro: Pytest pre-commit hook guide
- switowski.com: pre-commit vs. CI analysis
- pre-commit maintainers: Never added official pytest support due to speed concerns

### Prefect Testing
- docs.prefect.io: How to test workflows
- hoop.dev: Prefect pytest best practices
- medium.com/@vicky.guo97: Test and validate data pipelines with Prefect

### Test Organization
- docs.pytest.org: Good Integration Practices
- pytest-with-eric.com: 5 Best Practices For Organizing Tests
- dnmtechs.com: Storing Expected Data in Pytest

### Alembic Testing
- pypi.org/project/pytest-alembic
- pytest-alembic.readthedocs.io: Setup and usage guide

---

**Research Complete**: 2026-02-07
**Next Phase**: Generate quickstart.md and contracts/
