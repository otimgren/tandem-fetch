"""Tasks for authentication with T:Source."""

from prefect import task

from tandem_fetch.credentials import TConnectCredentials
from tandem_fetch.tsource import TSourceAPI


@task
def log_in_to_tsource() -> TSourceAPI:
    """Log in to T:Source and return the API client."""
    creds = TConnectCredentials.get_credentials()
    return TSourceAPI(credentials=creds)
