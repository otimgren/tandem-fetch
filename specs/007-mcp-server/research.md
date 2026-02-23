# Research: MCP Database Server

**Feature**: 007-mcp-server
**Date**: 2026-02-16

## R1: MCP Server Framework

**Decision**: FastMCP 2.x (`fastmcp` package on PyPI)

**Rationale**: FastMCP is the high-level Python framework for building MCP servers. It provides decorator-based tool registration, automatic JSON schema generation from type hints, and built-in STDIO transport. The API is minimal — a single `FastMCP` class with `@mcp.tool` decorators. This aligns with Constitution Principle II (Single-User Simplicity).

**Alternatives considered**:
- Raw MCP Python SDK (`mcp` package): Lower-level, requires manual protocol handling. More boilerplate for the same result.
- Off-the-shelf DuckDB MCP servers (MotherDuck, ktanaka101): Would work but don't integrate with existing `get_engine()` helper or allow custom validation logic.

## R2: Tool Design

**Decision**: Three tools — `list_tables`, `describe_table`, `query`

**Rationale**: This is the minimal set needed for an agent to discover the schema and query data. The `list_tables` tool provides entry-point discovery. The `describe_table` tool gives column-level detail. The `query` tool executes validated SELECT statements. This three-tool pattern is standard across database MCP servers.

**Alternatives considered**:
- Single `query` tool only: Agents would need to guess table names or use `information_schema` queries. Dedicated schema tools are more reliable.
- Additional tools (aggregate, filter, export): Over-engineering for the current use case. SQL is expressive enough through the `query` tool.

## R3: Query Validation Strategy

**Decision**: Keyword-based validation — strip and uppercase the query, check it starts with `SELECT` or `WITH`, reject if it contains write keywords (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, REPLACE, MERGE), reject multiple statements (semicolons in non-string positions).

**Rationale**: Simple and effective for a single-user local server. The goal is to prevent accidental writes by an AI agent, not to defend against adversarial SQL injection. Constitution Principle I (Data Integrity) requires protecting data from corruption, but Principle II (Single-User Simplicity) says not to over-engineer.

**Alternatives considered**:
- SQL parser (sqlglot, sqlparse): More robust but adds a dependency for minimal benefit in this context. The user is the only operator and the threat model is "agent accidentally writes data."
- DuckDB read-only mode (`access_mode='read_only'`): Could be used as a belt-and-suspenders approach alongside keyword validation. Worth considering as a secondary defense.

## R4: Result Formatting

**Decision**: Return results as formatted text with column headers and tab-separated values. Include row count and truncation notice.

**Rationale**: AI agents consume text naturally. A simple tabular format with headers is easy for agents to parse and reason about. Markdown tables would also work but add formatting overhead.

**Alternatives considered**:
- JSON output: More structured but harder for agents to read in context. Good for programmatic use but not the primary use case.
- Markdown tables: Render nicely but can be verbose for many columns. Also more complex to generate.

## R5: Transport

**Decision**: STDIO (default FastMCP transport)

**Rationale**: STDIO is the standard transport for local MCP servers used with Claude Desktop and Claude Code. No network setup, no ports, no authentication needed. Aligns with Constitution Principle II (Single-User Simplicity).

**Alternatives considered**:
- HTTP+SSE: Needed for remote access. Not applicable for local single-user use.

## R6: Error Handling

**Decision**: Use FastMCP's `ToolError` exception for validation errors (write rejection, missing DB). Return database error messages directly for SQL errors (syntax errors, etc.) to help agents self-correct.

**Rationale**: Agents benefit from clear error messages to adjust their queries. ToolError is the standard FastMCP mechanism and surfaces errors properly in the MCP protocol.

## R7: Entry Point

**Decision**: Add `tandem-mcp` script entry point in pyproject.toml pointing to `tandem_fetch.mcp.server:main`.

**Rationale**: Follows the existing pattern of CLI entry points in the project (run-pipeline, export-data, etc.). Makes it easy to configure in Claude Desktop/Code settings as a command.
