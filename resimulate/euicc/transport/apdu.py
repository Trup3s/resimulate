from dataclasses import dataclass

from osmocom.utils import b2h, i2h


@dataclass
class APDUPacket:
    cla: int
    ins: int
    p1: int
    p2: int
    data: bytes = b""
    le: int = 0x00

    def __str__(self):
        return (
            f"APDU (cla={b2h([self.cla])} ins={i2h([self.ins])} p1={i2h([self.p1])} "
            f"p2={i2h([self.p2])} lc={i2h([self.lc])} data={b2h(self.data)} le={i2h([self.le])} "
            f"extended={self.is_extended()})"
        )

    def __repr__(self):
        return str(self)

    @property
    def lc(self):
        return len(self.data) if self.data else 0

    def is_extended(self) -> bool:
        return self.lc > 255 or self.le > 255

    def to_short_apdu(self, data_size: int = 255) -> list["APDUPacket"]:
        """Convert the APDU to a list of short APDUs if it exceeds the maximum length."""
        if self.lc > data_size or self.le > data_size:
            short_apdus = []
            data_chunks = [
                self.data[i : i + data_size]
                for i in range(0, len(self.data), data_size)
            ]

            for index, chunk in enumerate(data_chunks):
                # p1 is 0x11 until the last chunk, where it is 0x91
                p1 = 0x11 if index + 1 < len(data_chunks) else 0x91
                short_apdu = APDUPacket(
                    cla=self.cla,
                    ins=self.ins,
                    p1=p1,
                    p2=index,
                    data=chunk,
                    le=min(self.le, data_size),
                )
                short_apdus.append(short_apdu)

            return short_apdus
        return [self]

    def to_hex(self) -> str:
        apdu = bytearray([self.cla, self.ins, self.p1, self.p2])

        if self.data and len(self.data) > 255 or self.le > 255:
            if self.data:
                lc = len(self.data)
                # Prepend 0x00 to indicate extended length
                apdu.append(0x00)
                apdu.extend(lc.to_bytes(2, "big"))
                apdu.extend(self.data)

                if self.le > 255:
                    apdu.extend(self.le.to_bytes(2, "big"))
                else:
                    apdu.append(self.le)
            else:
                if self.le > 255:
                    # No Lc, but extended Le -> Prepend 0x00
                    # to indicate extended length
                    apdu.append(0x00)
                    apdu.extend(self.le.to_bytes(2, "big"))
                else:
                    apdu.append(self.le)
        else:
            # Short APDU
            if self.data:
                apdu.append(len(self.data))
                apdu.extend(self.data)

                if self.le is not None:
                    apdu.append(self.le)

            elif self.le is not None:
                apdu.append(self.le)

        return apdu.hex()

    @classmethod
    def from_hex(cls, hex_str: str) -> "APDUPacket":
        data = bytes.fromhex(hex_str)
        if len(data) < 4:
            raise ValueError("APDU must be at least 4 bytes long")

        cla, ins, p1, p2 = data[:4]
        idx = 4
        apdu_data = b""
        le = None

        if idx == len(data):
            return cls(cla, ins, p1, p2)

        # Check for extended length indicator
        if data[idx] == 0x00:
            idx += 1

            if len(data) - idx == 2:
                # Case: only Le
                le = int.from_bytes(data[idx : idx + 2], "big")

            elif len(data) - idx >= 2:
                lc = int.from_bytes(data[idx : idx + 2], "big")
                idx += 2

                if len(data) - idx == lc:
                    apdu_data = data[idx:]
                elif len(data) - idx == lc + 2:
                    apdu_data = data[idx : idx + lc]
                    le = int.from_bytes(data[idx + lc : idx + lc + 2], "big")
                else:
                    raise ValueError("Invalid extended APDU format")
        else:
            if len(data) - idx == 1:
                le = data[idx]
            else:
                lc = data[idx]
                idx += 1
                if len(data) - idx == lc:
                    apdu_data = data[idx:]
                elif len(data) - idx == lc + 1:
                    apdu_data = data[idx : idx + lc]
                    le = data[idx + lc]
                else:
                    raise ValueError("Invalid short APDU format")

        return cls(cla, ins, p1, p2, data=apdu_data, le=le)
