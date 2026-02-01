"""Workflow to get and write to the DB all raw pump events from T:Connect."""

import datetime

import dateutil.parser
from loguru import logger
from prefect import flow
from sqlalchemy import create_engine, text

from tandem_fetch.definitions import DATABASE_URL
from tandem_fetch.tasks import auth, fetch, raw_events


def _get_latest_updated_at() -> datetime.datetime | None:
    """Get the latest event timestamp from the raw_events table.

    Uses the actual event_timestamp from the pump data (not the DB insertion time)
    to ensure we don't miss events if a previous fetch was interrupted.
    """
    if not DATABASE_URL:
        return None

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Query for the latest event_timestamp from the JSON data
        # Using DuckDB's json_extract_string function
        result = conn.execute(text("""
            SELECT MAX(json_extract_string(raw_event_data, '$.event_timestamp'))
            FROM raw_events
        """)).scalar()

        if result is None:
            return None

        # Parse the ISO timestamp string to datetime
        return dateutil.parser.parse(result)


@flow
def get_all_raw_pump_events_flow():
    """Get and write to the DB all raw pump events from T:Connect."""
    api = auth.log_in_to_tsource()

    start = _get_latest_updated_at() or datetime.datetime(2020, 1, 1)
    end = datetime.datetime.now()

    # Need to use batches here as there is a limit to how many events can
    # be fetched at once - using 7-day batches
    current_start = start
    batch_size = datetime.timedelta(days=7)

    while current_start < end:
        current_end = min(current_start + batch_size, end)

        pump_events = fetch.fetch_pump_events_for_time_range(
            api=api,
            start=current_start,
            end=current_end,
        )
        logger.info(
            f"Fetched {len(pump_events):,} pump events from {current_start} to {current_end}"
        )
        raw_events.write_raw_events_to_db(pump_events)

        current_start = current_end


if __name__ == "__main__":
    get_all_raw_pump_events_flow()
