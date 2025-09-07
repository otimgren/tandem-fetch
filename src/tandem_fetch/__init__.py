import polars as pl

pl.Config.set_fmt_str_lengths(1000)
pl.Config.set_tbl_rows(100)

from tandem_fetch import credentials, tsource


def main() -> None:
    print(f"Hello from tandem-fetch!")
    creds = credentials.TConnectCredentials.get_credentials()
    api = tsource.TSourceAPI(credentials=creds)
    pumper_info = api.get_pumper_info()
    pump_event_metadata = api.get_pump_event_metadata()
    pump_events = api.get_pump_events()
    print(f"{pumper_info=}")
    print(f"{pump_event_metadata=}")
    print(f"Number of pump events: {len(pump_events)=}")
    print("Last 2 events:")
    print(pump_events[-2:])

    df_events = pl.DataFrame(
        {
            "event_name": [repr(e.NAME) for e in pump_events],
        }
    )
    print(df_events["event_name"].value_counts().sort("count", descending=True))
