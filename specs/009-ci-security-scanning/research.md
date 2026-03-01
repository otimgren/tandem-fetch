# Research: CI Security Scanning

**Feature**: 009-ci-security-scanning
**Date**: 2026-02-28

## R1: Static Analysis Tool

**Decision**: Bandit with `[toml]` extra for pyproject.toml configuration

**Rationale**: Bandit is the standard Python SAST tool. It's fast, well-maintained by the PyCQA organization, has broad coverage of security issues (40+ checks), and supports inline suppression via `# nosec` comments. Configuration via `[tool.bandit]` in pyproject.toml keeps everything in one place. The `[toml]` extra is required to read pyproject.toml config.

**Alternatives considered**:
- Semgrep: More powerful rule engine but heavier, requires network for rule fetching, over-engineered for a single-user project.
- Pylint security plugins: Less comprehensive than Bandit for security-specific checks. Pylint is not currently used in this project.
- Ruff security rules: Ruff is already used but its security coverage is limited compared to Bandit's dedicated checks.

## R2: Dependency Vulnerability Scanner

**Decision**: pip-audit using the PyPI advisory database (default)

**Rationale**: pip-audit is maintained by PyPA (the Python Packaging Authority), uses the official Python advisory database, is lightweight, and has clear exit codes for CI (0 = clean, 1 = vulnerabilities found). It works with uv-managed projects by scanning the installed environment after `uv sync`.

**Alternatives considered**:
- Safety: Commercial tool with a free tier but rate-limited. Less open than pip-audit.
- uv-secure: Community tool specifically for uv lockfiles, but less mature and less widely adopted than pip-audit.
- Snyk/Trivy: Full-featured but heavy. Designed for container and infrastructure scanning. Over-engineered for a Python-only project.

## R3: Bandit Configuration

**Decision**: Configure via `[tool.bandit]` in pyproject.toml. Scan `src/` and `tests/` but skip `B101` (assert_used — standard in tests) and `B608` (hardcoded SQL — too many false positives with SQLAlchemy `text()` queries). Use `-c pyproject.toml` flag to load config.

**Rationale**: The project uses SQLAlchemy with `text()` for raw SQL queries (in the MCP server query tool), which triggers B608 false positives. Asserts are used extensively in tests. All other Bandit checks are relevant and should remain enabled.

**Known false positives in this codebase**:
- `signal.SIGALRM` usage in MCP server (B110 try_except_pass — not actually present, but worth monitoring)
- `subprocess.Popen` in continuous_fetch.py for Prefect server (B603 — LOW severity, acceptable)
- `requests.get()` calls without explicit timeout may trigger B113

## R4: pip-audit Integration

**Decision**: Run `pip-audit` after `uv sync` to scan the installed environment. Use CLI flags for any vulnerability allowlisting (no config file support yet). Output in default `columns` format for readable CI logs.

**Rationale**: pip-audit doesn't natively read `uv.lock` files, but scanning the installed venv after `uv sync --locked` achieves the same result with pinned versions. The `columns` format is human-readable in CI logs. JSON output can be added later if machine parsing is needed.

## R5: CI Integration Pattern

**Decision**: Add two new steps to the existing `.github/workflows/ci.yml` job — one for Bandit, one for pip-audit. Both run after dependency installation and before tests. Also add both commands to `.github/scripts/run-ci-locally.sh`.

**Rationale**: Running security scans in the same job (not a separate workflow) keeps CI simple and fast. Running before tests means security failures are caught early without waiting for the full test suite. The local CI script mirrors the GitHub Actions pipeline for environment parity.

**Alternatives considered**:
- Separate GitHub Actions workflow: Adds complexity for no benefit in a single-job CI.
- Pre-commit hooks: Would slow down every commit. Security scanning is better as a CI gate.
