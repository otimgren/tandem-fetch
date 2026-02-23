# Feature Specification: MCP Database Server

**Feature Branch**: `007-mcp-server`
**Created**: 2026-02-16
**Status**: Draft
**Input**: User description: "Set up a custom MCP server using FastMCP to expose DuckDB database for AI agent queries"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Health Data via AI Agent (Priority: P1)

A user connects an AI agent (e.g., Claude via Claude Desktop or Claude Code) to their local Tandem pump database. The agent can discover available tables, understand their structure, and run read-only queries to answer questions about the user's CGM readings, basal delivery rates, and pump events.

**Why this priority**: This is the core value proposition — enabling natural language interaction with personal health data through an AI agent. Without query capability, the MCP server has no purpose.

**Independent Test**: Can be fully tested by configuring an AI agent to connect to the MCP server, asking it "What was my average CGM reading last week?", and verifying it discovers the schema, writes an appropriate query, and returns a correct answer.

**Acceptance Scenarios**:

1. **Given** the MCP server is running and the database exists, **When** an agent requests the list of available tables, **Then** the server returns the names of all queryable tables (cgm_readings, basal_deliveries, events, raw_events).
2. **Given** the MCP server is running, **When** an agent requests the schema for the cgm_readings table, **Then** the server returns column names and their types (id, events_id, timestamp, cgm_reading).
3. **Given** the MCP server is running, **When** an agent submits a valid SELECT query, **Then** the server executes it and returns the results in a readable format.
4. **Given** the MCP server is running, **When** an agent submits a query that would return more rows than the configured limit, **Then** the server returns results truncated to the limit with a message indicating truncation.

---

### User Story 2 - Safety Guardrails for Read-Only Access (Priority: P1)

The MCP server enforces read-only access to the database. Any attempt to modify data (INSERT, UPDATE, DELETE, DROP, etc.) is rejected before execution. This protects the user's health data from accidental or unintended modifications by an AI agent.

**Why this priority**: Equal priority with querying — without safety guardrails, the server could corrupt irreplaceable personal health data. This is a non-negotiable safety requirement.

**Independent Test**: Can be tested by attempting to submit a DELETE or DROP query through the MCP server and verifying it is rejected with a clear error message.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an agent submits a query containing INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE statements, **Then** the server rejects the query with a clear error message explaining that only read-only queries are allowed.
2. **Given** the MCP server is running, **When** an agent submits a query with multiple statements (e.g., separated by semicolons), **Then** the server rejects the query to prevent piggy-backed write operations.

---

### User Story 3 - Graceful Handling of Missing Database (Priority: P2)

When the database file does not exist (e.g., fresh install before data has been fetched), the MCP server communicates this clearly to the agent rather than crashing or returning cryptic errors. The agent receives guidance on how to resolve the issue.

**Why this priority**: Important for user experience but not the core functionality. Users will typically have data already fetched before connecting an agent.

**Independent Test**: Can be tested by starting the MCP server without a database file present and verifying the agent receives a helpful error message.

**Acceptance Scenarios**:

1. **Given** the database file does not exist, **When** an agent attempts to query, **Then** the server returns a clear message explaining the database is not found and suggesting the user run the data pipeline first.
2. **Given** the database file does not exist, **When** an agent requests the table list or schema, **Then** the server returns the same helpful guidance message.

---

### Edge Cases

- What happens when a query has a syntax error? The server should return the database error message to help the agent correct its query.
- What happens when the database file is locked by another process? The server should return an appropriate error message.
- What happens when a query takes too long? The server should enforce a reasonable timeout and inform the agent.
- What happens when a query returns zero rows? The server should return an empty result set (not an error).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a tool for listing all available database tables and their descriptions.
- **FR-002**: System MUST expose a tool for retrieving the schema (column names and types) of a specific table.
- **FR-003**: System MUST expose a tool for executing read-only SQL queries against the database.
- **FR-004**: System MUST reject any query that is not a SELECT statement, returning a clear error message.
- **FR-005**: System MUST reject queries containing multiple statements (semicolon-separated).
- **FR-006**: System MUST enforce a configurable maximum row limit on query results (default: 1000 rows).
- **FR-007**: System MUST indicate when results have been truncated due to the row limit.
- **FR-008**: System MUST return query results in a human-readable text format suitable for AI agent consumption.
- **FR-009**: System MUST provide a clear error message when the database file is not found, including instructions to run the data pipeline.
- **FR-010**: System MUST reuse the existing database connection infrastructure (the project's established connection helper and database path configuration).
- **FR-011**: System MUST enforce a query execution timeout to prevent runaway queries.
- **FR-012**: System MUST use STDIO transport for local AI agent integration.

### Key Entities

- **Database Tables**: The four queryable tables — cgm_readings (CGM sensor readings with timestamps), basal_deliveries (insulin basal delivery rates with timestamps), events (parsed pump events with event type and data), and raw_events (original unprocessed event data as JSON).
- **Query**: A read-only SQL SELECT statement submitted by an AI agent, subject to validation and row limits.
- **Query Result**: The formatted output of a successful query, including column headers and row data, with truncation metadata if applicable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An AI agent can discover all available tables and their schemas without prior knowledge of the database structure.
- **SC-002**: An AI agent can answer natural language questions about the user's health data (e.g., "What was my average CGM reading yesterday?") by querying through the MCP server.
- **SC-003**: 100% of write operations (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE) are rejected before execution.
- **SC-004**: Query results are returned within 30 seconds or the query is terminated with a timeout message.
- **SC-005**: The server handles database-not-found scenarios gracefully, with zero crashes or unhandled exceptions.

## Assumptions

- The MCP server runs locally on the same machine as the database file — no network security or authentication is needed beyond the STDIO transport.
- The primary user is the project owner querying their own personal health data through an AI agent (Claude Desktop or Claude Code).
- All four database tables (cgm_readings, basal_deliveries, events, raw_events) are exposed for querying.
- The server is built using FastMCP, the high-level Python framework for MCP servers.
- The server is integrated into the existing tandem_fetch package (not a separate package), reusing the established database connection helpers.
