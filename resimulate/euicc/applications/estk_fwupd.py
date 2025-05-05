import os

from pySim.utils import sw_match

from resimulate.euicc.applications import Application
from resimulate.euicc.exceptions import ApduException, EuiccException
from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.util import str2ascii


class ESTK_FWUPD(Application):
    aid = "A06573746B6D65FFFFFFFF6677757064"
    name = "ESTK_FWUPD"

    def unlock(self):
        apdu = APDUPacket(cla=0xAA, ins=0x21, p1=0x00, p2=0x00)
        _, sw = self.link.send_apdu_with_mutation(self.name, "unlock", apdu)

        if not sw_match(sw, "9000"):
            raise ApduException(sw)

    def setup(self):
        apdu = APDUPacket(cla=0x01, ins=0x55, p1=0x55, p2=0x55)
        _, sw = self.link.send_apdu_with_mutation(self.name, "setup", apdu)

        if not sw_match(sw, "9000"):
            raise ApduException(sw)

    def check_flash_status(self):
        apdu = APDUPacket(cla=0xAA, ins=0x13, p1=0x00, p2=0x00)
        _, sw = self.link.send_apdu_with_mutation(self.name, "check_flash_status", apdu)

        if not sw_match(sw, "9000"):
            raise ApduException(sw)

    def get_version(self):
        self.setup()
        # TODO: Fix transaction failure
        apdu = APDUPacket(cla=0xAA, ins=0xFF, p1=0x00, p2=0x00, le=0x08)
        data, sw = self.link.send_apdu_with_mutation(self.name, "get_version", apdu)
        if not sw_match(sw, "9000"):
            raise ApduException(sw)

        return str2ascii(data)

    def __send_program_block(
        self, block_id: int, data: bytes, validate: bool = False
    ) -> int:
        remaining_bytes = len(data)
        ins = 0x12 if validate else 0x11

        while remaining_bytes > 0:
            chunk_size = min(self.link.apdu_data_size, remaining_bytes)
            current_chunk = len(data) - remaining_bytes
            p1 = current_chunk >> 8
            p2 = current_chunk & 0xFF

            apdu = APDUPacket(cla=0xAA, ins=ins, p1=p1, p2=p2)

            if not validate:
                apdu.data = bytearray(data[current_chunk : current_chunk + chunk_size])
            else:
                apdu.le = chunk_size

            name = (
                f"send_program_block_{block_id}_validate"
                if validate
                else f"send_program_block_{block_id}"
            )
            _, sw = self.link.send_apdu_with_mutation(self.name, name, apdu)
            if not sw_match(sw, "9000"):
                raise ApduException(sw)

            remaining_bytes -= chunk_size

        return True

    def send_firmware(self, binary_path: str, block_size: int = 0x80D):
        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"File not found: {binary_path}")

        program_block = 0

        self.setup()
        self.unlock()

        with open(binary_path, "rb") as file_stream:
            while data := file_stream.read(block_size):
                transmit_success = self.__send_program_block(program_block, data)
                valid = self.__send_program_block(program_block, data, validate=True)

                if not transmit_success or not valid:
                    raise EuiccException(
                        f"Error sending program block: {program_block} | "
                        f"Transmit success: {transmit_success} | Valid: {valid}"
                    )

                self.check_flash_status()
                program_block += 1

        _, sw = self.link.send_apdu_with_mutation(
            self.name, "finish_flash", APDUPacket.from_hex("aa0000000000")
        )
        if not sw_match(sw, "9000"):
            raise ApduException(sw)
