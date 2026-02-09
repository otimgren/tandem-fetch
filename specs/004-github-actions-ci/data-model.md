# Data Model: GitHub Actions CI

**Feature**: 004-github-actions-ci
**Date**: 2026-02-08

## Overview

This feature involves configuration files and CI artifacts rather than traditional data entities. This document describes the structure and relationships of these configuration entities.

## Configuration Entities

### Workflow File

**Location**: `.github/workflows/ci.yml`

**Purpose**: Defines the automated CI pipeline that runs on GitHub Actions

**Structure**:
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  ci:
    runs-on: ubuntu-latest
    steps: [...]
```

**Key Attributes**:
- **name**: Human-readable workflow identifier
- **on**: Trigger events (push, pull_request)
- **permissions**: GITHUB_TOKEN permissions (read-only for security)
- **jobs**: Collection of jobs to execute
- **steps**: Sequential actions within a job

**Relationships**:
- References GitHub Actions from marketplace (`actions/checkout@v4`, `astral-sh/setup-uv@v7`)
- Consumes `pyproject.toml` for Python version and test configuration
- Consumes `uv.lock` for dependency installation
- Produces CI status checks visible in GitHub PR UI

**Validation Rules**:
- Must be valid YAML syntax
- All action versions must be pinned (not @main or @master)
- Python version must match project constraint (3.12)
- Must include cache pruning step (`uv cache prune --ci`)

### Local CI Script

**Location**: `.github/scripts/run-ci-locally.sh` (or documented in README)

**Purpose**: Allows developers to run CI checks locally before pushing

**Structure**:
```bash
#!/bin/bash
set -e

echo "Running local CI validation..."
uv sync --locked --all-extras --group dev --group test
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

**Key Attributes**:
- **Exit code**: 0 for success, non-zero for failure (matches CI behavior)
- **Environment**: Uses local uv installation, not Docker
- **Output**: Terminal output matching pytest/ruff formats

**Relationships**:
- Replicates workflow steps from `.github/workflows/ci.yml`
- Consumes same dependencies and configuration as CI
- Should produce identical results to GitHub Actions (environment parity)

**Validation Rules**:
- Must use exact same commands as GitHub Actions workflow
- Must fail with non-zero exit code on any check failure
- Should be executable without arguments

### Branch Protection Rules

**Location**: GitHub repository settings (UI-configured, not version-controlled)

**Purpose**: Enforces CI checks must pass before merging to main

**Structure**:
```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
```

**Key Attributes**:
- **required_status_checks.contexts**: List of CI job names that must pass (`["ci"]`)
- **strict**: Branch must be up-to-date before merging
- **enforce_admins**: Whether rules apply to repository admins

**Relationships**:
- References workflow job name from `.github/workflows/ci.yml`
- Blocks PR merge if CI status check fails
- Displayed in PR UI as protection requirements

**Validation Rules**:
- Must reference existing workflow job name
- Should enable "require branches to be up to date" for safety

## State Transitions

### CI Run Lifecycle

```
PR Created/Updated
    ↓
Workflow Triggered
    ↓
[PENDING] Status check created
    ↓
Dependencies Installed (cached or fresh)
    ↓
Linting Executed
    ↓ (pass)
Tests Executed
    ↓ (all pass)
[SUCCESS] Status check updated → PR can be merged
    ↓ (any fail)
[FAILURE] Status check updated → PR blocked
```

### Cache Lifecycle

```
First Run on Main Branch
    ↓
Dependencies downloaded and built
    ↓
Cache stored (key: uv-<hash(uv.lock)>-<week>)
    ↓
Subsequent Runs (same uv.lock, same week)
    ↓
Cache restored (dependencies skip download)
    ↓
Cache pruned at end of job
    ↓
Weekly Rotation
    ↓
Cache key changes (new week number)
    ↓
Fresh cache created
```

## Non-Data Artifacts

### Test Results

**Type**: Transient output (not persisted to database)

**Attributes**:
- **Pass/fail status**: Boolean per test
- **Execution time**: Milliseconds per test
- **Output**: stdout/stderr from test execution
- **Coverage**: Percentage of code covered (optional future enhancement)

**Lifecycle**:
- Generated during workflow execution
- Displayed in GitHub Actions logs
- Not stored persistently (can be extended to upload artifacts if needed)

### Build Logs

**Type**: Transient text output

**Attributes**:
- **Timestamp**: When each step executed
- **Command output**: stdout/stderr from each command
- **Exit codes**: Success/failure status per step

**Lifecycle**:
- Streamed during workflow execution
- Stored by GitHub for ~90 days (configurable)
- Accessible via GitHub Actions UI

## Future Enhancements

### Code Coverage Reports

**Entity**: Coverage.py XML report

**Potential Attributes**:
- **Overall coverage percentage**: Float 0-100
- **Per-file coverage**: Map of file path → percentage
- **Uncovered lines**: List of line numbers per file

**Storage Options**:
- Upload as workflow artifact
- Send to Codecov/Coveralls service
- Store in repository (e.g., `coverage/` directory)

### Performance Metrics

**Entity**: Test duration tracking

**Potential Attributes**:
- **Per-test duration**: Milliseconds per test function
- **Trend data**: Historical duration over time
- **Slow test threshold**: Flag tests exceeding target time

**Storage Options**:
- GitHub Actions annotations
- Separate metrics service
- JSON artifact uploaded per run

## Schema Validation

Since this feature uses YAML configuration rather than database schemas, validation occurs via:

1. **YAML syntax validation**: GitHub Actions validates workflow syntax on push
2. **Action version validation**: Dependabot or Renovate can track action updates
3. **Local validation**: `act` tool can validate workflow syntax locally
4. **Schema linting**: Tools like `actionlint` can validate workflow structure

## Relationships Summary

```
.github/workflows/ci.yml
    ├── triggers on: push, pull_request events
    ├── reads: uv.lock (dependency resolution)
    ├── reads: pyproject.toml (pytest config, Python version)
    ├── produces: CI status check (pass/fail)
    └── stores: cache (uv dependencies)

.github/scripts/run-ci-locally.sh
    ├── replicates: ci.yml workflow steps
    ├── reads: uv.lock, pyproject.toml (same as CI)
    └── outputs: terminal feedback (matches CI output)

Branch Protection Rules (GitHub UI)
    ├── requires: CI status check = success
    ├── blocks: PR merge if CI fails
    └── references: "ci" job name from ci.yml
```

## Notes

- No persistent database entities are created by this feature
- All "data" is ephemeral configuration and runtime state
- GitHub serves as the storage layer for workflow definitions and run history
- Future enhancements could add persistent metrics tracking
