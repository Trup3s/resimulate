from osmocom.utils import Hexstr, h2i, i2h
from pySim.transport import LinkBaseTpdu, ProactiveHandler
from pySim.utils import ResTuple
from smartcard import System
from smartcard.CardConnection import CardConnection
from smartcard.CardRequest import CardRequest
from smartcard.Exceptions import (
    CardConnectionException,
    CardRequestTimeoutException,
    NoCardException,
)
from smartcard.ExclusiveConnectCardConnection import ExclusiveConnectCardConnection
from smartcard.pcsc.PCSCReader import PCSCReader

from resimulate.exceptions import PcscError
from resimulate.util.logger import log


class PcscLink(LinkBaseTpdu):
    protocol = CardConnection.T0_protocol

    def __init__(self, device_index: int, **kwargs):
        super().__init__(proactive_handler=ProactiveHandler(), **kwargs)

        readers: list[PCSCReader] = System.readers()
        if device_index > len(readers):
            raise PcscError(f"Device with index {device_index} not found.")

        self.pcsc_device = readers[device_index]
        self.card_connection = ExclusiveConnectCardConnection(
            self.pcsc_device.createConnection()
        )

    def __str__(self) -> str:
        return "PCSC[%s]" % (self._reader)

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        try:
            self.card_connection.disconnect()
            self.card_connection.connect()
            supported_protocol = self.card_connection.getProtocol()
            self.card_connection.disconnect()

            if supported_protocol & CardConnection.T0_protocol:
                protocol = CardConnection.T0_protocol
            elif supported_protocol & CardConnection.T1_protocol:
                protocol = CardConnection.T1_protocol
            else:
                raise PcscError("No supported protocol found: %s" % supported_protocol)

            self.set_tpdu_format(protocol)
            log.debug(
                "Connecting to device %s using protocol T%s", self.pcsc_device, protocol
            )

            self.card_connection.connect(protocol=protocol)
        except (CardConnectionException, NoCardException) as e:
            log.error("Failed to connect to device")
            raise PcscError("Failed to connect to device") from e

        log.debug("Connected to device %s", self.pcsc_device)

    def disconnect(self):
        self.card_connection.disconnect()
        log.debug("Disconnected from device %s", self.pcsc_device)

    def _reset_card(self):
        log.debug("Resetting card...")
        self.disconnect()
        self.connect()
        return 1

    def wait_for_card(self, timeout: int | None = None, newcardonly: bool = False):
        card_request = CardRequest(
            readers=[self.pcsc_device], timeout=timeout, newcardonly=newcardonly
        )
        try:
            log.debug("Waiting for card...")
            card_request.waitforcard()
        except CardRequestTimeoutException as e:
            raise PcscError("Timeout waiting for card") from e

        self.connect()

    def get_atr(self) -> Hexstr:
        return self.card_connection.getATR()

    def send_tpdu(self, tpdu: Hexstr) -> ResTuple:
        try:
            data, sw1, sw2 = self.card_connection.transmit(h2i(tpdu))
            return i2h(data), i2h([sw1, sw2])
        except CardConnectionException as e:
            raise PcscError("Failed to send TPDU") from e
