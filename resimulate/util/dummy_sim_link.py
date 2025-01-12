from osmocom.utils import h2i
from pySim.transport import LinkBase


# Taken from the pySim project and modified for the ReSIMulate project
class DummySimLink(LinkBase):
    """A dummy implementation of the LinkBase abstract base class.  Currently required
    as the UiccCardBase doesn't work without SimCardCommands, which in turn require
    a LinkBase implementation talking to a card.

    In the tracer, we don't actually talk to any card, so we simply drop everything
    and claim it is successful.

    The UiccCardBase / SimCardCommands should be refactored to make this obsolete later.
    """

    def __init__(self, debug: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._debug = debug
        self._atr = h2i("3B9F96801F878031E073FE211B674A4C753034054BA9")

    def __str__(self) -> str:
        return "dummy"

    def _send_apdu(self, pdu) -> tuple[list, str]:
        return [], "9000"

    def connect(self):
        pass

    def disconnect(self):
        pass

    def _reset_card(self):
        return 1

    def get_atr(self) -> list[int]:
        return self._atr

    def wait_for_card(self):
        pass
