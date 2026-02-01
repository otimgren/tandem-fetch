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
        # DuckDB-compatible SQL - use json_extract_string for JSON access
        query = text("""
            INSERT INTO basal_deliveries (
                id,
                events_id,
                timestamp,
                profile_basal_rate,
                algorithm_basal_rate,
                temp_basal_rate
            )
            SELECT
                nextval('basal_deliveries_id_seq'),
                e.id,
                e.timestamp,
                CAST(json_extract_string(e.event_data, '$.profileBasalRate') AS INTEGER),
                CAST(json_extract_string(e.event_data, '$.algorithmRate') AS INTEGER),
                CAST(json_extract_string(e.event_data, '$.tempRate') AS INTEGER)
            FROM events e
            LEFT JOIN basal_deliveries bd ON bd.events_id = e.id
            WHERE bd.id IS NULL
            AND e.event_name LIKE 'LID_BASAL_DELIVERY%'
        """)

        result = conn.execute(query)
        conn.commit()

        logger.success(
            f"Inserted {result.rowcount} basal deliveries using raw SQL"
        )


@flow
def populate_basal_deliveries_flow() -> None:
    """Populate the basal deliveries table."""
    logger.info("Start populating basal deliveries")

    populate_basal_deliveries()
    logger.success("Populating basal deliveries completed")


if __name__ == "__main__":
    populate_basal_deliveries_flow()
