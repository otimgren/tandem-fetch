"""Script to parse CGM readings from events table into cgm_readings table."""

from typing import Any

from loguru import logger
from prefect import flow, task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from tandem_fetch.db.cgm_readings import CgmReading
from tandem_fetch.db.events import Event
from tandem_fetch.definitions import DATABASE_URL


@task
def populate_cgm_readings() -> None:
    """Populate cgm_readings table using raw SQL INSERT...SELECT statement."""
    if not DATABASE_URL:
        msg = "DATABASE_URL is not configured"
        raise ValueError(msg)

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Raw SQL approach - direct INSERT...SELECT
        query = text("""
            INSERT INTO cgm_readings (events_id, timestamp, cgm_reading)
            SELECT
                e.id,
                e.timestamp,
                CAST(e.event_data->>'currentglucosedisplayvalue' AS INTEGER)
            FROM events e
            LEFT JOIN cgm_readings cgm ON cgm.events_id = e.id
            WHERE cgm.id IS NULL
            AND e.event_name LIKE 'LID_CGM_DATA%'
            AND e.event_data->>'currentglucosedisplayvalue' IS NOT NULL
        """)

        result = conn.execute(query)
        conn.commit()

        logger.success(f"Inserted {result.rowcount} CGM readings using raw SQL")


@flow(name="populate-cgm-readings")
def populate_cgm_readings_flow() -> None:
    """Populate the CGM readings table.

    Args:
        method: Method to use ("raw_sql", "orm", or "batch_orm")
        batch_size: Batch size for batch_orm method
    """
    logger.info(f"Starting CGM readings population")

    populate_cgm_readings()
    logger.success("CGM readings population completed")


if __name__ == "__main__":
    populate_cgm_readings_flow()
