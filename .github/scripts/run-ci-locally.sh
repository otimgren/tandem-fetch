#!/bin/bash
set -e

echo "Running local CI validation..."

# Install dependencies
uv sync --locked --all-extras --group dev --group test

# Run linting checks
uv run ruff check .

# Run format checks
uv run ruff format --check .

# Run tests
uv run pytest

echo "✓ All checks passed!"
