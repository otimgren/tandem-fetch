"""Script to parse raw_events table entries into structured events in the events table."""

from curses import raw

import dateutil
from loguru import logger
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import sessionmaker

from tandem_fetch.db.events import Event
from tandem_fetch.db.raw_events import RawEvent
from tandem_fetch.definitions import DATABASE_URL
from tandem_fetch.pump_events.events import EVENT_IDS


@task(cache_policy=NO_CACHE)
def get_raw_events_to_process(batch_size: int = 1000) -> list[RawEvent]:
    """Get raw events that haven't been processed yet.

    Args:
        batch_size: Number of raw events to fetch at once

    Returns:
        List of raw event records as dictionaries
    """
    if not DATABASE_URL:
        msg = "DATABASE_URL is not configured"
        raise ValueError(msg)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        raw_events_query = (
            session.query(RawEvent)
            .outerjoin(
                Event,
                (RawEvent.id == Event.raw_events_id),
            )
            .filter(Event.id.is_(None))
            .order_by(RawEvent.id)
            .limit(batch_size)
        )

        result = raw_events_query.all()

    logger.info(f"Found {len(result)} raw events to process")
    return result


@task
def parse_and_insert_events(raw_events: list[RawEvent]) -> None:
    """Parse raw events and insert them into the events table.

    Args:
        raw_events: List of raw event records to process
    """
    if not DATABASE_URL:
        msg = "DATABASE_URL is not configured"
        raise ValueError(msg)

    if not raw_events:
        logger.info("No raw events to process")
        return

    engine = create_engine(DATABASE_URL)
    session_maker = sessionmaker(bind=engine)

    with session_maker() as session:
        event_records = []
        for raw_event in raw_events:
            event_data = raw_event.raw_event_data

            event_timestamp = dateutil.parser.parse(
                event_data["event_timestamp"]
            )
            event_id = int(event_data["event_id"])
            event_name = EVENT_IDS[int(event_data["raw_event"]["id"])].NAME
            del event_data["raw_event"]

            event_record = Event(
                timestamp=event_timestamp,
                raw_events_id=raw_event.id,
                event_id=event_id,
                event_name=event_name,
                event_data=event_data,
            )
            event_records.append(event_record)

    if event_records:
        session.add_all(event_records)
        session.commit()
        logger.success(f"Successfully inserted {len(event_records)} events")


@flow(name="parse-raw-events-to-events")
def parse_raw_events_flow(batch_size: int = 1000) -> None:
    """Parse raw events into structured events table.

    Args:
        batch_size: Number of events to process in each batch

    """
    logger.info("Starting raw events parsing flow")

    while True:
        # Get a batch of raw events to process
        raw_events = get_raw_events_to_process(batch_size=batch_size)

        if not raw_events:
            logger.info("No more raw events to process")
            break

        # Parse and insert the events
        parse_and_insert_events(raw_events)

        logger.info(f"Processed batch of {len(raw_events)} events")

    logger.success("Raw events parsing flow completed")


if __name__ == "__main__":
    parse_raw_events_flow()
