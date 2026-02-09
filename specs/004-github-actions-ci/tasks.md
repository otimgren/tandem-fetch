# Tasks: GitHub Actions Continuous Integration

**Input**: Design documents from `/specs/004-github-actions-ci/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ci-workflow-schema.yml

**Tests**: No test tasks included - this feature adds CI infrastructure to run existing tests

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `.github/` at repository root
- CI workflow: `.github/workflows/ci.yml`
- Local script: `.github/scripts/run-ci-locally.sh`
- Documentation: README.md at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure for GitHub Actions configuration

- [x] T001 Create .github/workflows directory
- [x] T002 Create .github/scripts directory

**Checkpoint**: Directory structure ready for CI files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational tasks needed - existing test suite and project structure are already in place

**⚠️ NOTE**: This feature adds CI infrastructure, not application code. All prerequisites (tests, uv config, pytest config) already exist.

**Checkpoint**: Foundation verified - all user stories can proceed

---

## Phase 3: User Story 1 - Automatic Test Execution on PR/Push (Priority: P1) 🎯 MVP

**Goal**: Automated tests run on every PR and push to GitHub, with results visible in PR status checks

**Independent Test**: Create a test branch, push a commit, verify tests execute automatically and status check appears in PR

### Implementation for User Story 1

- [x] T003 [US1] Create GitHub Actions workflow file .github/workflows/ci.yml with workflow name "CI"
- [x] T004 [US1] Configure workflow triggers for push to main and pull_request events in .github/workflows/ci.yml
- [x] T005 [US1] Set read-only permissions (contents: read) in .github/workflows/ci.yml
- [x] T006 [US1] Add checkout step using actions/checkout@v4 in .github/workflows/ci.yml
- [x] T007 [US1] Add uv setup step using astral-sh/setup-uv@v7 with caching enabled in .github/workflows/ci.yml
- [x] T008 [US1] Add Python 3.12 installation step using "uv python install 3.12" in .github/workflows/ci.yml
- [x] T009 [US1] Add dependency installation step using "uv sync --locked --all-extras --group dev --group test" in .github/workflows/ci.yml
- [x] T010 [US1] Add ruff linting step using "uv run ruff check ." in .github/workflows/ci.yml
- [x] T011 [US1] Add ruff format check step using "uv run ruff format --check ." in .github/workflows/ci.yml
- [x] T012 [US1] Add pytest test execution step using "uv run pytest" in .github/workflows/ci.yml
- [x] T013 [US1] Add cache pruning step using "uv cache prune --ci" with if: always() in .github/workflows/ci.yml
- [x] T014 [US1] Verify workflow file syntax is valid YAML
- [x] T015 [US1] Commit and push workflow file to trigger first CI run
- [x] T016 [US1] Verify CI runs successfully on the push and status check appears

**Checkpoint**: At this point, CI automatically runs on every push and PR. Core CI functionality is complete and testable.

---

## Phase 4: User Story 2 - Local CI Validation (Priority: P2)

**Goal**: Developers can run the exact same CI checks locally before pushing to GitHub

**Independent Test**: Run the local script, verify it executes the same steps as GitHub Actions and produces identical results

### Implementation for User Story 2

- [x] T017 [US2] Create local CI script .github/scripts/run-ci-locally.sh with bash shebang
- [x] T018 [US2] Add "set -e" to exit on first error in .github/scripts/run-ci-locally.sh
- [x] T019 [US2] Add echo statement for "Running local CI validation..." in .github/scripts/run-ci-locally.sh
- [x] T020 [US2] Add "uv sync --locked --all-extras --group dev --group test" command in .github/scripts/run-ci-locally.sh
- [x] T021 [US2] Add "uv run ruff check ." command in .github/scripts/run-ci-locally.sh
- [x] T022 [US2] Add "uv run ruff format --check ." command in .github/scripts/run-ci-locally.sh
- [x] T023 [US2] Add "uv run pytest" command in .github/scripts/run-ci-locally.sh
- [x] T024 [US2] Add success message "All checks passed!" at end of .github/scripts/run-ci-locally.sh
- [x] T025 [US2] Make script executable with chmod +x .github/scripts/run-ci-locally.sh
- [x] T026 [US2] Test local script runs successfully and matches CI behavior
- [x] T027 [US2] Add README.md section documenting how to run CI locally using the script

**Checkpoint**: At this point, developers can validate changes locally before pushing. User Story 2 is complete and testable independently.

---

## Phase 5: User Story 3 - Optimized Test Execution (Priority: P3)

**Goal**: CI runs efficiently using caching and parallel test execution

**Independent Test**: Compare CI execution time with and without caching, verify parallel execution works

### Implementation for User Story 3

- [x] T028 [US3] Verify cache-dependency-glob is set to "uv.lock" in setup-uv step in .github/workflows/ci.yml
- [x] T029 [US3] Verify enable-cache: true is set in setup-uv step in .github/workflows/ci.yml
- [x] T030 [US3] Verify "uv cache prune --ci" runs with if: always() to clean cache in .github/workflows/ci.yml
- [x] T031 [US3] Verify pytest uses "-n auto" from pyproject.toml for parallel execution
- [x] T032 [US3] Test cold start CI run (no cache) and record duration
- [x] T033 [US3] Test warm start CI run (with cache) and verify cache hit in logs
- [x] T034 [US3] Verify warm start is faster than cold start (target: <2 minutes vs <3 minutes)
- [x] T035 [US3] Add README.md section documenting caching behavior and expected performance

**Checkpoint**: All optimizations are in place and verified. CI runs efficiently with caching and parallel tests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, optional branch protection, and final validation

- [x] T036 [P] Add CI status badge to README.md (![CI](https://github.com/USER/tandem-fetch/workflows/CI/badge.svg))
- [x] T037 [P] Document CI workflow in README.md Continuous Integration section
- [x] T038 [P] Document troubleshooting common CI issues in README.md
- [x] T039 Add optional documentation for setting up branch protection rules on main branch in README.md
- [x] T040 Run through quickstart.md verification steps to validate all acceptance criteria
- [x] T041 Verify all success criteria from spec.md are met (SC-001 through SC-008)

**Checkpoint**: Documentation complete, CI fully operational and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: No tasks - existing infrastructure sufficient
- **User Stories (Phase 3+)**: Can start immediately (no foundational blocking)
  - User Story 1 must complete before User Story 2 (local script replicates workflow)
  - User Story 3 depends on User Story 1 (optimizes existing workflow)
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies - can start after Setup (Phase 1)
- **User Story 2 (P2)**: Depends on User Story 1 completing (replicates workflow steps from US1)
- **User Story 3 (P3)**: Depends on User Story 1 completing (verifies optimizations in US1 workflow)

### Within Each User Story

**User Story 1** (T003-T016):
- T003-T013: Sequential workflow file construction (each step builds on previous)
- T014: Syntax validation after file complete
- T015-T016: Testing after workflow complete

**User Story 2** (T017-T027):
- T017-T024: Sequential script construction (each command builds on previous)
- T025-T027: Testing and documentation after script complete

**User Story 3** (T028-T035):
- T028-T031: Verification tasks (can run in parallel conceptually, but quick checks)
- T032-T034: Sequential performance testing (need baseline before comparison)
- T035: Documentation after validation

### Parallel Opportunities

- Phase 1 tasks (T001-T002) can run in parallel (different directories)
- Polish tasks (T036-T038) can run in parallel (different documentation sections)
- User Stories 2 and 3 could theoretically run in parallel, but US2 makes more sense to complete before US3 for validation purposes

**Note**: Given this is CI infrastructure (not application code), most tasks are sequential within each story. Parallelization opportunities are limited but identified with [P] markers.

---

## Parallel Example: Setup Phase

```bash
# Launch both directory creation tasks together:
Task: "Create .github/workflows directory"
Task: "Create .github/scripts directory"
```

## Parallel Example: Polish Phase

```bash
# Launch documentation tasks together:
Task: "Add CI status badge to README.md"
Task: "Document CI workflow in README.md Continuous Integration section"
Task: "Document troubleshooting common CI issues in README.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 3: User Story 1 (T003-T016)
3. **STOP and VALIDATE**: Create test PR, verify CI runs, check status checks
4. Deploy/use if ready

