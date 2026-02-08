# Quickstart: Running Integration Tests

**Feature**: 003-integration-tests
**Target Audience**: Developers working on tandem-fetch
**Time to Complete**: 2-3 minutes

## What These Tests Do

Integration tests validate the complete data pipeline from API fetch through data extraction:

1. ✅ **Mock Tandem API** - No real credentials or network needed
2. ✅ **In-Memory Database** - Fast, isolated, automatic cleanup
3. ✅ **Full Pipeline** - Tests fetch → parse → extract stages
4. ✅ **Pre-Commit Integration** - Catches breaks before commit

**Execution Time**: <30 seconds for full suite

---

## Quick Start

### Prerequisites

- Repository cloned
- Dependencies installed: `uv sync`

### Run All Tests

```bash
pytest
```

**Expected output**:
```
===================== test session starts ======================
collected 20 items

tests/integration/test_workflows/test_full_pipeline.py .      [ 5%]
tests/integration/test_workflows/test_step0_fetch_raw_events.py .  [10%]
tests/integration/test_workflows/test_step1_parse_events.py .      [15%]
...
===================== 20 passed in 18.45s ======================
```

### Run Specific Test Categories

```bash
# Only integration tests
pytest tests/integration/

# Only unit tests
pytest tests/unit/

# Only fast tests (skip slow ones)
pytest -m "not slow"

# Run tests in parallel (faster)
pytest -n auto
```

---

## Understanding Test Output

### ✅ All Tests Pass

```
===================== 20 passed in 18.45s ======================
```

→ Everything works! Safe to commit.

### ❌ Test Failure

```
FAILED tests/integration/test_workflows/test_step1_parse_events.py::test_parse_cgm_events

def test_parse_cgm_events(db_session, sample_cgm_events):
    result = parse_cgm_events(db_session, sample_cgm_events)
>   assert len(result) == 10
E   AssertionError: assert 8 == 10

tests/integration/test_workflows/test_step1_parse_events.py:25: AssertionError
```

**What to do**:
1. Read the assertion error: Expected 10 CGM events, got 8
2. Check if your code change affected CGM parsing
3. Fix the issue or update the test if expectation changed
4. Re-run: `pytest tests/integration/test_workflows/test_step1_parse_events.py`

### ⚡ Skipped Tests

```
1 passed, 1 skipped in 2.34s
```

→ Slow tests skipped (normal when using `-m "not slow"`)

---

## Common Testing Scenarios

### Scenario 1: Changed Event Parsing Logic

**Test to run**:
```bash
pytest tests/integration/test_workflows/test_step1_parse_events.py -v
```

**What it validates**:
- Raw events → parsed events transformation
- Event types correctly identified
- Timestamps preserved
- Event data extracted correctly

### Scenario 2: Modified CGM Extraction

**Test to run**:
```bash
pytest tests/integration/test_workflows/test_step2_extract_cgm.py -v
```

**What it validates**:
- CGM readings extracted from events
- Glucose values correct
- Timestamps match events
- No duplicate readings

### Scenario 3: Changed Database Schema

**Test to run**:
```bash
pytest tests/unit/test_db/test_models.py -v
```

**What it validates**:
- Model definitions match expectations
- Relationships work correctly
- Constraints enforced

### Scenario 4: Full Pipeline Validation

**Test to run**:
```bash
pytest tests/integration/test_workflows/test_full_pipeline.py -v
```

**What it validates**:
- Complete workflow from fetch to extraction
- All stages produce correct output
- Data integrity maintained throughout

---

## Pre-Commit Hooks

Tests run automatically before each commit (fast tests only).

### Normal Commit Flow

```bash
git add .
git commit -m "Fix CGM parsing bug"
```

**What happens**:
```
ruff format..............................................................Passed
ruff (legacy alias)......................................................Passed
Detect hardcoded secrets.................................................Passed
pytest-fast..............................................................Passed
[main abc1234] Fix CGM parsing bug
```

→ Commit succeeds

### Commit with Failing Tests

```bash
git commit -m "WIP: refactoring"
```

**What happens**:
```
pytest-fast..............................................................Failed
- hook id: pytest-fast
- exit code: 1

FAILED tests/integration/test_workflows/test_step1_parse_events.py::test_parse_cgm_events
```

→ Commit blocked. Fix tests before committing.

### Bypass Pre-Commit Tests (Emergency Only)

```bash
git commit --no-verify -m "WIP: known broken, will fix"
```

**⚠️ Use sparingly** - Broken code in history makes debugging harder.

---

## Test Performance

### Timing Individual Tests

```bash
pytest --durations=10
```

