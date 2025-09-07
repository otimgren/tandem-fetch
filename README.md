Modified version of [tconnectsync](https://github.com/jwoglom/tconnectsync) to read and parse
insulin pump data from Tandem Source.

# Setup
## Python
`uv sync`

## Credentials
- Fill in email and password for Tandem to sensitive/credentials.template.toml
- Optionally can also fill in pump serial number

## Database
- Install Postgresql
- Create `tandem_fetch` database
- Initialize alembic and point SQLAlchemy URL to `tandem_fetch`, something like `sqlalchemy.url = postgresql+psycopg2://[user]:[password]@localhost:5432/tandem_fetch`

# Run