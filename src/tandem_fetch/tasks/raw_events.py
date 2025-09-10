"""Tasks for writing raw events to the database."""

import base64
from dataclasses import asdict

from loguru import logger
from prefect import task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tandem_fetch.db.raw_events.models import RawEvent
from tandem_fetch.definitions import DATABASE_URL
from tandem_fetch.pump_events.events import BaseEvent


@task
def write_raw_events_to_db(events: list[BaseEvent]) -> None:
    """Write a list of BaseEvent objects to the raw_events table.

    Args:
        events: List of BaseEvent objects to write to the database

    Raises:
        ValueError: If DATABASE_URL is not configured
        Exception: If database write operation fails
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured")

    if not events:
        logger.info("No events to write to database")
        return

    logger.info(f"Writing {len(events)} events to raw_events table")

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    try:
        with Session() as session:
            raw_event_records = []

            for event in events:
                # Convert the BaseEvent dataclass to a dictionary
                event_dict = asdict(event)

                # Convert any Arrow datetime objects to ISO strings for JSON serialization
                serialized_dict = _serialize_datetime_objects(event_dict)

                # Create RawEvents record
                raw_event = RawEvent(raw_event_data=serialized_dict)
                raw_event_records.append(raw_event)

            # Bulk insert all records
            session.add_all(raw_event_records)
            session.commit()

            logger.success(
                f"Successfully wrote {len(raw_event_records)} events to database"
            )

    except Exception as e:
        logger.error(f"Failed to write events to database: {e}")
        raise


def _serialize_datetime_objects(obj: object) -> object:
    """Recursively serialize Arrow datetime objects and binary data to JSON-compatible formats.

    Args:
        obj: Object that may contain Arrow datetime objects or binary data

    Returns:
        Object with Arrow datetimes converted to ISO strings and binary data to base64 strings
    """
    if hasattr(
        obj, "isoformat"
    ):  # Arrow datetime objects have isoformat method
        return obj.isoformat()  # type: ignore[attr-defined]
    elif isinstance(obj, (bytes, bytearray)):
        # Convert binary data to base64 string for JSON serialization
        return base64.b64encode(bytes(obj)).decode("utf-8")
    elif isinstance(obj, dict):
        return {
            key: _serialize_datetime_objects(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [_serialize_datetime_objects(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_serialize_datetime_objects(item) for item in obj)
    else:
        return obj
