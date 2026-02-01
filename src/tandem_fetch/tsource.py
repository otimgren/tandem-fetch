"""Code for working with the Tandem Source API to fetch pump data."""

import base64
import datetime
import hashlib
import os
import urllib
import urllib.parse
from typing import Any

import jwt
import requests
from loguru import logger

from tandem_fetch.credentials import TConnectCredentials
from tandem_fetch.pump_events.events import EVENT_IDS, BaseEvent
from tandem_fetch.pump_events.generic import decode_raw_events, get_event_generator

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44"
DEFAULT_START_DATE = datetime.date(2025, 9, 1)


class TSourceAPI:
    """Helper class for working with the Tandem Source API."""

    LOGIN_PAGE_URL = "https://sso.tandemdiabetes.com"
    LOGIN_API_URL = "https://tdcservices.tandemdiabetes.com/accounts/api/login"
    TDC_OIDC_CLIENT_ID = "0oa27ho9tpZE9Arjy4h7"
    TDC_AUTH_CALLBACK_URL = "https://sso.tandemdiabetes.com/auth/callback"
    TDC_TOKEN_ENDPOINT = "https://tdcservices.tandemdiabetes.com/accounts/api/connect/token"  # noqa: S105
    TDC_AUTH_ENDPOINT = "https://tdcservices.tandemdiabetes.com/accounts/api/connect/authorize"
    TDC_OIDC_ISSUER = "https://tdcservices.tandemdiabetes.com/accounts/api"
    TDC_OIDC_CONFIG_URL = (
        "https://tdcservices.tandemdiabetes.com/accounts/api/.well-known/openid-configuration"
    )
    TDC_OIDC_JWKS_URL = (
        "https://tdcservices.tandemdiabetes.com/accounts/api/.well-known/openid-configuration/jwks"
    )
    SOURCE_URL = "https://source.tandemdiabetes.com"

    def __init__(self, credentials: TConnectCredentials) -> None:
        """Initialize the API.

        Store credentials in self and authorize so that can pull data from Tandem Source.
        """
        self.credentials = credentials
        self.session = requests.Session()
        self.id_token: str | None = None
        self.access_token: str | None = None
        self.pumper_id: str | None = None
        self.account_id: str | None = None
        self.tconnect_device_id: int | None = None

        self.log_in()
        self._load_oidc_tokens()
        self._load_pumper_id()
        self._load_pump_device_id()

    @property
    def headers(self) -> dict[str, str]:
        """Get auth and other headers."""
        return {**self.auth_headers, **self.other_headers}

    @property
    def other_headers(self) -> dict[str, str]:
        """Get headers other than authentication headers."""
        return {"user-agent": USER_AGENT}

    @property
    def auth_headers(self) -> dict[str, str]:
        """Get authentication related headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Origin": "https://tconnect.tandemdiabetes.com",
            "Referer": "https://tconnect.tandemdiabetes.com/",
        }

    def log_in(self) -> None:
        """Log in to Tandem Source."""
        logger.info("Logging in to Tandem Source...")

        payload = {
            "username": self.credentials.email,
            "password": self.credentials.password,
        }
        headers = {"Referer": self.LOGIN_PAGE_URL, **self.other_headers}
        response = self.session.post(
            self.LOGIN_API_URL,
            json=payload,
            headers=headers,
            allow_redirects=False,
        )
        if not response.ok:
            msg = f"Unable to log in to Tandem Source: {response=}"
            raise ConnectionRefusedError(msg)
        logger.info("Logged in to Tandem Source successfully.")

    def _load_oidc_tokens(self) -> None:
        """Get the OIDC tokens to authenticate identity with Tandem Source."""
        logger.info("Getting OIDC tokens...")
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        auth_params = {
            "client_id": self.TDC_OIDC_CLIENT_ID,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": self.TDC_AUTH_CALLBACK_URL,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_response = self.session.get(
            f"{self.TDC_AUTH_ENDPOINT}?{urllib.parse.urlencode(auth_params)}",
            headers={"Referer": self.LOGIN_PAGE_URL, **self.other_headers},
            allow_redirects=True,
        )
        oidc_callback_code = urllib.parse.parse_qs(urllib.parse.urlparse(auth_response.url).query)[
            "code"
        ][0]

        oidc_params = {
            "grant_type": "authorization_code",
            "client_id": self.TDC_OIDC_CLIENT_ID,
            "code": oidc_callback_code,
            "redirect_uri": self.TDC_AUTH_CALLBACK_URL,
            "code_verifier": code_verifier,
        }
        oidc_response = self.session.post(
            self.TDC_TOKEN_ENDPOINT,
            data=oidc_params,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                **self.other_headers,
            },
        )
        self.id_token = oidc_response.json()["id_token"]
        self.access_token = oidc_response.json()["access_token"]
        logger.info("Successfully retrieved OIDC tokens")

    @staticmethod
    def _generate_code_verifier() -> str:
        """Generate a high-entropy code verifier."""
        return base64.urlsafe_b64encode(os.urandom(64)).decode("utf-8").rstrip("=")

    @staticmethod
    def _generate_code_challenge(verifier: str) -> str:
        """Generate a code challenge from the code verifier."""
        sha256_digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(sha256_digest).decode("utf-8").rstrip("=")

    def _load_pumper_id(self) -> None:
        """Extract the pumper ID and account ID from the ID token.

        This contacts the OIDC provider to get JSON Web Key Sets, grabs the correct
        key, decodes the ID token and extracts the pumper ID and account ID.
        """
        logger.info("Getting pumper ID...")
        if self.id_token is None:
            msg = "id_token is None; run OIDC before trying to get pumper ID."
            raise ValueError(msg)

        oidc_config = self.session.get(self.TDC_OIDC_CONFIG_URL).json()
        jwks_client = jwt.PyJWKClient(oidc_config["jwks_uri"])
        signing_key = jwks_client.get_signing_key_from_jwt(self.id_token)

        data = jwt.decode_complete(
            self.id_token,
            key=signing_key,
            audience=self.TDC_OIDC_CLIENT_ID,
            algorithms=["RS256"],
            issuer=self.TDC_OIDC_ISSUER,
        )
        self.pumper_id = data["payload"]["pumperId"]
        self.account_id = data["payload"]["accountId"]
        logger.info(f"Successfully retrieved pumper ID: {self.pumper_id}")

    def _load_pump_device_id(self) -> None:
        """Get the device ID for the pump serial nuumber specified in self.credentials."""
        pump_event_metadata = self.get_pump_event_metadata()
        filtered_event_metadata = list(
            filter(
                lambda x: x["serialNumber"] == self.credentials.pump_serial_number,
                pump_event_metadata,
            )
        )
        if len(filtered_event_metadata) == 0:
            msg = "No pump found matching the provided serial number."
            raise ValueError(msg)
        if len(filtered_event_metadata) > 1:
            logger.warning(
                "Found more than 1 pump matching the provided serial number; using the first one."
            )
        self.tconnect_device_id = filtered_event_metadata[0]["tconnectDeviceId"]

    def get_pumper_info(self) -> dict[str, str]:
        """Get information about the user and available pumps."""
        response = self.session.get(
            f"{self.SOURCE_URL}/api/pumpers/pumpers/{self.pumper_id}",
            headers=self.headers,
        )
        if not response.ok:
            msg = f"Failed to get pumper info: {response}"
            raise requests.HTTPError(msg, response=response)
        return response.json()

    def get_pump_event_metadata(self) -> list[dict[str, Any]]:
        """Get info abount pump events."""
        response = self.session.get(
            f"{self.SOURCE_URL}/api/reports/reportsfacade/{self.pumper_id}/pumpeventmetadata",
            headers=self.headers,
        )
        if not response.ok:
            msg = f"Failed to get pump event metadata info: {response}"
            raise requests.HTTPError(msg, response=response)
        return response.json()

    def _get_pump_events_raw(self, start_date: datetime.date, end_date: datetime.date) -> str:
        """Get raw pump events."""
        if self.tconnect_device_id is None:
            self._load_pump_device_id()

        params = {
            "minDate": start_date.strftime("%Y-%m-%d"),
            "maxDate": end_date.strftime("%Y-%m-%d"),
        }
        event_ids = "%2C".join(str(event_code) for event_code in list(EVENT_IDS.keys()))
        query = f"{urllib.parse.urlencode(params)}&eventIds={event_ids}"
        url = (
            f"{self.SOURCE_URL}/api/reports/reportsfacade/pumpevents/{self.pumper_id}/"
            f"{self.tconnect_device_id}?{query}"
        )
        response = self.session.get(
            url,
            headers=self.headers,
        )
        if not response.ok:
            msg = f"Failed to get pump event data: {response}"
            print(response.text)
            raise requests.HTTPError(msg, response=response)
        return response.json()

    def get_pump_events(
        self,
        start_date: datetime.date = DEFAULT_START_DATE,
        end_date: datetime.date | None = None,
    ) -> list[BaseEvent]:
        """Get pump events for the given time period."""
        if end_date is None:
            end_date = datetime.date.today()

        raw_pump_events = self._get_pump_events_raw(start_date=start_date, end_date=end_date)
        decoded_events = decode_raw_events(raw_pump_events)
        return list(get_event_generator(decoded_events))
