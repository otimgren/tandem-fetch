<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (Initial ratification)
Modified principles: N/A (initial)
Added sections:
  - Core Principles (5 principles)
  - Data Handling section
  - Development Workflow section
  - Governance section
Removed sections: N/A (initial)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ reviewed (no updates needed)
  - .specify/templates/spec-template.md ✅ reviewed (no updates needed)
  - .specify/templates/tasks-template.md ✅ reviewed (no updates needed)
Follow-up TODOs: None
-->

# Tandem Fetch Constitution

## Core Principles

### I. Data Integrity First

All insulin pump and CGM data MUST be stored accurately and completely. Data loss or corruption is unacceptable for health-related records.

- Raw API responses MUST be preserved before any transformation
- All database operations MUST use transactions with proper rollback on failure
- Incremental fetches MUST NOT create duplicate records
- Data transformations MUST be idempotent and reproducible from raw data

**Rationale**: This is personal health data used for medical decisions. Accuracy and completeness are non-negotiable.

### II. Single-User Simplicity

This project serves a single user fetching their own data. Design decisions MUST prioritize simplicity over multi-tenancy or scalability concerns.

- No user management, authentication services, or multi-tenant isolation required
- Configuration via simple files (TOML) rather than complex config systems
- CLI commands preferred over web interfaces for data operations
- Local DB sufficient; no distributed database concerns

**Rationale**: Over-engineering for hypothetical scale wastes effort. Keep it simple for the actual use case.

### III. Incremental & Resumable

Data fetching MUST support incremental updates and graceful recovery from interruptions.

- Track last successful fetch timestamp per data type
- Support resuming interrupted backfills without re-fetching completed data
- Manual trigger for updates MUST fetch only new data since last run
- Future scheduled fetches MUST use the same incremental logic

**Rationale**: The API has rate limits and the dataset is large. Efficient incremental fetching is essential.

### IV. Clear Data Pipeline

The data flow from API to final tables MUST be explicit and traceable.

- Stage 1: Raw events stored as received from API (source of truth)
- Stage 2: Parsed events with structured fields extracted
- Stage 3: Domain-specific tables (CGM readings, basal deliveries, boluses, etc.)
- Each stage MUST be independently runnable and idempotent

**Rationale**: Debugging data issues requires tracing back through the pipeline. Clear stages enable this.

### V. Workflow Orchestration

A workflow orchestrator MUST be used for orchestrating data fetching and processing workflows.

- Backfill workflows organized as numbered scripts (0_, 1_, 2_, etc.)
- Each workflow stage corresponds to a data pipeline stage
- Logging for consistent observability
- Workflow failures MUST be clearly reported with actionable context

**Rationale**: An orchestrator provides task tracking, retries, and observability needed for reliable data pipelines.

## Data Handling

### Credential Security

- Credentials MUST NOT be committed to version control
- Use `sensitive/` directory (gitignored) for credential files
- Credential loading MUST fail explicitly if files are missing or malformed

### Database Schema

- Alembic MUST manage all schema migrations
- Migrations MUST be reversible where possible
- Raw event tables preserve original API response structure
- Processed tables use appropriate SQL dialect types (timestamps with timezone, numeric for decimals)

### API Interaction

- Respect Tandem Source API rate limits
- Handle authentication token refresh automatically
- Log API errors with sufficient context for debugging
- Never expose tokens or credentials in logs

## Development Workflow

### Code Organization

- Source code in `src/tandem_fetch/`
- Database models and operations in `db/` submodule
- Pump event parsing in `pump_events/` submodule
- Workflow orchestrator tasks in `tasks/` submodule
- Workflow orchestrator workflows in `workflows/` submodule

### Dependency Management

- Use `uv` for Python dependency management
- Pin major versions in `pyproject.toml`
- Development dependencies in separate dependency group

### Testing Philosophy

- Focus on integration tests for data pipeline correctness
- Unit tests for complex transformation logic
- Test against representative sample data, not production credentials

## Governance

This constitution defines the guiding principles for tandem-fetch development. All code changes MUST align with these principles.

### Amendment Process

1. Propose changes via discussion or PR
2. Document rationale for principle changes
3. Update version following semantic versioning:
   - MAJOR: Principle removal or incompatible redefinition
   - MINOR: New principle or significant expansion
   - PATCH: Clarifications and minor wording changes
4. Update LAST_AMENDED_DATE on any change

### Compliance

- Code reviews SHOULD verify alignment with constitution principles
- When principles conflict with practical needs, document the exception and rationale
- Prefer constitution amendments over repeated exceptions

**Version**: 1.0.0 | **Ratified**: 2026-01-31 | **Last Amended**: 2026-01-31
