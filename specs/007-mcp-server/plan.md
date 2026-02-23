# Implementation Plan: MCP Database Server

**Branch**: `007-mcp-server` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-mcp-server/spec.md`

## Summary

Build a read-only MCP server using FastMCP that exposes the existing DuckDB database to AI agents over STDIO transport. The server provides three tools — list tables, describe table schema, and execute read-only SQL queries — with safety guardrails (write rejection, row limits, query timeout) to protect personal health data.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastMCP 2.x, SQLAlchemy 2.0.43, duckdb-engine 0.17.0, DuckDB 1.0.0
**Storage**: DuckDB local file at `data/tandem.db` (read-only access)
**Testing**: pytest 8.0 with pytest-xdist, in-memory DuckDB fixtures
**Target Platform**: macOS (local CLI, STDIO transport)
**Project Type**: Single project — new `mcp/` submodule in existing package
**Performance Goals**: Query results within 30 seconds; typical queries < 1 second
**Constraints**: Read-only access only; max 1000 rows per query result; single concurrent user
**Scale/Scope**: 4 database tables, 3 MCP tools, ~150-200 lines of server code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Read-only access enforced — no writes through MCP server. Existing data pipeline unchanged. |
| II. Single-User Simplicity | PASS | Local STDIO transport, no authentication, no multi-tenancy. Single user queries own data. |
| III. Incremental & Resumable | N/A | MCP server is stateless read-only access, not a data fetching operation. |
| IV. Clear Data Pipeline | PASS | MCP server reads from existing pipeline output tables. Does not modify the pipeline. |
| V. Workflow Orchestration | N/A | Server is not a pipeline workflow. No Prefect flows needed. |
| Credential Security | PASS | No credentials exposed through MCP tools. Database is local file access only. |
| Database Schema | PASS | Read-only access. No schema migrations needed. |
| Code Organization | PASS | New `mcp/` submodule follows existing pattern (db/, tasks/, workflows/). |
| Dependency Management | PASS | FastMCP added to pyproject.toml using uv. |
| Testing Philosophy | PASS | Unit tests for query validation and tool logic; integration test for end-to-end MCP flow. |

**Result**: All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/007-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── tools.md         # MCP tool contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/tandem_fetch/
├── mcp/                 # NEW — MCP server submodule
│   ├── __init__.py
│   └── server.py        # FastMCP server with tools
├── db/                  # EXISTING — reused for database access
│   ├── connect.py       # get_engine() helper
│   ├── base.py          # SQLAlchemy Base
│   ├── cgm_readings.py  # CgmReading model
│   ├── basal_deliveries.py  # BasalDelivery model
│   ├── events.py        # Event model
│   └── raw_events.py    # RawEvent model
└── definitions.py       # EXISTING — DATABASE_PATH, DATABASE_URL

tests/unit/
└── test_mcp/            # NEW — MCP server unit tests
    ├── __init__.py
    └── test_server.py   # Tool logic and validation tests

pyproject.toml           # MODIFIED — add fastmcp dependency + entry point
```

**Structure Decision**: Single new `mcp/` submodule within existing `src/tandem_fetch/` package. Follows the established pattern of submodules (db/, tasks/, workflows/). Server code in a single `server.py` file since the scope is small (~3 tools + validation logic). Entry point added to pyproject.toml for CLI invocation.
