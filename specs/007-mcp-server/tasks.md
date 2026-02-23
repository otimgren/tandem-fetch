# Tasks: MCP Database Server

**Input**: Design documents from `/specs/007-mcp-server/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tools.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add FastMCP dependency, create MCP module structure, add CLI entry point

- [x] T001 Add `fastmcp>=2.0` to dependencies and `tandem-mcp = "tandem_fetch.mcp.server:main"` to `[project.scripts]` in pyproject.toml
- [x] T002 Run `uv sync` to install the new fastmcp dependency
- [x] T003 Create src/tandem_fetch/mcp/__init__.py (empty) and src/tandem_fetch/mcp/server.py with FastMCP server instance and `main()` entry point. Server name: `"tandem-db"`. The `main()` function should call `mcp.run()` for STDIO transport. Import `FastMCP` from `fastmcp`. Use `from fastmcp.exceptions import ToolError` for error handling.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Query validation logic shared by US1 (query tool) and US2 (safety guardrails)

**CRITICAL**: The query validation function is required before implementing the query tool.

- [x] T004 Implement `_validate_query(sql: str)` helper function in src/tandem_fetch/mcp/server.py. This function should: (1) strip whitespace and check the query starts with SELECT or WITH (case-insensitive) — if not, raise ToolError with "Only read-only SELECT queries are allowed. Write operations (INSERT, UPDATE, DELETE, DROP, etc.) are not permitted."; (2) check for write keywords (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE, MERGE) anywhere in the uppercased query — raise ToolError with same message; (3) check for semicolons (simple check: reject if `;` is present) — raise ToolError with "Only single SQL statements are allowed. Remove semicolons to execute one query at a time." See contracts/tools.md for exact error messages.

**Checkpoint**: Foundation ready — tool implementation can begin

---

## Phase 3: User Story 1 + User Story 2 — Query Health Data with Safety Guardrails (Priority: P1)

**Goal**: Agent can discover tables, inspect schemas, and run validated read-only SQL queries against the DuckDB database. All write operations are rejected before execution.

**Independent Test**: Connect an AI agent to the server, ask "What was my average CGM reading last week?", verify it discovers the schema, writes a SELECT query, and gets results. Then attempt a DELETE query and verify it's rejected.

**Note**: US1 (query capability) and US2 (safety guardrails) are combined because the query validation (US2) is intrinsic to the query tool (US1) — they cannot be meaningfully separated.

### Implementation

- [x] T005 [P] [US1] Implement `list_tables` tool in src/tandem_fetch/mcp/server.py. Use `@mcp.tool` decorator. Takes no parameters. Returns a text string listing all 4 tables with descriptions from data-model.md. Table descriptions: cgm_readings = "CGM (continuous glucose monitor) sensor readings with timestamps. Each row is a single glucose reading.", basal_deliveries = "Insulin basal delivery rates with timestamps. Includes profile, algorithm-adjusted, and temporary basal rates.", events = "Parsed pump events with event type, name, timestamp, and event-specific data as JSON.", raw_events = "Raw unprocessed API responses from the Tandem pump. Contains complete JSON blobs. Prefer querying the parsed tables for structured data." Docstring: "List all available database tables and their descriptions."
- [x] T006 [P] [US1] Implement `describe_table` tool in src/tandem_fetch/mcp/server.py. Use `@mcp.tool` decorator. Takes `table_name: str` parameter. Validate table_name against the 4 known tables — if invalid, raise ToolError listing valid table names. Connect to DB using `get_engine(interactive=False)` from `tandem_fetch.db.connect`, use SQLAlchemy `inspect(engine).get_columns(table_name)` to get column info. Format output per contracts/tools.md example. Docstring: "Get the schema (column names and types) for a specific database table."
- [x] T007 [US1] [US2] Implement `query` tool in src/tandem_fetch/mcp/server.py. Use `@mcp.tool` decorator. Parameters: `sql: str` (required), `limit: int = 1000` (1-10000 range). Implementation: (1) call `_validate_query(sql)` from T004; (2) clamp limit to 1-10000; (3) get engine via `get_engine(interactive=False)`; (4) wrap the SQL with `SELECT * FROM ({sql}) LIMIT {limit+1}` to detect truncation; (5) execute with `engine.connect()` and `conn.execute(text(wrapped_sql))` inside a timeout; (6) format results as tab-separated text with column headers; (7) append row count message, with truncation notice if rows > limit (see contracts/tools.md for exact format). For timeout: use Python's `signal.alarm(30)` or wrap in a try/except with a 30-second limit. On SQL errors, return the database error message to help the agent self-correct. Docstring: "Execute a read-only SQL query against the Tandem pump database. Only SELECT queries are allowed."

**Checkpoint**: US1 + US2 functional — agent can discover schema and query data; all write operations rejected

---

## Phase 4: User Story 3 — Graceful Missing Database Handling (Priority: P2)

**Goal**: All tools return a clear, helpful error message when the database file doesn't exist, rather than crashing.

**Independent Test**: Remove or rename `data/tandem.db`, call any tool, verify a helpful message appears telling the user to run `run-pipeline`.

### Implementation

- [x] T008 [US3] Add database existence check to all three tools in src/tandem_fetch/mcp/server.py. At the start of `list_tables`, `describe_table`, and `query`, check if `DATABASE_PATH.exists()` (import from `tandem_fetch.definitions`). If the file is missing, raise ToolError with: "Database not found at {DATABASE_PATH}. Run 'run-pipeline' to fetch data from the Tandem API before querying." This replaces the need to call `get_engine()` and catching DatabaseNotFoundError — check the file directly for a clearer error path. Note: `list_tables` doesn't use the DB engine (it's static data), so this check is only needed for `describe_table` and `query`. For `list_tables`, the tool can always return the static table list regardless of DB existence.

**Checkpoint**: All user stories functional — server handles all scenarios gracefully

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Tests, validation, and final cleanup

- [x] T009 [P] Create tests/unit/test_mcp/__init__.py and tests/unit/test_mcp/test_server.py with unit tests for: (1) `_validate_query` — test it accepts valid SELECT and WITH queries, rejects INSERT/UPDATE/DELETE/DROP/ALTER/CREATE, rejects multi-statement queries with semicolons, handles case-insensitive matching, handles whitespace; (2) `describe_table` — test it rejects invalid table names with ToolError; (3) `query` — test result formatting and truncation notice logic. Use the existing `test_db_engine` fixture from conftest.py for tests that need a database connection. Import ToolError from fastmcp.exceptions for assertion checks.
- [x] T010 Verify end-to-end: run `tandem-mcp` from the command line to confirm it starts without errors, then test with an MCP client (Claude Desktop, Claude Code, or MCP Inspector) following the steps in quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T003 creates the file where T004 goes)
- **US1+US2 (Phase 3)**: Depends on Phase 2 (T004 provides validation helper)
- **US3 (Phase 4)**: Depends on Phase 3 (tools must exist before adding DB checks)
- **Polish (Phase 5)**: Depends on Phase 4 (all tools complete before testing)

### Task Dependencies

```
T001 → T002 → T003 → T004 → T005, T006 (parallel) → T007 → T008 → T009 (parallel with T010)
```

### Parallel Opportunities

- T005 and T006 can run in parallel (independent tools, though same file)
- T009 and T010 can run in parallel (tests vs manual validation)

---

## Implementation Strategy

### MVP First (Phase 1-3)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004)
3. Complete Phase 3: US1+US2 tools (T005-T007)
4. **STOP and VALIDATE**: Run `tandem-mcp`, connect with Claude, test a query
5. This delivers the core value — agent can query health data safely

### Full Delivery (Phase 4-5)

6. Complete Phase 4: Missing DB handling (T008)
7. Complete Phase 5: Tests and final validation (T009-T010)

---

## Notes

- All server code goes in a single file: `src/tandem_fetch/mcp/server.py` (~150-200 lines total)
- Reuse existing `get_engine(interactive=False)` from `tandem_fetch.db.connect` — do not create new connection logic
- Reuse existing `DATABASE_PATH` from `tandem_fetch.definitions` for file existence checks
- Use `ToolError` from `fastmcp.exceptions` for all user-facing errors
- Never print to stdout in server code — STDIO transport uses stdout for JSON-RPC messages
- The `tandem-mcp` entry point in pyproject.toml makes it easy to configure in Claude Desktop/Code settings
