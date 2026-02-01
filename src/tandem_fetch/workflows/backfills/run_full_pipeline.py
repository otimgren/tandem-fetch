"""Run the complete data pipeline from fetch to parse."""

from loguru import logger
from prefect import flow

from tandem_fetch.workflows.backfills.step0_get_all_raw_pump_events import (
    get_all_raw_pump_events_flow,
)
from tandem_fetch.workflows.backfills.step1_parse_events_table import (
    parse_raw_events_flow,
)
from tandem_fetch.workflows.backfills.step2_parse_cgm_readings import (
    populate_cgm_readings_flow,
)
from tandem_fetch.workflows.backfills.step3_parse_basal_deliveries import (
    populate_basal_deliveries_flow,
)


@flow(name="full-pipeline")
def run_full_pipeline():
    """Run the complete data pipeline: fetch raw events and parse all tables.

    Steps:
        1. Fetch raw pump events from Tandem Source
        2. Parse raw events into structured events table
        3. Extract CGM readings from events
        4. Extract basal deliveries from events
    """
    logger.info("Starting full pipeline")

    # Step 0: Fetch raw events
    logger.info("Step 0: Fetching raw pump events from Tandem Source")
    get_all_raw_pump_events_flow()

    # Step 1: Parse events
    logger.info("Step 1: Parsing raw events into structured events table")
    parse_raw_events_flow()

    # Step 2: Extract CGM readings
    logger.info("Step 2: Extracting CGM readings")
    populate_cgm_readings_flow()

    # Step 3: Extract basal deliveries
    logger.info("Step 3: Extracting basal deliveries")
    populate_basal_deliveries_flow()

    logger.success("Full pipeline completed successfully")


if __name__ == "__main__":
    run_full_pipeline()
