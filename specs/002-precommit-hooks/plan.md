# Implementation Plan: Pre-Commit Hooks for Code Quality and Security

**Branch**: `002-precommit-hooks` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-precommit-hooks/spec.md`

## Summary

Add automated pre-commit hooks using prek (Rust-based pre-commit replacement) to enforce code quality and security standards. The implementation will automatically format Python code with ruff, detect secrets/PII, sort imports, remove trailing whitespace, and normalize line endings. Prek provides 4-10x faster performance than standard pre-commit while maintaining full compatibility with existing configurations.

## Technical Context

**Language/Version**: Python 3.12 (existing project constraint)
**Primary Dependencies**: prek (pre-commit hook manager), ruff (formatter/linter), gitleaks (secret detection)
**Storage**: N/A (configuration files only)
**Testing**: Manual testing of hook behavior (commit attempts with violations)
**Target Platform**: Developer workstations (macOS/Linux/Windows)
**Project Type**: Single project (existing tandem-fetch structure)
**Performance Goals**: Hook execution <5 seconds for typical commits, <1% false positive rate for secret detection
**Constraints**: Must work with existing Python 3.12 + uv + DuckDB stack, must not block legitimate commits
**Scale/Scope**: ~15-20 hooks covering formatting, linting, secret detection, file validation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Alignment with Constitution Principles

#### I. Data Integrity First ✅
- **Alignment**: Pre-commit hooks validate TOML/YAML configuration files to prevent malformed config that could break data fetching
- **No violations**: Hooks don't modify data pipeline logic

#### II. Single-User Simplicity ✅
- **Alignment**: One-command setup (`prek install`), no server/service required, configuration via simple YAML file
- **Enhancement**: Enforces simple patterns rather than allowing complex configurations

#### III. Incremental & Resumable ✅
- **Alignment**: Hooks run only on staged changes (incremental), don't affect existing pipeline resumability
- **No violations**: Formatting/linting doesn't impact workflow orchestration

#### IV. Clear Data Pipeline ✅
- **Alignment**: Hooks prevent committing broken code that could corrupt the 3-stage pipeline
- **Enhancement**: TOML validation ensures credentials/config remain valid

#### V. Workflow Orchestration ✅
- **Alignment**: No impact on Prefect workflows, hooks validate workflow files before commit
- **No violations**: Hooks are pre-commit only, don't interfere with runtime

### Credential Security (Constitution Data Handling) ✅
- **Enhancement**: Secret detection hooks provide defense-in-depth for credential security
- **Alignment**: Blocks commits to `sensitive/` directory, detects API keys/passwords in code

### Additional Checks

- **Single-User Focus**: No multi-user complexity added ✅
- **Simple Configuration**: Single `.pre-commit-config.yaml` file ✅
- **No Data Pipeline Changes**: Hooks are developer tooling only ✅

**GATE STATUS**: ✅ PASSED - No constitutional violations, multiple enhancements to existing principles

## Project Structure

### Documentation (this feature)

```text
specs/002-precommit-hooks/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - prek vs pre-commit analysis
├── quickstart.md        # Phase 1 output - setup guide for developers
└── contracts/           # Phase 1 output - .pre-commit-config.yaml schema
    └── pre-commit-config-schema.yaml
