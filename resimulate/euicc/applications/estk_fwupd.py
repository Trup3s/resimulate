from resimulate.euicc.applications import Application
from resimulate.euicc.transport.apdu import APDUPacket


class ESTK_FWUPD(Application):
    aid = "A06573746B6D65FFFFFFFF6677757064"
    name = "ESTK_FWUPD"

    def unlock(self):
        apdu = APDUPacket.from_str("0155555500")
        self.link.send_apdu_with_mutation(self.name, "unlock", apdu)

    def get_version(self):
        apdu = APDUPacket.from_str("aaff00000800")
        self.link.send_apdu_with_mutation(self.name, "get_version", apdu)

    def send_firmware(self, binary_path: str):
        pass
