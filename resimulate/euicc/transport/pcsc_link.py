import logging

from osmocom.utils import Hexstr, h2i, i2h
from pySim.transport import LinkBaseTpdu
from pySim.utils import ResTuple, sw_match
from pySim.exceptions import SwMatchError
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

from resimulate.euicc.mutation.engine import MutationEngine
from resimulate.euicc.mutation.types import MutationType
from resimulate.euicc.recorder.operation import MutationRecording, Operation
from resimulate.euicc.recorder.recorder import OperationRecorder
from resimulate.euicc.transport.apdu import APDUPacket
from resimulate.exceptions import PcscError


class PcscLink(LinkBaseTpdu):
    def __init__(
        self,
        mutation_engine: MutationEngine | None = None,
        recorder: OperationRecorder | None = None,
        device_index: int = 0,
        apdu_data_size: int = 255,
    ):
        super().__init__()

        readers: list[PCSCReader] = System.readers()
        if device_index > len(readers):
            raise PcscError(f"Device with index {device_index} not found.")

        if apdu_data_size > 255:
            logging.warning(
                "An APDU data size greater than 255 can cause issues with some cards."
            )

        self.pcsc_device = readers[device_index]
        self.card_connection = ExclusiveConnectCardConnection(
            self.pcsc_device.createConnection()
        )
        if recorder:
            logging.debug("Initializing recorder...")
            self.connect()
            recorder.atr = self.get_atr()
            self.disconnect()

        self.mutation_engine = mutation_engine
        self.recorder = recorder
        self.apdu_data_size = apdu_data_size

    def __str__(self) -> str:
        return "PCSC[%s]" % (self.pcsc_device)

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        try:
            self.disconnect()
            self.card_connection.connect()
            supported_protocol = self.card_connection.getProtocol()
            self.card_connection.disconnect()

            if supported_protocol & CardConnection.T0_protocol:
                protocol = CardConnection.T0_protocol
                self.set_tpdu_format(0)
            elif supported_protocol & CardConnection.T1_protocol:
                protocol = CardConnection.T1_protocol
                self.set_tpdu_format(1)
            else:
                raise PcscError("No supported protocol found: %s" % supported_protocol)

            logging.debug(
                "Connecting to device %s using protocol T%s", self.pcsc_device, protocol
            )

            self.card_connection.connect(protocol=protocol)
        except (CardConnectionException, NoCardException) as e:
            logging.error("Failed to connect to device")
            raise PcscError("Failed to connect to device") from e

        logging.debug("Connected to device %s", self.pcsc_device)

    def disconnect(self):
        try:
            self.card_connection.disconnect()
        except AttributeError:
            pass

        logging.debug("Disconnected from device %s", self.pcsc_device)

    def _reset_card(self):
        logging.debug("Resetting card...")
        self.disconnect()
        self.connect()

    def wait_for_card(self, timeout: int | None = None, newcardonly: bool = False):
        card_request = CardRequest(
            readers=[self.pcsc_device], timeout=timeout, newcardonly=newcardonly
        )
        try:
            logging.debug("Waiting for card...")
            card_request.waitforcard()
        except CardRequestTimeoutException as e:
            raise PcscError("Timeout waiting for card") from e

        self.connect()

    def get_atr(self) -> Hexstr:
        return i2h(self.card_connection.getATR())

    def send_tpdu(self, tpdu: Hexstr) -> ResTuple:
        data, sw1, sw2 = self.card_connection.transmit(h2i(tpdu))
        logging.debug(
            "Sent TPDU: %s, received data: %s, SW: %s",
            tpdu,
            i2h(data),
            i2h([sw1, sw2]),
        )
        return i2h(data), i2h([sw1, sw2])

    def send_apdu_with_mutation(
        self, app_name: str, func_name: str, apdu: APDUPacket
    ) -> ResTuple:
        def handle_apdu_tansmission(apdu: APDUPacket) -> tuple[str | None, str]:
            logging.debug("Sending %s", str(apdu))

            short_apdus = apdu.to_short_apdu(data_size=self.apdu_data_size)
            if len(short_apdus) > 1:
                logging.debug("Splitting APDU into %d short APDUs", len(short_apdus))

            for short_apdu in short_apdus:
                try:
                    data, sw = self.send_apdu_checksw(short_apdu.to_hex())
                except SwMatchError as exception:
                    return None, exception.sw_actual

            return data, sw

        if not self.mutation_engine:
            logging.debug("No mutation engine provided, sending original APDU")
            return handle_apdu_tansmission(apdu)

        recordings = []
        mutation_types = list(MutationType) + [None]
        success_data = None
        success_sw = "0000"

        for mutation_type in mutation_types:
            if mutation_type is None:
                mutated_apdu = apdu
            else:
                mutated_apdu = self.mutation_engine.mutate(
                    apdu, mutation_type=mutation_type
                )
                logging.debug(
                    "Testing mutation type: %s | APDU: %s -> %s",
                    mutation_type,
                    apdu.to_hex(),
                    mutated_apdu.to_hex(),
                )

            data, sw = handle_apdu_tansmission(mutated_apdu)
            if sw_match(sw, "9000"):
                success_data = data
                success_sw = sw

            if mutation_type is not None:
                recordings.append(
                    MutationRecording(
                        mutation_type,
                        apdu,
                        mutated_apdu,
                        sw,
                    )
                )

        if self.recorder:
            operation = Operation(
                app_name,
                func_name,
                mutation_recordings=recordings,
            )
            self.recorder.record(operation)

        return success_data, success_sw
