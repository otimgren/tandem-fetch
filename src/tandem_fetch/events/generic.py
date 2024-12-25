import base64
from typing import Generator

from tandem_fetch.events.events import EVENT_IDS, BaseEvent
from tandem_fetch.events.raw_event import EVENT_LEN, RawEvent
from tandem_fetch.events.utils import batched


def decode_raw_events(raw_events: str) -> bytearray:
    """Decode the raw events string."""
    return base64.b64decode(raw_events)


def get_event(event_bytes: bytearray) -> BaseEvent:
    """Parse the even string into the correct type of Event class."""
    return EVENT_IDS[RawEvent.build(event_bytes).id].build(event_bytes)


def get_event_generator(events_bytes: bytearray) -> Generator[BaseEvent, None, None]:
    """Parse the events string into the correct type of Event class."""
    return (get_event(bytearray(e)) for e in batched(events_bytes, EVENT_LEN))
