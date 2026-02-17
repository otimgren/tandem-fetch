"""Database connection helpers for external packages."""

from pathlib import Path

from sqlalchemy import Engine


class DatabaseNotFoundError(FileNotFoundError):
    """Raised when the database file does not exist and interactive mode is disabled."""

    def __init__(self, database_path: Path, message: str | None = None):
        self.database_path = database_path
        if message is None:
            message = (
                f"Database not found at {database_path}. "
                "Run 'run-pipeline' to fetch data or set interactive=True to be prompted."
            )
        super().__init__(message)


def get_engine(interactive: bool = True) -> Engine | None:
    """Get a SQLAlchemy Engine connected to the DuckDB database.

    Args:
        interactive: If True, prompts user to fetch data when DB is missing.
                    If False, raises DatabaseNotFoundError immediately.

    Returns:
        SQLAlchemy Engine connected to the DuckDB database file.
        Returns None if interactive=True and user declines to fetch data.

    Raises:
        DatabaseNotFoundError: When interactive=False and database file doesn't exist.
    """
    from sqlalchemy import create_engine

    from tandem_fetch.definitions import DATABASE_PATH, DATABASE_URL

    # Check if database file exists
    if not DATABASE_PATH.exists():
        if interactive:
            # Interactive mode - prompt user to fetch data
            print(f"\nDatabase not found at {DATABASE_PATH}")
            response = input("Would you like to fetch data now? (y/n): ").strip().lower()

            if response == "y":
                # User wants to fetch data - run the pipeline
                print("Running data pipeline...")
                from tandem_fetch.workflows.backfills.run_full_pipeline import (
                    run_full_pipeline,
                )

                run_full_pipeline()
                print("Pipeline completed successfully.")
                # After pipeline runs, DB should exist - create and return engine
                engine = create_engine(DATABASE_URL)
                return engine
            else:
                # User declined - print instructions and return None
                print("\nTo fetch data manually, run:")
                print("  run-pipeline")
                return None
        else:
            # Non-interactive mode - raise error with informative message
            raise DatabaseNotFoundError(DATABASE_PATH)

    # Database exists - create and return engine
    engine = create_engine(DATABASE_URL)
    return engine
