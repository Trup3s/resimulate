from osmocom.tlv import BER_TLV_IE
from osmocom.utils import h2b

from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.euicc.transport.pcsc_link import PcscLink


class Application:
    aid: str
    alternative_aids: list[str] = []
    name: str

    def __init__(
        self,
        link: PcscLink,
        aid: str | None = None,
    ):
        self.link = link
        self.aid = aid or self.aid

    def _merge_dicts(self, dicts: list[dict]) -> dict:
        return {k: v for d in dicts for k, v in d.items()}

    def store_data_tlv(
        self,
        caller_func_name: str,
        command_cls: type[BER_TLV_IE],
        response_cls: type[BER_TLV_IE] | None = None,
    ) -> type[BER_TLV_IE] | None:
        command_encoded = command_cls().to_tlv()

        if len(command_encoded) > 255:
            raise ValueError("Data too long")

        apdu = APDUPacket(cla=0x80, ins=0xE2, p1=0x91, p2=0x00, data=command_encoded)
        data, _ = self.link.send_apdu_with_mutation(self.name, caller_func_name, apdu)

        if response_cls is None:
            response_cls = command_cls

        if data:
            response = response_cls()
            response.from_tlv(h2b(data))
            return response

        return None
