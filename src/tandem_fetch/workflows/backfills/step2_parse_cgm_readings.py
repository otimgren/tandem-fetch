"""Script to parse CGM readings from events table into cgm_readings table."""

from loguru import logger
from prefect import flow, task
from sqlalchemy import create_engine, text

from tandem_fetch.definitions import DATABASE_URL


@task
def populate_cgm_readings() -> None:
    """Populate cgm_readings table using raw SQL INSERT...SELECT statement."""
    if not DATABASE_URL:
        msg = "DATABASE_URL is not configured"
        raise ValueError(msg)

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # DuckDB-compatible SQL - use json_extract_string for JSON access
        query = text("""
            INSERT INTO cgm_readings (events_id, timestamp, cgm_reading)
            SELECT
                e.id,
                e.timestamp,
                CAST(json_extract_string(e.event_data, '$.currentglucosedisplayvalue') AS INTEGER)
            FROM events e
            LEFT JOIN cgm_readings cgm ON cgm.events_id = e.id
            WHERE cgm.id IS NULL
            AND e.event_name LIKE 'LID_CGM_DATA%'
            AND json_extract_string(e.event_data, '$.currentglucosedisplayvalue') IS NOT NULL
        """)

        result = conn.execute(query)
        conn.commit()

        logger.success(f"Inserted {result.rowcount} CGM readings using raw SQL")


@flow(name="populate-cgm-readings")
def populate_cgm_readings_flow() -> None:
    """Populate the CGM readings table."""
    logger.info("Starting CGM readings population")

    populate_cgm_readings()
    logger.success("CGM readings population completed")


if __name__ == "__main__":
    populate_cgm_readings_flow()