```

### Source Code (repository root)

**NOTE**: This feature adds configuration files to the existing project root, no new source directories needed.

```text
# Repository root (existing structure unchanged)
/Users/oskari/projects/tandem-fetch/
├── .pre-commit-config.yaml        # NEW: Prek hook configuration
├── .gitleaks.toml                  # NEW: Gitleaks secret detection config
├── pyproject.toml                  # UPDATED: Add prek to dev dependencies
├── src/tandem_fetch/               # UNCHANGED: Existing source
├── tests/                          # UNCHANGED: Existing tests
├── alembic/                        # UNCHANGED: Existing migrations
├── sensitive/                      # UNCHANGED: Gitignored credentials
└── data/                           # UNCHANGED: DuckDB database
```

**Structure Decision**: Pre-commit hooks are developer tooling and only require configuration files at repository root. No changes to existing `src/`, `tests/`, or data pipeline structure needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No complexity violations - this feature aligns with all constitution principles.

## Phase 0: Research & Technical Decisions

**Status**: ✅ COMPLETE

See [research.md](./research.md) for detailed findings.

### Key Research Outcomes

1. **Prek vs Pre-commit**: Selected prek (Rust-based reimplementation)
   - 4-10x faster hook execution
   - 2-10x faster installation
   - 50% less disk space
   - Fully compatible with pre-commit config format
   - Installed by default in major projects (CPython, FastAPI, Apache Airflow as of Jan 2026)

2. **Formatter Selection**: Ruff (single tool for linting + formatting + import sorting)
   - Replaces multiple tools (Black, isort, flake8)
   - Native pre-commit support via `ruff-pre-commit`
   - Configurable via existing `pyproject.toml`

3. **Secret Detection**: Gitleaks (industry standard as of 2026)
   - Better pattern coverage than detect-secrets
   - Lower false positive rate
   - Configurable via `.gitleaks.toml`
   - Active maintenance and updates

4. **Built-in Hooks**: Use prek's `repo: builtin` for simple checks
   - Trailing whitespace removal
   - EOF fixer
   - Line ending normalization
   - YAML/TOML/JSON validation
   - Zero dependencies, instant execution

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

### Design Artifacts

1. **quickstart.md**: Developer setup guide
2. **contracts/pre-commit-config-schema.yaml**: Schema for hook configuration

### Hook Execution Flow

```text
Developer runs: git commit
     ↓
Prek intercepts (via git hooks)
     ↓
┌─────────────────────────────────┐
│ Stage 1: Built-in Checks (fast)│
│ - YAML/TOML/JSON validation     │
│ - Large file detection          │
│ - Trailing whitespace removal   │
│ - EOF fixer                     │
│ - Line ending normalization     │
│ - Case conflict detection       │
│ - Merge conflict detection      │
└─────────────────────────────────┘
     ↓ (parallel execution)
┌─────────────────────────────────┐
│ Stage 2: Ruff Linting          │
│ - Run ruff check with --fix     │
│ - Fix import order              │
│ - Fix linting issues            │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ Stage 3: Ruff Formatting       │
│ - Format code with ruff format  │
│ - Ensure consistent style       │
└─────────────────────────────────┘
     ↓ (parallel with above)
┌─────────────────────────────────┐
│ Stage 4: Secret Detection      │
│ - Gitleaks scan for secrets     │
│ - Check for API keys            │
│ - Check for passwords           │
│ - Check for PII patterns        │
│ - Block commits to sensitive/   │
└─────────────────────────────────┘
     ↓
All checks pass?
  YES → Commit proceeds
  NO  → Commit blocked, show errors
     ↓
Auto-fixed files?
  YES → Re-stage required
  NO  → Continue
```

### Hook Priority Ordering

1. **Fast validation** (builtin hooks) - Run first, fail fast
2. **Linting** (ruff check) - Fix issues before formatting
3. **Formatting** (ruff format) - Last code transformation
4. **Security** (gitleaks) - Can run in parallel, independent of formatting

### Configuration Strategy

All hooks configured via `.pre-commit-config.yaml` (standard format):

```yaml
repos:
  - repo: builtin              # Fast, no dependencies
    hooks: [basic checks]

  - repo: astral-sh/ruff       # Code quality
    hooks: [ruff, ruff-format]

  - repo: gitleaks/gitleaks    # Security
    hooks: [gitleaks]
```

Ruff configured via existing `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
extend-select = ["I"]  # Enable isort rules
```

Gitleaks configured via `.gitleaks.toml`:

```toml
[extend]
useDefault = true  # Use built-in secret patterns

