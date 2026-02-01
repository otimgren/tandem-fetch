# Tasks: Pre-Commit Hooks for Code Quality and Security

**Input**: Design documents from `/specs/002-precommit-hooks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, contracts/

**Tests**: No test tasks included (not explicitly requested in specification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: Repository root at `/Users/oskari/projects/tandem-fetch/`
- Configuration files at repository root
- No new source directories needed (developer tooling only)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install prek and create basic directory structure for validation

- [x] T001 Add prek to dev dependencies in pyproject.toml with `uv add --dev prek`
- [x] T002 Verify prek installation by running `prek --version`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook configuration that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Base Configuration Files

- [x] T003 Create `.pre-commit-config.yaml` at repository root with empty repos list
- [x] T004 Create `.gitleaks.toml` at repository root with base configuration
- [x] T005 Add `[tool.ruff]` section to pyproject.toml with line-length=100 and target-version="py312"
- [x] T006 Install git hooks with `prek install` to create .git/hooks/pre-commit

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Automatic Code Formatting (Priority: P1) 🎯 MVP

**Goal**: Enable automatic Python code formatting with ruff before each commit

**Independent Test**: Make a code change with inconsistent formatting (inconsistent quotes, missing newlines), attempt to commit, and verify that the hook auto-formats the code and requires re-staging.

### Implementation for User Story 1

- [x] T007 [US1] Add ruff formatter configuration to `[tool.ruff.format]` section in pyproject.toml (quote-style="double", indent-style="space")
- [x] T008 [US1] Add ruff linter configuration to `[tool.ruff.lint]` section in pyproject.toml with extend-select=["I"] for import sorting
- [x] T009 [US1] Add ruff-pre-commit repository to .pre-commit-config.yaml with rev v0.14.14
- [x] T010 [US1] Add ruff hook (linter) to .pre-commit-config.yaml with args: [--fix, --exit-non-zero-on-fix]
- [x] T011 [US1] Add ruff-format hook (formatter) to .pre-commit-config.yaml after ruff hook
- [x] T012 [US1] Run `prek run ruff-format --all-files` to format entire codebase
- [x] T013 [US1] Commit formatted files with message "Apply ruff formatting to codebase"
- [x] T014 [US1] Validate SC-001: Run `ruff format --check` to verify all files are consistently formatted
- [x] T015 [US1] Validate SC-008: Create test file with unsorted imports, attempt commit, verify auto-fix

**Checkpoint**: User Story 1 complete - automatic code formatting working

---

## Phase 4: User Story 2 - Secret Detection (Priority: P2)

**Goal**: Prevent commits containing API keys, passwords, tokens, or PII

**Independent Test**: Attempt to commit a file containing a fake API key or password string, and verify the hook blocks the commit with a clear error message.

### Implementation for User Story 2

- [x] T016 [US2] Configure `.gitleaks.toml` with [extend] section and useDefault=true
- [x] T017 [US2] Add [allowlist] section to .gitleaks.toml with paths for test directories: '''.*/tests/fixtures/.*'''
- [x] T018 [US2] Add gitleaks repository to .pre-commit-config.yaml with rev v8.24.3
- [x] T019 [US2] Add gitleaks hook to .pre-commit-config.yaml
- [x] T020 [US2] Run `prek run gitleaks --all-files` to scan entire codebase for existing secrets
- [x] T021 [US2] If secrets found in T020, add to .gitleaksignore or fix them before proceeding
- [x] T022 [US2] Validate SC-002: Verify no secrets exist with `git log -p | gitleaks detect --no-git`
- [x] T023 [US2] Validate SC-004: Create test file with fake API key, attempt commit, verify clear error message
- [x] T024 [US2] Validate SC-005: Test false positive handling by adding allowlist pattern to .gitleaks.toml
- [x] T025 [US2] Validate SC-006: Attempt to commit file in sensitive/ directory, verify blocked

**Checkpoint**: User Story 2 complete - secret detection working

---

## Phase 5: User Story 3 - Additional Code Quality Checks (Priority: P3)

**Goal**: Run additional code quality checks (import sorting, whitespace removal, line ending normalization)

**Independent Test**: Commit a file with unsorted imports or trailing whitespace, and verify the hooks fix or flag these issues.

### Implementation for User Story 3

- [x] T026 [P] [US3] Add builtin repository to .pre-commit-config.yaml with repo: builtin
- [x] T027 [P] [US3] Add trailing-whitespace hook to .pre-commit-config.yaml with args: ['--markdown-linebreak-ext=md']
- [x] T028 [P] [US3] Add end-of-file-fixer hook to .pre-commit-config.yaml
- [x] T029 [P] [US3] Add mixed-line-ending hook to .pre-commit-config.yaml with args: ['--fix=lf']
- [x] T030 [P] [US3] Add check-yaml hook to .pre-commit-config.yaml
- [x] T031 [P] [US3] Add check-toml hook to .pre-commit-config.yaml
- [x] T032 [P] [US3] Add check-json hook to .pre-commit-config.yaml
- [x] T033 [P] [US3] Add check-added-large-files hook to .pre-commit-config.yaml with args: ['--maxkb=1000']
- [x] T034 [P] [US3] Add check-case-conflict hook to .pre-commit-config.yaml
- [x] T035 [P] [US3] Add check-merge-conflict hook to .pre-commit-config.yaml
- [x] T036 [US3] Run `prek run --all-files` to apply all builtin hooks to entire codebase
- [x] T037 [US3] Commit any auto-fixed files with message "Apply code quality fixes (whitespace, line endings)"
- [x] T038 [US3] Validate SC-007: Create malformed TOML file in tests/, attempt commit, verify blocked
- [x] T039 [US3] Validate acceptance scenario 1: Create file with unsorted imports, verify auto-sort
- [x] T040 [US3] Validate acceptance scenario 2: Create file with trailing whitespace, verify removal
- [x] T041 [US3] Validate acceptance scenario 3: Create file with CRLF line endings, verify normalization to LF

**Checkpoint**: User Story 3 complete - all code quality checks working

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final checks

- [x] T042 Update README.md with "Pre-Commit Hooks" section linking to quickstart guide
- [x] T043 Add setup instructions to README.md: "Run `uv tool install prek` and `prek install`"
- [x] T044 Copy specs/002-precommit-hooks/quickstart.md to docs/pre-commit-hooks.md (create docs/ if needed)
- [x] T045 Validate SC-003: Measure hook execution time with `time git commit` on small change, verify <5 seconds
- [x] T046 Validate SC-004: Follow README setup instructions on clean environment, verify one-command setup
- [x] T047 Run full commit workflow test: modify file, stage, commit, verify all hooks run successfully
- [x] T048 Document bypass mechanism in README.md: "Use `SKIP=hook-id git commit` for exceptional cases"
- [x] T049 Add `.gitleaksignore` to .gitignore (file may be created during usage but should be tracked)
- [x] T050 Verify all configuration files are committed: .pre-commit-config.yaml, .gitleaks.toml, updated pyproject.toml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T002) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T003-T006) - Can start after foundational complete
- **User Story 2 (Phase 4)**: Depends on Foundational (T003-T006) - Can start after foundational complete, independent of US1
- **User Story 3 (Phase 5)**: Depends on Foundational (T003-T006) - Can start after foundational complete, independent of US1 and US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - can implement after foundational
- **User Story 2 (P2)**: Independent of US1 - can implement in parallel
- **User Story 3 (P3)**: Independent of US1 and US2 - can implement in parallel

### Within Each Phase

- **Phase 1**: T001 must complete before T002 (need prek installed to check version)
- **Phase 2**: T003-T005 can run in parallel [P], T006 depends on T003 (needs config file to install hooks)
- **User Story 1**: T007-T011 are configuration tasks that can run in parallel [P], T012-T015 are sequential validation
- **User Story 2**: T016-T019 are configuration tasks that can run in parallel [P], T020-T025 are sequential validation
- **User Story 3**: T026-T035 are all configuration tasks that can run in parallel [P], T036-T041 are sequential validation

### Parallel Opportunities

**Phase 2 - Foundational**:
```bash
# Launch config file creation in parallel:
Task: "Create .pre-commit-config.yaml"
Task: "Create .gitleaks.toml"
Task: "Add [tool.ruff] section to pyproject.toml"
```

**User Story 1 - Configuration**:
```bash
# Launch all ruff configuration in parallel:
Task: "Add ruff formatter configuration to pyproject.toml"
Task: "Add ruff linter configuration to pyproject.toml"
Task: "Add ruff-pre-commit repository to .pre-commit-config.yaml"
Task: "Add ruff hook to .pre-commit-config.yaml"
Task: "Add ruff-format hook to .pre-commit-config.yaml"
```

**User Story 2 - Configuration**:
```bash
# Launch gitleaks configuration in parallel:
Task: "Configure .gitleaks.toml with [extend] section"
Task: "Add [allowlist] section to .gitleaks.toml"
Task: "Add gitleaks repository to .pre-commit-config.yaml"
Task: "Add gitleaks hook to .pre-commit-config.yaml"
```

**User Story 3 - All Builtin Hooks**:
```bash
# Launch all builtin hook configuration in parallel:
Task: "Add builtin repository to .pre-commit-config.yaml"
Task: "Add trailing-whitespace hook"
Task: "Add end-of-file-fixer hook"
Task: "Add mixed-line-ending hook"
Task: "Add check-yaml hook"
Task: "Add check-toml hook"
Task: "Add check-json hook"
Task: "Add check-added-large-files hook"
Task: "Add check-case-conflict hook"
Task: "Add check-merge-conflict hook"
```

**After Foundational Phase**:
```bash
# User stories can be implemented in parallel by different developers:
Developer A: User Story 1 (T007-T015)
Developer B: User Story 2 (T016-T025)
Developer C: User Story 3 (T026-T041)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002) - ~2 minutes
2. Complete Phase 2: Foundational (T003-T006) - ~5 minutes
3. Complete Phase 3: User Story 1 (T007-T015) - ~10 minutes
4. **STOP and VALIDATE**: Test formatting by committing poorly formatted code
5. System is usable at this point with automatic code formatting

