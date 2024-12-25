"""Definitions for common constants."""

from pathlib import Path

ROOT_DIR = Path(__file__).absolute().parent.parent.parent
CREDENTIALS_PATH = ROOT_DIR / Path("sensitive/credentials.toml")

TIMEZONE_NAME = "America/New_York"
