"""Helpers for getting credentials for Tandem Connect."""

from dataclasses import dataclass
from typing import Self

import tomllib

from tandem_fetch import definitions


@dataclass
class TConnectCredentials:
    """Dataclass for storing TConnect credentials."""

    email: str
    password: str
    pump_serial_number: str

    @classmethod
    def get_credentials(cls) -> Self:
        """Get T:connect credentials from file."""
        with definitions.CREDENTIALS_PATH.open("rb") as f:
            creds = tomllib.load(f)

        return cls(
            email=creds["TANDEM_SOURCE_EMAIL"],
            password=creds["TANDEM_SOURCE_PASSWORD"],
            pump_serial_number=creds.get("PUMP_SERIAL_NUMBER", ""),
        )
