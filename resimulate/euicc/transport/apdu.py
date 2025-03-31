from dataclasses import dataclass

from osmocom.utils import b2h, i2h


@dataclass
class APDUPacket:
    cla: int
    ins: int
    p1: int
    p2: int
    data: bytes = b""
    le: int = 0

    def __str__(self):
        return f"APDU (cla={b2h([self.cla])} ins={i2h([self.ins])} p1={i2h([self.p1])} p2={i2h([self.p2])} lc={i2h([self.lc])} data={b2h(self.data)} p3/le={i2h([self.le])})"

    @property
    def lc(self):
        return len(self.data) if self.data else 0

    def to_hex(self) -> str:
        """Returns the APDU packet as a hex string."""
        apdu = bytearray([self.cla, self.ins, self.p1, self.p2])
        if self.lc > 0:
            apdu.append(self.lc)
            apdu.extend(self.data)
        if self.le > 0:
            apdu.append(self.le)

        return apdu.hex()
