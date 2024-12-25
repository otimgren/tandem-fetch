from tandem_fetch import credentials, tsource
from tandem_fetch.events.generic import decode_raw_events, get_event_generator


def main() -> None:
    print(f"Hello from tandem-fetch!")
    creds = credentials.TConnectCredentials.get_credentials()
    api = tsource.TSourceAPI(credentials=creds)
    pumper_info = api.get_pumper_info()
    pump_event_metadata = api.get_pump_event_metadata()
    raw_pump_events = api._get_pump_events_raw()
    decoded_events = decode_raw_events(raw_pump_events)
    events = list(get_event_generator(decoded_events))
    print(f"{pumper_info=}")
    print(f"{pump_event_metadata=}")
    # print(f"{decoded_events=}")
    print(events[-2:])
