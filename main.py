"""Single-file launcher for the SCI402 Agent API."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
APP_IMPORT_STRING = "sci402_agent.api:app"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def ensure_src_on_path() -> None:
    """Allow this launcher to run before the package is installed."""
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def get_port() -> int:
    """Read the local development port from the environment when provided."""
    return int(os.getenv("SCI402_PORT", DEFAULT_PORT))


def main() -> None:
    """Start the local FastAPI development server."""
    ensure_src_on_path()
    uvicorn.run(
        APP_IMPORT_STRING,
        host=os.getenv("SCI402_HOST", DEFAULT_HOST),
        port=get_port(),
        reload=True,
        reload_dirs=[str(SRC_DIR)],
        app_dir=str(SRC_DIR),
    )


if __name__ == "__main__":
    main()
