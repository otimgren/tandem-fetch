# Feature Specification: DuckDB Migration

**Feature Branch**: `001-duckdb-migration`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "Switch to DuckDB. Postgresql is overly complicated to set up for a simple single user project like this, and ultimately the goal will be to do analytics on data, so I think switching to using DuckDB on the backend makes more sense for us. Write a plan to switch everything from postgres to DuckDB. We can start the whole thing over by pulling all data from Tandem, no need to migrate the existing DBs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fresh Data Fetch to DuckDB (Priority: P1)

As a user, I want to run a command that fetches all my insulin pump data from Tandem Source and stores it in a local DuckDB file, so I can start fresh with a simpler database setup.

**Why this priority**: This is the core functionality - without data ingestion, nothing else works. The user explicitly stated they want to "start the whole thing over by pulling all data from Tandem."

**Independent Test**: Can be fully tested by running the fetch command and verifying data appears in the DuckDB file with correct schema and record counts.

**Acceptance Scenarios**:

1. **Given** valid Tandem credentials and an empty or non-existent DuckDB file, **When** I run the data fetch command, **Then** all raw pump events are fetched from Tandem and stored in the DuckDB file.
2. **Given** valid Tandem credentials and an existing DuckDB file with some data, **When** I run the data fetch command, **Then** only new events since the last fetch are retrieved (incremental fetch).
3. **Given** a DuckDB file with raw events, **When** I run the parse command, **Then** raw events are transformed into structured event records and domain-specific tables (CGM readings, basal deliveries).

---

### User Story 2 - Analytics-Ready Data Access (Priority: P2)

As a user, I want to query my insulin pump data using standard SQL tools, so I can perform analytics and generate insights from my health data.

**Why this priority**: The user stated "the goal will be to do analytics on data" - this is the primary motivation for switching to DuckDB.

**Independent Test**: Can be tested by connecting to the DuckDB file with any SQL client and running analytical queries against the data.

**Acceptance Scenarios**:

1. **Given** a DuckDB file with processed data, **When** I connect using DuckDB CLI or any compatible tool, **Then** I can query all tables with standard SQL.
2. **Given** CGM reading data in DuckDB, **When** I run aggregation queries (daily averages, time-in-range calculations), **Then** results are returned efficiently.
3. **Given** the DuckDB file, **When** I export data to Parquet or CSV, **Then** data exports successfully for use in external analytics tools.

---

### User Story 3 - Zero-Setup Database (Priority: P3)

As a user, I want the database to work without installing or configuring any database server, so I can get started immediately after cloning the repository.

**Why this priority**: This directly addresses the user's complaint that "PostgreSQL is overly complicated to set up for a simple single user project."

**Independent Test**: Can be tested by cloning the repo on a fresh machine and running the fetch command without any database setup steps.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repository with Python dependencies installed, **When** I run `uv sync`, **Then** DuckDB is available as a dependency with no additional setup.
2. **Given** no existing database file, **When** I run the fetch command, **Then** the DuckDB file is created automatically in the configured location.
3. **Given** the project running on a different machine, **When** I copy the DuckDB file, **Then** all data is preserved and accessible.

---

### Edge Cases

- What happens when the DuckDB file is locked by another process? System displays clear error message and exits gracefully.
- What happens when disk space runs out during a fetch? Transaction rolls back, partial data is not persisted, error is logged with context.
- What happens when the DuckDB file becomes corrupted? System detects corruption on startup and reports actionable error (user can delete and re-fetch).
- How does the system handle concurrent access for analytics while a fetch is running? DuckDB supports concurrent reads; writes acquire exclusive lock.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store all data in a single DuckDB file (no external database server required)
- **FR-002**: System MUST preserve existing three-stage data pipeline (raw events → parsed events → domain tables)
- **FR-003**: System MUST support incremental fetches that only retrieve new data since last successful fetch
- **FR-004**: System MUST create the database file automatically if it does not exist
- **FR-005**: System MUST use transactions for all write operations with rollback on failure
- **FR-006**: System MUST maintain referential integrity between tables (raw_events → events → domain tables)
- **FR-007**: System MUST store timestamps with timezone information
- **FR-008**: System MUST support JSON data storage for raw event payloads
- **FR-009**: System MUST provide CLI commands for data fetching and processing (existing command interface preserved)
- **FR-010**: System MUST remove all PostgreSQL-specific dependencies and configuration

### Key Entities

- **Raw Event**: Unprocessed API response from Tandem Source, stored as JSON blob with fetch timestamp
- **Event**: Parsed event record with extracted timestamp, event ID, event name, and structured event data
- **CGM Reading**: Blood glucose measurement extracted from CGM events, with timestamp and reading value
- **Basal Delivery**: Insulin basal rate record with profile, algorithm, and temp basal rates

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can fetch and store all pump data with zero database server setup (only `uv sync` required)
- **SC-002**: All existing data pipeline stages complete successfully with DuckDB backend
- **SC-003**: Full historical data fetch completes without data loss (same record count as PostgreSQL baseline)
- **SC-004**: Analytical queries (aggregations, joins, filters) execute against the data
- **SC-005**: Database file is portable - can be copied to another machine and accessed immediately
- **SC-006**: Setup instructions in README reduce from 5+ steps (install PostgreSQL, create database, configure connection, run migrations) to 1 step (run fetch command)

## Assumptions

- DuckDB's SQLAlchemy dialect supports the required column types (JSON, DateTime with timezone, Integer)
- The existing Alembic migration approach may need to be replaced or adapted for DuckDB's file-based model
- The workflow orchestrator (Prefect) continues to work with the new database backend
- Single-file database is sufficient for the expected data volume (years of pump data for one user)
- DuckDB's default configuration is suitable without tuning for this use case