**Output shows slowest tests**:
```
===== slowest 10 durations =====
8.23s call     tests/integration/test_workflows/test_full_pipeline.py::test_full_pipeline
3.45s call     tests/integration/test_workflows/test_step0_fetch_raw_events.py::test_fetch_events
2.12s call     tests/integration/test_workflows/test_step1_parse_events.py::test_parse_events
```

### Parallel Execution

```bash
# Use all CPU cores
pytest -n auto

# Use specific number of cores
pytest -n 4
```

**Performance improvement**: 4-8x faster with 4+ cores

---

## Debugging Failed Tests

### See Full Traceback

```bash
pytest --tb=long
```

### Stop on First Failure

```bash
pytest -x
```

### Run Only Failed Tests

```bash
# First run
pytest

# Re-run only failures
pytest --lf
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

---

## Writing New Tests

### Test Structure

```python
# tests/integration/test_workflows/test_my_feature.py
import pytest

def test_my_feature(db_session, tandem_api_mock):
    """Test my new feature works correctly."""
    # Arrange: Set up test data
    tandem_api_mock.get(
        'https://api.tandemdiabetes.com/my-endpoint',
        json={'result': 'success'}
    )

    # Act: Run the code
    result = my_feature()

    # Assert: Verify outcome
    assert result == expected_value
```

### Using Fixtures

Available fixtures (defined in `conftest.py`):

- `db_session`: In-memory database session
- `test_db_engine`: Database engine
- `tandem_api_mock`: Mocked Tandem API (requests-mock)
- `sample_pump_events`: Sample pump event data
- `sample_cgm_events`: Sample CGM event data

### Marking Tests

```python
@pytest.mark.slow
def test_full_backfill():
    """Test that takes >5 seconds."""
    pass

@pytest.mark.integration
def test_pipeline_stage():
    """Integration test."""
    pass
```

---

## Fixture Organization

### Loading Test Data from Files

```python
# tests/conftest.py
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def my_test_data():
    """Load test data from JSON file."""
    with open(FIXTURES_DIR / "api_responses" / "my_data.json") as f:
        return json.load(f)
```

### Fixture Files Location

```
tests/
  fixtures/
    api_responses/      # Mock API responses
      auth_success.json
      pump_events_sample.json
      cgm_events.json
    expected/           # Expected test outputs
      parsed_events.json
      cgm_readings.json
```

---

## Troubleshooting

### Problem: Tests are slow (>60 seconds)

**Solutions**:
```bash
# Run only fast tests
pytest -m "not slow"

# Use parallel execution
pytest -n auto

# Check which tests are slow
pytest --durations=10
```

### Problem: Import errors

**Solution**:
```bash
# Ensure dependencies installed
uv sync

# Verify pytest can find modules
pytest --collect-only
```

### Problem: Database errors

**Typical error**:
```
duckdb.IOException: Could not open database
```

**Solutions**:
- Tests use in-memory databases (should never touch files)
- Check if `DATABASE_URL` env var is set (shouldn't be in tests)
- Verify `test_db_engine` fixture is used

### Problem: API mock not working

**Typical error**:
```
requests.exceptions.ConnectionError: Connection refused
```

**Solutions**:
- Verify `tandem_api_mock` fixture is used
- Check mock URL matches actual API call
- Ensure test uses `requests` library (not `httpx` or `urllib`)

---

## Advanced Usage

### Run Specific Test

```bash
pytest tests/integration/test_workflows/test_step1_parse_events.py::test_parse_cgm_events
```

### Parametrized Testing

```python
@pytest.mark.parametrize("glucose_value,expected", [
    (70, "low"),
    (120, "normal"),
    (200, "high"),
])
def test_glucose_classification(glucose_value, expected):
    assert classify_glucose(glucose_value) == expected
```

### Using Test Fixtures in Multiple Tests

```python
# tests/conftest.py
@pytest.fixture
def db_with_events(db_session, sample_pump_events):
    """Database pre-populated with events."""
    for event in sample_pump_events:
        db_session.add(RawEvent(**event))
    db_session.commit()
    return db_session

# Use in test
def test_query_events(db_with_events):
    events = db_with_events.query(RawEvent).all()
    assert len(events) > 0
```

---

## Next Steps

After running tests successfully:

1. ✅ Make your code changes
2. ✅ Run relevant tests: `pytest tests/integration/test_workflows/test_your_area.py`
3. ✅ Fix any failures
4. ✅ Run full suite: `pytest`
5. ✅ Commit (tests run automatically in pre-commit hook)

**Questions?** Check:
- Full test suite: `pytest --collect-only` (see all available tests)
- Pytest docs: https://docs.pytest.org/
- Project-specific fixtures: `tests/conftest.py`

**Happy testing! 🧪**