**Result**: Basic CI is functional - tests run automatically on every push/PR

### Incremental Delivery

1. Complete Setup → Directory structure ready
2. Add User Story 1 → Test with real PR → **CI is live! (MVP)**
3. Add User Story 2 → Test local script → Local validation available
4. Add User Story 3 → Measure performance → Optimized CI
5. Add Polish → Full documentation and optional branch protection

Each story adds value without breaking previous functionality.

### Parallel Team Strategy

Not applicable - single developer should complete sequentially. If multiple developers:

1. Developer A: User Story 1 (T001-T016)
2. After US1 complete:
   - Developer A: User Story 2 (T017-T027)
   - Developer B: Could prepare User Story 3 verification scripts
3. User Story 3 validates US1's optimizations

---

## Success Criteria Validation

Each user story maps to success criteria from spec.md:

**User Story 1** delivers:
- SC-001: Complete test suite executes within 2 minutes ✓
- SC-002: Developers receive feedback within 10 minutes ✓
- SC-003: 100% of PRs show clear pass/fail status ✓
- SC-005: CI setup time under 2 minutes via caching ✓
- SC-006: Zero broken builds merged to main ✓
- SC-007: Developers can identify failing test within 3 minutes ✓

**User Story 2** delivers:
- SC-004: Local validation produces identical results (95% parity) ✓

**User Story 3** delivers:
- SC-001: Verification that parallel execution meets time target ✓
- SC-005: Verification that caching meets time target ✓
- SC-008: CI costs remain under $50/month (free for public repos) ✓

---

## Notes

- [P] tasks = different files, no dependencies within the phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after completing each user story phase
- Stop at any checkpoint to validate story independently
- Tests already exist (37 tests) - this feature adds CI to run them
- No new application code - only CI configuration files
- Validation happens by running actual CI and observing results

---

## Quick Reference

- **Total Tasks**: 41
- **Setup Tasks**: 2 (T001-T002)
- **User Story 1 (P1)**: 14 tasks (T003-T016) - Core CI workflow
- **User Story 2 (P2)**: 11 tasks (T017-T027) - Local validation script
- **User Story 3 (P3)**: 8 tasks (T028-T035) - Performance optimization
- **Polish**: 6 tasks (T036-T041) - Documentation and validation

**MVP Scope**: Setup + User Story 1 = 16 tasks
**Full Feature**: All 41 tasks
