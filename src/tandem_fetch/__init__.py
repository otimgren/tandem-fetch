from tandem_fetch import credentials, tsource
from tandem_fetch.events.generic import decode_raw_events, get_event_generator


def main() -> None:
    print(f"Hello from tandem-fetch!")
    creds = credentials.TConnectCredentials.get_credentials()
    api = tsource.TSourceAPI(credentials=creds)
    pumper_info = api.get_pumper_info()
    pump_event_metadata = api.get_pump_event_metadata()
    pump_events = api.get_pump_events()
    print(f"{pumper_info=}")
    print(f"{pump_event_metadata=}")
    print(pump_events[-2:])
