Modified version of [tconnectsync](https://github.com/jwoglom/tconnectsync) to read and parse
insulin pump data from Tandem Source.

# Setup
## Python
`uv sync`

## Credentials
- Fill in email and password for Tandem to sensitive/credentials.template.toml and rename credentials.toml
- Also fill in pump serial number. Can find on pump itself or from Tandem Source

## Database
- Install Postgresql
- Create `tandem_fetch` database
- Initialize alembic (`alembic init alembic`) and point SQLAlchemy URL to `tandem_fetch`, something like `sqlalchemy.url = postgresql+psycopg2://[user]:[password]@localhost:5432/tandem_fetch` by modifying `env.py`

## Get data from Tandem Source
- Run `uv run get-all-raw-pump-events` to fetch all raw data for pump events

# To-dos
1. Should migrate to having event created datetimes available in raw events so can run migrations with start times just after latest event created, so even if the latest data isn't fetched during the previous run can still fetch it during the next one.
2. Process raw events to CGM readings and boluses.