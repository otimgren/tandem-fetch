"""Tests for the continuous fetch workflow."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from click.exceptions import Exit as ClickExit

from tandem_fetch.workflows.continuous_fetch import (
    DEFAULT_INTERVAL_MINUTES,
    MIN_INTERVAL_MINUTES,
    start,
)


@pytest.fixture()
def mock_serve():
    """Mock run_full_pipeline.serve to prevent actual scheduling."""
    with patch("tandem_fetch.workflows.continuous_fetch.run_full_pipeline") as mock_flow:
        mock_flow.serve = MagicMock()
        yield mock_flow


@pytest.fixture()
def mock_server(mock_serve):
    """Mock the Prefect server startup so tests don't start a real server."""
    mock_proc = MagicMock()
    with patch(
        "tandem_fetch.workflows.continuous_fetch._start_prefect_server",
        return_value=mock_proc,
    ) as mock_start:
        yield mock_start, mock_proc


class TestDefaults:
    """Test default configuration values."""

    def test_default_interval_is_5_minutes(self):
        assert DEFAULT_INTERVAL_MINUTES == 5

    def test_min_interval_is_1_minute(self):
        assert MIN_INTERVAL_MINUTES == 1


class TestStartWithDefaultInterval:
    """Test start() with default interval."""

    def test_calls_serve_with_default_interval(self, mock_serve, mock_server):
        start(interval=DEFAULT_INTERVAL_MINUTES)

        mock_serve.serve.assert_called_once_with(
            name="continuous-fetch",
            interval=timedelta(minutes=DEFAULT_INTERVAL_MINUTES),
            limit=1,
            pause_on_shutdown=False,
        )

    def test_calls_serve_with_limit_1(self, mock_serve, mock_server):
        start(interval=DEFAULT_INTERVAL_MINUTES)

        _, kwargs = mock_serve.serve.call_args
        assert kwargs["limit"] == 1


class TestStartWithCustomInterval:
    """Test start() with custom interval values."""

    def test_calls_serve_with_custom_interval(self, mock_serve, mock_server):
        start(interval=10)

        mock_serve.serve.assert_called_once_with(
            name="continuous-fetch",
            interval=timedelta(minutes=10),
            limit=1,
            pause_on_shutdown=False,
        )

    def test_calls_serve_with_1_minute_interval(self, mock_serve, mock_server):
        start(interval=1)

        _, kwargs = mock_serve.serve.call_args
        assert kwargs["interval"] == timedelta(minutes=1)

    def test_calls_serve_with_30_minute_interval(self, mock_serve, mock_server):
        start(interval=30)

        _, kwargs = mock_serve.serve.call_args
        assert kwargs["interval"] == timedelta(minutes=30)


class TestIntervalValidation:
    """Test interval validation — values below minimum are rejected."""

    def test_interval_0_exits_with_error(self, mock_serve, mock_server):
        with pytest.raises(ClickExit):
            start(interval=0)

        mock_serve.serve.assert_not_called()

    def test_interval_negative_exits_with_error(self, mock_serve, mock_server):
        with pytest.raises(ClickExit):
            start(interval=-5)

        mock_serve.serve.assert_not_called()

    def test_interval_1_is_accepted(self, mock_serve, mock_server):
        start(interval=1)

        mock_serve.serve.assert_called_once()


class TestPrefectServer:
    """Test that the Prefect server is started and registered for cleanup."""

    def test_starts_prefect_server(self, mock_serve, mock_server):
        mock_start, _ = mock_server

        start(interval=5)

        mock_start.assert_called_once()

    def test_registers_server_cleanup(self, mock_serve, mock_server):
        _, mock_proc = mock_server

        with patch("tandem_fetch.workflows.continuous_fetch.atexit") as mock_atexit:
            start(interval=5)

            mock_atexit.register.assert_called_once_with(mock_proc.terminate)

    def test_does_not_start_server_for_invalid_interval(self, mock_serve, mock_server):
        mock_start, _ = mock_server

        with pytest.raises(ClickExit):
            start(interval=0)

        mock_start.assert_not_called()
