# Feature Specification: Database Connection Helpers

**Feature Branch**: `006-db-connection-helpers`
**Created**: 2026-02-16
**Status**: Draft
**Input**: User description: "Set up helpers for external packages to connect to the database files. Pass a SQLAlchemy connection to the DB to external users, after checking that the DB files exist (if they don't exist, ask if the user would like to fetch the data)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect to Existing Database (Priority: P1)

An external package developer (e.g., building an analysis or visualization tool in the health-stack ecosystem) wants to connect to the tandem database to query health data. They call a helper function from `tandem_fetch` and receive a SQLAlchemy connection they can use for queries. The database file already exists on disk because data has been previously fetched.

**Why this priority**: This is the core use case — providing a simple, validated connection to external consumers. Without this, there is no feature.

**Independent Test**: Can be fully tested by calling the helper function when a valid database file exists and verifying a working SQLAlchemy connection is returned that can execute queries against the database schema.

**Acceptance Scenarios**:

1. **Given** the database file exists at the configured path, **When** an external package calls the connection helper, **Then** a valid SQLAlchemy connection to the DuckDB database is returned.
2. **Given** a valid connection has been returned, **When** the external package executes a query (e.g., selecting from `cgm_readings`), **Then** the query succeeds and returns data.
3. **Given** a valid connection has been returned, **When** the external package is done using it, **Then** the connection can be cleanly closed without resource leaks.

---

### User Story 2 - Database File Missing with Recovery Option (Priority: P2)

An external package developer calls the connection helper, but the database file does not exist (e.g., fresh clone, new machine, or data directory was cleared). The system detects this and offers the user a choice: either fetch the data now (triggering the existing data pipeline) or exit gracefully with an informative message.

**Why this priority**: Provides a smooth onboarding experience for new setups, but depends on the core connection capability from P1.

**Independent Test**: Can be fully tested by calling the helper function when no database file exists and verifying the system prompts the user with options and handles each choice correctly.

**Acceptance Scenarios**:

1. **Given** the database file does not exist, **When** an external package calls the connection helper, **Then** the system informs the user that the database is missing and offers to fetch the data.
2. **Given** the database file does not exist and the user chooses to fetch data, **When** the data pipeline completes successfully, **Then** a valid SQLAlchemy connection is returned as if the database had existed all along.
3. **Given** the database file does not exist and the user declines to fetch data, **Then** the system exits gracefully with a clear message explaining how to fetch data manually.

---

### User Story 3 - Programmatic Use Without Interactive Prompts (Priority: P3)

An external package is running in a non-interactive context (e.g., a scheduled script, CI pipeline, or automated notebook). The connection helper should support a mode where it does not prompt the user interactively — instead, it either connects if the database exists or raises an informative error if it does not.

**Why this priority**: Supports automated workflows, but the interactive flow (P1 + P2) covers the primary use case first.

**Independent Test**: Can be fully tested by calling the helper in non-interactive mode when the database does not exist and verifying it raises an appropriate error rather than blocking on input.

**Acceptance Scenarios**:

1. **Given** the database file exists and the helper is called in non-interactive mode, **When** the connection is requested, **Then** a valid SQLAlchemy connection is returned (same behavior as P1).
2. **Given** the database file does not exist and the helper is called in non-interactive mode, **When** the connection is requested, **Then** an informative error is raised explaining the database is missing and how to populate it.

---

### Edge Cases

- What happens when the database file exists but is corrupted or has an incompatible schema? The system should detect the failure at connection time and provide a clear error message rather than surfacing obscure database errors.
- What happens when the data pipeline is triggered but fails partway through (e.g., network error, expired credentials)? The error should propagate clearly to the caller rather than returning a connection to a partially populated database.
- What happens when multiple external packages attempt to connect simultaneously? DuckDB supports multiple readers, so concurrent read access should work without additional handling.
- What happens when the database file path has been customized or overridden? The helper should use the configured database path from the project definitions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a public helper function that returns a SQLAlchemy connection to the tandem DuckDB database.
- **FR-002**: System MUST verify that the database file exists at the configured path before attempting to connect.
- **FR-003**: System MUST, when the database file is missing in interactive mode, prompt the user with a choice to either fetch the data or exit.
- **FR-004**: System MUST, when the user chooses to fetch data, execute the existing full data pipeline and then return a valid connection.
- **FR-005**: System MUST, when the user declines to fetch data, exit without error and display instructions for manual data fetching.
- **FR-006**: System MUST support a non-interactive mode that raises an informative error when the database file is missing instead of prompting.
- **FR-007**: System MUST return connections that allow read access to all tables in the database schema (raw_events, events, cgm_readings, basal_deliveries).
- **FR-008**: System MUST ensure returned connections can be used as context managers for clean resource management.

### Key Entities

- **Database Connection**: A SQLAlchemy connection object pointing to the local DuckDB file, providing read access to health data tables.
- **Connection Helper**: The public-facing function that validates database existence, handles missing database scenarios, and returns a usable connection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: External packages can obtain a working database connection with a single function call.
- **SC-002**: When the database file is missing, 100% of interactive users receive a clear prompt with actionable options within one function call.
- **SC-003**: Non-interactive callers receive an informative error (not an obscure file-not-found) when the database is missing.
- **SC-004**: All returned connections successfully execute read queries against every table in the database schema.
- **SC-005**: Connection helper has full unit test coverage for all acceptance scenarios (database exists, database missing interactive, database missing non-interactive).
