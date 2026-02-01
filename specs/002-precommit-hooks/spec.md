# Feature Specification: Pre-Commit Hooks for Code Quality and Security

**Feature Branch**: `002-precommit-hooks`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "I want to add pre commit hooks to this project using prek. I want to run a ruff formatter with reasonable defaults to start with and may add more checks in the future. If you have some recommendations for checks to run, let's add those. I'd be especially interested in checks that make sure no passwords, API keys or PII are committed"

## User Scenarios & Testing

### User Story 1 - Automatic Code Formatting (Priority: P1)

As a developer committing code, the pre-commit hook automatically formats my Python code with ruff so that all code follows consistent style without manual intervention.

**Why this priority**: Core value proposition - ensures code quality from day one. Without this, there's no pre-commit hook functionality at all.

**Independent Test**: Make a code change with inconsistent formatting (e.g., inconsistent quotes, missing newlines), attempt to commit, and verify that the hook auto-formats the code and requires re-staging.

**Acceptance Scenarios**:

1. **Given** I have modified a Python file with inconsistent formatting, **When** I run `git commit`, **Then** ruff formatter runs automatically and fixes formatting issues
2. **Given** the formatter made changes to my staged files, **When** the hook completes, **Then** I am prompted to review and re-stage the formatted files
3. **Given** my Python code is already properly formatted, **When** I run `git commit`, **Then** the formatter hook passes without making changes

---

### User Story 2 - Secret Detection (Priority: P2)

As a developer working with sensitive health data APIs, the pre-commit hook prevents me from accidentally committing passwords, API keys, or other secrets to version control.

**Why this priority**: Critical for security, especially given this project handles health data. However, P2 because the project can function without it (just with higher security risk).

**Independent Test**: Attempt to commit a file containing a fake API key or password string, and verify the hook blocks the commit with a clear error message.

**Acceptance Scenarios**:

1. **Given** I attempt to commit a file containing an API key pattern, **When** I run `git commit`, **Then** the hook detects the secret and blocks the commit
2. **Given** I attempt to commit a file with a password in plain text, **When** I run `git commit`, **Then** the hook detects the secret and blocks the commit
3. **Given** I have already configured credentials in `sensitive/credentials.toml`, **When** I accidentally try to commit that file, **Then** the hook blocks the commit
4. **Given** the hook detected a secret, **When** the commit is blocked, **Then** I receive a clear error message indicating which file and line contains the secret

---

### User Story 3 - Additional Code Quality Checks (Priority: P3)

As a developer, pre-commit hooks run additional Python code quality checks beyond formatting (e.g., import sorting, trailing whitespace removal) to catch common issues before they enter the codebase.

**Why this priority**: Nice to have - improves code quality but not critical for core functionality. Can be added incrementally after P1 and P2 are working.

**Independent Test**: Commit a file with unsorted imports or trailing whitespace, and verify the hooks fix or flag these issues.

**Acceptance Scenarios**:

1. **Given** I have a Python file with unsorted imports, **When** I run `git commit`, **Then** the hook automatically sorts the imports
2. **Given** I have a file with trailing whitespace, **When** I run `git commit`, **Then** the hook removes trailing whitespace
3. **Given** I have a file with mixed line endings, **When** I run `git commit`, **Then** the hook normalizes to LF line endings

---

### Edge Cases

- What happens when a hook modifies a file? The developer must review changes and re-stage the file before committing.
- How does the system handle false positives in secret detection? Developer can bypass with explicit flag or exclude specific patterns.
- What if a developer doesn't have pre-commit installed? The hooks won't run locally, but this should be documented in setup instructions.
- What happens when committing non-Python files? Hooks should skip files they don't apply to.
- How are credential files in `sensitive/` directory handled? They should be gitignored, but secret detection provides defense-in-depth.

## Requirements

### Functional Requirements

- **FR-001**: System MUST automatically format Python code using ruff with reasonable defaults before each commit
- **FR-002**: System MUST detect and block commits containing API keys, passwords, tokens, or other credential patterns
- **FR-003**: System MUST detect and block commits containing potential PII (email addresses, phone numbers, SSNs)
- **FR-004**: System MUST provide clear error messages indicating which files and lines contain detected secrets
- **FR-005**: System MUST allow developers to bypass hooks in exceptional circumstances (e.g., intentional test data)
- **FR-006**: System MUST automatically sort Python imports according to standard conventions
- **FR-007**: System MUST remove trailing whitespace from files
- **FR-008**: System MUST normalize line endings to LF (Unix-style)
- **FR-009**: Configuration MUST use prek (pre-commit hook manager) for managing hooks
- **FR-010**: Hooks MUST only run on staged files (not entire codebase) for performance
- **FR-011**: System MUST check for large files that shouldn't be committed (e.g., >1MB)
- **FR-012**: System MUST validate TOML configuration files for syntax errors
- **FR-013**: System MUST prevent committing files in `sensitive/` directory as defense-in-depth

### Key Entities

- **Pre-commit Configuration**: Defines which hooks run, in what order, on which file types
- **Hook**: Individual check or formatter (ruff, secret detection, whitespace, etc.)
- **Secret Pattern**: Regular expression or rule for detecting sensitive data
- **Excluded Pattern**: Files or patterns that should skip certain hooks

## Success Criteria

### Measurable Outcomes

- **SC-001**: All Python files in the codebase are automatically formatted consistently without manual intervention
- **SC-002**: Zero secrets (API keys, passwords, tokens) committed to version control after hook installation
- **SC-003**: Developers can commit properly formatted code in under 5 seconds (hook execution time)
- **SC-004**: Hook setup requires only one command (`uv run --with prek prek install` or similar)
- **SC-005**: Secret detection has <1% false positive rate on normal code
- **SC-006**: 100% of commits to `sensitive/` directory are blocked
- **SC-007**: All TOML configuration files are validated for syntax errors before commit
- **SC-008**: Import sorting and whitespace cleanup happen automatically without developer action
