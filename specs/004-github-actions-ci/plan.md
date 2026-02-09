# Implementation Plan: GitHub Actions Continuous Integration

**Branch**: `004-github-actions-ci` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-github-actions-ci/spec.md`

## Summary

Add automated continuous integration using GitHub Actions to run tests on every PR and push. The CI workflow will execute linting (ruff) and testing (pytest) with parallel execution, using uv for fast dependency management and caching. A local CI script will allow developers to validate changes before pushing.

**Technical Approach** (from research):
- Single-job GitHub Actions workflow targeting Python 3.12
- Official `astral-sh/setup-uv@v7` action with built-in caching
- Parallel test execution using existing pytest-xdist configuration
- Read-only GITHUB_TOKEN permissions for security
- Local execution script for pre-push validation

## Technical Context

**Language/Version**: Python 3.12 (existing project constraint)
**Primary Dependencies**:
- GitHub Actions (astral-sh/setup-uv@v7, actions/checkout@v4)
- uv (package manager, already in use)
- pytest with pytest-xdist (test execution, already configured)
- ruff (linting/formatting, already in use)

**Storage**: N/A (configuration files only, no persistent data)
**Testing**: pytest with parallel execution (`-n auto --dist loadfile`)
**Target Platform**: GitHub Actions runners (ubuntu-latest with Python 3.12)
**Project Type**: Single project (src/ directory structure)
**Performance Goals**:
- Complete CI run < 2 minutes (full test suite)
- Lint checks < 30 seconds
- Setup with cache < 1 minute

**Constraints**:
- Read-only GITHUB_TOKEN permissions (security hardening)
- Must replicate local environment (environment parity)
- No secrets required (tests use mocked APIs)

**Scale/Scope**:
- Single workflow file (.github/workflows/ci.yml)
- Single local script (.github/scripts/run-ci-locally.sh)
- 37 tests in current test suite (unit + integration)
- ~10 second test execution time currently

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Before Phase 0)

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| **I. Data Integrity First** | ✅ PASS | CI validates data pipeline correctness by running existing tests. Prevents broken code from being merged. |
| **II. Single-User Simplicity** | ✅ PASS | Simple single-job workflow. No multi-environment complexity. Local script for easy testing. |
| **III. Incremental & Resumable** | ✅ PASS | GitHub Actions automatically handles workflow retries and resumption. Not directly related to data fetching. |
| **IV. Clear Data Pipeline** | ✅ PASS | CI validates each stage of data pipeline (raw events → parsed → domain tables) by running tests. |
| **V. Workflow Orchestration** | ✅ PASS | CI ensures workflow orchestration code quality by testing Prefect workflows. |
| **Code Organization** | ✅ PASS | Follows convention: `.github/workflows/` for GitHub Actions, `.github/scripts/` for local scripts. |
| **Dependency Management** | ✅ PASS | Uses existing uv dependency management. No new dependencies in production code. |
| **Testing Philosophy** | ✅ PASS | Runs existing integration and unit tests. Doesn't change testing approach. |

**Initial Gate Result**: ✅ **PASS** - No constitution violations. This feature enhances existing quality gates.

### Post-Design Check (After Phase 1)

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| **I. Data Integrity First** | ✅ PASS | research.md confirms CI will catch data integrity issues early by running comprehensive test suite on every PR. |
| **II. Single-User Simplicity** | ✅ PASS | Design chose simplest approach: single workflow job, no matrix testing, Python 3.12 only. Branch protection optional (can be added but not required). |
| **III. Incremental & Resumable** | ✅ PASS | CI validates incremental data fetching logic through existing tests. |
| **IV. Clear Data Pipeline** | ✅ PASS | CI ensures pipeline stages remain independently runnable and idempotent by testing them. |
| **V. Workflow Orchestration** | ✅ PASS | CI validates Prefect workflow definitions through integration tests. |
| **Code Organization** | ✅ PASS | Proposed structure follows GitHub conventions. No changes to src/ organization. |
| **Dependency Management** | ✅ PASS | Uses uv for CI dependency installation (--locked flag ensures reproducibility). |
| **Testing Philosophy** | ✅ PASS | Executes all existing tests (unit + integration). No test philosophy changes. |

**Post-Design Gate Result**: ✅ **PASS** - Design maintains constitution compliance. No complexity violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-github-actions-ci/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output - GitHub Actions best practices research
├── data-model.md        # Phase 1 output - Configuration entities and relationships
├── quickstart.md        # Phase 1 output - Verification and usage guide
├── contracts/           # Phase 1 output
│   └── ci-workflow-schema.yml  # Workflow structure contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

```text
.github/
├── workflows/
│   └── ci.yml           # Main CI workflow definition (NEW)
└── scripts/
    └── run-ci-locally.sh  # Local CI validation script (NEW)

# Existing structure (no changes)
src/
├── tandem_fetch/
│   ├── db/              # Database models
│   ├── pump_events/     # Event parsing
│   ├── tasks/           # Prefect tasks
│   └── workflows/       # Prefect workflows

tests/
├── integration/         # Integration tests (existing)
└── unit/                # Unit tests (existing)

