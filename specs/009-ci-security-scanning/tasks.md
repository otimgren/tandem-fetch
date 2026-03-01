# Tasks: CI Security Scanning

**Input**: Design documents from `/specs/009-ci-security-scanning/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, contracts/ci.md, quickstart.md

**Tests**: Not included — this feature is verified by running the CI pipeline, not by unit tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add security scanning tools as dev dependencies

- [x] T001 Add `bandit[toml]` and `pip-audit` to the dev dependency group in `pyproject.toml`
- [x] T002 Run `uv sync --all-groups` to install new dependencies

---

## Phase 2: User Story 1 - Detect Insecure Code Patterns in CI (Priority: P1) 🎯 MVP

**Goal**: Bandit scans Python source code for security issues on every push/PR, failing CI if issues are found.

**Independent Test**: Run `uv run bandit -r src/ -c pyproject.toml` locally and verify it passes. Then push to confirm CI runs the same check.

**Maps to**: FR-001, FR-003, FR-005, FR-006, FR-009

### Implementation

- [x] T003 [US1] Add `[tool.bandit]` configuration section to `pyproject.toml` with `exclude_dirs = [".venv", "build", "dist"]` and `skips = ["B101", "B608"]` per research.md decisions
- [x] T004 [US1] Add Bandit scan step to `.github/workflows/ci.yml` after dependency installation: `uv run bandit -r src/ -c pyproject.toml`
- [x] T005 [US1] Run `uv run bandit -r src/ -c pyproject.toml` locally to verify the scan passes on the current codebase. Fix any findings or add `# nosec` suppressions with justification.

**Checkpoint**: Bandit runs in CI and locally, scanning all source code for security issues

---

## Phase 3: User Story 2 - Detect Vulnerable Dependencies in CI (Priority: P1)

**Goal**: pip-audit checks all installed dependencies for known CVEs on every push/PR, failing CI if vulnerabilities are found.

**Independent Test**: Run `uv run pip-audit` locally and verify it passes. Then push to confirm CI runs the same check.

**Maps to**: FR-002, FR-004, FR-005, FR-009

### Implementation

- [x] T006 [US2] Add pip-audit scan step to `.github/workflows/ci.yml` after dependency installation: `uv run pip-audit`
- [x] T007 [US2] Run `uv run pip-audit` locally to verify all current dependencies are clean. If vulnerabilities are found, either upgrade the affected package or add `--ignore-vuln` flag with justification.

**Checkpoint**: pip-audit runs in CI and locally, checking all dependencies for known vulnerabilities

---

## Phase 4: User Story 3 - Run Security Scans Locally (Priority: P2)

**Goal**: The local CI script includes the same security scans so developers get identical results before pushing.

**Independent Test**: Run `.github/scripts/run-ci-locally.sh` and verify it includes both Bandit and pip-audit steps.

**Maps to**: FR-008

### Implementation

- [x] T008 [US3] Add Bandit and pip-audit commands to `.github/scripts/run-ci-locally.sh` after linting checks and before tests, matching the exact commands used in CI

**Checkpoint**: Local CI script produces the same security scan results as the GitHub Actions pipeline

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T009 Push branch and verify the full CI pipeline passes on GitHub Actions (all existing checks + new security scans)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on Phase 1 — needs bandit installed
- **US2 (Phase 3)**: Depends on Phase 1 — needs pip-audit installed. Can run in parallel with US1.
- **US3 (Phase 4)**: Depends on US1 and US2 — mirrors their CI commands in the local script
- **Polish (Phase 5)**: Depends on all user stories being complete

### Parallel Opportunities

- T003, T004, T005 (Bandit setup) and T006, T007 (pip-audit setup) operate on different tools and can be developed in parallel after Phase 1
- T004 and T006 both modify `ci.yml` but add independent steps — can be done together in a single edit

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: User Story 1 (T003-T005)
3. **STOP and VALIDATE**: Run Bandit locally and verify it works
4. This alone delivers code security scanning in CI

### Incremental Delivery

1. Setup → US1 → Validate (MVP — Bandit code scanning)
2. Add US2 → Validate (dependency vulnerability scanning)
3. Add US3 → Validate (local CI parity)
4. Polish → Push and verify full CI pipeline

---

## Notes

- This feature modifies 3 existing files and creates 0 new source files
- All 9 tasks are configuration/CI changes — no application code is written
- The primary risk is false positives from Bandit on existing code (T005 handles this)
- pip-audit may find existing dependency vulnerabilities that need upgrading (T007 handles this)
