"""Continuous data fetch — runs the full pipeline on a configurable interval.

Uses Prefect's flow.serve() for scheduling, which provides:
- Interval-based scheduling (configurable, default 5 minutes)
- Overlap prevention (limit=1 ensures no concurrent runs)
- Error resilience (failed runs are logged but don't stop scheduling)
- Graceful shutdown on Ctrl+C

Requires a Prefect server for the scheduler to create scheduled flow runs.
A local server is started automatically as a subprocess and cleaned up on exit.
"""

import atexit
import os
import subprocess  # nosec B404
import sys
import time
from datetime import timedelta

import requests
import typer
from loguru import logger

from tandem_fetch.workflows.backfills.run_full_pipeline import run_full_pipeline

DEFAULT_INTERVAL_MINUTES = 5
MIN_INTERVAL_MINUTES = 1
PREFECT_SERVER_PORT = 4200
PREFECT_API_URL = f"http://127.0.0.1:{PREFECT_SERVER_PORT}/api"

app = typer.Typer(help="Continuously fetch data from the Tandem API")


def _start_prefect_server() -> subprocess.Popen:
    """Start a local Prefect server with the scheduler enabled.

    Returns the subprocess handle. The server is started with the UI disabled
    and minimal logging to keep console output clean.
    """
    logger.info("Starting local Prefect server...")
    proc = subprocess.Popen(  # nosec B603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "--factory",
            "prefect.server.api.server:create_app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PREFECT_SERVER_PORT),
            "--log-level",
            "warning",
            "--lifespan",
            "on",
        ],
        env={**os.environ, "PREFECT_UI_ENABLED": "0"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    health_url = f"http://127.0.0.1:{PREFECT_SERVER_PORT}/api/health"
    for _ in range(200):
        try:
            if requests.get(health_url, timeout=2).status_code == 200:
                logger.info("Prefect server ready.")
                return proc
        except requests.ConnectionError:
            time.sleep(0.1)

    proc.kill()
    raise RuntimeError("Prefect server failed to start within 20 seconds.")


@app.command()
def start(
    interval: int = typer.Option(
        DEFAULT_INTERVAL_MINUTES,
        "--interval",
        help="Minutes between pipeline cycles (minimum: 1)",
    ),
) -> None:
    """Start continuous data fetching from the Tandem API."""
    if interval < MIN_INTERVAL_MINUTES:
        logger.error("Interval must be at least 1 minute.")
        raise typer.Exit(code=1)

    server_proc = _start_prefect_server()
    atexit.register(server_proc.terminate)
    os.environ["PREFECT_API_URL"] = PREFECT_API_URL

    logger.info(f"Starting continuous fetch (interval: {interval} minutes)")
    logger.info("Press Ctrl+C to stop.")

    run_full_pipeline.serve(
        name="continuous-fetch",
        interval=timedelta(minutes=interval),
        limit=1,
        pause_on_shutdown=False,
    )


def main() -> None:
    """Entry point for the continuous-fetch CLI command."""
    app()


if __name__ == "__main__":
    main()
