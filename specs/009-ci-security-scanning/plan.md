# Implementation Plan: CI Security Scanning

**Branch**: `009-ci-security-scanning` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-ci-security-scanning/spec.md`

## Summary

Add security scanning to the existing CI pipeline and local CI script: Bandit for static analysis of Python source code, and pip-audit for dependency vulnerability scanning. Both tools are added as dev dependencies, configured via `pyproject.toml`, and integrated into both GitHub Actions and the local CI script.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Bandit 1.x (new), pip-audit 2.x (new) — both dev-only
**Storage**: N/A (configuration files only)
**Testing**: Manual verification — push a branch with a known insecure pattern and confirm CI catches it
**Target Platform**: GitHub Actions (ubuntu-latest) + macOS (local)
**Project Type**: Single project — CI/config changes only, no new source code
**Performance Goals**: Security scans complete within 30 seconds in CI
**Constraints**: Must not break existing CI; must be runnable locally with the same results
**Scale/Scope**: 3 files modified (pyproject.toml, ci.yml, run-ci-locally.sh), 0 new source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | No data changes. Security scanning is a CI-only concern. |
| II. Single-User Simplicity | PASS | Simple CLI tools configured in pyproject.toml. No complex infrastructure. |
| III. Incremental & Resumable | N/A | Not a data fetching feature. |
| IV. Clear Data Pipeline | N/A | Not a data pipeline feature. |
| V. Workflow Orchestration | N/A | Not a workflow feature. |
| Credential Security | PASS | No credential changes. Bandit will help catch hardcoded secrets. |
| Code Organization | PASS | Configuration in existing files (pyproject.toml, ci.yml). No new source code. |
| Dependency Management | PASS | New tools added to dev dependency group per constitution. Uses uv. |
| Testing Philosophy | PASS | Verified via CI pipeline execution rather than unit tests. |

**Result**: All applicable gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/009-ci-security-scanning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── ci.md            # CI pipeline contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
pyproject.toml                        # MODIFIED — add bandit, pip-audit to dev deps + [tool.bandit] config
.github/workflows/ci.yml             # MODIFIED — add bandit and pip-audit steps
.github/scripts/run-ci-locally.sh    # MODIFIED — add bandit and pip-audit commands
```

**Structure Decision**: No new source files. This feature only modifies existing configuration files to add security scanning steps. Bandit is configured via `[tool.bandit]` in pyproject.toml. pip-audit uses CLI flags only.