**Total MVP time**: ~17 minutes to working code formatter

### Incremental Delivery

1. Complete Setup + Foundational → Hooks installed, ready for configuration
2. Add User Story 1 → Test formatting → **MVP complete!** (Code formatter working)
3. Add User Story 2 → Test secret detection → Security layer added
4. Add User Story 3 → Test quality checks → Full quality suite complete
5. Polish phase → Documentation and validation

### Single Developer Strategy

Execute phases sequentially:
1. Phase 1: Setup (~2 min)
2. Phase 2: Foundational (~5 min)
3. Phase 3: User Story 1 (~10 min)
4. Phase 4: User Story 2 (~15 min)
5. Phase 5: User Story 3 (~15 min)
6. Phase 6: Polish (~10 min)

**Total time**: ~60 minutes for complete implementation

### Parallel Team Strategy

With 3 developers after foundational phase:
1. Team completes Setup + Foundational together (~7 min)
2. Once Foundational is done:
   - Developer A: User Story 1 (~10 min)
   - Developer B: User Story 2 (~15 min)
   - Developer C: User Story 3 (~15 min)
3. All developers collaborate on Polish (~10 min)

**Total time**: ~32 minutes with parallel execution

---

## Notes

- [P] tasks = different files or independent configuration, no dependencies between them
- [Story] label maps task to specific user story for traceability
- Configuration tasks can be parallelized because they modify different sections/files
- Validation tasks must be sequential to verify each feature works
- All user stories are independently testable after foundational phase completes
- Hooks run in the order defined in .pre-commit-config.yaml:
  1. builtin hooks (fast validation)
  2. ruff (linting)
  3. ruff-format (formatting)
  4. gitleaks (security)
- Can bypass hooks with `SKIP=hook-id git commit` or `git commit --no-verify` for emergencies
- Expected hook execution time: <1 second typical, <2 seconds for large commits
- Success criteria are validated in-line with user story tasks (T014-T015, T022-T025, T038-T041)
