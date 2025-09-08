"""Tasks for fetching data from T:Source."""

import datetime

from loguru import logger
from prefect import task

from tandem_fetch.pump_events.events import BaseEvent
from tandem_fetch.tsource import TSourceAPI


@task
def fetch_pump_events_for_time_range(
    api: TSourceAPI, start: datetime.datetime, end: datetime.datetime | None
) -> list[BaseEvent]:
    """Fetch pump events for the given time range."""
    if end is None:
        end = datetime.datetime.now()
    logger.info(f"Fetching pump events from {start} to {end}")
    pump_events = api.get_pump_events(
        start_date=start.date(), end_date=end.date()
    )
    logger.info(f"Fetched {len(pump_events):,} pump events")
    return pump_events
