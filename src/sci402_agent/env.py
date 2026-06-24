"""Environment loading helpers for local development."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOTENV_PATH = PROJECT_ROOT / ".env"


def load_environment() -> bool:
    """Load the project .env file without overriding existing variables."""
    return load_dotenv(dotenv_path=DOTENV_PATH, override=False)
