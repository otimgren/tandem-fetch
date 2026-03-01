# Feature Specification: Continuous Data Fetch

**Feature Branch**: `008-continuous-fetch`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "I'd like to start continuously fetching data from tandem (say every 5 min by default). Could you spec out how we could do that?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Continuous Data Fetching (Priority: P1)

The user starts a long-running process that automatically fetches new pump data from the Tandem API at a regular interval and processes it through the full data pipeline (fetch raw events, parse events, extract CGM readings, extract basal deliveries). This keeps the local database continuously up-to-date without manual intervention. The process runs in the foreground and can be stopped with Ctrl+C.

**Why this priority**: This is the core value proposition — replacing manual on-demand fetches with automated continuous updates. Without this, the user must remember to run the pipeline manually every time they want fresh data.

**Independent Test**: Start the continuous fetch process, wait for at least two fetch cycles to complete, then query the database to confirm new data was fetched and processed through all pipeline stages.

**Acceptance Scenarios**:

1. **Given** the user has valid credentials configured, **When** they start the continuous fetch process, **Then** it immediately runs a full data pipeline cycle and then repeats at the configured interval.
2. **Given** the continuous fetch process is running, **When** the configured interval elapses, **Then** it runs the next pipeline cycle and only fetches data newer than the last recorded event.
3. **Given** the continuous fetch process is running, **When** the user presses Ctrl+C, **Then** the process stops gracefully after completing any in-progress cycle (or cancels promptly if between cycles).

---

### User Story 2 - Configurable Fetch Interval (Priority: P2)

The user can specify a custom fetch interval when starting the continuous fetch process. The default interval is 5 minutes, but it can be adjusted (e.g., every 1 minute for closer-to-real-time data, or every 30 minutes to reduce API usage).

**Why this priority**: Important for flexibility but the default of 5 minutes works for most use cases. Some users may want more or less frequent updates depending on their needs.

**Independent Test**: Start the continuous fetch with a custom interval (e.g., 1 minute), verify that cycles run at the specified interval rather than the default.

**Acceptance Scenarios**:

1. **Given** the user starts the continuous fetch with no interval specified, **When** the process is running, **Then** it uses the default interval of 5 minutes between cycles.
2. **Given** the user starts the continuous fetch with a custom interval (e.g., 1 minute), **When** the process is running, **Then** it uses the specified interval between cycles.
3. **Given** the user specifies an interval below the minimum allowed (e.g., 0 seconds), **When** the process starts, **Then** it rejects the input with a clear error message stating the minimum interval.

---

### User Story 3 - Resilient Operation Through Transient Failures (Priority: P2)

The continuous fetch process recovers gracefully from transient errors (network timeouts, API rate limits, temporary authentication failures) without stopping the entire process. After a failed cycle, it waits and retries on the next interval. Persistent failures are surfaced clearly.

**Why this priority**: The Tandem API may experience intermittent issues, and the process should be resilient enough to run unattended for extended periods without crashing.

**Independent Test**: Simulate a network failure during a fetch cycle and verify the process logs the error but continues to the next scheduled cycle.

**Acceptance Scenarios**:

1. **Given** the continuous fetch process is running, **When** a single fetch cycle fails due to a transient error, **Then** the process logs the error and continues to the next scheduled cycle.
2. **Given** the continuous fetch process is running, **When** multiple consecutive cycles fail, **Then** the process logs each failure and continues attempting on schedule.
3. **Given** a cycle fails, **When** the next cycle runs, **Then** it picks up from the same point (last successful event timestamp), ensuring no data is lost.

---

### Edge Cases

- What happens when the Tandem API credentials expire during a long-running session? The process should attempt to re-authenticate and continue. If re-authentication fails, it should log the error and keep retrying on schedule.
- What happens if the system clock changes (e.g., DST transition) while the process is running? The interval should be based on elapsed time, not wall-clock targets.
- What happens if the database file is deleted while the process is running? The process should report the error clearly and stop.
- What happens if there's no new data since the last fetch? The cycle should complete successfully with a log message indicating no new data was found.
- What happens if a fetch cycle takes longer than the configured interval? The next cycle should start after the current one completes, not overlap with it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a command to start continuous data fetching that runs the full pipeline (fetch raw events, parse events, extract CGM readings, extract basal deliveries) on a repeating interval.
- **FR-002**: System MUST use a default interval of 5 minutes between pipeline cycles.
- **FR-003**: Users MUST be able to specify a custom interval when starting the continuous fetch.
- **FR-004**: System MUST enforce a minimum interval of 1 minute to avoid overloading the API.
- **FR-005**: System MUST run an initial pipeline cycle immediately upon starting, then repeat at the configured interval.
- **FR-006**: System MUST use the existing incremental fetching logic to only retrieve new data since the last recorded event.
- **FR-007**: System MUST stop gracefully when the user sends an interrupt signal (Ctrl+C).
- **FR-008**: System MUST recover from transient errors (network issues, API errors) without stopping the process, logging each failure and continuing to the next scheduled cycle.
- **FR-009**: System MUST log the start and completion of each pipeline cycle, including the number of new events fetched and the time taken.
- **FR-010**: System MUST prevent overlapping cycles — if a cycle takes longer than the interval, the next cycle waits until the current one finishes.

### Key Entities

- **Fetch Cycle**: A single execution of the full data pipeline (fetch → parse → extract). Includes timing metadata (start time, duration, events fetched) and outcome (success or failure with error details).
- **Fetch Interval**: The configurable time period between the end of one cycle and the start of the next. Default: 5 minutes. Minimum: 1 minute.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After starting, the system fetches and processes new data within 5 minutes (or the configured interval) without manual intervention.
- **SC-002**: The system runs unattended for at least 24 hours without crashing due to transient errors.
- **SC-003**: 100% of successfully fetched data is processed through all pipeline stages (not left as raw events only).
- **SC-004**: Data queried through the MCP server reflects updates within one fetch interval of the data being available in the Tandem API.
- **SC-005**: The user can start and stop the continuous fetch process with a single command and Ctrl+C respectively.

## Assumptions

- The continuous fetch runs as a foreground process started via a CLI command (consistent with the project's single-user CLI-first design).
- The existing incremental pipeline logic is reused — this feature adds scheduling/looping on top, not a new data pathway.
- All four pipeline stages run in each cycle. Partial-pipeline runs are not supported (to ensure data consistency).
- The process runs on the same machine as the database file and credentials — no remote deployment considerations.
- Logging uses the project's existing logging infrastructure for observability.
- The 5-minute default interval is a balance between data freshness and API usage. The Tandem pump typically reports new CGM readings every 5 minutes, making this a natural cadence.
