# Feature Specification: Integration Tests with Mocked Tandem Source API

**Feature Branch**: `003-integration-tests`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "I want to add some integration tests to this project to make sure everything runs after making changes. I'd like us to mock the Tandem Source API, but other than that everything else should work normally (though some filenames etc. should be modified for tests."

## User Scenarios & Testing

### User Story 1 - End-to-End Pipeline Testing (Priority: P1)

As a developer making code changes, I need integration tests that verify the complete data pipeline works correctly, so I can confidently deploy changes without breaking data fetch and processing.

**Why this priority**: Core value - without pipeline tests, changes risk breaking critical data fetch functionality. This is the MVP that validates the entire system works.

**Independent Test**: Run integration test suite that mocks Tandem API responses, executes full pipeline (fetch → parse → process), and validates data appears correctly in test database.

**Acceptance Scenarios**:

1. **Given** a fresh test database and mocked API responses, **When** I run the integration test suite, **Then** raw events are fetched and stored correctly
2. **Given** raw events in test database, **When** parsing step runs, **Then** events table is populated with correct event types and timestamps
3. **Given** parsed events in test database, **When** CGM reading extraction runs, **Then** CGM readings table contains expected glucose values
4. **Given** parsed events in test database, **When** basal delivery extraction runs, **Then** basal deliveries table contains expected insulin delivery data
5. **Given** a code change that breaks the pipeline, **When** I run integration tests, **Then** tests fail with clear error messages indicating what broke

---

### User Story 2 - Isolated Component Testing (Priority: P2)

As a developer working on specific components, I need tests for individual pipeline stages (fetch, parse events, extract CGM, extract basal) so I can validate changes to one component without running the entire pipeline.

**Why this priority**: Important for development efficiency - allows testing specific changes quickly. However, P2 because the full pipeline test (P1) is more critical for overall system validation.

**Independent Test**: Run test for a single pipeline stage (e.g., just event parsing) with fixture data as input, verify output matches expectations.

**Acceptance Scenarios**:

1. **Given** test fixture with raw pump events, **When** I run event parsing tests, **Then** events are parsed correctly without needing API access
2. **Given** test fixture with parsed events, **When** I run CGM extraction tests, **Then** glucose readings are extracted correctly
3. **Given** test fixture with parsed events, **When** I run basal extraction tests, **Then** insulin delivery data is extracted correctly
4. **Given** a code change affecting only event parsing, **When** I run parsing tests, **Then** only parsing tests run (fast feedback)

---

### User Story 3 - API Mock Validation (Priority: P3)

As a developer, I need to validate that API mocks accurately represent real Tandem Source API responses, so tests remain meaningful as the real API evolves.

**Why this priority**: Nice to have - ensures test quality but not critical for basic functionality. Can validate manually initially and automate later.

**Independent Test**: Compare mock API responses against documented real API response schemas, verify all required fields and data types match.

**Acceptance Scenarios**:

1. **Given** mock API response fixtures, **When** I validate against API documentation, **Then** all required fields are present
2. **Given** mock API response fixtures, **When** I validate data types, **Then** types match real API (strings, integers, timestamps)
3. **Given** a change to mock fixtures, **When** validation runs, **Then** schema compliance is verified

---

### Edge Cases

- What happens when mock API returns malformed JSON? Test should fail gracefully with clear error message
- What happens when test database already contains data from previous test? Tests use temporary in-memory DuckDB databases that are automatically cleaned up after each test
- What happens when a single stage fails mid-pipeline? Test should report which stage failed and provide diagnostic information
- What happens if test fixtures become outdated? Tests should have version markers and fail if fixtures are incompatible with current code
- How are test database files managed? Tests use temporary in-memory DuckDB databases for speed and automatic cleanup

## Requirements

### Functional Requirements

- **FR-001**: Integration tests MUST mock all Tandem Source API HTTP requests without making real network calls
- **FR-002**: Integration tests MUST execute the complete data pipeline from API fetch through data extraction
- **FR-003**: Integration tests MUST use isolated test databases that don't affect production data files
- **FR-004**: Integration tests MUST verify data correctness at each pipeline stage (raw events, parsed events, CGM readings, basal deliveries)
- **FR-005**: Integration tests MUST run automatically as part of pre-commit hooks to ensure all commits pass tests
- **FR-006**: Integration tests MUST complete within 30 seconds for developer feedback
- **FR-007**: Test fixtures MUST include representative sample data covering common event types and edge cases
- **FR-008**: Integration tests MUST clean up test artifacts (databases, temporary files) after execution
- **FR-009**: Integration tests MUST provide clear failure messages indicating which stage failed and why
- **FR-010**: Mock API responses MUST match the structure and data types of real Tandem Source API responses
- **FR-011**: Tests MUST be runnable on developer workstations without special setup beyond installing dependencies
- **FR-012**: Integration tests MUST validate database schema matches expected structure (tables, columns, types)
- **FR-013**: Tests MUST be idempotent - running multiple times produces same results without side effects

### Key Entities

- **Test Fixture**: Sample API response data representing realistic pump events, stored in version-controlled files
- **Test Database**: Isolated DuckDB database used exclusively for testing, separate from production data
- **Mock API Client**: Component that intercepts API calls and returns fixture data instead of making real HTTP requests
- **Test Case**: Individual test validating a specific pipeline stage or integration scenario
- **Test Assertion**: Verification that actual data matches expected values (event counts, field values, data types)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Developers can run full integration test suite and get pass/fail results within acceptable time limit
- **SC-002**: Integration tests catch breaking changes before code is merged (100% of pipeline-breaking changes detected)
- **SC-003**: Test suite executes without requiring Tandem API credentials or network access
- **SC-004**: Each pipeline stage has at least one integration test validating core functionality
- **SC-005**: Test failures provide sufficient diagnostic information to identify root cause without manual debugging
- **SC-006**: Tests run successfully on fresh repository clone with only `uv sync` and test command
- **SC-007**: Test execution is deterministic - same code produces same test results every time
- **SC-008**: Zero test artifacts (databases, temp files) remain after test execution completes
