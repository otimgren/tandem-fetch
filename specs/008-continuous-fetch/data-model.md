# Data Model: Continuous Data Fetch

**Feature**: 008-continuous-fetch
**Date**: 2026-02-28

## Overview

This feature does not introduce new data entities or database tables. It adds a scheduling layer on top of the existing data pipeline, reusing the same tables and incremental logic.

## Existing Entities (unchanged)

The continuous fetch runs the existing full pipeline on each cycle, which operates on:

- **raw_events**: Raw API responses (source of truth) — written by Step 0
- **events**: Parsed pump events — written by Step 1
- **cgm_readings**: CGM glucose readings — written by Step 2
- **basal_deliveries**: Insulin basal delivery rates — written by Step 3

## Scheduling Concepts (no persistence)

- **Fetch Cycle**: A single execution of the full 4-step pipeline. Tracked by the workflow orchestrator (Prefect), not by new database tables. Each cycle is an independent flow run with its own logs and state.
- **Fetch Interval**: A runtime configuration parameter (default: 5 minutes, minimum: 1 minute). Not persisted — set via CLI argument at startup.