pyproject.toml           # Already has pytest config (no changes needed)
uv.lock                  # Dependency lock file (existing, used by CI)
```

**Structure Decision**: Single project with existing src/ and tests/ directories. CI additions go in `.github/` directory following GitHub Actions conventions. No changes to existing source structure.

## Implementation Phases

### Phase 0: Research ✅ COMPLETE

**Status**: Completed by research agent

**Deliverable**: `research.md` with decisions on:
- ✅ GitHub Actions setup approach (single-job, Python 3.12 only, astral-sh/setup-uv)
- ✅ Dependency caching strategy (built-in caching with uv.lock, cache pruning)
- ✅ Parallel test execution (use existing pytest-xdist config)
- ✅ Local CI validation (act tool with limitations documented)
- ✅ Security hardening (read-only permissions, pinned actions)
- ✅ Optimization patterns (fail-fast linting, minimal job separation)

**Key Findings**:
- Use official `astral-sh/setup-uv@v7` action (faster than pip)
- Built-in caching keyed on uv.lock (no manual cache management)
- Single job for simplicity (lint + test together)
- Local script primary validation, act optional

### Phase 1: Design ✅ COMPLETE

**Status**: Completed

**Deliverables**:
- ✅ `data-model.md`: Configuration entities (workflow file, local script, branch protection)
- ✅ `contracts/ci-workflow-schema.yml`: Workflow structure contract
- ✅ `quickstart.md`: Verification steps and usage patterns
- ✅ Updated `CLAUDE.md`: Added CI technologies to agent context

**Design Decisions**:
1. **Workflow Structure**: Single `ci.yml` file with one job
2. **Steps**: checkout → setup uv → install deps → lint → test → prune cache
3. **Triggers**: push to main, pull_request to main
4. **Local Script**: Bash script in `.github/scripts/` replicating workflow steps
5. **Branch Protection**: Documented but not enforced (optional for single-user)

### Phase 2: Tasks Generation (NEXT STEP)

**Status**: Not started (requires `/speckit.tasks` command)

**Expected Output**: `tasks.md` with implementation tasks organized by user story:
- P1: Automatic Test Execution (CI workflow + branch protection)
- P2: Local CI Validation (local script)
- P3: Optimized Test Execution (caching, parallel execution)

**Task Categories**:
1. Create GitHub Actions workflow file
2. Configure workflow triggers and permissions
3. Implement workflow steps (setup, lint, test, cache)
4. Create local CI validation script
5. Document usage in README
6. Optionally configure branch protection rules
7. Verify CI works end-to-end

## Architecture Decisions

### 1. Single Job vs Multiple Jobs

**Decision**: Single consolidated job for lint + test

**Rationale**:
- Faster for small projects (avoids repeated dependency installation)
- Simpler to understand and maintain
- Test suite completes in ~10 seconds, no benefit from job parallelization
- Fail-fast linting still works (ruff runs before pytest)

**Alternative Rejected**: Separate jobs for lint and test (adds overhead)

### 2. Python Version Strategy

**Decision**: Target Python 3.12 only (no matrix testing)

**Rationale**:
- Project explicitly constrains to Python 3.12 per CLAUDE.md
- Single-user project (no library distribution concerns)
- Reduces CI complexity and cost
- Faster feedback (one job instead of matrix)

**Alternative Rejected**: Matrix testing across Python 3.10, 3.11, 3.12, 3.13 (unnecessary complexity)

### 3. Caching Strategy

**Decision**: Use built-in `setup-uv` caching with `uv cache prune --ci`

**Rationale**:
- Automatic cache key generation based on uv.lock hash
- Weekly cache rotation via calendar week number
- CI-optimized pruning reduces storage costs
- Simpler than manual cache management

**Alternative Rejected**: Manual actions/cache with custom keys (more verbose, harder to maintain)

### 4. Local CI Validation

**Decision**: Bash script replicating workflow steps, with optional act support

**Rationale**:
- Pre-commit hooks already provide primary quality gates
- Local script ensures exact command parity with CI
- act has limitations but useful for workflow syntax validation
- Simple bash script easier than Docker-based custom solution

**Alternative Rejected**: Require act for all local validation (too many limitations)

### 5. Security Posture

**Decision**: Read-only GITHUB_TOKEN, pinned action versions, branch protection

**Rationale**:
- Principle of least privilege (read-only sufficient for tests)
- Pinned versions prevent supply chain attacks
- Branch protection optional but recommended
- No secrets needed (tests use mocked APIs)

**Alternative Rejected**: Full write permissions (violates security best practices)

## Technology Integration Points

### With Existing Tools

| Tool | Integration | Notes |
|------|-------------|-------|
| **uv** | Primary package manager in CI | Uses `uv sync --locked` for reproducibility |
| **pytest** | Test execution | Uses existing config from pyproject.toml |
| **pytest-xdist** | Parallel testing | Already configured with `-n auto` |
| **ruff** | Linting/formatting | Runs `ruff check` and `ruff format --check` |
| **pre-commit** | Local quality gates | Complements CI (fast local checks) |
| **Prefect** | Workflow testing | CI validates Prefect workflows via tests |
| **DuckDB** | Test databases | In-memory databases work in CI (no setup needed) |

### New Dependencies

**Production**: None (CI is infrastructure, not production code)

**Development**: None (act is optional, not required)

**CI-Only**:
- `actions/checkout@v4` (clone repository)
- `astral-sh/setup-uv@v7` (install uv with caching)

## File Changes Summary

### New Files

1. **`.github/workflows/ci.yml`** (~50 lines)
   - Purpose: GitHub Actions workflow definition
   - Triggers: push (main), pull_request
   - Jobs: Single `ci` job with 8 steps

2. **`.github/scripts/run-ci-locally.sh`** (~30 lines)
   - Purpose: Local CI validation script
   - Usage: `bash .github/scripts/run-ci-locally.sh`
   - Replicates: CI workflow steps exactly

3. **Documentation updates to README.md** (~20 lines added)
   - Section: Testing / Continuous Integration
   - Content: How to run CI locally, how CI works
   - Badges: Optional CI status badge

### Modified Files

**`CLAUDE.md`** (updated by agent script):
- Added: "GitHub Actions (astral-sh/setup-uv, actions/checkout)" to technologies
- Section: Active Technologies

**README.md** (new section):
- Added: Continuous Integration section
- Content: CI overview, local validation, troubleshooting

### No Changes Required

- **`pyproject.toml`**: pytest config already complete
- **`uv.lock`**: Already exists and committed
- **`tests/**`**: No test changes needed
- **`src/**`**: No source code changes needed

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CI runs slow (>5 min) | Low | Medium | Use caching, parallel execution (already configured), optimize if needed |
| Environment parity issues (local ≠ CI) | Low | Medium | Local script uses same commands, act available for validation |
| Flaky tests break CI | Low | High | Current tests are stable (in-memory DB, mocked APIs), no known flakes |
| GitHub Actions costs exceed budget | Very Low | Low | Public repos get unlimited Actions minutes, caching reduces usage |
| act limitations prevent local validation | Medium | Low | Pre-commit hooks provide primary quality gates, act is optional |
| Branch protection too restrictive | Low | Low | Single-user can bypass if needed, protection is recommended not required |

## Performance Expectations

### CI Execution Times

| Scenario | Target | Rationale |
|----------|--------|-----------|
| **Cold start** (no cache) | < 3 minutes | Fresh dependency install + lint + tests |
| **Warm start** (cache hit) | < 2 minutes | Cached deps restore + lint + tests |
| **Lint only** | < 30 seconds | Ruff is fast, small codebase |
| **Test suite** | < 2 minutes | Current: ~10s local, expect <2min with CI overhead |
| **Setup** | < 1 minute | uv is very fast, especially with cache |

### Cache Hit Rates

- **Expected**: >90% cache hits after initial runs
- **Cache invalidation**: Weekly rotation + uv.lock changes
- **Storage**: ~50-200 MB cached dependencies

### Parallel Execution

- **Workers**: Auto-detected (typically 2-4 on GitHub runners)
- **Speedup**: 2-3x typical (from ~30s sequential to ~10s parallel for current suite)
- **Overhead**: Worker spawning adds ~1-2 seconds

## Success Metrics

From spec.md Success Criteria:

1. **SC-001**: Complete test suite executes within 2 minutes ✓
   - Measurement: GitHub Actions workflow duration
   - Current baseline: ~10 seconds for 37 tests

2. **SC-002**: Developers receive feedback within 10 minutes ✓
   - Measurement: Time from push to status check complete
   - Target: <10 minutes includes queue time

3. **SC-003**: 100% of PRs show clear pass/fail status ✓
   - Measurement: GitHub status checks visible on all PRs
   - Implementation: Required status check "ci"

4. **SC-004**: Local validation produces identical results (95% parity) ✓
   - Measurement: Compare local script vs CI results
   - Known differences: act limitations documented

5. **SC-005**: CI setup time under 2 minutes via caching ✓
   - Measurement: Time for checkout + setup + install steps
   - Target: <2 minutes with cache, <3 minutes cold start

6. **SC-006**: Zero broken builds merged to main ✓
   - Measurement: main branch test failures after merge
   - Implementation: Branch protection (optional but recommended)

7. **SC-007**: Developers identify failing test within 3 minutes ✓
   - Measurement: Time from failure notification to root cause
   - Implementation: Clear pytest output in logs

8. **SC-008**: CI costs under $50/month ✓
   - Measurement: GitHub Actions usage costs
   - Expected: $0 for public repos (unlimited minutes)

## Next Steps

1. **Run `/speckit.tasks`** to generate implementation tasks
2. **Review tasks.md** for task breakdown by user story
3. **Execute tasks** to implement CI workflow
4. **Verify** using quickstart.md verification steps
5. **Monitor** CI performance and optimize if needed

## Appendix: Research Sources

See `research.md` for detailed sources including:
- GitHub Actions Python/uv integration guides
- act local execution documentation
- Security best practices for GitHub Actions
- Caching strategies and optimization patterns
- Parallel testing with pytest-xdist
