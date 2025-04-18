import inspect

from osmocom.utils import h2b
from pySim.utils import sw_match

from resimulate.asn import asn
from resimulate.euicc.exceptions import ApduException
from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.euicc.transport.pcsc_link import PcscLink


class Application:
    aid: str
    alternative_aids: list[str] = []
    name: str
    cla_byte: int

    def __init__(
        self,
        link: PcscLink,
        aid: str,
        cla_byte: int = 0x80,
    ):
        self.link = link
        self.aid = aid or self.aid
        self.cla_byte = cla_byte

    def _merge_dicts(self, dicts: list[dict]) -> dict:
        return {k: v for d in dicts for k, v in d.items()}

    def store_data(
        self,
        request_type: str | None = None,
        response_type: str | None = None,
        request_data: dict | None = None,
        caller_func_name: str | None = None,
    ) -> dict | tuple | str | None:
        if request_data is None:
            request_data = dict()

        command_encoded = request_data
        if request_type is not None:
            command_encoded = asn.encode(
                request_type,
                request_data,
                check_constraints=True,
            )

        if len(command_encoded) > 65536:
            raise ValueError("Data too long")

        if not caller_func_name:
            caller_frame = inspect.stack()[1]
            caller_func_name = caller_frame.function

        apdu = APDUPacket(cla=0x80, ins=0xE2, p1=0x91, p2=0x00, data=command_encoded)
        data, sw = self.link.send_apdu_with_mutation(self.name, caller_func_name, apdu)

        if not any([sw_match(sw, pattern) for pattern in ["9000", "61??"]]):
            raise ApduException(sw)

        if not data:
            return None

        if response_type is None:
            return data

        return asn.decode(response_type, h2b(data), check_constraints=True)
