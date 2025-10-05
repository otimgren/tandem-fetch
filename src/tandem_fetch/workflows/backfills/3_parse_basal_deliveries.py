"""Script to parse basal deliveries from events."""

from loguru import logger
from prefect import flow, task
from sqlalchemy import create_engine, text

from tandem_fetch.definitions import DATABASE_URL


@task
def populate_basal_deliveries() -> None:
    """Populate basal_deliveries table."""
    if not DATABASE_URL:
        msg = "DATABASE_URL is not configured"
        raise ValueError(msg)

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Raw SQL approach - direct INSERT...SELECT
        query = text("""
            INSERT INTO basal_deliveries (
                events_id,
                timestamp,
                profile_basal_rate,
                algorithm_basal_rate,
                temp_basal_rate
            )
            SELECT
                e.id,
                e.timestamp,
                CAST(e.event_data->>'profileBasalRate' AS INTEGER),
                CAST(e.event_data->>'algorithmRate' AS INTEGER),
                CAST(e.event_data->>'tempRate' AS INTEGER)
            FROM events e
            LEFT JOIN basal_deliveries cgm ON cgm.events_id = e.id
            WHERE cgm.id IS NULL
            AND e.event_name LIKE 'LID_BASAL_DELIVERY%'
        """)

        result = conn.execute(query)
        conn.commit()

        logger.success(
            f"Inserted {result.rowcount} basal deliveries using raw SQL"
        )


@flow
def populate_basal_deliveries_flow() -> None:
    """Populate the CGM readings table."""
    logger.info("Start populating basal deliveries")

    populate_basal_deliveries()
    logger.success("Populating basal deliveries completed")


if __name__ == "__main__":
    populate_basal_deliveries_flow()
