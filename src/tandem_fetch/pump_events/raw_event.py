import struct
from dataclasses import dataclass
from typing import Self

import arrow

from tandem_fetch.definitions import TIMEZONE_NAME

EVENT_LEN = 26
UINT16 = ">H"
UINT32 = ">I"
TANDEM_EPOCH = 1199145600


@dataclass
class RawEvent:
    source: int
    id: int
    timestampRaw: int
    seqNum: int
    raw: bytearray

    @classmethod
    def build(cls, raw: bytearray) -> Self:
        """Build a raw event from a bytearray."""
        (source_and_id,) = struct.unpack_from(UINT16, raw[:EVENT_LEN], 0)
        (timestampRaw,) = struct.unpack_from(UINT32, raw[:EVENT_LEN], 2)
        (seqNum,) = struct.unpack_from(UINT32, raw[:EVENT_LEN], 6)

        return cls(
            source=(source_and_id & 0xF000) >> 12,
            id=source_and_id & 0x0FFF,
            timestampRaw=timestampRaw,
            seqNum=seqNum,
            raw=raw,
        )

    @property
    def timestamp(self) -> arrow.arrow.Arrow:
        """Get the timestamp for the event."""
        # Event timestamps do not have TZ data attached to them when parsed,
        # but represent the user's time zone setting. So we keep the time
        # referenced on them, but force the timezone to what the user
        # requests via the TZ secret.
        return arrow.get(TANDEM_EPOCH + self.timestampRaw, tzinfo="UTC").replace(
            tzinfo=TIMEZONE_NAME
        )
