# Quickstart: MCP Database Server

**Feature**: 007-mcp-server
**Date**: 2026-02-16

## Prerequisites

1. Python 3.12+
2. The tandem-fetch project installed with dependencies
3. Data fetched (database exists at `data/tandem.db`) — run `run-pipeline` if needed

## Installation

```bash
# From the project root, install with the new dependency
uv sync
```

This installs `fastmcp` alongside existing dependencies.

## Running the MCP Server

### Direct invocation

```bash
tandem-mcp
```

This starts the MCP server with STDIO transport. It will wait for JSON-RPC messages on stdin.

### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tandem-db": {
      "command": "tandem-mcp",
      "args": []
    }
  }
}
```

Restart Claude Desktop. The "tandem-db" tools will be available in conversations.

### With Claude Code

Add to your Claude Code MCP settings (`.claude/settings.json` or project settings):

```json
{
  "mcpServers": {
    "tandem-db": {
      "command": "tandem-mcp",
      "args": []
    }
  }
}
```

## Available Tools

Once connected, the agent has access to three tools:

1. **list_tables** — Discover available tables and their descriptions
2. **describe_table** — Get column names and types for a specific table
3. **query** — Execute a read-only SQL SELECT query

## Example Agent Interaction

```
User: "What was my average CGM reading this week?"

Agent thinks: I need to find CGM data. Let me check what tables are available.
Agent calls: list_tables()
Agent sees: cgm_readings table has glucose readings with timestamps.
Agent calls: describe_table(table_name="cgm_readings")
Agent sees: columns are id, events_id, timestamp, cgm_reading.
Agent calls: query(sql="SELECT AVG(cgm_reading) as avg_reading FROM cgm_readings WHERE timestamp >= '2026-02-10'")
Agent responds: "Your average CGM reading this week was 135 mg/dL."
```

## Running Tests

```bash
pytest tests/unit/test_mcp/
```
