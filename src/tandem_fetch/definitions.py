"""Definitions for common constants."""

from pathlib import Path

ROOT_DIR = Path(__file__).absolute().parent.parent.parent
CREDENTIALS_PATH = ROOT_DIR / Path("sensitive/credentials.toml")

# DuckDB database configuration
DATABASE_PATH = ROOT_DIR / "data" / "tandem.db"
DATABASE_URL = f"duckdb:///{DATABASE_PATH}"

# Export configuration
EXPORT_DIR = ROOT_DIR / "exports"

TIMEZONE_NAME = "America/Los_Angeles"
