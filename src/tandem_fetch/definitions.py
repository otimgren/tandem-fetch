"""Definitions for common constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).absolute().parent.parent.parent
CREDENTIALS_PATH = ROOT_DIR / Path("sensitive/credentials.toml")
DATABASE_URL = os.getenv("DATABASE_URL")

TIMEZONE_NAME = "America/Los_Angeles"
