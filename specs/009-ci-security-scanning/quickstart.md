# Quickstart: CI Security Scanning

**Feature**: 009-ci-security-scanning
**Date**: 2026-02-28

## Prerequisites

1. Python 3.12+
2. The tandem-fetch project installed with dev dependencies (`uv sync --all-groups`)

## Running Security Scans Locally

### All scans (via local CI script)

```bash
.github/scripts/run-ci-locally.sh
```

This runs the full CI pipeline locally, including the new security scans.

### Bandit (code security analysis)

```bash
# Scan source code
uv run bandit -r src/ -c pyproject.toml

# Scan with verbose output
uv run bandit -r src/ -c pyproject.toml -v
```

### pip-audit (dependency vulnerabilities)

```bash
# Check all installed dependencies
uv run pip-audit
```

## Handling Findings

### Suppressing a Bandit finding (intentional exception)

Add `# nosec` with the test ID to the line:

```python
# Before (Bandit reports B602)
subprocess.Popen(cmd, shell=True)

# After (suppressed with explanation)
subprocess.Popen(cmd, shell=True)  # nosec B602 - trusted internal command
```

### Allowlisting a dependency vulnerability

If a vulnerability is reviewed and accepted (e.g., not applicable to this project), add it to the pip-audit command:

```bash
uv run pip-audit --ignore-vuln GHSA-xxxx-yyyy-zzzz
```

## What Gets Scanned

| Tool | Scope | What it checks |
|------|-------|---------------|
| Bandit | `src/` directory | Insecure functions, hardcoded secrets, injection risks, weak crypto |
| pip-audit | All installed packages | Known CVEs in dependencies |

## CI Behavior

Both scans run automatically on every push to `main` and every pull request. If either scan finds issues, the CI pipeline fails and the PR cannot be merged until the issues are resolved or explicitly suppressed.
