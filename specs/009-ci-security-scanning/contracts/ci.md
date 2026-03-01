# CI Contract: Security Scanning

**Feature**: 009-ci-security-scanning
**Date**: 2026-02-28

## CI Steps (added to existing pipeline)

### Step: Run Bandit security scan

**Purpose**: Static analysis of Python source code for security vulnerabilities.

**Runs after**: Dependency installation
**Runs before**: Tests

**Command**:
```bash
uv run bandit -r src/ -c pyproject.toml
```

**Exit codes**:
- `0`: No security issues found
- `1`: One or more security issues found (CI fails)

**Output** (on failure):
```
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified
   Severity: High   Confidence: High
   CWE: CWE-78
   More Info: https://bandit.readthedocs.io/en/...
   Location: src/tandem_fetch/example.py:42:4
```

**Maps to**: FR-001, FR-003, FR-005, FR-006, FR-009

---

### Step: Run pip-audit dependency scan

**Purpose**: Check installed dependencies for known security vulnerabilities (CVEs).

**Runs after**: Dependency installation
**Runs before**: Tests

**Command**:
```bash
uv run pip-audit
```

**Exit codes**:
- `0`: No vulnerable dependencies found
- `1`: One or more vulnerable dependencies found (CI fails)

**Output** (on failure):
```
Name       Version ID                  Fix Versions
---------- ------- ------------------- ------------
requests   2.25.0  GHSA-xxxx-yyyy-zzzz 2.32.0
```

**Maps to**: FR-002, FR-004, FR-005, FR-009

---

## Local CI Script

### Command: `run-ci-locally.sh`

**Purpose**: Run the same security scans locally as CI.

**Added commands** (after linting, before tests):
```bash
# Security scans
uv run bandit -r src/ -c pyproject.toml
uv run pip-audit
```

**Maps to**: FR-008

---

## Bandit Configuration (pyproject.toml)

```toml
[tool.bandit]
exclude_dirs = [".venv", "build", "dist"]
skips = ["B101", "B608"]
```

**Skipped checks**:
- `B101` (assert_used): Asserts are standard in test code and acceptable in this project.
- `B608` (hardcoded_sql_expressions): False positives with SQLAlchemy `text()` parameterized queries.

**Maps to**: FR-006 (inline suppression via `# nosec`), FR-007 (config-level exclusions)
