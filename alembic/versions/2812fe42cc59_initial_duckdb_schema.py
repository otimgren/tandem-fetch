"""initial_duckdb_schema

Revision ID: 2812fe42cc59
Revises:
Create Date: 2026-01-31 15:45:45.574867

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2812fe42cc59"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sequences for auto-increment (DuckDB doesn't support SERIAL)
    op.execute("CREATE SEQUENCE IF NOT EXISTS raw_events_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS events_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS cgm_readings_id_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS basal_deliveries_id_seq")

    # Create raw_events table first (no dependencies)
    op.create_table(
        "raw_events",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("raw_events_id_seq"),
            primary_key=True,
        ),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("raw_event_data", sa.JSON(), nullable=False),
    )

    # Create events table (no foreign key, just reference to raw_events)
    op.create_table(
        "events",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("events_id_seq"),
            primary_key=True,
        ),
        sa.Column("raw_events_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("event_name", sa.Text(), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.UniqueConstraint("raw_events_id"),
    )

    # Create cgm_readings table (references events)
    op.create_table(
        "cgm_readings",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("cgm_readings_id_seq"),
            primary_key=True,
        ),
        sa.Column("events_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("cgm_reading", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["events_id"],
            ["events.id"],
        ),
        sa.UniqueConstraint("events_id"),
    )

    # Create basal_deliveries table (references events)
    op.create_table(
        "basal_deliveries",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("basal_deliveries_id_seq"),
            primary_key=True,
        ),
        sa.Column("events_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("profile_basal_rate", sa.Integer(), nullable=True),
        sa.Column("algorithm_basal_rate", sa.Integer(), nullable=True),
        sa.Column("temp_basal_rate", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["events_id"],
            ["events.id"],
        ),
        sa.UniqueConstraint("events_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("basal_deliveries")
    op.drop_table("cgm_readings")
    op.drop_table("events")
    op.drop_table("raw_events")

    # Drop sequences
    op.execute("DROP SEQUENCE IF EXISTS basal_deliveries_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS cgm_readings_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS events_id_seq")
    op.execute("DROP SEQUENCE IF EXISTS raw_events_id_seq")
