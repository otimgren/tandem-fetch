"""Workflow to get and write to the DB all raw pump events from T:Connect."""

import datetime
from venv import logger

from prefect import flow
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from tandem_fetch.db.raw_events.models import RawEvents
from tandem_fetch.definitions import DATABASE_URL
from tandem_fetch.tasks import auth, fetch, raw_events


def _get_latest_updated_at() -> datetime.datetime | None:
    """Get the latest created timestamp from the raw_events table."""
    if not DATABASE_URL:
        return None

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        result = session.query(func.max(RawEvents.created)).scalar()
        if result is None:
            return None
        return result


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