[allowlist]
paths = [
  '''.*/tests/fixtures/.*''',  # Exclude test data
]
```

### False Positive Handling

**Strategy**: Progressive override mechanisms

1. **File-level exclusion**: `.gitleaks.toml` allowlist for test files
2. **Pattern-level exclusion**: `.gitleaksignore` for known false positives
3. **Commit-level bypass**: `SKIP=gitleaks git commit -m "..."` for exceptional cases

**Expected false positive rate**: <1% based on gitleaks benchmarks

### Installation Requirements

**For developers**:
1. One-time: `uv tool install prek` or `uv add --dev prek`
2. Per-repo: `prek install` (sets up git hooks)

**For CI/CD** (future):
- Same config file works with standard pre-commit in CI
- Or use `prek run --all-files` for faster CI execution

## Phase 2: Task Breakdown

**Status**: ⏸️ NOT STARTED - Run `/speckit.tasks` to generate tasks.md

Task generation will create:
- Dependency installation tasks (uv add prek, ruff, etc.)
- Configuration file creation tasks (.pre-commit-config.yaml, .gitleaks.toml)
- Ruff configuration in pyproject.toml
- Hook installation tasks (prek install)
- Testing/validation tasks
- Documentation update tasks (README.md)

Expected task count: ~15-20 tasks organized into phases:
1. Setup (dependencies, config files)
2. Ruff configuration (P1 - formatting)
3. Secret detection setup (P2 - security)
4. Additional quality checks (P3 - whitespace, imports, etc.)
5. Testing and validation
6. Documentation

## Implementation Notes

### Key Decisions

1. **Why prek over pre-commit?**
   - 4-10x faster (critical for developer experience)
   - Fully compatible (zero migration cost from pre-commit if ever needed)
   - Active development (released Jan 2026, adopted by major projects)
   - Single binary (no Python dependency conflicts)

2. **Why ruff over Black + isort + flake8?**
   - Single tool replaces 3 tools
   - Faster than Black alone
   - Native import sorting (replaces isort)
   - Already fast-moving toward becoming Python standard

3. **Why gitleaks over detect-secrets?**
   - Better maintained (2026 updates vs 2023 for detect-secrets)
   - Lower false positive rate in benchmarks
   - Better pattern coverage for modern APIs
   - Simpler allowlist configuration

4. **Why builtin hooks?**
   - Zero latency (no network, no environment)
   - Offline-compatible
   - Covers 80% of common file validation needs

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Developers bypass hooks | Medium | Document bypass process, make hooks fast (<5s) |
| False positives in secret detection | Medium | Provide clear allowlist process, document common patterns |
| Hook slowdown on large commits | Low | Prek only runs on staged files, parallel execution |
| Conflicts with existing linters | Low | Ruff replaces existing tools, consolidates config |
| Installation friction | Low | One uv command, documented in README |

### Future Enhancements (Out of Scope)

- CI/CD integration (run hooks on GitHub Actions)
- Custom hook for SQL migration validation
- Custom hook for TOML credential schema validation
- Auto-update prek configuration weekly
- Pre-push hooks for running tests

## Success Metrics

Aligned with spec success criteria:

- **SC-001**: Measure - All Python files formatted consistently ✅ (Verified by running `ruff format --check`)
- **SC-002**: Measure - Zero secrets committed ✅ (Verified by `git log -p | gitleaks detect --no-git`)
- **SC-003**: Measure - Hook execution time <5s ✅ (Measured via `time git commit`)
- **SC-004**: Measure - One-command setup ✅ (Verified by following quickstart.md)
- **SC-005**: Measure - <1% false positive rate ✅ (Track gitleaks false positives over first 100 commits)
- **SC-006**: Measure - 100% of `sensitive/` commits blocked ✅ (Test by attempting commit to sensitive/)
- **SC-007**: Measure - TOML validation ✅ (Verified by check-toml hook)
- **SC-008**: Measure - Auto-formatting without action ✅ (Verified by commit flow)

## Next Steps

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Review and approve tasks.md
3. Run `/speckit.implement` to execute tasks
4. Validate all success criteria
5. Update main branch documentation
