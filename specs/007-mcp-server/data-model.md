# Data Model: MCP Database Server

**Feature**: 007-mcp-server
**Date**: 2026-02-16

## Overview

The MCP server does not introduce new data entities. It provides read-only access to the four existing database tables through MCP tools.

## Existing Entities (read-only access)

### cgm_readings

Continuous glucose monitor readings from the insulin pump.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment identifier |
| events_id | Integer (FK → events.id) | Reference to source event |
| timestamp | DateTime | When the reading was taken |
| cgm_reading | Integer | Glucose reading value |

### basal_deliveries

Insulin basal delivery rates from the pump.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment identifier |
| events_id | Integer (FK → events.id) | Reference to source event |
| timestamp | DateTime | When the delivery was recorded |
| profile_basal_rate | Integer | Profile-configured basal rate |
| algorithm_basal_rate | Integer | Algorithm-adjusted basal rate |
| temp_basal_rate | Integer | Temporary basal rate override |

### events

Parsed pump events with structured fields.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment identifier |
| raw_events_id | Integer (unique) | Reference to raw event source |
| created | DateTime | Record creation timestamp |
| timestamp | DateTime | Event timestamp from pump |
| event_id | Integer | Tandem event type identifier |
| event_name | Text | Human-readable event name |
| event_data | JSON | Event-specific parsed data |

### raw_events

Original unprocessed API responses (source of truth).

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment identifier |
| created | DateTime | Record creation timestamp |
| raw_event_data | JSON | Complete raw API response |

## Relationships

```text
raw_events (source of truth)
    ↓ raw_events_id
events (parsed/structured)
    ↓ events_id
cgm_readings          basal_deliveries
```

## Table Descriptions (exposed to agents)

These descriptions are provided by the `list_tables` tool to help agents understand what data is available:

- **cgm_readings**: "CGM (continuous glucose monitor) sensor readings with timestamps. Each row is a single glucose reading."
- **basal_deliveries**: "Insulin basal delivery rates with timestamps. Includes profile, algorithm-adjusted, and temporary basal rates."
- **events**: "Parsed pump events with event type, name, timestamp, and event-specific data as JSON."
- **raw_events**: "Raw unprocessed API responses from the Tandem pump. Contains complete JSON blobs. Prefer querying the parsed tables (events, cgm_readings, basal_deliveries) for structured data."
