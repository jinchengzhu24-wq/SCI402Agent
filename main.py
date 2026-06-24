"""Single-file launcher for the SCI402 Agent API."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

import uvicorn


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
APP_IMPORT_STRING = "sci402_agent.api:app"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
PORT_SCAN_LIMIT = 20


def ensure_src_on_path() -> None:
    """Allow this launcher to run before the package is installed."""
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def is_port_available(host: str, port: int) -> bool:
    """Return True when the local server can bind to the requested port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))
    except OSError:
        return False

    return True


def get_port(host: str) -> int:
    """Read or choose the local development port."""
    configured_port = os.getenv("SCI402_PORT")
    if configured_port:
        return int(configured_port)

    for port in range(DEFAULT_PORT, DEFAULT_PORT + PORT_SCAN_LIMIT):
        if is_port_available(host, port):
            return port

    raise RuntimeError(
        f"No available local port found from {DEFAULT_PORT} "
        f"to {DEFAULT_PORT + PORT_SCAN_LIMIT - 1}."
    )


def main() -> None:
    """Start the local FastAPI development server."""
    ensure_src_on_path()
    host = os.getenv("SCI402_HOST", DEFAULT_HOST)
    port = get_port(host)
    print(f"Starting SCI402 Agent at http://{host}:{port}")
    uvicorn.run(
        APP_IMPORT_STRING,
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(SRC_DIR)],
        app_dir=str(SRC_DIR),
    )


if __name__ == "__main__":
    main()
