# Data Model: DuckDB Migration

**Date**: 2026-01-31
**Feature**: 001-duckdb-migration

## Overview

This document describes the data model for the DuckDB-based storage. The schema preserves the existing three-stage pipeline structure while adapting to DuckDB-specific requirements.

## Entity Relationship Diagram

```
┌─────────────────┐
│   raw_events    │
├─────────────────┤
│ id (PK)         │
│ created         │
│ raw_event_data  │──────┐
└─────────────────┘      │
                         │ 1:1
                         ▼
┌─────────────────┐      │
│     events      │◄─────┘
├─────────────────┤
│ id (PK)         │
│ raw_events_id   │──────┐
│ created         │      │
│ timestamp       │      │
│ event_id        │      │
│ event_name      │      │
│ event_data      │      │
└─────────────────┘      │
         │               │
         │ 1:1           │ 1:1
         ▼               ▼
┌─────────────────┐    ┌──────────────────┐
│  cgm_readings   │    │ basal_deliveries │
├─────────────────┤    ├──────────────────┤
│ id (PK)         │    │ id (PK)          │
│ events_id (FK)  │    │ events_id (FK)   │
│ timestamp       │    │ timestamp        │
│ cgm_reading     │    │ profile_basal_   │
└─────────────────┘    │   rate           │
                       │ algorithm_basal_ │
                       │   rate           │
                       │ temp_basal_rate  │
                       └──────────────────┘
```

## Tables

### Stage 1: raw_events

Stores unprocessed API responses from Tandem Source. This is the source of truth.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, auto-increment via Sequence | Unique identifier |
| created | TIMESTAMP | NOT NULL, DEFAULT now() | When record was inserted |
| raw_event_data | JSON | NOT NULL | Complete API response payload |

**Indexes**:
- Primary key on `id`
- Index on `created` for incremental fetch queries

**DuckDB-specific**:
- Auto-increment via `Sequence('raw_events_id_seq')`

### Stage 2: events

Parsed events with extracted fields from raw data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, auto-increment via Sequence | Unique identifier |
| raw_events_id | INTEGER | NOT NULL, UNIQUE, FK → raw_events.id | Link to source raw event |
| created | TIMESTAMP | NOT NULL, DEFAULT now() | When record was inserted |
| timestamp | TIMESTAMP | NOT NULL | Event timestamp from pump |
| event_id | INTEGER | NOT NULL | Tandem event type ID |
| event_name | TEXT | NOT NULL | Human-readable event name |
| event_data | JSON | NULLABLE | Parsed event-specific data |

**Indexes**:
- Primary key on `id`
- Unique index on `raw_events_id`
- Index on `timestamp` for time-range queries
- Index on `event_name` for filtering by event type

### Stage 3a: cgm_readings

Continuous glucose monitor readings extracted from CGM events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, auto-increment via Sequence | Unique identifier |
| events_id | INTEGER | NOT NULL, UNIQUE, FK → events.id | Link to source event |
| timestamp | TIMESTAMP | NOT NULL | Reading timestamp |
| cgm_reading | INTEGER | NOT NULL | Glucose value in mg/dL |

**Indexes**:
- Primary key on `id`
- Unique index on `events_id`
- Index on `timestamp` for time-series queries

### Stage 3b: basal_deliveries

Basal insulin delivery records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, auto-increment via Sequence | Unique identifier |
| events_id | INTEGER | NOT NULL, UNIQUE, FK → events.id | Link to source event |
| timestamp | TIMESTAMP | NOT NULL | Delivery timestamp |
| profile_basal_rate | INTEGER | NULLABLE | Programmed profile rate (units * 1000) |
| algorithm_basal_rate | INTEGER | NULLABLE | Control-IQ algorithm rate |
| temp_basal_rate | INTEGER | NULLABLE | Temporary basal rate if active |

**Indexes**:
- Primary key on `id`
- Unique index on `events_id`
- Index on `timestamp` for time-series queries

## Validation Rules

### raw_events
- `raw_event_data` must be valid JSON
- `raw_event_data` must contain required Tandem API fields (validated at application level)

### events
- `raw_events_id` must reference existing raw_events record
- `event_name` must be non-empty
- `timestamp` must be a valid datetime

### cgm_readings
- `cgm_reading` must be positive integer (typically 40-400 mg/dL range)
- `events_id` must reference an event with CGM-related event_name

### basal_deliveries
- At least one of the rate columns should be non-null
- Rate values are integers representing units * 1000 (e.g., 1500 = 1.5 units/hr)

## Data Pipeline Flow

```
1. Fetch from Tandem API
   ↓
2. Insert into raw_events (JSON blob)
   ↓
3. Parse raw_events → insert into events
   ↓
4. Filter events by type → insert into domain tables
   - CGM events → cgm_readings
   - Basal events → basal_deliveries
   - (Future: bolus events → boluses)
```

## DuckDB-Specific Considerations

### Sequences for Auto-increment

DuckDB doesn't support PostgreSQL's SERIAL type. Use SQLAlchemy Sequences:

```python
from sqlalchemy import Sequence

class RawEvent(Base):
    __tablename__ = "raw_events"
    id = Column(Integer, Sequence('raw_events_id_seq'), primary_key=True)
```

### JSON Storage

DuckDB stores JSON as validated VARCHAR. Query JSON fields using:
- `json_extract(column, '$.field')`
- `column->>'field'` (PostgreSQL-style, supported)

### Timestamp Handling

DuckDB TIMESTAMP stores microseconds since epoch. For timezone-aware queries:
- Store as TIMESTAMP (no timezone)
- Handle timezone conversion in application code
- Use `SET TimeZone` for session-level timezone

### File Location

Database stored at: `data/tandem.db` (relative to project root)
- Auto-created on first connection
- Gitignored (contains personal health data)
