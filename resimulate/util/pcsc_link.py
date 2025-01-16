from exceptions import PcscError
from osmocom.utils import Hexstr, h2i, i2h
from pySim.transport import LinkBaseTpdu
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
from util.logger import log


class PcscLink(LinkBaseTpdu):
    protocol = CardConnection.T0_protocol

    def __init__(self, device: int, **kwargs):
        super().__init__(**kwargs)

        readers = System.readers()
        if device > len(readers):
            raise PcscError(f"Device with index {device} not found.")

        self.pcsc_device = readers[device]
        self.card_connection = ExclusiveConnectCardConnection(
            self.pcsc_device.createConnection()
        )

    def __str__(self) -> str:
        return "PCSC[%s]" % (self._reader)

    def __del__(self):
        try:
            self.card_connection.disconnect()
        except:
            pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.card_connection.disconnect()
        log.debug("Disconnected from device %s", self.pcsc_device)

    def connect(self):
        try:
            self.card_connection.disconnect()
            self.card_connection.connect()
            supported_protocols = self.card_connection.getSupportedProtocols()
            self.card_connection.disconnect()

            if supported_protocols & CardConnection.T0_protocol:
                protocol = CardConnection.T0_protocol
            elif supported_protocols & CardConnection.T1_protocol:
                protocol = CardConnection.T1_protocol
            else:
                raise PcscError("No supported protocol found.")

            log.debug(
                "Connecting to device %s using protocol %s", self.pcsc_device, protocol
            )

            self.card_connection.connect(protocol=protocol)
        except (CardConnectionException, NoCardException) as e:
            raise PcscError from e

        log.debug("Connected to device %s", self.pcsc_device)

    def disconnect(self):
        self.card_connection.disconnect()
        log.debug("Disconnected from device %s", self.pcsc_device)

    def _reset_card(self):
        self.disconnect()
        self.connect()

    def wait_for_card(self, timeout: int | None = None, newcardonly: bool = False):
        card_request = CardRequest(
            readers=[self.pcsc_device], timeout=timeout, newcardonly=newcardonly
        )
        try:
            log.debug("Waiting for card on device %s", self.pcsc_device)
            card_request.waitforcard()
        except CardRequestTimeoutException as e:
            raise PcscError from e

        self.__connect()

    def send_tpdu(self, tpdu: Hexstr) -> ResTuple:
        try:
            data, sw1, sw2 = self.card_connection.transmit(h2i(tpdu))
            return i2h(data) + i2h([sw1, sw2])
        except CardConnectionException as e:
            raise PcscError from e
