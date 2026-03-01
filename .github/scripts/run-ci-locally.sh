#!/bin/bash
set -e

echo "Running local CI validation..."

# Install dependencies
uv sync --locked --all-extras --group dev --group test

# Run linting checks
uv run ruff check .

# Run format checks
uv run ruff format --check .

# Run security scans
uv run bandit -r src/ -c pyproject.toml
uv run pip-audit --ignore-vuln CVE-2025-69872 --ignore-vuln CVE-2025-62727

# Run tests
uv run pytest

echo "✓ All checks passed!"
